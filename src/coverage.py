"""Deterministic acceptance-criterion coverage calculation."""

from collections import Counter

from src.schemas import (
    CoverageSummary,
    RequirementInput,
    RiskLevel,
    TestCase,
)


def calculate_coverage(
    requirement: RequirementInput,
    test_cases: list[TestCase],
) -> CoverageSummary:
    """Calculate coverage using valid criterion mappings.

    Test cases connected to another requirement are excluded.
    Unknown criterion IDs are not counted as covered.
    """

    criterion_ids = [
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    ]

    valid_criterion_ids = set(criterion_ids)
    covered_criterion_ids: set[str] = set()

    relevant_test_cases = [
        test_case
        for test_case in test_cases
        if test_case.requirement_id == requirement.requirement_id
    ]

    for test_case in relevant_test_cases:
        for criterion_id in test_case.acceptance_criteria_ids:
            if criterion_id in valid_criterion_ids:
                covered_criterion_ids.add(criterion_id)

    covered_criteria = [
        criterion_id
        for criterion_id in criterion_ids
        if criterion_id in covered_criterion_ids
    ]

    uncovered_criteria = [
        criterion_id
        for criterion_id in criterion_ids
        if criterion_id not in covered_criterion_ids
    ]

    total_criteria = len(criterion_ids)

    coverage_percentage = round(
        len(covered_criteria) / total_criteria * 100,
        2,
    )

    type_counts = Counter(
        test_case.test_type
        for test_case in relevant_test_cases
    )

    tests_by_type = dict(type_counts)

    high_risk_tests = [
        test_case.test_id
        for test_case in relevant_test_cases
        if test_case.risk_level == RiskLevel.HIGH
    ]

    return CoverageSummary(
        total_criteria=total_criteria,
        covered_criteria=covered_criteria,
        uncovered_criteria=uncovered_criteria,
        coverage_percentage=coverage_percentage,
        tests_by_type=tests_by_type,
        high_risk_tests=high_risk_tests,
        validation_warnings=[],
    )