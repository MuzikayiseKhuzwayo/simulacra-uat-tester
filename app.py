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
from src.schemas import (
    AcceptanceCriterion,
    RequirementInput,
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

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Custom Modern UI Theme
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Simulacra UAT — Autonomous User Testing Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject Custom High-End Modern CSS Design System
st.markdown(
    """
    <style>
        /* Base page styling */
        .stApp {
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Hero Header */
        .hero-container {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        }
        .hero-badge {
            display: inline-block;
            background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 20px;
            margin-bottom: 12px;
        }
        .hero-title {
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #f8fafc;
            margin: 0 0 6px 0;
        }
        .hero-subtitle {
            font-size: 14px;
            color: #94a3b8;
            margin: 0;
            line-height: 1.5;
        }

        /* Status bar */
        .system-status-bar {
            display: flex;
            gap: 20px;
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 12px;
            color: #64748b;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #10b981;
            box-shadow: 0 0 8px #10b981;
        }

        /* Clean Card Surfaces */
        .sim-panel {
            background-color: #111726;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .sim-panel-title {
            font-size: 15px;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Metric Cards */
        .metric-card {
            background: linear-gradient(180deg, #161f33 0%, #101524 100%);
            border: 1px solid #202b42;
            border-radius: 10px;
            padding: 16px 18px;
            text-align: left;
            position: relative;
            overflow: hidden;
        }
        .metric-card.accent-blue { border-top: 3px solid #3b82f6; }
        .metric-card.accent-emerald { border-top: 3px solid #10b981; }
        .metric-card.accent-amber { border-top: 3px solid #f59e0b; }
        .metric-card.accent-rose { border-top: 3px solid #f43f5e; }
        .metric-card.accent-purple { border-top: 3px solid #8b5cf6; }

        .metric-label {
            font-size: 12px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .metric-val {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.2;
        }
        .metric-sub {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }

        /* Persona Badge */
        .persona-card {
            background: #151c2c;
            border: 1px solid #243048;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .persona-name {
            font-weight: 700;
            font-size: 13px;
            color: #f8fafc;
        }
        .persona-role {
            font-size: 11px;
            color: #38bdf8;
            margin-bottom: 6px;
        }
        .tag-pill {
            display: inline-block;
            font-size: 10px;
            padding: 2px 7px;
            border-radius: 4px;
            margin-right: 4px;
            background: #1e293b;
            color: #cbd5e1;
        }

        /* Step Timeline */
        .step-timeline-box {
            background: #131929;
            border: 1px solid #1f2a40;
            border-left: 3px solid #38bdf8;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }

        /* Live Terminal Box */
        .terminal-box {
            background-color: #070a10;
            border: 1px solid #1e2638;
            border-radius: 8px;
            padding: 14px;
            font-family: "JetBrains Mono", "Courier New", monospace;
            font-size: 12px;
            color: #38bdf8;
            max-height: 250px;
            overflow-y: auto;
        }

        /* Tabs overhaul */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #0d121f;
            padding: 6px;
            border-radius: 10px;
            border: 1px solid #1e293b;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            font-size: 13px;
            padding: 8px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Helper Functions for Acceptance Criteria
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


# -----------------------------------------------------------------------------
# Hero Header & System Telemetry Status
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-container">
        <span class="hero-badge">Autonomous UAT Engine &bull; v2.5 Enterprise</span>
        <h1 class="hero-title">Simulacra UAT &mdash; Autonomous Persona Testing Platform</h1>
        <p class="hero-subtitle">
            Simulate cohorts of diverse synthetic customer personas exploring web applications, evaluating cognitive friction,
            capturing fine-grained DOM telemetry, and generating executive UX audits &amp; customer feedback surveys.
        </p>
        <div class="system-status-bar">
            <span class="status-pill"><span class="status-dot"></span> Playwright Engine: <b>Active (Chromium)</b></span>
            <span class="status-pill"><span class="status-dot"></span> Cognitive AI: <b>Gemini 2.5 Flash</b></span>
            <span class="status-pill"><span class="status-dot"></span> Synthetic Personas: <b>6 Archetypes Ready</b></span>
            <span class="status-pill"><span class="status-dot"></span> Survey Synthesizer: <b>Google Form &amp; SUS Integrated</b></span>
        </div>
    </div>
    """,

    unsafe_allow_html=True,
)

# Main Navigation Tabs
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
# TAB 1: Simulation Studio (Autonomous Cockpit)
# -----------------------------------------------------------------------------

with tab_studio:
    # Environment Presets & Target Setup
    col_left, col_right = st.columns([1.1, 1], gap="medium")

    with col_left:
        st.markdown(
            """
            <div class="sim-panel-title">🎯 1. Target Environment &amp; Mission Goal</div>
            """,
            unsafe_allow_html=True,
        )

        # Quick Target Selector Buttons
        st.caption("Quick Environment Presets:")
        preset_cols = st.columns(3)
        if preset_cols[0].button("🌐 Quantix App (4200)", use_container_width=True):
            st.session_state["target_url_input"] = "http://localhost:4200/"
            st.session_state["campaign_title_input"] = "Quantix Live Web App UAT Audit"
            st.session_state["mission_goal_input"] = (
                "Explore features, inspect pricing tiers and risk models, test signup onboarding, "
                "and reach the main portfolio dashboard."
            )
        if preset_cols[1].button("🏢 AcmeCloud Demo (8585)", use_container_width=True):
            st.session_state["target_url_input"] = "http://127.0.0.1:8585"
            st.session_state["campaign_title_input"] = "AcmeCloud SaaS Trial & Onboarding"
            st.session_state["mission_goal_input"] = (
                "Explore features, inspect pricing plans, sign up for a free trial, and reach the dashboard to issue an invoice."
            )
        if preset_cols[2].button("⚡ Start Demo Server", use_container_width=True):
            server = MockAppServer.get_or_start(port=8585)
            st.success(f"Built-in AcmeCloud SaaS running at {server.base_url}")
            st.session_state["target_url_input"] = "http://127.0.0.1:8585"

        default_url = st.session_state.get("target_url_input", "http://localhost:4200/")
        default_title = st.session_state.get("campaign_title_input", "Quantix Live Web App UAT Audit")
        default_goal = st.session_state.get(
            "mission_goal_input",
            "Explore features, inspect pricing tiers and risk models, test signup onboarding, and reach the main portfolio dashboard.",
        )

        c_url, c_title = st.columns([3, 2])
        with c_url:
            target_url = st.text_input(
                "Target Web App URL",
                value=default_url,
                help="Local or public URL of the application under test (e.g., http://localhost:4200/)",
            )
        with c_title:
            campaign_title = st.text_input(
                "Campaign Title",
                value=default_title,
                help="Descriptive name for this UAT campaign run",
            )

        mission_goal = st.text_area(
            "Primary User Goal / Mission Objective",
            value=default_goal,
            rows=3,
            help="High-level scenario the synthetic personas will attempt to accomplish autonomously.",
        )

    with col_right:
        st.markdown(
            """
            <div class="sim-panel-title">👥 2. Synthetic Persona Cohort</div>
            """,
            unsafe_allow_html=True,
        )

        cohort_mode = st.radio(
            "Cohort Generation Strategy",
            ["Curated Archetypes (Recommended)", "Algorithmic Diverse Cohort"],
            horizontal=True,
        )

        preset_personas = get_preset_personas()
        preset_labels = [
            f"{p.name} — {p.role} (Tech: {p.technical_skill.value}, Patience: {p.patience.value})"
            for p in preset_personas
        ]

        if cohort_mode.startswith("Curated"):
            selected_indices = st.multiselect(
                "Select Personas to Participate in Cohort",
                options=list(range(len(preset_labels))),
                format_func=lambda idx: preset_labels[idx],
                default=[0, 1, 2],
            )
            cohort_size = len(selected_indices)

            # Persona preview summary
            with st.expander(f"👁️ View Selected Personas Details ({cohort_size} Active)", expanded=False):
                for idx in selected_indices:
                    p = preset_personas[idx]
                    st.markdown(
                        f"""
                        <div class="persona-card">
                            <div class="persona-name">👤 {p.name} &bull; <span style="font-weight:normal; color:#cbd5e1;">{p.role} (Age {p.age})</span></div>
                            <div class="persona-role">Device: {p.device_type.value} &bull; Tech: {p.technical_skill.value} &bull; Patience: {p.patience.value}</div>
                            <div>
                                <span class="tag-pill">Risk: {p.risk_tolerance.value}</span>
                                <span class="tag-pill">Speed: {p.reading_speed.value}</span>
                                <span class="tag-pill">Attention: {p.attention_span.value}</span>
                            </div>
                            <div style="font-size:11px; color:#94a3b8; margin-top:6px;">
                                <b>Biases:</b> {', '.join(p.biases[:2])}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            cohort_size = st.slider("Algorithmic Cohort Size (Synthetic Users)", min_value=1, max_value=20, value=5)
            selected_indices = []

        st.markdown(
            """
            <div class="sim-panel-title" style="margin-top: 14px;">⚙️ 3. Execution Parameters</div>
            """,
            unsafe_allow_html=True,
        )
        p_c1, p_c2, p_c3 = st.columns(3)
        with p_c1:
            max_steps = st.number_input("Max Steps per User", min_value=3, max_value=40, value=12)
        with p_c2:
            headless_mode = st.checkbox("Headless Browser", value=True, help="Run Chromium without opening a visible window")
        with p_c3:
            capture_shots = st.checkbox("Capture Screenshots", value=True, help="Save milestone DOM screenshots")

    st.write("")
    launch_btn = st.button("🚀 Launch Autonomous UAT Simulation Cohort", type="primary", use_container_width=True)

    if launch_btn:
        if not target_url.strip():
            st.error("⚠️ Please specify a valid Target Web Application URL.")
        else:
            if cohort_mode.startswith("Curated"):
                if not selected_indices:
                    st.warning("⚠️ Please select at least one persona archetype.")
                    st.stop()
                cohort = [preset_personas[i].model_copy(update={"primary_goal": mission_goal}) for i in selected_indices]
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

            st.markdown("---")
            st.markdown("### 📡 Live Execution Telemetry Stream")
            progress_bar = st.progress(0.0)
            status_container = st.empty()
            terminal_placeholder = st.empty()
            stream_messages: list[str] = []

            def on_step(persona, evt, current, total):
                prog = round((current - 1 + (evt.step_number / max_steps)) / total, 2)
                progress_bar.progress(min(prog, 0.99))
                status_container.info(
                    f"🏃 **Simulating Persona ({current}/{total}):** `{persona.name}` ({persona.role}) &bull; "
                    f"Step {evt.step_number}/{max_steps}: Action `{evt.action_type.value.upper()}`"
                )
                stream_messages.append(
                    f"[{persona.name}] {evt.action_type.value.upper()} -> {evt.page_title or evt.page_url}\n"
                    f"  Reason: \"{evt.cognitive_reasoning}\" (Emotion: {evt.emotion.value}, Conf: {evt.confidence:.2f})\n"
                )
                formatted_terminal = "\n".join(stream_messages[-8:])
                terminal_placeholder.markdown(
                    f'<div class="terminal-box"><pre style="margin:0; color:#38bdf8;">{formatted_terminal}</pre></div>',
                    unsafe_allow_html=True,
                )

            with st.spinner("🤖 Autonomous synthetic personas are navigating, evaluating UX, and answering surveys..."):
                runner = SimulationRunner()
                report, report_md, sessions, feedbacks, all_telemetry = runner.run_campaign(
                    mission=mission,
                    personas=cohort,
                    on_step_progress=on_step,
                )

            progress_bar.progress(1.0)
            status_container.success(f"🎉 Simulation Campaign Completed! Executed {len(sessions)} synthetic persona journeys.")
            st.session_state["active_campaign_id"] = report.campaign_id
            st.balloons()


# -----------------------------------------------------------------------------
# TAB 2: Executive UAT Reports (Command Center)
# -----------------------------------------------------------------------------

with tab_reports:
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No simulation campaigns recorded yet. Launch a simulation in the Simulation Studio to generate an executive report.")
    else:
        camp_options = {c["campaign_id"]: f"{c['title']} — ({c['created_at'][:19]})" for c in campaigns}
        default_camp_id = st.session_state.get("active_campaign_id", campaigns[0]["campaign_id"])
        if default_camp_id not in camp_options:
            default_camp_id = campaigns[0]["campaign_id"]

        col_sel, col_empty = st.columns([2, 1])
        with col_sel:
            selected_camp_id = st.selectbox(
                "Select UAT Campaign Audit to Inspect",
                options=list(camp_options.keys()),
                format_func=lambda cid: camp_options[cid],
                index=list(camp_options.keys()).index(default_camp_id),
            )

        camp_data = sim.get_campaign(selected_camp_id)
        report_obj, report_markdown = sim.get_uat_report(selected_camp_id)
        camp_sessions = sim.list_sessions_by_campaign(selected_camp_id)
        camp_feedbacks = sim.list_feedback_by_campaign(selected_camp_id)

        # Usability Grade Calculation
        sus_score = camp_data.get("average_sus_score", 0.0)
        if sus_score >= 80.3:
            grade_badge = "A (Excellent)"
            grade_color = "accent-emerald"
        elif sus_score >= 68.0:
            grade_badge = "B (Good)"
            grade_color = "accent-blue"
        elif sus_score >= 51.0:
            grade_badge = "C (Marginal)"
            grade_color = "accent-amber"
        else:
            grade_badge = "F (High Friction)"
            grade_color = "accent-rose"

        # Executive KPI Cards Grid
        m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
        with m_c1:
            st.markdown(
                f"""
                <div class="metric-card {grade_color}">
                    <div class="metric-label">Usability (SUS)</div>
                    <div class="metric-val">{sus_score:.1f} <span style="font-size:14px; font-weight:normal; color:#94a3b8;">/ 100</span></div>
                    <div class="metric-sub">Grade: <b>{grade_badge}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_c2:
            succ_pct = camp_data.get("success_rate_percent", 0.0)
            succ_card_accent = "accent-emerald" if succ_pct >= 80 else ("accent-amber" if succ_pct >= 50 else "accent-rose")
            st.markdown(
                f"""
                <div class="metric-card {succ_card_accent}">
                    <div class="metric-label">Task Success Rate</div>
                    <div class="metric-val">{succ_pct:.1f}%</div>
                    <div class="metric-sub">{camp_data.get('successful_sessions', 0)} / {camp_data.get('total_sessions', 0)} Completed</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_c3:
            fric_score = camp_data.get("average_friction_score", 0.0)
            fric_accent = "accent-rose" if fric_score > 40 else ("accent-amber" if fric_score > 20 else "accent-emerald")
            fric_desc = "Elevated Risk" if fric_score > 40 else ("Moderate" if fric_score > 20 else "Smooth UX")
            st.markdown(
                f"""
                <div class="metric-card {fric_accent}">
                    <div class="metric-label">Friction Index</div>
                    <div class="metric-val">{fric_score:.1f} <span style="font-size:14px; font-weight:normal; color:#94a3b8;">/ 100</span></div>
                    <div class="metric-sub">Status: <b>{fric_desc}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_c4:
            st.markdown(
                f"""
                <div class="metric-card accent-rose">
                    <div class="metric-label">Rage Clicks</div>
                    <div class="metric-val">{camp_data.get('total_rage_clicks', 0)}</div>
                    <div class="metric-sub">Dead / Misclick Triggers</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_c5:
            st.markdown(
                f"""
                <div class="metric-card accent-purple">
                    <div class="metric-label">Personas Tested</div>
                    <div class="metric-val">{camp_data.get('total_sessions', 0)}</div>
                    <div class="metric-sub">Across All Archetypes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # Action Bar: Downloads & Exports
        d_col1, d_col2, d_col3 = st.columns(3)
        if report_markdown:
            d_col1.download_button(
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
            camp_qforms = sim.list_quantix_feedbacks_by_campaign(selected_camp_id)
            excel_bytes = ReportGenerator.export_excel_workbook(
                report=report_obj,
                sessions=camp_sessions,
                feedbacks=camp_feedbacks,
                telemetry=all_tel,
                quantix_forms=camp_qforms,
            )
            d_col2.download_button(
                "📥 Export UX Audit Workbook (Excel)",
                data=excel_bytes,
                file_name=f"UAT_Audit_{selected_camp_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            d_col3.download_button(
                "📥 Export Full Telemetry (JSON)",
                data=report_obj.model_dump_json(indent=2),
                file_name=f"UAT_Data_{selected_camp_id}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("---")

        # Render Markdown Report
        if report_markdown:
            st.markdown(report_markdown)


# -----------------------------------------------------------------------------
# TAB 3: User Sessions & Telemetry (Forensics Lab)
# -----------------------------------------------------------------------------

with tab_sessions:
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No recorded sessions found. Launch a simulation to inspect synthetic user journeys.")
    else:
        col_c_sel, col_s_sel = st.columns([1, 2])
        with col_c_sel:
            sel_campaign_for_sess = st.selectbox(
                "Select Campaign",
                options=[c["campaign_id"] for c in campaigns],
                format_func=lambda cid: next((c["title"] for c in campaigns if c["campaign_id"] == cid), cid),
                key="sess_camp_select",
            )
        sessions = sim.list_sessions_by_campaign(sel_campaign_for_sess)

        if not sessions:
            st.info("No sessions in this campaign.")
        else:
            sess_dict = {
                s.session_id: f"{s.persona_name} — {'✅ Passed' if s.task_success else '❌ Abandoned'} ({s.duration_seconds}s, {s.total_steps} steps)"
                for s in sessions
            }
            with col_s_sel:
                selected_sess_id = st.selectbox(
                    "Select Synthetic Persona Journey",
                    options=list(sess_dict.keys()),
                    format_func=lambda sid: sess_dict[sid],
                )

            current_session = next(s for s in sessions if s.session_id == selected_sess_id)
            telemetry_events = sim.get_session_telemetry(selected_sess_id)

            # Session Metrics Overview Bar
            s_c1, s_c2, s_c3, s_c4 = st.columns(4)
            with s_c1:
                st.metric("Friction Score", f"{current_session.friction_score:.1f} / 100")
            with s_c2:
                st.metric("Total Steps Taken", f"{current_session.total_steps}")
            with s_c3:
                st.metric("Rage Clicks Triggered", f"{current_session.rage_clicks_total}")
            with s_c4:
                st.metric("Exit Reason", f"{current_session.exit_reason.value}")

            st.markdown("#### 🧠 Chronological Cognitive Journey Stream")
            for evt in telemetry_events:
                status_color = "#10b981" if evt.emotion.value in ["Delighted", "Satisfied", "Curious"] else ("#f43f5e" if evt.emotion.value in ["Frustrated", "Annoyed"] else "#38bdf8")
                st.markdown(
                    f"""
                    <div class="step-timeline-box" style="border-left-color: {status_color};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <div>
                                <span style="background:#1e293b; color:#38bdf8; font-weight:700; padding:2px 8px; border-radius:4px; font-size:11px; font-family:monospace;">
                                    STEP {evt.step_number:02d}
                                </span>
                                &nbsp;
                                <b style="color:#ffffff; font-size:13px;">{evt.action_type.value.upper()}</b>
                                &nbsp;
                                <span style="color:#94a3b8; font-size:12px;">on <code>{evt.target_element or evt.page_url}</code></span>
                            </div>
                            <div style="font-size:11px; color:#cbd5e1;">
                                Emotion: <b style="color:{status_color};">{evt.emotion.value}</b> &bull;
                                Confidence: <b>{evt.confidence:.2f}</b> &bull;
                                Hesitation: <b>{evt.hesitation_ms}ms</b>
                            </div>
                        </div>
                        <div style="background:#0c101c; border-radius:6px; padding:10px 14px; font-size:13px; color:#e2e8f0; font-style:italic;">
                            💭 <b>Inner Monologue:</b> "{evt.cognitive_reasoning}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if evt.screenshot_path and Path(evt.screenshot_path).exists():
                    st.image(evt.screenshot_path, caption=f"Step {evt.step_number} DOM Snapshot — {evt.page_title}", width=700)


# -----------------------------------------------------------------------------
# TAB 4: Persona UX Surveys & Google Form Feedback
# -----------------------------------------------------------------------------

with tab_surveys:
    campaigns = sim.list_campaigns()

    if not campaigns:
        st.info("No feedback records available. Run a simulation in the Simulation Studio to generate survey responses.")
    else:
        col_fb_c, col_fb_fmt = st.columns([1, 1])
        with col_fb_c:
            sel_campaign_for_fb = st.selectbox(
                "Select Campaign for Surveys",
                options=[c["campaign_id"] for c in campaigns],
                format_func=lambda cid: next((c["title"] for c in campaigns if c["campaign_id"] == cid), cid),
                key="fb_camp_select",
            )
        feedbacks = sim.list_feedback_by_campaign(sel_campaign_for_fb)
        quantix_feedbacks = sim.list_quantix_feedbacks_by_campaign(sel_campaign_for_fb)

        with col_fb_fmt:
            survey_format = st.radio(
                "Survey Display Format",
                [
                    "📋 Google Form Format (Customer Feedback - Quantix)",
                    "📊 Standard UX Scorecard (SUS / CES / NPS)",
                ],
                horizontal=True,
            )

        if quantix_feedbacks:
            all_qfb_json = json.dumps([q.model_dump() for q in quantix_feedbacks], indent=2)
            st.download_button(
                "📥 Export Complete Google Forms Data (JSON)",
                data=all_qfb_json,
                file_name=f"Quantix_Google_Forms_{sel_campaign_for_fb}.json",
                mime="application/json",
            )

        if survey_format.startswith("📋 Google Form Format"):
            if not quantix_feedbacks:
                st.info(
                    "No 8-section Google Form responses found for this campaign. "
                    "Run a new simulation from the Simulation Studio to synthesize authentic Google Form responses."
                )
            else:
                st.caption(
                    f"Survey responses modeled directly after the official "
                    f"[Quantix Customer Feedback Google Form]({sim.GOOGLE_FORM_VIEW_URL}) "
                    f"capturing all 8 sections, Likert scales, and qualitative feedback."
                )

                for qfb in quantix_feedbacks:
                    expander_label = (
                        f"📝 {qfb.persona_name} ({qfb.primary_role}) — "
                        f"NPS: {qfb.nps_recommendation}/10 | PMF: {qfb.pmf_feeling.split(';')[0]} | Emotion: {qfb.emotional_sentiment}"
                    )
                    with st.expander(expander_label, expanded=True):
                        # Google Form Teal Branded Header
                        st.markdown(
                            f"""
                            <div style="background: linear-gradient(135deg, #02746b 0%, #039f93 100%); 
                                        color: white; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                                <h2 style="margin: 0; color: white; font-family: sans-serif; font-weight: 600;">Customer Feedback - Quantix</h2>
                                <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">
                                    Synthetic Persona Response &bull; <b>{qfb.persona_name}</b> ({qfb.primary_role}) &bull; Submitted: <code>{qfb.submitted_at[:19]}</code>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # SECTION 1: Landing Page Evaluation
                        st.markdown("### 1. Landing Page Evaluation")
                        col_lp1, col_lp2 = st.columns([1, 1])
                        with col_lp1:
                            st.markdown(f"**Gut Reaction:**")
                            for gr in qfb.gut_reaction:
                                st.markdown(f"- 🏷️ `{gr}`")
                        with col_lp2:
                            c_s1, c_s2, c_s3 = st.columns(3)
                            c_s1.metric("Clarity (10-15s)", f"{qfb.clarity_10_15s} / 5")
                            c_s2.metric("Visual Design", f"{qfb.visual_design} / 5")
                            c_s3.metric("Credibility", f"{qfb.credibility} / 5")

                        st.markdown(f"**Element that convinced you to explore further:**")
                        st.info(f"💬 \"{qfb.convincing_element}\"")
                        if qfb.hesitation_trigger:
                            st.markdown(f"**Element that caused hesitation or skepticism:**")
                            st.warning(f"⚠️ \"{qfb.hesitation_trigger}\"")

                        st.divider()

                        # SECTION 2: Account Creation and Sign-Up
                        st.markdown("### 2. Account Creation and Sign-Up")
                        c_su1, c_su2, c_su3 = st.columns(3)
                        c_su1.markdown(f"**Sign-Up Method:**\n`{qfb.signup_method}`")
                        c_su2.markdown(f"**Information Requested:**\n`{qfb.info_requested_feeling}`")
                        c_su3.markdown(f"**Technical Issues:**\n`{qfb.signup_technical_issues}`")

                        st.divider()

                        # SECTION 3: Initial Intake Experience
                        st.markdown("### 3. Initial Intake Experience")
                        c_in1, c_in2, c_in3, c_in4 = st.columns(4)
                        c_in1.metric("Relevance", f"{qfb.relevance_rating} / 5")
                        c_in2.metric("Clarity", f"{qfb.clarity_rating} / 5")
                        c_in3.metric("Progression", f"{qfb.progression_rating} / 5")
                        c_in4.metric("Engagement", f"{qfb.engagement_rating} / 5")
                        st.markdown(f"- **Time Expected vs Actual:** `{qfb.time_expected_vs_actual}`")
                        st.markdown(f"- **Comfort Answering Profile:** `{qfb.comfort_answering_profile}`")
                        st.markdown(f"- **Awkward / Intrusive Question:** *\"{qfb.awkward_question}\"*")

                        st.divider()

                        # SECTION 4: Core Product
                        st.markdown("### 4. Core Product")
                        col_cp1, col_cp2 = st.columns(2)
                        with col_cp1:
                            st.markdown("**Initial Feeling upon Dashboard Load:**")
                            for df in qfb.initial_dashboard_feeling:
                                st.markdown(f"- 💡 `{df}`")
                        with col_cp2:
                            c_cp_m1, c_cp_m2, c_cp_m3 = st.columns(3)
                            c_cp_m1.metric("Intuitiveness", f"{qfb.navigating_intuitiveness} / 5")
                            c_cp_m2.metric("Speed", f"{qfb.speed_responsiveness} / 5")
                            c_cp_m3.metric("Reliability", f"{qfb.reliability} / 5")

                        st.markdown(f"**The 'Aha!' Moment:**")
                        st.success(f"✨ \"{qfb.aha_moment}\"")

                        st.divider()

                        # SECTION 5: Emotional Sentiment
                        st.markdown("### 5. Emotional Sentiment and Perception")
                        st.markdown(f"**Dominant Emotional Sentiment:** `{qfb.emotional_sentiment}`")

                        st.divider()

                        # SECTION 6: Friction and Missing Pieces
                        st.markdown("### 6. Friction and Missing Pieces")
                        st.markdown(f"**Most Frustrating or Confusing Moment:**")
                        st.error(f"🛑 \"{qfb.most_frustrating_moment}\"")
                        st.markdown(f"**Feature Expected but Missing:**")
                        st.info(f"🔍 \"{qfb.missing_feature_expected}\"")
                        st.markdown(f"**Prior Alternative Used:** `{qfb.prior_alternative_used}`")

                        st.divider()

                        # SECTION 7: Overall Satisfaction & PMF
                        st.markdown("### 7. Overall Satisfaction & Product-Market Fit")
                        c_sat1, c_sat2 = st.columns([1, 2])
                        with c_sat1:
                            nps_label = "🟢 Promoter" if qfb.nps_recommendation >= 9 else ("🟡 Passive" if qfb.nps_recommendation >= 7 else "🔴 Detractor")
                            st.metric("NPS Score", f"{qfb.nps_recommendation} / 10", nps_label)
                            st.markdown(f"**PMF Assessment:**\n`{qfb.pmf_feeling}`")
                        with c_sat2:
                            st.markdown(f"**Reason for Recommendation Rating:**")
                            st.markdown(f"> \"{qfb.nps_reason}\"")
                            st.markdown(f"**Magic Wand (One Wish):**")
                            st.markdown(f"> 🪄 \"{qfb.magic_wand_change}\"")

                        st.divider()

                        # SECTION 8: User Qualification and Comprehension
                        st.markdown("### 8. User Qualification and Comprehension")
                        c_uq1, c_uq2 = st.columns(2)
                        with c_uq1:
                            st.markdown(f"- **Primary Role:** `{qfb.primary_role}`")
                            st.markdown(f"- **Discovery Source:** `{qfb.discovery_source}`")
                            st.markdown(f"- **Problem Urgency:** `{qfb.problem_urgency}`")
                            st.markdown(f"- **Team Size:** `{qfb.team_size}`")
                        with c_uq2:
                            st.markdown(f"- **Decision Maker Role:** `{qfb.role_in_selecting_tools}`")
                            st.markdown(f"- **Domain Knowledge:** `{qfb.problem_space_knowledge}`")
                            st.markdown(f"- **Technical Comfort:** `{qfb.tech_comfort} / 5`")
                            st.markdown(f"- **Related Tools Used:** `{', '.join(qfb.related_tools_used)}`")

                        st.markdown(f"**Quantix Pitch in Persona's Own Words:**")
                        st.info(f"📢 \"{qfb.one_sentence_pitch}\"")
                        st.markdown(f"**Expected Outcome / Transformation:**")
                        st.info(f"🚀 \"{qfb.expected_transformation}\"")

                        # Live Google Form Actions
                        st.markdown("#### 🔗 Live Google Form Automation")
                        col_act1, col_act2 = st.columns([1, 1])
                        with col_act1:
                            st.link_button(
                                "🌐 Open Live Google Form in Browser",
                                sim.GOOGLE_FORM_VIEW_URL,
                                use_container_width=True,
                            )
                        with col_act2:
                            if st.button(
                                f"🤖 Auto-Fill Live Google Form with Playwright ({qfb.persona_name})",
                                key=f"btn_fill_{qfb.session_id}",
                                use_container_width=True,
                            ):
                                with st.spinner(f"Launching Playwright to fill Google Form for {qfb.persona_name}..."):
                                    ok, msg, shot = sim.fill_google_form_playwright(qfb, headless=True, submit=False)
                                    if ok:
                                        st.success(f"Playwright executed: {msg}")
                                        if shot and Path(shot).exists():
                                            st.image(shot, caption=f"Google Form Snapshot for {qfb.persona_name}", use_container_width=True)
                                    else:
                                        st.warning(f"Playwright result: {msg}")

        else:
            # Standard UX Scorecard View
            if not feedbacks:
                st.info("No standard feedback surveys recorded for this campaign.")
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
# TAB 5: Legacy UAT TestPack Design Agent (Preserved & Styled)
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