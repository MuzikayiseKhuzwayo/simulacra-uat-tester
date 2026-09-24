"""Cognitive Journey Planner & Decision Engine for Simulacra UAT.

Models human-like behavioral decisions, cognitive friction, emotional state transitions,
and inner-monologue reasoning based on synthetic persona profiles.
"""

from dataclasses import dataclass
from typing import Any
from src.simulacra.models import (
    ActionType,
    CampaignMission,
    Emotion,
    ExitReason,
    PatienceLevel,
    Persona,
    ReadingSpeed,
    TechnicalSkill,
    TelemetryEvent,
)


@dataclass
class PageObservation:
    """Snapshot of page state observed by browser agent."""

    url: str
    title: str
    scroll_y: int
    page_height: int
    viewport_height: int
    interactive_elements: list[dict[str, Any]]
    headings: list[str]
    form_inputs: list[dict[str, Any]]
    has_success_marker: bool
    has_error_marker: bool
    error_text: str | None


@dataclass
class PlannedDecision:
    """Action and cognitive state decided by the planner."""

    action_type: ActionType
    target_selector: str | None
    target_text: str | None
    input_value: str | None
    scroll_amount: int
    hesitation_ms: int
    rage_clicks: int
    emotion: Emotion
    confidence: float
    cognitive_reasoning: str
    is_terminal: bool
    exit_reason: ExitReason | None


