from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")

        if not name or not email or not password:
            return jsonify({
                "success": False,
                "message": "Name, email and password are required"
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password, phone, role)
            VALUES (%s, %s, %s, %s, 'user')
            """,
            (name, email, hashed_password, phone)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Registration successful"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, password, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user or not check_password_hash(
            user["password"],
            password
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["name"] = user["name"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


@auth_bp.route("/api/me", methods=["GET"])
def current_user():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session["user_id"],
            "name": session["name"],
            "role": session["role"]
        }
    })
@auth_bp.route("/api/profile", methods=["GET"])
def profile():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, phone, role, created_at
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "user": user
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@auth_bp.route("/api/change-password", methods=["POST"])
def change_password():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        data = request.get_json()

        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return jsonify({
                "success": False,
                "message": "Both passwords are required"
            }), 400

        if len(new_password) < 6:
            return jsonify({
                "success": False,
                "message": "New password must contain at least 6 characters"
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password"],
            current_password
        ):

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Current password is incorrect"
            }), 401

        hashed_password = generate_password_hash(
            new_password,
            method="pbkdf2:sha256"
        )

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (
                hashed_password,
                session["user_id"]
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500