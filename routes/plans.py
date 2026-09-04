from flask import Blueprint, render_template, jsonify
from database.db import get_db_connection

plans_bp = Blueprint("plans", __name__)


@plans_bp.route("/plans")
def plans_page():
    return render_template("plans.html")


@plans_bp.route("/api/plans", methods=["GET"])
def get_plans():

    conn = get_db_connection()

    plans = conn.execute(
        """
        SELECT
            p.id,
            p.name,
            p.price,
            f.feature_key,
            f.feature_name
        FROM plans p
        LEFT JOIN plan_features pf
            ON p.id = pf.plan_id
        LEFT JOIN features f
            ON pf.feature_id = f.id
        ORDER BY p.id, f.id
        """
    ).fetchall()

    conn.close()

    plan_data = {}

    for plan in plans:

        plan_id = plan["id"]

        if plan_id not in plan_data:
            plan_data[plan_id] = {
                "id": plan["id"],
                "name": plan["name"],
                "price": plan["price"],
                "features": []
            }

        if plan["feature_name"]:
            plan_data[plan_id]["features"].append({
                "key": plan["feature_key"],
                "name": plan["feature_name"]
            })

    return jsonify({
        "plans": list(plan_data.values())
    }), 200