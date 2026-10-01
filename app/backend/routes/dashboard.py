from flask import Blueprint, jsonify

from utils.database import get_db_connection


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)
# =========================================================
# GET STUDENT DASHBOARD
# =========================================================

@dashboard_bp.route(
    "/dashboard/<int:student_id>",
    methods=["GET"]
)
def get_dashboard(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # 1. STUDENT PROFILE
        # =================================================

        cursor.execute(
            """
            SELECT
                s.id AS student_id,
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

            INNER JOIN users u
                ON s.user_id = u.id

            WHERE s.id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404


        # =================================================
        # 2. COURSE STATISTICS
        # =================================================

        cursor.execute(
            """
            SELECT

                COUNT(*) AS total_courses,

                SUM(
                    CASE
                        WHEN COALESCE(
                            NULLIF(sc.status, ''),
                            'not_started'
                        ) = 'completed'
                        THEN 1
                        ELSE 0
                    END
                ) AS completed_courses,

                SUM(
                    CASE
                        WHEN COALESCE(
                            NULLIF(sc.status, ''),
                            'not_started'
                        ) = 'in_progress'
                        THEN 1
                        ELSE 0
                    END
                ) AS in_progress_courses,

                AVG(
                    CASE
                        WHEN sc.status = 'completed' THEN 100
                        ELSE COALESCE(p.progress_percent, 0)
                    END
                ) AS average_progress,

                AVG(sc.score) AS average_score

            FROM student_courses sc

            LEFT JOIN progress p
                ON p.student_id = sc.student_id
                AND p.course_id = sc.course_id

            WHERE sc.student_id = %s
            """,
            (student_id,)
        )

        course_stats = cursor.fetchone()


        # =================================================
        # 3. RECENT COURSES
        # =================================================

        cursor.execute(
            """
            SELECT

                c.course_id,
                c.course_name,
                c.branch,
                c.semester,
                c.difficulty,

                COALESCE(
                    NULLIF(sc.status, ''),
                    'not_started'
                ) AS status,

                COALESCE(
                    p.progress_percent,
                    0
                ) AS progress_percent,

                sc.score,

                p.time_spent_minutes,
                p.last_activity

            FROM student_courses sc

            INNER JOIN courses c
                ON sc.course_id = c.id

            LEFT JOIN progress p
                ON p.student_id = sc.student_id
                AND p.course_id = sc.course_id

            WHERE sc.student_id = %s

            ORDER BY
                COALESCE(
                    p.last_activity,
                    sc.id
                ) DESC

            LIMIT 5
            """,
            (student_id,)
        )

        recent_courses = cursor.fetchall()


        # =================================================
        # 4. SKILL COUNT
        # =================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS skill_count
            FROM student_skills
            WHERE student_id = %s
            """,
            (student_id,)
        )

        skill_result = cursor.fetchone()

        skill_count = (
            skill_result["skill_count"]
            if skill_result
            else 0
        )


        # =================================================
        # 5. SKILL GAPS
        # =================================================

        cursor.execute(
            """
            SELECT

                skill_name,
                current_level,
                required_level,
                gap_score,
                priority

            FROM skill_gaps

            WHERE student_id = %s

            ORDER BY
                gap_score DESC

            LIMIT 10
            """,
            (student_id,)
        )

        skill_gaps = cursor.fetchall()


        # =================================================
        # 6. NOTIFICATIONS
        # =================================================

        cursor.execute(
            """
            SELECT

                id,
                title,
                message,
                notification_type,
                is_read,
                created_at

            FROM notifications

            WHERE student_id = %s

            ORDER BY
                created_at DESC

            LIMIT 5
            """,
            (student_id,)
        )

        notifications = cursor.fetchall()


        # =================================================
        # 7. PROGRESS SUMMARY
        # =================================================

        total_courses = course_stats["total_courses"] or 0

        completed_courses = course_stats["completed_courses"] or 0

        in_progress_courses = course_stats["in_progress_courses"] or 0

        average_progress = course_stats["average_progress"] or 0

        average_score = course_stats["average_score"] or 0

        completion_rate = (
            float(completed_courses) / float(total_courses)
            if total_courses
            else 0
        )

        readiness_score = (
            (float(average_progress) / 100 * 0.5)
            + (completion_rate * 0.3)
            + (float(average_score) / 100 * 0.2)
        )
        readiness_score = round(
            max(0.0, min(1.0, readiness_score)),
            4
        )

        cursor.execute(
            """
            UPDATE students
            SET readiness_score = %s
            WHERE id = %s
            """,
            (readiness_score, student_id)
        )
        connection.commit()
        student["readiness_score"] = readiness_score

        # =================================================
        # 8. RESPONSE
        # =================================================

        return jsonify({

            "success": True,

            "student": student,

            "stats": {

                "total_courses":
                    int(total_courses),

                "completed_courses":
                    int(completed_courses),

                "in_progress_courses":
                    int(in_progress_courses),

                "average_progress":
                    round(
                        float(
                            average_progress
                        ),
                        2
                    ),

                "average_score":
                    round(
                        float(
                            average_score
                        ),
                        2
                    ),

                "readiness_score":
                    readiness_score,

                "skill_count":
                    int(skill_count)

            },

            "recent_courses":
                recent_courses,

            "skill_gaps":
                skill_gaps,

            "notifications":
                notifications

        })


    except Exception as error:

        print(
            "Dashboard error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()