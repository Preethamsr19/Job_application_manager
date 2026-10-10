
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.db import get_db_connection

extra = Blueprint("extra", __name__)


def owns_application(cursor, application_id):
    """Check whether the application belongs to the logged-in user."""
    cursor.execute(
        """
        SELECT application_id
        FROM applications
        WHERE application_id = %s AND user_id = %s
        """,
        (application_id, current_user.id)
    )
    return cursor.fetchone() is not None


# ==================== ASSESSMENTS ====================

@extra.route("/api/assessments", methods=["GET"])
@login_required
def get_assessments():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.assessment_id,
                a.application_id,
                c.company_name,
                j.job_role,
                a.assessment_name,
                a.assessment_date,
                a.platform,
                a.status,
                a.notes
            FROM assessments a
            JOIN applications j
                ON a.application_id = j.application_id
            JOIN companies c
                ON j.company_id = c.company_id
            WHERE j.user_id = %s
            ORDER BY a.assessment_date
            """,
            (current_user.id,)
        )

        results = cursor.fetchall()

        for item in results:
            for key, value in item.items():
                if hasattr(value, "isoformat"):
                    item[key] = value.isoformat()

        return jsonify(results)
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/assessments", methods=["POST"])
@login_required
def add_assessment():
    data = request.get_json(silent=True) or {}

    application_id = data.get("application_id")
    name = data.get("assessment_name", "").strip()
    assessment_date = data.get("assessment_date") or None
    platform = data.get("platform") or None
    status = data.get("status", "Scheduled")
    notes = data.get("notes") or None

    if not application_id or not name:
        return jsonify({
            "error": "Application ID and assessment name are required"
        }), 400

    if status not in {"Scheduled", "Completed", "Missed"}:
        return jsonify({"error": "Invalid assessment status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not owns_application(cursor, application_id):
            return jsonify({"error": "Application not found"}), 404

        cursor.execute(
            """
            INSERT INTO assessments
            (application_id, assessment_name, assessment_date,
             platform, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                application_id, name, assessment_date,
                platform, status, notes
            )
        )
        connection.commit()

        return jsonify({
            "message": "Assessment added successfully",
            "assessment_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        return jsonify({
            "error": "Could not add assessment. Check the supplied values."
        }), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/assessments/<int:assessment_id>", methods=["PUT"])
@login_required
def update_assessment(assessment_id):
    data = request.get_json(silent=True) or {}

    allowed_fields = {
        "assessment_name", "assessment_date",
        "platform", "status", "notes"
    }
    updates = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    if "assessment_name" in updates:
        updates["assessment_name"] = (
            updates["assessment_name"] or ""
        ).strip()
        if not updates["assessment_name"]:
            return jsonify({
                "error": "Assessment name cannot be empty"
            }), 400

    if "status" in updates and updates["status"] not in {
        "Scheduled", "Completed", "Missed"
    }:
        return jsonify({"error": "Invalid assessment status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT a.assessment_id
            FROM assessments a
            JOIN applications j
                ON a.application_id = j.application_id
            WHERE a.assessment_id = %s AND j.user_id = %s
            """,
            (assessment_id, current_user.id)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Assessment not found"}), 404

        columns = ", ".join(f"{field} = %s" for field in updates)
        values = list(updates.values()) + [assessment_id]

        cursor.execute(
            f"UPDATE assessments SET {columns} WHERE assessment_id = %s",
            tuple(values)
        )
        connection.commit()

        return jsonify({"message": "Assessment updated successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not update assessment"}), 400
    finally:
        cursor.close()
        connection.close()




@extra.route("/api/assessments/<int:assessment_id>", methods=["DELETE"])
@login_required
def delete_assessment(assessment_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE a FROM assessments a
            JOIN applications j ON a.application_id = j.application_id
            WHERE a.assessment_id = %s AND j.user_id = %s
            """,
            (assessment_id, current_user.id)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Assessment not found"}), 404
        return jsonify({"message": "Assessment deleted successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not delete assessment"}), 400
    finally:
        cursor.close()
        connection.close()


# ==================== INTERVIEWS ====================

@extra.route("/api/interviews", methods=["GET"])
@login_required
def get_interviews():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                i.interview_id,
                i.application_id,
                c.company_name,
                j.job_role,
                i.interview_type,
                i.interview_date,
                i.mode,
                i.meeting_link,
                i.interviewer_name,
                i.status,
                i.feedback
            FROM interviews i
            JOIN applications j
                ON i.application_id = j.application_id
            JOIN companies c
                ON j.company_id = c.company_id
            WHERE j.user_id = %s
            ORDER BY i.interview_date
            """,
            (current_user.id,)
        )

        results = cursor.fetchall()

        for item in results:
            for key, value in item.items():
                if hasattr(value, "isoformat"):
                    item[key] = value.isoformat()

        return jsonify(results)
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/interviews", methods=["POST"])
@login_required
def add_interview():
    data = request.get_json(silent=True) or {}

    application_id = data.get("application_id")
    interview_date = data.get("interview_date")
    interview_type = data.get("interview_type", "Technical")
    mode = data.get("mode", "Online")

    if not application_id or not interview_date:
        return jsonify({
            "error": "Application ID and interview date are required"
        }), 400

    if interview_type not in {
        "Technical", "HR", "Managerial", "Other"
    }:
        return jsonify({"error": "Invalid interview type"}), 400

    if mode not in {"Online", "Offline", "Phone"}:
        return jsonify({"error": "Invalid interview mode"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not owns_application(cursor, application_id):
            return jsonify({"error": "Application not found"}), 404

        cursor.execute(
            """
            INSERT INTO interviews
            (application_id, interview_type, interview_date, mode,
             meeting_link, interviewer_name, status, feedback)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                application_id,
                interview_type,
                interview_date,
                mode,
                data.get("meeting_link") or None,
                data.get("interviewer_name") or None,
                "Scheduled",
                data.get("feedback") or None
            )
        )
        connection.commit()

        return jsonify({
            "message": "Interview scheduled successfully",
            "interview_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        return jsonify({
            "error": "Could not schedule interview. Check the supplied values."
        }), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/interviews/<int:interview_id>", methods=["PUT"])
