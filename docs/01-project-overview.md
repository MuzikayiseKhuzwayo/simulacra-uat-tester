# 01 — Project Overview

## Project name

**TestScope AI — UAT Test Design Agent**

## Background

Designing effective UAT scenarios requires more than rewriting acceptance criteria as test cases. A Test Lead must understand the intended business outcome, identify missing rules, consider operational risks, prepare suitable test data and maintain traceability between requirements and tests.

This work is often performed manually and its quality can depend on the tester's experience, the completeness of the requirement and the time available for analysis.

## Vision

Create an AI-assisted test-design workflow that helps testers analyse requirements consistently and produce a high-quality first draft of a UAT test pack.

The solution is an assistant, not an autonomous approval authority. Testers and business stakeholders retain responsibility for confirming business rules and approving test coverage.

## Primary users

- UAT Test Leads
- Business Testers
- Manual Testers
- Business Analysts
- Quality Engineers

## Primary user need

> As a UAT Test Lead, I want an agent to analyse a requirement, highlight missing information and generate traceable, risk-based test cases so that I can create an initial UAT test pack more quickly and consistently.

## Project objective

Build a small proof of concept that accepts one business requirement, analyses its business rules and risks, requests clarification where necessary, generates structured UAT test cases and reports requirement coverage.

## Expected value

| Area | Expected value |
|---|---|
| Analysis | Earlier identification of ambiguous or incomplete requirements |
| Efficiency | Reduced time spent creating the first draft of test cases |
| Consistency | Standard test categories and output fields |
| Coverage | Clear mapping between acceptance criteria and test cases |
| Risk | Greater visibility of high-impact business scenarios |
| Governance | Assumptions and human decisions remain visible |

## High-level workflow

1. Capture the requirement and acceptance criteria.
2. Extract explicit business rules.
3. Detect gaps, ambiguities and potential risks.
4. Ask clarification questions.
5. Record stakeholder answers or approved assumptions.
6. Generate structured UAT test cases.
7. Run deterministic completeness and coverage checks.
8. Present the test pack for human review and export.

## POC outcome

The POC should demonstrate that an AI agent can create a useful and traceable first draft of UAT tests without hiding uncertainty or replacing the Test Lead's judgement.

## Current stage

The project is in **Step 1 — scope and requirements definition**. No production-ready software has been implemented yet.
