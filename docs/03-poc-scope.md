# 03 — POC Scope

## Scope statement

TestScope AI will accept one business requirement and its acceptance criteria, analyse the requirement, identify ambiguities and business risks, ask clarification questions, generate risk-based UAT test cases, validate coverage and allow the tester to export the results.

## In scope for Version 1

- Text entry for one requirement
- Requirement ID and title
- User story and acceptance criteria
- Optional domain and business context
- Business-rule extraction
- Ambiguity and missing-information detection
- Clarification-question generation
- Explicit assumption recording
- Business-risk identification
- Positive, negative, boundary and end-to-end test generation
- Test priority and risk classification
- Requirement-to-test traceability
- Basic deterministic validation
- Editable results
- CSV export

## Out of scope for Version 1

- Direct Jira or Azure DevOps integration
- Automatic browser or API test execution
- Playwright or Selenium code generation
- Production deployment and enterprise authentication
- Processing an entire project backlog in one request
- Confidential company requirements or production customer data
- Automated UAT approval or release sign-off
- Performance, penetration or specialist security testing

These capabilities may be considered after the core workflow has been evaluated.

## Required input

| Field | Required? | Purpose |
|---|---:|---|
| Requirement ID | Yes | Traceability reference |
| Requirement title | Yes | Short description |
| User story or requirement | Yes | Main business need |
| Acceptance criteria | Yes | Conditions the solution must satisfy |
| Business domain | No | Additional context for analysis |
| Business rules | No | Known constraints and validations |
| Known risks | No | Tester-provided risk information |

## Agent workflow

### Stage A — Requirement analysis

The agent will produce a concise requirement summary, extracted business rules, ambiguities, clarification questions, assumptions requiring approval and business risks.

### Human review

The tester can answer the clarification questions or choose to continue using clearly documented assumptions.

### Stage B — Test generation

The agent will create structured test cases covering relevant positive, negative, boundary and end-to-end scenarios.

### Stage C — Validation

Rule-based validation will check:

- required fields are populated;
- test IDs are unique;
- priorities and test types use approved values;
- every acceptance criterion is mapped;
- expected results are present;
- at least one negative test exists; and
- boundary tests exist when numerical limits are present.

## Expected output

The output will contain a requirement analysis, structured test cases and a coverage summary. Each test case will include its ID, requirement reference, title, objective, type, priority, risk, preconditions, test data, steps, expected result and assumptions used.

## POC success criteria

The POC will be considered successful when:

1. the agent extracts the main explicit business rules;
2. significant missing information is presented as clarification questions;
3. unsupported assumptions are not presented as confirmed facts;
4. every acceptance criterion is mapped to at least one test;
5. positive, negative and applicable boundary scenarios are generated;
6. every test includes steps and an expected result;
7. test IDs are unique;
8. the tester can review and export the results; and
9. the end-to-end workflow can be completed in approximately two minutes.

## Constraints and assumptions

- Version 1 will use synthetic requirements.
- AI output requires human review.
- The model may produce variable results, so benchmark evaluations will be required.
- API usage may incur cost and requires secure secret management.
- Coverage percentage measures mapped criteria; it does not guarantee test quality.

## Step 1 completion condition

Step 1 is complete when the project objective, boundaries, inputs, outputs and success criteria are agreed and the sample banking requirement plus structured output schema are finalised.
