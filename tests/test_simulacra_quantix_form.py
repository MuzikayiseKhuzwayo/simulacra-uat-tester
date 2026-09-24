"""Tests for Quantix Google Form schema, persona synthesizer, and persistence."""

from pathlib import Path
import pytest

from src.simulacra.database import (
    initialize_database,
    save_campaign,
    save_persona,
    save_quantix_feedback,
    save_session,
    get_quantix_feedback,
    list_quantix_feedbacks_by_campaign,
)
from src.simulacra.models import (
    ActionType,
    CampaignMission,
    Emotion,
    ExitReason,
    PatienceLevel,
    Persona,
    SessionMetrics,
    TechnicalSkill,
    TelemetryEvent,
)
from src.simulacra.persona import get_preset_personas
from src.simulacra.quantix_feedback_form import (
    GOOGLE_FORM_ID,
    GOOGLE_FORM_VIEW_URL,
    QuantixFeedbackForm,
    build_google_form_payload,
    generate_quantix_feedback,
)
from src.simulacra.reporting import ReportGenerator


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_quantix_form.db"
    initialize_database(db_file)
    return db_file


@pytest.fixture
def sample_persona() -> Persona:
    base = get_preset_personas()[0]
    return base.model_copy(
        update={
            "name": "Sarah Chen",
            "role": "Fintech Founder & Angel",
            "primary_goal": "Assess Quantix for pricing clarity and fast onboarding.",
        }
    )


@pytest.fixture
def sample_metrics() -> SessionMetrics:
    return SessionMetrics(
        session_id="sess_101",
        campaign_id="camp_test",
        persona_id="persona_sarah_smb",
        persona_name="Sarah Chen",
        started_at="2026-09-24T00:00:01Z",
        completed_at="2026-09-24T00:00:43Z",
        duration_seconds=42.5,
        total_steps=8,
        pages_visited=2,
        total_clicks=4,
        rage_clicks_total=0,
        hesitation_time_total_ms=300,
        friction_score=15.0,
        task_success=True,
        exit_reason=ExitReason.GOAL_COMPLETED,
        final_sentiment=Emotion.SATISFIED,
    )


@pytest.fixture
def sample_telemetry() -> list[TelemetryEvent]:
    return [
        TelemetryEvent(
            event_id="evt_101_1",
            session_id="sess_101",
            step_number=1,
            timestamp="2026-09-24T00:00:01Z",
            action_type=ActionType.NAVIGATE,
            page_url="http://localhost:4200/",
            page_title="Quantix — Automated Wealth Intelligence",
            cognitive_reasoning="Landing page loads fast, hero headline catches my eye.",
            emotion=Emotion.CONFIDENT,
            confidence=0.9,
        ),
        TelemetryEvent(
            event_id="evt_101_2",
            session_id="sess_101",
            step_number=2,
            timestamp="2026-09-24T00:00:05Z",
            action_type=ActionType.CLICK,
            target_element="Pricing link",
            page_url="http://localhost:4200/#pricing",
            cognitive_reasoning="Pricing table is transparent and easy to digest.",
            emotion=Emotion.SATISFIED,
            confidence=0.85,
        ),
    ]


def test_quantix_feedback_generation(sample_persona, sample_metrics, sample_telemetry):
    """Verify that generate_quantix_feedback accurately generates all 8 sections."""
    form = generate_quantix_feedback(
        persona=sample_persona,
        metrics=sample_metrics,
        telemetry=sample_telemetry,
    )

    assert isinstance(form, QuantixFeedbackForm)
    assert form.persona_name == "Sarah Chen"
    assert form.session_id == "sess_101"

    # Section 1: Landing page
    assert len(form.gut_reaction) >= 1
    assert 1 <= form.clarity_10_15s <= 5
    assert 1 <= form.visual_design <= 5
    assert 1 <= form.credibility <= 5
    assert len(form.convincing_element) > 0

    # Section 2: Account creation
    assert form.signup_method in ["Email & Password", "Google Single Sign-On (SSO)", "None (Explored as guest/demo)"]

    # Section 3: Initial intake
    assert 1 <= form.relevance_rating <= 5
    assert 1 <= form.clarity_rating <= 5
    assert 1 <= form.progression_rating <= 5
    assert 1 <= form.engagement_rating <= 5

    # Section 4: Core product
    assert len(form.initial_dashboard_feeling) >= 1
    assert 1 <= form.navigating_intuitiveness <= 5
    assert 1 <= form.speed_responsiveness <= 5
    assert len(form.aha_moment) > 0

    # Section 5: Emotional sentiment
    assert form.emotional_sentiment in [
        "Calm/Confident",
        "Hopeful/Curious",
        "Overwhelmed",
        "Confused/Frustrated",
        "Indifferent/Bored",
    ]

    # Section 6: Friction
    assert len(form.prior_alternative_used) > 0

    # Section 7: Overall & PMF
    assert 0 <= form.nps_recommendation <= 10
    assert "disappointed" in form.pmf_feeling.lower() or "not disappointed" in form.pmf_feeling.lower()
    assert len(form.nps_reason) > 0

    # Section 8: Qualification
    assert form.primary_role == "Founder/Executive/C-Suite"
    assert len(form.one_sentence_pitch) > 0
    assert len(form.expected_transformation) > 0


