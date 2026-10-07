import os

from flask import Flask, jsonify, session
from flask_cors import CORS
from extensions import mail
from dotenv import load_dotenv

from routes.auth import auth_bp
from routes.loan import loan_bp
from routes.admin import admin_bp

from db import get_db_connection


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "loan-approval-secret-key"
)


# ============================================================
# SESSION CONFIGURATION
# ============================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = os.getenv(
    "MAIL_SERVER",
    "smtp.gmail.com"
)

app.config["MAIL_PORT"] = int(
    os.getenv(
        "MAIL_PORT",
        "587"
    )
)

app.config["MAIL_USE_TLS"] = (
    os.getenv(
        "MAIL_USE_TLS",
        "True"
    ).lower() == "true"
)

app.config["MAIL_USE_SSL"] = (
    os.getenv(
        "MAIL_USE_SSL",
        "False"
    ).lower() == "true"
)

app.config["MAIL_USERNAME"] = os.getenv(
    "MAIL_USERNAME",
    ""
)

app.config["MAIL_PASSWORD"] = os.getenv(
    "MAIL_PASSWORD",
    ""
)

app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
    "MAIL_DEFAULT_SENDER",
    os.getenv(
        "MAIL_USERNAME",
        ""
    )
)


# ============================================================
# INITIALIZE MAIL
# ============================================================

mail.init_app(app)


# ============================================================
# CORS CONFIGURATION
# ============================================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "https://warm-lokum-36b19b.netlify.app",
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ],
            "methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization"
            ],
            "supports_credentials": True
        }
    }
)
# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

app.register_blueprint(auth_bp)
app.register_blueprint(loan_bp)
app.register_blueprint(admin_bp)
@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 204


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message":
            "Loan Approval Prediction API is running!",
        "status": "online"
    })


# ============================================================
# DATABASE TEST
# ============================================================

@app.route(
    "/api/test-db",
    methods=["GET"]
)
def test_database():

    connection = None

    try:

        connection = get_db_connection()

        if connection.is_connected():

            return jsonify({
                "success": True,
                "message":
                    "Database connected successfully!"
            })

        return jsonify({
            "success": False,
            "message":
                "Database connection failed"
        }), 500

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                f"Database connection failed: {str(e)}"
        }), 500

    finally:

        if connection:

            try:
                connection.close()

            except Exception:
                pass


# ============================================================
# SESSION STATUS
# ============================================================

@app.route(
    "/api/session",
    methods=["GET"]
)
def session_status():

    if "user_id" not in session:

        return jsonify({
            "success": True,
            "logged_in": False,
            "user": None
        })


    return jsonify({
        "success": True,
        "logged_in": True,

        "user": {
            "id":
                session.get("user_id"),

            "name":
                session.get("name"),

            "email":
                session.get("email"),

            "role":
                session.get("role")
        }
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health_check():

    return jsonify({

        "success": True,

        "application":
            "Loan Approval Prediction System",

        "backend":
            "Flask",

        "database":
            "MySQL",

        "machine_learning":
            "scikit-learn",

        "email_service":
            "Flask-Mail",

        "status":
            "healthy"
    })


# ============================================================
# EMAIL CONFIGURATION TEST
# ============================================================

@app.route(
    "/api/test-email-config",
    methods=["GET"]
)
def test_email_config():

    username = app.config.get(
        "MAIL_USERNAME"
    )

    password = app.config.get(
        "MAIL_PASSWORD"
    )

    if not username:

        return jsonify({

            "success": False,

            "message":
                "MAIL_USERNAME is not configured"
        }), 500


    if not password:

        return jsonify({

            "success": False,

            "message":
                "MAIL_PASSWORD is not configured"
        }), 500


    return jsonify({

        "success": True,

        "message":
            "Email configuration is loaded successfully",

        "email":
            username
    })


# ============================================================
# 404 ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "message":
            "API endpoint not found"
    }), 404


# ============================================================
# 405 ERROR HANDLER
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success": False,

        "message":
            "HTTP method not allowed"
    }), 405


# ============================================================
# 500 ERROR HANDLER
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "message":
            "Internal server error"
    }), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(
        "       LOAN APPROVAL PREDICTION SYSTEM"
    )
    print("=" * 60)

    print(
        "Backend : Flask"
    )

    print(
        "Database: MySQL"
    )

    print(
        "ML      : scikit-learn"
    )

    print(
        "Email   : Flask-Mail"
    )

    print(
        "Server  : https://loan-approval-api-881e.onrender.com"
    )

    print("=" * 60)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )