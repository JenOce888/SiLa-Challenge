"""
Dialogue_Tache.py — VIEW layer.

Add/Edit task form. Talks to TaskModel (not Database directly) — MVC compliant.
Validation errors from the Model are shown as inline UI feedback.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt

from models import TaskModel, ValidationError
from logger import get_logger

log = get_logger(__name__)


class TaskDialog(QDialog):
    def __init__(self, model: TaskModel, task: dict = None, parent=None):
        super().__init__(parent)
        self.model   = model
        self.task    = task
        self.is_edit = task is not None

        self.setWindowTitle("Edit Task" if self.is_edit else "New Task")
        self.setMinimumWidth(420)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel  { color: #cdd6f4; font-size: 13px; }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 6px 10px; font-size: 13px;
            }
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                padding: 8px 18px; font-weight: bold;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#cancelBtn { background-color: #45475a; color: #cdd6f4; }
            QPushButton#cancelBtn:hover { background-color: #585b70; }
            QLabel#errorLbl { color: #f38ba8; font-size: 11px; }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task title…")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (optional)…")
        self.desc_input.setFixedHeight(90)

        self.status_input = QComboBox()
        self.status_input.addItems(["todo", "inprogress", "done"])

        self.priority_input = QComboBox()
        self.priority_input.addItems(["High", "Medium", "Low"])

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3…")

        self.due_input = QLineEdit()
        self.due_input.setPlaceholderText("YYYY-MM-DD (optional)")

        # Inline error label (hidden by default)
        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("errorLbl")
        self.error_lbl.hide()

        form.addRow("Title *",      self.title_input)
        form.addRow("Description",  self.desc_input)
        form.addRow("Status",       self.status_input)
        form.addRow("Priority",     self.priority_input)
        form.addRow("Tags",         self.tags_input)
        form.addRow("Due Date",     self.due_input)

        layout.addLayout(form)
        layout.addWidget(self.error_lbl)

        # Pre-fill for edit mode
        if self.is_edit:
            self.title_input.setText(self.task.get("title", ""))
            self.desc_input.setPlainText(self.task.get("description", ""))
            idx = self.status_input.findText(self.task.get("status", "todo"))
            if idx >= 0:
                self.status_input.setCurrentIndex(idx)
            idx = self.priority_input.findText(self.task.get("priority", "Medium"))
            if idx >= 0:
                self.priority_input.setCurrentIndex(idx)
            self.tags_input.setText(self.task.get("tags", ""))
            self.due_input.setText(self.task.get("due_date") or "")

        # Buttons
        btn_row = QHBoxLayout()
        save_btn   = QPushButton("💾  Save")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _show_error(self, message: str):
        self.error_lbl.setText(f"⚠ {message}")
        self.error_lbl.show()

    def _save(self):
        title    = self.title_input.text().strip()
        desc     = self.desc_input.toPlainText().strip()
        status   = self.status_input.currentText()
        priority = self.priority_input.currentText()
        tags     = ",".join(t.strip() for t in self.tags_input.text().split(",") if t.strip())
        due      = self.due_input.text().strip() or None

        try:
            if self.is_edit:
                # Controller delegates to Model — Model validates + saves
                self.model.update_task(self.task["id"], title, desc, status, priority, tags, due)
            else:
                self.model.create_task(title, desc, status, priority, tags, due)
            self.accept()

        except ValidationError as e:
            # Model rejected the data — show error in View
            self._show_error(str(e))
            log.warning("Validation error in TaskDialog: %s", str(e))
