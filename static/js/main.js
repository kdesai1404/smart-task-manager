/* ═══════════════════════════════════════════════════════
   TaskFlow – main.js
   Handles: Task CRUD, Analytics, WebSocket real-time events
   ═══════════════════════════════════════════════════════ */

// ── WebSocket Setup ───────────────────────────────────────────────────────────
const socket = io({ transports: ["websocket", "polling"] });

socket.on("connect", () => {
  socket.emit("join_room", { room: "global" });
  console.log("WebSocket connected:", socket.id);
});

socket.on("task_created", ({ task }) => {
  showToast(`✅ New task added: "${task.title}"`);
  loadTasks();
  loadAnalytics();
});

socket.on("task_updated", ({ task }) => {
  showToast(`✏️ Task updated: "${task.title}"`);
  loadTasks();
  loadAnalytics();
});

socket.on("task_deleted", ({ task }) => {
  showToast(`🗑️ Task deleted: "${task.title}"`);
  loadTasks();
  loadAnalytics();
});

socket.on("notification", ({ message }) => {
  console.log("Server notification:", message);
});

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(message, duration = 3500) {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

function priorityBadge(p) {
  const labels = { low: "🟢 Low", medium: "🟡 Medium", high: "🔴 High" };
  return `<span class="badge badge-${p}">${labels[p] ?? p}</span>`;
}

function statusBadge(s) {
  const labels = { pending: "⏳ Pending", in_progress: "🔵 In Progress", completed: "✅ Done" };
  return `<span class="badge badge-${s}">${labels[s] ?? s}</span>`;
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
}

// ── Analytics ─────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics/");
    const { analytics: a } = await res.json();
    if (!a) return;

    $("statTotal").textContent       = a.total_tasks;
    $("statCompleted").textContent   = a.completed_tasks;
    $("statPending").textContent     = a.pending_tasks;
    $("statInProgress").textContent  = a.in_progress_tasks;
    $("statPct").textContent         = a.completion_percentage + "%";
    $("progressBar").style.width     = a.completion_percentage + "%";
  } catch (err) {
    console.error("Analytics error:", err);
  }
}

// ── Load tasks ────────────────────────────────────────────────────────────────
async function loadTasks() {
  const status   = $("filterStatus").value;
  const priority = $("filterPriority").value;

  const params = new URLSearchParams();
  if (status)   params.append("status", status);
  if (priority) params.append("priority", priority);

  const res   = await fetch(`/api/tasks/?${params}`);
  const { tasks } = await res.json();
  renderTasks(tasks || []);
}

function renderTasks(tasks) {
  const list = $("taskList");

  if (!tasks.length) {
    list.innerHTML = `<p class="empty-state">No tasks yet – add one above!</p>`;
    return;
  }

  list.innerHTML = tasks.map((t) => `
    <div class="task-card priority-${t.priority} status-${t.status}" data-id="${t.id}">
      <div class="task-body">
        <div class="task-title">${escapeHtml(t.title)}</div>
        ${t.description ? `<div class="task-desc">${escapeHtml(t.description)}</div>` : ""}
        <div class="task-meta">
          ${priorityBadge(t.priority)}
          ${statusBadge(t.status)}
          <span class="task-date">📅 ${fmtDate(t.created_at)}</span>
        </div>
      </div>
      <div class="task-actions">
        <button class="btn btn-outline btn-sm" onclick="openEdit(${t.id})">Edit</button>
        <button class="btn btn-danger  btn-sm" onclick="deleteTask(${t.id})">Delete</button>
      </div>
    </div>
  `).join("");
}

// ── Create task ───────────────────────────────────────────────────────────────
async function createTask() {
  const errEl = $("taskError");
  errEl.classList.add("hidden");

  const title    = $("taskTitle").value.trim();
  const desc     = $("taskDesc").value.trim();
  const priority = $("taskPriority").value;

  if (!title) {
    errEl.textContent = "Title is required.";
    errEl.classList.remove("hidden");
    return;
  }

  const res = await fetch("/api/tasks/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description: desc, priority }),
  });

  const data = await res.json();
  if (data.success) {
    $("taskTitle").value = "";
    $("taskDesc").value  = "";
    $("taskPriority").value = "medium";
    // WebSocket will trigger loadTasks + loadAnalytics
  } else {
    errEl.textContent = (data.errors || ["Error creating task."]).join(" ");
    errEl.classList.remove("hidden");
  }
}

// ── Delete task ───────────────────────────────────────────────────────────────
async function deleteTask(id) {
  if (!confirm("Delete this task?")) return;
  await fetch(`/api/tasks/${id}`, { method: "DELETE" });
  // WebSocket handles refresh
}

// ── Edit modal ────────────────────────────────────────────────────────────────
async function openEdit(id) {
  const res  = await fetch(`/api/tasks/${id}`);
  const { task } = await res.json();
  if (!task) return;

  $("editId").value          = task.id;
  $("editTitle").value       = task.title;
  $("editDesc").value        = task.description || "";
  $("editPriority").value    = task.priority;
  $("editStatus").value      = task.status;

  $("editModal").classList.remove("hidden");
}

function closeModal() {
  $("editModal").classList.add("hidden");
}

async function saveEdit() {
  const id = $("editId").value;
  const res = await fetch(`/api/tasks/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title:       $("editTitle").value.trim(),
      description: $("editDesc").value.trim(),
      priority:    $("editPriority").value,
      status:      $("editStatus").value,
    }),
  });

  const data = await res.json();
  if (data.success) {
    closeModal();
    // WebSocket handles refresh
  } else {
    alert((data.errors || ["Update failed."]).join("\n"));
  }
}

// ── XSS helper ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const d = document.createElement("div");
  d.appendChild(document.createTextNode(str));
  return d.innerHTML;
}

// ── Allow Enter key on task title ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const titleInput = $("taskTitle");
  if (titleInput) {
    titleInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") createTask();
    });
  }
  loadAnalytics();
  loadTasks();
});
