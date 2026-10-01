import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

sys.path.insert(
    0,
    str(BASE_DIR / "app" / "backend")
)


from utils.database import get_db_connection


# ============================================================
# FILE
# ============================================================

RECOMMENDATION_FILE = (
    BASE_DIR
    / "results"
    / "deployment_recommendations.csv"
)


# ============================================================
# LOAD RECOMMENDATIONS
# ============================================================

def load_recommendations():

    print("=" * 60)
    print("LOADING RECOMMENDATIONS INTO MYSQL")
    print("=" * 60)

    if not RECOMMENDATION_FILE.exists():

        print(
            "ERROR: Recommendation file not found:"
        )

        print(RECOMMENDATION_FILE)

        return

    df = pd.read_csv(
        RECOMMENDATION_FILE
    )

    print(
        "Recommendation records:",
        len(df)
    )

    required_columns = [
        "id_student",
        "course_id",
        "rank",
        "hybrid_score",
        "explanation"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        print(
            "ERROR: Missing columns:",
            missing
        )

        return

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        # ----------------------------------------------------
        # PREPARE INSERT
        # ----------------------------------------------------

        insert_query = """
            INSERT INTO recommendations
            (
                student_id,
                course_id,
                recommendation_rank,
                hybrid_score,
                explanation
            )

            SELECT
                %s,
                c.id,
                %s,
                %s,
                %s

            FROM courses c

            WHERE c.course_id = %s

            ON DUPLICATE KEY UPDATE

                recommendation_rank = VALUES(recommendation_rank),
                hybrid_score = VALUES(hybrid_score),
                explanation = VALUES(explanation)
        """

        inserted = 0
        skipped = 0

        # ----------------------------------------------------
        # INSERT RECORDS
        # ----------------------------------------------------

        for _, row in df.iterrows():

            student_id = int(
                row["id_student"]
            )

            course_id = str(
                row["course_id"]
            )

            rank = int(
                row["rank"]
            )

            hybrid_score = float(
                row["hybrid_score"]
            )

            explanation = str(
                row["explanation"]
            )

            cursor.execute(
                insert_query,
                (
                    student_id,
                    rank,
                    hybrid_score,
                    explanation,
                    course_id
                )
            )

            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        connection.commit()

        print(
            "Processed:",
            len(df)
        )

        print(
            "Inserted/updated:",
            inserted
        )

        print(
            "Skipped:",
            skipped
        )

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM recommendations
            """
        )

        total = cursor.fetchone()[0]

        print(
            "Total recommendations in database:",
            total
        )

        cursor.close()

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "ERROR:",
            error
        )

    finally:

        if connection and connection.is_connected():
            connection.close()

    print("=" * 60)
    print("RECOMMENDATION LOADING COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    load_recommendations()