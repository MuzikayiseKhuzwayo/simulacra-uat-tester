# 08 — Technical Implementation Plan

## 1. Purpose of this plan

The solution architecture explains the components and their responsibilities. This implementation plan converts that design into a safe build order.

Each increment must:

- produce a small working result;
- have an objective way to verify it;
- preserve the human-review gate;
- keep model reasoning separate from deterministic validation; and
- avoid adding infrastructure that the POC does not need.

The result will be a vertical prototype that accepts a requirement, analyses it, pauses for clarification, generates structured UAT tests, validates coverage and exports a reviewed CSV file.

## 2. Technical baseline

| Area | POC choice | Purpose |
|---|---|---|
| Runtime | Python 3.11 or 3.12 | Application language |
| User interface | Streamlit | Forms, review screens, editable test table and download |
| Agent orchestration | OpenAI Agents SDK | Agent instructions, runs and typed results |
| Data contracts | Pydantic | Input, analysis and test-pack validation |
| Data processing | Pandas | Tabular transformation and CSV export |
| Configuration | `python-dotenv` and environment variables | Local API-key configuration without committing secrets |
| Automated tests | Pytest | Unit and integration checks |
| Source control | Git and GitHub | Version history, documentation and review |

Exact compatible dependency versions will be recorded in `requirements.txt` after the first successful local installation. This avoids selecting version numbers that have not been tested together.

## 3. Proposed project structure

```text
testscope-ai-uat-agent/
├── app.py
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── assets/
├── data/
│   └── sample_requirement.json
├── docs/
├── prompts/
│   ├── analyse_requirement.md
│   └── generate_test_cases.md
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   ├── agent_service.py
│   ├── validators.py
│   ├── coverage.py
│   ├── workflow.py
│   └── exporter.py
└── tests/
    ├── test_schemas.py
    ├── test_validators.py
    ├── test_coverage.py
    ├── test_workflow.py
    └── test_exporter.py
```

### Why this structure?

- `app.py` is only the Streamlit presentation layer.
- `src/` contains reusable application logic independent of the interface.
- `prompts/` keeps agent behaviour visible and version-controlled.
- `data/` holds synthetic examples, never confidential requirements.
- `tests/` mirrors the deterministic application modules.
- `docs/` records the product and engineering decisions.

This separation lets us test schemas, validation and workflow logic without launching Streamlit or making a real model call.

## 4. Ordered implementation increments

### Increment 1 — Repository and environment scaffold

**Files**

- `.gitignore`
- `.env.example`
- `requirements.txt`
- `src/__init__.py`
- `src/config.py`
- empty `tests/` package structure

**Build**

1. Create a Python virtual environment.
2. Add the minimum application and test dependencies.
3. Add `.env` to `.gitignore`.
4. Put only an example key name such as `OPENAI_API_KEY=` in `.env.example`.
5. Read configuration from environment variables and fail with a clear message when required configuration is absent.

**Why first?**

Every later component needs a repeatable runtime and safe secret handling.

**Verification**

- a clean environment can install `requirements.txt`;
- importing `src` succeeds;
- `.env` is ignored by Git; and
- no real key appears in tracked files.

**Definition of done**

Another developer can clone the repository, create the environment and run the test command without guessing the setup.

---

### Increment 2 — Pydantic data contracts

**Files**

- `src/schemas.py`
- `tests/test_schemas.py`

**Build**

Implement the structures in `docs/05-output-schema.md`:

- requirement and acceptance-criterion models;
- requirement-analysis models;
- assumption, ambiguity, rule and risk models;
- test-case and test-step models;
- coverage model;
- final test-pack model; and
- enums for controlled values.

Add model-level checks for values that are always invalid, for example:

- blank identifiers;
- no acceptance criteria;
- duplicate acceptance-criterion IDs;
- step numbers below one; and
- empty test steps.

**Why before the agent?**

The agent, workflow, user interface, validator and exporter must agree on one data contract. Building this contract first prevents unstructured output from becoming the application design.

**Verification**

- valid example objects are accepted;
- missing required fields are rejected;
- unsupported enum values are rejected;
- duplicate criterion IDs are rejected; and
- models can be serialised to JSON and restored without data loss.

**Definition of done**

`pytest tests/test_schemas.py` passes and the sample object matches the documented schema.

---

### Increment 3 — Synthetic sample fixture

**Files**

- `data/sample_requirement.json`
- optional `data/expected_analysis.json`

**Build**

Convert the banking example in `docs/04-sample-requirement.md` into valid `RequirementInput` JSON. Keep ambiguities in the requirement because they are needed to demonstrate Run A.

**Why now?**

One stable input lets us test every later layer against the same business scenario and compare changes between runs.

**Verification**

- Pydantic loads the JSON successfully;
- every criterion has a unique ID; and
- the fixture contains only synthetic information.

**Definition of done**

