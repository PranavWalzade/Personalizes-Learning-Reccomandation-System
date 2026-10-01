import sys
from pathlib import Path

import pandas as pd


# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from utils.database import get_db_connection


# Project root
PROJECT_ROOT = BACKEND_DIR.parent.parent

# Engineering course CSV
COURSE_FILE = (
    PROJECT_ROOT
    / "data"
    / "engineering"
    / "engineering_courses_extended.csv"
)


def load_courses():

    print("=" * 60)
    print("LOADING ENGINEERING COURSES")
    print("=" * 60)

    # Check CSV
    if not COURSE_FILE.exists():
        print("\nERROR: Course CSV not found.")
        print("Expected:")
        print(COURSE_FILE)
        return

    print("\nLoading CSV...")

    df = pd.read_csv(COURSE_FILE)

    print("Courses found:", len(df))

    connection = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor()

        inserted = 0
        updated = 0

        for _, row in df.iterrows():

            query = """
                SELECT id
                FROM courses
                WHERE course_id = %s
            """

            cursor.execute(
                query,
                (str(row["course_id"]),)
            )

            existing = cursor.fetchone()

            if existing:

                update_query = """
                    UPDATE courses
                    SET
                        course_name = %s,
                        branch = %s,
                        semester = %s,
                        category = %s,
                        skills = %s,
                        prerequisites = %s,
                        difficulty = %s,
                        credits = %s,
                        course_level = %s,
                        is_core = %s
                    WHERE course_id = %s
                """

                cursor.execute(
                    update_query,
                    (
                        str(row["course_name"]),
                        str(row["branch"]),
                        int(row["semester"]),
                        str(row["category"]),
                        str(row["skills"]),
                        str(row["prerequisites"]),
                        int(row["difficulty"]),
                        int(row["credits"]),
                        str(row["course_level"]),
                        bool(row["is_core"]),
                        str(row["course_id"])
                    )
                )

                updated += 1

            else:

                insert_query = """
                    INSERT INTO courses (
                        course_id,
                        course_name,
                        branch,
                        semester,
                        category,
                        skills,
                        prerequisites,
                        difficulty,
                        credits,
                        course_level,
                        is_core
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                """

                cursor.execute(
                    insert_query,
                    (
                        str(row["course_id"]),
                        str(row["course_name"]),
                        str(row["branch"]),
                        int(row["semester"]),
                        str(row["category"]),
                        str(row["skills"]),
                        str(row["prerequisites"]),
                        int(row["difficulty"]),
                        int(row["credits"]),
                        str(row["course_level"]),
                        bool(row["is_core"])
                    )
                )

                inserted += 1

        connection.commit()

        print("\n" + "=" * 60)
        print("COURSE LOADING COMPLETED")
        print("=" * 60)

        print("Inserted:", inserted)
        print("Updated:", updated)

        cursor.execute(
            "SELECT COUNT(*) FROM courses"
        )

        total = cursor.fetchone()[0]

        print("Total courses in database:", total)

        cursor.close()

    except Exception as error:

        if connection:
            connection.rollback()

        print("\nERROR:", error)

    finally:

        if connection and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    load_courses()