from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from models.user import create_user, get_user_by_email


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    student_id = data.get("student_id")
    branch = data.get("branch")
    semester = data.get("semester")
    cgpa = data.get("cgpa")
    previous_sgpa = data.get("previous_sgpa")
    backlogs = data.get("backlogs", 0)

    if not name or not email or not password:
        return jsonify({
            "message": "Name, email and password are required"
        }), 400

    if not student_id or not branch or not semester:
        return jsonify({
            "message": "Student ID, branch and semester are required"
        }), 400

    if cgpa is None or previous_sgpa is None or backlogs is None:
        return jsonify({
            "message": "CGPA, previous SGPA and backlogs are required"
        }), 400

    try:
        cgpa = float(cgpa)
        previous_sgpa = float(previous_sgpa)
        backlogs = int(backlogs)
    except (ValueError, TypeError):
        return jsonify({
            "message": "CGPA and SGPA must be numbers, and backlogs must be a whole number"
        }), 400

    if not 0 <= cgpa <= 10:
        return jsonify({
            "message": "CGPA must be between 0 and 10"
        }), 400

    if not 0 <= previous_sgpa <= 10:
        return jsonify({
            "message": "Previous SGPA must be between 0 and 10"
        }), 400

    if backlogs < 0:
        return jsonify({
            "message": "Backlogs cannot be negative"
        }), 400

    existing_user = get_user_by_email(email)

    if existing_user:
        return jsonify({
            "message": "Email already registered"
        }), 409

    hashed_password = generate_password_hash(password)

    user_id = create_user(
        name,
        email,
        hashed_password,
        student_id,
        branch,
        semester,
        cgpa,
        previous_sgpa,
        backlogs
    )

    return jsonify({
        "message": "User registered successfully",
        "user_id": user_id
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    user = get_user_by_email(email)

    if not user:
        return jsonify({
            "message": "Invalid email or password"
        }), 401

    if not check_password_hash(user["password"], password):
        return jsonify({
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(user["id"])
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token
    }), 200