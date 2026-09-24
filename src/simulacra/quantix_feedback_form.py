"""Detailed Quantix Customer Feedback Survey modeled after the official Google Form.

Maps all 8 sections, multi-select checkboxes, 1-5 Likert scales, NPS, PMF scores,
and qualitative open-ended questions to authentic persona responses.
"""

import json
import urllib.parse
import urllib.request
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from src.simulacra.models import (
    ActionType,
    Emotion,
    ExitReason,
    PatienceLevel,
    Persona,
    SessionMetrics,
    TechnicalSkill,
    TelemetryEvent,
)

GOOGLE_FORM_ID = "1uY1kuwIU6mbTAxoNJYta-FluRCjWxmPWBlJvf-FY1eI"
GOOGLE_FORM_VIEW_URL = f"https://docs.google.com/forms/d/{GOOGLE_FORM_ID}/viewform"
GOOGLE_FORM_POST_URL = f"https://docs.google.com/forms/d/{GOOGLE_FORM_ID}/formResponse"


class QuantixFeedbackForm(BaseModel):
    """Complete survey response matching Google Form 'Customer Feedback - Quantix'."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    form_id: str = Field(default_factory=lambda: f"gform_{uuid.uuid4().hex[:10]}")
    session_id: str
    persona_id: str
    persona_name: str
    submitted_at: str

    # 1. Landing Page Evaluation
    gut_reaction: list[str] = Field(default_factory=list)  # entry.1591633300
    clarity_10_15s: int = Field(default=3, ge=1, le=5)    # entry.326955045
    visual_design: int = Field(default=4, ge=1, le=5)     # entry.1696159737
    credibility: int = Field(default=4, ge=1, le=5)       # entry.485428648
    convincing_element: str = ""                          # entry.879531967
    hesitation_trigger: str = ""                          # entry.581158488

    # 2. Account Creation and Sign-Up
    signup_method: str = "Email & Password"               # entry.2130349355
    info_requested_feeling: str = "Perfectly reasonable/minimal"  # entry.1692060985
    signup_technical_issues: str = "No, it worked flawlessly"     # entry.821373294

    # 3. Initial Intake Experience
    time_expected_vs_actual: str = "Just right/As expected"       # entry.1000840381
    relevance_rating: int = Field(default=4, ge=1, le=5)          # entry.848109780
    clarity_rating: int = Field(default=4, ge=1, le=5)            # entry.1772778842
    progression_rating: int = Field(default=4, ge=1, le=5)        # entry.1997500533
    engagement_rating: int = Field(default=4, ge=1, le=5)         # entry.570983164
    comfort_answering_profile: str = "100% comfortable; clear why each piece of data was needed"  # entry.362347072
    awkward_question: str = "None"                                # entry.141539753

    # 4. Core Product
    initial_dashboard_feeling: list[str] = Field(default_factory=list)  # entry.1519142306
    navigating_intuitiveness: int = Field(default=4, ge=1, le=5)        # entry.1549113816
    aha_moment: str = "Seeing pre-calculated volatility envelopes"      # entry.1221085709
    speed_responsiveness: int = Field(default=5, ge=1, le=5)            # entry.567762584
    reliability: int = Field(default=4, ge=1, le=5)                     # entry.583499807

    # 5. Emotional Sentiment and Perception
    emotional_sentiment: str = "Hopeful/Curious"          # entry.553593956

    # 6. Friction and Missing Pieces
    most_frustrating_moment: str = ""                     # entry.1704229802
    missing_feature_expected: str = ""                    # entry.693558549
    prior_alternative_used: str = "Spreadsheets/Manual notes"  # entry.1104210811

    # 7. Overall Satisfaction & PMF
    nps_recommendation: int = Field(default=8, ge=0, le=10)     # entry.1522315979
    nps_reason: str = ""                                       # entry.1608936399
    pmf_feeling: str = "Somewhat disappointed"                 # entry.1474503764
    magic_wand_change: str = ""                                # entry.943741917

    # 8. User Qualification and Comprehension
    primary_role: str                                          # entry.958837792
    discovery_source: str = "Direct Link from an article, newsletter, or partner site"  # entry.1517313392
    problem_urgency: str = "Important (Looking for a solution for this within the next 3 weeks)"  # entry.1973028867
    team_size: str = "2-10 people (Early Stage/Boutique)"      # entry.888248497
    role_in_selecting_tools: str = "Sole Decison Maker: I decide and pay directly"  # entry.491093053
    problem_space_knowledge: str = "Intermediate: I understand the core concepts and workflows reasonably well"  # entry.1085938728
    tech_comfort: int = Field(default=3, ge=1, le=5)           # entry.1439741479
    related_tools_used: list[str] = Field(default_factory=list)  # entry.82933934
    one_sentence_pitch: str                                    # entry.1934953822
    primary_target_audience: str = "People exactly like me"    # entry.1144200843
    expected_transformation: str                               # entry.362573784


ENTRY_MAP = {
    "gut_reaction": 1591633300,
    "clarity_10_15s": 326955045,
    "visual_design": 1696159737,
    "credibility": 485428648,
    "convincing_element": 879531967,
    "hesitation_trigger": 581158488,
    "signup_method": 2130349355,
    "info_requested_feeling": 1692060985,
    "signup_technical_issues": 821373294,
    "time_expected_vs_actual": 1000840381,
    "relevance_rating": 848109780,
    "clarity_rating": 1772778842,
    "progression_rating": 1997500533,
    "engagement_rating": 570983164,
    "comfort_answering_profile": 362347072,
    "awkward_question": 141539753,
    "initial_dashboard_feeling": 1519142306,
    "navigating_intuitiveness": 1549113816,
    "aha_moment": 1221085709,
    "speed_responsiveness": 567762584,
    "reliability": 583499807,
    "emotional_sentiment": 553593956,
    "most_frustrating_moment": 1704229802,
    "missing_feature_expected": 693558549,
    "prior_alternative_used": 1104210811,
    "nps_recommendation": 1522315979,
    "nps_reason": 1608936399,
    "pmf_feeling": 1474503764,
    "magic_wand_change": 943741917,
    "primary_role": 958837792,
    "discovery_source": 1517313392,
    "problem_urgency": 1973028867,
    "team_size": 888248497,
    "role_in_selecting_tools": 491093053,
    "problem_space_knowledge": 1085938728,
    "tech_comfort": 1439741479,
    "related_tools_used": 82933934,
    "one_sentence_pitch": 1934953822,
    "primary_target_audience": 1144200843,
    "expected_transformation": 362573784,
}


def generate_quantix_feedback(
    persona: Persona,
    metrics: SessionMetrics,
    telemetry: list[TelemetryEvent],
) -> QuantixFeedbackForm:
    """Synthesize complete Quantix Google Form response tailored to persona's experience."""

    # 1. Map Demographics based on persona profile
    if persona.technical_skill == TechnicalSkill.HIGH:
        primary_role = "Product/Engineering/Technical Lead"
        knowledge = "Expert/Power User: I have years of specialised experience and deep technical knowledge"
        tech_comfort = 5
        team_size = "11-50 people (Growing Team)"
        authority = "Influencer/Evaluator: I evaluate options and recommend them to my team/manager"
        tools_used = ["Specialised software in this category (eg direct competitor tools)", "Custom in house or manual scripts"]
        pitch = "A deterministic mathematical risk engine that eliminates emotional guesswork in portfolio positioning."
        transformation = "Automated ATR risk boundary computation integrated with my existing quantitative trading stack."
        urgency = "Important (Looking for a solution for this within the next 3 weeks)"
    elif persona.persona_id == "persona_marcus_exec" or "exec" in persona.persona_id or "vp" in persona.role.lower() or "founder" in persona.role.lower():
        primary_role = "Founder/Executive/C-Suite"
        knowledge = "Advanced/Practitioner: I do this regularly and know the industry best practices."
        tech_comfort = 4
        team_size = "11-50 people (Growing Team)"
        authority = "Sole Decison Maker: I decide and pay directly"
        tools_used = ["General productivity tools (eg Notion, Airtable, Excel, Google Sheets)", "Specialised software in this category (eg direct competitor tools)"]
        pitch = "An institutional-grade risk management platform that bridges market analysis and disciplined execution."
        transformation = "Capital preservation through strictly calculated risk parameters and automated draw-down defense."
        urgency = "Critical (Need an immediate solution within days)"
    elif persona.persona_id == "persona_sarah_smb" or "smb" in persona.persona_id or persona.technical_skill == TechnicalSkill.LOW:
        primary_role = "Individual Creator/Freelancer/Consultant"
        knowledge = "Beginner/Novice: I am just starting out and need a lot of guidance"
        tech_comfort = 2
        team_size = "Just me (Solo/Individual)"
        authority = "Sole Decison Maker: I decide and pay directly"
        tools_used = ["Spreadsheets/Manual notes", "None -- I currently have no structured workflows for this"]
        pitch = "A clean platform that helps traders calculate market risks without getting lost in complicated charts."
        transformation = "Stop blowing up trading accounts by having clear math-driven stop-loss boundaries."
        urgency = "Important (Looking for a solution for this within the next 3 weeks)"
    else:
        primary_role = "Operations/Finance/Administrative"
        knowledge = "Intermediate: I understand the core concepts and workflows reasonably well"
        tech_comfort = 3
        team_size = "2-10 people (Early Stage/Boutique)"
        authority = "Influencer/Evaluator: I evaluate options and recommend them to my team/manager"
        tools_used = ["General productivity tools (eg Notion, Airtable, Excel, Google Sheets)"]
        pitch = "A portfolio risk intelligence system for disciplined traders."
        transformation = "Systematic position sizing without second-guessing."
        urgency = "Low Priority (Nice to Have, exploring for future reference)"

    # 2. Section 1: Landing Page Evaluation
    if metrics.friction_score < 15:
        gut = ["Impressed/Professional", "Intruiged/Curious"]
        clarity_10_15s = 4 if persona.technical_skill != TechnicalSkill.LOW else 3
        visual_design = 5
        credibility = 5
        convincing_element = "The 'Math-Driven Risk Engine. Zero Discretionary Guesswork' heading and clean ATR envelopes."
        hesitation = "The initial hero view didn't show pricing immediately until I scrolled or clicked navbar."
    else:
        gut = ["Skeptical/Hesitant", "Confused/Overwhelmed"]
        clarity_10_15s = 2
        visual_design = 4
        credibility = 4
        convincing_element = "The promise of bridging analysis and execution without manual chart fatigue."
        hesitation = "The terminology is quite dense; wasn't immediately obvious whether it's an automated bot or decision support tool."

    # 3. Section 2 & 3: Signup & Intake
    signup_issues = "No, it worked flawlessly"
    has_rage = metrics.rage_clicks_total > 0
    if has_rage:
        signup_issues = "Encountered unclickable/unresponsive elements when attempting initial sandbox exploration."

    # 4. Section 4 & 5: Core Product & Emotion
    if metrics.task_success and metrics.friction_score < 20:
        dashboard_feeling = ["Validated/Understood", "Excited to explore further"]
        nav_rating = 4
        aha = "Reviewing the Scalp Specialist and Semi-Pro Swing breakdown stories in the portfolio section."
        sentiment = "Delighted/Empowered" if persona.patience != PatienceLevel.LOW else "Hopeful/Curious"
    elif metrics.task_success:
        dashboard_feeling = ["Relieved/Satisfied"]
        nav_rating = 3
        aha = "Seeing the 20% annual discount and structured pricing tiers."
        sentiment = "Hopeful/Curious"
    else:
        dashboard_feeling = ["Confused about what to do next", "Underwhelmed/Expected more depth"]
        nav_rating = 2
        aha = "Not yet -- trying to see the value"
        sentiment = "Frustated" if metrics.rage_clicks_total > 0 else "Anxious/Sceptical"

    # 5. Section 6: Friction & Missing Pieces
    if "launch" in [e.target_text.lower() for e in telemetry if e.target_text]:
        most_frustrating = (
            "Clicking 'Launch Pathfinder' does not trigger a visible registration modal or redirect; "
            "it remained on the page with a javascript placeholder link."
        )
    elif has_rage:
        most_frustrating = "Repeatedly clicking an element that looked like an active link or sandbox button with no response."
    else:
        most_frustrating = "Having to scroll several thousand pixels to compare the pricing tiers against the feature list."

    if persona.technical_skill == TechnicalSkill.HIGH:
        missing_feature = "Interactive REST API documentation and sandbox Webhook endpoints."
    elif persona.technical_skill == TechnicalSkill.LOW:
        missing_feature = "A 60-second video walkthrough showing the actual Pathfinder terminal UI."
    else:
        missing_feature = "A direct interactive risk calculator demo widget embedded right into the hero section."

    # 6. Section 7: Overall Satisfaction & PMF
    if metrics.task_success and metrics.friction_score < 15:
        nps = 9
        nps_reason = "Unique focus on deterministic mathematical risk rather than generic chatbot hype."
        pmf = "Very disappointed"
        magic_wand = "Provide an instant browser-based live demo without needing account registration."
    elif metrics.task_success:
        nps = 7
        nps_reason = "Solid mathematical value proposition, but needs clearer onboarding paths."
        pmf = "Somewhat disappointed"
        magic_wand = "Connect the 'Launch Pathfinder' CTA to an immediate interactive preview modal."
    else:
        nps = 4
        nps_reason = "Encountered confusion and lack of clear next steps after clicking primary buttons."
        pmf = "Not disappointed"
        magic_wand = "Fix dead links and simplify the initial hero section for non-expert traders."

    return QuantixFeedbackForm(
        session_id=metrics.session_id,
        persona_id=persona.persona_id,
        persona_name=persona.name,
        submitted_at=metrics.completed_at or "2026-09-24T00:00:00Z",
        gut_reaction=gut,
        clarity_10_15s=clarity_10_15s,
        visual_design=visual_design,
        credibility=credibility,
        convincing_element=convincing_element,
        hesitation_trigger=hesitation,
        signup_method="Email & Password",
        info_requested_feeling="Perfectly reasonable/minimal",
        signup_technical_issues=signup_issues,
        time_expected_vs_actual="Just right/As expected",
        relevance_rating=4,
        clarity_rating=clarity_10_15s,
        progression_rating=4,
        engagement_rating=4,
        comfort_answering_profile="100% comfortable; clear why each piece of data was needed",
        awkward_question="None",
        initial_dashboard_feeling=dashboard_feeling,
        navigating_intuitiveness=nav_rating,
        aha_moment=aha,
        speed_responsiveness=5,
        reliability=4 if not has_rage else 3,
        emotional_sentiment=sentiment,
        most_frustrating_moment=most_frustrating,
        missing_feature_expected=missing_feature,
        prior_alternative_used="Spreadsheets/Manual notes" if persona.technical_skill != TechnicalSkill.HIGH else "Custom in house or manual scripts",
        nps_recommendation=nps,
        nps_reason=nps_reason,
        pmf_feeling=pmf,
        magic_wand_change=magic_wand,
        primary_role=primary_role,
        discovery_source="Direct Link from an article, newsletter, or partner site",
        problem_urgency=urgency,
        team_size=team_size,
        role_in_selecting_tools=authority,
        problem_space_knowledge=knowledge,
        tech_comfort=tech_comfort,
        related_tools_used=tools_used,
        one_sentence_pitch=pitch,
        primary_target_audience="People exactly like me",
        expected_transformation=transformation,
    )


