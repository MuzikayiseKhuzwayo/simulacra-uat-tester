"""Synthetic User Feedback & Survey Engine for Simulacra UAT.

Generates structured post-session UX surveys, SUS metrics, CES effort scores,
verbatim persona critiques, and targeted usability recommendations.
"""

import os
import uuid
import logging
from typing import Any
from pydantic import BaseModel, Field

from src.config import get_gemini_client, get_gemini_model
from src.simulacra.models import (
    ActionType,
    ExitReason,
    Emotion,
    PatienceLevel,
    Persona,
    PersonaFeedback,
    SessionMetrics,
    TechnicalSkill,
    TelemetryEvent,
)

logger = logging.getLogger(__name__)


class GeminiFeedbackSynthesis(BaseModel):
    """Pydantic schema for Gemini 2.5 feedback synthesis."""

    verbatim_quote: str
    sentiment_summary: str
    what_worked_well: list[str] = Field(default_factory=list)
    confusing_elements: list[str] = Field(default_factory=list)
    friction_points: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class FeedbackEngine:
    """Analyzes behavioral telemetry to generate authentic persona feedback."""

    @classmethod
    def generate_feedback(
        cls,
        persona: Persona,
        metrics: SessionMetrics,
        telemetry: list[TelemetryEvent],
    ) -> PersonaFeedback:
        """Synthesize post-experience UX survey and structured critique."""
        # 1. Calculate SUS Usability Score (0-100)
        base_sus = 85.0 if metrics.task_success else 40.0
        sus_penalty = (metrics.rage_clicks_total * 15.0) + (metrics.friction_score * 0.35)
        if metrics.exit_reason == ExitReason.PATIENCE_EXHAUSTED:
            sus_penalty += 20.0
        sus_score = max(10.0, min(98.0, round(base_sus - sus_penalty, 1)))

        # 2. Customer Effort Score (1 = very difficult, 7 = very easy)
        if metrics.friction_score < 20 and metrics.task_success:
            ces_score = 6 if metrics.total_steps > 8 else 7
        elif metrics.friction_score < 45 and metrics.task_success:
            ces_score = 5
        elif metrics.task_success:
            ces_score = 4
        elif metrics.exit_reason == ExitReason.PATIENCE_EXHAUSTED:
            ces_score = 2
        else:
            ces_score = 1

        # 3. Overall 1-5 Star Rating & NPS
        if sus_score >= 80:
            overall_rating = 5
            nps_rating = 9
        elif sus_score >= 68:
            overall_rating = 4
            nps_rating = 7
        elif sus_score >= 50:
            overall_rating = 3
            nps_rating = 5
        elif sus_score >= 35:
            overall_rating = 2
            nps_rating = 3
        else:
            overall_rating = 1
            nps_rating = 1

        # 4. Attempt Gemini 2.5 qualitative feedback generation
        use_gemini = os.getenv("SIMULACRA_USE_GEMINI", "true").lower() in ("true", "1")
        if use_gemini:
            client = get_gemini_client()
            if client:
                try:
                    llm_data = cls._generate_gemini_feedback(
                        persona=persona,
                        metrics=metrics,
                        telemetry=telemetry,
                        sus_score=sus_score,
                        client=client,
                    )
                    if llm_data:
                        return PersonaFeedback(
                            feedback_id=f"fb_{uuid.uuid4().hex[:12]}",
                            session_id=metrics.session_id,
                            persona_id=persona.persona_id,
                            persona_name=persona.name,
                            overall_rating=overall_rating,
                            sus_score=sus_score,
                            ces_score=ces_score,
                            nps_rating=nps_rating,
                            sentiment_summary=llm_data.sentiment_summary,
                            what_worked_well=llm_data.what_worked_well,
                            confusing_elements=llm_data.confusing_elements,
                            friction_points=llm_data.friction_points,
                            verbatim_quote=llm_data.verbatim_quote,
                            recommendations=llm_data.recommendations,
                        )
                except Exception as exc:
                    logger.warning(
                        f"Gemini 2.5 feedback synthesis failed: {exc}. Falling back to heuristic feedback."
                    )
        # 5. Fallback Heuristic Generation: Extract confusing elements & friction points
        confusing_elements: list[str] = []
        friction_points: list[str] = []
        what_worked_well: list[str] = []


        for evt in telemetry:
            if evt.action_type == ActionType.RAGE_CLICK:
                elem_name = evt.target_text or evt.target_element or "Interactive badge"
                friction_points.append(
                    f"Rage-clicked on '{elem_name}' at step {evt.step_number} (unresponsive element)"
                )
                confusing_elements.append(f"Misleading button-styled element: '{elem_name}'")
            elif evt.emotion in (Emotion.CONFUSED, Emotion.FRUSTRATED) and evt.target_text:
                confusing_elements.append(f"Ambiguous target: '{evt.target_text}' on {evt.page_title}")

            if evt.emotion in (Emotion.CONFIDENT, Emotion.SATISFIED):
                if evt.action_type == ActionType.COMPLETE_GOAL:
                    what_worked_well.append(f"Clean goal transition to {evt.page_title}")
                elif "dashboard" in evt.page_url.lower():
                    what_worked_well.append("Fast overview in the invoice management console")

        if not what_worked_well:
            if metrics.pages_visited > 1:
                what_worked_well.append("Clean visual aesthetic and modern header navigation")
            else:
                what_worked_well.append("Page loaded quickly without layout shifts")

        # Deduplicate
        confusing_elements = list(dict.fromkeys(confusing_elements))[:4]
        friction_points = list(dict.fromkeys(friction_points))[:4]
        what_worked_well = list(dict.fromkeys(what_worked_well))[:3]

        # 5. Formulate authentic verbatim persona quote
        verbatim_quote = cls._generate_verbatim_quote(
            persona=persona,
            metrics=metrics,
            telemetry=telemetry,
            sus_score=sus_score,
        )

        # 6. Actionable Recommendations
        recommendations: list[str] = []
        if metrics.rage_clicks_total > 0:
            recommendations.append(
                "Remove fake/unclickable interactive styling from badges or connect them to actual sandbox previews."
            )
        if metrics.exit_reason == ExitReason.PATIENCE_EXHAUSTED:
            recommendations.append(
                "Shorten conversion funnel: reduce required form fields or provide single-click guest preview."
            )
        if "pricing" in persona.primary_goal.lower() and metrics.friction_score > 30:
            recommendations.append(
                "Clarify enterprise pricing tiers and provide explicit self-serve trial buttons."
            )
        if not recommendations:
            recommendations.append(
                "Maintain current streamlined onboarding flow; consider adding guided onboarding tooltips."
            )

        # Sentiment summary
        if metrics.task_success and sus_score >= 75:
            sentiment_summary = f"Highly positive. {persona.name} felt confident and reached their goal with minimal friction."
        elif metrics.task_success:
            sentiment_summary = f"Cautiously satisfied. {persona.name} completed the task, but encountered minor cognitive friction."
        else:
            sentiment_summary = f"Dissatisfied. {persona.name} abandoned the journey due to {metrics.exit_reason.value.lower().replace('_', ' ')}."

        return PersonaFeedback(
            feedback_id=f"fb_{uuid.uuid4().hex[:12]}",
            session_id=metrics.session_id,
            persona_id=persona.persona_id,
            persona_name=persona.name,
            overall_rating=overall_rating,
            sus_score=sus_score,
            ces_score=ces_score,
            nps_rating=nps_rating,
            sentiment_summary=sentiment_summary,
            what_worked_well=what_worked_well,
            confusing_elements=confusing_elements,
            friction_points=friction_points,
            verbatim_quote=verbatim_quote,
            recommendations=recommendations,
        )

    @classmethod
    def _generate_verbatim_quote(
        cls,
        persona: Persona,
        metrics: SessionMetrics,
        telemetry: list[TelemetryEvent],
        sus_score: float,
    ) -> str:
        """Compose a first-person review in the persona's authentic voice."""
        if metrics.task_success and sus_score >= 80:
            if persona.technical_skill == TechnicalSkill.HIGH:
                return (
                    f"\"The workflow is snappy and direct. I was able to verify the API docs and inspect the "
                    f"dashboard in under a minute without getting trapped in marketing fluff.\" — {persona.name} ({persona.role})"
                )
            return (
                f"\"I was able to create an account and get straight into the invoice dashboard. "
                f"The navigation is intuitive and didn't make me jump through unnecessary hoops.\" — {persona.name} ({persona.role})"
            )

        if metrics.rage_clicks_total > 0:
            return (
                f"\"I kept clicking the demo button on the homepage expecting an interactive sandbox to open, "
                f"but nothing happened at all. If a badge looks like a button, it should work. That was very frustrating.\" — {persona.name} ({persona.role})"
            )

        if metrics.exit_reason == ExitReason.PATIENCE_EXHAUSTED:
            return (
                f"\"I don't have all day to figure out where things are. I came here looking for '{persona.primary_goal}', "
                f"and after wandering through several pages without a clear CTA, I gave up.\" — {persona.name} ({persona.role})"
            )

        return (
            f"\"The experience was okay, but could be clearer. There were moments where I had to stop and guess "
            f"what the next step was. With some guidance and clearer labels, it would be much better.\" — {persona.name} ({persona.role})"
        )

    @classmethod
    def _generate_gemini_feedback(
        cls,
        persona: Persona,
        metrics: SessionMetrics,
        telemetry: list[TelemetryEvent],
        sus_score: float,
        client: Any,
    ) -> GeminiFeedbackSynthesis | None:
        """Use Gemini 2.5 to synthesize authentic persona post-session critique."""
        from google.genai import types

        model_name = get_gemini_model()

        events_summary = []
        for evt in telemetry:
            events_summary.append(
                f"- Step {evt.step_number}: {evt.action_type.value.upper()} on '{evt.target_text or evt.target_element or evt.page_url}' | Emotion: {evt.emotion.value} | Reason: \"{evt.cognitive_reasoning}\""
            )

        prompt = f"""
You are synthesizing post-testing UX feedback for a web application as the user {persona.name} ({persona.role}, age {persona.age}).
Embody this persona's voice, communication style, technical background ({persona.technical_skill.value}), and biases ({', '.join(persona.biases)}).

SESSION TELEMETRY:
- Goal: {persona.primary_goal}
- Duration: {metrics.duration_seconds}s across {metrics.total_steps} steps
- Task Success: {metrics.task_success}
- Exit Reason: {metrics.exit_reason.value}
- Rage Clicks: {metrics.rage_clicks_total}
- Friction Score: {metrics.friction_score:.1f} / 100
- Usability Score (SUS): {sus_score:.1f} / 100
- Final Sentiment: {metrics.final_sentiment.value}

JOURNEY TIMELINE:
{chr(10).join(events_summary) if events_summary else "  (No interaction events recorded)"}

Generate realistic, authentic persona feedback:
1. 'verbatim_quote': 2-3 sentences in first person directly quoting {persona.name}. Reference specific things encountered. Conclude with '— {persona.name} ({persona.role})'.
2. 'sentiment_summary': Single executive sentence summarizing overall impression.
3. 'what_worked_well': 2-3 bullet items of what was clear or effective.
4. 'confusing_elements': 1-3 bullet items of confusing, ambiguous, or misleading elements encountered.
5. 'friction_points': 1-3 bullet items describing friction or hesitation moments.
6. 'recommendations': 2-3 specific, actionable recommendations from this persona's perspective.
""".strip()

        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiFeedbackSynthesis,
                temperature=0.3,
            ),
        )

        if not resp.text:
            return None

        return GeminiFeedbackSynthesis.model_validate_json(resp.text)

