# 06 — Solution Architecture

## 1. Architecture objective

The architecture must support a small, explainable and testable POC that:

- accepts one business requirement;
- analyses ambiguity before generating tests;
- pauses for human clarification;
- generates structured UAT test cases;
- validates coverage using deterministic Python rules;
- allows human review and editing; and
- exports the final test pack.

The first version uses a **bounded two-stage agent workflow**. It does not require autonomous multi-agent handoffs, external system integrations or persistent databases.

## 2. Core design statement

> TestScope AI combines AI-based requirement reasoning with schema-controlled outputs, deterministic quality checks and mandatory human review to generate a traceable first draft of a UAT test pack.

## 3. Architecture decisions

| Decision | Selected approach | Reason |
|---|---|---|
| Agent design | One UAT specialist persona used across two controlled runs | Keeps the POC understandable while supporting analysis before generation |
| Stage 1 | Requirement analysis | Identifies uncertainty before test cases are created |
| Stage 2 | Test generation | Uses requirement data plus confirmed answers and approved assumptions |
| AI framework | OpenAI Agents SDK for Python | Supports agent instructions, typed outputs, guardrails, runtime state and tracing |
| Output control | Pydantic models through the agent `output_type` | Produces predictable Python objects rather than unstructured text |
| Workflow control | Deterministic Python controller | Keeps state transitions and business approvals outside model control |
| Validation | Python rule engine | Ensures coverage calculations and structural checks are reproducible |
| User interface | Streamlit | Provides a fast interactive POC with forms, tables and downloads |
| State | Streamlit session state | Avoids a database during the POC |
| Export | Pandas to CSV initially | Produces a familiar and portable test pack |
| Human review | Mandatory between analysis and generation | Prevents the model from silently resolving business ambiguity |

## 4. Logical architecture

![TestScope AI solution architecture](../assets/testscope-ai-solution-architecture.svg)

The numbered path in the diagram represents the main workflow:

1. The Tester or Business Analyst provides the requirement.
2. The Streamlit interface submits validated input to the workflow controller.
3. The controller starts requirement analysis.
4. The analysis is presented at the human-review gate.
5. Confirmed answers and approved assumptions are used for test generation.
6. The generated test cases pass through schema validation.
7. The quality engine calculates traceability and coverage before presenting the editable test pack.
8. Only reviewed structured data is exported.

## 5. Component responsibilities

### 5.1 Streamlit user interface

The interface is responsible for:

- collecting requirement metadata, user story and acceptance criteria;
- displaying extracted business rules and risks;
- displaying clarification questions;
- accepting stakeholder answers or assumption approvals;
- displaying editable test cases;
- displaying coverage and validation warnings; and
- providing export buttons.

The interface does not calculate coverage or decide whether a business assumption is correct.

### 5.2 Workflow controller

The workflow controller is the trusted application layer. It is responsible for:

- validating the initial form;
- creating the agent input;
- starting requirement analysis;
- pausing for human review;
- combining stakeholder answers with the original requirement;
- starting test generation;
- invoking deterministic validators;
- controlling state transitions;
- preventing export when essential data is structurally invalid; and
- handling API and validation errors.

The model cannot bypass this controller.

### 5.3 Schema layer

Pydantic models provide the data contract defined in `05-output-schema.md`.

The schema layer includes:

- `RequirementInput`;
- `AcceptanceCriterion`;
- `RequirementAnalysis`;
- `Ambiguity`;
- `Assumption`;
- `BusinessRisk`;
- `TestCase`;
- `TestStep`;
- `CoverageSummary`; and
- `TestPack`.

These models are shared by the user interface, agent service, validation engine, tests and exporter.

### 5.4 Agent service

The agent service owns one logical specialist persona:

> Senior UAT Test Lead specialising in requirement analysis, business-risk identification, traceability and test design.

It performs two separate runs with stage-specific instructions and typed outputs.

#### Run A — Requirement analysis

Input:

- original requirement;
- acceptance criteria;
- known context; and
- known risks.

Typed output:

- requirement summary;
- extracted rules;
- ambiguities;
- clarification questions;
- proposed assumptions; and
- business risks.

#### Run B — Test generation

Input:

- original requirement;
- Run A analysis;
- stakeholder answers;
- approved assumptions; and
- required test categories.

Typed output:

- structured UAT test cases.

Version 1 will not use handoffs to other agents. We can introduce specialist agents later only if a genuinely different capability, tool or approval policy is required.

### 5.5 Human-review gate

After Run A, the workflow pauses.

For each ambiguity, the tester can:

1. provide a stakeholder answer;
2. approve a documented temporary assumption; or
3. leave it unresolved.

Unresolved items remain visible. Any affected test case must be marked `Needs Clarification`; the agent must not convert uncertainty into a confirmed fact.

### 5.6 Validation and coverage engine

The quality engine is standard Python code, not model reasoning.

It checks:

- required fields;
- unique IDs;
- permitted enum values;
- valid requirement and acceptance-criterion references;
- sequential test steps;
- non-empty expected results;
- valid assumption references;
- acceptance-criterion coverage;
- correctness of coverage percentage;
- presence of negative tests; and
- presence of boundary tests when numerical limits exist.

The engine returns:

- blocking validation errors;
- non-blocking quality warnings; and
- the calculated `CoverageSummary`.

### 5.7 Session-state manager

For the POC, Streamlit session state stores:

- requirement input;
- current workflow state;
- requirement analysis;
- clarification answers;
- assumption decisions;
- generated test cases;
- edited test cases;
- coverage results; and
- error messages.

Refreshing or closing the session may remove this data. Persistent project storage is out of scope for Version 1.

