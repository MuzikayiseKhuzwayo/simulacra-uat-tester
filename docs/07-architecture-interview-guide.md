# 07 — Architecture Interview Guide

## 1. How to position the project honestly

At the current stage, say:

> I designed the POC architecture and data contract, and I am implementing the solution incrementally.

Do not yet say:

> I deployed a production-ready agent used by business teams.

The distinction matters. Interviewers value clear design thinking, but they may ask for implementation evidence. Once the code and demonstration are complete, the wording can be updated.

## 2. Thirty-second introduction

Use this when the interviewer asks, “Tell me about your AI agent project.”

> I designed TestScope AI, a bounded AI agent for UAT test design. It solves a common quality-engineering problem: business requirements often contain missing or ambiguous rules, but testers still need to create complete and traceable test cases. The solution first analyses the requirement and generates clarification questions. It then pauses for human review before generating positive, negative, boundary and end-to-end UAT tests. The AI handles reasoning, while Pydantic schemas and deterministic Python validators control structure, traceability and coverage. The final result is an editable test pack that can be exported to CSV.

## 3. Two-minute architecture explanation

> I started with the problem rather than the technology. In UAT, the main challenge is not simply writing test steps. It is understanding the business outcome, identifying missing rules and ensuring that assumptions are visible before testing begins.
>
> The architecture therefore uses a bounded two-stage agent workflow. The tester enters a user story, acceptance criteria and optional business context through a Streamlit interface. A trusted Python workflow controller validates the input and starts the first agent run.
>
> Run A behaves as a Senior UAT Test Lead. It extracts explicit business rules, identifies ambiguities, creates clarification questions and assesses business risks. The workflow then pauses at a human-review gate. The tester can provide an answer, approve a temporary assumption or leave an item unresolved.
>
> Run B receives the original requirement together with the reviewed answers and approved assumptions. It generates structured UAT test cases covering positive, negative, boundary, end-to-end and accessibility scenarios where relevant.
>
> The generated content must conform to Pydantic models. After that, a deterministic Python quality engine validates required fields, IDs, traceability, negative and boundary coverage, and calculates the acceptance-criteria coverage percentage. I deliberately keep those calculations outside the language model because they need to be repeatable and testable.
>
> Finally, the tester reviews and edits the results before exporting them. This design uses AI for reasoning, humans for business accountability and deterministic code for validation.

## 4. Five-minute whiteboard walkthrough

When presenting the architecture image, explain it from top to bottom.

### Step 1 — Tester or Business Analyst

Say:

> The process begins with a tester or Business Analyst providing a requirement. For the POC, the input contains a requirement ID, title, user story, acceptance criteria and optional business context.

Why:

> Stable IDs are important because every generated test must be traceable to a requirement and one or more acceptance criteria.

### Step 2 — Streamlit interface and workflow controller

Say:

> Streamlit provides the user-facing POC. It captures the requirement, displays clarification questions and presents an editable test pack. Behind the interface, a Python workflow controller owns the process.

Why:

> The workflow controller is trusted application code. It controls which stage runs next, preserves state, handles errors and prevents the model from bypassing human approval.

How:

> The controller moves the application through states such as Draft, Analysing, Awaiting Review, Generating, Validating and Ready for Review.

### Step 3 — Agent Run A: requirement analysis

Say:

> The first agent run focuses only on requirement understanding. It does not immediately generate test cases. It extracts explicit rules, identifies ambiguity, creates clarification questions and assesses business risks.

Why:

> Generating test cases directly from an incomplete requirement can convert an AI assumption into a false expected result. Separating analysis from generation reduces that risk.

How:

> The agent receives stage-specific instructions and returns a typed `RequirementAnalysis` object containing business rules, ambiguities, assumptions and risks.

### Step 4 — Human-review gate

Say:

> The workflow pauses after analysis. For every ambiguity, the tester can enter a stakeholder answer, approve or reject an assumption, or leave the matter unresolved.

Why:

> UAT expected results represent business decisions. The model can identify uncertainty, but it should not approve business rules on behalf of a Product Owner or Business Analyst.

How:

