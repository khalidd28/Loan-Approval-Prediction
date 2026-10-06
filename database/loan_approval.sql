CREATE DATABASE IF NOT EXISTS loan_approval;

USE loan_approval;

-- =========================================
-- USERS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- LOAN APPLICATIONS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS loan_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    gender VARCHAR(20),
    married VARCHAR(20),
    dependents VARCHAR(20),
    education VARCHAR(50),
    self_employed VARCHAR(20),

    applicant_income DECIMAL(12,2) NOT NULL,
    coapplicant_income DECIMAL(12,2) DEFAULT 0,

    loan_amount DECIMAL(12,2) NOT NULL,
    loan_term INT,

    credit_history INT,
    property_area VARCHAR(50),

    prediction VARCHAR(20),
    probability DECIMAL(5,2),

    status ENUM(
        'Pending',
        'Approved',
        'Rejected'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_loan_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================
-- PREDICTION HISTORY TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS prediction_history (
    id INT AUTO_INCREMENT PRIMARY KEY,

    application_id INT NOT NULL,

    predicted_result VARCHAR(20) NOT NULL,
    probability DECIMAL(5,2),

    model_name VARCHAR(100),

    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_prediction_application
        FOREIGN KEY (application_id)
        REFERENCES loan_applications(id)
        ON DELETE CASCADE
);

-- =========================================
-- ADMIN ACCOUNT
-- =========================================

INSERT INTO users
(name, email, password, phone, role)
VALUES
(
    'System Admin',
    'admin@loanprediction.com',
    'CHANGE_THIS_PASSWORD',
    '0000000000',
    'admin'
);

-- =========================================
-- CHECK TABLES
-- =========================================

SHOW TABLES;