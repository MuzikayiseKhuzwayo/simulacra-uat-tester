"""CLI entrypoint for running Simulacra UAT simulations from terminal or CI/CD."""

import argparse
import sys
import uuid
from pathlib import Path

from src.simulacra.mock_app import MockAppServer
from src.simulacra.models import CampaignMission
from src.simulacra.persona import generate_cohort, get_preset_personas
from src.simulacra.runner import SimulationRunner


def main() -> None:
    """Parse arguments and execute simulation campaign."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(
        description="Simulacra UAT — Autonomous Persona-Driven UAT Simulation Platform"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8585",
        help="Target application URL to test (default: http://127.0.0.1:8585)",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="Explore features, test trial registration, and verify invoice workflow",
        help="Primary mission goal for simulated personas",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="CLI Automated UAT Run",
        help="Title of the testing campaign",
    )
    parser.add_argument(
        "--personas",
        type=int,
        default=3,
        help="Number of synthetic personas to simulate (default: 3)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in visible mode (default is headless)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=15,
        help="Maximum steps per persona session",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🤖 SIMULACRA UAT — AUTONOMOUS USER SIMULATION PLATFORM")
    print("=" * 60)

    # Start mock server if testing against local default
    if "127.0.0.1:8585" in args.url or "localhost:8585" in args.url:
        print("⚡ Ensuring local demo application is active on http://127.0.0.1:8585...")
        MockAppServer.get_or_start(port=8585)

    cohort = generate_cohort(count=args.personas, custom_goal=args.goal)
    print(f"👥 Generated cohort of {len(cohort)} synthetic personas:")
    for p in cohort:
        print(f"   • {p.name} ({p.role}) — Tech: {p.technical_skill.value}, Patience: {p.patience.value}")

    mission = CampaignMission(
        mission_id=f"camp_{uuid.uuid4().hex[:10]}",
        title=args.title,
        target_url=args.url,
        primary_goal=args.goal,
        max_steps=args.max_steps,
        headless=not args.headed,
        capture_screenshots=True,
    )

    print(f"\n🚀 Launching simulation against {args.url} (Headless: {mission.headless})...\n")

    runner = SimulationRunner()

    def on_step(persona, evt, current, total):
        icon = "⚡" if evt.action_type == "rage_click" else "👉"
        print(f"[{current}/{total}] {persona.name} {icon} [{evt.action_type.value}] {evt.page_title or evt.page_url}")
        print(f"      Thought: {evt.cognitive_reasoning}")

    def on_complete(metrics, feedback):
        status_sym = "✅ PASSED" if metrics.task_success else "❌ FAILED"
        print(f"\n✨ Session Completed: {metrics.persona_name} -> {status_sym}")
        print(f"   Duration: {metrics.duration_seconds}s | Friction: {metrics.friction_score}/100 | SUS: {feedback.sus_score}/100")
        print(f"   Verbatim: {feedback.verbatim_quote}\n")

    report, report_md, sessions, feedbacks, _ = runner.run_campaign(
        mission=mission,
        personas=cohort,
        on_step_progress=on_step,
        on_session_complete=on_complete,
    )

    print("=" * 60)
    print(f"📊 CAMPAIGN RESULTS: {report.title}")
    print("=" * 60)
    print(f"Success Rate:    {report.campaign_summary.success_rate_percent}% ({report.campaign_summary.successful_sessions}/{report.campaign_summary.total_sessions})")
    print(f"Avg Friction:    {report.campaign_summary.average_friction_score} / 100")
    print(f"Avg SUS Score:   {report.campaign_summary.average_sus_score} / 100")
    print(f"Rage Clicks:     {report.campaign_summary.total_rage_clicks}")
    print("\nExecutive Summary:")
    print(report.executive_summary)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
