"""FastAPI Route Handlers for Simulacra UAT Engine."""

import json
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

import src.simulacra as sim
from src.agent_service import AgentServiceError
from src.schemas import AcceptanceCriterion, RequirementInput
from src.simulacra.mock_app import MockAppServer
from src.simulacra.models import CampaignMission
from src.simulacra.persona import generate_cohort, get_preset_personas
from src.simulacra.reporting import ReportGenerator
from src.simulacra.runner import SimulationRunner
from src.workflow import WorkflowBlockedError, run_uat_workflow

from .schemas import (
    LaunchSimulationRequest,
    PlaywrightFormFillRequest,
    TestPackRequest,
)

router = APIRouter(prefix="/api")


@router.get("/health")
def get_health():
    return {
        "status": "online",
        "engine": "Simulacra UAT",
        "version": "2.5.0",
        "browser_automation": "Playwright Chromium",
    }


@router.get("/personas/presets")
def list_preset_personas():
    personas = get_preset_personas()
    return [p.model_dump() for p in personas]


@router.get("/campaigns")
def list_campaigns():
    return sim.list_campaigns()


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    camp = sim.get_campaign(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")
    report_obj, report_md = sim.get_uat_report(campaign_id)
    return {
        "campaign": camp,
        "report": report_obj.model_dump() if report_obj else None,
        "report_markdown": report_md,
    }


@router.get("/campaigns/{campaign_id}/sessions")
def get_campaign_sessions(campaign_id: str):
    sessions = sim.list_sessions_by_campaign(campaign_id)
    return [s.model_dump() for s in sessions]


@router.get("/campaigns/{campaign_id}/feedbacks")
def get_campaign_feedbacks(campaign_id: str):
    standard_fb = sim.list_feedback_by_campaign(campaign_id)
    quantix_fb = sim.list_quantix_feedbacks_by_campaign(campaign_id)
    return {
        "standard_feedbacks": [f.model_dump() for f in standard_fb],
        "quantix_feedbacks": [q.model_dump() for q in quantix_fb],
    }


@router.get("/sessions/{session_id}/telemetry")
def get_session_telemetry(session_id: str):
    telemetry = sim.get_session_telemetry(session_id)
    return [t.model_dump() for t in telemetry]


@router.get("/campaigns/{campaign_id}/export/markdown")
def export_campaign_markdown(campaign_id: str):
    _, report_md = sim.get_uat_report(campaign_id)
    if not report_md:
        raise HTTPException(status_code=404, detail="Markdown report not found")
    return Response(
        content=report_md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="UAT_Report_{campaign_id}.md"'},
    )


@router.get("/campaigns/{campaign_id}/export/excel")
def export_campaign_excel(campaign_id: str):
    report_obj, _ = sim.get_uat_report(campaign_id)
    if not report_obj:
        raise HTTPException(status_code=404, detail="Campaign report not found")
    sessions = sim.list_sessions_by_campaign(campaign_id)
    feedbacks = sim.list_feedback_by_campaign(campaign_id)
    quantix_forms = sim.list_quantix_feedbacks_by_campaign(campaign_id)
    all_telemetry = []
    for s in sessions:
        all_telemetry.extend(sim.get_session_telemetry(s.session_id))

    excel_bytes = ReportGenerator.export_excel_workbook(
        report=report_obj,
        sessions=sessions,
        feedbacks=feedbacks,
        telemetry=all_telemetry,
        quantix_forms=quantix_forms,
    )
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="UAT_Audit_{campaign_id}.xlsx"'},
    )


