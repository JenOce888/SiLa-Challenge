"""
Gestionnaire_Tache_Avance_PyQt.py — CONTROLLER layer of the MVC architecture.

Responsibilities:
    - Owns the TaskModel (business logic)
    - Listens to user actions from Views (button clicks, drag-drops, dialog results)
    - Calls Model methods to read/write data
    - Passes results back to Views (Kanban columns, dashboard)
    - Knows nothing about SQL or chart rendering — that belongs to Model/View

MVC Flow:
    View (click) → Controller → Model (logic + DB) → Controller → View (render)
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QScrollArea, QFrame, QMessageBox, QFileDialog,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag, QIcon, QAction, QPixmap, QColor

from database import Database
from models import TaskModel
from task_card import TaskCard
from task_dialog import TaskDialog
from dashboard import DashboardDialog
from export_manager import ExportManager
from logger import get_logger

log = get_logger(__name__)


# KanbanColumn — VIEW component


class KanbanColumn(QWidget):
    """VIEW: A single Kanban column that accepts card drops."""
    task_dropped = pyqtSignal(int, str)  # (task_id, new_status)

    def __init__(self, title: str, status: str, parent=None):
        super().__init__(parent)
        self.status = status
        self.setAcceptDrops(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background-color: ##5a0000; color: #ffffff;
                font-size: 15px; font-weight: bold;
                padding: 10px; border-radius: 8px;
            }
        """)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.cards_widget)
        layout.addWidget(self.scroll)

        self._set_style(False)

    def _set_style(self, highlighted: bool):
        border = "#89b4fa" if highlighted else "#3a3144"
        self.setStyleSheet(f"""
            KanbanColumn {{
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 2px solid {border};
            }}
        """)

    def add_card(self, card):
        self.cards_layout.addWidget(card)

    def clear_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self._set_style(True)

    def dragLeaveEvent(self, event):
        self._set_style(False)

    def dropEvent(self, event):
        task_id = int(event.mimeData().text())
        self.task_dropped.emit(task_id, self.status)
        self._set_style(False)
        event.acceptProposedAction()


# MainWindow — primary CONTROLLER

