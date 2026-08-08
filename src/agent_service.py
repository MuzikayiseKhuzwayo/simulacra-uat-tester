"""Ollama-backed agent services for TestScope AI."""

import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import ResponseError, chat
from pydantic import ValidationError

from src.schemas import RequirementAnalysis, RequirementInput


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_PROMPT_PATH = (
    PROJECT_ROOT / "prompts" / "analyse_requirement.md"
)


class AgentServiceError(RuntimeError):
    """Raised when the AI agent cannot produce a usable result."""


def load_analysis_prompt() -> str:
    """Load the requirement-analysis instructions."""

    if not ANALYSIS_PROMPT_PATH.exists():
        raise AgentServiceError(
            "The requirement-analysis prompt was not found at "
            f"{ANALYSIS_PROMPT_PATH}."
        )

    prompt = ANALYSIS_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise AgentServiceError(
            "The requirement-analysis prompt is empty."
        )

    return prompt


def get_ollama_model() -> str:
    """Return the configured local Ollama model."""

    load_dotenv()

    return (
        os.getenv("OLLAMA_MODEL", "qwen3:4b").strip()
        or "qwen3:4b"
    )


def request_structured_analysis(
    user_message: str,
) -> RequirementAnalysis:
    """Request and validate structured analysis from Ollama."""

    try:
        response = chat(
            model=get_ollama_model(),
            messages=[
                {
                    "role": "system",
                    "content": load_analysis_prompt(),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            format=RequirementAnalysis.model_json_schema(),
            options={"temperature": 0},
            think=False,
        )

        response_content = response.message.content

        if not response_content:
            raise AgentServiceError(
                "The local model returned an empty response."
            )

        return RequirementAnalysis.model_validate_json(
            response_content
        )

    except ResponseError as error:
        raise AgentServiceError(
            f"Ollama request failed: {error}"
        ) from error

    except ValidationError as error:
        raise AgentServiceError(
            "Ollama returned output that did not match the "
            "RequirementAnalysis schema."
        ) from error


def analyse_requirement(
    requirement: RequirementInput,
) -> RequirementAnalysis:
    """Perform the initial requirement analysis."""

    requirement_json = requirement.model_dump_json(indent=2)

    return request_structured_analysis(
        "Analyse the following validated business requirement.\n\n"
        f"{requirement_json}"
    )


def correct_analysis(
    requirement: RequirementInput,
    previous_analysis: RequirementAnalysis,
    issues: list[str],
) -> RequirementAnalysis:
    """Request one correction using deterministic feedback."""

    valid_criterion_ids = [
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    ]

    issues_text = "\n".join(
        f"{number}. {issue}"
        for number, issue in enumerate(issues, start=1)
    )

    correction_message = f"""
Your previous requirement analysis failed deterministic validation.

Correct every reported issue. Do not defend or explain the previous
response. Return only the corrected structured analysis.

Mandatory correction rules:

1. Business-rule IDs must be RULE-001, RULE-002 and so on.
2. Business-risk IDs must be RISK-001, RISK-002 and so on.
3. Ambiguity IDs must use the AMB- prefix.
4. Assumption IDs must use the ASM- prefix.
5. Generated identifiers must be unique.
6. Criterion-reference fields may contain only exact IDs from this list:
   {valid_criterion_ids}
7. Do not add descriptions to criterion-reference values.
8. Do not use "Known Risk:" text as a criterion ID.
9. Evaluate every acceptance criterion.
10. Ensure every acceptance criterion is represented by at least one
    extracted business rule.
11. Preserve supported findings while repairing their identifiers and
    traceability.
12. Do not invent information that is absent from the requirement.

ORIGINAL REQUIREMENT:

{requirement.model_dump_json(indent=2)}

PREVIOUS ANALYSIS:

{previous_analysis.model_dump_json(indent=2)}

DETERMINISTIC VALIDATION ISSUES:

{issues_text}
""".strip()

    return request_structured_analysis(correction_message)