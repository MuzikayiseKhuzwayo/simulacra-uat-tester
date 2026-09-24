-- Simulacra UAT Platform Schema Migration
-- Migration: 20260924_init_simulacra_schema.sql
-- Description: Core tables for synthetic personas, campaigns, sessions, telemetry, feedback, and UAT reports

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    target_url TEXT NOT NULL,
    primary_goal TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    successful_sessions INTEGER DEFAULT 0,
    success_rate_percent REAL DEFAULT 0.0,
    average_friction_score REAL DEFAULT 0.0,
    average_sus_score REAL DEFAULT 0.0,
    total_rage_clicks INTEGER DEFAULT 0,
    config_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS personas (
    persona_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    age INTEGER NOT NULL,
    technical_skill TEXT NOT NULL,
    patience TEXT NOT NULL,
    device_type TEXT NOT NULL,
    persona_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    persona_id TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL DEFAULT 0.0,
    total_steps INTEGER DEFAULT 0,
    pages_visited INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    rage_clicks_total INTEGER DEFAULT 0,
    hesitation_time_total_ms INTEGER DEFAULT 0,
    friction_score REAL DEFAULT 0.0,
    task_success INTEGER DEFAULT 0,
    exit_reason TEXT NOT NULL,
    final_sentiment TEXT NOT NULL,
    FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    page_url TEXT NOT NULL,
    page_title TEXT,
    action_type TEXT NOT NULL,
    target_element TEXT,
    target_text TEXT,
    scroll_depth_percent REAL DEFAULT 0.0,
    hesitation_ms INTEGER DEFAULT 0,
    rage_click_count INTEGER DEFAULT 0,
    emotion TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    cognitive_reasoning TEXT NOT NULL,
    screenshot_path TEXT,
    FOREIGN KEY(session_id) REFERENCES agent_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS session_feedback (
    feedback_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    persona_id TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    overall_rating INTEGER NOT NULL,
    sus_score REAL NOT NULL,
    ces_score INTEGER NOT NULL,
    nps_rating INTEGER NOT NULL,
    sentiment_summary TEXT NOT NULL,
    what_worked_well_json TEXT NOT NULL,
    confusing_elements_json TEXT NOT NULL,
    friction_points_json TEXT NOT NULL,
    verbatim_quote TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES agent_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS uat_reports (
    report_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    title TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    report_json TEXT NOT NULL,
    report_markdown TEXT NOT NULL,
    FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_campaign ON agent_sessions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_events(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session ON session_feedback(session_id);

-- rollback
-- DROP INDEX IF EXISTS idx_feedback_session;
-- DROP INDEX IF EXISTS idx_telemetry_session;
-- DROP INDEX IF EXISTS idx_sessions_campaign;
-- DROP TABLE IF EXISTS uat_reports;
-- DROP TABLE IF EXISTS session_feedback;
-- DROP TABLE IF EXISTS telemetry_events;
-- DROP TABLE IF EXISTS agent_sessions;
-- DROP TABLE IF EXISTS personas;
-- DROP TABLE IF EXISTS campaigns;
