from flask import Blueprint, request, jsonify

from utils.database import get_db_connection
from utils.notifications import insert_notification


progress_bp = Blueprint(
    "progress",
    __name__
)


# =========================================================
# GET STUDENT PROGRESS
# =========================================================

@progress_bp.route(
    "/student/<int:student_id>/progress",
    methods=["GET"]
)
def get_student_progress(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                p.id,

                p.student_id,

                c.id AS course_database_id,
                c.course_id,
                c.course_name,
                c.branch,
                c.semester,

                p.progress_percent,
                p.time_spent_minutes,
                p.last_activity

            FROM progress p

            INNER JOIN courses c
                ON p.course_id = c.id

            WHERE p.student_id = %s

            ORDER BY p.last_activity DESC
            """,
            (student_id,)
        )

        progress = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(progress),
            "progress": progress
        })

    except Exception as error:

        print(
            "Get progress error:",
            error
        )

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE COURSE PROGRESS
# IMPORTANT:
# FRONTEND SENDS CSE005
# =========================================================

@progress_bp.route(
    "/student/<int:student_id>/progress/<course_code>",
    methods=["PUT"]
)
def update_progress(
    student_id,
    course_code
):

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        progress_percent = data.get(
            "progress_percent",
            0
        )

        time_spent_minutes = data.get(
            "time_spent_minutes",
            0
        )

        # -----------------------------------------
        # VALIDATE PROGRESS
        # -----------------------------------------

        try:

            progress_percent = float(
                progress_percent
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "success": False,
                "message": "Progress must be a number."
            }), 400

        if (
            progress_percent < 0
            or progress_percent > 100
        ):

            return jsonify({
                "success": False,
                "message": "Progress must be between 0 and 100."
            }), 400

        # -----------------------------------------
        # VALIDATE TIME
        # -----------------------------------------

        try:

            time_spent_minutes = int(
                time_spent_minutes
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "success": False,
                "message": "Time spent must be a number."
            }), 400

        if time_spent_minutes < 0:

            return jsonify({
                "success": False,
                "message": "Time spent cannot be negative."
            }), 400

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -----------------------------------------
        # FIND COURSE
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                course_id,
                course_name
            FROM courses
            WHERE course_id = %s
            """,
            (course_code,)
        )

        course = cursor.fetchone()

        if not course:

            return jsonify({
                "success": False,
                "message": "Course not found."
            }), 404

        database_course_id = course["id"]

        # -----------------------------------------
        # CHECK ENROLLMENT
        # -----------------------------------------

        cursor.execute(
            """
            SELECT id, status
            FROM student_courses
            WHERE student_id = %s
              AND course_id = %s
            FOR UPDATE
            """,
            (
                student_id,
                database_course_id
            )
        )

        enrollment = cursor.fetchone()

        if not enrollment:

            return jsonify({
                "success": False,
                "message": "Student is not enrolled in this course."
            }), 404

        # -----------------------------------------
        # CHECK EXISTING PROGRESS
        # -----------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM progress
            WHERE student_id = %s
              AND course_id = %s
            """,
            (
                student_id,
                database_course_id
            )
        )

        existing = cursor.fetchone()

        # -----------------------------------------
        # UPDATE
        # -----------------------------------------

        if existing:

            cursor.execute(
                """
                UPDATE progress

                SET
                    progress_percent = %s,
                    time_spent_minutes = %s,
                    last_activity = CURRENT_TIMESTAMP

                WHERE student_id = %s
                  AND course_id = %s
                """,
                (
                    progress_percent,
                    time_spent_minutes,
                    student_id,
                    database_course_id
                )
            )

        # -----------------------------------------
        # INSERT
        # -----------------------------------------

        else:

            cursor.execute(
                """
                INSERT INTO progress
                (
                    student_id,
                    course_id,
                    progress_percent,
                    time_spent_minutes,
                    last_activity
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    student_id,
                    database_course_id,
                    progress_percent,
                    time_spent_minutes
                )
            )

        if (
            progress_percent == 100
            and enrollment["status"] != "completed"
        ):
            cursor.execute(
                """
                UPDATE student_courses
                SET
                    status = 'completed',
                    completed_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
                  AND course_id = %s
                """,
                (
                    student_id,
                    database_course_id
                )
            )

            insert_notification(
                cursor,
                student_id,
                "Course completed",
                f"You completed {course['course_name']}. Great work!",
                "success"
            )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Progress updated successfully.",
            "progress": {
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "progress_percent": progress_percent,
                "time_spent_minutes": time_spent_minutes
            }
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Update progress error:",
            error
        )

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()