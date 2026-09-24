"""Unit tests for Cognitive Journey Planner."""

from src.simulacra.models import (
    ActionType,
    CampaignMission,
    Emotion,
    ExitReason,
    PatienceLevel,
    Persona,
    TechnicalSkill,
)
from src.simulacra.persona import get_preset_personas
from src.simulacra.planner import CognitivePlanner, PageObservation


def test_planner_detects_goal_completion():
    persona = get_preset_personas()[0]
    mission = CampaignMission(
        mission_id="m1",
        title="Test Mission",
        target_url="http://test.local",
        primary_goal="Reach dashboard and see invoice",
    )
    planner = CognitivePlanner(persona, mission)

    obs = PageObservation(
        url="http://test.local/dashboard",
        title="Dashboard — AcmeCloud",
        scroll_y=0,
        page_height=800,
        viewport_height=800,
        interactive_elements=[],
        headings=["Invoice Management"],
        form_inputs=[],
        has_success_marker=True,
        has_error_marker=False,
        error_text=None,
    )

    decision = planner.evaluate_step(obs, history=[])
    assert decision.action_type == ActionType.COMPLETE_GOAL
    assert decision.is_terminal is True
    assert decision.exit_reason == ExitReason.GOAL_COMPLETED
    assert decision.emotion == Emotion.SATISFIED


def test_planner_handles_form_inputs():
    persona = get_preset_personas()[0]
    mission = CampaignMission(
        mission_id="m1",
        title="Test Mission",
        target_url="http://test.local/signup",
        primary_goal="Sign up for account",
    )
    planner = CognitivePlanner(persona, mission)

    obs = PageObservation(
        url="http://test.local/signup",
        title="Sign Up",
        scroll_y=0,
        page_height=800,
        viewport_height=800,
        interactive_elements=[{"tag": "button", "text": "Register", "selector": "#btn-reg", "type": "submit"}],
        headings=["Create Account"],
        form_inputs=[
            {"name": "name", "selector": "#name", "type": "text", "filled": False},
            {"name": "email", "selector": "#email", "type": "email", "filled": False},
        ],
        has_success_marker=False,
        has_error_marker=False,
        error_text=None,
    )

    decision = planner.evaluate_step(obs, history=[])
    assert decision.action_type == ActionType.FILL_INPUT
    assert decision.target_selector == "#name"
    assert decision.input_value is not None


def test_planner_rage_clicks_on_unresponsive_element():
    sarah = get_preset_personas()[0]  # Sarah (Low patience)
    mission = CampaignMission(
        mission_id="m1",
        title="Test Mission",
        target_url="http://test.local",
        primary_goal="Test app",
    )
    planner = CognitivePlanner(sarah, mission)
    planner.step_count = 1  # Next will be step 2

    obs = PageObservation(
        url="http://test.local",
        title="Home",
        scroll_y=0,
        page_height=800,
        viewport_height=800,
        interactive_elements=[
            {
                "tag": "span",
                "text": "⚡ Click here for Instant Sandbox Demo",
                "selector": "#demo-badge",
                "classes": "rage-target",
            }
        ],
        headings=["Hero Title"],
        form_inputs=[],
        has_success_marker=False,
        has_error_marker=False,
        error_text=None,
    )

    decision = planner.evaluate_step(obs, history=[])
    assert decision.action_type == ActionType.RAGE_CLICK
    assert decision.rage_clicks >= 3
    assert decision.emotion == Emotion.FRUSTRATED
