(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const page = document.body.dataset.page || "";

  let applications = [], companies = [], allApplications = [], allTasks = [];

  const esc = (value) =>
    String(value ?? "").replace(/[&<>"']/g, ch => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[ch]));

  const dateText = value => {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime())
      ? esc(value)
      : d.toLocaleString([], {
          dateStyle: "medium",
          timeStyle: value.includes("T") ? "short" : undefined
        });
  };

  const dateOnly = value => value ? String(value).slice(0, 10) : "—";

  function toast(message, isError = false) {
    const el = $("#toast");
    if (!el) return;

    el.textContent = message;
    el.className = "toast show" + (isError ? " error" : "");

    window.setTimeout(() => el.classList.remove("show"), 3200);
  }

  async function api(url, options = {}) {
    const opts = {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {})
      }
    };

    const response = await fetch(url, opts);
    let data = {};

    try {
      data = await response.json();
    } catch (_) {}

    if (
      response.status === 401 &&
      !["login", "register"].includes(page)
    ) {
      window.location.href = "/login";
      throw new Error("Please sign in again.");
    }

    if (!response.ok) {
      throw new Error(
        data.error || data.message || `Request failed (${response.status})`
      );
    }

    return data;
  }

  const formData = form => Object.fromEntries(new FormData(form).entries());
  const jsonBody = data => JSON.stringify(data);

  function statusPill(status) {
    const cls = String(status || "")
      .toLowerCase()
      .replace(/[^a-z]+/g, "-");

    return `<span class="pill pill-${esc(cls)}">${esc(status || "—")}</span>`;
  }

  function actionButtons(id, type) {
    return `
      <div class="row-actions">
        <button class="action-btn"
          data-action="edit"
          data-type="${type}"
          data-id="${id}">Edit</button>
        <button class="action-btn danger-text"
          data-action="delete"
          data-type="${type}"
          data-id="${id}">Delete</button>
      </div>`;
  }

  function emptyRow(message, cols) {
    return `<tr><td colspan="${cols}" class="empty-cell">${esc(message)}</td></tr>`;
  }

  function renderApplications(items) {
    const holder = $("#applications-table");
    if (!holder) return;

    $("#application-count").textContent =
      `${items.length} application${items.length === 1 ? "" : "s"}`;

    holder.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Company / role</th>
            <th>Type</th>
            <th>Applied</th>
            <th>Status</th>
            <th>Location</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${items.length ? items.map(a => `
            <tr>
              <td>
                <strong>${esc(a.company_name)}</strong>
                <small class="cell-sub">${esc(a.job_role)}</small>
                ${a.job_link
                  ? `<a class="cell-sub" href="${esc(a.job_link)}"
                       target="_blank" rel="noopener">View job ↗</a>`
                  : ""}
              </td>
              <td>${esc(a.job_type || "—")}</td>
              <td>${dateOnly(a.application_date)}</td>
              <td>${statusPill(a.status)}</td>
              <td>${esc(a.location || "—")}</td>
              <td>${actionButtons(a.application_id, "application")}</td>
            </tr>
          `).join("") : emptyRow(
            "No applications yet. Add your first opportunity above.",
            6
          )}
        </tbody>
      </table>`;
  }

  async function loadApplications() {
    allApplications = await api("/api/applications");
    applications = allApplications;

    const selects = $$(".application-select");

    selects.forEach(select => {
      const old = select.value;
      const general =
        select.querySelector('option[value=""]')?.textContent ||
        "Choose application";

      select.innerHTML =
        `<option value="">${esc(general)}</option>` +
        allApplications.map(a => `
          <option value="${a.application_id}">
            ${esc(a.company_name)} — ${esc(a.job_role)}
          </option>
        `).join("");

      if (old) select.value = old;
    });

    if (page === "applications") filterApplications();

    return allApplications;
  }

  function filterApplications() {
    const q = ($("#application-search")?.value || "").toLowerCase();
    const status = $("#application-filter")?.value || "";

    renderApplications(
      allApplications.filter(a =>
        (!status || a.status === status) &&
        `${a.company_name} ${a.job_role} ${a.location || ""}`
          .toLowerCase()
          .includes(q)
      )
    );
  }

  async function loadCompanies() {
    companies = await api("/api/companies");
    return companies;
  }

  async function findOrCreateCompany(name, location) {
    await loadCompanies();

    let company = companies.find(
      c => c.company_name.trim().toLowerCase() === name.trim().toLowerCase()
    );

    if (!company) {
      try {
        const result = await api("/api/companies", {
          method: "POST",
          body: jsonBody({
            company_name: name,
            location: location || ""
          })
        });

        company = {
          company_id: result.company_id,
          company_name: name,
          location
        };
      } catch (error) {
        await loadCompanies();

        company = companies.find(
          c => c.company_name.trim().toLowerCase() === name.trim().toLowerCase()
        );

        if (!company) throw error;
      }
    }

    return company;
  }

  async function saveApplication(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const data = formData(form);
    const id = data.application_id;

    try {
      if (id) {
        const old = allApplications.find(
          a => String(a.application_id) === String(id)
        );

        await api(`/api/applications/${id}`, {
          method: "PUT",
          body: jsonBody({
            job_role: data.job_role,
            job_type: data.job_type || null,
            job_link: data.job_link || null,
            application_date: data.application_date || null,
            status: data.status,
            location: data.location || null,
            salary: data.salary || null,
            notes: data.notes || null
          })
        });

        toast(`Updated ${old?.company_name || "application"}.`);
      } else {
        const company = await findOrCreateCompany(
          data.company_name,
          data.location
        );

        await api("/api/applications", {
          method: "POST",
          body: jsonBody({
            company_id: company.company_id,
            job_role: data.job_role,
            job_type: data.job_type || null,
            job_link: data.job_link || null,
            application_date: data.application_date || null,
            status: data.status,
            location: data.location || null,
            salary: data.salary || null,
            notes: data.notes || null
          })
        });

        toast("Application saved successfully.");
      }

      form.reset();
      form.elements.application_id.value = "";
      setApplicationEditMode(false);

      await loadApplications();

      if (page === "dashboard") await loadDashboard();
    } catch (e) {
      toast(e.message, true);
    }
  }

  function setApplicationEditMode(editing) {
    const heading = $("#application-form-heading");
    const submit = $("#application-submit");
    const companyInput = $("#application-form")?.elements.company_name;

    if (!heading || !submit || !companyInput) return;

    heading.textContent = editing ? "Edit application" : "Add an application";
    submit.textContent = editing ? "Save changes" : "Save application";

    $("#application-cancel")?.classList.toggle("hidden", !editing);

    companyInput.disabled = editing;
    companyInput.placeholder = editing
      ? "Company can't be changed here"
      : "e.g. HPE";
  }

  async function loadDashboard() {
    const [apps, assessments, interviews, tasks] = await Promise.all([
      api("/api/applications"),
      api("/api/assessments"),
      api("/api/interviews"),
      api("/api/tasks")
    ]);

    allApplications = apps;
    allTasks = tasks;

    const active = apps.filter(
      a => !["Offer", "Rejected", "Withdrawn"].includes(a.status)
    );

    const today = new Date();
    const upcoming = value =>
      value && new Date(value) >= new Date(today.toDateString());

    $("#stat-total").textContent = apps.length;
    $("#stat-active").textContent = active.length;

    $("#stat-oa").textContent = assessments.filter(
      a => a.status === "Scheduled" && upcoming(a.assessment_date)
    ).length;

    $("#stat-interviews").textContent = interviews.filter(
      i => i.status === "Scheduled" && upcoming(i.interview_date)
    ).length;

    $("#stat-offers").textContent =
      apps.filter(a => a.status === "Offer").length;

    $("#stat-rejections").textContent =
      apps.filter(a => a.status === "Rejected").length;

    const recent = $("#recent-applications");

    recent.innerHTML = `
      <table>
        <thead>
          <tr><th>Company / role</th><th>Status</th><th>Applied</th></tr>
        </thead>
        <tbody>
          ${apps.slice(0, 5).map(a => `
            <tr>
              <td>
                <strong>${esc(a.company_name)}</strong>
                <small class="cell-sub">${esc(a.job_role)}</small>
              </td>
              <td>${statusPill(a.status)}</td>
              <td>${dateOnly(a.application_date)}</td>
            </tr>
          `).join("") || emptyRow("Your applications will appear here.", 3)}
        </tbody>
      </table>`;

    const taskBox = $("#dashboard-tasks");
    const todo = tasks.filter(t => t.status !== "Completed").slice(0, 5);

    taskBox.innerHTML = todo.length
      ? todo.map(t => `
          <div class="task-preview-row">
            <span class="task-check ${t.status === "In Progress" ? "in-progress" : ""}">
              ${t.status === "In Progress" ? "↻" : "○"}
            </span>
            <div>
              <strong>${esc(t.task_title)}</strong>
              <small>${esc(t.company_name || "General task")} · Due ${dateOnly(t.due_date)}</small>
            </div>
            <button class="icon-action"
              data-action="complete-task"
              data-id="${t.task_id}"
              title="Mark completed">✓</button>
          </div>
        `).join("")
      : `
          <div class="empty-state">
            <span>✓</span>
            <strong>All caught up</strong>
            <p>Add a preparation task when you need a next step.</p>
          </div>`;
  }

  async function loadAssessments() {
    const items = await api("/api/assessments");
    const box = $("#assessments-table");
    if (!box) return;

    box.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Assessment</th>
            <th>Company / role</th>
            <th>Date</th>
            <th>Platform</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(x => `
            <tr>
              <td>
                <strong>${esc(x.assessment_name)}</strong>
                <small class="cell-sub">${esc(x.notes || "")}</small>
              </td>
              <td>
                ${esc(x.company_name)}
                <small class="cell-sub">${esc(x.job_role)}</small>
              </td>
              <td>${dateText(x.assessment_date)}</td>
              <td>${esc(x.platform || "—")}</td>
              <td>
                <select class="inline-status"
                  data-action="assessment-status"
                  data-id="${x.assessment_id}">
                  ${["Scheduled", "Completed", "Missed"].map(s =>
                    `<option ${s === x.status ? "selected" : ""}>${s}</option>`
                  ).join("")}
                </select>
              </td>
              <td>
                <button class="action-btn danger-text"
                  data-action="delete"
                  data-type="assessment"
                  data-id="${x.assessment_id}">Delete</button>
              </td>
            </tr>
          `).join("") || emptyRow("No assessments added yet.", 6)}
        </tbody>
      </table>`;
  }

  async function loadInterviews() {
    const items = await api("/api/interviews");
    const box = $("#interviews-table");
    if (!box) return;

    box.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Company / role</th>
            <th>Round</th>
            <th>Date & time</th>
            <th>Mode</th>
            <th>Meeting</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(x => `
            <tr>
              <td>
                <strong>${esc(x.company_name)}</strong>
                <small class="cell-sub">${esc(x.job_role)}</small>
              </td>
              <td>
                ${esc(x.interview_type)}
                ${x.interviewer_name
                  ? `<small class="cell-sub">${esc(x.interviewer_name)}</small>`
                  : ""}
              </td>
              <td>${dateText(x.interview_date)}</td>
              <td>${esc(x.mode)}</td>
              <td>
                ${x.meeting_link
                  ? `<a href="${esc(x.meeting_link)}" target="_blank" rel="noopener">Open link ↗</a>`
                  : "—"}
              </td>
              <td>
                <select class="inline-status"
                  data-action="interview-status"
                  data-id="${x.interview_id}">
                  ${["Scheduled", "Completed", "Cancelled"].map(s =>
                    `<option ${s === x.status ? "selected" : ""}>${s}</option>`
                  ).join("")}
                </select>
              </td>
              <td>
                <button class="action-btn danger-text"
                  data-action="delete"
                  data-type="interview"
                  data-id="${x.interview_id}">Delete</button>
              </td>
            </tr>
            ${x.feedback ? `
              <tr class="detail-row">
                <td colspan="7">
                  <span class="muted">Notes:</span> ${esc(x.feedback)}
                </td>
              </tr>
            ` : ""}
          `).join("") || emptyRow("No interviews scheduled yet.", 7)}
        </tbody>
      </table>`;
  }

  async function loadTasks() {
    allTasks = await api("/api/tasks");

    const box = $("#tasks-table");
    if (!box) return;

    const filter = $("#task-filter")?.value || "";
    const items = allTasks.filter(t => !filter || t.status === filter);

    box.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Task</th>
            <th>Application</th>
            <th>Due date</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(t => `
            <tr>
              <td>
                <strong>${esc(t.task_title)}</strong>
                <small class="cell-sub">${esc(t.description || "")}</small>
              </td>
              <td>
                ${esc(t.company_name || "General task")}
                ${t.job_role ? `<small class="cell-sub">${esc(t.job_role)}</small>` : ""}
              </td>
              <td>${dateOnly(t.due_date)}</td>
              <td>${statusPill(t.priority)}</td>
              <td>
                <select class="inline-status"
                  data-action="task-status"
                  data-id="${t.task_id}">
                  ${["Pending", "In Progress", "Completed"].map(s =>
                    `<option ${s === t.status ? "selected" : ""}>${s}</option>`
                  ).join("")}
                </select>
              </td>
              <td>${actionButtons(t.task_id, "task")}</td>
            </tr>
          `).join("") || emptyRow("No tasks match this filter.", 6)}
        </tbody>
      </table>`;
  }

  // Load saved notes and render the inline editor within each note card.
  async function loadNotes() {
    const items = await api("/api/notes");
    const box = $("#notes-list");
    if (!box) return;

    box.innerHTML = items.map(n => `
      <article class="note-card" data-note-card="${n.note_id}">
        <div class="note-display">
          <div class="note-card-top">
            <span class="note-icon">▧</span>
            <span class="note-date">${dateText(n.updated_at || n.created_at)}</span>
          </div>

          <h3>${esc(n.note_title || "Untitled note")}</h3>
          <p class="note-related">${esc(n.company_name)} · ${esc(n.job_role)}</p>
          <div class="note-content">${esc(n.note_content)}</div>

          <div class="note-actions">
            <button type="button" class="action-btn"
              data-action="edit" data-type="note" data-id="${n.note_id}">Edit</button>
            <button type="button" class="action-btn danger-text"
              data-action="delete" data-type="note" data-id="${n.note_id}">Delete</button>
          </div>
        </div>

        <form class="note-edit-form hidden" data-id="${n.note_id}">
          <label>Note title
            <input type="text" name="note_title"
              value="${esc(n.note_title || "")}"
              maxlength="255" required>
          </label>

          <label>Note content
            <textarea name="note_content" rows="5" required>${esc(n.note_content || "")}</textarea>
          </label>

          <div class="note-actions">
            <button type="submit" class="btn btn-primary">Save changes</button>
            <button type="button" class="btn btn-secondary"
              data-action="cancel-note">Cancel</button>
          </div>
        </form>
      </article>
    `).join("") || `
      <div class="empty-state">
        <span>▧</span>
        <strong>No notes yet</strong>
        <p>Save details from recruiter calls and role research.</p>
      </div>`;
  }

  async function handleForm(form, endpoint, reload) {
    form.addEventListener("submit", async e => {
      e.preventDefault();

      const data = formData(form);

      if ("application_id" in data && data.application_id === "") {
        data.application_id = null;
      }

      if (data.graduation_year === "") {
        data.graduation_year = null;
      }

      try {
        await api(endpoint, {
          method: "POST",
          body: jsonBody(data)
        });

        form.reset();
        toast("Saved successfully.");
        await reload();
      } catch (err) {
        toast(err.message, true);
      }
    });
  }

  async function handleClick(e) {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    const action = btn.dataset.action;
    const id = btn.dataset.id;
    const type = btn.dataset.type;

    try {
      if (action === "complete-task") {
        await api(`/api/tasks/${id}`, {
          method: "PUT",
          body: jsonBody({ status: "Completed" })
        });

        await loadDashboard();
        toast("Task marked completed.");
        return;
      }

      if (action === "delete") {
        const labels = {
          application: "application",
          assessment: "assessment",
          interview: "interview",
          task: "task",
          note: "note"
        };

        if (!window.confirm(
          `Delete this ${labels[type] || "item"}? This cannot be undone.`
        )) return;

        const endpoint = {
          application: "applications",
          assessment: "assessments",
          interview: "interviews",
          task: "tasks",
          note: "notes"
        }[type];

        await api(`/api/${endpoint}/${id}`, { method: "DELETE" });
        toast("Deleted successfully.");

        if (type === "application") {
          await loadApplications();
          if (page === "dashboard") await loadDashboard();
        }

        if (type === "assessment") await loadAssessments();
        if (type === "interview") await loadInterviews();

        if (type === "task") {
          await loadTasks();
          if (page === "dashboard") await loadDashboard();
        }

        if (type === "note") await loadNotes();
      }

      if (action === "edit" && type === "application") {
        const a = allApplications.find(
          x => String(x.application_id) === String(id)
        );
        if (!a) return;

        const form = $("#application-form");

        Object.entries({
          application_id: a.application_id,
          company_name: a.company_name,
          job_role: a.job_role,
          job_type: a.job_type || "",
          status: a.status,
          application_date: dateOnly(a.application_date) === "—"
            ? ""
            : dateOnly(a.application_date),
          location: a.location || "",
          job_link: a.job_link || "",
          salary: a.salary || "",
          notes: a.notes || ""
        }).forEach(([k, v]) => {
          if (form.elements[k]) form.elements[k].value = v;
        });

        setApplicationEditMode(true);
        form.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      if (action === "edit" && type === "task") {
        const t = allTasks.find(
          x => String(x.task_id) === String(id)
        );
        if (!t) return;

        const form = $("#task-form");

        Object.entries({
          task_title: t.task_title,
          application_id: t.application_id || "",
          due_date: dateOnly(t.due_date) === "—" ? "" : dateOnly(t.due_date),
          priority: t.priority,
          status: t.status,
          description: t.description || ""
        }).forEach(([k, v]) => {
          if (form.elements[k]) form.elements[k].value = v;
        });

        form.dataset.editId = id;
        form.querySelector('button[type="submit"]').textContent =
          "Save task changes";

        form.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      // Open the inline note editor instead of browser prompt popups.
      if (action === "edit" && type === "note") {
        const card = document.querySelector(`[data-note-card="${id}"]`);
        if (!card) return;

        card.querySelector(".note-display").classList.add("hidden");
        card.querySelector(".note-edit-form").classList.remove("hidden");
        card.querySelector('input[name="note_title"]').focus();
        return;
      }

      // Cancel note editing without saving.
      if (action === "cancel-note") {
        const card = btn.closest("[data-note-card]");
        if (!card) return;

        card.querySelector(".note-edit-form").classList.add("hidden");
        card.querySelector(".note-display").classList.remove("hidden");
        return;
      }

    } catch (err) {
      toast(err.message, true);
    }
  }

  document.addEventListener("click", handleClick);

  // Save edited note content using the existing Flask API.
  document.addEventListener("submit", async e => {
    const form = e.target;

    if (!form.matches(".note-edit-form")) return;

    e.preventDefault();

    const id = form.dataset.id;
    const data = formData(form);

    data.note_title = data.note_title.trim();
    data.note_content = data.note_content.trim();

    if (!data.note_title || !data.note_content) {
      toast("Please enter a note title and content.", true);
      return;
    }

    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    submit.textContent = "Saving...";

    try {
      await api(`/api/notes/${id}`, {
        method: "PUT",
        body: jsonBody({
          note_title: data.note_title,
          note_content: data.note_content
        })
      });

      await loadNotes();
      toast("Note updated successfully.");

    } catch (err) {
      toast(err.message, true);
      submit.disabled = false;
      submit.textContent = "Save changes";
    }
  });

  document.addEventListener("change", async e => {
    const el = e.target;
    const action = el.dataset.action;
    const id = el.dataset.id;

    try {
      if (action === "assessment-status") {
        await api(`/api/assessments/${id}`, {
          method: "PUT",
          body: jsonBody({ status: el.value })
        });
        toast("Assessment status updated.");
      }

      if (action === "interview-status") {
        await api(`/api/interviews/${id}`, {
          method: "PUT",
          body: jsonBody({ status: el.value })
        });
        toast("Interview status updated.");
      }

      if (action === "task-status") {
        await api(`/api/tasks/${id}`, {
          method: "PUT",
          body: jsonBody({ status: el.value })
        });

        await loadTasks();
        toast("Task status updated.");
      }

      if (el.id === "application-filter" || el.id === "task-filter") {
        if (el.id === "application-filter") {
          filterApplications();
        } else {
          loadTasks();
        }
      }

    } catch (err) {
      toast(err.message, true);
    }
  });

  if ($("#today-label")) {
    $("#today-label").textContent = new Date().toLocaleDateString([], {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  }

  $$("[data-nav]").forEach(a => {
    if (a.dataset.nav === page) a.classList.add("active");
  });

  if ($("#logout-button")) {
    $("#logout-button").addEventListener("click", async () => {
      try {
        await api("/api/logout", { method: "POST" });
        window.location.href = "/login";
      } catch (e) {
        toast(e.message, true);
      }
    });
  }

  if ($("#login-form")) {
    $("#login-form").addEventListener("submit", async e => {
      e.preventDefault();

      const form = e.currentTarget;

      try {
        await api("/api/login", {
          method: "POST",
          body: jsonBody(formData(form))
        });

        window.location.href = "/dashboard";
      } catch (err) {
        $("#auth-error").textContent = err.message;
      }
    });
  }

  if ($("#register-form")) {
    $("#register-form").addEventListener("submit", async e => {
      e.preventDefault();

      const form = e.currentTarget;
      const data = formData(form);

      if (!data.graduation_year) data.graduation_year = null;

      try {
        await api("/api/register", {
          method: "POST",
          body: jsonBody(data)
        });

        toast("Account created. Please sign in.");
        window.location.href = "/login";
      } catch (err) {
        $("#auth-error").textContent = err.message;
      }
    });
  }

  if ($("#application-form")) {
    $("#application-form").addEventListener("submit", saveApplication);

    $("#application-cancel").addEventListener("click", () => {
      const f = $("#application-form");
      f.reset();
      f.elements.application_id.value = "";
      setApplicationEditMode(false);
    });

    $("#application-search").addEventListener("input", filterApplications);
  }

  if ($("#assessment-form")) {
    handleForm(
      $("#assessment-form"),
      "/api/assessments",
      async () => {
        await loadAssessments();
        await loadApplications();
      }
    );
  }

  if ($("#interview-form")) {
    handleForm(
      $("#interview-form"),
      "/api/interviews",
      async () => {
        await loadInterviews();
        await loadApplications();
      }
    );
  }

  if ($("#task-form")) {
    const form = $("#task-form");

    form.addEventListener("submit", async e => {
      e.preventDefault();

      const data = formData(form);
      const id = form.dataset.editId;

      data.application_id = data.application_id || null;
      data.due_date = data.due_date || null;
      data.description = data.description || null;

      try {
        await api(
          id ? `/api/tasks/${id}` : "/api/tasks",
          {
            method: id ? "PUT" : "POST",
            body: jsonBody(data)
          }
        );

        delete form.dataset.editId;
        form.reset();

        form.querySelector('button[type="submit"]').textContent =
          "Create task";

        toast(id ? "Task updated." : "Task created.");
        await loadTasks();

      } catch (err) {
        toast(err.message, true);
      }
    });
  }

  if ($("#note-form")) {
    handleForm($("#note-form"), "/api/notes", loadNotes);
  }

  if ($("#quick-task-form")) {
    $("#quick-task-form").addEventListener("submit", async e => {
      e.preventDefault();

      const form = e.currentTarget;

      try {
        await api("/api/tasks", {
          method: "POST",
          body: jsonBody({
            task_title: form.elements.task_title.value,
            priority: "Medium",
            status: "Pending"
          })
        });

        form.reset();
        await loadDashboard();
        toast("Task added.");

      } catch (err) {
        toast(err.message, true);
      }
    });
  }

  (async () => {
    try {
      if (["applications", "assessments", "interviews", "tasks", "notes"].includes(page)) {
        await loadApplications();
      }

      if (page === "dashboard") await loadDashboard();
      if (page === "applications") filterApplications();
      if (page === "assessments") await loadAssessments();
      if (page === "interviews") await loadInterviews();
      if (page === "tasks") await loadTasks();
      if (page === "notes") await loadNotes();

    } catch (err) {
      toast(
        err.message || "Could not load data. Check your server and database.",
        true
      );
    }
  })();

})();