### 5.8 Export service

The export service converts validated test cases into:

- CSV in Version 1; and
- formatted Excel in a later increment.

Export logic does not call the model. It uses the reviewed structured data held by the application.

## 6. End-to-end processing flow

| Step | Actor or component | Action | Result |
|---:|---|---|---|
| 1 | Tester | Enters requirement and acceptance criteria | Draft requirement input |
| 2 | Streamlit and workflow controller | Validate required input fields | Valid `RequirementInput` |
| 3 | Agent Run A | Analyse rules, gaps, questions and risks | Typed `RequirementAnalysis` |
| 4 | Tester | Answer questions or decide on proposed assumptions | Reviewed clarification decisions |
| 5 | Agent Run B | Generate risk-based UAT scenarios | Typed test cases |
| 6 | Schema validator | Check required fields, types, IDs and references | Structurally valid output or errors |
| 7 | Coverage engine | Calculate coverage and quality warnings | Reviewable `TestPack` |
| 8 | Tester and exporter | Edit, approve and download results | CSV test pack |

## 7. Workflow states

| State | Meaning | Allowed next state |
|---|---|---|
| `DRAFT` | User is entering the requirement | `INPUT_VALIDATED` |
| `INPUT_VALIDATED` | Required input passed structural checks | `ANALYSING` |
| `ANALYSING` | Run A is in progress | `AWAITING_REVIEW` or `ERROR` |
| `AWAITING_REVIEW` | Questions and assumptions require human action | `READY_TO_GENERATE` |
| `READY_TO_GENERATE` | Human decisions have been captured | `GENERATING` |
| `GENERATING` | Run B is in progress | `VALIDATING` or `ERROR` |
| `VALIDATING` | Deterministic checks are running | `READY_FOR_REVIEW` or `NEEDS_CORRECTION` |
| `NEEDS_CORRECTION` | Blocking structural problems exist | `GENERATING` or `READY_FOR_REVIEW` after correction |
| `READY_FOR_REVIEW` | Test pack is editable and reviewable | `EXPORTED` |
| `EXPORTED` | User downloaded the test pack | `READY_FOR_REVIEW` |
| `ERROR` | A recoverable failure occurred | Previous safe state |

## 8. Validation and correction strategy

The architecture distinguishes between two error types:

### Structural error

Examples:

- invalid JSON or typed output;
- missing required field;
- duplicate ID;
- unknown acceptance-criterion reference.

The application may retry the failed agent run once with the validation error included. If it fails again, the user receives a recoverable error and the previous state is retained.

### Business ambiguity

Examples:

- unclear daily-limit interpretation;
- unspecified payment-reference rules;
- undefined overdraft behaviour.

These are never automatically repaired. They return to the human-review gate.

## 9. Proposed project structure

```text
testscope-ai-uat-agent/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
│
├── docs/
│   └── ...
│
├── src/
│   ├── config.py
│   ├── schemas.py
│   ├── workflow.py
│   ├── state.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── test_design_agent.py
│   │   └── prompts.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── validation.py
│       ├── coverage.py
│       └── exporter.py
│
├── sample_data/
│   └── banking_requirement.json
│
└── tests/
    ├── test_schemas.py
    ├── test_validation.py
    ├── test_coverage.py
    └── evaluation_cases.json
```

## 10. Security and privacy

- Store the API key in an environment variable or Streamlit secret.
- Commit only `.env.example`; never commit `.env`.
- Use synthetic requirements during development and demonstration.
- Do not log API keys or complete confidential requirements.
- Display safe error messages without secret or stack-trace exposure.
- Apply request-size and output-size limits.
- Keep export generation in trusted application code.

## 11. Observability and evaluation

The POC should capture:

- run ID;
- workflow stage;
- elapsed time;
- success or failure;
- validation errors;
- number of generated tests;
- coverage percentage; and
- human quality score during evaluation.

The Agents SDK supports tracing of model calls, tool calls, handoffs and guardrails. Tracing should be used only with synthetic or approved data and reviewed before any use with sensitive requirements.

## 12. Failure handling

| Failure | Application behaviour |
|---|---|
| Missing input | Show field-level validation message |
| API timeout | Preserve input and allow retry |
| Agent output fails schema | Retry once, then show recoverable error |
| Unresolved ambiguity | Mark affected tests `Needs Clarification` |
| Coverage gap | Display warning and uncovered criterion IDs |
| Export error | Keep reviewed results and allow another attempt |

## 13. Deployment view

### Local development

- Streamlit application runs on the developer's machine.
- Secrets remain in local environment variables.
- No database is required.

### POC deployment

- Deploy the Streamlit application to a controlled hosting environment.
- Store the API key in the platform's secret manager.
- Use synthetic demonstration requirements.
- Add basic authentication only if the deployment is not intended to be public.

Production identity, audit, persistent storage and enterprise integrations remain outside Version 1.

## 14. Why this architecture is appropriate

This design is suitable for the POC because it:

- keeps the workflow understandable;
- gives the agent meaningful reasoning responsibility;
- keeps deterministic calculations in Python;
- makes uncertainty visible;
- includes a genuine human-in-the-loop decision;
- supports typed, editable and exportable results;
- can be unit-tested without calling the model for every rule; and
- can later evolve toward Jira integration, file ingestion, execution tools or specialist agents.

## 15. Step 3 completion criteria

The architecture is approved when:

- each component has one clear responsibility;
- the two agent stages and human-review gate are agreed;
- the data flow matches the Step 2 schema;
- deterministic and model responsibilities are separated;
- workflow states and failure handling are understood; and
- the proposed project structure is accepted for implementation.
