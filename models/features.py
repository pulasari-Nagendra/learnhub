from database.db import get_db_connection


def user_has_feature(user_id, feature_key):
    connection = get_db_connection()

    cursor = connection.execute(
        """
        SELECT 1
        FROM subscriptions s
        JOIN plans p
            ON s.plan_id = p.id
        JOIN plan_features pf
            ON p.id = pf.plan_id
        JOIN features f
            ON pf.feature_id = f.id
        WHERE s.user_id = ?
          AND s.status = 'active'
          AND f.feature_key = ?
        LIMIT 1
        """,
        (user_id, feature_key)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None