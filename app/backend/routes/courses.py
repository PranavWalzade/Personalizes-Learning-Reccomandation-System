from flask import Blueprint, request, jsonify

from utils.database import get_db_connection


courses_bp = Blueprint("courses", __name__)


# ============================================================
# GET ALL COURSES
# ============================================================

@courses_bp.route("/courses", methods=["GET"])
def get_courses():

    connection = None

    try:

        # Optional filters
        branch = request.args.get("branch")
        semester = request.args.get("semester")
        search = request.args.get("search")

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                course_id,
                course_name,
                branch,
                semester,
                category,
                skills,
                prerequisites,
                difficulty,
                credits,
                course_level,
                is_core
            FROM courses
            WHERE 1 = 1
        """

        params = []

        # Branch filter
        if branch:

            query += """
                AND branch = %s
            """

            params.append(branch)

        # Semester filter
        if semester:

            try:
                semester = int(semester)

                query += """
                    AND semester = %s
                """

                params.append(semester)

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": "Semester must be a number"
                }), 400

        # Search
        if search:

            query += """
                AND (
                    course_name LIKE %s
                    OR course_id LIKE %s
                    OR skills LIKE %s
                    OR category LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value
            ])

        query += """
            ORDER BY semester ASC, course_name ASC
        """

        cursor.execute(
            query,
            params
        )

        courses = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "count": len(courses),
            "courses": courses
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to load courses",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


# ============================================================
# GET SINGLE COURSE
# ============================================================

@courses_bp.route(
    "/courses/<string:course_id>",
    methods=["GET"]
)
def get_course(course_id):

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                id,
                course_id,
                course_name,
                branch,
                semester,
                category,
                skills,
                prerequisites,
                difficulty,
                credits,
                course_level,
                is_core
            FROM courses
            WHERE course_id = %s
            LIMIT 1
        """

        cursor.execute(
            query,
            (course_id,)
        )

        course = cursor.fetchone()

        cursor.close()

        if not course:

            return jsonify({
                "success": False,
                "message": "Course not found"
            }), 404

        return jsonify({
            "success": True,
            "course": course
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to load course",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()