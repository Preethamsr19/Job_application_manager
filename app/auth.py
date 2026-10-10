
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.db import get_db_connection
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("login.html", page="login")


@auth.route("/register")
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("register.html", page="register")


@auth.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    university = data.get("university", "").strip()
    graduation_year = data.get("graduation_year") or None

    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    password_hash = generate_password_hash(password)
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users
            (name, email, password_hash, university, graduation_year)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                email,
                password_hash,
                university or None,
                graduation_year
            )
        )
        connection.commit()

        return jsonify({
            "message": "Registration successful"
        }), 201

    except Exception as error:
        connection.rollback()

        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "error": "Email is already registered"
            }), 409

        app_error = "Registration failed"
        return jsonify({"error": app_error}), 500

    finally:
        cursor.close()
        connection.close()


@auth.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM users
            WHERE email = %s
            """,
            (email,)
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if not row or not check_password_hash(
        row["password_hash"], password
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    user = User(
        row["user_id"],
        row["name"],
        row["email"]
    )
    login_user(user)

    return jsonify({
        "message": "Login successful",
        "name": user.name
    })


@auth.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()

    return jsonify({
        "message": "Logged out successfully"
    })


@auth.route("/api/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return jsonify({
            "authenticated": False
        }), 401

    return jsonify({
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        }
    })
