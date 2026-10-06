from flask import current_app
from flask_mail import Message
from extensions import mail


def send_status_email(
    applicant_email,
    applicant_name,
    application_id,
    status,
    prediction
):

    if status not in [
        "Approved",
        "Rejected"
    ]:
        return False

    if status == "Approved":

        subject = (
            f"Loan Application #{application_id} - Approved"
        )

        message = f"""
Dear {applicant_name},

We are pleased to inform you that your loan application
#{application_id} has been marked as APPROVED.

Prediction Result: {prediction}
Application Status: Approved

Please note that this system is an educational
Loan Approval Prediction System and does not represent
an actual banking approval.

Thank you for using our Loan Approval Prediction System.

Regards,
Loan Approval Prediction System
"""

    else:

        subject = (
            f"Loan Application #{application_id} - Rejected"
        )

        message = f"""
Dear {applicant_name},

Your loan application #{application_id} has been marked
as REJECTED.

Prediction Result: {prediction}
Application Status: Rejected

Please note that this system is an educational
Loan Approval Prediction System and does not represent
an actual banking decision.

Thank you for using our Loan Approval Prediction System.

Regards,
Loan Approval Prediction System
"""

    try:

        msg = Message(
            subject=subject,
            recipients=[applicant_email],
            body=message
        )

        mail.send(msg)

        return True

    except Exception as e:

        print(
            f"Email sending failed: {str(e)}"
        )

        return False