def build_google_form_payload(form: QuantixFeedbackForm) -> dict[str, Any]:
    """Map QuantixFeedbackForm fields to Google Form entry.XXXX parameter names."""
    payload: dict[str, Any] = {}
    data = form.model_dump()

    for field_name, entry_id in ENTRY_MAP.items():
        val = data.get(field_name)
        param_name = f"entry.{entry_id}"
        if isinstance(val, list):
            # For checkboxes, pass list or repeated keys
            payload[param_name] = val
        elif val is not None:
            payload[param_name] = str(val)

    return payload


def submit_to_google_form_http(form: QuantixFeedbackForm) -> tuple[bool, str]:
    """Send filled survey directly to Google Forms via HTTP POST.

    Returns (success_boolean, status_message).
    """
    payload = build_google_form_payload(form)
    # Form-encoded query string with repeated entries for lists
    query_parts: list[tuple[str, str]] = []
    for k, v in payload.items():
        if isinstance(v, list):
            for item in v:
                query_parts.append((k, str(item)))
        else:
            query_parts.append((k, str(v)))

    encoded = urllib.parse.urlencode(query_parts).encode("utf-8")
    req = urllib.request.Request(
        GOOGLE_FORM_POST_URL,
        data=encoded,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 302):
                return True, f"Google Form successfully submitted! Status: {resp.status}"
            return True, f"Google Form accepted with status {resp.status}"
    except urllib.error.HTTPError as he:
        # Google forms often returns 302 or 200; 400 means a field was rejected
        return False, f"HTTP Error {he.code}: {he.reason}"
    except Exception as exc:
        return False, f"Network submission error: {str(exc)}"


