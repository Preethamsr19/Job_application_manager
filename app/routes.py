
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from app.db import get_db_connection

main = Blueprint("main", __name__)

APPLICATION_STATUSES = {
    "Interested",
    "Applied",
    "OA Scheduled",
    "OA Completed",
    "Shortlisted",
    "Technical Interview",
    "HR Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
}


@main.route("/")
def home():
    if current_user.is_authenticated:
        return dashboard()
    from flask import redirect, url_for
    return redirect(url_for("auth.login_page"))


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", page="dashboard")


@main.route("/applications")
@login_required
def applications_page():
    return render_template("applications.html", page="applications")


@main.route("/assessments")
@login_required
def assessments_page():
    return render_template("assesments.html", page="assessments")


@main.route("/interviews")
@login_required
def interviews_page():
    return render_template("interviews.html", page="interviews")


@main.route("/tasks")
@login_required
def tasks_page():
    return render_template("tasks.html", page="tasks")


@main.route("/notes")
@login_required
def notes_page():
    return render_template("notes.html", page="notes")


# -------------------- COMPANIES --------------------

@main.route("/api/companies", methods=["GET"])
@login_required
def get_companies():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT company_id, company_name, website, location, created_at
            FROM companies
            WHERE user_id = %s
            ORDER BY company_name
            """,
            (current_user.id,)
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        connection.close()


@main.route("/api/companies", methods=["POST"])
@login_required
def add_company():
    data = request.get_json(silent=True) or {}

    name = data.get("company_name", "").strip()
    website = data.get("website", "").strip() or None
    location = data.get("location", "").strip() or None

    if not name:
        return jsonify({"error": "Company name is required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO companies (user_id, company_name, website, location)
            VALUES (%s, %s, %s, %s)
            """,
            (current_user.id, name, website, location)
        )
        connection.commit()

        return jsonify({
            "message": "Company added successfully",
            "company_id": cursor.lastrowid
        }), 201

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "error": "You have already added this company"
            }), 409

        return jsonify({"error": "Could not add company"}), 500
    finally:
        cursor.close()
        connection.close()


@main.route("/api/companies/<int:company_id>", methods=["PUT"])
@login_required
def update_company(company_id):
    data = request.get_json(silent=True) or {}

    name = data.get("company_name", "").strip()
    website = data.get("website", "").strip() or None
    location = data.get("location", "").strip() or None

    if not name:
        return jsonify({"error": "Company name is required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE companies
            SET company_name = %s, website = %s, location = %s
            WHERE company_id = %s AND user_id = %s
            """,
            (name, website, location, company_id, current_user.id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            cursor.execute(
                """
                SELECT company_id FROM companies
                WHERE company_id = %s AND user_id = %s
                """,
                (company_id, current_user.id)
            )
            if cursor.fetchone() is None:
                return jsonify({"error": "Company not found"}), 404

        return jsonify({"message": "Company updated successfully"})

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "error": "You have already added this company"
            }), 409

        return jsonify({"error": "Could not update company"}), 500
    finally:
        cursor.close()
        connection.close()


@main.route("/api/companies/<int:company_id>", methods=["DELETE"])
@login_required
def delete_company(company_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM companies
            WHERE company_id = %s AND user_id = %s
            """,
            (company_id, current_user.id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Company not found"}), 404

        return jsonify({"message": "Company deleted successfully"})
    finally:
        cursor.close()
        connection.close()


# -------------------- APPLICATIONS --------------------

@main.route("/api/applications", methods=["GET"])
@login_required
def get_applications():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.application_id,
                a.company_id,
                c.company_name,
                a.job_role,
                a.job_type,
                a.job_link,
                a.application_date,
                a.status,
                a.salary,
                a.location,
                a.notes,
                a.created_at
            FROM applications a
            JOIN companies c ON a.company_id = c.company_id
            WHERE a.user_id = %s
            ORDER BY a.created_at DESC
            """,
            (current_user.id,)
        )

        applications = cursor.fetchall()

        # Convert dates to JSON-friendly strings.
        for application in applications:
            for field, value in application.items():
                if hasattr(value, "isoformat"):
                    application[field] = value.isoformat()

        return jsonify(applications)
    finally:
        cursor.close()
        connection.close()


@main.route("/api/applications", methods=["POST"])
@login_required
def add_application():
    data = request.get_json(silent=True) or {}

    company_id = data.get("company_id")
    job_role = data.get("job_role", "").strip()
    status = data.get("status", "Interested")

    if not company_id or not job_role:
        return jsonify({
            "error": "Company ID and job role are required"
        }), 400

    if status not in APPLICATION_STATUSES:
        return jsonify({"error": "Invalid application status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT company_id FROM companies
            WHERE company_id = %s AND user_id = %s
            """,
            (company_id, current_user.id)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Company not found in your company list"
            }), 404

        cursor.execute(
            """
            INSERT INTO applications
            (user_id, company_id, job_role, job_type, job_link,
             application_date, status, salary, location, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                current_user.id,
                company_id,
                job_role,
                data.get("job_type") or None,
                data.get("job_link") or None,
                data.get("application_date") or None,
                status,
                data.get("salary") or None,
                data.get("location") or None,
                data.get("notes") or None
            )
        )
        connection.commit()

        return jsonify({
            "message": "Application added successfully",
            "application_id": cursor.lastrowid
        }), 201

    except Exception:
        connection.rollback()
        return jsonify({
            "error": "Could not add application. Check the supplied values."
        }), 400
    finally:
        cursor.close()
        connection.close()


@main.route("/api/applications/<int:application_id>", methods=["PUT"])
@login_required
def update_application(application_id):
    data = request.get_json(silent=True) or {}

    allowed_fields = {
        "job_role", "job_type", "job_link", "application_date",
        "status", "salary", "location", "notes"
    }

    updates = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    if "job_role" in updates:
        updates["job_role"] = (updates["job_role"] or "").strip()
        if not updates["job_role"]:
            return jsonify({"error": "Job role cannot be empty"}), 400

    if "status" in updates and updates["status"] not in APPLICATION_STATUSES:
        return jsonify({"error": "Invalid application status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT application_id FROM applications
            WHERE application_id = %s AND user_id = %s
            """,
            (application_id, current_user.id)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Application not found"}), 404

        columns = ", ".join(f"{field} = %s" for field in updates)
        values = list(updates.values()) + [
            application_id,
            current_user.id
        ]

        cursor.execute(
            f"""
            UPDATE applications
            SET {columns}
            WHERE application_id = %s AND user_id = %s
            """,
            tuple(values)
        )
        connection.commit()

        return jsonify({"message": "Application updated successfully"})

    except Exception:
        connection.rollback()
        return jsonify({
            "error": "Could not update application. Check the supplied values."
        }), 400
    finally:
        cursor.close()
        connection.close()


@main.route("/api/applications/<int:application_id>", methods=["DELETE"])
@login_required
def delete_application(application_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM applications
            WHERE application_id = %s AND user_id = %s
            """,
            (application_id, current_user.id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Application not found"}), 404

        return jsonify({"message": "Application deleted successfully"})
    finally:
        cursor.close()
        connection.close()
