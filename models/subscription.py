from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.db import get_db_connection


subscriptions_bp = Blueprint("subscriptions", __name__)


# Get all available plans
@subscriptions_bp.route("/api/plans", methods=["GET"])
def get_plans():

    conn = get_db_connection()

    plans = conn.execute("""
        SELECT
            p.id,
            p.name,
            p.price,
            p.features
        FROM plans p
        ORDER BY p.price
    """).fetchall()

    conn.close()

    return jsonify([
        {
            "id": plan["id"],
            "name": plan["name"],
            "price": plan["price"],
            "features": plan["features"]
        }
        for plan in plans
    ]), 200


# Get current user's subscription
@subscriptions_bp.route("/api/my-subscription", methods=["GET"])
@jwt_required()
def my_subscription():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    subscription = conn.execute("""
        SELECT
        s.id,
        s.user_id,
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
    """, (user_id,)).fetchone()

    conn.close()

    if not subscription:
        return jsonify({
            "message": "No active subscription"
        }), 404

    return jsonify({
        "subscription": {
        "id": subscription["id"],
        "user_id": subscription["user_id"],
        "plan_id": subscription["plan_id"],
        "plan": subscription["plan_name"],
        "price": subscription["price"],
        "start_date": subscription["start_date"],
        "end_date": subscription["end_date"],
        "status": subscription["status"]
        }
    }), 200


# Get features available to the logged-in user
@subscriptions_bp.route("/api/my-features", methods=["GET"])
@jwt_required()
def my_features():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    features = conn.execute("""
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
    """, (user_id,)).fetchall()

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