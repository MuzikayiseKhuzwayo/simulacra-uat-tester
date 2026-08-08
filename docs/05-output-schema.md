# 05 — Input and Output Schema

## Why a schema is required

An unrestricted language-model response may contain useful ideas but vary in wording and structure between runs. TestScope AI needs predictable data so that it can validate coverage, display an editable table and export a reusable test pack.

The schema therefore acts as a contract between the user interface, agent, validator and exporter.

## Design principles

- Every acceptance criterion receives a stable ID.
- Facts, questions and assumptions are stored separately.
- Every test case maps to one or more acceptance criteria.
- Controlled fields use approved values.
- Lists are used where multiple values are expected.
- Rule-based validation runs after AI generation.
- Human approval remains visible.

## Input schema

### `RequirementInput`

| Field | Type | Required? | Description |
|---|---|---:|---|
| `requirement_id` | string | Yes | Unique requirement reference |
| `title` | string | Yes | Short requirement title |
| `domain` | string | No | Business domain |
| `feature` | string | No | Product or feature area |
| `user_story` | string | Yes | Main business requirement |
| `acceptance_criteria` | list of `AcceptanceCriterion` | Yes | Conditions that must be satisfied |
| `business_context` | list of strings | No | Known supporting information |
| `known_risks` | list of strings | No | Risks supplied by the tester |

### `AcceptanceCriterion`

| Field | Type | Required? | Description |
|---|---|---:|---|
| `criterion_id` | string | Yes | Stable ID such as `AC-001` |
| `description` | string | Yes | Acceptance-criterion text |

## Requirement-analysis schema

### `RequirementAnalysis`

| Field | Type | Description |
|---|---|---|
| `requirement_summary` | string | Concise description based only on the supplied requirement |
| `business_rules` | list of `BusinessRule` | Explicit rules extracted from the input |
| `ambiguities` | list of `Ambiguity` | Missing or unclear information |
| `assumptions` | list of `Assumption` | Temporary interpretations requiring visibility |
| `business_risks` | list of `BusinessRisk` | Risks relevant to UAT |

### Supporting analysis objects

#### `BusinessRule`

| Field | Type | Description |
|---|---|---|
| `rule_id` | string | Generated identifier such as `RULE-001` |
| `description` | string | Extracted rule |
| `source_criteria` | list of strings | Related acceptance-criterion IDs |

#### `Ambiguity`

| Field | Type | Description |
|---|---|---|
| `ambiguity_id` | string | Generated identifier |
| `description` | string | What is missing or unclear |
| `impact` | string | Why the information matters for testing |
| `clarification_question` | string | Question for the stakeholder |
| `related_criteria` | list of strings | Relevant acceptance-criterion IDs |

#### `Assumption`

| Field | Type | Description |
|---|---|---|
| `assumption_id` | string | Generated identifier |
| `description` | string | Temporary interpretation |
| `related_criteria` | list of strings | Relevant acceptance-criterion IDs |
| `approval_required` | boolean | Whether human approval is required |
| `status` | enum | `Proposed`, `Approved` or `Rejected` |

#### `BusinessRisk`

| Field | Type | Description |
|---|---|---|
| `risk_id` | string | Generated identifier |
| `description` | string | Potential business harm |
| `severity` | enum | `High`, `Medium` or `Low` |
| `rationale` | string | Reason for the severity |
| `related_criteria` | list of strings | Relevant acceptance-criterion IDs |

## Test-case schema

### `TestCase`

| Field | Type | Required? | Description |
|---|---|---:|---|
| `test_id` | string | Yes | Unique ID such as `UAT-001` |
| `requirement_id` | string | Yes | Parent requirement |
| `acceptance_criteria_ids` | list of strings | Yes | Traceability mapping |
| `title` | string | Yes | Concise scenario name |
| `objective` | string | Yes | What the test validates |
| `test_type` | enum | Yes | Approved test category |
| `priority` | enum | Yes | Execution priority |
| `risk_level` | enum | Yes | Business impact |
| `preconditions` | list of strings | Yes | Required starting conditions |
| `test_data` | list of strings | Yes | Data needed for execution |
| `steps` | list of `TestStep` | Yes | Ordered tester actions |
| `expected_result` | string | Yes | Observable expected outcome |
| `assumption_ids` | list of strings | No | Assumptions used by this test |
| `status` | enum | Yes | Draft or review state |

### `TestStep`

| Field | Type | Description |
|---|---|---|
| `step_number` | integer | Execution order beginning at 1 |
| `action` | string | Action performed by the tester |

### Controlled values

| Field | Allowed values |
|---|---|
| `test_type` | `Positive`, `Negative`, `Boundary`, `End-to-End`, `Accessibility` |
| `priority` | `High`, `Medium`, `Low` |
| `risk_level` | `High`, `Medium`, `Low` |
| `status` | `Draft`, `Needs Clarification`, `Ready for Review` |

## Coverage schema

### `CoverageSummary`

| Field | Type | Description |
|---|---|---|
| `total_criteria` | integer | Number of acceptance criteria received |
| `covered_criteria` | list of strings | Criteria mapped to at least one valid test |
| `uncovered_criteria` | list of strings | Criteria without a valid mapping |
| `coverage_percentage` | number | Covered criteria divided by total criteria |
| `tests_by_type` | object | Test totals grouped by category |
| `high_risk_tests` | list of strings | IDs of high-risk tests |
| `validation_warnings` | list of strings | Deterministic quality warnings |

## Complete response

### `TestPack`

The final response contains:

```json
{
  "requirement": {},
  "analysis": {},
  "test_cases": [],
  "coverage_summary": {}
}
```

The placeholder objects must conform to the structures defined above.

## Example test case

```json
{
  "test_id": "UAT-001",
  "requirement_id": "BR-001",
  "acceptance_criteria_ids": ["AC-002", "AC-003", "AC-006"],
  "title": "Complete a successful transfer below the daily limit",
  "objective": "Verify that an authenticated customer can transfer GBP to an existing UK beneficiary",
  "test_type": "Positive",
  "priority": "High",
  "risk_level": "High",
  "preconditions": [
    "Customer is authenticated",
    "Customer has an active current account",
    "An existing UK beneficiary is available",
    "Available balance is sufficient"
  ],
  "test_data": [
    "Transfer amount: £100.00",
    "Payment reference: Invoice 1001"
  ],
  "steps": [
    {
      "step_number": 1,
      "action": "Open the transfer-money feature"
    },
    {
      "step_number": 2,
      "action": "Select the existing UK beneficiary"
    },
    {
      "step_number": 3,
      "action": "Enter the amount and payment reference"
    },
    {
      "step_number": 4,
      "action": "Review and submit the transfer"
    }
  ],
  "expected_result": "The transfer succeeds, the available balance is updated and a confirmation containing a unique transaction reference is displayed.",
  "assumption_ids": [],
  "status": "Ready for Review"
}
```

## Deterministic validation rules

The application will reject or flag an output when:

- a required field is empty;
- a test ID is duplicated;
- a controlled field contains an unsupported value;
- a test references an unknown requirement or acceptance criterion;
- test steps are missing or not sequential;
- the expected result is blank;
- an assumption ID does not exist in the analysis;
- a criterion is reported as covered without a mapped valid test;
- the coverage calculation is incorrect; or
- a numerical limit exists but no applicable boundary test is generated.

## How this schema will be implemented

The structures will be converted into Python Pydantic models in `src/schemas.py`. The user interface, validation logic and CSV/Excel exporter will consume the same models so that every component uses one consistent definition.
