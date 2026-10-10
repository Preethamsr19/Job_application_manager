-- Job Application Management System database schema.
-- Safe to run on an existing database: CREATE TABLE IF NOT EXISTS does not drop data.
CREATE DATABASE IF NOT EXISTS job_application_manager
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_application_manager;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  university VARCHAR(180) NULL,
  graduation_year SMALLINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS companies (
  company_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  company_name VARCHAR(180) NOT NULL,
  website VARCHAR(500) NULL,
  location VARCHAR(180) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_companies_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT uq_user_company UNIQUE (user_id, company_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applications (
  application_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  company_id INT NOT NULL,
  job_role VARCHAR(180) NOT NULL,
  job_type VARCHAR(80) NULL,
  job_link VARCHAR(1000) NULL,
  application_date DATE NULL,
  status ENUM('Interested','Applied','OA Scheduled','OA Completed','Shortlisted','Technical Interview','HR Interview','Offer','Rejected','Withdrawn') NOT NULL DEFAULT 'Interested',
  salary VARCHAR(120) NULL,
  location VARCHAR(180) NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_applications_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_applications_company FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
  INDEX idx_applications_user_status (user_id, status),
  INDEX idx_applications_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS assessments (
  assessment_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL,
  assessment_name VARCHAR(180) NOT NULL,
  assessment_date DATETIME NULL,
  platform VARCHAR(180) NULL,
  status ENUM('Scheduled','Completed','Missed') NOT NULL DEFAULT 'Scheduled',
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_assessments_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
  INDEX idx_assessments_date (assessment_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interviews (
  interview_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL,
  interview_type ENUM('Technical','HR','Managerial','Other') NOT NULL DEFAULT 'Technical',
  interview_date DATETIME NOT NULL,
  mode ENUM('Online','Offline','Phone') NOT NULL DEFAULT 'Online',
  meeting_link VARCHAR(1000) NULL,
  interviewer_name VARCHAR(180) NULL,
  status ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
  feedback TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_interviews_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
  INDEX idx_interviews_date (interview_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tasks (
  task_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  application_id INT NULL,
  task_title VARCHAR(220) NOT NULL,
  description TEXT NULL,
  due_date DATE NULL,
  priority ENUM('Low','Medium','High') NOT NULL DEFAULT 'Medium',
  status ENUM('Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_tasks_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE SET NULL,
  INDEX idx_tasks_user_status (user_id, status),
  INDEX idx_tasks_due_date (due_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notes (
  note_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL,
  note_title VARCHAR(220) NULL,
  note_content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_notes_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
  INDEX idx_notes_updated (updated_at)
) ENGINE=InnoDB;
