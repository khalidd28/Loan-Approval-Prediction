# Loan Approval Prediction System

An intelligent web-based **Loan Approval Prediction System** that uses Machine Learning to predict whether a loan application is likely to be approved or rejected based on applicant and loan-related information.

The system provides separate interfaces for **users and administrators**, along with prediction history, application tracking, analytics, downloadable reports, and email notifications.

> **Academic Project:** This system is developed for educational and demonstration purposes. ML predictions should not be considered actual banking or financial approval decisions.

---

## 📌 Project Overview

The Loan Approval Prediction System combines:

- Web application development
- Machine Learning
- MySQL database management
- User authentication
- Administrative management
- Data analytics
- Email notifications
- PDF and CSV reporting

Users can submit their loan details and receive an ML-based prediction. Administrators can monitor applications, manage statuses, view analytics, export reports, and notify applicants through email.

---

## ✨ Features

### 👤 User Features

- User registration
- Secure login and logout
- User profile management
- Change password
- Loan application form
- Machine Learning loan prediction
- Prediction probability
- Prediction history
- Application status tracking
- Downloadable application PDF report

### 🛠️ Admin Features

- Admin authentication
- Dashboard statistics
- Registered user management
- Loan application management
- Application search
- Application filtering
- Application sorting
- Detailed application view
- Application status management
- CSV export
- PDF export
- Notifications
- Advanced analytics
- ML model comparison
- Email notifications to applicants

### 📧 Email Notification

When an administrator changes an application status to:

- **Approved**
- **Rejected**

the system can automatically send an email notification to the applicant.

---

## 🤖 Machine Learning

The system compares multiple Machine Learning algorithms:

| Model | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|
| Logistic Regression | 70.0% | 100.0% | 62.5% | 76.92% |
| Decision Tree | 100.0% | 100.0% | 100.0% | 100.0% |
| Random Forest | 90.0% | 100.0% | 87.5% | 93.33% |

### Best Model

**Decision Tree**

The model is selected based on the highest accuracy on the evaluation split.

> The dataset used for this academic project is small, so these evaluation results should not be interpreted as real-world banking performance.

---

## 🧠 Input Parameters

The prediction system uses applicant and loan-related attributes such as:

- Gender
- Marital Status
- Dependents
- Education
- Self Employment
- Applicant Income
- Co-applicant Income
- Loan Amount
- Loan Term
- Credit History
- Property Area

---

## 🏗️ Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend

- Python
- Flask
- Flask-Mail

### Database

- MySQL

### Machine Learning

- Pandas
- NumPy
- Scikit-learn
- Joblib

### Reporting

- ReportLab
- CSV Export

### Development Tools

- Visual Studio Code
- Git
- GitHub

---

## 📂 Project Structure

```text
Loan-Approval-Prediction/
│
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── email_service.py
│   ├── extensions.py
│   ├── requirements.txt
│   │
│   ├── model/
│   │   ├── train_model.py
│   │   ├── loan_model.pkl
│   │   ├── imputer.pkl
│   │   ├── label_encoders.pkl
│   │   ├── model_columns.pkl
│   │   └── model_metrics.json
│   │
│   └── routes/
│       ├── auth.py
│       ├── loan.py
│       └── admin.py
│
├── database/
│   └── loan_approval.sql
│
├── dataset/
│   └── loan_data.csv
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── apply-loan.html
│   ├── history.html
│   ├── profile.html
│   ├── admin.html
│   │
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── login.js
│       ├── loan.js
│       └── admin.js
│
├── .gitignore
├── README.md
└── .env