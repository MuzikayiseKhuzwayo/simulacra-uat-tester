"""Gemini 2.5-backed agent services for TestScope AI."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from src.config import get_gemini_api_key, get_gemini_client, get_gemini_model
from src.schemas import (
    GeneratedTestCases,
    RequirementAnalysis,
    RequirementInput,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_PROMPT_PATH = (
    PROJECT_ROOT / "prompts" / "analyse_requirement.md"
)
TEST_GENERATION_PROMPT_PATH = (
    PROJECT_ROOT / "prompts" / "generate_uat_tests.md"
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

def load_test_generation_prompt() -> str:
    """Load the UAT test-generation instructions."""

    if not TEST_GENERATION_PROMPT_PATH.exists():
        raise AgentServiceError(
            "The UAT test-generation prompt was not found at "
            f"{TEST_GENERATION_PROMPT_PATH}."
        )

    prompt = TEST_GENERATION_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise AgentServiceError(
            "The UAT test-generation prompt is empty."
        )

    return prompt


# Backward compatibility alias
get_ollama_model = get_gemini_model


def clean_gemini_schema(d: Any) -> Any:
    """Recursively strip additionalProperties and invalid fields for Gemini API schema."""
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            if k in ("additionalProperties", "additional_properties"):
                continue
            new_d[k] = clean_gemini_schema(v)
        return new_d
    elif isinstance(d, list):
        return [clean_gemini_schema(item) for item in d]
    return d


def request_structured_analysis(
    user_message: str,
) -> RequirementAnalysis:
    """Request and validate structured analysis from Gemini 2.5."""

    client = get_gemini_client()
    if not client:
        raise AgentServiceError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in .env."
        )

    try:
        from google.genai import types

        model_name = get_gemini_model()
        system_instruction = load_analysis_prompt()
        analysis_schema = clean_gemini_schema(RequirementAnalysis.model_json_schema())

        response = client.models.generate_content(
            model=model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=analysis_schema,
                temperature=0.0,
            ),
        )

        response_content = response.text

        if not response_content:
            raise AgentServiceError(
                "Gemini returned an empty response."
            )

        return RequirementAnalysis.model_validate_json(
            response_content
        )

    except ValidationError as error:
        raise AgentServiceError(
            "Gemini returned output that did not match the "
            "RequirementAnalysis schema."
        ) from error

    except Exception as error:
        raise AgentServiceError(
            f"Gemini request failed: {error}"
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

def request_structured_test_cases(
    user_message: str,
) -> GeneratedTestCases:
    """Request and validate structured UAT test cases from Gemini 2.5."""

    client = get_gemini_client()
    if not client:
        raise AgentServiceError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in .env."
        )

    try:
        from google.genai import types

        model_name = get_gemini_model()
        system_instruction = load_test_generation_prompt()
        test_case_schema = clean_gemini_schema(GeneratedTestCases.model_json_schema())

        response = client.models.generate_content(
            model=model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=test_case_schema,
                temperature=0.0,
            ),
        )


        response_content = response.text

        if not response_content:
            raise AgentServiceError(
                "Gemini returned an empty test-case response."
            )

        return GeneratedTestCases.model_validate_json(
            response_content
        )

    except ValidationError as error:
        raise AgentServiceError(
            "Gemini returned output that did not match the "
            "GeneratedTestCases schema."
        ) from error

    except Exception as error:
        raise AgentServiceError(
            f"Gemini test-generation request failed: {error}"
        ) from error


def correct_generated_test_cases(
    requirement: RequirementInput,
    analysis: RequirementAnalysis,
    previous_tests: GeneratedTestCases,
    issues: list[str],
) -> GeneratedTestCases:
    """Request one correction using deterministic test-case feedback."""

    valid_criterion_ids = [
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    ]

    valid_risk_ids = [
        risk.risk_id
        for risk in analysis.business_risks
    ]

    valid_ambiguity_ids = [
        ambiguity.ambiguity_id
        for ambiguity in analysis.ambiguities
    ]

    valid_assumption_ids = [
        assumption.assumption_id
        for assumption in analysis.assumptions
    ]

    issues_text = "\n".join(
        f"{number}. {issue}"
        for number, issue in enumerate(issues, start=1)
    )

    correction_message = f"""
Your previously generated UAT test cases failed deterministic validation.

Correct every reported issue. Do not defend or explain the previous
response. Return only the corrected structured test cases.

Mandatory correction rules:

1. Test IDs must be UAT-001, UAT-002 and so on.
2. Every test ID and test title must be unique.
3. Every test must use requirement ID:
   {requirement.requirement_id}
4. Criterion references may contain only exact IDs from:
   {valid_criterion_ids}
5. Every acceptance criterion must be covered.
6. Risk references may contain only exact IDs from:
   {valid_risk_ids}
7. Every supplied business risk must be covered by a relevant test.
8. Ambiguity references may contain only exact IDs from:
   {valid_ambiguity_ids}
9. Every supplied ambiguity must be represented by an affected test.
10. Tests referencing unresolved ambiguities must have status
    "Needs Clarification".
11. Assumption references may contain only exact IDs from:
    {valid_assumption_ids}
12. Tests depending on unapproved assumptions must have status
    "Needs Clarification".
13. Do not reference rejected assumptions.
14. Step numbers must begin at 1 and remain sequential.
15. High-severity risks must be covered by High-risk tests.
16. Do not invent requirements, rules, IDs, limits or dependencies.
17. Preserve valid tests while repairing traceability and quality issues.

ORIGINAL REQUIREMENT:

{requirement.model_dump_json(indent=2)}

VALIDATED REQUIREMENT ANALYSIS:

{analysis.model_dump_json(indent=2)}

PREVIOUS GENERATED TEST CASES:

{previous_tests.model_dump_json(indent=2)}

DETERMINISTIC VALIDATION ISSUES:

{issues_text}
""".strip()

    return request_structured_test_cases(correction_message)

def generate_uat_tests(
    requirement: RequirementInput,
    analysis: RequirementAnalysis,
) -> GeneratedTestCases:
    """Generate structured UAT tests from validated inputs."""

    generation_input = (
        "Generate UAT test cases from the following validated inputs.\n\n"
        "ORIGINAL REQUIREMENT:\n\n"
        f"{requirement.model_dump_json(indent=2)}\n\n"
        "VALIDATED REQUIREMENT ANALYSIS:\n\n"
        f"{analysis.model_dump_json(indent=2)}"
    )

    return request_structured_test_cases(generation_input)

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