from flask import Blueprint, request, jsonify
import sqlite3
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

subscriptions_bp = Blueprint("subscriptions", __name__)


def get_db_connection():
    conn = sqlite3.connect("learnhub.db")
    conn.row_factory = sqlite3.Row
    return conn


@subscriptions_bp.route("/api/plans", methods=["GET"])
def get_plans():
    conn = get_db_connection()

    plans = conn.execute(
        "SELECT id, name, price, features FROM plans"
    ).fetchall()

    conn.close()

    return jsonify({
        "plans": [dict(plan) for plan in plans]
    })




@subscriptions_bp.route("/api/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    user_id = get_jwt_identity()

    data = request.get_json()
    plan_id = data.get("plan_id")

    if not plan_id:
        return jsonify({"message": "plan_id is required"}), 400

    conn = get_db_connection()

    # Check whether the selected plan exists
    plan = conn.execute(
        "SELECT * FROM plans WHERE id = ?",
        (plan_id,)
    ).fetchone()

    if not plan:
        conn.close()
        return jsonify({"message": "Plan not found"}), 404

    # Check if user already has an active subscription
    existing = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active'",
        (user_id,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "message": "User already has an active subscription"
        }), 400

    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    conn.execute(
        """
        INSERT INTO subscriptions
        (user_id, plan_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            plan_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            "active"
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subscription created successfully",
        "plan": plan["name"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "status": "active"
    }), 201

@subscriptions_bp.route("/api/my-subscription", methods=["GET"])
@jwt_required()
def my_subscription():
    user_id = get_jwt_identity()

    conn = get_db_connection()

    subscription = conn.execute(
        """
        SELECT
            subscriptions.id,
            subscriptions.start_date,
            subscriptions.end_date,
            subscriptions.status,
            plans.name AS plan_name,
            plans.price
        FROM subscriptions
        JOIN plans ON subscriptions.plan_id = plans.id
        WHERE subscriptions.user_id = ?
        AND subscriptions.status = 'active'
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not subscription:
        return jsonify({
            "message": "No active subscription found"
        }), 404

    return jsonify({
        "subscription": dict(subscription)
    })
@subscriptions_bp.route("/api/change-subscription", methods=["POST"])
@jwt_required()
def change_subscription():

    user_id = get_jwt_identity()
    data = request.get_json()

    new_plan_id = data.get("plan_id")

    if not new_plan_id:
        return jsonify({
            "message": "plan_id is required"
        }), 400

    conn = get_db_connection()

    # Check whether the new plan exists
    new_plan = conn.execute(
        "SELECT * FROM plans WHERE id = ?",
        (new_plan_id,)
    ).fetchone()

    if not new_plan:
        conn.close()
        return jsonify({
            "message": "Plan not found"
        }), 404

    # Get user's current active subscription
    current_subscription = conn.execute(
        """
        SELECT *
        FROM subscriptions
        WHERE user_id = ?
        AND status = 'active'
        """,
        (user_id,)
    ).fetchone()

    if not current_subscription:
        conn.close()
        return jsonify({
            "message": "No active subscription found"
        }), 404

    # Check if user selected the same plan
    if current_subscription["plan_id"] == new_plan_id:
        conn.close()
        return jsonify({
            "message": "You are already subscribed to this plan"
        }), 400

    # Change the plan
    conn.execute(
        """
        UPDATE subscriptions
        SET plan_id = ?
        WHERE id = ?
        """,
        (
            new_plan_id,
            current_subscription["id"]
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Subscription changed successfully",
        "plan": new_plan["name"],
        "price": new_plan["price"],
        "status": "active"
    }), 200

@subscriptions_bp.route("/api/cancel-subscription", methods=["POST"])
@jwt_required()
def cancel_subscription():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    subscription = conn.execute(
        """
        SELECT *
        FROM subscriptions
        WHERE user_id = ?
        AND status = 'active'
        """,
        (user_id,)
    ).fetchone()

    if not subscription:
        conn.close()
        return jsonify({
            "message": "No active subscription found"
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