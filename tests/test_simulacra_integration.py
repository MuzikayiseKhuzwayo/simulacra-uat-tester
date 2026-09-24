"""End-to-end integration test for Simulacra Playwright browser simulation."""

from pathlib import Path
import pytest

from src.simulacra.database import (
    get_campaign,
    get_feedback_by_session,
    get_session_telemetry,
    get_uat_report,
    initialize_database,
    list_sessions_by_campaign,
)
from src.simulacra.mock_app import MockAppServer
from src.simulacra.models import CampaignMission
from src.simulacra.persona import get_preset_personas
from src.simulacra.runner import SimulationRunner


@pytest.fixture(scope="module")
def mock_server():
    server = MockAppServer(port=8589)
    server.start()
    yield server
    server.stop()


def test_e2e_simulated_uat_run(mock_server: MockAppServer, tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "simulacra_e2e.db"
    initialize_database(db_path)

    # Use 2 archetypes: Sarah (prone to friction/rage-click) & Marcus (direct converter)
    cohort = get_preset_personas()[:2]
    mission = CampaignMission(
        mission_id="camp_e2e_verified",
        title="E2E Integration Campaign",
        target_url=f"{mock_server.base_url}/",
        primary_goal="Start Free 14-Day Trial and explore app",
        max_steps=8,
        headless=True,
        capture_screenshots=True,
    )

    runner = SimulationRunner(database_path=db_path)

    report, report_md, sessions, feedbacks, all_telemetry = runner.run_campaign(
        mission=mission,
        personas=cohort,
    )

    # 1. Assertions on Campaign
    campaign_row = get_campaign("camp_e2e_verified", database_path=db_path)
    assert campaign_row is not None
    assert campaign_row["status"] == "COMPLETED"
    assert campaign_row["total_sessions"] == 2

    # 2. Assertions on Sessions
    db_sessions = list_sessions_by_campaign("camp_e2e_verified", database_path=db_path)
    assert len(db_sessions) == 2
    for s in db_sessions:
        assert s.duration_seconds > 0.0
        assert s.total_steps > 0
        assert s.pages_visited >= 1

    # 3. Assertions on Telemetry Events
    for s in db_sessions:
        events = get_session_telemetry(s.session_id, database_path=db_path)
        assert len(events) >= 1
        assert any(e.action_type.value in ("click", "complete_goal", "rage_click", "navigate", "scroll_down") for e in events)
        assert all(len(e.cognitive_reasoning) > 0 for e in events)

    # 4. Assertions on Feedback
    for s in db_sessions:
        fb = get_feedback_by_session(s.session_id, database_path=db_path)
        assert fb is not None
        assert 0.0 <= fb.sus_score <= 100.0
        assert len(fb.verbatim_quote) > 10

    # 5. Assertions on UAT Report
    saved_report, saved_md = get_uat_report("camp_e2e_verified", database_path=db_path)
    assert saved_report is not None
    assert saved_md is not None
    assert "Simulacra UAT Synthesis Report" in saved_md
