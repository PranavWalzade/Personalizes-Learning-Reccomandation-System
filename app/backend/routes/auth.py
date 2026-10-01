from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from utils.database import get_db_connection


auth_bp = Blueprint("auth", __name__)


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    student_name = data.get("student_name", "").strip()
    branch = data.get("branch", "").strip()
    semester = data.get("semester")
    interests = data.get("interests", "").strip()
    preferred_difficulty = data.get("preferred_difficulty")

    # Required fields
    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "Username, email and password are required"
        }), 400

    if not student_name or not branch or semester is None:
        return jsonify({
            "success": False,
            "message": "Student name, branch and semester are required"
        }), 400

    # Password validation
    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters"
        }), 400

    try:

        semester = int(semester)

        if semester < 1 or semester > 8:
            return jsonify({
                "success": False,
                "message": "Semester must be between 1 and 8"
            }), 400

        if preferred_difficulty is not None:

            preferred_difficulty = int(
                preferred_difficulty
            )

            if preferred_difficulty < 1 or preferred_difficulty > 5:
                return jsonify({
                    "success": False,
                    "message": "Difficulty must be between 1 and 5"
                }), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check username/email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
               OR email = %s
            """,
            (username, email)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Username or email already exists"
            }), 409

        # Hash password
        password_hash = generate_password_hash(
            password
        )

        # Insert user
        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                role
            )
            VALUES (%s, %s, %s, 'student')
            """,
            (
                username,
                email,
                password_hash
            )
        )

        user_id = cursor.lastrowid

        # Insert student profile
        cursor.execute(
            """
            INSERT INTO students
            (
                user_id,
                student_name,
                branch,
                semester,
                interests,
                preferred_difficulty
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                student_name,
                branch,
                semester,
                interests,
                preferred_difficulty
            )
        )

        student_id = cursor.lastrowid

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user_id": user_id,
            "student_id": student_id
        }), 201

    except Exception as error:

        if "connection" in locals() and connection:
            connection.rollback()
            connection.close()

        return jsonify({
            "success": False,
            "message": "Registration failed",
            "error": str(error)
        }), 500


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    login_value = data.get("login", "").strip()
    password = data.get("password", "").strip()

    if not login_value or not password:
        return jsonify({
            "success": False,
            "message": "Username/email and password are required"
        }), 400

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                u.id AS user_id,
                u.username,
                u.email,
                u.password_hash,
                u.role,

                s.id AS student_id,
                s.student_name,
                s.branch,
                s.semester,
                s.interests,
                s.preferred_difficulty,
                s.learning_level,
                s.academic_strength,
                s.engagement_strength,
                s.readiness_score

            FROM users u

            LEFT JOIN students s
                ON u.id = s.user_id

            WHERE u.username = %s
               OR u.email = %s

            LIMIT 1
        """

        cursor.execute(
            query,
            (
                login_value,
                login_value.lower()
            )
        )

        user = cursor.fetchone()

        if not user:

            cursor.close()

            return jsonify({
                "success": False,
                "message": "Invalid username/email or password"
            }), 401

        # Check password
        password_valid = check_password_hash(
            user["password_hash"],
            password
        )

        if not password_valid:

            cursor.close()

            return jsonify({
                "success": False,
                "message": "Invalid username/email or password"
            }), 401

        # Never send password hash
        user.pop(
            "password_hash",
            None
        )

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Login failed",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()