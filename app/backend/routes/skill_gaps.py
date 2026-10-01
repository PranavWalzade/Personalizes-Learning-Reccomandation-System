from flask import Blueprint, jsonify
from utils.database import get_db_connection


skill_gaps_bp = Blueprint("skill_gaps", __name__)


def calculate_required_level(difficulty):
    """
    Convert course difficulty into the minimum
    skill level required.
    """

    difficulty = int(difficulty)

    required_levels = {
        1: 50,
        2: 60,
        3: 70,
        4: 80,
        5: 90
    }

    return required_levels.get(difficulty, 70)


def get_priority(gap_score):
    """
    Convert gap score into priority.
    """

    if gap_score >= 0.50:
        return "high"

    if gap_score >= 0.25:
        return "medium"

    return "low"


@skill_gaps_bp.route(
    "/student/<int:student_id>/skill-gaps",
    methods=["GET"]
)
def get_skill_gaps(student_id):

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                skill_name,
                current_level,
                required_level,
                gap_score,
                priority
            FROM skill_gaps
            WHERE student_id = %s
            ORDER BY gap_score DESC, priority ASC
        """

        cursor.execute(query, (student_id,))
        gaps = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "count": len(gaps),
            "skill_gaps": gaps
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Failed to fetch skill gaps",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


@skill_gaps_bp.route(
    "/student/<int:student_id>/skill-gaps/generate",
    methods=["POST"]
)
def generate_skill_gaps(student_id):

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # 1. Check student
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                branch,
                semester
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

        # -------------------------------------------------
        # 2. Get student's current skills
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                skill_name,
                skill_level
            FROM student_skills
            WHERE student_id = %s
            """,
            (student_id,)
        )

        student_skills = cursor.fetchall()

        skill_map = {}

        for skill in student_skills:

            skill_name = skill["skill_name"].strip().lower()

            skill_map[skill_name] = float(
                skill["skill_level"] or 0
            )

        # -------------------------------------------------
        # 3. Get relevant engineering courses
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                course_id,
                course_name,
                branch,
                semester,
                skills,
                difficulty
            FROM courses
            ORDER BY semester, course_name
            """
        )

        courses = cursor.fetchall()

        # -------------------------------------------------
        # 4. Collect required skills
        # -------------------------------------------------

        skill_requirements = {}

        for course in courses:

            course_branch = (
                course["branch"] or ""
            ).strip().lower()

            student_branch = (
                student["branch"] or ""
            ).strip().lower()

            # Include common/all-engineering courses
            # and courses matching student's branch.
            branch_matches = (
                course_branch == ""
                or course_branch == "all engineering"
                or course_branch == student_branch
            )

            if not branch_matches:
                continue

            skills_text = course["skills"] or ""

            required_level = calculate_required_level(
                course["difficulty"] or 3
            )

            skills = skills_text.split(";")

            for skill in skills:

                skill = skill.strip()

                if not skill:
                    continue

                normalized_skill = skill.lower()

                if normalized_skill not in skill_requirements:

                    skill_requirements[normalized_skill] = {
                        "skill_name": skill,
                        "required_level": required_level
                    }

                else:

                    skill_requirements[
                        normalized_skill
                    ]["required_level"] = max(
                        skill_requirements[
                            normalized_skill
                        ]["required_level"],
                        required_level
                    )

        # -------------------------------------------------
        # 5. Generate skill gaps
        # -------------------------------------------------

        generated_gaps = []

        for normalized_skill, requirement in skill_requirements.items():

            skill_name = requirement["skill_name"]

            required_level = float(
                requirement["required_level"]
            )

            current_level = float(
                skill_map.get(normalized_skill, 0)
            )

            gap = max(
                required_level - current_level,
                0
            )

            gap_score = gap / 100

            priority = get_priority(gap_score)

            # Ignore completely satisfied skills.
            if gap_score <= 0:
                continue

            generated_gaps.append({
                "skill_name": skill_name,
                "current_level": round(current_level, 2),
                "required_level": round(required_level, 2),
                "gap_score": round(gap_score, 4),
                "priority": priority
            })

        # -------------------------------------------------
        # 6. Save gaps to MySQL
        # -------------------------------------------------

        cursor.execute(
            """
            DELETE FROM skill_gaps
            WHERE student_id = %s
            """,
            (student_id,)
        )

        for gap in generated_gaps:

            cursor.execute(
                """
                INSERT INTO skill_gaps
                (
                    student_id,
                    skill_name,
                    current_level,
                    required_level,
                    gap_score,
                    priority
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON DUPLICATE KEY UPDATE
                    current_level = VALUES(current_level),
                    required_level = VALUES(required_level),
                    gap_score = VALUES(gap_score),
                    priority = VALUES(priority)
                """,
                (
                    student_id,
                    gap["skill_name"],
                    gap["current_level"],
                    gap["required_level"],
                    gap["gap_score"],
                    gap["priority"]
                )
            )

        connection.commit()

        cursor.close()

        # -------------------------------------------------
        # 7. Return result
        # -------------------------------------------------

        generated_gaps.sort(
            key=lambda x: x["gap_score"],
            reverse=True
        )

        return jsonify({
            "success": True,
            "message": "Skill gaps generated successfully",
            "count": len(generated_gaps),
            "skill_gaps": generated_gaps
        }), 200

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to generate skill gaps",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()