# TestScope AI — UAT Test Design Agent

TestScope AI is a proof-of-concept AI agent that analyses software requirements, identifies ambiguities and generates structured, risk-based User Acceptance Testing (UAT) test cases.

> Project status: **Project scaffold and schema contract implemented — Increment 2 complete**

## Why this project?

Testers frequently receive requirements that contain incomplete business rules, unclear acceptance criteria or hidden assumptions. Analysing these gaps and producing a traceable UAT test pack is valuable but time-consuming work.

TestScope AI is intended to support that process by producing a reviewable first draft while keeping the tester in control of business decisions.

## POC objective

Build an AI-powered agent that can:

- analyse one business requirement and its acceptance criteria;
- extract explicit business rules;
- identify ambiguities, missing information and assumptions;
- generate clarification questions before test design;
- produce positive, negative, boundary and end-to-end UAT test cases;
- assign risk and priority;
- validate acceptance-criteria coverage; and
- allow the tester to review and export the generated test pack.

## Planned workflow

1. The tester enters a requirement and acceptance criteria.
2. The agent extracts business rules and risks.
3. The agent presents ambiguities and clarification questions.
4. The tester answers the questions or approves documented assumptions.
5. The agent generates structured UAT test cases.
6. Rule-based checks validate completeness and traceability.
7. The tester reviews, edits and exports the results.

## Human-in-the-loop principle

The agent will not silently invent missing business rules. Missing information must be shown as a clarification question or a clearly labelled assumption. Final approval remains with the tester or business stakeholder.

## Initial technology direction

| Area | Proposed technology |
|---|---|
| Language | Python |
| Interface | Streamlit |
| AI orchestration | OpenAI Agents SDK |
| Data validation | Pydantic |
| Test-pack processing | Pandas |
| Automated checks | Pytest |
| Export | CSV initially, Excel later |

Technology choices will be confirmed during the implementation-design stage.

## Local development

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the tested dependencies and run the automated tests:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Copy `.env.example` to `.env` only when the agent integration is added. Never commit a real API key.

### See schema validation working

Run the small demonstration from the repository root:

```bash
python -m scripts.demo_schema_validation
```

It submits one valid requirement and one intentionally invalid requirement. The valid input becomes a structured Python object; the invalid input is rejected with readable validation errors.

## Documentation

- [Project overview](docs/01-project-overview.md)
- [Problem statement](docs/02-problem-statement.md)
- [POC scope](docs/03-poc-scope.md)
- [Sample banking requirement](docs/04-sample-requirement.md)
- [Input and output schema](docs/05-output-schema.md)
- [Solution architecture](docs/06-solution-architecture.md)
- [Architecture interview guide](docs/07-architecture-interview-guide.md)
- [Technical implementation plan](docs/08-technical-implementation-plan.md)
- [Eclipse local setup guide](docs/09-eclipse-local-setup.md)
- [VS Code local setup guide](docs/10-vscode-local-setup.md)

## Solution architecture

![TestScope AI solution architecture](assets/testscope-ai-solution-architecture.svg)

The interview guide will be revisited after implementation so that the answers can include evidence from the completed POC.

## Roadmap

- [x] Create repository
- [x] Define the project problem and initial POC scope
- [x] Finalise the sample banking requirement
- [x] Define input and output schemas
- [x] Design the solution architecture
- [x] Create the technical implementation plan
- [x] Create the Python scaffold and safe environment configuration
- [x] Implement and test the shared Pydantic schemas
- [ ] Add the synthetic sample requirement fixture
- [ ] Build the command-line prototype
- [ ] Add rule-based validation
- [ ] Build the Streamlit interface
- [ ] Add CSV and Excel export
- [ ] Evaluate the agent using benchmark requirements
- [ ] Deploy the demonstration application

## Responsible use and data protection

This project will use synthetic or publicly shareable requirements only. API keys, personal data, customer data and confidential company requirements must never be committed to the repository.

## Author

**Shalaka Jaitapkar**

## Licence

This project is available under the [MIT License](LICENSE).