@login_required
def update_interview(interview_id):
    data = request.get_json(silent=True) or {}

    allowed_fields = {
        "interview_type", "interview_date", "mode",
        "meeting_link", "interviewer_name", "status", "feedback"
    }
    updates = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    if "interview_type" in updates and updates["interview_type"] not in {
        "Technical", "HR", "Managerial", "Other"
    }:
        return jsonify({"error": "Invalid interview type"}), 400

    if "mode" in updates and updates["mode"] not in {
        "Online", "Offline", "Phone"
    }:
        return jsonify({"error": "Invalid interview mode"}), 400

    if "status" in updates and updates["status"] not in {
        "Scheduled", "Completed", "Cancelled"
    }:
        return jsonify({"error": "Invalid interview status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT i.interview_id
            FROM interviews i
            JOIN applications j
                ON i.application_id = j.application_id
            WHERE i.interview_id = %s AND j.user_id = %s
            """,
            (interview_id, current_user.id)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Interview not found"}), 404

        columns = ", ".join(f"{field} = %s" for field in updates)
        values = list(updates.values()) + [interview_id]

        cursor.execute(
            f"UPDATE interviews SET {columns} WHERE interview_id = %s",
            tuple(values)
        )
        connection.commit()

        return jsonify({"message": "Interview updated successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not update interview"}), 400
    finally:
        cursor.close()
        connection.close()

    


@extra.route("/api/interviews/<int:interview_id>", methods=["DELETE"])
@login_required
def delete_interview(interview_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE i FROM interviews i
            JOIN applications j ON i.application_id = j.application_id
            WHERE i.interview_id = %s AND j.user_id = %s
            """,
            (interview_id, current_user.id)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Interview not found"}), 404
        return jsonify({"message": "Interview deleted successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not delete interview"}), 400
    finally:
        cursor.close()
        connection.close()


# ==================== PREPARATION TASKS ====================

@extra.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                t.task_id,
                t.application_id,
                c.company_name,
                a.job_role,
                t.task_title,
                t.description,
                t.due_date,
                t.priority,
                t.status,
                t.created_at
            FROM tasks t
            LEFT JOIN applications a
                ON t.application_id = a.application_id
            LEFT JOIN companies c
                ON a.company_id = c.company_id
            WHERE t.user_id = %s
            ORDER BY t.due_date IS NULL, t.due_date
            """,
            (current_user.id,)
        )

        results = cursor.fetchall()

        for item in results:
            for key, value in item.items():
                if hasattr(value, "isoformat"):
                    item[key] = value.isoformat()

        return jsonify(results)
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/tasks", methods=["POST"])
@login_required
def add_task():
    data = request.get_json(silent=True) or {}

    title = data.get("task_title", "").strip()
    description = data.get("description") or None
    application_id = data.get("application_id") or None
    due_date = data.get("due_date") or None
    priority = data.get("priority", "Medium")
    status = data.get("status", "Pending")

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if priority not in {"Low", "Medium", "High"}:
        return jsonify({"error": "Invalid priority"}), 400

    if status not in {"Pending", "In Progress", "Completed"}:
        return jsonify({"error": "Invalid task status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if application_id is not None:
            if not owns_application(cursor, application_id):
                return jsonify({"error": "Application not found"}), 404

        cursor.execute(
            """
            INSERT INTO tasks
            (user_id, application_id, task_title, description,
             due_date, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                current_user.id, application_id, title, description,
                due_date, priority, status
            )
        )
        connection.commit()

        return jsonify({
            "message": "Task created successfully",
            "task_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        return jsonify({
            "error": "Could not create task. Check the supplied values."
        }), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    data = request.get_json(silent=True) or {}

    allowed_fields = {
        "task_title", "description", "application_id",
        "due_date", "priority", "status"
    }
    updates = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    if "task_title" in updates:
        updates["task_title"] = (updates["task_title"] or "").strip()
        if not updates["task_title"]:
            return jsonify({"error": "Task title cannot be empty"}), 400

    if "priority" in updates and updates["priority"] not in {
        "Low", "Medium", "High"
    }:
        return jsonify({"error": "Invalid priority"}), 400

    if "status" in updates and updates["status"] not in {
        "Pending", "In Progress", "Completed"
    }:
        return jsonify({"error": "Invalid task status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, current_user.id)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Task not found"}), 404

        if "application_id" in updates:
            application_id = updates["application_id"]
            if application_id is not None:
                if not owns_application(cursor, application_id):
                    return jsonify({"error": "Application not found"}), 404

        columns = ", ".join(f"{field} = %s" for field in updates)
        values = list(updates.values()) + [task_id, current_user.id]

        cursor.execute(
            f"""
            UPDATE tasks
            SET {columns}
            WHERE task_id = %s AND user_id = %s
            """,
            tuple(values)
        )
        connection.commit()

        return jsonify({"message": "Task updated successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not update task"}), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, current_user.id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"message": "Task deleted successfully"})
    finally:
        cursor.close()
        connection.close()

    