class MainWindow(QMainWindow):
    """
    CONTROLLER: Orchestrates Model <-> View interactions.
    All user actions route through here; no SQL or chart code lives here.
    """

    def __init__(self):
        super().__init__()
        # Model (business logic layer)
        db = Database()
        db.migrate()
        self.model = TaskModel(db)
        self.export_manager = ExportManager(db)

        self.setWindowTitle("Advanced Task Manager")
        self.setMinimumSize(1100, 700)
        self._apply_global_styles()
        self._setup_tray()
        self._build_ui()
        self.refresh_board()
        log.info("MainWindow initialized.")

    def _apply_global_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #181825; }
            QWidget { background-color: #181825; color: #cdd6f4; font-family: 'Segoe UI', News Times; }
            QComboBox, QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 6px 10px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                padding: 8px 18px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#exportBtn { background-color: #a6e3a1; color: #1e1e2e; }
            QPushButton#statsBtn  { background-color: #cba6f7; color: #1e1e2e; }
        """)

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#89b4fa"))
        self.tray.setIcon(QIcon(pixmap))
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.setToolTip("Task Manager")
        self.tray.show()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Top bar
        topbar = QHBoxLayout()

        title = QLabel("📑 Kanban Board")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #89b4fa;")
        topbar.addWidget(title)
        topbar.addStretch()

        self.filter_tag = QComboBox()
        self.filter_tag.setFixedWidth(140)
        self.filter_tag.addItem("󠀯🎟 All Tags")
        self.filter_tag.currentTextChanged.connect(self.refresh_board)

        self.filter_priority = QComboBox()
        self.filter_priority.setFixedWidth(150)
        self.filter_priority.addItems(["Priority", "High", "Medium", "Low"])
        self.filter_priority.currentTextChanged.connect(self.refresh_board)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search...")
        self.search_box.setFixedWidth(200)
        self.search_box.textChanged.connect(self.refresh_board)

        add_btn = QPushButton("＋  New Task")
        add_btn.clicked.connect(self.on_new_task)

        stats_btn = QPushButton("📈  Dashboard")
        stats_btn.setObjectName("statsBtn")
        stats_btn.clicked.connect(self.on_open_dashboard)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.setObjectName("exportBtn")
        export_csv_btn.clicked.connect(self.on_export_csv)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setObjectName("exportBtn")
        export_pdf_btn.clicked.connect(self.on_export_pdf)

        for w in [self.search_box, self.filter_tag, self.filter_priority,
                  add_btn, stats_btn, export_csv_btn, export_pdf_btn]:
            topbar.addWidget(w)

        root.addLayout(topbar)

        # Kanban columns
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(12)

        self.col_todo       = KanbanColumn("📝  To Do",       "todo")
        self.col_inprogress = KanbanColumn("🔧  In Progress", "inprogress")
        self.col_done       = KanbanColumn("✅  Done",        "done")

        for col in [self.col_todo, self.col_inprogress, self.col_done]:
            col.task_dropped.connect(self.on_task_dropped)
            columns_layout.addWidget(col)

        root.addLayout(columns_layout)

    # Controller: Board Refresh 

    def refresh_board(self):
        """Ask Model for filtered tasks, render them in View columns."""
        for col in [self.col_todo, self.col_inprogress, self.col_done]:
            col.clear_cards()

        tag = self.filter_tag.currentText()
        tag = None if "All" in tag else tag.strip()

        priority = self.filter_priority.currentText()
        priority = None if "Priority" in priority else priority.lstrip("(HighMediumLow)").strip().lower()

        search = self.search_box.text().strip() or None

        # Model call — business logic decides what to return
        tasks = self.model.get_all_tasks(tag=tag, priority=priority, search=search)

        # Sync tag dropdown with current tags in DB
        all_tags    = self.model.get_all_tags()
        current_tag = self.filter_tag.currentText()
        self.filter_tag.blockSignals(True)
        self.filter_tag.clear()
        self.filter_tag.addItem("🎟 All Tags")
        for t in all_tags:
            self.filter_tag.addItem(t)
        idx = self.filter_tag.findText(current_tag)
        if idx >= 0:
            self.filter_tag.setCurrentIndex(idx)
        self.filter_tag.blockSignals(False)

        col_map = {
            "todo":       self.col_todo,
            "inprogress": self.col_inprogress,
            "done":       self.col_done,
        }

        # Pass data to View (TaskCard renders it)
        for task in tasks:
            card = TaskCard(task)
            card.edit_requested.connect(self.on_edit_task)
            card.delete_requested.connect(self.on_delete_task)
            col_map.get(task["status"], self.col_todo).add_card(card)

        log.debug("Board refreshed: %d tasks rendered.", len(tasks))

    # Controller: User Action Handlers

    def on_task_dropped(self, task_id: int, new_status: str):
        """User dragged a card to a new column."""
        self.model.move_task(task_id, new_status)
        self.tray.showMessage("Task Moved", f"Task #{task_id} moved to {new_status}",
                              QSystemTrayIcon.MessageIcon.Information, 2000)
        self.refresh_board()

    def on_new_task(self):
        log.info("User opened New Task dialog.")
        dlg = TaskDialog(self.model, parent=self)
        if dlg.exec():
            self.refresh_board()

    def on_edit_task(self, task_id: int):
        log.info("User opened Edit dialog for task #%d.", task_id)
        task = self.model.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Not Found", f"Task #{task_id} could not be found.")
            return
        dlg = TaskDialog(self.model, task=task, parent=self)
        if dlg.exec():
            self.refresh_board()

    def on_delete_task(self, task_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model.delete_task(task_id)
            self.refresh_board()

    def on_open_dashboard(self):
        """Fetch stats from Model, pass to Dashboard View."""
        log.info("User opened Dashboard.")
        stats = self.model.get_stats()
        dlg = DashboardDialog(stats, parent=self)
        dlg.exec()

    def on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "tasks.csv", "CSV (*.csv)")
        if path:
            self.export_manager.to_csv(path)
            log.info("Exported CSV to: %s", path)
            self.tray.showMessage("Export", f"CSV saved: {path}",
                                  QSystemTrayIcon.MessageIcon.Information, 3000)
            QMessageBox.information(self, "Success", f"Exported to:\n{path}")

    def on_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "tasks.pdf", "PDF (*.pdf)")
        if path:
            self.export_manager.to_pdf(path)
            log.info("Exported PDF to: %s", path)
            self.tray.showMessage("Export", f"PDF saved: {path}",
                                  QSystemTrayIcon.MessageIcon.Information, 3000)
            QMessageBox.information(self, "Success", f"Exported to:\n{path}")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        log.info("Window hidden to system tray.")
        self.tray.showMessage(
            "App Minimized",
            "Running in background. Click the tray icon to reopen.",
            QSystemTrayIcon.MessageIcon.Information, 2000
        )


# Application entry point

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
