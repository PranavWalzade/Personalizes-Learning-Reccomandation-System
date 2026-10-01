from flask import Blueprint, request, jsonify

from utils.database import get_db_connection
from utils.notifications import insert_notification


student_courses_bp = Blueprint(
    "student_courses",
    __name__
)


# =========================================================
# GET STUDENT COURSES
# =========================================================

@student_courses_bp.route(
    "/student/<int:student_id>/courses",
    methods=["GET"]
)
def get_student_courses(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                sc.id AS student_course_id,

                c.id AS course_database_id,
                c.course_id,
                c.course_name,
                c.branch,
                c.semester,
                c.category,
                c.skills,
                c.prerequisites,
                c.difficulty,
                c.credits,
                c.course_level,
                c.is_core,

                sc.status,
                sc.score,
                sc.completed_at,

                COALESCE(
                    p.progress_percent,
                    0
                ) AS progress_percent,

                COALESCE(
                    p.time_spent_minutes,
                    0
                ) AS time_spent_minutes,

                p.last_activity

            FROM student_courses sc

            INNER JOIN courses c
                ON sc.course_id = c.id

            LEFT JOIN progress p
                ON p.student_id = sc.student_id
                AND p.course_id = sc.course_id

            WHERE sc.student_id = %s

            ORDER BY sc.id DESC
            """,
            (student_id,)
        )

        courses = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(courses),
            "courses": courses
        })

    except Exception as error:

        print(
            "Get student courses error:",
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
# REMOVE COURSE FROM MY COURSES
# =========================================================

@student_courses_bp.route(
    "/student/<int:student_id>/courses/<course_code>",
    methods=["DELETE"]
)
def delete_student_course(student_id, course_code):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM courses
            WHERE course_id = %s
            LIMIT 1
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

        cursor.execute(
            """
            SELECT id
            FROM student_courses
            WHERE student_id = %s
              AND course_id = %s
            LIMIT 1
            """,
            (student_id, database_course_id)
        )

        enrollment = cursor.fetchone()

        if not enrollment:
            return jsonify({
                "success": False,
                "message": "Student is not enrolled in this course."
            }), 404

        cursor.execute(
            """
            DELETE FROM progress
            WHERE student_id = %s
              AND course_id = %s
            """,
            (student_id, database_course_id)
        )

        cursor.execute(
            """
            DELETE FROM student_courses
            WHERE student_id = %s
              AND course_id = %s
            """,
            (student_id, database_course_id)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Course removed from My Courses."
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Delete student course error:",
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
# ADD COURSE TO MY COURSES
# =========================================================

@student_courses_bp.route(
    "/student/<int:student_id>/courses",
    methods=["POST"]
)
def add_student_course(student_id):

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        course_code = data.get("course_id")

        status = data.get(
            "status",
            "not_started"
        )

        score = data.get("score")

        if not course_code:

            return jsonify({
                "success": False,
                "message": "Course ID is required."
            }), 400

        allowed_statuses = [
            "not_started",
            "in_progress",
            "completed"
        ]

        if status not in allowed_statuses:

            return jsonify({
                "success": False,
                "message": "Invalid course status."
            }), 400

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE id = %s
            LIMIT 1
            """,
            (student_id,)
        )

        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Student profile not found."
            }), 404

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
        # CHECK DUPLICATE
        # -----------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM student_courses
            WHERE student_id = %s
              AND course_id = %s
            """,
            (
                student_id,
                database_course_id
            )
        )

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "success": False,
                "message": "Course already exists in My Courses."
            }), 409

        # -----------------------------------------
        # VALIDATE SCORE
        # -----------------------------------------

        if score is not None:

            try:

                score = float(score)

            except (
                ValueError,
                TypeError
            ):

                return jsonify({
                    "success": False,
                    "message": "Score must be a number."
                }), 400

            if score < 0 or score > 100:

                return jsonify({
                    "success": False,
                    "message": "Score must be between 0 and 100."
                }), 400

        # -----------------------------------------
        # INSERT
        # -----------------------------------------

        cursor.execute(
            """
            INSERT INTO student_courses
            (
                student_id,
                course_id,
                status,
                score
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                student_id,
                database_course_id,
                status,
                score
            )
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Course added successfully.",
            "course": {
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "status": status,
                "score": score
            }
        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Add student course error:",
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
# UPDATE COURSE
# IMPORTANT:
# FRONTEND SENDS CSE005, NOT MYSQL ID 5
# =========================================================

@student_courses_bp.route(
    "/student/<int:student_id>/courses/<course_code>",
    methods=["PUT"]
)
def update_student_course(
    student_id,
    course_code
):

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        status = data.get("status")

        score = data.get("score")

        # -----------------------------------------
        # VALIDATE STATUS
        # -----------------------------------------

        allowed_statuses = [
            "not_started",
            "in_progress",
            "completed"
        ]

        if (
            status is not None
            and status not in allowed_statuses
        ):

            return jsonify({
                "success": False,
                "message": "Invalid course status."
            }), 400

        # -----------------------------------------
        # VALIDATE SCORE
        # -----------------------------------------

        if score is not None:

            try:

                score = float(score)

            except (
                ValueError,
                TypeError
            ):

                return jsonify({
                    "success": False,
                    "message": "Score must be a number."
                }), 400

            if score < 0 or score > 100:

                return jsonify({
                    "success": False,
                    "message": "Score must be between 0 and 100."
                }), 400

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -----------------------------------------
        # FIND COURSE USING COURSE CODE
        # Example: CSE005
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
        # CHECK STUDENT ENROLLMENT
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
        # BUILD UPDATE
        # -----------------------------------------

        update_fields = []

        update_values = []

        if status is not None:

            update_fields.append(
                "status = %s"
            )

            update_values.append(status)

            update_fields.append(
                "completed_at = CASE WHEN %s = 'completed' "
                "THEN CURRENT_TIMESTAMP ELSE NULL END"
            )

            update_values.append(status)

        if score is not None:

            update_fields.append(
                "score = %s"
            )

            update_values.append(score)

        if not update_fields:

            return jsonify({
                "success": False,
                "message": "No data to update."
            }), 400

        update_values.extend([
            student_id,
            database_course_id
        ])

        query = f"""
            UPDATE student_courses

            SET {", ".join(update_fields)}

            WHERE student_id = %s
              AND course_id = %s
        """

        cursor.execute(
            query,
            tuple(update_values)
        )

        if (
            status == "completed"
            and enrollment["status"] != "completed"
        ):
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
            "message": "Course updated successfully.",
            "course": {
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "status": status,
                "score": score
            }
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Update student course error:",
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