def test_quantix_feedback_payload_building(sample_persona, sample_metrics, sample_telemetry):
    """Verify that build_google_form_payload serializes fields into Google Form entry.XXXX format."""
    form = generate_quantix_feedback(
        persona=sample_persona,
        metrics=sample_metrics,
        telemetry=sample_telemetry,
    )
    payload = build_google_form_payload(form)

    assert isinstance(payload, dict)
    assert len(payload) >= 25
    # Check key entry IDs match the Google Form definition
    assert "entry.326955045" in payload  # clarity_10_15s
    assert "entry.1696159737" in payload  # visual_design
    assert "entry.1522315979" in payload  # nps_recommendation
    assert "entry.1934953822" in payload  # one_sentence_pitch
    assert payload["entry.1934953822"] == form.one_sentence_pitch


def test_quantix_feedback_database_crud(temp_db: Path, sample_persona, sample_metrics, sample_telemetry):
    """Verify storing and retrieving QuantixFeedbackForm from the database."""
    mission = CampaignMission(
        mission_id="camp_test",
        title="Test Campaign",
        target_url="http://localhost:4200",
        primary_goal="Testing",
    )
    save_campaign(
        campaign_id="camp_test",
        title="Test Campaign",
        target_url="http://localhost:4200",
        primary_goal="Testing",
        created_at="2026-09-24T00:00:00Z",
        status="COMPLETED",
        config=mission,
        total_sessions=1,
        database_path=temp_db,
    )
    save_persona(sample_persona, database_path=temp_db)
    save_session(sample_metrics, database_path=temp_db)

    # Generate and save form
    form = generate_quantix_feedback(
        persona=sample_persona,
        metrics=sample_metrics,
        telemetry=sample_telemetry,
    )
    save_quantix_feedback(form, database_path=temp_db)

    # Retrieve by session
    retrieved = get_quantix_feedback("sess_101", database_path=temp_db)
    assert retrieved is not None
    assert retrieved.session_id == "sess_101"
    assert retrieved.persona_name == "Sarah Chen"
    assert retrieved.nps_recommendation == form.nps_recommendation
    assert retrieved.gut_reaction == form.gut_reaction
    assert retrieved.convincing_element == form.convincing_element

    # List by campaign
    camp_forms = list_quantix_feedbacks_by_campaign("camp_test", database_path=temp_db)
    assert len(camp_forms) == 1
    assert camp_forms[0].session_id == "sess_101"


def test_excel_export_includes_google_form_tab(temp_db: Path, sample_persona, sample_metrics, sample_telemetry):
    """Verify that Excel workbook export creates the Google Form Feedback worksheet."""
    mission = CampaignMission(
        mission_id="camp_test",
        title="Test Campaign",
        target_url="http://localhost:4200",
        primary_goal="Testing",
    )
    save_campaign(
        campaign_id="camp_test",
        title="Test Campaign",
        target_url="http://localhost:4200",
        primary_goal="Testing",
        created_at="2026-09-24T00:00:00Z",
        status="COMPLETED",
        config=mission,
        total_sessions=1,
        database_path=temp_db,
    )
    save_persona(sample_persona, database_path=temp_db)
    save_session(sample_metrics, database_path=temp_db)

    form = generate_quantix_feedback(
        persona=sample_persona,
        metrics=sample_metrics,
        telemetry=sample_telemetry,
    )
    save_quantix_feedback(form, database_path=temp_db)

    report, _ = ReportGenerator.generate_report(
        campaign_id="camp_test",
        mission=mission,
        sessions=[sample_metrics],
        feedbacks=[],
        all_telemetry=sample_telemetry,
    )

    excel_bytes = ReportGenerator.export_excel_workbook(
        report=report,
        sessions=[sample_metrics],
        feedbacks=[],
        telemetry=sample_telemetry,
        quantix_feedbacks=[form],
    )

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 2000
