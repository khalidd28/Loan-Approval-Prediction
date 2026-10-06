from flask import Blueprint, jsonify, request, session, Response
from db import get_db_connection

import os
import io
import joblib
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.units import mm


loan_bp = Blueprint("loan", __name__)


# =========================================================
# LOAD ML MODEL
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)


model = joblib.load(
    os.path.join(
        MODEL_DIR,
        "loan_model.pkl"
    )
)

model_columns = joblib.load(
    os.path.join(
        MODEL_DIR,
        "model_columns.pkl"
    )
)

label_encoders = joblib.load(
    os.path.join(
        MODEL_DIR,
        "label_encoders.pkl"
    )
)

imputer = joblib.load(
    os.path.join(
        MODEL_DIR,
        "imputer.pkl"
    )
)


# =========================================================
# VALIDATION
# =========================================================

def validate_application(data):

    errors = []

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    required_fields = [
        "Gender",
        "Married",
        "Dependents",
        "Education",
        "Self_Employed",
        "ApplicantIncome",
        "CoapplicantIncome",
        "LoanAmount",
        "Loan_Amount_Term",
        "Credit_History",
        "Property_Area"
    ]

    for field in required_fields:

        if (
            field not in data
            or data[field] is None
            or str(data[field]).strip() == ""
        ):

            errors.append(
                f"{field} is required"
            )

    if errors:
        return errors

    # -----------------------------------------------------
    # CATEGORY VALIDATION
    # -----------------------------------------------------

    if data["Gender"] not in ["Male", "Female"]:

        errors.append(
            "Invalid gender"
        )

    if data["Married"] not in ["Yes", "No"]:

        errors.append(
            "Invalid marital status"
        )

    if data["Education"] not in [
        "Graduate",
        "Not Graduate"
    ]:

        errors.append(
            "Invalid education value"
        )

    if data["Self_Employed"] not in [
        "Yes",
        "No"
    ]:

        errors.append(
            "Invalid employment status"
        )

    if data["Property_Area"] not in [
        "Urban",
        "Semiurban",
        "Rural"
    ]:

        errors.append(
            "Invalid property area"
        )

    # -----------------------------------------------------
    # DEPENDENTS
    # -----------------------------------------------------

    dependents = str(
        data["Dependents"]
    ).strip()

    if (
        not dependents.isdigit()
        and dependents != "3+"
    ):

        errors.append(
            "Dependents must be 0, 1, 2 or 3+"
        )

    else:

        if dependents.isdigit():

            dependents_number = int(
                dependents
            )

            if dependents_number > 3:

                errors.append(
                    "Dependents cannot be greater than 3"
                )

    # -----------------------------------------------------
    # APPLICANT INCOME
    # -----------------------------------------------------

    try:

        applicant_income = float(
            data["ApplicantIncome"]
        )

        if applicant_income <= 0:

            errors.append(
                "Applicant income must be greater than 0"
            )

    except (TypeError, ValueError):

        errors.append(
            "Applicant income must be a valid number"
        )

    # -----------------------------------------------------
    # CO-APPLICANT INCOME
    # -----------------------------------------------------

    try:

        coapplicant_income = float(
            data["CoapplicantIncome"]
        )

        if coapplicant_income < 0:

            errors.append(
                "Co-applicant income cannot be negative"
            )

    except (TypeError, ValueError):

        errors.append(
            "Co-applicant income must be a valid number"
        )

    # -----------------------------------------------------
    # LOAN AMOUNT
    # -----------------------------------------------------

    try:

        loan_amount = float(
            data["LoanAmount"]
        )

        if loan_amount <= 0:

            errors.append(
                "Loan amount must be greater than 0"
            )

    except (TypeError, ValueError):

        errors.append(
            "Loan amount must be a valid number"
        )

    # -----------------------------------------------------
    # LOAN TERM
    # -----------------------------------------------------

    try:

        loan_term = int(
            float(
                data["Loan_Amount_Term"]
            )
        )

        if (
            loan_term < 12
            or loan_term > 480
        ):

            errors.append(
                "Loan term must be between 12 and 480 months"
            )

    except (TypeError, ValueError):

        errors.append(
            "Loan term must be a valid number"
        )

    # -----------------------------------------------------
    # CREDIT HISTORY
    # -----------------------------------------------------

    if str(
        data["Credit_History"]
    ) not in ["0", "1"]:

        errors.append(
            "Credit history must be 0 or 1"
        )

    return errors


