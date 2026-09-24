"""Simulacra UAT — Autonomous Persona-Driven User Simulation & Testing Platform.

Combines Playwright autonomous synthetic user agents, cognitive journey planning,
high-resolution telemetry, post-session UX surveys, and executive synthesis reports.
"""

import json
from pathlib import Path
import streamlit as st
from pydantic import ValidationError

import src.simulacra as sim
from src.agent_service import AgentServiceError
from src.excel_export import create_test_pack_excel
from src.history_repository import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    complete_execution,
    fail_execution,
    get_execution_json,
    list_executions,
    start_execution,
)
from src.schemas import (
    AcceptanceCriterion,
    RequirementInput,
    TestPack,
)
from src.simulacra.mock_app import MockAppServer
from src.simulacra.models import CampaignMission
from src.simulacra.persona import generate_cohort, get_preset_personas
from src.simulacra.reporting import ReportGenerator
from src.simulacra.runner import SimulationRunner
from src.workflow import (
    WorkflowBlockedError,
    run_uat_workflow,
)

st.set_page_config(
    page_title="Simulacra UAT Platform",
    page_icon="🤖",
    layout="wide",
)


# -----------------------------------------------------------------------------
# Helper Functions for Legacy TestPack Designer
# -----------------------------------------------------------------------------

def parse_acceptance_criteria(raw_text: str) -> list[AcceptanceCriterion]:
    criteria: list[AcceptanceCriterion] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if "|" not in line:
            raise ValueError(
                f"Acceptance criterion line {line_number} must use: AC-ID | description"
            )
        criterion_id, description = line.split("|", maxsplit=1)
        criteria.append(
            AcceptanceCriterion(
                criterion_id=criterion_id.strip(),
                description=description.strip(),
            )
        )
    return criteria


