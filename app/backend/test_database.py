from utils.database import get_db_connection


def test_database():
    connection = None

    try:
        connection = get_db_connection()

        if connection.is_connected():
            print("=" * 60)
            print("MYSQL DATABASE CONNECTION SUCCESSFUL")
            print("=" * 60)

            cursor = connection.cursor()

            cursor.execute("SELECT DATABASE();")
            database = cursor.fetchone()

            print("Database:", database[0])

            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            print("\nTables:")

            for table in tables:
                print(" -", table[0])

            cursor.close()

    except Exception as error:
        print("=" * 60)
        print("MYSQL DATABASE CONNECTION FAILED")
        print("=" * 60)
        print("Error:", error)

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    test_database()