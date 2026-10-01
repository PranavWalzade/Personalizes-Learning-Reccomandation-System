import unittest
from unittest.mock import patch

from flask import Flask

from routes.student_courses import student_courses_bp


class FakeCursor:
    def __init__(self, course_exists=True, enrolled=True, fail_on_delete=False):
        self.course_exists = course_exists
        self.enrolled = enrolled
        self.fail_on_delete = fail_on_delete
        self.result = None
        self.queries = []
        self.closed = False

    def execute(self, query, params=()):
        sql = " ".join(query.lower().split())
        self.queries.append(sql)

        if "from courses" in sql:
            self.result = {"id": 12} if self.course_exists else None
        elif "from student_courses" in sql:
            self.result = {"id": 34} if self.enrolled else None
        elif self.fail_on_delete and "delete from progress" in sql:
            raise RuntimeError("Simulated database error")

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


class StudentCourseDeleteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(student_courses_bp, url_prefix="/api")
        self.client = app.test_client()

    def test_delete_removes_enrollment_and_saved_progress(self):
        connection = FakeConnection()

        with patch(
            "routes.student_courses.get_db_connection",
            return_value=connection
        ):
            response = self.client.delete(
                "/api/student/4/courses/CSE005"
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(connection.closed)
        self.assertTrue(connection.fake_cursor.closed)
        self.assertIn(
            "delete from progress where student_id = %s and course_id = %s",
            connection.fake_cursor.queries
        )
        self.assertIn(
            "delete from student_courses where student_id = %s and course_id = %s",
            connection.fake_cursor.queries
        )

    def test_delete_rejects_course_the_student_is_not_enrolled_in(self):
        connection = FakeConnection(enrolled=False)

        with patch(
            "routes.student_courses.get_db_connection",
            return_value=connection
        ):
            response = self.client.delete(
                "/api/student/4/courses/CSE005"
            )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(connection.committed)
        self.assertFalse(
            any(
                query.startswith("delete from")
                for query in connection.fake_cursor.queries
            )
        )

    def test_delete_rolls_back_when_database_operation_fails(self):
        connection = FakeConnection(fail_on_delete=True)

        with patch(
            "routes.student_courses.get_db_connection",
            return_value=connection
        ):
            response = self.client.delete(
                "/api/student/4/courses/CSE005"
            )

        self.assertEqual(response.status_code, 500)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
