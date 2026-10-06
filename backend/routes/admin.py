from flask import Blueprint, jsonify, session, Response, request

from db import get_db_connection
from email_service import send_status_email

import os
import json
import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


admin_bp = Blueprint("admin", __name__)


# =========================================================
# ADMIN ACCESS CHECK
# =========================================================

def check_admin():

    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.route(
    "/api/admin/dashboard",
    methods=["GET"]
)
def admin_dashboard():

    if not check_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # TOTAL USERS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'user'
        """)

        total_users = cursor.fetchone()["total"]

        # TOTAL APPLICATIONS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
        """)

        total_applications = cursor.fetchone()["total"]

        # APPROVED

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Approved'
        """)

        approved = cursor.fetchone()["total"]

        # REJECTED

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Rejected'
        """)

        rejected = cursor.fetchone()["total"]

        # APPLICATION DETAILS

        cursor.execute("""
            SELECT
                la.id,
                u.name,
                u.email,
                u.phone,

                la.gender,
                la.married,
                la.dependents,
                la.education,
                la.self_employed,

                la.applicant_income,
                la.coapplicant_income,
                la.loan_amount,
                la.loan_term,
                la.credit_history,
                la.property_area,

                la.prediction,
                la.probability,
                la.status,

                la.created_at

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            ORDER BY la.created_at DESC
        """)

        applications = cursor.fetchall()

        return jsonify({

            "success": True,

            "statistics": {

                "total_users":
                    total_users,

                "total_applications":
                    total_applications,

                "approved":
                    approved,

                "rejected":
                    rejected

            },

            "applications":
                applications
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load dashboard: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# MODEL METRICS
# =========================================================

@admin_bp.route(
    "/api/admin/model-metrics",
    methods=["GET"]
)
def model_metrics():

    if not check_admin():

        return jsonify({

            "success": False,

            "message":
                "Admin access required"

        }), 403

    try:

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        metrics_path = os.path.join(
            base_dir,
            "model",
            "model_metrics.json"
        )

        if not os.path.exists(metrics_path):

            return jsonify({

                "success": False,

                "message":
                    "Model metrics file not found"

            }), 404

        with open(
            metrics_path,
            "r"
        ) as file:

            metrics = json.load(file)

        return jsonify({

            "success": True,

            "data":
                metrics

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load model metrics: {str(e)}"

        }), 500


# =========================================================
# ADMIN USER MANAGEMENT
# =========================================================

@admin_bp.route(
    "/api/admin/users",
    methods=["GET"]
)
def admin_users():

    if not check_admin():

        return jsonify({

            "success": False,

            "message":
                "Admin access required"

        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                role,
                created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()

        return jsonify({

            "success": True,

            "users":
                users

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load users: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADMIN APPLICATION DETAILS
# =========================================================

@admin_bp.route(
    "/api/admin/application/<int:application_id>",
    methods=["GET"]
)
def application_details(application_id):

    if not check_admin():

        return jsonify({

            "success": False,

            "message":
                "Admin access required"

        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                la.id,
                la.user_id,

                u.name,
                u.email,
                u.phone,

                la.gender,
                la.married,
                la.dependents,
                la.education,
                la.self_employed,

                la.applicant_income,
                la.coapplicant_income,
                la.loan_amount,
                la.loan_term,
                la.credit_history,
                la.property_area,

                la.prediction,
                la.probability,
                la.status,

                la.created_at

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            WHERE la.id = %s

        """, (application_id,))

        application = cursor.fetchone()

        if not application:

            return jsonify({

                "success": False,

                "message":
                    "Application not found"

            }), 404

        return jsonify({

            "success": True,

            "application":
                application

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load application: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EXPORT APPLICATIONS TO CSV
# =========================================================

@admin_bp.route(
    "/api/admin/export/csv",
    methods=["GET"]
)
def export_applications_csv():

    if not check_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                la.id AS application_id,
                u.name AS applicant_name,
                u.email,
                u.phone,
                la.gender,
                la.married,
                la.dependents,
                la.education,
                la.self_employed,
                la.applicant_income,
                la.coapplicant_income,
                la.loan_amount,
                la.loan_term,
                la.credit_history,
                la.property_area,
                la.prediction,
                la.probability,
                la.status,
                la.created_at

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            ORDER BY la.created_at DESC
        """)

        applications = cursor.fetchall()

        output = io.StringIO()

        fieldnames = [
            "application_id",
            "applicant_name",
            "email",
            "phone",
            "gender",
            "married",
            "dependents",
            "education",
            "self_employed",
            "applicant_income",
            "coapplicant_income",
            "loan_amount",
            "loan_term",
            "credit_history",
            "property_area",
            "prediction",
            "probability",
            "status",
            "created_at"
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for application in applications:

            writer.writerow(application)

        csv_data = output.getvalue()

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=loan_applications.csv"
            }
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                f"Failed to export applications: {str(e)}"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EXPORT APPLICATIONS TO PDF
# =========================================================

@admin_bp.route(
    "/api/admin/export/pdf",
    methods=["GET"]
)
def export_applications_pdf():

    if not check_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # STATISTICS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'user'
        """)

        total_users = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
        """)

        total_applications = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Approved'
        """)

        approved = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Rejected'
        """)

        rejected = cursor.fetchone()["total"]

        # APPLICATIONS

        cursor.execute("""
            SELECT
                la.id AS application_id,
                u.name AS applicant_name,
                u.email,
                la.loan_amount,
                la.loan_term,
                la.credit_history,
                la.property_area,
                la.prediction,
                la.probability,
                la.status,
                la.created_at

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            ORDER BY la.created_at DESC
        """)

        applications = cursor.fetchall()

        # PDF

        pdf_buffer = io.BytesIO()

        document = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        story = []

        story.append(
            Paragraph(
                "Loan Approval Prediction System",
                title_style
            )
        )

        story.append(
            Spacer(1, 8)
        )

        story.append(
            Paragraph(
                "Administrative Application Report",
                heading_style
            )
        )

        story.append(
            Spacer(1, 12)
        )

        summary_data = [
            ["Metric", "Value"],
            ["Total Users", str(total_users)],
            [
                "Total Applications",
                str(total_applications)
            ],
            [
                "Approved Applications",
                str(approved)
            ],
            [
                "Rejected Applications",
                str(rejected)
            ]
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                80 * mm,
                50 * mm
            ]
        )

        summary_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        story.append(summary_table)

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                "Loan Applications",
                heading_style
            )
        )

        story.append(
            Spacer(1, 8)
        )

        application_data = [[
            "ID",
            "Applicant",
            "Loan",
            "Term",
            "Credit",
            "Area",
            "Prediction",
            "Probability"
        ]]

        for application in applications:

            probability = application["probability"]

            if probability is None:

                probability_text = "-"

            else:

                probability_text = (
                    f"{float(probability):.2f}%"
                )

            application_data.append([
                str(
                    application["application_id"]
                ),

                str(
                    application["applicant_name"]
                ),

                str(
                    application["loan_amount"]
                ),

                str(
                    application["loan_term"]
                ),

                str(
                    application["credit_history"]
                ),

                str(
                    application["property_area"]
                ),

                str(
                    application["prediction"]
                ),

                probability_text
            ])

        if len(application_data) == 1:

            application_data.append([
                "-",
                "No applications",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-"
            ])

        application_table = Table(
            application_data,
            repeatRows=1,
            colWidths=[
                12 * mm,
                32 * mm,
                20 * mm,
                17 * mm,
                17 * mm,
                20 * mm,
                25 * mm,
                25 * mm
            ]
        )

        application_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )
            ])
        )

        story.append(application_table)

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                "This report is generated for educational "
                "and administrative purposes.",
                normal_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

        story.append(
            Paragraph(
                "The ML prediction should not be treated "
                "as an actual banking approval decision.",
                normal_style
            )
        )

        document.build(story)

        pdf_buffer.seek(0)

        return Response(
            pdf_buffer.getvalue(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition":
                    "attachment; filename=loan_application_report.pdf"
            }
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                f"Failed to generate PDF report: {str(e)}"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADMIN NOTIFICATIONS
# =========================================================

@admin_bp.route(
    "/api/admin/notifications",
    methods=["GET"]
)
def admin_notifications():

    if not check_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # RECENT APPLICATIONS

        cursor.execute("""
            SELECT
                la.id,
                u.name AS applicant_name,
                la.prediction,
                la.status,
                la.created_at

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            ORDER BY la.created_at DESC

            LIMIT 10
        """)

        recent_applications = cursor.fetchall()

        # PENDING

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE status = 'Pending'
        """)

        pending = cursor.fetchone()["total"]

        # APPROVED

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Approved'
        """)

        approved = cursor.fetchone()["total"]

        # REJECTED

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM loan_applications
            WHERE prediction = 'Rejected'
        """)

        rejected = cursor.fetchone()["total"]

        notifications = []

        for app in recent_applications:

            if app["prediction"] == "Approved":

                message = (
                    f'{app["applicant_name"]} '
                    f'had their loan application approved.'
                )

            elif app["prediction"] == "Rejected":

                message = (
                    f'{app["applicant_name"]} '
                    f'had their loan application rejected.'
                )

            else:

                message = (
                    f'{app["applicant_name"]} '
                    f'submitted a new loan application.'
                )

            notifications.append({

                "application_id":
                    app["id"],

                "message":
                    message,

                "prediction":
                    app["prediction"],

                "status":
                    app["status"],

                "created_at":
                    app["created_at"].isoformat()
                    if app["created_at"]
                    else None
            })

        return jsonify({

            "success": True,

            "summary": {

                "pending":
                    pending,

                "approved":
                    approved,

                "rejected":
                    rejected

            },

            "notifications":
                notifications
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load notifications: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADMIN ANALYTICS
# =========================================================

@admin_bp.route(
    "/api/admin/analytics",
    methods=["GET"]
)
def admin_analytics():

    if not check_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # PREDICTION DISTRIBUTION

        cursor.execute("""
            SELECT
                prediction,
                COUNT(*) AS total

            FROM loan_applications

            GROUP BY prediction
        """)

        prediction_data = cursor.fetchall()

        # EDUCATION DISTRIBUTION

        cursor.execute("""
            SELECT
                education,
                COUNT(*) AS total

            FROM loan_applications

            GROUP BY education
        """)

        education_data = cursor.fetchall()

        # PROPERTY DISTRIBUTION

        cursor.execute("""
            SELECT
                property_area,
                COUNT(*) AS total

            FROM loan_applications

            GROUP BY property_area
        """)

        property_data = cursor.fetchall()

        # AVERAGE LOAN

        cursor.execute("""
            SELECT
                AVG(loan_amount) AS average_loan

            FROM loan_applications
        """)

        average_loan = cursor.fetchone()["average_loan"]

        # AVERAGE INCOME

        cursor.execute("""
            SELECT
                AVG(applicant_income) AS average_income

            FROM loan_applications
        """)

        average_income = cursor.fetchone()["average_income"]

        return jsonify({

            "success": True,

            "prediction_distribution":
                prediction_data,

            "education_distribution":
                education_data,

            "property_distribution":
                property_data,

            "average_loan_amount":
                round(float(average_loan), 2)
                if average_loan is not None
                else 0,

            "average_applicant_income":
                round(float(average_income), 2)
                if average_income is not None
                else 0
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load analytics: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE APPLICATION STATUS + EMAIL
# =========================================================

@admin_bp.route(
    "/api/admin/application/<int:application_id>/status",
    methods=["PATCH"]
)
def update_application_status(application_id):

    if not check_admin():

        return jsonify({

            "success": False,

            "message":
                "Admin access required"

        }), 403

    data = request.get_json(
        silent=True
    )

    if not data or data.get("status") not in [
        "Pending",
        "Approved",
        "Rejected"
    ]:

        return jsonify({

            "success": False,

            "message":
                "Invalid application status"

        }), 400

    new_status = data["status"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # GET APPLICATION + APPLICANT DETAILS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                la.id,
                la.status,
                la.prediction,
                u.name AS applicant_name,
                u.email AS applicant_email

            FROM loan_applications la

            INNER JOIN users u
                ON la.user_id = u.id

            WHERE la.id = %s

        """, (application_id,))

        application = cursor.fetchone()

        if not application:

            return jsonify({

                "success": False,

                "message":
                    "Application not found"

            }), 404

        old_status = application["status"]

        # -------------------------------------------------
        # UPDATE STATUS
        # -------------------------------------------------

        cursor.execute("""
            UPDATE loan_applications

            SET status = %s

            WHERE id = %s
        """, (
            new_status,
            application_id
        ))

        connection.commit()

        # -------------------------------------------------
        # SEND EMAIL
        #
        # Only send when changing TO Approved/Rejected.
        # This prevents emails for Pending.
        #
        # Also prevents duplicate emails when selecting
        # the same status again.
        # -------------------------------------------------

        email_sent = False

        if (
            new_status in [
                "Approved",
                "Rejected"
            ]
            and old_status != new_status
        ):

            email_sent = send_status_email(

                applicant_email=
                    application["applicant_email"],

                applicant_name=
                    application["applicant_name"],

                application_id=
                    application_id,

                status=
                    new_status,

                prediction=
                    application["prediction"]
            )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        if email_sent:

            message = (
                "Application status updated successfully "
                "and email notification sent to applicant."
            )

        elif (
            new_status in [
                "Approved",
                "Rejected"
            ]
            and old_status != new_status
        ):

            message = (
                "Application status updated successfully, "
                "but email notification could not be sent."
            )

        else:

            message = (
                "Application status updated successfully."
            )

        return jsonify({

            "success": True,

            "message":
                message,

            "application_id":
                application_id,

            "status":
                new_status,

            "email_sent":
                email_sent

        })

    except Exception as e:

        if connection:

            connection.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Failed to update status: {str(e)}"

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()