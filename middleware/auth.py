from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "message": "Authentication required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


def get_current_user_id():
    return int(get_jwt_identity())