class CognitivePlanner:
    """Simulates realistic user cognition, intent, hesitation, and emotional shifts."""

    def __init__(self, persona: Persona, mission: CampaignMission) -> None:
        self.persona = persona
        self.mission = mission
        self.current_emotion = Emotion.NEUTRAL
        self.accumulated_friction = 0.0
        self.visited_urls: set[str] = set()
        self.clicked_selectors: set[str] = set()
        self.step_count = 0

    def evaluate_step(
        self,
        observation: PageObservation,
        history: list[TelemetryEvent],
    ) -> PlannedDecision:
        """Analyze page state and decide the persona's next cognitive and physical action."""
        self.step_count += 1
        self.visited_urls.add(observation.url)

        # 1. Check Success Conditions
        has_met_criteria = False
        if self.mission.success_criteria:
            for crit in self.mission.success_criteria:
                cl = crit.lower()
                if any(cl in h.lower() for h in observation.headings) or cl in observation.title.lower():
                    has_met_criteria = True
                    break

        is_spa_goal_satisfied = (
            self.step_count >= 4
            and any(any(kw in s.lower() for kw in ("launch", "pricing", "trial", "pathfinder")) for s in self.clicked_selectors)
            and self.accumulated_friction < 50
        )

        if observation.has_success_marker or has_met_criteria or is_spa_goal_satisfied or (
            "/dashboard" in observation.url
            and ("dashboard" in self.persona.primary_goal.lower() or "invoice" in self.persona.primary_goal.lower() or "trial" in self.persona.primary_goal.lower())
        ):
            self.current_emotion = Emotion.SATISFIED
            return PlannedDecision(
                action_type=ActionType.COMPLETE_GOAL,
                target_selector=None,
                target_text=None,
                input_value=None,
                scroll_amount=0,
                hesitation_ms=self._calculate_hesitation(base_ms=400),
                rage_clicks=0,
                emotion=Emotion.SATISFIED,
                confidence=0.95,
                cognitive_reasoning=(
                    f"Successfully explored application workflow! Reached target objectives on '{observation.title}' "
                    f"and completed evaluation for: '{self.persona.primary_goal}'."
                ),
                is_terminal=True,
                exit_reason=ExitReason.GOAL_COMPLETED,
            )

        # 2. Check Patience / Friction Threshold
        patience_limit = 6 if self.persona.patience == PatienceLevel.LOW else 12 if self.persona.patience == PatienceLevel.MEDIUM else 20
        if self.step_count >= patience_limit and self.accumulated_friction > 60:
            self.current_emotion = Emotion.ABANDONED
            return PlannedDecision(
                action_type=ActionType.ABANDON,
                target_selector=None,
                target_text=None,
                input_value=None,
                scroll_amount=0,
                hesitation_ms=self._calculate_hesitation(base_ms=1200),
                rage_clicks=0,
                emotion=Emotion.ABANDONED,
                confidence=0.15,
                cognitive_reasoning=(
                    f"I have had enough. I am feeling {self.current_emotion.value} after {self.step_count} "
                    f"steps without clear progress toward '{self.persona.primary_goal}'. Abandoning session."
                ),
                is_terminal=True,
                exit_reason=ExitReason.PATIENCE_EXHAUSTED,
            )

        # 3. Handle Form Pages (/signup, modal forms)
        if observation.form_inputs and any(not f.get("filled") for f in observation.form_inputs):
            unfilled = [f for f in observation.form_inputs if not f.get("filled")]
            target_field = unfilled[0]
            field_name = target_field.get("name", "input")
            field_type = target_field.get("type", "text")

            val = self._generate_form_value(field_name, field_type)
            hesitation = self._calculate_hesitation(base_ms=750)

            # Sarah/Marcus bias: hates complex forms
            if "hates complex" in " ".join(self.persona.biases).lower():
                self.accumulated_friction += 8
                self.current_emotion = Emotion.HESITANT
                reasoning = (
                    f"Filling in '{field_name}'. As a {self.persona.role}, I hate lengthy sign-up forms, "
                    "hoping this doesn't ask for billing info right away."
                )
            else:
                self.current_emotion = Emotion.CONFIDENT
                reasoning = f"Entering my {field_name} into the form."

            return PlannedDecision(
                action_type=ActionType.FILL_INPUT,
                target_selector=target_field.get("selector"),
                target_text=field_name,
                input_value=val,
                scroll_amount=0,
                hesitation_ms=hesitation,
                rage_clicks=0,
                emotion=self.current_emotion,
                confidence=0.8,
                cognitive_reasoning=reasoning,
                is_terminal=False,
                exit_reason=None,
            )

        # Submit form if all filled and submit button is available
        if observation.form_inputs and all(f.get("filled") for f in observation.form_inputs):
            submit_btn = next(
                (el for el in observation.interactive_elements if el.get("type") == "submit" or "submit" in el.get("text", "").lower() or "register" in el.get("text", "").lower()),
                None,
            )
            if submit_btn:
                return PlannedDecision(
                    action_type=ActionType.SUBMIT_FORM,
                    target_selector=submit_btn.get("selector"),
                    target_text=submit_btn.get("text"),
                    input_value=None,
                    scroll_amount=0,
                    hesitation_ms=self._calculate_hesitation(base_ms=600),
                    rage_clicks=0,
                    emotion=Emotion.CONFIDENT,
                    confidence=0.85,
                    cognitive_reasoning=f"All fields filled. Clicking '{submit_btn.get('text')}' to submit the form.",
                    is_terminal=False,
                    exit_reason=None,
                )

        # 4. Check for Rage Click Trigger on unclickable/misleading element
        rage_target = next(
            (el for el in observation.interactive_elements if "rage-target" in el.get("classes", "") or "demo" in el.get("text", "").lower() and el.get("tag") == "span"),
            None,
        )
        if rage_target and self.step_count == 2 and self.persona.patience == PatienceLevel.LOW:
            self.accumulated_friction += 25
            self.current_emotion = Emotion.FRUSTRATED
            return PlannedDecision(
                action_type=ActionType.RAGE_CLICK,
                target_selector=rage_target.get("selector"),
                target_text=rage_target.get("text"),
                input_value=None,
                scroll_amount=0,
                hesitation_ms=self._calculate_hesitation(base_ms=300),
                rage_clicks=3,
                emotion=Emotion.FRUSTRATED,
                confidence=0.3,
                cognitive_reasoning=(
                    f"Clicked '{rage_target.get('text')}' multiple times because it looks like a button, "
                    "but nothing happened! Feeling frustrated."
                ),
                is_terminal=False,
                exit_reason=None,
            )

        # 5. Look for Intent-Matched CTA / Links
        best_element = self._find_best_interactive_match(observation)
        if best_element:
            target_selector = best_element.get("selector")
            target_text = best_element.get("text", "link")
            self.clicked_selectors.add(target_selector)

            emotion = Emotion.CURIOUS if self.step_count < 3 else Emotion.CONFIDENT
            self.current_emotion = emotion
            hesitation = self._calculate_hesitation(base_ms=500)

            reasoning = (
                f"Spotted '{target_text}'. This matches my goal '{self.persona.primary_goal}'. "
                f"Clicking to proceed."
            )

            return PlannedDecision(
                action_type=ActionType.CLICK,
                target_selector=target_selector,
                target_text=target_text,
                input_value=None,
                scroll_amount=0,
                hesitation_ms=hesitation,
                rage_clicks=0,
                emotion=emotion,
                confidence=0.75,
                cognitive_reasoning=reasoning,
                is_terminal=False,
                exit_reason=None,
            )

        # 6. Scroll down to discover content if near top
        if observation.scroll_y < (observation.page_height - observation.viewport_height - 100):
            self.accumulated_friction += 5
            hesitation = self._calculate_hesitation(base_ms=450)
            return PlannedDecision(
                action_type=ActionType.SCROLL_DOWN,
                target_selector=None,
                target_text=None,
                input_value=None,
                scroll_amount=min(450, observation.viewport_height // 2),
                hesitation_ms=hesitation,
                rage_clicks=0,
                emotion=Emotion.NEUTRAL if self.accumulated_friction < 20 else Emotion.HESITANT,
                confidence=0.6,
                cognitive_reasoning=(
                    f"No immediate obvious match above the fold for '{self.persona.primary_goal}'. "
                    "Scrolling down to explore more options."
                ),
                is_terminal=False,
                exit_reason=None,
            )

        # 7. Fallback: Dead end or max steps
        self.accumulated_friction += 15
        self.current_emotion = Emotion.CONFUSED
        return PlannedDecision(
            action_type=ActionType.HESITATE,
            target_selector=None,
            target_text=None,
            input_value=None,
            scroll_amount=0,
            hesitation_ms=self._calculate_hesitation(base_ms=1000),
            rage_clicks=0,
            emotion=Emotion.CONFUSED,
            confidence=0.3,
            cognitive_reasoning=(
                f"I am confused. Explored page '{observation.title}', but could not find a clear path "
                f"forward for my objective."
            ),
            is_terminal=(self.step_count >= self.mission.max_steps),
            exit_reason=ExitReason.MAX_STEPS_REACHED if (self.step_count >= self.mission.max_steps) else None,
        )

    def _calculate_hesitation(self, base_ms: int) -> int:
        """Calculate human-like hesitation delay based on reading speed and patience."""
        multiplier = 1.0
        if self.persona.reading_speed == ReadingSpeed.SLOW:
            multiplier *= 1.4
        elif self.persona.reading_speed == ReadingSpeed.FAST:
            multiplier *= 0.75

        if self.persona.patience == PatienceLevel.LOW:
            multiplier *= 0.8
        elif self.persona.patience == PatienceLevel.HIGH:
            multiplier *= 1.25

        return int(base_ms * multiplier)

    def _generate_form_value(self, field_name: str, field_type: str) -> str:
        """Provide believable input data according to field context."""
        name_lower = field_name.lower()
        if "name" in name_lower:
            return self.persona.name
        if "email" in name_lower or field_type == "email":
            clean_name = self.persona.name.lower().replace(" ", ".")
            return f"{clean_name}@example.org"
        if "password" in name_lower or field_type == "password":
            return "SecurePass2026!"
        if "company" in name_lower:
            return f"{self.persona.name.split()[0]} Dynamics"
        if "amount" in name_lower:
            return "2450.00"
        if "client" in name_lower:
            return "Vanguard Partners"
        return "Standard Value"

    def _find_best_interactive_match(
        self, observation: PageObservation
    ) -> dict[str, Any] | None:
        """Score interactive elements according to persona biases and goal alignment."""
        goal_keywords = [w.lower() for w in self.persona.primary_goal.split() if len(w) > 3]
        best_score = -1.0
        best_element = None

        for el in observation.interactive_elements:
            selector = el.get("selector", "")
            if selector in self.clicked_selectors:
                continue

            text = el.get("text", "").lower()
            href = el.get("href", "").lower()
            score = 0.0

            # Match persona goal keywords
            for kw in goal_keywords:
                if kw in text or kw in href:
                    score += 5.0

            # Persona role-specific preferences
            if "pricing" in self.persona.primary_goal.lower() and "pricing" in text:
                score += 8.0
            if "trial" in self.persona.primary_goal.lower() and ("trial" in text or "start" in text or "free" in text or "signup" in href):
                score += 10.0
            if "invoice" in self.persona.primary_goal.lower() and ("invoice" in text or "create" in text or "dashboard" in href):
                score += 9.0
            if "docs" in self.persona.primary_goal.lower() and ("doc" in text or "api" in text or "auth" in text):
                score += 9.0

            # Button vs raw link bias
            if el.get("tag") == "button" or "btn" in el.get("classes", ""):
                score += 2.0

            if score > best_score and score > 2.0:
                best_score = score
                best_element = el

        return best_element
