"""Pydantic data contracts for Simulacra UAT simulation platform."""

from enum import StrEnum
from typing import Annotated
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)

NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class StrictModel(BaseModel):
    """Base model that forbids uncontracted fields and strips strings."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TechnicalSkill(StrEnum):
    """User technical skill level."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class PatienceLevel(StrEnum):
    """User patience tolerance level."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AttentionSpan(StrEnum):
    """User attention span."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ReadingSpeed(StrEnum):
    """User reading speed."""

    SLOW = "Slow"
    AVERAGE = "Average"
    FAST = "Fast"


class RiskTolerance(StrEnum):
    """User risk tolerance when exploring web apps."""

    CAUTIOUS = "Cautious"
    MODERATE = "Moderate"
    ADVENTUROUS = "Adventurous"


class DeviceType(StrEnum):
    """Simulated device form factor."""

    DESKTOP = "Desktop"
    MOBILE = "Mobile"
    TABLET = "Tablet"


class ActionType(StrEnum):
    """Simulated user action in browser."""

    NAVIGATE = "navigate"
    CLICK = "click"
    FILL_INPUT = "fill_input"
    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"
    HESITATE = "hesitate"
    RAGE_CLICK = "rage_click"
    READ_CONTENT = "read_content"
    SUBMIT_FORM = "submit_form"
    COMPLETE_GOAL = "complete_goal"
    ABANDON = "abandon"


class Emotion(StrEnum):
    """Simulated cognitive & emotional state."""

    CURIOUS = "curious"
    CONFIDENT = "confident"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    HESITANT = "hesitant"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ANNOYED = "annoyed"
    ABANDONED = "abandoned"


class ExitReason(StrEnum):
    """Reason why the simulated user ended their session."""

    GOAL_COMPLETED = "GOAL_COMPLETED"
    PATIENCE_EXHAUSTED = "PATIENCE_EXHAUSTED"
    NAVIGATION_DEAD_END = "NAVIGATION_DEAD_END"
    CONFUSION_THRESHOLD = "CONFUSION_THRESHOLD"
    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class Persona(StrictModel):
    """Synthetic customer persona profile with behavioral biases."""

    persona_id: NonEmptyString
    name: NonEmptyString
    role: NonEmptyString
    age: int = Field(ge=16, le=100)
    technical_skill: TechnicalSkill
    patience: PatienceLevel
    attention_span: AttentionSpan = AttentionSpan.MEDIUM
    reading_speed: ReadingSpeed = ReadingSpeed.AVERAGE
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    biases: list[NonEmptyString] = Field(min_length=1)
    primary_goal: NonEmptyString
    device_type: DeviceType = DeviceType.DESKTOP
    viewport_width: int = Field(default=1280, ge=320, le=3840)
    viewport_height: int = Field(default=800, ge=480, le=2160)
    user_agent: str | None = None


class CampaignMission(StrictModel):
    """Configuration for a UAT simulation run."""

    mission_id: NonEmptyString
    title: NonEmptyString
    target_url: NonEmptyString
    primary_goal: NonEmptyString
    success_criteria: list[NonEmptyString] = Field(default_factory=list)
    max_steps: int = Field(default=25, ge=1, le=100)
    timeout_seconds: int = Field(default=60, ge=10, le=600)
    capture_screenshots: bool = True
    headless: bool = True


class TelemetryEvent(StrictModel):
    """Single fine-grained behavioral and cognitive event from simulated browsing."""

    event_id: NonEmptyString
    session_id: NonEmptyString
    step_number: int = Field(ge=0)
    timestamp: NonEmptyString
    page_url: NonEmptyString
    page_title: str = ""
    action_type: ActionType
    target_element: str | None = None
    target_text: str | None = None
    scroll_depth_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    hesitation_ms: int = Field(default=0, ge=0)
    rage_click_count: int = Field(default=0, ge=0)
    emotion: Emotion = Emotion.NEUTRAL
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    cognitive_reasoning: NonEmptyString
    screenshot_path: str | None = None


class SessionMetrics(StrictModel):
    """Aggregated behavioral telemetry metrics for a completed agent session."""

    session_id: NonEmptyString
    campaign_id: NonEmptyString
    persona_id: NonEmptyString
    persona_name: NonEmptyString
    started_at: NonEmptyString
    completed_at: str | None = None
    duration_seconds: float = Field(default=0.0, ge=0.0)
    total_steps: int = Field(default=0, ge=0)
    pages_visited: int = Field(default=0, ge=0)
    total_clicks: int = Field(default=0, ge=0)
    rage_clicks_total: int = Field(default=0, ge=0)
    hesitation_time_total_ms: int = Field(default=0, ge=0)
    friction_score: float = Field(default=0.0, ge=0.0, le=100.0)
    task_success: bool = False
    exit_reason: ExitReason = ExitReason.MAX_STEPS_REACHED
    final_sentiment: Emotion = Emotion.NEUTRAL


class PersonaFeedback(StrictModel):
    """Post-test structured qualitative UX feedback and ratings."""

    feedback_id: NonEmptyString
    session_id: NonEmptyString
    persona_id: NonEmptyString
    persona_name: NonEmptyString
    overall_rating: int = Field(ge=1, le=5)
    sus_score: float = Field(ge=0.0, le=100.0)
    ces_score: int = Field(ge=1, le=7)
    nps_rating: int = Field(ge=0, le=10)
    sentiment_summary: NonEmptyString
    what_worked_well: list[str] = Field(default_factory=list)
    confusing_elements: list[str] = Field(default_factory=list)
    friction_points: list[str] = Field(default_factory=list)
    verbatim_quote: NonEmptyString
    recommendations: list[str] = Field(default_factory=list)


class CampaignSummary(StrictModel):
    """High-level metrics for an entire simulation campaign."""

    campaign_id: NonEmptyString
    title: NonEmptyString
    target_url: NonEmptyString
    created_at: NonEmptyString
    total_sessions: int = Field(ge=0)
    successful_sessions: int = Field(ge=0)
    success_rate_percent: float = Field(ge=0.0, le=100.0)
    average_friction_score: float = Field(ge=0.0, le=100.0)
    average_sus_score: float = Field(ge=0.0, le=100.0)
    total_rage_clicks: int = Field(ge=0)
    status: NonEmptyString


class UATReport(StrictModel):
    """Synthesis UAT & UX report across all synthetic user sessions."""

    report_id: NonEmptyString
    campaign_id: NonEmptyString
    title: NonEmptyString
    generated_at: NonEmptyString
    campaign_summary: CampaignSummary
    top_blockers: list[dict] = Field(default_factory=list)
    friction_hotspots: list[dict] = Field(default_factory=list)
    persona_cohort_breakdown: list[dict] = Field(default_factory=list)
    actionable_recommendations: list[dict] = Field(default_factory=list)
    executive_summary: NonEmptyString