def parse_list(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


# -----------------------------------------------------------------------------
# Main Application Header & Tabs
# -----------------------------------------------------------------------------

st.title("🤖 Simulacra UAT — Autonomous User Testing Platform")
st.caption(
    "Simulate cohorts of diverse synthetic customer personas exploring your web application, "
    "evaluating cognitive friction, capturing fine-grained telemetry, and generating executive UX audits."
)

tab_studio, tab_reports, tab_sessions, tab_surveys, tab_designer = st.tabs(
    [
        "🚀 Simulation Studio",
        "📊 Executive UAT Reports",
        "🕵️ User Sessions & Telemetry",
        "💬 Persona UX Surveys",
        "📝 TestPack Design Agent",
    ]
)


# -----------------------------------------------------------------------------
# TAB 1: Simulation Studio
# -----------------------------------------------------------------------------

with tab_studio:
    st.subheader("Configure & Launch Synthetic User Simulation")

    # Local Mock App Controller
    col_demo1, col_demo2 = st.columns([3, 1])
    with col_demo1:
        st.info(
            "💡 **Demo Target Available:** Test against the built-in multi-page AcmeCloud SaaS application "
            "(`http://127.0.0.1:8585`), featuring realistic friction points, unclickable demo badges, and multi-step workflows."
        )
    with col_demo2:
        if st.button("⚡ Start Built-in Demo App", use_container_width=True):
            server = MockAppServer.get_or_start(port=8585)
            st.success(f"Demo application running at {server.base_url}")

    with st.form("simulation_config_form"):
        col_url, col_title = st.columns([2, 1])
        with col_url:
            target_url = st.text_input(
                "Target Application URL",
                value="http://127.0.0.1:8585",
                help="URL of the web application under test (local or public web)",
            )
        with col_title:
            campaign_title = st.text_input(
                "Campaign Title",
                value="AcmeCloud Onboarding & Trial Simulation",
            )

        mission_goal = st.text_area(
            "Primary User Goal / Mission",
            value="Explore features, inspect pricing plans, sign up for a free trial, and reach the dashboard to issue an invoice.",
            rows=2,
        )

        st.markdown("#### Persona Cohort Configuration")
        persona_mode = st.radio(
            "Cohort Generation Mode",
            ["Preset Archetypes", "Algorithmic Cohort Generator"],
            horizontal=True,
        )

        preset_options = get_preset_personas()
        preset_names = [f"{p.name} ({p.role}) - Tech: {p.technical_skill.value}, Patience: {p.patience.value}" for p in preset_options]

        if persona_mode == "Preset Archetypes":
            selected_indices = st.multiselect(
                "Select Archetypes to Simulate",
                options=list(range(len(preset_names))),
                format_func=lambda i: preset_names[i],
                default=[0, 1, 2],
            )
            cohort_size = len(selected_indices)
        else:
            cohort_size = st.slider("Cohort Size (Number of synthetic users)", min_value=1, max_value=20, value=5)
            selected_indices = []

        col_opt1, col_opt2, col_opt3 = st.columns(3)
        with col_opt1:
            max_steps = st.number_input("Max Steps per Persona", min_value=3, max_value=40, value=12)
        with col_opt2:
            headless_mode = st.checkbox("Headless Browser Mode", value=True)
        with col_opt3:
            capture_shots = st.checkbox("Capture Milestone Screenshots", value=True)

        submitted = st.form_submit_button("🚀 Launch Synthetic UAT Simulation", type="primary", use_container_width=True)

    if submitted:
        if not target_url.strip():
            st.error("Please provide a valid Target Application URL.")
        else:
            # Build cohort
            if persona_mode == "Preset Archetypes":
                if not selected_indices:
                    st.warning("Please select at least one preset archetype.")
                    st.stop()
                cohort = [preset_options[i].model_copy(update={"primary_goal": mission_goal}) for i in selected_indices]
            else:
                cohort = generate_cohort(count=cohort_size, custom_goal=mission_goal)

            mission = CampaignMission(
                mission_id=f"camp_{target_url.replace(':', '_').replace('/', '_')[:15]}",
                title=campaign_title,
                target_url=target_url,
                primary_goal=mission_goal,
                max_steps=int(max_steps),
                headless=headless_mode,
                capture_screenshots=capture_shots,
            )

            progress_bar = st.progress(0.0)
            status_box = st.empty()
            event_log = st.empty()
            stream_messages: list[str] = []

            def on_step(persona, evt, current, total):
                progress_bar.progress(round((current - 1 + (evt.step_number / max_steps)) / total, 2))
                status_box.markdown(
                    f"**Simulating:** `{persona.name}` ({persona.role}) | Step {evt.step_number}: `{evt.action_type.value}`"
                )
                stream_messages.append(
                    f"**[{persona.name}]** `{evt.action_type.value}` on *{evt.page_title or evt.page_url}* — "
                    f"💭 *\"{evt.cognitive_reasoning}\"* (Emotion: `{evt.emotion.value}`, Conf: `{evt.confidence:.2f}`)"
                )
                with event_log.container():
                    for msg in stream_messages[-5:]:
                        st.markdown(msg)

            with st.spinner("Synthetic agents are navigating, evaluating UX, and submitting surveys..."):
                runner = SimulationRunner()
                report, report_md, sessions, feedbacks, all_telemetry = runner.run_campaign(
                    mission=mission,
                    personas=cohort,
                    on_step_progress=on_step,
                )

            progress_bar.progress(1.0)
            st.success(f"🎉 Simulation Campaign Completed! {len(sessions)} sessions executed.")
            st.session_state["active_campaign_id"] = report.campaign_id
            st.balloons()


# -----------------------------------------------------------------------------
# TAB 2: Executive UAT Reports
# -----------------------------------------------------------------------------

with tab_reports:
    st.subheader("Campaign Analytics & Executive UAT Synthesis")
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No simulation campaigns recorded yet. Launch a simulation in the Simulation Studio.")
    else:
        camp_options = {c["campaign_id"]: f"{c['title']} ({c['created_at'][:19]})" for c in campaigns}
        default_camp_id = st.session_state.get("active_campaign_id", campaigns[0]["campaign_id"])
        if default_camp_id not in camp_options:
            default_camp_id = campaigns[0]["campaign_id"]

        selected_camp_id = st.selectbox(
            "Select Campaign to Inspect",
            options=list(camp_options.keys()),
            format_func=lambda cid: camp_options[cid],
            index=list(camp_options.keys()).index(default_camp_id),
        )

        camp_data = sim.get_campaign(selected_camp_id)
        report_obj, report_markdown = sim.get_uat_report(selected_camp_id)
        camp_sessions = sim.list_sessions_by_campaign(selected_camp_id)
        camp_feedbacks = sim.list_feedback_by_campaign(selected_camp_id)

        # KPI Metric Cards
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        success_rate = camp_data.get("success_rate_percent", 0.0)
        col_m1.metric("Success Rate", f"{success_rate:.1f}%", f"{camp_data.get('successful_sessions', 0)}/{camp_data.get('total_sessions', 0)} completed")
        col_m2.metric("Avg Usability (SUS)", f"{camp_data.get('average_sus_score', 0.0):.1f} / 100")
        col_m3.metric("Friction Index", f"{camp_data.get('average_friction_score', 0.0):.1f} / 100")
        col_m4.metric("Rage Clicks", f"{camp_data.get('total_rage_clicks', 0)}")
        col_m5.metric("Total Personas", f"{camp_data.get('total_sessions', 0)}")

        st.divider()

        # Action Bar: Downloads
        col_d1, col_d2, col_d3 = st.columns(3)
        if report_markdown:
            col_d1.download_button(
                "📥 Download Executive Report (Markdown)",
                data=report_markdown,
                file_name=f"UAT_Report_{selected_camp_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        if report_obj:
            all_tel: list[sim.TelemetryEvent] = []
            for s in camp_sessions:
                all_tel.extend(sim.get_session_telemetry(s.session_id))
            excel_bytes = ReportGenerator.export_excel_workbook(
                report=report_obj,
                sessions=camp_sessions,
                feedbacks=camp_feedbacks,
                telemetry=all_tel,
            )
            col_d2.download_button(
                "📥 Download UX Audit Workbook (Excel)",
                data=excel_bytes,
                file_name=f"UAT_Audit_{selected_camp_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            col_d3.download_button(
                "📥 Export Full Telemetry (JSON)",
                data=report_obj.model_dump_json(indent=2),
                file_name=f"UAT_Data_{selected_camp_id}.json",
                mime="application/json",
                use_container_width=True,
            )

        # Markdown report rendering
        if report_markdown:
            with st.expander("📄 View Executive Markdown Document", expanded=True):
                st.markdown(report_markdown)


# -----------------------------------------------------------------------------
# TAB 3: User Sessions & Telemetry
# -----------------------------------------------------------------------------

with tab_sessions:
    st.subheader("Synthetic User Sessions & Telemetry Timeline")
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No recorded sessions found.")
    else:
        sel_campaign_for_sess = st.selectbox(
            "Campaign",
            options=[c["campaign_id"] for c in campaigns],
            format_func=lambda cid: next((c["title"] for c in campaigns if c["campaign_id"] == cid), cid),
            key="sess_camp_select",
        )
        sessions = sim.list_sessions_by_campaign(sel_campaign_for_sess)

        if not sessions:
            st.info("No sessions in this campaign.")
        else:
            sess_dict = {s.session_id: f"{s.persona_name} — {'✅ Passed' if s.task_success else '❌ Abandoned'} ({s.duration_seconds}s, {s.total_steps} steps)" for s in sessions}
            selected_sess_id = st.selectbox(
                "Select Persona Session",
                options=list(sess_dict.keys()),
                format_func=lambda sid: sess_dict[sid],
            )

            current_session = next(s for s in sessions if s.session_id == selected_sess_id)
            telemetry_events = sim.get_session_telemetry(selected_sess_id)

            # Session metric overview
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Friction Score", f"{current_session.friction_score:.1f} / 100")
            c2.metric("Total Steps", f"{current_session.total_steps}")
            c3.metric("Rage Clicks", f"{current_session.rage_clicks_total}")
            c4.metric("Exit Reason", f"{current_session.exit_reason.value}")

            st.markdown("#### Chronological Cognitive Stream")
            for evt in telemetry_events:
                with st.container():
                    st.markdown(
                        f"**Step {evt.step_number}:** `{evt.action_type.value.upper()}` "
                        f"on `{evt.target_element or evt.page_url}` &nbsp;&nbsp; "
                        f"*(Emotion: **{evt.emotion.value}**, Confidence: **{evt.confidence:.2f}**, Hesitation: **{evt.hesitation_ms}ms**)*"
                    )
                    st.markdown(f"> 🧠 **Inner Monologue:** *\"{evt.cognitive_reasoning}\"*")

                    if evt.screenshot_path and Path(evt.screenshot_path).exists():
                        st.image(evt.screenshot_path, caption=f"Step {evt.step_number} Snapshot: {evt.page_title}", width=600)

                    st.divider()


# -----------------------------------------------------------------------------
# TAB 4: Persona UX Surveys
# -----------------------------------------------------------------------------

with tab_surveys:
    st.subheader("Structured Persona UX Feedback & Surveys")
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No feedback records available.")
    else:
        sel_campaign_for_fb = st.selectbox(
            "Campaign",
            options=[c["campaign_id"] for c in campaigns],
            format_func=lambda cid: next((c["title"] for c in campaigns if c["campaign_id"] == cid), cid),
            key="fb_camp_select",
        )
        feedbacks = sim.list_feedback_by_campaign(sel_campaign_for_fb)

        if not feedbacks:
            st.info("No feedback surveys recorded for this campaign.")
        else:
            for fb in feedbacks:
                with st.expander(f"👤 {fb.persona_name} — Usability Score: {fb.sus_score:.1f}/100 ({'⭐' * fb.overall_rating})", expanded=True):
                    st.markdown(f"### 💬 Verbatim Quote")
                    st.info(f"{fb.verbatim_quote}")

                    col_f1, col_f2, col_f3 = st.columns(3)
                    col_f1.metric("SUS Score", f"{fb.sus_score:.1f}/100")
                    col_f2.metric("Customer Effort (CES)", f"{fb.ces_score}/7")
                    col_f3.metric("Net Promoter (NPS)", f"{fb.nps_rating}/10")

                    st.markdown(f"**Sentiment Overview:** {fb.sentiment_summary}")

                    if fb.what_worked_well:
                        st.markdown("**✅ What Worked Well:**")
                        for item in fb.what_worked_well:
                            st.markdown(f"- {item}")

                    if fb.confusing_elements:
                        st.markdown("**⚠️ Confusing Elements:**")
                        for item in fb.confusing_elements:
                            st.markdown(f"- {item}")

                    if fb.friction_points:
                        st.markdown("**🚨 Friction Points:**")
                        for item in fb.friction_points:
                            st.markdown(f"- {item}")

                    if fb.recommendations:
                        st.markdown("**💡 Recommendations from this Persona:**")
                        for item in fb.recommendations:
                            st.markdown(f"- {item}")


# -----------------------------------------------------------------------------
# TAB 5: Legacy UAT TestPack Design Agent (Preserved)
# -----------------------------------------------------------------------------

with tab_designer:
    st.subheader("Deterministic Requirement Analysis & Test Case Design")
    st.caption("Analyzes requirements and generates traceable UAT test packs with risks, coverage, and guardrails.")

    with st.form("requirement_input_form"):
        req_id = st.text_input("Requirement ID", value="REQ-001")
        req_title = st.text_input("Requirement Title", value="Self-service Instant Invoicing")
        user_story = st.text_area("User Story", value="As a small business owner, I want to create an invoice in 15 seconds so that I can bill clients immediately.")
        acceptance_criteria_text = st.text_area(
            "Acceptance Criteria (one per line: ID | description)",
            value="AC-001 | Customer can specify client name and amount.\nAC-002 | Invoice is assigned a unique identifier upon creation.\nAC-003 | Status displays as Issued immediately.",
            rows=4,
        )
        generate_testpack_btn = st.form_submit_button("Generate UAT TestPack", type="primary")

    if generate_testpack_btn:
        try:
            criteria = parse_acceptance_criteria(acceptance_criteria_text)
            req_input = RequirementInput(
                requirement_id=req_id,
                title=req_title,
                user_story=user_story,
                acceptance_criteria=criteria,
            )
            with st.spinner("Running deterministic UAT generation workflow..."):
                test_pack = run_uat_workflow(req_input)
                st.success("TestPack generated successfully!")
                st.json(test_pack.model_dump())
        except (ValidationError, ValueError, WorkflowBlockedError, AgentServiceError) as err:
            st.error(f"Generation error: {str(err)}")