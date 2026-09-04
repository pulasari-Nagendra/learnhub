from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.db import get_db_connection


subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.route("/api/my-subscription", methods=["GET"])
@jwt_required()
def my_subscription():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    subscription = conn.execute(
        """
        SELECT
        s.id,
        s.plan_id,
        p.name AS plan_name,
        p.price,
        s.start_date,
        s.end_date,
        s.status
        FROM subscriptions s
        JOIN plans p
            ON s.plan_id = p.id
        WHERE s.user_id = ?
          AND s.status = 'active'
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not subscription:
        return jsonify({
            "message": "No active subscription"
        }), 404

    return jsonify({
        "subscription": {
            "id": subscription["id"],
            "plan_id": subscription["plan_id"],
            "plan": subscription["plan_name"],
            "price": subscription["price"],
            "start_date": subscription["start_date"],
            "end_date": subscription["end_date"],
            "status": subscription["status"]
        }
    }), 200


@subscriptions_bp.route("/api/my-features", methods=["GET"])
@jwt_required()
def my_features():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    features = conn.execute(
        """
        SELECT
            f.feature_key,
            f.feature_name
        FROM subscriptions s
        JOIN plan_features pf
            ON s.plan_id = pf.plan_id
        JOIN features f
            ON pf.feature_id = f.id
        WHERE s.user_id = ?
          AND s.status = 'active'
        ORDER BY f.id
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    return jsonify({
        "features": [
            {
                "key": feature["feature_key"],
                "name": feature["feature_name"]
            }
            for feature in features
        ]
    }), 200
@subscriptions_bp.route("/api/plans", methods=["GET"])
def get_plans():

    conn = get_db_connection()

    plans = conn.execute(
        """
        SELECT
            id,
            name,
            price,
            features
        FROM plans
        ORDER BY id
        """
    ).fetchall()

    conn.close()

    return jsonify({
        "plans": [
            {
                "id": plan["id"],
                "name": plan["name"],
                "price": plan["price"],
                "features": plan["features"]
            }
            for plan in plans
        ]
    }), 200
@subscriptions_bp.route("/api/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    user_id = get_jwt_identity()

    data = request.get_json()

    if not data or "plan_id" not in data:
        return jsonify({
            "message": "plan_id is required"
        }), 400

    plan_id = data["plan_id"]

    conn = get_db_connection()

    # Check whether plan exists
    plan = conn.execute(
        "SELECT id, name, price FROM plans WHERE id = ?",
        (plan_id,)
    ).fetchone()

    if not plan:
        conn.close()
        return jsonify({
            "message": "Plan not found"
        }), 404

    # Check existing active subscription
    existing = conn.execute(
        """
        SELECT id, plan_id
        FROM subscriptions
        WHERE user_id = ?
          AND status = 'active'
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if existing:
        # If already on the selected plan
        if existing["plan_id"] == plan_id:
            conn.close()
            return jsonify({
                "message": "You are already subscribed to this plan"
            }), 400

        # Cancel current plan
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'cancelled'
            WHERE id = ?
            """,
            (existing["id"],)
        )

    # Create new subscription
    conn.execute(
        """
        INSERT INTO subscriptions
        (user_id, plan_id, start_date, end_date, status)
        VALUES (
            ?,
            ?,
            CURRENT_TIMESTAMP,
            DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 30 DAY),
            'active'
        )
        """,
        (user_id, plan_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subscription created successfully",
        "plan": plan["name"],
        "price": plan["price"]
    }), 200


@subscriptions_bp.route("/api/cancel-subscription", methods=["POST"])
@jwt_required()
def cancel_subscription():
    user_id = get_jwt_identity()

    conn = get_db_connection()

    subscription = conn.execute(
        """
        SELECT id
        FROM subscriptions
        WHERE user_id = ?
          AND status = 'active'
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if not subscription:
        conn.close()
        return jsonify({
            "message": "No active subscription"
        }), 404

    conn.execute(
        """
        UPDATE subscriptions
        SET status = 'cancelled'
        WHERE id = ?
        """,
        (subscription["id"],)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subscription cancelled successfully"
    }), 200