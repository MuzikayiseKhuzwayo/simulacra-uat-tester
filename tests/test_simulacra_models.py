"""Unit tests for Simulacra UAT Pydantic contracts."""

import pytest
from pydantic import ValidationError

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
)


def test_persona_contract_valid():
    p = Persona(
        persona_id="p1",
        name="Test User",
        role="Tester",
        age=30,
        technical_skill=TechnicalSkill.MEDIUM,
        patience=PatienceLevel.HIGH,
        biases=["hates jargon"],
        primary_goal="Test the app",
        device_type=DeviceType.DESKTOP,
    )
    assert p.persona_id == "p1"
    assert p.viewport_width == 1280
    assert p.viewport_height == 800


def test_persona_contract_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Persona(
            persona_id="p1",
            name="Test User",
            role="Tester",
            age=30,
            technical_skill=TechnicalSkill.MEDIUM,
            patience=PatienceLevel.HIGH,
            biases=["hates jargon"],
            primary_goal="Test the app",
            unknown_prop="illegal",
        )


def test_mission_validation():
    mission = CampaignMission(
        mission_id="m1",
        title="Mission 1",
        target_url="http://example.com",
        primary_goal="Buy product",
        max_steps=10,
    )
    assert mission.mission_id == "m1"
    assert mission.timeout_seconds == 60


def test_telemetry_event_contract():
    event = TelemetryEvent(
        event_id="e1",
        session_id="s1",
        step_number=1,
        timestamp="2026-09-24T00:00:00Z",
        page_url="http://example.com",
        action_type=ActionType.CLICK,
        emotion=Emotion.CURIOUS,
        confidence=0.8,
        cognitive_reasoning="Looking at hero button",
    )
    assert event.action_type == ActionType.CLICK
    assert event.emotion == Emotion.CURIOUS
    assert event.scroll_depth_percent == 0.0


def test_feedback_scores_boundaries():
    fb = PersonaFeedback(
        feedback_id="fb1",
        session_id="s1",
        persona_id="p1",
        persona_name="Sarah",
        overall_rating=4,
        sus_score=85.5,
        ces_score=6,
        nps_rating=9,
        sentiment_summary="Great experience",
        what_worked_well=["Easy navigation"],
        confusing_elements=[],
        friction_points=[],
        verbatim_quote="Really liked the ease of use.",
        recommendations=["Keep it fast"],
    )
    assert fb.overall_rating == 4
    assert fb.sus_score == 85.5
