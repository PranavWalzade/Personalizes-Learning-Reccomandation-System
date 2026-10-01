
from flask import Blueprint, jsonify
from utils.database import get_db_connection


learning_path_bp = Blueprint("learning_path", __name__)


def normalize_text(value):
    """Convert text to a normalized lowercase string."""
    if value is None:
        return ""

    return str(value).strip().lower()


def parse_list(value):
    """Convert semicolon-separated text into a list."""
    if not value:
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


@learning_path_bp.route(
    "/student/<int:student_id>/learning-path",
    methods=["GET"]
)
def get_learning_path(student_id):

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get active learning path
        cursor.execute(
            """
            SELECT
                id,
                path_name,
                description,
                total_courses,
                estimated_hours,
                status,
                created_at
            FROM learning_paths
            WHERE student_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (student_id,)
        )

        path = cursor.fetchone()

        if not path:
            cursor.close()

            return jsonify({
                "success": True,
                "message": "No learning path found",
                "learning_path": None,
                "courses": []
            }), 200

        # Get courses in the learning path
        cursor.execute(
            """
            SELECT
                lpc.id,
                lpc.sequence_number,
                lpc.status,
                c.course_id,
                c.course_name,
                c.branch,
                c.semester,
                c.category,
                c.skills,
                c.prerequisites,
                c.difficulty,
                c.credits,
                c.course_level
            FROM learning_path_courses lpc
            JOIN courses c
                ON lpc.course_id = c.id
            WHERE lpc.learning_path_id = %s
            ORDER BY lpc.sequence_number
            """,
            (path["id"],)
        )

        courses = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "learning_path": path,
            "courses": courses
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to fetch learning path",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


@learning_path_bp.route(
    "/student/<int:student_id>/learning-path/generate",
    methods=["POST"]
)
def generate_learning_path(student_id):

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # 1. Get student information
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                student_name,
                branch,
                semester,
                preferred_difficulty,
                readiness_score
            FROM students
            WHERE id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            cursor.close()

            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        student_branch = normalize_text(
            student["branch"]
        )

        student_semester = int(
            student["semester"] or 1
        )

        # -------------------------------------------------
        # 2. Get skill gaps
        # -------------------------------------------------

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
            ORDER BY gap_score DESC
            """,
            (student_id,)
        )

        gaps = cursor.fetchall()

        # If skill gaps don't exist, generate them first
        if not gaps:

            cursor.close()

            return jsonify({
                "success": False,
                "message": "No skill gaps found. Generate skill gaps first."
            }), 400

        # -------------------------------------------------
        # 3. Get student's completed/in-progress courses
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                c.id,
                c.course_id,
                c.course_name,
                sc.status
            FROM student_courses sc
            JOIN courses c
                ON sc.course_id = c.id
            WHERE sc.student_id = %s
            """,
            (student_id,)
        )

        student_courses = cursor.fetchall()

        completed_courses = {
            row["course_id"]
            for row in student_courses
            if row["status"] == "completed"
        }

        # -------------------------------------------------
        # 4. Get engineering courses
        # -------------------------------------------------

        cursor.execute(
            """
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
                course_level
            FROM courses
            ORDER BY semester, difficulty
            """
        )

        all_courses = cursor.fetchall()

        # -------------------------------------------------
        # 5. Select courses that can reduce skill gaps
        # -------------------------------------------------

        gap_skills = {
            normalize_text(gap["skill_name"])
            for gap in gaps
        }

        candidate_courses = []

        for course in all_courses:

            course_id = course["course_id"]

            # Don't recommend courses already completed.
            if course_id in completed_courses:
                continue

            course_branch = normalize_text(
                course["branch"]
            )

            # Match student's branch or common engineering.
            branch_match = (
                course_branch == student_branch
                or course_branch == ""
                or course_branch == "all engineering"
            )

            if not branch_match:
                continue

            course_skills = parse_list(
                course["skills"]
            )

            normalized_course_skills = {
                normalize_text(skill)
                for skill in course_skills
            }

            matched_skills = (
                gap_skills &
                normalized_course_skills
            )

            if not matched_skills:
                continue

            # More matching gap skills = better course.
            skill_match_score = (
                len(matched_skills) /
                max(len(gap_skills), 1)
            )

            # Prefer courses around the student's level.
            course_semester = int(
                course["semester"] or 1
            )

            semester_distance = abs(
                course_semester -
                student_semester
            )

            semester_fit = 1 / (
                1 + semester_distance
            )

            # Difficulty preference.
            difficulty = float(
                course["difficulty"] or 3
            )

            preferred_difficulty = float(
                student["preferred_difficulty"] or 3
            )

            difficulty_fit = 1 - (
                abs(
                    difficulty -
                    preferred_difficulty
                ) / 4
            )

            difficulty_fit = max(
                0,
                min(1, difficulty_fit)
            )

            # Final course score.
            course_score = (
                0.60 * skill_match_score
                + 0.25 * semester_fit
                + 0.15 * difficulty_fit
            )

            candidate_courses.append({
                "course": course,
                "matched_skills": list(matched_skills),
                "course_score": course_score
            })

        # -------------------------------------------------
        # 6. Sort candidates
        # -------------------------------------------------

        candidate_courses.sort(
            key=lambda x: x["course_score"],
            reverse=True
        )

        # Keep a manageable learning path.
        selected_courses = candidate_courses[:8]

        # -------------------------------------------------
        # 7. Create learning path
        # -------------------------------------------------

        # Mark previous generated paths as completed/archived.
        cursor.execute(
            """
            UPDATE learning_paths
            SET status = 'completed'
            WHERE student_id = %s
            AND status = 'active'
            """,
            (student_id,)
        )

        path_name = "Personalized Engineering Learning Path"

        description = (
            "A personalized course sequence_number generated "
            "from the student's skill gaps, branch, "
            "semester and learning preferences."
        )

        total_courses = len(selected_courses)

        # Estimate 12 hours per credit.
        estimated_hours = 0

        for item in selected_courses:

            credits = float(
                item["course"]["credits"] or 3
            )

            estimated_hours += credits * 12

        cursor.execute(
            """
            INSERT INTO learning_paths
            (
                student_id,
                path_name,
                description,
                total_courses,
                estimated_hours,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                'active'
            )
            """,
            (
                student_id,
                path_name,
                description,
                total_courses,
                estimated_hours
            )
        )

        learning_path_id = cursor.lastrowid

        # -------------------------------------------------
        # 8. Insert courses into learning path
        # -------------------------------------------------

        sequence_number = 1

        for item in selected_courses:

            course = item["course"]

            cursor.execute(
                """
                INSERT INTO learning_path_courses
                (
                    learning_path_id,
                    course_id,
                    sequence_number,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'available'
                )
                """,
                (
                    learning_path_id,
                    course["id"],
                    sequence_number
                )
            )

            sequence_number += 1

        connection.commit()

        # -------------------------------------------------
        # 9. Build response
        # -------------------------------------------------

        response_courses = []

        for item in selected_courses:

            course = item["course"]

            response_courses.append({
                "sequence_number": response_courses.__len__() + 1,
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "branch": course["branch"],
                "semester": course["semester"],
                "difficulty": course["difficulty"],
                "credits": course["credits"],
                "matched_skills": item["matched_skills"],
                "course_score": round(
                    item["course_score"],
                    4
                )
            })

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Personalized learning path generated successfully",
            "learning_path_id": learning_path_id,
            "total_courses": total_courses,
            "estimated_hours": estimated_hours,
            "courses": response_courses
        }), 200

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to generate learning path",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()
