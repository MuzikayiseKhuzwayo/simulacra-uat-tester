"""Tests for Simulacra UAT SQLite persistence and Invariant 3 verification."""

from pathlib import Path
import pytest

from src.simulacra.database import (
    connect,
    get_campaign,
    get_feedback_by_session,
    get_persona,
    get_session_telemetry,
    get_uat_report,
    initialize_database,
    list_campaigns,
    list_feedback_by_campaign,
    list_sessions_by_campaign,
    save_campaign,
    save_feedback,
    save_persona,
    save_session,
    save_telemetry_event,
    save_uat_report,
    verify_live_datastore_write,
)
from src.simulacra.models import (
    ActionType,
    CampaignMission,
    DeviceType,
    Emotion,
    ExitReason,
    PatienceLevel,
    Persona,
    PersonaFeedback,
    SessionMetrics,
    TechnicalSkill,
    TelemetryEvent,
    UATReport,
    CampaignSummary,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_simulacra.db"
    initialize_database(db_file)
    return db_file


def test_invariant3_live_datastore_write(temp_db: Path):
    """Enforce Invariant 3: Live datastore write verification must succeed."""
    assert verify_live_datastore_write(temp_db) is True


def test_persona_crud(temp_db: Path):
    p = Persona(
        persona_id="test_p1",
        name="Alice Walker",
        role="Product Designer",
        age=31,
        technical_skill=TechnicalSkill.HIGH,
        patience=PatienceLevel.MEDIUM,
        biases=["Values aesthetics"],
        primary_goal="Check contrast",
        device_type=DeviceType.DESKTOP,
    )
    save_persona(p, database_path=temp_db)
    loaded = get_persona("test_p1", database_path=temp_db)
    assert loaded is not None
    assert loaded.name == "Alice Walker"
    assert loaded.technical_skill == TechnicalSkill.HIGH


def test_campaign_and_session_full_lifecycle(temp_db: Path):
    mission = CampaignMission(
        mission_id="camp_lifecycle_1",
        title="Lifecycle Test",
        target_url="http://test.local",
        primary_goal="Check signup",
    )
    save_campaign(
        campaign_id="camp_lifecycle_1",
        title="Lifecycle Test",
        target_url="http://test.local",
        primary_goal="Check signup",
        created_at="2026-09-24T00:00:00Z",
        status="RUNNING",
        config=mission,
        database_path=temp_db,
    )

    campaigns = list_campaigns(database_path=temp_db)
    assert len(campaigns) == 1
    assert campaigns[0]["campaign_id"] == "camp_lifecycle_1"

    # Save initial session
    metrics = SessionMetrics(
        session_id="sess_101",
        campaign_id="camp_lifecycle_1",
        persona_id="p_test",
        persona_name="Tester",
        started_at="2026-09-24T00:00:01Z",
        completed_at="2026-09-24T00:00:05Z",
        duration_seconds=4.0,
        total_steps=3,
        pages_visited=1,
        total_clicks=2,
        rage_clicks_total=0,
        hesitation_time_total_ms=400,
        friction_score=15.0,
        task_success=True,
        exit_reason=ExitReason.GOAL_COMPLETED,
        final_sentiment=Emotion.SATISFIED,
    )
    save_session(metrics, database_path=temp_db)

    # Save telemetry event
    evt = TelemetryEvent(
        event_id="evt_01",
        session_id="sess_101",
        step_number=1,
        timestamp="2026-09-24T00:00:02Z",
        page_url="http://test.local",
        page_title="Test Home",
        action_type=ActionType.CLICK,
        target_element="#btn-test",
        target_text="Submit",
        scroll_depth_percent=10.0,
        hesitation_ms=200,
        rage_click_count=0,
        emotion=Emotion.CONFIDENT,
        confidence=0.9,
        cognitive_reasoning="Target verified.",
        screenshot_path=None,
    )
    save_telemetry_event(evt, database_path=temp_db)

    # Save feedback
    fb = PersonaFeedback(
        feedback_id="fb_01",
        session_id="sess_101",
        persona_id="p_test",
        persona_name="Tester",
        overall_rating=5,
        sus_score=92.0,
        ces_score=7,
        nps_rating=10,
        sentiment_summary="Excellent",
        what_worked_well=["Fast form"],
        confusing_elements=[],
        friction_points=[],
        verbatim_quote="Everything went smoothly.",
        recommendations=[],
    )
    save_feedback(fb, database_path=temp_db)

    # Assert retrieval
    sessions = list_sessions_by_campaign("camp_lifecycle_1", database_path=temp_db)
    assert len(sessions) == 1
    assert sessions[0].task_success is True

    telemetry = get_session_telemetry("sess_101", database_path=temp_db)
    assert len(telemetry) == 1
    assert telemetry[0].target_element == "#btn-test"

    fb_loaded = get_feedback_by_session("sess_101", database_path=temp_db)
    assert fb_loaded is not None
    assert fb_loaded.sus_score == 92.0

    all_fb = list_feedback_by_campaign("camp_lifecycle_1", database_path=temp_db)
    assert len(all_fb) == 1
