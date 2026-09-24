"""UAT Synthesis & Executive Reporting Engine for Simulacra UAT.

Aggregates multi-agent telemetry, UX surveys, and behavioral friction into
executive markdown summaries, JSON contracts, and Excel audit workbooks.
"""

import io
import uuid
from datetime import datetime, timezone
from typing import Any
import pandas as pd

from src.simulacra.models import (
    CampaignMission,
    CampaignSummary,
    PersonaFeedback,
    SessionMetrics,
    TelemetryEvent,
    UATReport,
)


class ReportGenerator:
    """Generates cross-session UAT synthesis reports and exports."""

    @classmethod
    def generate_report(
        cls,
        campaign_id: str,
        mission: CampaignMission,
        sessions: list[SessionMetrics],
        feedbacks: list[PersonaFeedback],
        all_telemetry: list[TelemetryEvent],
    ) -> tuple[UATReport, str]:
        """Produce structured UATReport model and full GitHub-flavored Markdown document."""
        total_sessions = len(sessions)
        if total_sessions == 0:
            summary = CampaignSummary(
                campaign_id=campaign_id,
                title=mission.title,
                target_url=mission.target_url,
                created_at=datetime.now(timezone.utc).isoformat(),
                total_sessions=0,
                successful_sessions=0,
                success_rate_percent=0.0,
                average_friction_score=0.0,
                average_sus_score=0.0,
                total_rage_clicks=0,
                status="NO_DATA",
            )
            report = UATReport(
                report_id=f"rep_{uuid.uuid4().hex[:12]}",
                campaign_id=campaign_id,
                title=f"UAT Synthesis Report: {mission.title}",
                generated_at=datetime.now(timezone.utc).isoformat(),
                campaign_summary=summary,
                top_blockers=[],
                friction_hotspots=[],
                persona_cohort_breakdown=[],
                actionable_recommendations=[],
                executive_summary="No simulation sessions were executed for this campaign.",
            )
            return report, "# UAT Synthesis Report\n\nNo simulation sessions recorded."

        successful_sessions = sum(1 for s in sessions if s.task_success)
        success_rate = round((successful_sessions / total_sessions) * 100.0, 1)
        avg_friction = round(sum(s.friction_score for s in sessions) / total_sessions, 1)
        avg_sus = round(sum(fb.sus_score for fb in feedbacks) / len(feedbacks), 1) if feedbacks else 0.0
        total_rage = sum(s.rage_clicks_total for s in sessions)

        summary = CampaignSummary(
            campaign_id=campaign_id,
            title=mission.title,
            target_url=mission.target_url,
            created_at=datetime.now(timezone.utc).isoformat(),
            total_sessions=total_sessions,
            successful_sessions=successful_sessions,
            success_rate_percent=success_rate,
            average_friction_score=avg_friction,
            average_sus_score=avg_sus,
            total_rage_clicks=total_rage,
            status="COMPLETED",
        )

        # 1. Identify Top Blockers & Friction Hotspots
        friction_hotspots: list[dict[str, Any]] = []
        rage_events = [e for e in all_telemetry if e.rage_click_count > 0]
        if rage_events:
            friction_hotspots.append({
                "page": rage_events[0].page_url,
                "element": rage_events[0].target_text or rage_events[0].target_element or "Interactive badge",
                "severity": "CRITICAL",
                "occurrences": len(rage_events),
                "description": "Users repeatedly clicked unclickable element expecting sandbox/action.",
            })

        hesitant_events = [e for e in all_telemetry if e.hesitation_ms > 1000]
        if hesitant_events:
            friction_hotspots.append({
                "page": hesitant_events[0].page_url,
                "element": hesitant_events[0].target_text or hesitant_events[0].page_title,
                "severity": "MEDIUM",
                "occurrences": len(hesitant_events),
                "description": "Noticeable reading hesitation; unclear messaging or complex form layout.",
            })

        # 2. Persona Cohort Breakdown
        cohort_breakdown: list[dict[str, Any]] = []
        for s in sessions:
            fb = next((f for f in feedbacks if f.session_id == s.session_id), None)
            cohort_breakdown.append({
                "persona_name": s.persona_name,
                "task_success": s.task_success,
                "friction_score": s.friction_score,
                "sus_score": fb.sus_score if fb else 0.0,
                "duration_seconds": s.duration_seconds,
                "exit_reason": s.exit_reason.value,
                "rage_clicks": s.rage_clicks_total,
            })

        # 3. Actionable Recommendations
        recs: list[dict[str, Any]] = []
        if total_rage > 0:
            recs.append({
                "priority": "P0 - Immediate",
                "area": "Homepage / Interactive Badges",
                "action": "Connect pseudo-button demo badges to real sandbox modals, or style as non-interactive text.",
            })
        if success_rate < 80.0:
            recs.append({
                "priority": "P1 - High",
                "area": "Conversion Funnel",
                "action": "Streamline navigation paths; ensure prominent primary CTAs are visible above the fold on all device viewports.",
            })
        recs.append({
            "priority": "P2 - Medium",
            "area": "Pricing Transparency",
            "action": "Add explicit self-serve trial buttons on Pro/Growth pricing tiers to prevent enterprise bounce.",
        })

        # Executive narrative
        exec_summary = (
            f"Simulated UAT testing across {total_sessions} diverse synthetic personas achieved a "
            f"{success_rate}% task success rate with an average SUS score of {avg_sus}/100. "
            f"Synthetic agents logged {total_rage} rage-click incidents and an average friction index of "
            f"{avg_friction}/100. Key friction was concentrated around misleading interactive badges and "
            f"multi-step signup form hesitations."
        )

        report = UATReport(
            report_id=f"rep_{uuid.uuid4().hex[:12]}",
            campaign_id=campaign_id,
            title=f"Simulacra UAT Synthesis: {mission.title}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            campaign_summary=summary,
            top_blockers=friction_hotspots,
            friction_hotspots=friction_hotspots,
            persona_cohort_breakdown=cohort_breakdown,
            actionable_recommendations=recs,
            executive_summary=exec_summary,
        )

        # Build Markdown Document
        md = cls._build_markdown(report, sessions, feedbacks)
        return report, md

    @classmethod
    def _build_markdown(
        cls,
        report: UATReport,
        sessions: list[SessionMetrics],
        feedbacks: list[PersonaFeedback],
    ) -> str:
        """Render high-impact executive markdown artifact."""
        summary = report.campaign_summary
        lines = [
            f"# 🧪 Simulacra UAT Synthesis Report",
            f"**Campaign:** {report.title}  ",
            f"**Target URL:** `{summary.target_url}`  ",
            f"**Generated:** {report.generated_at}  ",
            "",
            "## 📌 Executive Summary",
            report.executive_summary,
            "",
            "## 📊 Campaign Telemetry Scorecard",
            "| Metric | Result | Target Benchmark | Status |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Task Success Rate** | **{summary.success_rate_percent}%** ({summary.successful_sessions}/{summary.total_sessions}) | ≥ 80.0% | {'✅ Pass' if summary.success_rate_percent >= 80 else '⚠️ Warning'} |",
            f"| **Average Usability (SUS)** | **{summary.average_sus_score} / 100** | ≥ 68.0 (Grade B) | {'✅ Good' if summary.average_sus_score >= 68 else '❌ Poor'} |",
            f"| **Average Friction Score** | **{summary.average_friction_score} / 100** | ≤ 30.0 | {'✅ Low' if summary.average_friction_score <= 30 else '⚠️ High'} |",
            f"| **Total Rage Clicks** | **{summary.total_rage_clicks}** | 0 | {'✅ Zero' if summary.total_rage_clicks == 0 else '🚨 Detected'} |",
            "",
            "## 👥 Persona Cohort Performance",
            "| Persona | Role | Success | Duration | Friction | SUS Score | Exit Reason |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
        ]

        for s in sessions:
            fb = next((f for f in feedbacks if f.session_id == s.session_id), None)
            sus = f"{fb.sus_score:.1f}" if fb else "N/A"
            icon = "✅" if s.task_success else "❌"
            lines.append(
                f"| **{s.persona_name}** | {s.persona_id} | {icon} | {s.duration_seconds}s | {s.friction_score:.1f} | {sus} | `{s.exit_reason.value}` |"
            )

        lines.extend([
            "",
            "## ⚠️ Friction Hotspots & Blockers",
        ])
        if report.friction_hotspots:
            for hotspot in report.friction_hotspots:
                lines.append(f"- **[{hotspot.get('severity')}] {hotspot.get('element')}** on `{hotspot.get('page')}`: {hotspot.get('description')} ({hotspot.get('occurrences')} incident(s))")
        else:
            lines.append("- No critical friction hotspots or rage-click loops detected.")

        lines.extend([
            "",
            "## 💬 Persona Verbatim Quotes",
        ])
        for fb in feedbacks:
            lines.append(f"> {fb.verbatim_quote}")
            lines.append("")

        lines.extend([
            "## 🛠️ Prioritized Actionable Recommendations",
            "| Priority | UX Surface Area | Recommended Action |",
            "| :--- | :--- | :--- |",
        ])
        for r in report.actionable_recommendations:
            lines.append(f"| **{r.get('priority')}** | {r.get('area')} | {r.get('action')} |")

        lines.append("\n---  \n*Report generated deterministically by Simulacra Autonomous UAT Platform.*")
        return "\n".join(lines)

    @classmethod
    def export_excel_workbook(
        cls,
        report: UATReport,
        sessions: list[SessionMetrics],
        feedbacks: list[PersonaFeedback],
        telemetry: list[TelemetryEvent],
        quantix_forms: list[Any] | None = None,
        **kwargs: Any,
    ) -> bytes:
        """Generate structured multi-tab Excel workbook for QA and product teams."""
        forms_to_export = quantix_forms or kwargs.get("quantix_feedbacks") or []
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Sheet 1: Campaign Summary
            summary_data = [
                {"Metric": "Campaign Title", "Value": report.title},
                {"Metric": "Target URL", "Value": report.campaign_summary.target_url},
                {"Metric": "Execution Date", "Value": report.generated_at},
                {"Metric": "Total Synthetic Users", "Value": report.campaign_summary.total_sessions},
                {"Metric": "Successful Runs", "Value": report.campaign_summary.successful_sessions},
                {"Metric": "Success Rate (%)", "Value": report.campaign_summary.success_rate_percent},
                {"Metric": "Average SUS Score", "Value": report.campaign_summary.average_sus_score},
                {"Metric": "Average Friction Score", "Value": report.campaign_summary.average_friction_score},
                {"Metric": "Total Rage Clicks", "Value": report.campaign_summary.total_rage_clicks},
            ]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            # Sheet 2: Sessions
            if sessions:
                sess_df = pd.DataFrame([s.model_dump() for s in sessions])
                sess_df.to_excel(writer, sheet_name="Sessions", index=False)

            # Sheet 3: Persona Feedback
            if feedbacks:
                fb_df = pd.DataFrame([fb.model_dump() for fb in feedbacks])
                fb_df.to_excel(writer, sheet_name="Feedback", index=False)

            # Sheet 4: Telemetry Events
            if telemetry:
                tel_df = pd.DataFrame([e.model_dump() for e in telemetry])
                tel_df.to_excel(writer, sheet_name="Telemetry", index=False)

            # Sheet 5: Detailed Google Form Feedback
            if forms_to_export:
                gform_rows = []
                for qf in forms_to_export:
                    row = qf if isinstance(qf, dict) else qf.model_dump()
                    # Flatten list values for Excel readability
                    flat_row = {}
                    for k, v in row.items():
                        flat_row[k] = ", ".join(v) if isinstance(v, list) else v
                    gform_rows.append(flat_row)
                gform_df = pd.DataFrame(gform_rows)
                gform_df.to_excel(writer, sheet_name="Google Form Feedback", index=False)

        return output.getvalue()
