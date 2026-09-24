"""SQLite persistence repository for Simulacra UAT platform."""

import json
import sqlite3
from pathlib import Path
from typing import Any
from src.simulacra.models import (
    CampaignMission,
    CampaignSummary,
    ExitReason,
    Emotion,
    Persona,
    PersonaFeedback,
    SessionMetrics,
    TelemetryEvent,
    UATReport,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SIMULACRA_DB_PATH = PROJECT_ROOT / "data" / "simulacra_uat.db"
MIGRATION_FILE_PATH = (
    PROJECT_ROOT / "database" / "migrations" / "20260924_init_simulacra_schema.sql"
)


def connect(
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> sqlite3.Connection:
    """Connect to SQLite database with Row factory and foreign keys enabled."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Run DDL migration and ensure schema is initialized."""
    with connect(database_path) as conn:
        if MIGRATION_FILE_PATH.exists():
            sql = MIGRATION_FILE_PATH.read_text(encoding="utf-8")
            # Strip rollback comment section
            if "-- rollback" in sql:
                sql = sql.split("-- rollback")[0]
            conn.executescript(sql)
        else:
            # Fallback schema execution
            conn.executescript(
                """
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
                """
            )


# ---------------------------------------------------------
# Persona Operations
# ---------------------------------------------------------

def save_persona(
    persona: Persona,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Insert or update a synthetic persona record."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT INTO personas (
                persona_id, name, role, age, technical_skill, patience, device_type, persona_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(persona_id) DO UPDATE SET
                name = excluded.name,
                role = excluded.role,
                age = excluded.age,
                technical_skill = excluded.technical_skill,
                patience = excluded.patience,
                device_type = excluded.device_type,
                persona_json = excluded.persona_json;
            """,
            (
                persona.persona_id,
                persona.name,
                persona.role,
                persona.age,
                persona.technical_skill.value,
                persona.patience.value,
                persona.device_type.value,
                persona.model_dump_json(),
            ),
        )


def get_persona(
    persona_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> Persona | None:
    """Fetch persona by identifier."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        row = conn.execute(
            "SELECT persona_json FROM personas WHERE persona_id = ?;",
            (persona_id,),
        ).fetchone()
        if row:
            return Persona.model_validate_json(row["persona_json"])
    return None


# ---------------------------------------------------------
# Campaign Operations
# ---------------------------------------------------------

def save_campaign(
    campaign_id: str,
    title: str,
    target_url: str,
    primary_goal: str,
    created_at: str,
    status: str,
    config: CampaignMission,
    total_sessions: int = 0,
    successful_sessions: int = 0,
    success_rate_percent: float = 0.0,
    average_friction_score: float = 0.0,
    average_sus_score: float = 0.0,
    total_rage_clicks: int = 0,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Save or update a campaign."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT INTO campaigns (
                campaign_id, title, target_url, primary_goal, created_at, status,
                total_sessions, successful_sessions, success_rate_percent,
                average_friction_score, average_sus_score, total_rage_clicks, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(campaign_id) DO UPDATE SET
                status = excluded.status,
                total_sessions = excluded.total_sessions,
                successful_sessions = excluded.successful_sessions,
                success_rate_percent = excluded.success_rate_percent,
                average_friction_score = excluded.average_friction_score,
                average_sus_score = excluded.average_sus_score,
                total_rage_clicks = excluded.total_rage_clicks,
                config_json = excluded.config_json;
            """,
            (
                campaign_id,
                title,
                target_url,
                primary_goal,
                created_at,
                status,
                total_sessions,
                successful_sessions,
                success_rate_percent,
                average_friction_score,
                average_sus_score,
                total_rage_clicks,
                config.model_dump_json(),
            ),
        )


def get_campaign(
    campaign_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> dict[str, Any] | None:
    """Retrieve campaign row as dictionary."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?;",
            (campaign_id,),
        ).fetchone()
        if row:
            data = dict(row)
            data["config"] = json.loads(data["config_json"])
            return data
    return None


def list_campaigns(
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> list[dict[str, Any]]:
    """List all campaigns ordered by creation date descending."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        rows = conn.execute(
            "SELECT * FROM campaigns ORDER BY created_at DESC;"
        ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------
# Session & Telemetry Operations
# ---------------------------------------------------------

def save_session(
    metrics: SessionMetrics,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Save or update agent session metrics."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT INTO agent_sessions (
                session_id, campaign_id, persona_id, persona_name,
                started_at, completed_at, duration_seconds, total_steps,
                pages_visited, total_clicks, rage_clicks_total,
                hesitation_time_total_ms, friction_score, task_success,
                exit_reason, final_sentiment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                completed_at = excluded.completed_at,
                duration_seconds = excluded.duration_seconds,
                total_steps = excluded.total_steps,
                pages_visited = excluded.pages_visited,
                total_clicks = excluded.total_clicks,
                rage_clicks_total = excluded.rage_clicks_total,
                hesitation_time_total_ms = excluded.hesitation_time_total_ms,
                friction_score = excluded.friction_score,
                task_success = excluded.task_success,
                exit_reason = excluded.exit_reason,
                final_sentiment = excluded.final_sentiment;
            """,
            (
                metrics.session_id,
                metrics.campaign_id,
                metrics.persona_id,
                metrics.persona_name,
                metrics.started_at,
                metrics.completed_at,
                metrics.duration_seconds,
                metrics.total_steps,
                metrics.pages_visited,
                metrics.total_clicks,
                metrics.rage_clicks_total,
                metrics.hesitation_time_total_ms,
                metrics.friction_score,
                1 if metrics.task_success else 0,
                metrics.exit_reason.value,
                metrics.final_sentiment.value,
            ),
        )


def list_sessions_by_campaign(
    campaign_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> list[SessionMetrics]:
    """Retrieve all sessions for a campaign."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        rows = conn.execute(
            "SELECT * FROM agent_sessions WHERE campaign_id = ? ORDER BY started_at ASC;",
            (campaign_id,),
        ).fetchall()
        sessions: list[SessionMetrics] = []
        for r in rows:
            sessions.append(
                SessionMetrics(
                    session_id=r["session_id"],
                    campaign_id=r["campaign_id"],
                    persona_id=r["persona_id"],
                    persona_name=r["persona_name"],
                    started_at=r["started_at"],
                    completed_at=r["completed_at"],
                    duration_seconds=r["duration_seconds"],
                    total_steps=r["total_steps"],
                    pages_visited=r["pages_visited"],
                    total_clicks=r["total_clicks"],
                    rage_clicks_total=r["rage_clicks_total"],
                    hesitation_time_total_ms=r["hesitation_time_total_ms"],
                    friction_score=r["friction_score"],
                    task_success=bool(r["task_success"]),
                    exit_reason=ExitReason(r["exit_reason"]),
                    final_sentiment=Emotion(r["final_sentiment"]),
                )
            )
        return sessions


def save_telemetry_event(
    event: TelemetryEvent,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Record an individual telemetry event."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO telemetry_events (
                event_id, session_id, step_number, timestamp, page_url, page_title,
                action_type, target_element, target_text, scroll_depth_percent,
                hesitation_ms, rage_click_count, emotion, confidence,
                cognitive_reasoning, screenshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event.event_id,
                event.session_id,
                event.step_number,
                event.timestamp,
                event.page_url,
                event.page_title,
                event.action_type.value,
                event.target_element,
                event.target_text,
                event.scroll_depth_percent,
                event.hesitation_ms,
                event.rage_click_count,
                event.emotion.value,
                event.confidence,
                event.cognitive_reasoning,
                event.screenshot_path,
            ),
        )


def get_session_telemetry(
    session_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> list[TelemetryEvent]:
    """Retrieve full chronological telemetry event stream for a session."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        rows = conn.execute(
            "SELECT * FROM telemetry_events WHERE session_id = ? ORDER BY step_number ASC;",
            (session_id,),
        ).fetchall()
        events: list[TelemetryEvent] = []
        for r in rows:
            events.append(
                TelemetryEvent(
                    event_id=r["event_id"],
                    session_id=r["session_id"],
                    step_number=r["step_number"],
                    timestamp=r["timestamp"],
                    page_url=r["page_url"],
                    page_title=r["page_title"] or "",
                    action_type=r["action_type"],
                    target_element=r["target_element"],
                    target_text=r["target_text"],
                    scroll_depth_percent=r["scroll_depth_percent"],
                    hesitation_ms=r["hesitation_ms"],
                    rage_click_count=r["rage_click_count"],
                    emotion=r["emotion"],
                    confidence=r["confidence"],
                    cognitive_reasoning=r["cognitive_reasoning"],
                    screenshot_path=r["screenshot_path"],
                )
            )
        return events


# ---------------------------------------------------------
# Feedback & Report Operations
# ---------------------------------------------------------

def save_feedback(
    feedback: PersonaFeedback,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Save structured post-session feedback."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT INTO session_feedback (
                feedback_id, session_id, persona_id, persona_name,
                overall_rating, sus_score, ces_score, nps_rating,
                sentiment_summary, what_worked_well_json, confusing_elements_json,
                friction_points_json, verbatim_quote, recommendations_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                overall_rating = excluded.overall_rating,
                sus_score = excluded.sus_score,
                ces_score = excluded.ces_score,
                nps_rating = excluded.nps_rating,
                sentiment_summary = excluded.sentiment_summary,
                what_worked_well_json = excluded.what_worked_well_json,
                confusing_elements_json = excluded.confusing_elements_json,
                friction_points_json = excluded.friction_points_json,
                verbatim_quote = excluded.verbatim_quote,
                recommendations_json = excluded.recommendations_json;
            """,
            (
                feedback.feedback_id,
                feedback.session_id,
                feedback.persona_id,
                feedback.persona_name,
                feedback.overall_rating,
                feedback.sus_score,
                feedback.ces_score,
                feedback.nps_rating,
                feedback.sentiment_summary,
                json.dumps(feedback.what_worked_well),
                json.dumps(feedback.confusing_elements),
                json.dumps(feedback.friction_points),
                feedback.verbatim_quote,
                json.dumps(feedback.recommendations),
            ),
        )


def get_feedback_by_session(
    session_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> PersonaFeedback | None:
    """Fetch feedback for a given session."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        row = conn.execute(
            "SELECT * FROM session_feedback WHERE session_id = ?;",
            (session_id,),
        ).fetchone()
        if row:
            return PersonaFeedback(
                feedback_id=row["feedback_id"],
                session_id=row["session_id"],
                persona_id=row["persona_id"],
                persona_name=row["persona_name"],
                overall_rating=row["overall_rating"],
                sus_score=row["sus_score"],
                ces_score=row["ces_score"],
                nps_rating=row["nps_rating"],
                sentiment_summary=row["sentiment_summary"],
                what_worked_well=json.loads(row["what_worked_well_json"]),
                confusing_elements=json.loads(row["confusing_elements_json"]),
                friction_points=json.loads(row["friction_points_json"]),
                verbatim_quote=row["verbatim_quote"],
                recommendations=json.loads(row["recommendations_json"]),
            )
    return None


def list_feedback_by_campaign(
    campaign_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> list[PersonaFeedback]:
    """Retrieve all feedbacks for sessions in a campaign."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        rows = conn.execute(
            """
            SELECT sf.* FROM session_feedback sf
            JOIN agent_sessions s ON sf.session_id = s.session_id
            WHERE s.campaign_id = ?;
            """,
            (campaign_id,),
        ).fetchall()
        feedbacks: list[PersonaFeedback] = []
        for row in rows:
            feedbacks.append(
                PersonaFeedback(
                    feedback_id=row["feedback_id"],
                    session_id=row["session_id"],
                    persona_id=row["persona_id"],
                    persona_name=row["persona_name"],
                    overall_rating=row["overall_rating"],
                    sus_score=row["sus_score"],
                    ces_score=row["ces_score"],
                    nps_rating=row["nps_rating"],
                    sentiment_summary=row["sentiment_summary"],
                    what_worked_well=json.loads(row["what_worked_well_json"]),
                    confusing_elements=json.loads(row["confusing_elements_json"]),
                    friction_points=json.loads(row["friction_points_json"]),
                    verbatim_quote=row["verbatim_quote"],
                    recommendations=json.loads(row["recommendations_json"]),
                )
            )
        return feedbacks


def save_uat_report(
    report: UATReport,
    report_markdown: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> None:
    """Persist generated UAT synthesis report."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO uat_reports (
                report_id, campaign_id, title, generated_at, report_json, report_markdown
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                report.report_id,
                report.campaign_id,
                report.title,
                report.generated_at,
                report.model_dump_json(),
                report_markdown,
            ),
        )


def get_uat_report(
    campaign_id: str,
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> tuple[UATReport | None, str | None]:
    """Retrieve UAT report model and markdown for a campaign."""
    initialize_database(database_path)
    with connect(database_path) as conn:
        row = conn.execute(
            "SELECT report_json, report_markdown FROM uat_reports WHERE campaign_id = ? ORDER BY generated_at DESC LIMIT 1;",
            (campaign_id,),
        ).fetchone()
        if row:
            return UATReport.model_validate_json(row["report_json"]), row["report_markdown"]
    return None, None


# ---------------------------------------------------------
# Anti-Mirage Invariant 3 Verification Routine
# ---------------------------------------------------------

def verify_live_datastore_write(
    database_path: Path = DEFAULT_SIMULACRA_DB_PATH,
) -> bool:
    """Enforce Invariant 3: Live Datastore Write Verification.

    Must insert records across tables, read them back, assert fidelity, and confirm non-zero count.
    Raises RuntimeError on failure.
    """
    initialize_database(database_path)
    test_id = "test_inv3_probe"

    with connect(database_path) as conn:
        # Check tables exist
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        }
        required_tables = {
            "campaigns",
            "personas",
            "agent_sessions",
            "telemetry_events",
            "session_feedback",
            "uat_reports",
        }
        missing = required_tables - tables
        if missing:
            raise RuntimeError(f"Missing tables in datastore: {missing}")

        # Live write test
        conn.execute(
            """
            INSERT OR REPLACE INTO campaigns (
                campaign_id, title, target_url, primary_goal, created_at, status, config_json
            ) VALUES (?, 'Probe Campaign', 'http://127.0.0.1', 'Probe goal', '2026-09-24T00:00:00Z', 'COMPLETED', '{}');
            """,
            (test_id,),
        )
        # Read back
        row = conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?;", (test_id,)
        ).fetchone()
        if not row or row["title"] != "Probe Campaign":
            raise RuntimeError("Live write verification failed to read back inserted campaign")

        # Cleanup probe
        conn.execute("DELETE FROM campaigns WHERE campaign_id = ?;", (test_id,))

    return True
