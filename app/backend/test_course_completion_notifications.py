import unittest
from unittest.mock import patch

from flask import Flask

from routes.progress import progress_bp
from routes.student_courses import student_courses_bp


class FakeCursor:
    def __init__(self, enrollment_status="in_progress", progress_exists=False):
        self.enrollment_status = enrollment_status
        self.progress_exists = progress_exists
        self.result = None
        self.queries = []
        self.closed = False

    def execute(self, query, params=()):
        sql = " ".join(query.lower().split())
        self.queries.append(sql)

        if "from courses" in sql:
            self.result = {
                "id": 12,
                "course_id": "CSE005",
                "course_name": "Learning Python"
            }
        elif "from student_courses" in sql:
            self.result = {
                "id": 34,
                "status": self.enrollment_status
            }
        elif "from progress" in sql:
            self.result = {"id": 56} if self.progress_exists else None

    def fetchone(self):
        result, self.result = self.result, None
        return result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, **cursor_options):
        self.fake_cursor = FakeCursor(**cursor_options)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, **kwargs):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class CourseCompletionNotificationTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(student_courses_bp, url_prefix="/api")
        app.register_blueprint(progress_bp, url_prefix="/api")
        self.client = app.test_client()

    def test_completing_course_creates_notification_once(self):
        connection = FakeConnection()

        with patch(
            "routes.student_courses.get_db_connection",
            return_value=connection
        ):
            response = self.client.put(
                "/api/student/4/courses/CSE005",
                json={"status": "completed"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(connection.committed)
        self.assertEqual(
            sum("insert into notifications" in query for query in connection.fake_cursor.queries),
            1
        )

    def test_repeated_completion_does_not_create_duplicate_notification(self):
        connection = FakeConnection(enrollment_status="completed")

        with patch(
            "routes.student_courses.get_db_connection",
            return_value=connection
        ):
            response = self.client.put(
                "/api/student/4/courses/CSE005",
                json={"status": "completed"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(connection.committed)
        self.assertFalse(
            any(
                "insert into notifications" in query
                for query in connection.fake_cursor.queries
            )
        )

    def test_progress_reaching_100_completes_course_and_notifies(self):
        connection = FakeConnection()

        with patch(
            "routes.progress.get_db_connection",
            return_value=connection
        ):
            response = self.client.put(
                "/api/student/4/progress/CSE005",
                json={
                    "progress_percent": 100,
                    "time_spent_minutes": 60
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(connection.committed)
        queries = connection.fake_cursor.queries
        self.assertTrue(
            any("set status = 'completed'" in query for query in queries)
        )
        self.assertEqual(
            sum("insert into notifications" in query for query in queries),
            1
        )

    def test_progress_update_for_completed_course_does_not_duplicate_notification(self):
        connection = FakeConnection(enrollment_status="completed")

        with patch(
            "routes.progress.get_db_connection",
            return_value=connection
        ):
            response = self.client.put(
                "/api/student/4/progress/CSE005",
                json={
                    "progress_percent": 100,
                    "time_spent_minutes": 60
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(connection.committed)
        self.assertFalse(
            any(
                "insert into notifications" in query
                for query in connection.fake_cursor.queries
            )
        )


if __name__ == "__main__":
    unittest.main()
