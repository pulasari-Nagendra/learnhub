from flask import Blueprint, jsonify, request

from flask_jwt_extended import jwt_required, get_jwt_identity

from google import genai
from google.genai import types

from models.features import user_has_feature
from database.db import get_db_connection

import os


ai_bp = Blueprint("ai", __name__)


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# Helper: verify Premium access
# ============================================================

def has_ai_access(user_id):

    return user_has_feature(
        user_id,
        "ai_assistant"
    )


# ============================================================
# Create a new conversation
# ============================================================

@ai_bp.route("/api/ai/conversations", methods=["POST"])
@jwt_required()
def create_conversation():

    user_id = get_jwt_identity()

    if not has_ai_access(user_id):

        return jsonify({
            "message": (
                "AI Study Assistant is available "
                "only with the Premium plan."
            )
        }), 403

    try:

        connection = get_db_connection()

        cursor = connection.execute(
            """
            INSERT INTO ai_conversations
            (user_id, title)
            VALUES (?, ?)
            """,
            (
                user_id,
                "New Conversation"
            )
        )

        conversation_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return jsonify({
            "conversation_id": conversation_id,
            "title": "New Conversation"
        }), 201

    except Exception as error:

        print("CREATE CONVERSATION ERROR:", error)

        return jsonify({
            "message": "Unable to create a new conversation."
        }), 500


# ============================================================
# Get user's conversations
# ============================================================

@ai_bp.route("/api/ai/conversations", methods=["GET"])
@jwt_required()
def get_conversations():

    user_id = get_jwt_identity()

    if not has_ai_access(user_id):

        return jsonify({
            "message": (
                "AI Study Assistant is available "
                "only with the Premium plan."
            )
        }), 403

    try:

        connection = get_db_connection()

        rows = connection.execute(
            """
            SELECT
                id,
                title,
                created_at,
                updated_at
            FROM ai_conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,)
        ).fetchall()

        connection.close()

        conversations = []

        for row in rows:

            conversations.append({
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })

        return jsonify({
            "conversations": conversations
        }), 200

    except Exception as error:

        print("GET CONVERSATIONS ERROR:", error)

        return jsonify({
            "message": "Unable to load your conversations."
        }), 500


# ============================================================
# Get messages for one conversation
# ============================================================

@ai_bp.route(
    "/api/ai/conversations/<int:conversation_id>",
    methods=["GET"]
)
@jwt_required()
def get_conversation(conversation_id):

    user_id = get_jwt_identity()

    if not has_ai_access(user_id):

        return jsonify({
            "message": (
                "AI Study Assistant is available "
                "only with the Premium plan."
            )
        }), 403

    try:

        connection = get_db_connection()

        # Verify conversation belongs to current user
        conversation = connection.execute(
            """
            SELECT id, title
            FROM ai_conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        ).fetchone()

        if not conversation:

            connection.close()

            return jsonify({
                "message": "Conversation not found."
            }), 404


        rows = connection.execute(
            """
            SELECT role, message, created_at
            FROM ai_messages
            WHERE conversation_id = ?
              AND user_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (
                conversation_id,
                user_id
            )
        ).fetchall()

        connection.close()

        messages = []

        for row in rows:

            messages.append({
                "role": row["role"],
                "message": row["message"],
                "created_at": row["created_at"]
            })

        return jsonify({
            "conversation": {
                "id": conversation["id"],
                "title": conversation["title"]
            },
            "messages": messages
        }), 200

    except Exception as error:

        print("GET CONVERSATION ERROR:", error)

        return jsonify({
            "message": "Unable to load this conversation."
        }), 500


# ============================================================
# Send message
# ============================================================

@ai_bp.route("/api/ai/chat", methods=["POST"])
@jwt_required()
def ai_chat():

    user_id = get_jwt_identity()

    if not has_ai_access(user_id):

        return jsonify({
            "message": (
                "AI Study Assistant is available "
                "only with the Premium plan."
            )
        }), 403


    data = request.get_json(silent=True) or {}

    user_message = str(
        data.get("message", "")
    ).strip()

    conversation_id = data.get(
        "conversation_id"
    )


    if not user_message:

        return jsonify({
            "message": "Please enter a question."
        }), 400


    if not conversation_id:

        return jsonify({
            "message": (
                "Please select or create a conversation first."
            )
        }), 400


    try:

        connection = get_db_connection()


        # ------------------------------------------------
        # Verify conversation belongs to this user
        # ------------------------------------------------

        conversation = connection.execute(
            """
            SELECT id, title
            FROM ai_conversations
            WHERE id = ?
              AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        ).fetchone()


        if not conversation:

            connection.close()

            return jsonify({
                "message": "Conversation not found."
            }), 404


        # ------------------------------------------------
        # Load selected conversation history
        # ------------------------------------------------

        history_rows = connection.execute(
            """
            SELECT role, message
            FROM ai_messages
            WHERE conversation_id = ?
              AND user_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (
                conversation_id,
                user_id
            )
        ).fetchall()


        connection.close()


        # ------------------------------------------------
        # Convert history to Gemini format
        # ------------------------------------------------

        contents = []


        for row in history_rows[-20:]:

            role = row["role"]

            gemini_role = (
                "user"
                if role == "user"
                else "model"
            )

            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[
                        types.Part(
                            text=row["message"]
                        )
                    ]
                )
            )


        # Current question
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=user_message
                    )
                ]
            )
        )


        # ------------------------------------------------
        # Ask Gemini
        # ------------------------------------------------

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents
        )


        if not response.text:

            return jsonify({
                "message": (
                    "The AI could not generate a response. "
                    "Please try again."
                )
            }), 502


        ai_message = response.text.strip()


        # ------------------------------------------------
        # Save messages
        # ------------------------------------------------

        connection = get_db_connection()


        connection.execute(
            """
            INSERT INTO ai_messages
            (
                user_id,
                conversation_id,
                role,
                message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                conversation_id,
                "user",
                user_message
            )
        )


        connection.execute(
            """
            INSERT INTO ai_messages
            (
                user_id,
                conversation_id,
                role,
                message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                conversation_id,
                "assistant",
                ai_message
            )
        )


        # ------------------------------------------------
        # Automatically give conversation a title
        # ------------------------------------------------

        current_title = conversation["title"]

        if current_title == "New Conversation":

            new_title = user_message[:60]

            if len(user_message) > 60:
                new_title += "..."

            connection.execute(
                """
                UPDATE ai_conversations
                SET title = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    new_title,
                    conversation_id,
                    user_id
                )
            )


        # ------------------------------------------------
        # Update conversation timestamp
        # ------------------------------------------------

        connection.execute(
            """
            UPDATE ai_conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )


        connection.commit()
        connection.close()


        return jsonify({
            "conversation_id": conversation_id,
            "message": ai_message
        }), 200


    except Exception as error:

        print("GEMINI ERROR:", error)

        return jsonify({
            "message": (
                "We're unable to process your question "
                "right now. Please try again shortly."
            )
        }), 500