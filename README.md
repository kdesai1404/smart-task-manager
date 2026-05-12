# ✅ TaskFlow – Smart Task Management System

A full-stack task management web application built with **Flask**, **PostgreSQL**, **Pandas/NumPy**, **WebSockets**, and a clean responsive **HTML/CSS** frontend.

---

## 🚀 Features

| Feature | Details |
|---|---|
| **Authentication** | Register, Login, Logout (session-based with Flask-Login) |
| **Task CRUD** | Add, view, edit, delete tasks via REST API |
| **Task Fields** | Title, Description, Priority (low/medium/high), Status, Created Date |
| **PostgreSQL** | Users & Tasks stored in a relational DB with proper indexing |
| **Analytics** | Pandas + NumPy: total, completed, pending, completion % |
| **WebSockets** | Live real-time task notifications via Flask-SocketIO |
| **Frontend** | Responsive HTML/CSS dashboard with filters and edit modal |

---

## 📁 Project Structure

```
smart-task-manager/
├── app.py                   # Flask app + SocketIO entry point
├── config.py                # App configuration (env-based)
├── models.py                # SQLAlchemy models: User, Task
├── routes/
│   ├── auth.py              # /auth/register, /auth/login, /auth/logout
│   ├── tasks.py             # /api/tasks/ CRUD endpoints + /dashboard
│   └── analytics.py         # /api/analytics/  (Pandas + NumPy)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
├── static/
│   ├── css/style.css
│   └── js/main.js           # WebSocket client + fetch API calls
├── schema.sql               # Raw SQL schema (optional, ORM creates tables)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/smart-task-manager.git
cd smart-task-manager
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY and DATABASE_URL
```

### 5. Set up PostgreSQL

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE task_manager;"

# (Optional) Apply the raw schema manually
psql -U postgres -d task_manager -f schema.sql
```

> The ORM will auto-create tables on first run, so step 5 is optional if you use SQLAlchemy's `db.create_all()`.

### 6. Run the application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🌐 REST API Reference

All task endpoints require authentication (session cookie).

| Method | URL | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login |
| `GET` | `/auth/logout` | Logout |
| `GET` | `/api/tasks/` | Get all tasks (supports `?status=` & `?priority=`) |
| `POST` | `/api/tasks/` | Create a new task |
| `GET` | `/api/tasks/<id>` | Get a single task |
| `PUT` | `/api/tasks/<id>` | Update a task |
| `DELETE` | `/api/tasks/<id>` | Delete a task |
| `GET` | `/api/analytics/` | Get analytics summary |

### Example – Create Task

```bash
curl -X POST http://localhost:5000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Write tests", "priority": "high", "description": "Unit tests for auth"}'
```

---

## 🔌 WebSocket Events

| Event (server → client) | Payload |
|---|---|
| `task_created` | `{ task: TaskObject }` |
| `task_updated` | `{ task: TaskObject }` |
| `task_deleted` | `{ task_id, task: TaskObject }` |
| `notification` | `{ message: string }` |

---

## 📊 Analytics Response

```json
{
  "analytics": {
    "total_tasks": 12,
    "completed_tasks": 5,
    "pending_tasks": 4,
    "in_progress_tasks": 3,
    "completion_percentage": 41.67,
    "priority_breakdown": { "low": 2, "medium": 7, "high": 3 },
    "status_breakdown": { "pending": 4, "in_progress": 3, "completed": 5 },
    "avg_tasks_per_day": 2.4
  }
}
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask 3, Flask-Login, Flask-SocketIO
- **Database**: PostgreSQL 15+, Flask-SQLAlchemy, psycopg2
- **Analytics**: Pandas 2, NumPy 1.26
- **Real-time**: WebSockets via Flask-SocketIO + Socket.IO (client)
- **Frontend**: Vanilla HTML5, CSS3 (no framework), JavaScript (Fetch API)

---

## 📝 License

MIT – for educational purposes.
