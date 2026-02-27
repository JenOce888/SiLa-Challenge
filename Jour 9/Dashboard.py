"""
Dashboard.py — VIEW layer.

Displays a statistics dashboard with:
  - Summary stat cards (total, overdue, due today, completion %)
  - Pie chart: tasks by status
  - Bar chart: tasks by priority
  - Uses matplotlib embedded in PyQt6 via FigureCanvasQTAgg
  - Falls back to a plain text view if matplotlib is not installed
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QWidget, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from logger import get_logger

log = get_logger(__name__)

# ── Color palette (matches app theme) ────────────────────────────
STATUS_COLORS   = ["#f38ba8", "#fab387", "#a6e3a1"]   # red, orange, green
PRIORITY_COLORS = ["#f38ba8", "#fab387", "#a6e3a1"]   # red, orange, green
BG_COLOR        = "#f5f5f5"  # light gray background for charts
TEXT_COLOR       = "#f8f8ff"  # off-white text color


def _make_stat_card(label: str, value: str, color: str = "#89b4fa") -> QFrame:
    """Creates a single KPI card widget."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: #2a2a3e;
            border-radius: 10px;
            border-left: 4px solid {color};
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 12, 16, 12)

    val_lbl = QLabel(value)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")

    lbl = QLabel(label)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("font-size: 12px; color: #6c7086;")

    layout.addWidget(val_lbl)
    layout.addWidget(lbl)
    return card


class DashboardDialog(QDialog):
    """
    Dashboard VIEW — opened by the Controller (main.py).
    Receives pre-computed stats dict from TaskModel.get_stats().
    """

    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("Dashboard — Task Statistics")
        self.setMinimumSize(800, 560)
        self.setStyleSheet(f"""
            QDialog  {{ background-color: {BG_COLOR}; }}
            QWidget  {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; font-family: 'Segoe UI', News Times; }}
            QLabel   {{ color: {TEXT_COLOR}; }}
            QPushButton {{
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                padding: 8px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #b4befe; }}
        """)
        log.info("DashboardDialog opened. Stats: %s", stats)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # Header
        header = QLabel("Task Statistics Dashboard")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        root.addWidget(header)

        # KPI Cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        s = self.stats
        cards_row.addWidget(_make_stat_card("Total Tasks",       str(s["total"]),             "#89b4fa"))
        cards_row.addWidget(_make_stat_card("Overdue",           str(s["overdue"]),            "#f38ba8"))
        cards_row.addWidget(_make_stat_card("Due Today",         str(s["due_today"]),          "#a6e3a1"))
        cards_row.addWidget(_make_stat_card("Completion Rate",   f"{s['completion_rate']}%",   "#cba6f7"))
        root.addLayout(cards_row)

        # Charts
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            # Pie chart — by status
            pie_canvas = self._make_pie_chart(FigureCanvasQTAgg, Figure)
            charts_row.addWidget(pie_canvas, 1)

            # Bar chart — by priority
            bar_canvas = self._make_bar_chart(FigureCanvasQTAgg, Figure)
            charts_row.addWidget(bar_canvas, 1)

            log.info("Charts rendered using matplotlib.")

        except ImportError:
            log.warning("matplotlib not installed — showing text fallback for charts.")
            charts_row.addWidget(self._make_text_fallback())

        root.addLayout(charts_row)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _make_pie_chart(self, Canvas, Figure):
        """Pie chart: tasks by status."""
        by_status = self.stats["by_status"]
        labels = ["To Do", "In Progress", "Done"]
        values = [by_status["todo"], by_status["inprogress"], by_status["done"]]

        fig = Figure(figsize=(4, 3.5), facecolor=BG_COLOR)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(BG_COLOR)

        # Only plot non-zero slices
        filtered = [(l, v, c) for l, v, c in zip(labels, values, STATUS_COLORS) if v > 0]
        if filtered:
            fl, fv, fc = zip(*filtered)
            wedges, texts, autotexts = ax.pie(
                fv, labels=fl, colors=fc,
                autopct="%1.0f%%", startangle=90,
                textprops={"color": TEXT_COLOR, "fontsize": 10},
                wedgeprops={"linewidth": 2, "edgecolor": BG_COLOR}
            )
            for at in autotexts:
                at.set_color("#1e1e2e")
                at.set_fontweight("bold")
        else:
            ax.text(0.5, 0.5, "No tasks yet", ha="center", va="center",
                    color=TEXT_COLOR, fontsize=12, transform=ax.transAxes)

        ax.set_title("Tasks by Status", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        return Canvas(fig)

    def _make_bar_chart(self, Canvas, Figure):
        """Bar chart: tasks by priority."""
        by_priority = self.stats["by_priority"]
        labels = ["High", "Medium", "Low"]
        values = [by_priority[l] for l in labels]

        fig = Figure(figsize=(4, 4), facecolor=BG_COLOR)
        ax  = fig.add_subplot(111)
        ax.set_facecolor("#2a2a3e")

        bars = ax.bar(labels, values, color=PRIORITY_COLORS,
                      width=0.5, edgecolor=BG_COLOR, linewidth=2)

        # Value labels on top of each bar
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.1,
                    str(val),
                    ha="center", va="bottom",
                    color=TEXT_COLOR, fontsize=13, fontweight="bold"
                )

        ax.set_title("Tasks by Priority", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
        ax.set_ylabel("Count", color=TEXT_COLOR, fontsize=12)
        ax.tick_params(colors=TEXT_COLOR, labelsize=12)
        ax.spines["bottom"].set_color("#45475a")
        ax.spines["left"].set_color("#45475a")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_ylim(0, max(values or [1]) + 1)
        fig.tight_layout()
        return Canvas(fig)

    def _make_text_fallback(self) -> QWidget:
        """Plain text stats if matplotlib isn't installed."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        s = self.stats
        info = QLabel(
            f"<b>By Status</b><br>"
            f"  To Do: {s['by_status']['todo']}<br>"
            f"  In Progress: {s['by_status']['inprogress']}<br>"
            f"  Done: {s['by_status']['done']}<br><br>"
            f"<b>By Priority</b><br>"
            f"  High: {s['by_priority']['High']}<br>"
            f"  Medium: {s['by_priority']['Medium']}<br>"
            f"  Low: {s['by_priority']['Low']}<br><br>"
            f"<i>Install matplotlib for visual charts:<br>"
            f"pip install matplotlib</i>"
        )
        info.setStyleSheet("font-size: 13px; color: #cdd6f4; line-height: 1.55;")
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)
        layout.addStretch()
        return widget