# =========================================================
# PREDICT LOAN
# =========================================================

@loan_bp.route(
    "/api/predict",
    methods=["POST"]
)
def predict_loan():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login before applying for a loan"
        }), 401

    # -----------------------------------------------------
    # GET JSON
    # -----------------------------------------------------

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "Application data is required"
        }), 400

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    errors = validate_application(data)

    if errors:

        return jsonify({
            "success": False,
            "message": "Please correct the following errors",
            "errors": errors
        }), 400

    connection = None
    cursor = None

    try:

        # -------------------------------------------------
        # PREPARE INPUT
        # -------------------------------------------------

        input_data = {

            "Gender":
                data["Gender"],

            "Married":
                data["Married"],

            "Dependents":
                data["Dependents"],

            "Education":
                data["Education"],

            "Self_Employed":
                data["Self_Employed"],

            "ApplicantIncome":
                float(
                    data["ApplicantIncome"]
                ),

            "CoapplicantIncome":
                float(
                    data["CoapplicantIncome"]
                ),

            "LoanAmount":
                float(
                    data["LoanAmount"]
                ),

            "Loan_Amount_Term":
                int(
                    float(
                        data["Loan_Amount_Term"]
                    )
                ),

            "Credit_History":
                int(
                    data["Credit_History"]
                ),

            "Property_Area":
                data["Property_Area"]
        }

        df = pd.DataFrame(
            [input_data]
        )

        # -------------------------------------------------
        # ENCODE CATEGORICAL VALUES
        # -------------------------------------------------

        for column, encoder in label_encoders.items():

            if column in df.columns:

                try:

                    df[column] = encoder.transform(
                        df[column].astype(str)
                    )

                except ValueError:

                    return jsonify({
                        "success": False,
                        "message": f"Invalid value for {column}"
                    }), 400

        # -------------------------------------------------
        # MATCH MODEL COLUMNS
        # -------------------------------------------------

        df = df.reindex(
            columns=model_columns
        )

        # -------------------------------------------------
        # IMPUTE
        # -------------------------------------------------

        transformed_data = imputer.transform(
            df
        )

        df = pd.DataFrame(
            transformed_data,
            columns=model_columns
        )

        # -------------------------------------------------
        # PREDICTION
        # -------------------------------------------------

        prediction_value = model.predict(
            df
        )[0]

        # -------------------------------------------------
        # PROBABILITY
        # -------------------------------------------------

        probability = 0.0

        if hasattr(
            model,
            "predict_proba"
        ):

            probabilities = model.predict_proba(
                df
            )[0]

            probability = float(
                max(probabilities) * 100
            )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        if int(prediction_value) == 1:

            prediction = "Approved"

        else:

            prediction = "Rejected"

        model_name = type(model).__name__

        # -------------------------------------------------
        # DATABASE
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor()

        # -------------------------------------------------
        # SAVE APPLICATION
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO loan_applications (

                user_id,

                gender,
                married,
                dependents,
                education,
                self_employed,

                applicant_income,
                coapplicant_income,
                loan_amount,
                loan_term,

                credit_history,
                property_area,

                prediction,
                probability,
                status

            )

            VALUES (

                %s,

                %s,
                %s,
                %s,
                %s,
                %s,

                %s,
                %s,
                %s,
                %s,

                %s,
                %s,

                %s,
                %s,
                %s

            )
            """,
            (
                session["user_id"],

                data["Gender"],
                data["Married"],
                data["Dependents"],
                data["Education"],
                data["Self_Employed"],

                float(
                    data["ApplicantIncome"]
                ),

                float(
                    data["CoapplicantIncome"]
                ),

                float(
                    data["LoanAmount"]
                ),

                int(
                    float(
                        data["Loan_Amount_Term"]
                    )
                ),

                int(
                    data["Credit_History"]
                ),

                data["Property_Area"],

                prediction,

                probability,

                prediction
            )
        )

        # -------------------------------------------------
        # APPLICATION ID
        # -------------------------------------------------

        application_id = cursor.lastrowid

        # -------------------------------------------------
        # SAVE PREDICTION HISTORY
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO prediction_history (

                application_id,
                predicted_result,
                probability,
                model_name

            )

            VALUES (

                %s,
                %s,
                %s,
                %s

            )
            """,
            (
                application_id,
                prediction,
                probability,
                model_name
            )
        )

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        connection.commit()

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "prediction":
                prediction,

            "probability":
                round(
                    probability,
                    2
                ),

            "model":
                model_name,

            "application_id":
                application_id,

            "message":
                "Loan application processed successfully"

        })

    except Exception as e:

        if connection:

            connection.rollback()

        return jsonify({

            "success": False,

            "message":
                f"Prediction failed: {str(e)}"

        }), 500

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# USER PREDICTION HISTORY
# =========================================================

