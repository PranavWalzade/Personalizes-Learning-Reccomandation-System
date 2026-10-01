from flask import Blueprint, request, jsonify

from utils.database import get_db_connection


profile_bp = Blueprint("profile", __name__)


# ============================================================
# GET STUDENT PROFILE
# ============================================================

@profile_bp.route("/profile/<int:student_id>", methods=["GET"])
def get_profile(student_id):

    connection = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                s.id AS student_id,
                s.user_id,
                s.student_name,
                s.branch,
                s.semester,
                s.interests,
                s.preferred_difficulty,
                s.learning_level,
                s.academic_strength,
                s.engagement_strength,
                s.readiness_score,
                u.username,
                u.email
            FROM students s
            JOIN users u
                ON s.user_id = u.id
            WHERE s.id = %s
            LIMIT 1
        """

        cursor.execute(query, (student_id,))

        student = cursor.fetchone()

        cursor.close()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student profile not found"
            }), 404

        return jsonify({
            "success": True,
            "profile": student
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to load profile",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


# ============================================================
# UPDATE STUDENT PROFILE
# ============================================================

@profile_bp.route("/profile/<int:student_id>", methods=["PUT"])
def update_profile(student_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    student_name = data.get("student_name")
    branch = data.get("branch")
    semester = data.get("semester")
    interests = data.get("interests")
    preferred_difficulty = data.get("preferred_difficulty")

    if not student_name or not branch or semester is None:
        return jsonify({
            "success": False,
            "message": "Student name, branch and semester are required"
        }), 400

    try:
        semester = int(semester)

        if semester < 1 or semester > 8:
            return jsonify({
                "success": False,
                "message": "Semester must be between 1 and 8"
            }), 400

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Semester must be a number"
        }), 400

    if preferred_difficulty is not None:

        try:
            preferred_difficulty = int(
                preferred_difficulty
            )

            if preferred_difficulty < 1 or preferred_difficulty > 5:
                return jsonify({
                    "success": False,
                    "message": "Preferred difficulty must be between 1 and 5"
                }), 400

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Preferred difficulty must be a number"
            }), 400

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        # Check whether student exists
        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE id = %s
            LIMIT 1
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            cursor.close()

            return jsonify({
                "success": False,
                "message": "Student profile not found"
            }), 404

        # Update profile
        cursor.execute(
            """
            UPDATE students
            SET
                student_name = %s,
                branch = %s,
                semester = %s,
                interests = %s,
                preferred_difficulty = %s
            WHERE id = %s
            """,
            (
                student_name.strip(),
                branch.strip(),
                semester,
                (interests or "").strip(),
                preferred_difficulty,
                student_id
            )
        )

        connection.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "student_id": student_id
        }), 200

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update profile",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()