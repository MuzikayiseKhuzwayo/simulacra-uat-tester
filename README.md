# Simulacra UAT — Autonomous User Simulation & Testing Platform

**Simulacra UAT** transforms acceptance testing from static test scripts into a **fleet of autonomous, persona-driven browser agents**. Instead of merely asserting selectors, synthetic customers with diverse technical proficiencies, patience levels, cognitive biases, and goals organically explore web applications, encounter friction, rage-click misleading elements, form opinions, and submit structured UX audits.

```
       Requirements / Goals
                │
                ▼
      ┌───────────────────┐
      │  Persona Engine   │ ◄── Archetypes: SMB Owner, Exec Buyer, Dev, QA, Mobile Consumer
      └─────────┬─────────┘
                │ Cohort & Behavioral Biases
                ▼
      ┌───────────────────┐
      │  Journey Planner  │ ◄── Cognitive Decision Loop (Emotion, Hesitation, Perception)
      └─────────┬─────────┘
                │ Human-like Actions (Jitter typing, scrolling, rage-clicks)
                ▼
      ┌───────────────────┐
      │ Browser Agent Pool│ ◄── Headless / Headed Playwright Execution
      └─────────┬─────────┘
                │
         Live Application
                │
                ▼
      ┌───────────────────┐
      │  Event Collector  │ ◄── High-Resolution Telemetry (Hesitations, Clicks, Inner Monologue)
      └─────────┬─────────┘
                │
                ▼
      ┌───────────────────┐
      │  Feedback Engine  │ ◄── SUS Score, CES Effort, NPS, Verbatim Persona Quotes
      └─────────┬─────────┘
                │
                ▼
      ┌───────────────────┐
      │ Executive Reports │ ◄── Markdown Synthesis, Excel Audit Workbook, Telemetry JSON
      └───────────────────┘
```

---

## 🎯 What Simulacra Solves

Traditional test automation checks whether code matches predefined acceptance criteria. However, acceptance criteria rarely catch:
- **Confusing hero messaging & value propositions**
- **Hidden friction on multi-step onboarding forms**
- **Dead-end navigation paths and layout shifts**
- **Interactive elements that look clickable but fail to respond (triggering rage clicks)**
- **Demographic drop-offs (e.g. low-tech users abandoning vs technical users succeeding)**

Simulacra bridges QA engineering with **autonomous UX research**, simulating real human customer behavior at scale.

---

## 🌟 Core Platform Capabilities

1. **Synthetic Persona Archetypes & Dynamic Generator (`src/simulacra/persona.py`)**:
   - `Sarah Jenkins` (Small Business Owner): Low tech, low patience, hates complex multi-step forms, expects single-click paths.
   - `Marcus Vance` (Enterprise VP): Medium tech, low patience, scans for transparent pricing & ROI, avoids demo sales calls.
   - `Priya Sharma` (Senior Developer): High tech, high patience, inspects technical documentation, tests form boundaries.
   - `Carl Miller` (Retired Accountant): Low tech, medium patience, reads terms cautiously, sensitive to low visual contrast.
   - `Maya Lin` (Mobile Consumer): Medium tech, low patience, scrolls fast on mobile viewports, rage-clicks unresponsive targets.
   - `David O'Connor` (Accessibility Auditor): High tech, audits error boundaries, keyboard focus, and missing feedback.
   - **Algorithmic Cohort Generator**: Generate cohorts of 1 to 100 parameterized synthetic users on demand.

2. **Cognitive Journey Planner & Inner Monologue (`src/simulacra/planner.py`)**:
   - Evaluates live DOM accessibility trees, interactive buttons, inputs, links, and banners.
   - Models human psychological states: `neutral` → `curious` → `confident` → `satisfied` or `hesitant` → `confused` → `frustrated` → `abandoned`.
   - Records authentic first-person inner monologues explaining *why* the persona hesitates, clicks, or leaves.

3. **Playwright Autonomous Browser Agent (`src/simulacra/browser_agent.py`)**:
   - Natural human typing with delay jitter (25–65ms per stroke).
   - Smooth mouse scrolling and reading pauses scaled to content length.
   - High-fidelity milestone screenshot capture saved locally for visual inspection.

4. **High-Resolution Telemetry Datastore (`src/simulacra/database.py`)**:
   - SQLite relational schema (`campaigns`, `personas`, `agent_sessions`, `telemetry_events`, `session_feedback`, `uat_reports`).
   - Compliant with **Systems Engineering Anti-Mirage Invariant 3 & 4** (verified live datastore writes and DDL migrations).

5. **Post-Session UX Survey & Sentiment Engine (`src/simulacra/feedback.py`)**:
   - **SUS Score** (System Usability Scale: 0–100).
   - **CES Score** (Customer Effort Score: 1–7).
   - **NPS Rating** (Net Promoter Score: 0–10).
   - Verbatim persona critiques and prioritized usability recommendations.