def fill_google_form_playwright(
    form: QuantixFeedbackForm,
    headless: bool = True,
    submit: bool = True,
) -> tuple[bool, str, str | None]:
    """Automate persona filling out the Google Form via headless/headed Playwright.

    Returns (success_boolean, message, screenshot_path).
    """
    from playwright.sync_api import sync_playwright
    from pathlib import Path
    import time

    screenshots_dir = Path(__file__).resolve().parent.parent.parent / "data" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot_path = str(screenshots_dir / f"gform_{form.session_id}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        try:
            page.goto(GOOGLE_FORM_VIEW_URL, wait_until="domcontentloaded", timeout=20000)
            time.sleep(1.0)

            # 1. Fill Text Inputs and Textareas
            text_mappings = [
                form.convincing_element,
                form.hesitation_trigger,
                form.awkward_question,
                form.most_frustrating_moment,
                form.missing_feature_expected,
                form.nps_reason,
                form.magic_wand_change,
                form.one_sentence_pitch,
                form.expected_transformation,
            ]
            inputs = page.locator('input[type="text"]:visible, textarea:visible').all()
            for idx, text_val in enumerate(text_mappings):
                if idx < len(inputs) and text_val:
                    try:
                        inputs[idx].fill(text_val)
                    except Exception:
                        pass

            # 2. Select matching choices
            choices_to_click = [
                form.signup_method,
                form.info_requested_feeling,
                form.signup_technical_issues,
                form.time_expected_vs_actual,
                form.comfort_answering_profile,
                form.emotional_sentiment,
                form.prior_alternative_used,
                form.pmf_feeling,
                form.primary_role,
                form.discovery_source,
                form.problem_urgency,
                form.team_size,
                form.role_in_selecting_tools,
                form.problem_space_knowledge,
                form.primary_target_audience,
            ]
            for choice in choices_to_click:
                if choice:
                    try:
                        # Locate radio or checkbox with matching label
                        loc = page.locator(f'div[role="radio"]:has-text("{choice[:25]}"), div[role="checkbox"]:has-text("{choice[:25]}"), span:has-text("{choice[:25]}")').first
                        if loc.count() > 0:
                            loc.click(timeout=1500)
                    except Exception:
                        pass

            # 3. Handle ratings (1-5, 0-10)
            ratings = [
                form.clarity_10_15s,
                form.visual_design,
                form.credibility,
                form.relevance_rating,
                form.clarity_rating,
                form.progression_rating,
                form.engagement_rating,
                form.navigating_intuitiveness,
                form.speed_responsiveness,
                form.reliability,
                form.nps_recommendation,
                form.tech_comfort,
            ]
            for r in ratings:
                try:
                    loc = page.locator(f'[data-value="{r}"]:visible').first
                    if loc.count() > 0:
                        loc.click(timeout=1000)
                except Exception:
                    pass

            time.sleep(1.0)
            page.screenshot(path=shot_path, full_page=False)

            if submit:
                submit_btn = page.locator('div[role="button"]:has-text("Submit"), span:has-text("Submit")').first
                if submit_btn.count() > 0:
                    submit_btn.click(timeout=3000)
                    time.sleep(2.0)
                    page.screenshot(path=shot_path, full_page=False)

            return True, "Persona successfully completed Google Form in Playwright browser.", shot_path
        except Exception as exc:
            return False, f"Playwright Google Form execution encountered error: {str(exc)}", None
        finally:
            context.close()
            browser.close()
