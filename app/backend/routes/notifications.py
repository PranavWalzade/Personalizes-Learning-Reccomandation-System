from flask import Blueprint, jsonify, request
from utils.database import get_db_connection
from utils.notifications import insert_notification

notifications_bp = Blueprint(
    "notifications",
    __name__
)

# ---------------------------------------------------------
# GET NOTIFICATIONS
# ---------------------------------------------------------

@notifications_bp.route(
    "/student/<int:student_id>/notifications",
    methods=["GET"]
)
def get_notifications(student_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                student_id,
                title,
                message,
                notification_type,
                is_read,
                created_at
            FROM notifications
            WHERE student_id = %s
            ORDER BY created_at DESC
        """

        cursor.execute(query, (student_id,))

        notifications = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(notifications),
            "notifications": notifications
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to fetch notifications",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
# ---------------------------------------------------------
# CREATE NOTIFICATION
# ---------------------------------------------------------

@notifications_bp.route(
    "/student/<int:student_id>/notifications",
    methods=["POST"]
)
def create_notification(student_id):

    connection = None

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        title = str(
            data.get("title", "")
        ).strip()

        message = str(
            data.get("message", "")
        ).strip()

        notification_notification_type = str(
            data.get("notification_type", "info")
        ).strip()

        if not title:
            return jsonify({
                "success": False,
                "message": "Title is required"
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "message": "Message is required"
            }), 400

        allowed_notification_types = {
            "info",
            "success",
            "warning",
            "recommendation",
            "progress",
            "skill_gap"
        }

        if notification_notification_type not in allowed_notification_types:
            notification_notification_type = "info"

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check student
        cursor.execute(
            """
            SELECT id
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

        insert_notification(
            cursor,
            student_id,
            title,
            message,
            notification_notification_type
        )

        notification_id = cursor.lastrowid

        connection.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Notification created successfully",
            "notification_id": notification_id
        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to create notification",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# MARK ONE NOTIFICATION AS READ
# ---------------------------------------------------------

@notifications_bp.route(
    "/student/<int:student_id>/notifications/<int:notification_id>/read",
    methods=["PUT"]
)
def mark_notification_read(student_id, notification_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            UPDATE notifications
            SET is_read = 1
            WHERE id = %s
              AND student_id = %s
        """

        cursor.execute(
            query,
            (notification_id, student_id)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Notification not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        }), 200

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to mark notification as read",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# ---------------------------------------------------------
# MARK ALL NOTIFICATIONS AS READ
# ---------------------------------------------------------

@notifications_bp.route(
    "/student/<int:student_id>/notifications/read-all",
    methods=["PUT"]
)
def mark_all_notifications_read(student_id):

    connection = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE student_id = %s
            AND is_read = FALSE
            """,
            (student_id,)
        )

        updated_count = cursor.rowcount

        connection.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "All notifications marked as read",
            "updated_count": updated_count
        }), 200

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update notifications",
            "error": str(error)
        }), 500

    finally:

        if connection and connection.is_connected():
            connection.close()
