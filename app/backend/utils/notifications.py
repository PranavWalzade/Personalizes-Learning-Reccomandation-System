def insert_notification(
    cursor,
    student_id,
    title,
    message,
    notification_type
):
    cursor.execute(
        """
        INSERT INTO notifications
        (
            student_id,
            title,
            message,
            notification_type,
            is_read
        )
        VALUES (%s, %s, %s, %s, FALSE)
        """,
        (
            student_id,
            title,
            message,
            notification_type
        )
    )
