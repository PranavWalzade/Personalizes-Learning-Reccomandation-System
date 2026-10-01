from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from routes.auth import auth_bp
from routes.courses import courses_bp
from routes.profile import profile_bp
from routes.dashboard import dashboard_bp
from routes.student_courses import student_courses_bp
from routes.progress import progress_bp
from routes.skills import skills_bp
from routes.recommendations import recommendations_bp
from routes.skill_gaps import skill_gaps_bp
from routes.learning_path import learning_path_bp
from routes.notifications import notifications_bp
from routes.model_metrics import model_metrics_bp


# =========================================================
# CREATE FLASK APP
# =========================================================

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

CORS(app)


# =========================================================
# BASIC ROUTES
# =========================================================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/pages/<path:page>")
def frontend_page(page):
    return send_from_directory(FRONTEND_DIR / "pages", page)


@app.errorhandler(404)
def not_found(error):
    if error.description:
        return jsonify({
            "success": False,
            "message": "Resource not found"
        }), 404

    return jsonify({
        "success": False,
        "message": "Resource not found"
    }), 404


@app.route("/api/health")
def health():

    return jsonify({
        "success": True,
        "message": "API is working."
    })


@app.route("/api/database-test")
def database_test():

    try:

        from utils.database import get_db_connection

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT DATABASE()"
        )

        database_name = cursor.fetchone()[0]

        cursor.close()

        connection.close()

        return jsonify({
            "success": True,
            "database": database_name
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# REGISTER BLUEPRINTS
# =========================================================

app.register_blueprint(
    auth_bp,
    url_prefix="/api"
)

app.register_blueprint(
    courses_bp,
    url_prefix="/api"
)

app.register_blueprint(
    profile_bp,
    url_prefix="/api"
)

app.register_blueprint(
    dashboard_bp,
    url_prefix="/api"
)

app.register_blueprint(
    student_courses_bp,
    url_prefix="/api"
)

app.register_blueprint(
    progress_bp,
    url_prefix="/api"
)

app.register_blueprint(
    skills_bp,
    url_prefix="/api"
)

app.register_blueprint(
    recommendations_bp,
    url_prefix="/api"
)

app.register_blueprint(
    skill_gaps_bp,
    url_prefix="/api"
)

app.register_blueprint(
    learning_path_bp,
    url_prefix="/api"
)

app.register_blueprint(
    notifications_bp,
    url_prefix="/api"
)

app.register_blueprint(
    model_metrics_bp,
    url_prefix="/api"
)


# =========================================================
# SHOW REGISTERED ROUTES
# =========================================================

@app.route("/api/routes")
def show_routes():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({
            "endpoint": rule.endpoint,
            "methods": sorted(
                rule.methods
            ),
            "path": str(rule)
        })

    return jsonify({
        "success": True,
        "routes": routes
    })

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )