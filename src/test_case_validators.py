"""Deterministic validation for AI-generated UAT test cases."""

from collections import Counter

from src.schemas import (
    AssumptionStatus,
    GeneratedTestCases,
    RequirementAnalysis,
    RequirementInput,
    RiskLevel,
    Severity,
    TestStatus,
)


def validate_generated_test_cases(
    requirement: RequirementInput,
    analysis: RequirementAnalysis,
    generated: GeneratedTestCases,
) -> list[str]:
    """Return traceability and quality issues in generated UAT tests."""

    issues: list[str] = []

    valid_criterion_ids = {
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    }

    assumptions_by_id = {
        assumption.assumption_id: assumption
        for assumption in analysis.assumptions
    }

    valid_risk_ids = {
    risk.risk_id
    for risk in analysis.business_risks
    }

    valid_ambiguity_ids = {
    ambiguity.ambiguity_id
    for ambiguity in analysis.ambiguities
    }

    test_ids = [
        test_case.test_id
        for test_case in generated.test_cases
    ]

    duplicate_test_ids = sorted(
        test_id
        for test_id, count in Counter(test_ids).items()
        if count > 1
    )

    for test_id in duplicate_test_ids:
        issues.append(
            f"Generated test identifier '{test_id}' is duplicated."
        )

    normalized_titles = [
        test_case.title.casefold()
        for test_case in generated.test_cases
    ]

    duplicate_titles = sorted(
        title
        for title, count in Counter(normalized_titles).items()
        if count > 1
    )

    for title in duplicate_titles:
        issues.append(
            f"Generated test title '{title}' is duplicated."
        )

    for test_case in generated.test_cases:
        if not test_case.test_id.startswith("UAT-"):
            issues.append(
                f"Test '{test_case.test_id}' must use the UAT- prefix."
            )

        if test_case.requirement_id != requirement.requirement_id:
            issues.append(
                f"Test '{test_case.test_id}' references requirement "
                f"'{test_case.requirement_id}' instead of "
                f"'{requirement.requirement_id}'."
            )

        for criterion_id in test_case.acceptance_criteria_ids:
            if criterion_id not in valid_criterion_ids:
                issues.append(
                    f"Test '{test_case.test_id}' references unknown "
                    f"acceptance criterion '{criterion_id}'."
                )

        if len(test_case.acceptance_criteria_ids) != len(
            set(test_case.acceptance_criteria_ids)
        ):
            issues.append(
                f"Test '{test_case.test_id}' contains duplicate "
                "acceptance-criterion references."
            )

        expected_step_numbers = list(
            range(1, len(test_case.steps) + 1)
        )
        actual_step_numbers = [
            step.step_number
            for step in test_case.steps
        ]

        if actual_step_numbers != expected_step_numbers:
            issues.append(
                f"Test '{test_case.test_id}' step numbers must begin "
                "at 1 and remain sequential."
            )

        if len(test_case.risk_ids) != len(set(test_case.risk_ids)):
            issues.append(
                f"Test '{test_case.test_id}' contains duplicate "
                "business-risk references."
            )

        for risk_id in test_case.risk_ids:
            if risk_id not in valid_risk_ids:
                issues.append(
                    f"Test '{test_case.test_id}' references unknown "
                    f"business risk '{risk_id}'."
                )

        if len(test_case.ambiguity_ids) != len(
            set(test_case.ambiguity_ids)
        ):
            issues.append(
                f"Test '{test_case.test_id}' contains duplicate "
                "ambiguity references."
            )

        for ambiguity_id in test_case.ambiguity_ids:
            if ambiguity_id not in valid_ambiguity_ids:
                issues.append(
                    f"Test '{test_case.test_id}' references unknown "
                    f"ambiguity '{ambiguity_id}'."
                )
                continue

            if test_case.status is not TestStatus.NEEDS_CLARIFICATION:
                issues.append(
                    f"Test '{test_case.test_id}' references unresolved "
                    f"ambiguity '{ambiguity_id}' and must have status "
                    "'Needs Clarification'."
                )

        for assumption_id in test_case.assumption_ids:
            assumption = assumptions_by_id.get(assumption_id)

            if assumption is None:
                issues.append(
                    f"Test '{test_case.test_id}' references unknown "
                    f"assumption '{assumption_id}'."
                )
                continue

            if assumption.status is AssumptionStatus.REJECTED:
                issues.append(
                    f"Test '{test_case.test_id}' references rejected "
                    f"assumption '{assumption_id}'."
                )

            if (
                assumption.status is not AssumptionStatus.APPROVED
                and test_case.status is not TestStatus.NEEDS_CLARIFICATION
            ):
                issues.append(
                    f"Test '{test_case.test_id}' depends on unapproved "
                    f"assumption '{assumption_id}' and must have status "
                    "'Needs Clarification'."
                )

    covered_criterion_ids = {
        criterion_id
        for test_case in generated.test_cases
        for criterion_id in test_case.acceptance_criteria_ids
        if criterion_id in valid_criterion_ids
    }

    uncovered_criterion_ids = sorted(
        valid_criterion_ids - covered_criterion_ids
    )

    if uncovered_criterion_ids:
        issues.append(
            "Acceptance criteria not covered by generated tests: "
            + ", ".join(uncovered_criterion_ids)
        )

    high_risk_criterion_ids = {
        criterion_id
        for risk in analysis.business_risks
        if risk.severity is Severity.HIGH
        for criterion_id in risk.related_criteria
        if criterion_id in valid_criterion_ids
    }

    criteria_with_high_risk_tests = {
        criterion_id
        for test_case in generated.test_cases
        if test_case.risk_level is RiskLevel.HIGH
        for criterion_id in test_case.acceptance_criteria_ids
        if criterion_id in valid_criterion_ids
    }

    missing_high_risk_coverage = sorted(
        high_risk_criterion_ids - criteria_with_high_risk_tests
    )

    covered_risk_ids = {
        risk_id
        for test_case in generated.test_cases
        for risk_id in test_case.risk_ids
        if risk_id in valid_risk_ids
    }

    uncovered_risk_ids = sorted(
        valid_risk_ids - covered_risk_ids
    )

    if uncovered_risk_ids:
        issues.append(
            "Business risks not covered by generated tests: "
            + ", ".join(uncovered_risk_ids)
        )

    covered_ambiguity_ids = {
        ambiguity_id
        for test_case in generated.test_cases
        for ambiguity_id in test_case.ambiguity_ids
        if ambiguity_id in valid_ambiguity_ids
    }

    uncovered_ambiguity_ids = sorted(
        valid_ambiguity_ids - covered_ambiguity_ids
    )

    if uncovered_ambiguity_ids:
        issues.append(
            "Ambiguities not represented by generated tests: "
            + ", ".join(uncovered_ambiguity_ids)
        )

    if missing_high_risk_coverage:
        issues.append(
            "High-risk acceptance criteria without a High-risk test: "
            + ", ".join(missing_high_risk_coverage)
        )

    return issues