> The workflow state remains `AWAITING_REVIEW` until the decisions are captured. Unresolved items remain visible and affected tests are marked `Needs Clarification`.

### Step 5 — Agent Run B: test generation

Say:

> The second run receives the original requirement, the analysis, stakeholder answers and approved assumptions. It then generates risk-based UAT tests.

Why:

> This creates a clear evidence chain between the original requirement, human decisions and the generated test cases.

How:

> Every test contains a unique ID, acceptance-criteria references, type, priority, risk level, preconditions, test data, steps, expected result and any assumption IDs used.

### Step 6 — Pydantic schema validation

Say:

> The agent output is not accepted as unrestricted text. Pydantic models enforce the agreed data contract.

Why:

> The application needs predictable data for validation, editing and export. A paragraph cannot reliably support automated coverage calculations.

How:

> The Agents SDK `output_type` is mapped to Pydantic classes. Invalid types, missing required fields or unsupported enum values are rejected.

### Step 7 — deterministic coverage and quality engine

Say:

> After structural validation, standard Python code checks quality and calculates coverage.

Why:

> Counting mapped criteria, checking duplicate IDs and validating step sequence are deterministic tasks. Using an LLM for them would add unnecessary variability.

How:

> Coverage is calculated as the number of unique acceptance criteria mapped to at least one valid test divided by the total number of acceptance criteria, multiplied by 100.

### Step 8 — review and export

Say:

> The tester sees the generated test pack, coverage gaps and warnings. The results remain editable because AI output is a first draft. Only the reviewed structured data is exported to CSV.

Why:

> The aim is to accelerate a Test Lead, not replace professional judgement or UAT sign-off.

## 5. Explain the banking example

Use this if the interviewer asks for a concrete example.

> My benchmark requirement allows an authenticated customer to transfer money to an existing UK beneficiary, with a stated maximum daily limit of £10,000. The requirement does not say whether the limit is per transaction or cumulative, whether exactly £10,000 is allowed, when the daily limit resets or whether pending payments count towards it.
>
> Run A should identify those gaps and ask precise questions. If the Product Owner confirms that the limit is cumulative and inclusive, Run B can generate scenarios below the limit, exactly at the limit, one penny above it and multiple transfers that cumulatively cross it.
>
> If the rule is not confirmed, the agent must not invent an answer. The affected scenarios remain marked as needing clarification. This example demonstrates why the human-review gate is a core control rather than an optional UI feature.

## 6. What makes this an agent?

Word-for-word answer:

> It is agentic because it is given a goal and specialist instructions, interprets the requirement, determines which ambiguities and risks are material, produces structured decisions and operates within a stateful multi-step workflow. However, I deliberately describe it as a bounded agent rather than a fully autonomous system. Python controls the stages, and the model cannot independently approve assumptions, export data or execute external actions.

If challenged that it could be implemented using two LLM calls:

> Technically, the first POC could be implemented using direct structured model calls. I selected the Agents SDK because it gives a clean path for typed agent outputs, guardrails, runtime state and tracing as the workflow grows. The agentic value is in the controlled goal-driven workflow, not simply in using an SDK label.

## 7. Why and how each technology was selected

| Technology | Why selected | How it is used | Limitation |
|---|---|---|---|
| Python | Strong AI ecosystem and easy validation/testing | Controller, schemas, validators and exporters | Requires a separate production API layer at scale |
| Streamlit | Fastest route to an interactive POC | Forms, review screens, editable tables and downloads | Limited enterprise UI and session management |
| OpenAI Agents SDK | Typed outputs, guardrails, state and tracing | Two stage-specific agent runs | Adds dependency and API cost |
| Pydantic | Runtime type and field validation | Shared data contract | Structural validity does not prove business correctness |
| Pandas | Simple tabular transformation and export | Converts reviewed tests to CSV/Excel | Not a persistence layer |
| Pytest | Repeatable developer testing | Unit and integration tests | Model-quality evaluation needs additional methods |
| Session state | No database required for POC | Holds current workflow data | Data can be lost when the session ends |

## 8. Most important design questions and answers

### Q1. Why did you select a two-stage workflow?

> Requirement understanding and test generation are different cognitive tasks. The first stage exposes missing rules; the second uses reviewed information to generate tests. Combining both stages encourages the model to fill gaps silently and makes the reasoning harder to govern.

### Q2. Why not generate test cases with one prompt?

> A single prompt can generate readable tests, but it does not provide a reliable clarification checkpoint, structured state or traceable assumption approval. The POC is designed as a controlled workflow rather than a prompt demonstration.

### Q3. Why use one specialist rather than multiple agents?

> The two stages use the same UAT expertise and do not require different external tools or approval policies. Multiple agents would increase prompt complexity, handoff errors, latency and cost without a proven benefit. I would split the design only when specialist ownership becomes materially different.

### Q4. Why did you keep the workflow controller outside the model?

> Stage transitions, approval rules, retries and export permissions must be predictable. These are application-control responsibilities, so Python owns them. The model contributes reasoning but cannot change the workflow policy.

### Q5. Why is human review mandatory?

> UAT validates business acceptance. An AI model cannot authoritatively decide an unstated business rule. Human review prevents an inferred rule from becoming a false expected result.

### Q6. Why use structured output?

> Structured output makes the response machine-readable, validates required fields, supports editing and export, and enables deterministic traceability calculations. The agent still generates the content; the schema only controls its format.

### Q7. Why Pydantic?

> Pydantic converts the data contract into executable validation. It checks types, required fields and allowed values and produces clear validation errors. The same models can be reused across the agent, UI, validator, tests and exporter.

### Q8. Why not let the LLM calculate coverage?

> Coverage is an exact set calculation. Python can deterministically compare acceptance-criterion IDs with mapped IDs in valid tests. Using the model would make the result variable and difficult to audit.

### Q9. Why Streamlit?

> Streamlit lets me prove the complete workflow quickly with forms, session state, editable data tables and downloads. For production, I would separate a FastAPI backend from a React or enterprise front end.

### Q10. Why use CSV first?

> CSV is universally accessible and simple to validate. It proves the export flow without adding formatting complexity. Excel and Jira integration can be added after the core test-generation quality is demonstrated.

### Q11. Why is there no database?

> Version 1 processes one requirement within one session. A database would add schema, migration, security and hosting work before persistence has been proven necessary. Production would require persistent project storage, identity and audit history.

### Q12. Why no RAG or vector database?

> The first POC is grounded in a requirement supplied directly by the user. There is no large external knowledge collection to retrieve from. RAG becomes valuable later when the agent must use policy documents, testing standards, domain rules or historical defects.

### Q13. Why no MCP?

> Version 1 has no external Jira, Confluence or test-management action. MCP would be useful later for governed access to those tools, but adding it now would not improve the core requirement-analysis hypothesis.

### Q14. Why use the Agents SDK instead of only the Responses API?

> A direct API call could support the smallest version. I selected the Agents SDK because the design already needs typed outputs, guardrail boundaries, run state and observability, and it provides a cleaner growth path for future tools or specialist handoffs.

### Q15. How is the design explainable?

> Extracted rules reference acceptance-criteria IDs, ambiguities show their impact and clarification question, risks include rationale, assumptions remain visible and every test maps back to one or more criteria. This provides evidence for why a test exists.

## 9. Hallucination and GenAI-risk questions

### Q16. How do you reduce hallucination?

> I use five controls: constrain the prompt to supplied evidence, separate confirmed rules from proposed assumptions, require acceptance-criteria references, pause for human review and run deterministic validation. I would also measure unsupported-assumption rate using benchmark requirements.

### Q17. Can Pydantic prevent hallucination?

> No. Pydantic validates structure, not truth. A perfectly structured answer can still be factually unsupported. Truthfulness is addressed through source traceability, prompt constraints, human review and evaluation against known requirements.

### Q18. How do you handle unresolved information?

> It remains explicitly unresolved. Affected tests receive `Needs Clarification`, and the export shows the dependency. The system does not silently select an expected result.

### Q19. How would you handle prompt injection inside a requirement?

