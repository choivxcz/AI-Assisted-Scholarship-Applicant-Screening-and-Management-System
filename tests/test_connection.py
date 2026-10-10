from database.connection import get_connection

def test_database_connection():
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, mysql_version = cursor.fetchone()

        print("Database connection successful!")
        print(f"Database: {database_name}")
        print(f"MySQL version: {mysql_version}")

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print("\nTables found:")
        for (table_name,) in tables:
            print(f"- {table_name}")

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

if __name__ == "__main__":
    test_database_connection()