# 04 — Sample Banking Requirement

## Purpose

This synthetic requirement will be the first benchmark used to build and evaluate TestScope AI. It includes enough information to generate useful UAT tests while deliberately leaving several business rules unclear. A capable agent should identify those gaps instead of silently inventing answers.

No real customer, company or production data is used.

## Requirement metadata

| Field | Value |
|---|---|
| Requirement ID | BR-001 |
| Title | Transfer money to an existing UK beneficiary |
| Domain | Retail Banking |
| Feature | Digital Payments |
| User type | Authenticated personal banking customer |

## User story

> As an online banking customer, I want to transfer money from my current account to an existing UK beneficiary so that I can make a payment securely.

## Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| AC-001 | The customer must be logged in and have an active current account. |
| AC-002 | The customer must be able to select an existing UK beneficiary. |
| AC-003 | The customer must enter a transfer amount and payment reference before submitting the payment. |
| AC-004 | The maximum daily transfer limit is £10,000. |
| AC-005 | The transfer must be prevented when the customer has insufficient available funds. |
| AC-006 | After a successful transfer, the available balance must be updated and a confirmation containing a unique transaction reference must be displayed. |
| AC-007 | If a transfer fails, an appropriate error message must be displayed and the customer's account must not be debited. |

## Known business context

- Transfers are made in GBP.
- The beneficiary already exists in the customer's beneficiary list.
- The feature is available through online banking.
- The POC is concerned with the business flow, not the underlying payment-network implementation.

## Information deliberately left unclear

The requirement does not confirm:

- whether £10,000 is a per-transaction limit or a cumulative daily limit;
- whether a transfer of exactly £10,000 is allowed;
- which timezone controls the daily-limit reset;
- whether pending, scheduled or failed payments count towards the daily limit;
- the minimum permitted amount;
- the permitted length and characters for the payment reference;
- whether an authorised overdraft is included in available funds;
- what happens when a beneficiary is blocked, deleted or temporarily unavailable;
- whether additional authentication is required;
- how duplicate submissions are detected and handled; or
- what specific message should be displayed for each failure condition.

These items provide the benchmark for ambiguity detection and clarification-question generation.

## Expected analysis behaviour

The agent should:

1. summarise the payment objective without adding unsupported rules;
2. extract the seven acceptance criteria as traceable business rules;
3. identify material ambiguities, especially around the limit, available balance, payment reference and failure handling;
4. generate clear questions that a Business Analyst or Product Owner could answer;
5. label any temporary interpretation as an assumption requiring approval; and
6. identify fraud, duplicate payment, incorrect debit and misleading confirmation as high-impact risks.

## Minimum expected test coverage

The generated test pack should include at least:

- successful transfer below the limit;
- transfer of exactly £10,000;
- transfer above £10,000;
- cumulative transfers approaching or exceeding the daily limit;
- zero, negative, blank and malformed amounts;
- sufficient and insufficient available funds;
- valid, blank and invalid payment references;
- successful balance update;
- unique transaction-reference display;
- failed transfer with no debit;
- unavailable or invalid beneficiary;
- duplicate submission;
- session or authentication failure; and
- accessible and understandable confirmation and error messages.

Some scenarios may initially be marked as blocked or assumption-dependent until the clarification questions are answered.

## Behaviour the agent must avoid

The agent must not:

- claim that the limit resets at midnight without supporting information;
- invent a payment-reference length;
- assume an overdraft can be used;
- invent exact error-message wording;
- claim a specific authentication method is mandatory; or
- report full coverage while an acceptance criterion remains unmapped.

## Benchmark use

During evaluation, the generated analysis and tests will be compared with the expectations in this document. This benchmark is intended to test reasoning quality and traceability, not exact wording.
