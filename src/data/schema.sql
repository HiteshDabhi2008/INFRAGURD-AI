-- InfraGuard-AI Initial Database Schema
-- Compatible with SQLite/PostgreSQL

CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name VARCHAR(255) NOT NULL,
    report_month VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    project_code VARCHAR(100) PRIMARY KEY,
    project_name TEXT NOT NULL,
    agency VARCHAR(255),
    state VARCHAR(255),
    approval_date DATE,
    original_cost DECIMAL(15, 2),
    original_completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code VARCHAR(100) NOT NULL,
    report_month VARCHAR(50) NOT NULL,
    start_date DATE,
    revised_cost DECIMAL(15, 2),
    revised_completion_date DATE,
    cumulative_expenditure DECIMAL(15, 2),
    physical_progress DECIMAL(5, 2),
    data_source_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_code) REFERENCES projects(project_code),
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id),
    UNIQUE(project_code, report_month)
);

CREATE TABLE IF NOT EXISTS project_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code VARCHAR(100) NOT NULL,
    report_month VARCHAR(50) NOT NULL,
    project_age_days INTEGER,
    original_duration_days INTEGER,
    revised_duration_days INTEGER,
    expenditure_percent DECIMAL(10, 2),
    progress_gap DECIMAL(10, 2),
    cost_change DECIMAL(15, 2),
    cost_change_percent DECIMAL(10, 2),
    project_size_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_code) REFERENCES projects(project_code),
    UNIQUE(project_code, report_month)
);
