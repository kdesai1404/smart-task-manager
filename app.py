"""
Smart Task Management System
Entry point – Flask app with Flask-SocketIO for real-time updates.
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.analytics import analytics_bp

# ── App factory ──────────────────────────────────────────────────────────────

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    # Root redirect
    from flask import redirect, url_for
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


# ── WebSocket events ──────────────────────────────────────────────────────────

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

# Expose socketio to blueprints via app context
app.socketio = socketio


@socketio.on("connect")
def handle_connect():
    print("Client connected via WebSocket")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected from WebSocket")


@socketio.on("join_room")
def handle_join(data):
    from flask_socketio import join_room
    room = data.get("room", "global")
    join_room(room)
    socketio.emit("notification", {"message": f"Joined room: {room}"}, room=room)


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
