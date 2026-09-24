"""Unit tests for FeedbackEngine and Reporting."""

from src.simulacra.feedback import FeedbackEngine
from src.simulacra.models import (
    ActionType,
    CampaignMission,
    Emotion,
    ExitReason,
    PatienceLevel,
    SessionMetrics,
    TechnicalSkill,
    TelemetryEvent,
)
from src.simulacra.persona import get_preset_personas
from src.simulacra.reporting import ReportGenerator


def test_feedback_high_satisfaction():
    persona = get_preset_personas()[1]  # Marcus
    metrics = SessionMetrics(
        session_id="s1",
        campaign_id="c1",
        persona_id=persona.persona_id,
        persona_name=persona.name,
        started_at="2026-09-24T00:00:00Z",
        completed_at="2026-09-24T00:00:03Z",
        duration_seconds=3.0,
        total_steps=2,
        pages_visited=2,
        total_clicks=1,
        rage_clicks_total=0,
        hesitation_time_total_ms=400,
        friction_score=2.0,
        task_success=True,
        exit_reason=ExitReason.GOAL_COMPLETED,
        final_sentiment=Emotion.SATISFIED,
    )
    feedback = FeedbackEngine.generate_feedback(persona, metrics, telemetry=[])
    assert feedback.overall_rating >= 4
    assert feedback.sus_score >= 80.0
    assert feedback.nps_rating >= 8
    assert "intuitive" in feedback.verbatim_quote.lower() or "direct" in feedback.verbatim_quote.lower()


def test_feedback_rage_clicks_penalty():
    persona = get_preset_personas()[0]  # Sarah
    metrics = SessionMetrics(
        session_id="s2",
        campaign_id="c1",
        persona_id=persona.persona_id,
        persona_name=persona.name,
        started_at="2026-09-24T00:00:00Z",
        completed_at="2026-09-24T00:00:08Z",
        duration_seconds=8.0,
        total_steps=4,
        pages_visited=1,
        total_clicks=5,
        rage_clicks_total=3,
        hesitation_time_total_ms=2500,
        friction_score=85.0,
        task_success=False,
        exit_reason=ExitReason.PATIENCE_EXHAUSTED,
        final_sentiment=Emotion.FRUSTRATED,
    )
    feedback = FeedbackEngine.generate_feedback(persona, metrics, telemetry=[])
    assert feedback.overall_rating <= 2
    assert feedback.sus_score < 40.0
    assert "frustrating" in feedback.verbatim_quote.lower()


def test_reporting_synthesis_and_excel():
    mission = CampaignMission(
        mission_id="camp_rep",
        title="Reporting Verification",
        target_url="http://test.local",
        primary_goal="Check reporting",
    )
    persona = get_preset_personas()[0]
    metrics = SessionMetrics(
        session_id="s3",
        campaign_id="camp_rep",
        persona_id=persona.persona_id,
        persona_name=persona.name,
        started_at="2026-09-24T00:00:00Z",
        completed_at="2026-09-24T00:00:05Z",
        duration_seconds=5.0,
        total_steps=3,
        pages_visited=2,
        total_clicks=2,
        rage_clicks_total=0,
        hesitation_time_total_ms=300,
        friction_score=5.0,
        task_success=True,
        exit_reason=ExitReason.GOAL_COMPLETED,
        final_sentiment=Emotion.SATISFIED,
    )
    feedback = FeedbackEngine.generate_feedback(persona, metrics, telemetry=[])

    report, md = ReportGenerator.generate_report(
        campaign_id="camp_rep",
        mission=mission,
        sessions=[metrics],
        feedbacks=[feedback],
        all_telemetry=[],
    )

    assert report.campaign_summary.total_sessions == 1
    assert report.campaign_summary.success_rate_percent == 100.0
    assert "Simulacra UAT Synthesis Report" in md
    assert report.executive_summary is not None

    excel_bytes = ReportGenerator.export_excel_workbook(
        report=report,
        sessions=[metrics],
        feedbacks=[feedback],
        telemetry=[],
    )
    assert len(excel_bytes) > 1000