# ==================== APPLICATION NOTES ====================

@extra.route("/api/notes", methods=["GET"])
@login_required
def get_notes():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                n.note_id,
                n.application_id,
                c.company_name,
                a.job_role,
                n.note_title,
                n.note_content,
                n.created_at,
                n.updated_at
            FROM notes n
            JOIN applications a
                ON n.application_id = a.application_id
            JOIN companies c
                ON a.company_id = c.company_id
            WHERE a.user_id = %s
            ORDER BY n.updated_at DESC
            """,
            (current_user.id,)
        )

        results = cursor.fetchall()

        for item in results:
            for key, value in item.items():
                if hasattr(value, "isoformat"):
                    item[key] = value.isoformat()

        return jsonify(results)
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/notes", methods=["POST"])
@login_required
def add_note():
    data = request.get_json(silent=True) or {}

    application_id = data.get("application_id")
    title = data.get("note_title") or None
    content = data.get("note_content", "").strip()

    if not application_id or not content:
        return jsonify({
            "error": "Application ID and note content are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not owns_application(cursor, application_id):
            return jsonify({"error": "Application not found"}), 404

        cursor.execute(
            """
            INSERT INTO notes
            (application_id, note_title, note_content)
            VALUES (%s, %s, %s)
            """,
            (application_id, title, content)
        )
        connection.commit()

        return jsonify({
            "message": "Note created successfully",
            "note_id": cursor.lastrowid
        }), 201
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not create note"}), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/notes/<int:note_id>", methods=["PUT"])
@login_required
def update_note(note_id):
    data = request.get_json(silent=True) or {}

    allowed_fields = {"note_title", "note_content"}
    updates = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    if "note_content" in updates:
        updates["note_content"] = (
            updates["note_content"] or ""
        ).strip()

        if not updates["note_content"]:
            return jsonify({"error": "Note content cannot be empty"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT n.note_id
            FROM notes n
            JOIN applications a
                ON n.application_id = a.application_id
            WHERE n.note_id = %s AND a.user_id = %s
            """,
            (note_id, current_user.id)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Note not found"}), 404

        columns = ", ".join(f"{field} = %s" for field in updates)
        values = list(updates.values()) + [note_id]

        cursor.execute(
            f"UPDATE notes SET {columns} WHERE note_id = %s",
            tuple(values)
        )
        connection.commit()

        return jsonify({"message": "Note updated successfully"})
    except Exception:
        connection.rollback()
        return jsonify({"error": "Could not update note"}), 400
    finally:
        cursor.close()
        connection.close()


@extra.route("/api/notes/<int:note_id>", methods=["DELETE"])
@login_required
def delete_note(note_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE n
            FROM notes n
            JOIN applications a
                ON n.application_id = a.application_id
            WHERE n.note_id = %s AND a.user_id = %s
            """,
            (note_id, current_user.id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Note not found"}), 404

        return jsonify({"message": "Note deleted successfully"})
    finally:
        cursor.close()
        connection.close()


