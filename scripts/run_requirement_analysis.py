"""Run the TestScope AI requirement-analysis workflow."""

from pathlib import Path

from pydantic import ValidationError

from src.agent_service import (
    AgentServiceError,
    analyse_requirement,
    correct_analysis,
)
from src.analysis_validators import validate_analysis
from src.schemas import RequirementAnalysis, RequirementInput


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENT_PATH = (
    PROJECT_ROOT / "data" / "sample_requirement.json"
)

MAX_CORRECTION_ATTEMPTS = 1


def load_sample_requirement() -> RequirementInput:
    """Load and validate the sample requirement."""

    if not REQUIREMENT_PATH.exists():
        raise FileNotFoundError(
            f"Requirement file not found: {REQUIREMENT_PATH}"
        )

    requirement_json = REQUIREMENT_PATH.read_text(
        encoding="utf-8"
    )

    return RequirementInput.model_validate_json(
        requirement_json
    )


def display_analysis(
    heading: str,
    analysis: RequirementAnalysis,
) -> None:
    """Display structured analysis."""

    print()
    print(heading)
    print("=" * 52)
    print(analysis.model_dump_json(indent=2))


def display_guardrail_result(
    issues: list[str],
) -> bool:
    """Display guardrail issues and return pass status."""

    print()
    print("Deterministic guardrail validation")
    print("=" * 52)

    if not issues:
        print("GUARDRAIL: PASSED")
        return True

    print("GUARDRAIL: FAILED")
    print(f"Total issues detected: {len(issues)}")
    print()

    for number, issue in enumerate(issues, start=1):
        print(f"{number}. {issue}")

    return False


def main() -> None:
    """Run analysis, validation and one controlled correction."""

    print("TestScope AI - Local Requirement Analysis Agent")
    print("=" * 52)

    try:
        requirement = load_sample_requirement()

        print("Requirement validation: PASSED")
        print(f"Requirement ID: {requirement.requirement_id}")
        print(f"Title: {requirement.title}")
        print()
        print("Running initial local AI analysis...")

        analysis = analyse_requirement(requirement)

        display_analysis(
            "Initial requirement analysis: COMPLETED",
            analysis,
        )

        issues = validate_analysis(
            requirement,
            analysis,
        )

        if display_guardrail_result(issues):
            print()
            print("Analysis is ready for human review.")
            return

        for attempt in range(1, MAX_CORRECTION_ATTEMPTS + 1):
            print()
            print(
                f"Running controlled correction attempt "
                f"{attempt} of {MAX_CORRECTION_ATTEMPTS}..."
            )

            analysis = correct_analysis(
                requirement,
                analysis,
                issues,
            )

            display_analysis(
                "Corrected requirement analysis: COMPLETED",
                analysis,
            )

            issues = validate_analysis(
                requirement,
                analysis,
            )

            if display_guardrail_result(issues):
                print()
                print(
                    "Correction succeeded. Analysis is ready "
                    "for human review."
                )
                return

        print()
        print("CORRECTION FAILED")
        print(
            "Test-case generation remains BLOCKED. "
            "Human review is required."
        )

    except FileNotFoundError as error:
        print(f"FAILED: {error}")

    except ValidationError as error:
        print("FAILED: The requirement input is invalid.")
        print(error)

    except AgentServiceError as error:
        print("FAILED: The local agent could not complete.")
        print(error)


if __name__ == "__main__":
    main()