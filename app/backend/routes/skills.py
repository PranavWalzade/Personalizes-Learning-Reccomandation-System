from flask import Blueprint, jsonify, request

from utils.database import get_db_connection


skills_bp = Blueprint("skills", __name__)


def validate_skill_level(value):
    try:
        level = float(value)
    except (TypeError, ValueError):
        return None

    if not 0 <= level <= 100:
        return None

    return level


@skills_bp.route(
    "/student/<int:student_id>/skills",
    methods=["GET"]
)
def get_student_skills(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, skill_name, skill_level, source
            FROM student_skills
            WHERE student_id = %s
            ORDER BY skill_name
            """,
            (student_id,)
        )

        skills = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(skills),
            "skills": skills
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Failed to fetch student skills",
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@skills_bp.route(
    "/student/<int:student_id>/skills",
    methods=["POST"]
)
def add_student_skill(student_id):
    data = request.get_json(silent=True) or {}
    skill_name = str(data.get("skill_name") or "").strip()
    skill_level = validate_skill_level(data.get("skill_level"))

    if not skill_name:
        return jsonify({
            "success": False,
            "message": "Skill name is required"
        }), 400

    if skill_level is None:
        return jsonify({
            "success": False,
            "message": "Skill level must be between 0 and 100"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO student_skills
                (student_id, skill_name, skill_level, source)
            VALUES (%s, %s, %s, 'self-assessment')
            ON DUPLICATE KEY UPDATE
                skill_level = VALUES(skill_level),
                source = 'self-assessment'
            """,
            (student_id, skill_name, skill_level)
        )
        connection.commit()

        cursor.execute(
            """
            SELECT id, skill_name, skill_level, source
            FROM student_skills
            WHERE student_id = %s AND LOWER(skill_name) = LOWER(%s)
            LIMIT 1
            """,
            (student_id, skill_name)
        )
        skill = cursor.fetchone()

        return jsonify({
            "success": True,
            "message": "Skill saved",
            "skill": skill
        }), 201

    except Exception as error:
        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to save skill",
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@skills_bp.route(
    "/student/<int:student_id>/skills/<int:skill_id>",
    methods=["PUT"]
)
def update_student_skill(student_id, skill_id):
    data = request.get_json(silent=True) or {}
    skill_level = validate_skill_level(data.get("skill_level"))

    if skill_level is None:
        return jsonify({
            "success": False,
            "message": "Skill level must be between 0 and 100"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE student_skills
            SET skill_level = %s, source = 'self-assessment'
            WHERE id = %s AND student_id = %s
            """,
            (skill_level, skill_id, student_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            cursor.execute(
                """
                SELECT id
                FROM student_skills
                WHERE id = %s AND student_id = %s
                """,
                (skill_id, student_id)
            )
            if cursor.fetchone():
                return jsonify({
                    "success": True,
                    "message": "Skill level unchanged"
                }), 200

            return jsonify({
                "success": False,
                "message": "Skill not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Skill level updated"
        }), 200

    except Exception as error:
        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update skill",
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@skills_bp.route(
    "/student/<int:student_id>/skills/<int:skill_id>",
    methods=["DELETE"]
)
def delete_student_skill(student_id, skill_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM student_skills
            WHERE id = %s AND student_id = %s
            """,
            (skill_id, student_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Skill not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Skill removed"
        }), 200

    except Exception as error:
        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to remove skill",
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
