CREATE DATABASE IF NOT EXISTS iskolar_ng_bayan
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE iskolar_ng_bayan;

CREATE TABLE IF NOT EXISTS applicants (
    applicant_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20) NULL,

    birth_date DATE NULL,

    sex ENUM(
        'MALE',
        'FEMALE',
        'OTHER',
        'PREFER_NOT_TO_SAY'
    ) NULL,

    email VARCHAR(150) NULL,
    phone VARCHAR(30) NULL,

    house_no_street VARCHAR(255) NULL,
    barangay VARCHAR(100) NOT NULL,
    municipality VARCHAR(100) NOT NULL DEFAULT 'Santa Cruz',
    province VARCHAR(100) NOT NULL DEFAULT 'Laguna',

    is_archived BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_applicant_name (last_name, first_name),
    INDEX idx_applicant_barangay (barangay),
    INDEX idx_applicant_archived (is_archived)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applications (
    application_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    applicant_id BIGINT UNSIGNED NOT NULL,

    scholarship_program VARCHAR(150) NOT NULL,
    scholarship_year SMALLINT UNSIGNED NOT NULL,

    academic_average DECIMAL(5,2) NOT NULL,

    monthly_income DECIMAL(12,2) NOT NULL,
    mswdo_poverty_eligible BOOLEAN NOT NULL DEFAULT FALSE,

    household INT UNSIGNED NOT NULL,
    children_count INT UNSIGNED NOT NULL DEFAULT 0,
    senior_count INT UNSIGNED NOT NULL DEFAULT 0,
    pwd_count INT UNSIGNED NOT NULL DEFAULT 0,

    solo_parent BOOLEAN NOT NULL DEFAULT FALSE,
    dependent BOOLEAN NOT NULL DEFAULT FALSE,

    exam_score DECIMAL(5,2) NULL,
    exam_passed BOOLEAN NOT NULL DEFAULT FALSE,

    four_ps_beneficiary BOOLEAN NOT NULL DEFAULT FALSE,
    spes_beneficiary BOOLEAN NOT NULL DEFAULT FALSE,
    scholars_in_family INT UNSIGNED NOT NULL DEFAULT 0,

    residency VARCHAR(100) NULL,
    previous_scholarship BOOLEAN NOT NULL DEFAULT FALSE,

    status ENUM(
        'DRAFT',
        'SUBMITTED',
        'UNDER_REVIEW',
        'FOR_INTERVIEW',
        'INTERVIEWED',
        'RECOMMENDED',
        'APPROVED',
        'REJECTED',
        'WAITLISTED',
        'WITHDRAWN'
    ) NOT NULL DEFAULT 'DRAFT',

    submitted_at DATETIME NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_application_applicant
        FOREIGN KEY (applicant_id)
        REFERENCES applicants(applicant_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_applicant_program_year
        UNIQUE (
            applicant_id,
            scholarship_program,
            scholarship_year
        ),

    CONSTRAINT chk_academic_average
        CHECK (academic_average BETWEEN 0 AND 100),

    CONSTRAINT chk_monthly_income
        CHECK (monthly_income >= 0),

    CONSTRAINT chk_household_size
        CHECK (household >= 1),

    CONSTRAINT chk_household_counts
        CHECK (
            children_count <= household
            AND senior_count <= household
            AND pwd_count <= household
        ),

    CONSTRAINT chk_exam_score
        CHECK (
            exam_score IS NULL
            OR exam_score BETWEEN 0 AND 100
        ),

    CONSTRAINT chk_scholarship_year
        CHECK (scholarship_year BETWEEN 2000 AND 2200),

    INDEX idx_application_status (status),
    INDEX idx_application_year (scholarship_year),
    INDEX idx_application_applicant (applicant_id),
    INDEX idx_application_program_year (
        scholarship_program,
        scholarship_year
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS model_versions (
    model_version_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    version_name VARCHAR(100) NOT NULL UNIQUE,

    algorithm VARCHAR(100) NOT NULL
        DEFAULT 'Random Forest Classifier',

    artifact_path VARCHAR(500) NOT NULL,
    feature_config JSON NULL,

    accuracy DECIMAL(7,6) NULL,
    precision_score DECIMAL(7,6) NULL,
    recall_score DECIMAL(7,6) NULL,
    f1_score DECIMAL(7,6) NULL,

    is_active BOOLEAN NOT NULL DEFAULT FALSE,

    trained_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_model_accuracy
        CHECK (accuracy IS NULL OR accuracy BETWEEN 0 AND 1),

    CONSTRAINT chk_model_precision
        CHECK (
            precision_score IS NULL
            OR precision_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_model_recall
        CHECK (
            recall_score IS NULL
            OR recall_score BETWEEN 0 AND 1
        ),

    CONSTRAINT chk_model_f1
        CHECK (f1_score IS NULL OR f1_score BETWEEN 0 AND 1),

    INDEX idx_model_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS screening_results (
    screening_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    application_id BIGINT UNSIGNED NOT NULL,
    model_version_id BIGINT UNSIGNED NOT NULL,

    predicted_class ENUM(
        'PROCEED_TO_INTERVIEW',
        'NEEDS_OFFICIAL_REVIEW',
        'REJECTED'
    ) NOT NULL,

    confidence_score DECIMAL(7,6) NULL,
    explanation TEXT NULL,

    screened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_screening_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_screening_model
        FOREIGN KEY (model_version_id)
        REFERENCES model_versions(model_version_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_confidence_score
        CHECK (
            confidence_score IS NULL
            OR confidence_score BETWEEN 0 AND 1
        ),

    INDEX idx_screening_application_date (
        application_id,
        screened_at,
        screening_id
    ),

    INDEX idx_screening_prediction (predicted_class)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interviews (
    interview_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    application_id BIGINT UNSIGNED NOT NULL,

    scheduled_at DATETIME NOT NULL,
    location VARCHAR(255) NULL,

    status ENUM(
        'SCHEDULED',
        'COMPLETED',
        'RESCHEDULED',
        'CANCELLED',
        'NO_SHOW'
    ) NOT NULL DEFAULT 'SCHEDULED',

    result ENUM(
        'PASSED',
        'FAILED',
        'FOR_FURTHER_REVIEW'
    ) NULL,

    remarks TEXT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_interview_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_interview_result
        CHECK (
            result IS NULL
            OR status = 'COMPLETED'
        ),

    INDEX idx_interview_schedule (scheduled_at, status),
    INDEX idx_interview_application (application_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS scholarship_decisions (
    decision_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    application_id BIGINT UNSIGNED NOT NULL,

    decision ENUM(
        'APPROVED',
        'REJECTED',
        'WAITLISTED'
    ) NOT NULL,

    reason TEXT NOT NULL,

    decided_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_decision_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_decision_application_date (
        application_id,
        decided_at,
        decision_id
    ),

    INDEX idx_decision_type (decision),
    INDEX idx_decision_date (decided_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id BIGINT UNSIGNED NULL,

    details JSON NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_date (created_at)
) ENGINE=InnoDB;

SHOW TABLES;

DESCRIBE applicants;
DESCRIBE applications;
DESCRIBE model_versions;
DESCRIBE screening_results;
DESCRIBE interviews;
DESCRIBE scholarship_decisions;
DESCRIBE audit_logs;

SHOW COLUMNS FROM applicants LIKE 'is_archived';




USE iskolar_ng_bayan;

ALTER TABLE applicants
ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;

SHOW COLUMNS FROM applicants LIKE 'is_archived';

USE iskolar_ng_bayan;

SHOW CREATE TABLE applications;

USE iskolar_ng_bayan;

ALTER TABLE applications
ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;

SHOW COLUMNS FROM applications LIKE 'is_archived';