The sample can be loaded with one command and produces a valid `RequirementInput`.

---

### Increment 4 — Deterministic validation and coverage

**Files**

- `src/validators.py`
- `src/coverage.py`
- `tests/test_validators.py`
- `tests/test_coverage.py`

**Build**

Implement pure Python functions for:

- unique test IDs;
- valid requirement references;
- valid criterion references;
- sequential step numbering;
- non-empty expected results;
- valid assumption references;
- acceptance-criterion coverage;
- test totals by type;
- high-risk test identification;
- missing negative-test warnings; and
- boundary-test warnings when a numerical limit is present.

Return blocking errors separately from non-blocking warnings.

**Why not ask the model to validate its own output?**

IDs, references, step order and coverage arithmetic are objective rules. Normal Python makes them repeatable, inexpensive and easy to unit test.

**Verification**

Use hand-written valid and invalid test packs. Confirm that:

- invalid references create blocking errors;
- uncovered criteria are calculated correctly;
- coverage percentage is reproducible;
- warnings do not incorrectly block review; and
- 100% coverage is reported only when every criterion has a valid mapped test.

**Definition of done**

All validation and coverage tests pass without an API key or model call.

---

### Increment 5 — Agent prompts and service

**Files**

- `prompts/analyse_requirement.md`
- `prompts/generate_test_cases.md`
- `src/agent_service.py`
- agent-service tests using fakes or mocks

**Build**

Create one logical **Senior UAT Test Lead** specialist with two bounded operations:

1. `analyse_requirement(requirement) -> RequirementAnalysis`
2. `generate_test_cases(context) -> list[TestCase]`

Run A instructions must:

- use only supplied facts;
- separate explicit rules from ambiguities;
- create specific clarification questions;
- label proposed assumptions; and
- identify business risks with rationale.

Run B instructions must:

- use the original requirement and reviewed Run A decisions;
- map every test to criterion IDs;
- create positive, negative, boundary and end-to-end cases where relevant;
- reference assumptions explicitly; and
- mark affected tests `Needs Clarification` when information remains unresolved.

Use typed outputs based on the Pydantic models. Capture useful run metadata such as duration and errors, but never log secrets or confidential requirement text.

**Why two runs?**

Generating tests immediately can hide missing rules inside plausible-looking scenarios. The separate analysis run makes uncertainty visible before generation.

**Verification**

- each operation returns the expected typed model;
- malformed model output is reported clearly;
- an API failure does not destroy previous workflow data; and
- the banking fixture produces visible ambiguities before test generation.

**Definition of done**

Both operations work from a small command-line script and their outputs pass Pydantic validation.

---

### Increment 6 — Workflow controller and human gate

**Files**

- `src/workflow.py`
- `tests/test_workflow.py`

**Build**

Implement the states documented in `docs/06-solution-architecture.md` and explicit transition functions such as:

- submit requirement;
- start and complete analysis;
- record an answer;
- approve or reject an assumption;
- confirm readiness for generation;
- start and complete generation;
- validate the test pack; and
- mark export.

The controller must prevent:

- generation before analysis;
- generation before review decisions are captured;
- treating an unresolved ambiguity as a confirmed rule; and
- export when blocking structural errors exist.

**Why is this application code rather than agent logic?**

The workflow represents product policy. The model may suggest content, but it must not decide whether mandatory human approval can be skipped.

**Verification**

- valid transitions succeed;
- invalid transitions fail with understandable messages;
- unresolved decisions remain visible; and
- recoverable failures return to the last safe state.

**Definition of done**

The complete workflow can be exercised in tests with fake agent outputs and no Streamlit interface.

---

### Increment 7 — Command-line vertical slice

**Files**

- a small `scripts/run_sample.py` or equivalent development entry point

**Build**

Connect:

1. sample input;
2. Run A;
3. terminal display of questions;
4. temporary user answers;
5. Run B;
6. deterministic validation; and
7. JSON result display.

**Why build a CLI before the UI?**

It proves the core application flow independently of screen state and layout. If a failure occurs, we know it is in the workflow rather than Streamlit.

**Verification**

Run the banking example end to end and retain one redacted example result for comparison.

**Definition of done**

One command completes the workflow and produces a valid test pack or a clear recoverable error.

---

### Increment 8 — Streamlit interface

**Files**

- `app.py`
- optional UI helper module

**Build**

Create four user-facing stages:

1. **Requirement input** — metadata, user story and acceptance criteria.
2. **Analysis review** — rules, risks, questions and proposed assumptions.
3. **Test-pack review** — editable structured test cases plus warnings and coverage.
4. **Export** — download the reviewed data.

Use Streamlit session state to retain the current workflow object between reruns. Use forms and deliberate action buttons so that editing a field does not unintentionally start an agent run.

**Why Streamlit?**

It provides enough interaction for a credible POC while allowing the Python validation and workflow modules to remain unchanged.

**Verification**

