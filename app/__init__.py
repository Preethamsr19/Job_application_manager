
from flask import Flask, jsonify, request, redirect, url_for
from flask_login import LoginManager

from app.config import Config
from app.db import get_db_connection
from app.models import User
from app.routes import main
from app.auth import auth
from app.extra_routes import extra

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT user_id, name, email
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            return User(
                row["user_id"],
                row["name"],
                row["email"]
            )

        return None
    finally:
        cursor.close()
        connection.close()


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Authentication required"
        }), 401

    return redirect(url_for("auth.login_page"))


def create_app():
    app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)
    app.config.from_object(Config)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")

    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(extra)

    return app
