"""Tests for Gemini 2.5 integration across Simulacra UAT."""

from unittest.mock import MagicMock
import pytest

from src.config import Settings, get_gemini_model
from src.simulacra.models import (
    ActionType,
    CampaignMission,
    Emotion,
    Persona,
    SessionMetrics,
    TelemetryEvent,
)
from src.simulacra.persona import get_preset_personas
from src.simulacra.planner import (
    CognitivePlanner,
    GeminiStepDecision,
    PageObservation,
)
from src.simulacra.feedback import FeedbackEngine, GeminiFeedbackSynthesis
from src.simulacra.quantix_feedback_form import (
    GeminiQuantixOpenEnded,
    _generate_gemini_quantix_open_ended,
    generate_quantix_feedback,
)


def test_gemini_step_decision_schema_parsing():
    """Verify GeminiStepDecision parses structured JSON correctly."""
    json_str = (
        '{"action_type": "click", "target_selector": "#trial-btn", "target_text": "Start Trial", '
        '"emotion": "curious", "confidence": 0.85, '
        '"cognitive_reasoning": "As a founder, I want to see the pricing and trial terms directly.", '
        '"is_terminal": false}'
    )
    decision = GeminiStepDecision.model_validate_json(json_str)
    assert decision.action_type == ActionType.CLICK
    assert decision.target_selector == "#trial-btn"
    assert decision.emotion == Emotion.CURIOUS
    assert decision.confidence == 0.85
    assert "founder" in decision.cognitive_reasoning


def test_planner_evaluates_with_gemini_mock():
    """Verify CognitivePlanner integrates Gemini 2.5 client correctly."""
    persona = get_preset_personas()[0]
    mission = CampaignMission(
        mission_id="m1",
        title="Test Mission",
        target_url="http://test.local",
        primary_goal="Evaluate platform",
    )
    planner = CognitivePlanner(persona, mission, use_gemini=True)

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = (
        '{"action_type": "click", "target_selector": "a.nav-pricing", "target_text": "Pricing", '
        '"emotion": "confident", "confidence": 0.9, '
        '"cognitive_reasoning": "I want to check the pricing tiers first.", "is_terminal": false}'
    )
    mock_client.models.generate_content.return_value = mock_resp

    obs = PageObservation(
        url="http://test.local",
        title="Home Page",
        scroll_y=0,
        page_height=800,
        viewport_height=800,
        interactive_elements=[{"tag": "a", "text": "Pricing", "selector": "a.nav-pricing"}],
        headings=["Welcome"],
        form_inputs=[],
        has_success_marker=False,
        has_error_marker=False,
        error_text=None,
    )

    decision = planner._evaluate_step_gemini(obs, history=[], client=mock_client)

    assert decision is not None
    assert decision.action_type == ActionType.CLICK
    assert decision.target_selector == "a.nav-pricing"
    assert decision.emotion == Emotion.CONFIDENT
    assert "pricing tiers" in decision.cognitive_reasoning


def test_feedback_engine_with_gemini_mock():
    """Verify FeedbackEngine synthesizes qualitative critique with Gemini 2.5."""
    persona = get_preset_personas()[0]
    metrics = SessionMetrics(
        session_id="s1",
        campaign_id="c1",
        persona_id=persona.persona_id,
        persona_name=persona.name,
        started_at="2026-09-24T00:00:00Z",
        duration_seconds=45.0,
        total_steps=5,
        task_success=True,
    )
    telemetry = [
        TelemetryEvent(
            event_id="e1",
            session_id="s1",
            step_number=1,
            timestamp="2026-09-24T00:00:00Z",
            page_url="http://test.local",
            page_title="Home",
            action_type=ActionType.CLICK,
            emotion=Emotion.CONFIDENT,
            cognitive_reasoning="Looking for quick setup.",
        )
    ]

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = (
        '{"verbatim_quote": "\\"The platform was clear and took less than a minute.\\" — Sarah (Small Business Owner)", '
        '"sentiment_summary": "Highly impressed by onboarding clarity.", '
        '"what_worked_well": ["Rapid navigation", "Clean header"], '
        '"confusing_elements": ["Subtle footer links"], '
        '"friction_points": [], '
        '"recommendations": ["Add video demo"]}'
    )
    mock_client.models.generate_content.return_value = mock_resp

    synthesis = FeedbackEngine._generate_gemini_feedback(
        persona=persona,
        metrics=metrics,
        telemetry=telemetry,
        sus_score=85.0,
        client=mock_client,
    )

    assert synthesis is not None
    assert "Sarah" in synthesis.verbatim_quote
    assert "Rapid navigation" in synthesis.what_worked_well
    assert len(synthesis.recommendations) == 1


def test_quantix_open_ended_with_gemini_mock():
    """Verify Quantix survey open-ended generation with Gemini 2.5."""
    persona = get_preset_personas()[1]
    metrics = SessionMetrics(
        session_id="s2",
        campaign_id="c2",
        persona_id=persona.persona_id,
        persona_name=persona.name,
        started_at="2026-09-24T00:00:00Z",
        duration_seconds=60.0,
        total_steps=6,
        task_success=True,
    )

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = (
        '{"convincing_element": "The mathematical drawdown defense model", '
        '"hesitation_trigger": "Initial dense jargon", '
        '"aha_moment": "Seeing volatility envelope breakdown", '
        '"most_frustrating_moment": "Unclickable sandbox badge", '
        '"missing_feature_expected": "REST Webhook integration", '
        '"nps_reason": "High institutional discipline", '
        '"magic_wand_change": "Direct terminal preview", '
        '"one_sentence_pitch": "Automated mathematical risk governance", '
        '"expected_transformation": "Zero-guesswork capital preservation"}'
    )
    mock_client.models.generate_content.return_value = mock_resp

    res = _generate_gemini_quantix_open_ended(
        persona=persona,
        metrics=metrics,
        telemetry=[],
        client=mock_client,
    )

    assert res is not None
    assert "drawdown defense" in res.convincing_element
    assert "REST Webhook" in res.missing_feature_expected