- users cannot skip required stages;
- repeated button clicks do not create accidental duplicate runs;
- errors are readable and recoverable;
- test rows can be reviewed and edited; and
- session-state changes match controller state.

**Definition of done**

A user can complete the full banking scenario through the browser without using the terminal.

---

### Increment 9 — CSV export

**Files**

- `src/exporter.py`
- `tests/test_exporter.py`

**Build**

Flatten each structured test case into a consistent CSV row. Decide how list fields are represented, for example:

- criterion IDs separated by semicolons;
- preconditions and data separated by line breaks;
- numbered steps combined into one readable cell; and
- assumption IDs preserved for traceability.

Export only the reviewed in-memory data; do not call the model during export.

**Verification**

- all test cases are exported;
- IDs and special characters survive correctly;
- edited values appear in the file;
- column order is stable; and
- the file opens correctly in a spreadsheet application.

**Definition of done**

The Streamlit download produces a valid, readable CSV test pack.

---

### Increment 10 — Evaluation and resilience

**Files**

- `evaluation/benchmark_requirements.json`
- `evaluation/evaluation_rubric.md`
- additional automated and manual tests

**Build**

Add a small benchmark containing different requirement types:

- numerical boundary;
- missing business rule;
- negative permission scenario;
- end-to-end workflow; and
- requirement with no ambiguity.

Score results for:

- criterion traceability;
- hallucinated or unsupported rules;
- useful ambiguity detection;
- required test-type coverage;
- expected-result clarity; and
- duplicate or redundant tests.

Also test invalid input, timeouts, malformed outputs and safe retry behaviour.

**Verification**

Record baseline results and manually review model quality. Deterministic checks should remain stable across repeated runs even when test wording varies.

**Definition of done**

The repository contains a repeatable evaluation method, known limitations and a documented POC result.

---

### Increment 11 — Packaging and demonstration

**Files**

- final README setup and usage instructions;
- screenshots or short demo media;
- deployment configuration if required; and
- final interview guide updates.

**Build**

- document installation and execution;
- document security and privacy limitations;
- deploy only after local acceptance testing;
- record the exact tested dependency versions; and
- revisit `docs/07-architecture-interview-guide.md` using evidence from the completed implementation.

**Definition of done**

A reviewer can understand, run and evaluate the POC from the repository instructions.

## 5. Testing strategy

| Test level | What it proves | Real model call? |
|---|---|---:|
| Schema unit tests | Data contracts reject malformed data | No |
| Validator unit tests | IDs, references and structural rules are correct | No |
| Coverage unit tests | Traceability calculations are reproducible | No |
| Workflow tests | Human gate and state transitions cannot be bypassed | No |
| Agent-service tests | Typed response and failure handling work | Mocked by default |
| Prompt benchmark | The model finds gaps and generates useful UAT tests | Yes |
| UI smoke test | A user can complete the intended journey | Yes |
| Export tests | Reviewed structured data becomes a stable CSV | No |

Most tests should be deterministic and free. Real model calls are reserved for the prompt benchmark and end-to-end demonstration.

## 6. POC-wide definition of done

Version 1 is complete when:

- a tester can enter one requirement with acceptance criteria;
- Run A displays rules, risks, ambiguities and clarification questions;
- the workflow pauses for human decisions;
- Run B generates schema-valid UAT tests;
- every test has traceability to requirement and criterion IDs;
- deterministic validation reports blocking errors and quality warnings;
- coverage is calculated from valid mappings rather than model claims;
- users can review and edit the test pack;
- users can download a CSV;
- automated tests pass;
- the sample contains no confidential information;
- no API key is committed; and
- setup, limitations and evaluation results are documented.

## 7. Main risks and controls

| Risk | Control |
|---|---|
| Model invents missing business rules | Separate ambiguity detection, human review and explicit assumption status |
| Output shape varies | Pydantic typed outputs and structural validation |
| Model reports false coverage | Calculate coverage in Python from criterion mappings |
| UI reruns duplicate model calls | Controller state, forms and guarded action buttons |
| Prompt changes reduce quality | Version-controlled prompts and benchmark fixtures |
| API failure loses user work | Preserve last safe workflow state and show recoverable errors |
| Secrets enter Git history | Environment variables, `.env.example`, `.gitignore` and repository scan |
| POC becomes over-engineered | No database, retrieval system or external test-management integration in Version 1 |

## 8. Recommended build order

The increments should be completed in this dependency order:

1. scaffold and configuration;
2. schemas;
3. sample fixture;
4. validation and coverage;
5. agent service;
6. workflow controller;
7. command-line vertical slice;
8. Streamlit interface;
9. export;
10. evaluation; and
11. packaging and demonstration.

The first coding task is therefore:

> Create the repository scaffold, then implement `src/schemas.py` and `tests/test_schemas.py`.

This gives the project a stable contract before any prompt, agent call or screen is built.