6. **Executive Synthesis & Multi-Format Reporting (`src/simulacra/reporting.py`)**:
   - Auto-generates GitHub-Flavored Markdown executive briefs.
   - Exports multi-tab Excel workbooks (`Summary`, `Sessions`, `Feedback`, `Telemetry`).
   - Exports machine-readable JSON telemetry packs.

7. **Built-in Mock Test Application (`src/simulacra/mock_app.py`)**:
   - A multi-page local web application (`http://127.0.0.1:8585`) featuring landing page, pricing plans, registration, invoice dashboard, and intentional UX friction traps for offline testing.

8. **Preserved TestPack Design Agent**:
   - Retains the deterministic requirement analysis and test case generation subsystem from the original POC.

---

## 🚀 Quickstart

### 1. Installation

Ensure Python 3.11+ and Playwright are installed:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Launch the Next.js Enterprise UAT Platform (Recommended)

Start both the **FastAPI Backend (port 8000)** and **Next.js 15 Web App (port 3000)** with one command:

```bash
python run_dev.py
```

- **Frontend**: [http://localhost:3000](http://localhost:3000) (Next.js 15, React 19, Tailwind CSS, SSE real-time streaming)
- **Backend API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (FastAPI Swagger UI)

You can also run them independently:
```bash
# Terminal 1: Backend
python run_api.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

*(Note: The legacy Streamlit prototype is still available via `streamlit run app.py` on port 8501).*

### 3. Run Headless Simulation via CLI

Launch a simulated testing campaign directly from terminal or CI/CD:

```bash
# Test against built-in local demo application with 3 synthetic users
python -m src.simulacra.cli --personas 3 --title "Smoke Test Campaign"

# Test an external or local application
python -m src.simulacra.cli --url "https://my-app.com" --goal "Browse catalog and complete checkout" --personas 5
```

### 4. Run Automated Test Suite

```bash
pytest -v
```

99 automated tests with zero warnings covering Pydantic contracts, FastAPI endpoints, SQLite transactions, cognitive planning, Playwright browser interactions, and report generation.

---

## 📊 Sample Executive Telemetry Scorecard

| Metric | Result | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Task Success Rate** | **100.0%** (2/2) | ≥ 80.0% | ✅ Pass |
| **Average Usability (SUS)** | **84.3 / 100** | ≥ 68.0 (Grade B) | ✅ Good |
| **Average Friction Score** | **2.1 / 100** | ≤ 30.0 | ✅ Low |
| **Total Rage Clicks** | **0** | 0 | ✅ Zero |

### Verbatim Persona Insight:
> *"I was able to create an account and get straight into the invoice dashboard. The navigation is intuitive and didn't make me jump through unnecessary hoops."* — **Sarah Jenkins (Small Business Owner)**

---

## 🛠️ Repository Architecture

```text
simulacra-uat-tester/
├── app.py                             # Full-featured Streamlit UI (5 integrated tabs)
├── database/
│   └── migrations/
│       └── 20260924_init_simulacra_schema.sql  # DDL migration with rollback block
├── src/
│   ├── simulacra/
│   │   ├── __init__.py                # Package exports
│   │   ├── models.py                  # Pydantic strict contracts
│   │   ├── persona.py                 # Archetypes & cohort generator
│   │   ├── mock_app.py                # Built-in multi-page demo app
│   │   ├── planner.py                 # Cognitive journey planner & friction model
│   │   ├── browser_agent.py           # Playwright autonomous browser agent
│   │   ├── telemetry.py               # Telemetry collection utilities
│   │   ├── feedback.py                # Synthetic SUS survey & verbatim quotes
│   │   ├── reporting.py               # Markdown, JSON, and Excel workbook exports
│   │   ├── runner.py                  # Campaign orchestration engine
│   │   ├── database.py                # SQLite repository & Invariant 3 verification
│   │   └── cli.py                     # Headless command-line runner
│   ├── agent_service.py               # (Legacy) Ollama requirement analysis service
│   ├── schemas.py                     # (Legacy) Requirement contracts
│   └── workflow.py                    # (Legacy) TestPack generation workflow
├── tests/
│   ├── test_simulacra_models.py       # Pydantic model contract tests
│   ├── test_simulacra_database.py     # SQLite persistence & Invariant 3 tests
│   ├── test_simulacra_persona.py      # Persona generation tests
│   ├── test_simulacra_planner.py      # Cognitive decision tests
│   ├── test_simulacra_feedback.py     # Survey & SUS scoring tests
│   ├── test_simulacra_integration.py  # Playwright E2E integration test
│   └── ...                            # Legacy 78 test suite
└── requirements.txt
```

---

## 📜 License

MIT License. Built for rigorous autonomous software verification and synthetic customer research.