> I would treat requirement text as untrusted data, delimit it clearly from system instructions, prohibit it from changing workflow rules, avoid tool execution in Version 1 and validate all outputs. Future external tools would use least privilege and approval controls.

### Q20. How do you manage inconsistent model output?

> I use typed outputs, fixed prompt and model versions during evaluation, deterministic post-processing and one controlled retry for structural failures. Business ambiguity is never solved through an automatic retry.

### Q21. What happens if the model invents an acceptance criterion?

> The validator detects references that are not present in `RequirementInput`. The test is blocked or flagged, and the unsupported rule is shown for human correction.

### Q22. What is the difference between an error and an ambiguity?

> An error is a structural problem such as a duplicate ID or missing expected result. Python can detect and correct or reject it. An ambiguity is missing business knowledge and must be resolved by a person or remain visible.

## 10. Testing and evaluation questions

### Q23. How will you test the application?

> I will use a test pyramid. Unit tests will cover Pydantic schemas, ID validation, coverage calculations and export transformations. Integration tests will cover workflow-state transitions and mocked agent responses. Agent evaluation will use synthetic benchmark requirements with known ambiguities, risks and expected coverage. Finally, a UAT Test Lead will score usefulness and correctness.

### Q24. What is the golden dataset?

> It is a curated set of synthetic requirements where the important rules, ambiguities, risks and minimum expected scenarios are defined in advance. The banking requirement is the first benchmark case. Additional retail and insurance cases will reduce domain bias.

### Q25. Which metrics will you use?

| Metric | Meaning |
|---|---|
| Schema pass rate | Percentage of model outputs accepted by the typed schema |
| Acceptance-criteria coverage | Percentage of criteria mapped to valid tests |
| Critical ambiguity recall | Percentage of known critical gaps identified |
| Ambiguity precision | Percentage of raised ambiguities judged relevant |
| Unsupported-assumption rate | Frequency of rules invented without evidence |
| Duplicate-test rate | Percentage of materially duplicated scenarios |
| High-risk scenario recall | Percentage of known critical scenarios generated |
| Human acceptance rate | Percentage of generated tests accepted with minor or no edits |
| Edit distance or edit rate | Degree of human correction required |
| Latency | Time to complete analysis and generation |
| Cost per test pack | Model usage cost for one completed workflow |

### Q26. Why is 100% criteria coverage not enough?

> Coverage shows that every criterion has at least one mapped test. It does not prove that the tests are correct, sufficiently deep or free from hallucination. That is why I also measure risk coverage, ambiguity recall, unsupported assumptions, duplication and human acceptance.

### Q27. How do you evaluate ambiguity detection?

> For each benchmark, I define known material ambiguities. Identified relevant gaps are true positives, missed gaps are false negatives and unnecessary questions are false positives. I can then calculate precision and recall, with higher weighting for critical business rules.

### Q28. How do you test nondeterministic outputs?

> I avoid asserting exact wording. I test structural validity, required semantic elements, traceability and rubric-based quality. I also run repeated trials to understand stability rather than judging the model from one successful response.

### Q29. What negative tests would you run against the agent?

> I would use empty requirements, contradictory criteria, duplicated IDs, extremely long text, malicious instructions, unsupported domain claims, missing numerical units, multiple conflicting limits and criteria that cannot be tested. The application should reject invalid input or expose uncertainty safely.

### Q30. How will you prove business value?

> I would compare manual and assisted test-design time, number of important gaps identified, accepted test percentage and reviewer effort. The target is not only faster generation; it is faster production of a useful and reviewable first draft.

## 11. Reliability, security and production questions

### Q31. What happens if the API times out?

> The workflow controller keeps the last safe session state, displays a recoverable error and allows the user to retry. It does not discard the requirement or duplicate an export.

### Q32. What is your retry strategy?

> I allow one bounded retry for transient API or structural-output failures. I do not use unlimited loops, and I do not retry to resolve missing business knowledge.

### Q33. How are API keys protected?

> The key is stored in an environment variable or deployment secret manager. Only `.env.example` is committed. The key is never displayed, logged or sent to the browser.

### Q34. How do you protect requirement data?

