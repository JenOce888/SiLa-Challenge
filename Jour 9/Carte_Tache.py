"""
Carte_Tache.py — VIEW layer.

Renders a single task as a draggable Kanban card.
Due date is color-coded using the Model's get_due_date_status() helper:
    - Overdue  → red  (#f38ba8)
    - Today    → green (#a6e3a1)
    - Upcoming → cadetblue (#5f9ea0)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QColor

from models import get_due_date_status
from logger import get_logger

log = get_logger(__name__)

PRIORITY_COLORS = {
    "High":   "#f38ba8",
    "Medium": "#fab387",
    "Low":    "#a6e3a1",
}

DUE_DATE_STYLES = {
    "overdue":  ("🔴", "#f38ba8", "bold"),
    "today":    ("🟢", "#a6e3a1", "bold"),
    "upcoming": ("📅", "#5f9ea0", "normal"),
    "none":     ("",   "#5f9ea0", "normal"),
}


class TaskCard(QWidget):
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_id = task["id"]
        self._drag_start_pos = None
        self._build_ui()

    def _build_ui(self):
        self.setFixedHeight(130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        priority = self.task.get("priority", "Medium")
        color = PRIORITY_COLORS.get(priority, "#cdd6f4")

        self.setStyleSheet(f"""
            TaskCard {{
                background-color: #2a2a3e;
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
            TaskCard:hover {{
                background-color: #313155;
            }}
        """)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(self.task["title"])
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #d6f4cd;")
        title_lbl.setWordWrap(True)
        title_row.addWidget(title_lbl, 1)

        # Priority badge
        badge = QLabel(f" {priority} ")
        badge.setStyleSheet(f"""
            background-color: {color};
            color: #1e1e2e;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            font-weight: bold;
        """)
        title_row.addWidget(badge)
        layout.addLayout(title_row)

        # Description (truncated)
        desc = self.task.get("description", "")
        if desc:
            desc_lbl = QLabel(desc[:60] + ("…" if len(desc) > 60 else ""))
            desc_lbl.setStyleSheet("color: #6c7086; font-size: 11px;")
            layout.addWidget(desc_lbl)

        # Tags
        tags = self.task.get("tags", "")
        if tags:
            tags_row = QHBoxLayout()
            tags_row.setSpacing(4)
            for tag in tags.split(",")[:4]:
                tag = tag.strip()
                if tag:
                    tag_lbl = QLabel(f"#{tag}")
                    tag_lbl.setStyleSheet("""
                        background-color: #45475a;
                        color: #89b4fa;
                        border-radius: 4px;
                        padding: 1px 6px;
                        font-size: 10px;
                    """)
                    tags_row.addWidget(tag_lbl)
            tags_row.addStretch()
            layout.addLayout(tags_row)

        layout.addStretch()

        # Bottom row: due date + action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        due_str    = self.task.get("due_date")
        due_status = get_due_date_status(due_str)

        if due_str:
            icon, due_color, weight = DUE_DATE_STYLES[due_status]
            if due_status == "overdue":
                label = f"{icon} Overdue: {due_str}"
            elif due_status == "today":
                label = f"{icon} Due Today"
            else:
                label = f"📅 {due_str}"

            due_lbl = QLabel(label)
            due_lbl.setStyleSheet(
                f"color: {due_color}; font-size: 10px; font-weight: {weight};"
            )
            btn_row.addWidget(due_lbl)

            if due_status in ("overdue", "today"):
                log.debug("Card #%d has due status '%s'.", self.task_id, due_status)

        btn_row.addStretch()

        edit_btn = QPushButton("")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setStyleSheet("""
            QPushButton { background: #313244; border-radius: 6px; font-size: 13px; }
            QPushButton:hover { background: #45475a; }
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task_id))

        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton { background: #313244; border-radius: 6px; font-size: 13px; }
            QPushButton:hover { background: #f38ba8; }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))

        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    # Drag & Drop 

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(self.task_id))
        drag.setMimeData(mime)

        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(0, 0, 0, 0))
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(self._drag_start_pos)

        drag.exec(Qt.DropAction.MoveAction)
