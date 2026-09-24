"""Campaign Runner & Multi-Agent Orchestrator for Simulacra UAT."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src.simulacra.browser_agent import SimulatedUserAgent
from src.simulacra.database import (
    DEFAULT_SIMULACRA_DB_PATH,
    initialize_database,
    save_campaign,
    save_feedback,
    save_persona,
    save_quantix_feedback,
    save_session,
    save_telemetry_event,
    save_uat_report,
)
from src.simulacra.feedback import FeedbackEngine
from src.simulacra.mock_app import MockAppServer
from src.simulacra.quantix_feedback_form import generate_quantix_feedback
from src.simulacra.models import (
    CampaignMission,
    Emotion,
    ExitReason,
    Persona,
    PersonaFeedback,
    SessionMetrics,
    TelemetryEvent,
    UATReport,
)
from src.simulacra.reporting import ReportGenerator


class SimulationRunner:
    """Orchestrates multi-persona UAT simulation campaigns."""

    def __init__(self, database_path: Path = DEFAULT_SIMULACRA_DB_PATH) -> None:
        self.database_path = database_path
        initialize_database(self.database_path)

    def run_campaign(
        self,
        mission: CampaignMission,
        personas: list[Persona],
        on_step_progress: Callable[[Persona, TelemetryEvent, int, int], None] | None = None,
        on_session_complete: Callable[[SessionMetrics, PersonaFeedback], None] | None = None,
    ) -> tuple[UATReport, str, list[SessionMetrics], list[PersonaFeedback], list[TelemetryEvent]]:
        """Execute full synthetic UAT campaign across provided personas."""
        campaign_id = mission.mission_id or f"camp_{uuid.uuid4().hex[:10]}"
        created_at = datetime.now(timezone.utc).isoformat()

        # If target URL is pointing to local demo port, ensure MockAppServer is running
        if "127.0.0.1:8585" in mission.target_url or "localhost:8585" in mission.target_url:
            MockAppServer.get_or_start(port=8585)

        # Save initial campaign state
        save_campaign(
            campaign_id=campaign_id,
            title=mission.title,
            target_url=mission.target_url,
            primary_goal=mission.primary_goal,
            created_at=created_at,
            status="RUNNING",
            config=mission,
            database_path=self.database_path,
        )

        all_sessions: list[SessionMetrics] = []
        all_feedbacks: list[PersonaFeedback] = []
        all_telemetry: list[TelemetryEvent] = []

        total_personas = len(personas)

        for idx, persona in enumerate(personas, start=1):
            # Save persona definition
            save_persona(persona, database_path=self.database_path)

            def event_callback(evt: TelemetryEvent) -> None:
                # Save each event to datastore immediately (streaming persistence)
                save_telemetry_event(evt, database_path=self.database_path)
                if on_step_progress:
                    on_step_progress(persona, evt, idx, total_personas)

            # Execute agent session
            agent = SimulatedUserAgent(
                persona=persona,
                mission=mission,
                campaign_id=campaign_id,
                on_event=event_callback,
            )

            # Persist initial session record to satisfy foreign key constraint for streaming events
            initial_metrics = SessionMetrics(
                session_id=agent.session_id,
                campaign_id=campaign_id,
                persona_id=persona.persona_id,
                persona_name=persona.name,
                started_at=datetime.now(timezone.utc).isoformat(),
                exit_reason=ExitReason.MAX_STEPS_REACHED,
                final_sentiment=Emotion.NEUTRAL,
            )
            save_session(initial_metrics, database_path=self.database_path)

            metrics, events = agent.run_session()
            all_sessions.append(metrics)
            all_telemetry.extend(events)
            save_session(metrics, database_path=self.database_path)

            # Generate and persist synthetic feedback
            feedback = FeedbackEngine.generate_feedback(
                persona=persona,
                metrics=metrics,
                telemetry=events,
            )
            all_feedbacks.append(feedback)
            save_feedback(feedback, database_path=self.database_path)

            # Generate and persist detailed Quantix Google Form survey
            quantix_form = generate_quantix_feedback(persona, metrics, events)
            save_quantix_feedback(quantix_form, database_path=self.database_path)

            if on_session_complete:
                on_session_complete(metrics, feedback)

        # Generate synthesis report
        report, report_md = ReportGenerator.generate_report(
            campaign_id=campaign_id,
            mission=mission,
            sessions=all_sessions,
            feedbacks=all_feedbacks,
            all_telemetry=all_telemetry,
        )

        # Save report and update campaign status to COMPLETED
        save_uat_report(report, report_md, database_path=self.database_path)

        save_campaign(
            campaign_id=campaign_id,
            title=mission.title,
            target_url=mission.target_url,
            primary_goal=mission.primary_goal,
            created_at=created_at,
            status="COMPLETED",
            config=mission,
            total_sessions=report.campaign_summary.total_sessions,
            successful_sessions=report.campaign_summary.successful_sessions,
            success_rate_percent=report.campaign_summary.success_rate_percent,
            average_friction_score=report.campaign_summary.average_friction_score,
            average_sus_score=report.campaign_summary.average_sus_score,
            total_rage_clicks=report.campaign_summary.total_rage_clicks,
            database_path=self.database_path,
        )

        return report, report_md, all_sessions, all_feedbacks, all_telemetry
