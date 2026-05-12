"""
Authentication blueprint – register, login, logout.
Serves both HTML pages and JSON responses.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User

auth_bp = Blueprint("auth", __name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def _wants_json() -> bool:
    """Return True when the client prefers JSON (API call)."""
    return request.is_json or request.headers.get("Accept") == "application/json"


# ── Registration ──────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.dashboard"))

    if request.method == "POST":
        data = request.get_json() if _wants_json() else request.form

        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        # ── Validation ────────────────────────────────────────────────────────
        errors = []
        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            if _wants_json():
                return jsonify({"success": False, "errors": errors}), 400
            for err in errors:
                flash(err, "danger")
            return render_template("register.html"), 400

        # ── Create user ───────────────────────────────────────────────────────
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)

        if _wants_json():
            return jsonify({"success": True, "user": user.to_dict()}), 201

        flash("Account created! Welcome 🎉", "success")
        return redirect(url_for("tasks.dashboard"))

    return render_template("register.html")


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.dashboard"))

    if request.method == "POST":
        data = request.get_json() if _wants_json() else request.form

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        remember = bool(data.get("remember", False))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            msg = "Invalid email or password."
            if _wants_json():
                return jsonify({"success": False, "error": msg}), 401
            flash(msg, "danger")
            return render_template("login.html"), 401

        login_user(user, remember=remember)

        if _wants_json():
            return jsonify({"success": True, "user": user.to_dict()})

        next_page = request.args.get("next")
        return redirect(next_page or url_for("tasks.dashboard"))

    return render_template("login.html")


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    if _wants_json():
        return jsonify({"success": True, "message": "Logged out."})
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