@loan_bp.route(
    "/api/history",
    methods=["GET"]
)
def prediction_history():

    if "user_id" not in session:

        return jsonify({

            "success": False,

            "message":
                "Please login first"

        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT

                la.id,

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

            WHERE la.user_id = %s

            ORDER BY la.created_at DESC
            """,
            (
                session["user_id"],
            )
        )

        history = cursor.fetchall()

        return jsonify({

            "success": True,

            "history":
                history

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Failed to load history: {str(e)}"

        }), 500

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()
@loan_bp.route("/api/my-applications", methods=["GET"])
def my_applications():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                loan_amount,
                loan_term,
                prediction,
                probability,
                status,
                created_at
            FROM loan_applications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (session["user_id"],))

        applications = cursor.fetchall()

        return jsonify({
            "success": True,
            "applications": applications
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Failed to load applications: {str(e)}"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
@loan_bp.route(
    "/api/my-applications/<int:application_id>/pdf",
    methods=["GET"]
)
def download_my_application_pdf(application_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                la.*,
                u.name,
                u.email,
                u.phone
            FROM loan_applications la
            INNER JOIN users u
                ON la.user_id = u.id
            WHERE la.id = %s
              AND la.user_id = %s
        """, (
            application_id,
            session["user_id"]
        ))

        application = cursor.fetchone()

        if not application:
            return jsonify({
                "success": False,
                "message": "Application not found"
            }), 404

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "Loan Approval Prediction Report",
                styles["Title"]
            )
        )

        story.append(Spacer(1, 15))

        data = [
            ["Field", "Details"],

            ["Application ID",
             str(application["id"])],

            ["Applicant Name",
             str(application["name"])],

            ["Email",
             str(application["email"])],

            ["Phone",
             str(application["phone"] or "-")],

            ["Loan Amount",
             f'₹{application["loan_amount"]}'],

            ["Loan Term",
             f'{application["loan_term"]} months'],

            ["Credit History",
             str(application["credit_history"])],

            ["Property Area",
             str(application["property_area"])],

            ["Prediction",
             str(application["prediction"])],

            ["Probability",
             f'{float(application["probability"] or 0):.2f}%'],

            ["Status",
             str(application["status"])],

            ["Submitted",
             str(application["created_at"])]
        ]

        table = Table(
            data,
            colWidths=[
                55 * mm,
                105 * mm
            ]
        )

        table.setStyle(
            TableStyle([
                ("BACKGROUND",
                 (0, 0),
                 (-1, 0),
                 colors.lightgrey),

                ("FONTNAME",
                 (0, 0),
                 (-1, 0),
                 "Helvetica-Bold"),

                ("GRID",
                 (0, 0),
                 (-1, -1),
                 0.5,
                 colors.grey),

                ("PADDING",
                 (0, 0),
                 (-1, -1),
                 7)
            ])
        )

        story.append(table)

        story.append(Spacer(1, 20))

        story.append(
            Paragraph(
                "This report is generated for educational purposes. "
                "The ML prediction should not be treated as an actual "
                "banking approval decision.",
                styles["Normal"]
            )
        )

        document.build(story)

        buffer.seek(0)

        return Response(
            buffer.getvalue(),
            mimetype="application/pdf",
            headers={
                "Content-Disposition":
                    f"attachment; filename=loan_application_{application_id}.pdf"
            }
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                f"Failed to generate PDF: {str(e)}"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()