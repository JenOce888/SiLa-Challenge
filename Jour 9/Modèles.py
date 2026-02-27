"""
Modèles.py — The MODEL layer of our MVC architecture.

Responsibility:
    - All business logic lives here (validation, date checks, stats)
    - Talks to the Database (data layer) directly
    - Knows NOTHING about PyQt or the UI
    - The Controller (Gestionnaire_Tâche_Avancé_PyQt.py) calls these methods and passes results to Views

MVC Flow in this app:
    User action → Controller (Gestionnaire_Tâche_Avancé_PyQt.py)
                → Model (models.py) — business logic + DB calls
                → View (Carte_Taches.py, Dashboard.py, Dialogue_Tache.py) — renders data
"""

from datetime import date, datetime
from typing import Optional
from database import Database
from logger import get_logger

log = get_logger(__name__)


# Constants 

VALID_STATUSES = {"todo", "inprogress", "done"}
VALID_PRIORITIES = {"High", "Medium", "Low"}
DATE_FORMAT = "%Y-%m-%d"


# Due Date Helpers 

def parse_due_date(due_str: Optional[str]) -> Optional[date]:
    """Parse a YYYY-MM-DD string into a date object. Returns None on failure."""
    if not due_str:
        return None
    try:
        return datetime.strptime(due_str.strip(), DATE_FORMAT).date()
    except ValueError:
        log.warning("Invalid due date format: '%s'. Expected YYYY-MM-DD.", due_str)
        return None


def get_due_date_status(due_str: Optional[str]) -> str:
    """
    Classify a due date relative to today.

    Returns:
        "overdue"  — past due
        "today"    — due today
        "upcoming" — future date
        "none"     — no due date set
    """
    due = parse_due_date(due_str)
    if due is None:
        return "none"

    today = date.today()
    if due < today:
        return "overdue"
    elif due == today:
        return "today"
    else:
        return "upcoming"


# Validation and Business Logic 

class ValidationError(Exception):
    """Raised when task data fails business rule validation."""
    pass


def validate_task(title: str, status: str, priority: str, due_date: str = None):
    """
    Validate task fields before saving.
    Raises ValidationError with a user-friendly message on failure.
    """
    if not title or not title.strip():
        raise ValidationError("Title cannot be empty.")

    if len(title.strip()) > 200:
        raise ValidationError("Title must be 200 characters or fewer.")

    if status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    if priority not in VALID_PRIORITIES:
        raise ValidationError(f"Invalid priority '{priority}'. Must be one of: {VALID_PRIORITIES}")

    if due_date:
        parsed = parse_due_date(due_date)
        if parsed is None:
            raise ValidationError("Due date must be in YYYY-MM-DD format (e.g. 2025-12-31).")


# Task Model (business logic facade over Database) 

class TaskModel:
    """
    The Model in MVC. Encapsulates all task-related business logic.
    Controllers interact with tasks exclusively through this class.
    """

    def __init__(self, db: Database):
        self.db = db
        log.info("TaskModel initialized.")

    # Read 

    def get_all_tasks(self, tag: str = None, priority: str = None, search: str = None) -> list[dict]:
        tasks = self.db.get_tasks(tag=tag, priority=priority, search=search)
        log.debug("Fetched %d tasks (tag=%s, priority=%s, search=%s).", len(tasks), tag, priority, search)
        return tasks

    def get_task(self, task_id: int) -> Optional[dict]:
        task = self.db.get_task_by_id(task_id)
        if task is None:
            log.warning("Task #%d not found.", task_id)
        return task

    def get_all_tags(self) -> list[str]:
        return self.db.get_all_tags()

    # Write 

    def create_task(self, title: str, description: str = "", status: str = "todo",
                    priority: str = "Medium", tags: str = "", due_date: str = None) -> bool:
        """Validate and create a new task. Returns True on success."""
        try:
            validate_task(title, status, priority, due_date)
            self.db.add_task(title.strip(), description.strip(), status, priority, tags, due_date or None)
            log.info("Task created: title='%s', priority=%s, status=%s.", title, priority, status)
            return True
        except ValidationError as e:
            log.error("Task creation failed — %s", str(e))
            raise

    def update_task(self, task_id: int, title: str, description: str,
                    status: str, priority: str, tags: str, due_date: str = None) -> bool:
        """Validate and update an existing task. Returns True on success."""
        try:
            validate_task(title, status, priority, due_date)
            self.db.update_task(task_id, title.strip(), description.strip(), status, priority, tags, due_date or None)
            log.info("Task #%d updated: title='%s', status=%s.", task_id, title, status)
            return True
        except ValidationError as e:
            log.error("Task #%d update failed — %s", task_id, str(e))
            raise

    def move_task(self, task_id: int, new_status: str):
        """Move a task to a new Kanban column."""
        if new_status not in VALID_STATUSES:
            log.error("Invalid status '%s' for task #%d.", new_status, task_id)
            return
        self.db.update_task_status(task_id, new_status)
        log.info("Task #%d moved to '%s'.", task_id, new_status)

    def delete_task(self, task_id: int):
        """Delete a task by ID."""
        self.db.delete_task(task_id)
        log.info("Task #%d deleted.", task_id)

    # Statistics (used by DashboardView)

    def get_stats(self) -> dict:
        """
        Compute dashboard statistics.

        Returns a dict with:
            by_status   — {status: count}
            by_priority — {priority: count}
            total       — int
            overdue     — int
            due_today   — int
            completion_rate — float (0.0–100.0)
        """
        all_tasks = self.db.get_all_tasks()
        total = len(all_tasks)

        by_status = {"todo": 0, "inprogress": 0, "done": 0}
        by_priority = {"High": 0, "Medium": 0, "Low": 0}
        overdue = 0
        due_today = 0

        for task in all_tasks:
            status = task.get("status", "todo")
            priority = task.get("priority", "Medium")

            if status in by_status:
                by_status[status] += 1
            if priority in by_priority:
                by_priority[priority] += 1

            due_status = get_due_date_status(task.get("due_date"))
            if due_status == "overdue" and status != "done":
                overdue += 1
            elif due_status == "today":
                due_today += 1

        completion_rate = (by_status["done"] / total * 100) if total > 0 else 0.0

        stats = {
            "by_status": by_status,
            "by_priority": by_priority,
            "total": total,
            "overdue": overdue,
            "due_today": due_today,
            "completion_rate": round(completion_rate, 1),
        }

        log.debug("Stats computed: %s", stats)
        return stats
