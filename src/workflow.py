"""Reusable end-to-end TestScope AI workflow."""

from src.agent_service import (
    analyse_requirement,
    correct_analysis,
    correct_generated_test_cases,
    generate_uat_tests,
)
from src.analysis_validators import validate_analysis
from src.coverage import calculate_coverage
from src.schemas import (
    RequirementInput,
    TestPack,
)
from src.test_case_enrichment import enrich_test_traceability
from src.test_case_validators import validate_generated_test_cases


MAX_ANALYSIS_CORRECTION_ATTEMPTS = 1
MAX_TEST_CORRECTION_ATTEMPTS = 1


class WorkflowBlockedError(RuntimeError):
    """Raised when deterministic validation blocks the workflow."""

    def __init__(
        self,
        stage: str,
        issues: list[str],
    ) -> None:
        self.stage = stage
        self.issues = issues

        super().__init__(
            f"Workflow blocked during {stage}: "
            + "; ".join(issues)
        )


def obtain_validated_analysis(
    requirement: RequirementInput,
):
    """Generate and deterministically validate requirement analysis."""

    analysis = analyse_requirement(requirement)

    issues = validate_analysis(
        requirement,
        analysis,
    )

    for _ in range(MAX_ANALYSIS_CORRECTION_ATTEMPTS):
        if not issues:
            break

        analysis = correct_analysis(
            requirement,
            analysis,
            issues,
        )

        issues = validate_analysis(
            requirement,
            analysis,
        )

    if issues:
        raise WorkflowBlockedError(
            stage="requirement analysis",
            issues=issues,
        )

    return analysis


def obtain_validated_test_cases(
    requirement: RequirementInput,
    analysis,
):
    """Generate, enrich and validate structured UAT tests."""

    generated = generate_uat_tests(
        requirement,
        analysis,
    )

    generated = enrich_test_traceability(
        analysis,
        generated,
    )

    issues = validate_generated_test_cases(
        requirement,
        analysis,
        generated,
    )

    for _ in range(MAX_TEST_CORRECTION_ATTEMPTS):
        if not issues:
            break

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

        issues = validate_generated_test_cases(
            requirement,
            analysis,
            generated,
        )

    if issues:
        raise WorkflowBlockedError(
            stage="UAT test generation",
            issues=issues,
        )

    return generated


def run_uat_workflow(
    requirement: RequirementInput,
) -> TestPack:
    """Run the complete TestScope AI workflow."""

    analysis = obtain_validated_analysis(
        requirement
    )

    generated = obtain_validated_test_cases(
        requirement,
        analysis,
    )

    coverage_summary = calculate_coverage(
        requirement,
        generated.test_cases,
    )

    return TestPack(
        requirement=requirement,
        analysis=analysis,
        test_cases=generated.test_cases,
        coverage_summary=coverage_summary,
    )