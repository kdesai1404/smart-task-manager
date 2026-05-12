"""
Tasks blueprint – CRUD REST API + dashboard page.

Endpoints
---------
GET    /api/tasks/          – list all tasks for current user
POST   /api/tasks/          – create a new task
GET    /api/tasks/<id>      – get a single task
PUT    /api/tasks/<id>      – update a task
DELETE /api/tasks/<id>      – delete a task
GET    /dashboard           – render the main dashboard (HTML)
"""

from datetime import datetime, timezone

from flask import (
    Blueprint,
    jsonify,
    request,
    render_template,
    current_app,
)
from flask_login import login_required, current_user

from models import db, Task, Priority, Status

tasks_bp = Blueprint("tasks", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _emit_task_event(event: str, payload: dict) -> None:
    """Emit a WebSocket event if SocketIO is attached to the app."""
    socketio = getattr(current_app, "socketio", None)
    if socketio:
        socketio.emit(event, payload, room="global")


def _validate_task_data(data: dict, require_title: bool = True) -> list[str]:
    errors = []
    title = (data.get("title") or "").strip()
    if require_title and not title:
        errors.append("Title is required.")
    priority = data.get("priority")
    if priority and priority not in Priority.CHOICES:
        errors.append(f"Priority must be one of: {', '.join(Priority.CHOICES)}.")
    status = data.get("status")
    if status and status not in Status.CHOICES:
        errors.append(f"Status must be one of: {', '.join(Status.CHOICES)}.")
    return errors


# ── Dashboard (HTML) ──────────────────────────────────────────────────────────

@tasks_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# ── GET all tasks ─────────────────────────────────────────────────────────────

@tasks_bp.route("/", methods=["GET"])
@login_required
def get_tasks():
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")

    query = Task.query.filter_by(user_id=current_user.id)

    if status_filter and status_filter in Status.CHOICES:
        query = query.filter_by(status=status_filter)
    if priority_filter and priority_filter in Priority.CHOICES:
        query = query.filter_by(priority=priority_filter)

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify({"success": True, "tasks": [t.to_dict() for t in tasks]})


# ── GET single task ───────────────────────────────────────────────────────────

@tasks_bp.route("/<int:task_id>", methods=["GET"])
@login_required
def get_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    return jsonify({"success": True, "task": task.to_dict()})


# ── POST create task ──────────────────────────────────────────────────────────

@tasks_bp.route("/", methods=["POST"])
@login_required
def create_task():
    data = request.get_json(silent=True) or {}

    errors = _validate_task_data(data, require_title=True)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    task = Task(
        title=data["title"].strip(),
        description=(data.get("description") or "").strip() or None,
        priority=data.get("priority", Priority.MEDIUM),
        status=data.get("status", Status.PENDING),
        user_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()

    _emit_task_event("task_created", {"task": task.to_dict()})

    return jsonify({"success": True, "task": task.to_dict()}), 201


# ── PUT update task ───────────────────────────────────────────────────────────

@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    errors = _validate_task_data(data, require_title=False)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    if "title" in data and data["title"].strip():
        task.title = data["title"].strip()
    if "description" in data:
        task.description = (data["description"] or "").strip() or None
    if "priority" in data:
        task.priority = data["priority"]
    if "status" in data:
        task.status = data["status"]

    task.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    _emit_task_event("task_updated", {"task": task.to_dict()})

    return jsonify({"success": True, "task": task.to_dict()})


# ── DELETE task ───────────────────────────────────────────────────────────────

@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task_data = task.to_dict()

    db.session.delete(task)
    db.session.commit()

    _emit_task_event("task_deleted", {"task_id": task_id, "task": task_data})

    return jsonify({"success": True, "message": f"Task {task_id} deleted."})