@router.get("/campaigns/{campaign_id}/export/json")
def export_campaign_json(campaign_id: str):
    report_obj, _ = sim.get_uat_report(campaign_id)
    if not report_obj:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(
        content=report_obj.model_dump_json(indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="UAT_Data_{campaign_id}.json"'},
    )


@router.post("/demo/start")
def start_demo_server():
    server = MockAppServer.get_or_start(port=8585)
    return {
        "status": "running",
        "url": server.base_url,
        "port": server.port,
    }


@router.post("/simulation/run")
async def run_simulation_stream(req: LaunchSimulationRequest):
    """Executes synthetic personas and streams Server-Sent Events (SSE) in real-time."""

    presets = get_preset_personas()
    if req.cohort_mode == "curated":
        cohort = [presets[i].model_copy(update={"primary_goal": req.primary_goal}) for i in req.selected_preset_indices if i < len(presets)]
        if not cohort:
            cohort = [presets[0].model_copy(update={"primary_goal": req.primary_goal})]
    else:
        cohort = generate_cohort(count=req.cohort_size, custom_goal=req.primary_goal)

    mission = CampaignMission(
        mission_id=f"camp_{req.target_url.replace(':', '_').replace('/', '_')[:15]}",
        title=req.campaign_title,
        target_url=req.target_url,
        primary_goal=req.primary_goal,
        max_steps=req.max_steps,
        headless=req.headless,
        capture_screenshots=req.capture_screenshots,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        # Initial status event
        yield f"data: {json.dumps({'type': 'init', 'total_personas': len(cohort), 'mission_id': mission.mission_id})}\n\n"

        def on_step(persona, evt, current, total):
            event_payload = {
                "type": "step",
                "current_persona": current,
                "total_personas": total,
                "persona_name": persona.name,
                "persona_role": persona.role,
                "step_number": evt.step_number,
                "max_steps": req.max_steps,
                "action_type": evt.action_type.value,
                "page_url": evt.page_url,
                "page_title": evt.page_title,
                "cognitive_reasoning": evt.cognitive_reasoning,
                "emotion": evt.emotion.value,
                "confidence": evt.confidence,
                "hesitation_ms": evt.hesitation_ms,
            }
            # Note: synchronous callback within runner
            # We will yield outside or handle in thread
            nonlocal step_events
            step_events.append(event_payload)

        step_events: list[dict] = []
        runner = SimulationRunner()

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)

        # Run campaign in background worker thread while polling step_events
        future = loop.run_in_executor(
            executor,
            runner.run_campaign,
            mission,
            cohort,
            on_step,
        )

        sent_index = 0
        while not future.done():
            while sent_index < len(step_events):
                yield f"data: {json.dumps(step_events[sent_index])}\n\n"
                sent_index += 1
            await asyncio.sleep(0.2)

        # Flush any remaining step events
        while sent_index < len(step_events):
            yield f"data: {json.dumps(step_events[sent_index])}\n\n"
            sent_index += 1

        report, report_md, sessions, feedbacks, _ = future.result()
        complete_payload = {
            "type": "complete",
            "campaign_id": report.campaign_id,
            "success_rate": report.task_completion_rate,
            "average_sus": report.average_sus_score,
            "sessions_count": len(sessions),
        }
        yield f"data: {json.dumps(complete_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/surveys/fill-google-form")
def fill_google_form(req: PlaywrightFormFillRequest):
    quantix_feedbacks = sim.list_quantix_feedbacks_by_campaign(req.campaign_id)
    target_qfb = next((q for q in quantix_feedbacks if q.session_id == req.session_id), None)
    if not target_qfb:
        raise HTTPException(status_code=404, detail="Quantix feedback not found for session")

    ok, msg, shot = sim.fill_google_form_playwright(target_qfb, headless=req.headless, submit=req.submit)
    return {
        "success": ok,
        "message": msg,
        "screenshot_path": shot,
    }


@router.post("/testpack/generate")
def generate_testpack(req: TestPackRequest):
    try:
        criteria = []
        for line in req.acceptance_criteria:
            if "|" in line:
                cid, desc = line.split("|", maxsplit=1)
                criteria.append(AcceptanceCriterion(criterion_id=cid.strip(), description=desc.strip()))
        req_input = RequirementInput(
            requirement_id=req.requirement_id,
            title=req.title,
            user_story=req.user_story,
            acceptance_criteria=criteria,
        )
        test_pack = run_uat_workflow(req_input)
        return test_pack.model_dump()
    except (ValidationError, ValueError, WorkflowBlockedError, AgentServiceError) as err:
        raise HTTPException(status_code=400, detail=str(err))
