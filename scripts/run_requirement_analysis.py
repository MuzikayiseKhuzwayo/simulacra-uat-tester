"""Run the TestScope AI requirement-analysis workflow."""

from pathlib import Path

from pydantic import ValidationError

from src.agent_service import (
    AgentServiceError,
    analyse_requirement,
    correct_analysis,
    correct_generated_test_cases,
    generate_uat_tests,
)
from src.analysis_validators import validate_analysis
from src.schemas import (RequirementAnalysis, RequirementInput, TestPack)
from src.coverage import calculate_coverage
from src.test_case_validators import validate_generated_test_cases
from src.test_case_enrichment import enrich_test_traceability


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENT_PATH = (
    PROJECT_ROOT / "data" / "sample_requirement.json"
)

MAX_CORRECTION_ATTEMPTS = 1
MAX_TEST_CORRECTION_ATTEMPTS = 1

OUTPUT_DIRECTORY = PROJECT_ROOT / "output"
TEST_PACK_PATH = OUTPUT_DIRECTORY / "test_pack.json"



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

def save_test_pack(test_pack: TestPack) -> None:
    """Save the validated TestPack as formatted JSON."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEST_PACK_PATH.write_text(
        test_pack.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print()
    print(f"TestPack saved to: {TEST_PACK_PATH}")

def generate_and_display_test_pack(
    requirement: RequirementInput,
    analysis: RequirementAnalysis,
    ) -> None:
    """Generate, validate, correct and display the final UAT pack."""

    print()
    print("Generating structured UAT test cases...")
    print("Model execution may take several minutes.")

    generated = generate_uat_tests(
        requirement,
        analysis,
)

    generated = enrich_test_traceability(
    analysis,
    generated,
)
    print()
    print("Generated UAT test cases: COMPLETED")
    print("=" * 52)
    print(generated.model_dump_json(indent=2))

    issues = validate_generated_test_cases(
        requirement,
        analysis,
        generated,
    )

    print()
    print("Deterministic test-case guardrail validation")
    print("=" * 52)

    if issues:
        print("TEST-CASE GUARDRAIL: FAILED")
        print(f"Total issues detected: {len(issues)}")
        print()

        for number, issue in enumerate(issues, start=1):
            print(f"{number}. {issue}")

        for attempt in range(
            1,
            MAX_TEST_CORRECTION_ATTEMPTS + 1,
        ):
            print()
            print(
                "Running controlled test-case correction attempt "
                f"{attempt} of {MAX_TEST_CORRECTION_ATTEMPTS}..."
            )

            generated = correct_generated_test_cases(
                requirement,
                analysis,
                generated,
                issues,
            )

            generated = enrich_test_traceability(
            analysis,
            generated,
            )

            print()
            print("Corrected UAT test cases: COMPLETED")
            print("=" * 52)
            print(generated.model_dump_json(indent=2))

            issues = validate_generated_test_cases(
                requirement,
                analysis,
                generated,
            )

            print()
            print("Corrected test-case guardrail validation")
            print("=" * 52)

            if not issues:
                print("TEST-CASE GUARDRAIL: PASSED")
                break

            print("TEST-CASE GUARDRAIL: FAILED")
            print(f"Total issues detected: {len(issues)}")
            print()

            for number, issue in enumerate(issues, start=1):
                print(f"{number}. {issue}")

        if issues:
            print()
            print("TEST-CASE CORRECTION FAILED")
            print(
                "Final TestPack generation remains BLOCKED. "
                "Human review is required."
            )
            return

    else:
        print("TEST-CASE GUARDRAIL: PASSED")

    coverage_summary = calculate_coverage(
        requirement,
        generated.test_cases,
    )

    test_pack = TestPack(
        requirement=requirement,
        analysis=analysis,
        test_cases=generated.test_cases,
        coverage_summary=coverage_summary,
    )

    save_test_pack(test_pack)

    print()
    print("Final UAT TestPack: COMPLETED")
    print("=" * 52)
    print(test_pack.model_dump_json(indent=2))

    print()
    print(
        "Acceptance-criteria coverage: "
        f"{coverage_summary.coverage_percentage}%"
    )
    print(f"Total UAT tests: {len(test_pack.test_cases)}")

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
            print("Analysis is ready for UAT test generation.")

            generate_and_display_test_pack(
                requirement,
                analysis,
            )
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
                "for UAT test generation."
             )

            generate_and_display_test_pack(
                requirement,
                analysis,
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