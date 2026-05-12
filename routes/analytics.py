"""
Analytics blueprint – uses Pandas & NumPy to compute task statistics.

Endpoint
--------
GET /api/analytics/  – returns summary stats for the current user's tasks
"""

import numpy as np
import pandas as pd

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from models import Task, Status, Priority

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/", methods=["GET"])
@login_required
def get_analytics():
    """
    Build a Pandas DataFrame from the user's tasks and use NumPy
    to compute aggregated statistics returned as JSON.
    """
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    if not tasks:
        return jsonify({
            "success": True,
            "analytics": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "in_progress_tasks": 0,
                "completion_percentage": 0.0,
                "priority_breakdown": {},
                "status_breakdown": {},
                "avg_tasks_per_day": 0.0,
            }
        })

    # ── Build DataFrame ───────────────────────────────────────────────────────
    records = [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "status": t.status,
            "created_at": pd.Timestamp(t.created_at),
        }
        for t in tasks
    ]
    df = pd.DataFrame(records)

    # ── Core counts (NumPy) ───────────────────────────────────────────────────
    total = int(np.int64(len(df)))
    completed = int(np.sum(df["status"] == Status.COMPLETED))
    pending = int(np.sum(df["status"] == Status.PENDING))
    in_progress = int(np.sum(df["status"] == Status.IN_PROGRESS))

    completion_pct = float(
        np.round((completed / total) * 100, 2) if total > 0 else 0.0
    )

    # ── Priority breakdown ────────────────────────────────────────────────────
    priority_counts = (
        df.groupby("priority")["id"]
        .count()
        .reindex(Priority.CHOICES, fill_value=0)
        .to_dict()
    )
    priority_breakdown = {k: int(v) for k, v in priority_counts.items()}

    # ── Status breakdown ──────────────────────────────────────────────────────
    status_counts = (
        df.groupby("status")["id"]
        .count()
        .reindex(Status.CHOICES, fill_value=0)
        .to_dict()
    )
    status_breakdown = {k: int(v) for k, v in status_counts.items()}

    # ── Average tasks created per day ─────────────────────────────────────────
    df["date"] = df["created_at"].dt.date
    tasks_per_day = df.groupby("date")["id"].count()
    avg_per_day = float(np.round(tasks_per_day.mean(), 2))

    return jsonify({
        "success": True,
        "analytics": {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "completion_percentage": completion_pct,
            "priority_breakdown": priority_breakdown,
            "status_breakdown": status_breakdown,
            "avg_tasks_per_day": avg_per_day,
        }
    })
