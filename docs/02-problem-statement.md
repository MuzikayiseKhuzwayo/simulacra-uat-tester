# 02 — Problem Statement

## Current situation

Software testers often receive user stories and acceptance criteria that are incomplete, ambiguous or focused mainly on the expected successful path. Testers must interpret the requirement, identify missing rules and manually convert it into comprehensive test scenarios.

## Key challenges

| Challenge | Description | Potential impact |
|---|---|---|
| Incomplete requirements | Limits, validations, failure behaviour or dependencies may be missing | Defects or scope gaps discovered late |
| Ambiguous language | Terms such as valid, quickly or appropriate may be undefined | Different stakeholders interpret the requirement differently |
| Manual test design | Test scenarios, steps and expected results are written repeatedly | Increased preparation time |
| Inconsistent coverage | Test depth varies according to individual experience | Negative or boundary scenarios may be missed |
| Weak traceability | Tests may not be mapped clearly to acceptance criteria | Difficult coverage assessment and sign-off |
| Hidden assumptions | Testers may make decisions without recording them | Incorrect expected results and rework |
| Limited risk focus | High-impact scenarios may not be prioritised consistently | Critical business failures may receive insufficient attention |

## Core problem statement

> UAT teams need a faster and more consistent way to analyse business requirements and create risk-based, traceable test cases while ensuring that missing information and assumptions remain visible for human review.

## Why existing prompting alone is insufficient

A single request such as “generate test cases for this requirement” can produce readable output, but it may:

- invent missing business rules;
- omit important clarification questions;
- produce inconsistent fields;
- create duplicate or generic scenarios;
- fail to map tests to acceptance criteria; or
- provide no deterministic quality validation.

The POC therefore combines AI-based requirement reasoning with structured output, human review and rule-based checks.

## Proposed response

TestScope AI will:

1. separate requirement analysis from test generation;
2. extract only rules supported by the input;
3. label uncertainty as a question or assumption;
4. generate standardised test-case records;
5. assign risk and priority;
6. map tests to acceptance criteria; and
7. run deterministic checks on the generated test pack.

## Design principle

> The agent supports test-design decisions; it does not silently make business decisions.

## Intended impact

The expected outcome is a more complete and reviewable first draft that allows the Test Lead to spend more time on business risk, stakeholder discussion and final quality approval.
