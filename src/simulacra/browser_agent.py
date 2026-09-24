"""Playwright-driven autonomous browser agent executing realistic persona behaviors."""

import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from src.simulacra.models import (
    ActionType,
    CampaignMission,
    ExitReason,
    Emotion,
    Persona,
    SessionMetrics,
    TelemetryEvent,
)
from src.simulacra.planner import (
    CognitivePlanner,
    PageObservation,
    PlannedDecision,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "screenshots"


class SimulatedUserAgent:
    """Executes a single synthetic user journey inside a Playwright browser."""

    def __init__(
        self,
        persona: Persona,
        mission: CampaignMission,
        campaign_id: str,
        on_event: Callable[[TelemetryEvent], None] | None = None,
    ) -> None:
        self.persona = persona
        self.mission = mission
        self.campaign_id = campaign_id
        self.session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.on_event = on_event
        self.planner = CognitivePlanner(persona, mission)
        self.telemetry_history: list[TelemetryEvent] = []
        self.pages_visited: set[str] = set()
        self.total_clicks = 0
        self.total_rage_clicks = 0
        self.total_hesitation_ms = 0
        self.task_success = False
        self.exit_reason = ExitReason.MAX_STEPS_REACHED

    def run_session(self) -> tuple[SessionMetrics, list[TelemetryEvent]]:
        """Launch browser, execute autonomous persona exploration loop, and capture telemetry."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc).isoformat()
        start_time_perf = time.perf_counter()

        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=self.mission.headless)
            context: BrowserContext = browser.new_context(
                viewport={
                    "width": self.persona.viewport_width,
                    "height": self.persona.viewport_height,
                },
                user_agent=self.persona.user_agent,
            )
            page: Page = context.new_page()

            # Set navigation timeout
            page.set_default_timeout(10000)

            try:
                # Initial navigation
                page.goto(self.mission.target_url, wait_until="domcontentloaded")
                self.pages_visited.add(page.url)

                step_number = 0
                while step_number < self.mission.max_steps:
                    step_number += 1

                    # 1. Observe current page state
                    observation = self._observe_page(page)

                    # 2. Plan cognitive decision
                    decision = self.planner.evaluate_step(
                        observation, self.telemetry_history
                    )

                    # 3. Capture screenshot if configured
                    screenshot_path: str | None = None
                    if self.mission.capture_screenshots and (
                        decision.is_terminal
                        or decision.action_type in (ActionType.RAGE_CLICK, ActionType.SUBMIT_FORM, ActionType.CLICK)
                        or step_number == 1
                    ):
                        file_name = f"{self.session_id}_step{step_number}.png"
                        target_file = SCREENSHOTS_DIR / file_name
                        try:
                            page.screenshot(path=str(target_file), full_page=False)
                            screenshot_path = str(target_file)
                        except Exception:
                            screenshot_path = None

                    # 4. Construct telemetry event
                    current_scroll_percent = 0.0
                    if observation.page_height > 0:
                        current_scroll_percent = min(
                            100.0,
                            round((observation.scroll_y / max(1, observation.page_height - observation.viewport_height)) * 100.0, 1),
                        )

                    event = TelemetryEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:12]}",
                        session_id=self.session_id,
                        step_number=step_number,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        page_url=page.url,
                        page_title=observation.title,
                        action_type=decision.action_type,
                        target_element=decision.target_selector,
                        target_text=decision.target_text,
                        scroll_depth_percent=current_scroll_percent,
                        hesitation_ms=decision.hesitation_ms,
                        rage_click_count=decision.rage_clicks,
                        emotion=decision.emotion,
                        confidence=decision.confidence,
                        cognitive_reasoning=decision.cognitive_reasoning,
                        screenshot_path=screenshot_path,
                    )

                    self.telemetry_history.append(event)
                    self.total_hesitation_ms += decision.hesitation_ms
                    self.total_rage_clicks += decision.rage_clicks
                    if decision.action_type in (ActionType.CLICK, ActionType.SUBMIT_FORM, ActionType.RAGE_CLICK):
                        self.total_clicks += 1

                    if self.on_event:
                        self.on_event(event)

                    # 5. Execute action in Playwright
                    if decision.is_terminal:
                        self.task_success = (decision.exit_reason == ExitReason.GOAL_COMPLETED)
                        self.exit_reason = decision.exit_reason or ExitReason.MAX_STEPS_REACHED
                        break

                    self._execute_action(page, decision)
                    self.pages_visited.add(page.url)

            except Exception as exc:
                self.exit_reason = ExitReason.SYSTEM_ERROR
                # Record exception event
                err_event = TelemetryEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    session_id=self.session_id,
                    step_number=len(self.telemetry_history) + 1,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    page_url=page.url if page else self.mission.target_url,
                    page_title="Error Encountered",
                    action_type=ActionType.ABANDON,
                    target_element=None,
                    target_text=None,
                    scroll_depth_percent=0.0,
                    hesitation_ms=0,
                    rage_click_count=0,
                    emotion=Emotion.FRUSTRATED,
                    confidence=0.0,
                    cognitive_reasoning=f"System or navigation failure encountered: {str(exc)}",
                    screenshot_path=None,
                )
                self.telemetry_history.append(err_event)
                if self.on_event:
                    self.on_event(err_event)
            finally:
                context.close()
                browser.close()

        duration = round(time.perf_counter() - start_time_perf, 2)
        completed_at = datetime.now(timezone.utc).isoformat()

        # Calculate friction score (0-100)
        # Factors: rage clicks (+25 each), hesitation time (>5000ms), low confidence, abandonment
        raw_friction = (self.total_rage_clicks * 25.0) + (self.total_hesitation_ms / 300.0)
        if not self.task_success:
            raw_friction += 30.0
        friction_score = min(100.0, round(raw_friction, 1))

        final_sentiment = self.telemetry_history[-1].emotion if self.telemetry_history else Emotion.NEUTRAL

        metrics = SessionMetrics(
            session_id=self.session_id,
            campaign_id=self.campaign_id,
            persona_id=self.persona.persona_id,
            persona_name=self.persona.name,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            total_steps=len(self.telemetry_history),
            pages_visited=len(self.pages_visited),
            total_clicks=self.total_clicks,
            rage_clicks_total=self.total_rage_clicks,
            hesitation_time_total_ms=self.total_hesitation_ms,
            friction_score=friction_score,
            task_success=self.task_success,
            exit_reason=self.exit_reason,
            final_sentiment=final_sentiment,
        )

        return metrics, self.telemetry_history

    def _observe_page(self, page: Page) -> PageObservation:
        """Extract interactive elements, text blocks, and state markers from the live DOM."""
        dom_script = """
        () => {
            const interactives = [];
            const headings = [];
            const formInputs = [];

            // Headings
            document.querySelectorAll('h1, h2, h3').forEach(h => {
                const text = h.innerText.trim();
                if (text) headings.push(text);
            });

            // Buttons, links, and clickable items
            document.querySelectorAll('a, button, input[type="submit"], [role="button"], .btn, .rage-target').forEach((el, idx) => {
                const text = (el.innerText || el.getAttribute('value') || '').trim();
                const id = el.id ? '#' + el.id : '';
                const tag = el.tagName.toLowerCase();
                const href = el.getAttribute('href') || '';
                const type = el.getAttribute('type') || '';
                const classes = el.className || '';
                let selector = id;
                if (!selector) {
                    if (tag === 'a' && href && !href.startsWith('javascript') && href !== '#') {
                        selector = `a[href="${href}"]`;
                    } else if (text) {
                        const cleanText = text.slice(0, 30).replace(/"/g, '\\"');
                        selector = `${tag}:has-text("${cleanText}")`;
                    } else {
                        selector = `${tag}:nth-of-type(${idx + 1})`;
                    }
                }
                interactives.push({
                    tag: tag,
                    text: text,
                    href: href,
                    type: type,
                    classes: classes,
                    selector: selector,
                    id: el.id
                });
            });

            // Form inputs
            document.querySelectorAll('input:not([type="submit"]):not([type="button"]):not([type="hidden"]), select, textarea').forEach(inp => {
                const name = inp.getAttribute('name') || inp.id || 'field';
                const id = inp.id ? '#' + inp.id : '';
                const type = inp.getAttribute('type') || 'text';
                const val = inp.value || '';
                formInputs.push({
                    name: name,
                    type: type,
                    selector: id || `input[name="${name}"]`,
                    filled: val.length > 0
                });
            });

            // Success / error markers
            const hasSuccess = document.querySelector('.success-banner, #success-container:not([style*="display: none"]), .badge-paid') !== null;
            const errorEl = document.querySelector('.error-banner:not([style*="display: none"])');
            const hasError = errorEl !== null;
            const errorText = errorEl ? errorEl.innerText.trim() : null;

            return {
                title: document.title,
                scroll_y: window.scrollY || 0,
                page_height: document.documentElement.scrollHeight || 800,
                viewport_height: window.innerHeight || 800,
                interactive_elements: interactives,
                headings: headings,
                form_inputs: formInputs,
                has_success_marker: hasSuccess,
                has_error_marker: hasError,
                error_text: errorText
            };
        }
        """
        data = page.evaluate(dom_script)
        return PageObservation(
            url=page.url,
            title=data.get("title", ""),
            scroll_y=data.get("scroll_y", 0),
            page_height=data.get("page_height", 800),
            viewport_height=data.get("viewport_height", 800),
            interactive_elements=data.get("interactive_elements", []),
            headings=data.get("headings", []),
            form_inputs=data.get("form_inputs", []),
            has_success_marker=data.get("has_success_marker", False),
            has_error_marker=data.get("has_error_marker", False),
            error_text=data.get("error_text"),
        )

    def _execute_action(self, page: Page, decision: PlannedDecision) -> None:
        """Perform browser action with realistic human jitter and timing."""
        # Simulated hesitation
        if decision.hesitation_ms > 0:
            time.sleep(min(decision.hesitation_ms / 1000.0, 1.5))

        if decision.action_type == ActionType.SCROLL_DOWN:
            page.evaluate(f"window.scrollBy({{ top: {decision.scroll_amount}, behavior: 'smooth' }});")
            time.sleep(0.3)

        elif decision.action_type == ActionType.SCROLL_UP:
            page.evaluate(f"window.scrollBy({{ top: -{decision.scroll_amount}, behavior: 'smooth' }});")
            time.sleep(0.3)

        elif decision.action_type in (ActionType.CLICK, ActionType.SUBMIT_FORM):
            if decision.target_selector:
                try:
                    locator = page.locator(decision.target_selector).first
                    locator.scroll_into_view_if_needed(timeout=3000)
                    time.sleep(random.uniform(0.1, 0.25))
                    locator.click(timeout=4000)
                    time.sleep(0.4)
                except Exception:
                    # Try clicking by text if CSS selector failed
                    if decision.target_text:
                        page.get_by_text(decision.target_text).first.click(timeout=3000)
                        time.sleep(0.4)

        elif decision.action_type == ActionType.FILL_INPUT:
            if decision.target_selector and decision.input_value:
                try:
                    locator = page.locator(decision.target_selector).first
                    locator.click(timeout=2000)
                    # Human typing with slight jitter
                    for char in decision.input_value:
                        locator.press_sequentially(char, delay=random.randint(25, 65))
                    time.sleep(0.2)
                except Exception:
                    pass

        elif decision.action_type == ActionType.RAGE_CLICK:
            if decision.target_selector:
                try:
                    locator = page.locator(decision.target_selector).first
                    locator.scroll_into_view_if_needed(timeout=2000)
                    # Rapid consecutive clicks
                    for _ in range(decision.rage_clicks or 3):
                        locator.click(timeout=1000)
                        time.sleep(0.08)
                except Exception:
                    pass