> The POC uses synthetic data. For enterprise use, I would add authentication, role-based access, encryption, retention policies, audit logs, approved model endpoints, data-loss-prevention controls and explicit restrictions on sensitive fields.

### Q35. How would the solution scale?

> I would separate the Streamlit prototype into a stateless API service and production front end, persist workflow state in a database, use asynchronous job processing for long runs and isolate each tenant. Scaling the infrastructure is straightforward; maintaining evaluation quality and governance is the more important challenge.

### Q36. How do you control cost?

> The POC uses two bounded model runs per completed test pack, compact structured inputs, output limits and no uncontrolled tool loop. I would record token usage and cost per run, evaluate smaller models for extraction tasks and reserve stronger models for cases where quality improvement is measurable.

### Q37. How do you monitor the system?

> I would capture run ID, stage, latency, failure type, schema result, test count, coverage and reviewer score. Model traces help diagnose agent behaviour, while application logs monitor deterministic components. Sensitive requirement content should not be placed in general logs.

### Q38. What is the main production risk?

> The main risk is false confidence: a well-formatted test pack may appear authoritative even when business assumptions are wrong. The architecture addresses this through visible uncertainty, source mapping, human approval and multiple quality metrics rather than relying on appearance or coverage alone.

## 12. Trade-offs and limitations

Be ready to say:

> The design intentionally optimises for a demonstrable POC. Its limitations are that it handles one requirement at a time, uses session state rather than persistent storage, has no enterprise authentication, does not retrieve policy documents and does not integrate with Jira. Model output also remains nondeterministic and requires review. These are conscious scope boundaries, not hidden production claims.

## 13. Future roadmap answer

> Once the POC proves requirement analysis and test quality, I would add three capabilities in order. First, persistent projects, authentication and audit history. Second, retrieval of approved policies and domain rules with citations. Third, governed Jira or test-management integration for import and export. Only after evaluating the single-specialist design would I consider separate agents for domain-policy retrieval, test generation or automation generation.

## 14. Questions to ask the interviewer

These questions show architectural judgement:

1. How are requirements and test artefacts currently stored?
2. Which part of test design creates the most delay: clarification, scenario design, data preparation or traceability?
3. What level of human approval is required before AI-generated tests can be used?
4. Are there restrictions on sending requirements to external model providers?
5. Which quality metrics would the organisation trust for an AI-assisted testing solution?
6. Would the first integration priority be Jira, Confluence or an existing test-management tool?
7. Does the organisation already maintain approved policy or business-rule repositories?

## 15. Strong closing statement

> The key principle behind my design is separation of responsibility. The AI is used where reasoning and language understanding add value. Humans retain ownership of business decisions. Deterministic Python code owns validation and coverage. That separation makes the solution useful, explainable and safer to evolve from a POC into an enterprise capability.

## 16. Interview vocabulary

| Term | Simple meaning |
|---|---|
| Bounded agent | An agent operating within explicit stages, permissions and stopping points |
| Human-in-the-loop | A person reviews or approves a decision before the workflow continues |
| Structured output | Model-generated content returned in a predefined machine-readable format |
| Data contract | Agreed fields and types exchanged between components |
| Deterministic validation | Code that returns the same result for the same input |
| Traceability | Evidence linking a test back to its requirement or criterion |
| Guardrail | A check or policy that can block, flag or pause behaviour |
| Hallucination | Unsupported content generated as though it were true |
| Golden dataset | Curated examples with known expected qualities used for evaluation |
| Observability | Logs, metrics and traces used to understand system behaviour |
| State machine | Defined workflow statuses and permitted transitions |
| Idempotency | Repeating an operation without creating unintended duplicate effects |

## 17. Final preparation checklist

Before discussing the project:

- practise the 30-second and two-minute explanations aloud;
- explain the architecture without reading every box;
- prepare the banking-limit example;
- remember that Pydantic controls structure, not truth;
- remember that Python calculates coverage;
- explain why human review is mandatory;
- state the current implementation status honestly;
- describe at least three measurable evaluation metrics;
- acknowledge limitations before proposing future enhancements; and
- finish with the separation-of-responsibility principle.
