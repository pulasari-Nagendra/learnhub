from database.db import get_db_connection


def create_user(
    name,
    email,
    password,
    student_id,
    branch,
    semester,
    cgpa,
    previous_sgpa,
    backlogs
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO users (
            name,
            email,
            password,
            student_id,
            branch,
            semester,
            cgpa,
            previous_sgpa,
            backlogs
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            email,
            password,
            student_id,
            branch,
            semester,
            cgpa,
            previous_sgpa,
            backlogs
        )
    )

    connection.commit()

    user_id = cursor.lastrowid

    connection.close()

    return user_id


def get_user_by_email(email):
    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    connection.close()

    return user
def get_user_by_id(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, email, student_id, branch, semester, cgpa, previous_sgpa, backlogs "
        "FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return user