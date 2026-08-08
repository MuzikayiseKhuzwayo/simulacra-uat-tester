"""Deterministic validation rules for generated UAT test cases."""

from src.schemas import TestCase


def find_duplicate_test_ids(test_cases: list[TestCase]) -> list[str]:
    """Return duplicate test IDs in the order they are detected.

    Each duplicate ID is returned only once.
    """

    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    recorded_duplicates: set[str] = set()

    for test_case in test_cases:
        test_id = test_case.test_id

        if test_id in seen_ids and test_id not in recorded_duplicates:
            duplicate_ids.append(test_id)
            recorded_duplicates.add(test_id)

        seen_ids.add(test_id)

    return duplicate_ids

def find_unknown_criterion_ids(
    test_cases: list[TestCase],
    valid_criterion_ids: set[str],
) -> list[str]:
    """Return criterion IDs that do not exist in the requirement."""

    unknown_ids: list[str] = []
    recorded_unknown_ids: set[str] = set()

    for test_case in test_cases:
        for criterion_id in test_case.acceptance_criteria_ids:
            if (
                criterion_id not in valid_criterion_ids
                and criterion_id not in recorded_unknown_ids
            ):
                unknown_ids.append(criterion_id)
                recorded_unknown_ids.add(criterion_id)

    return unknown_ids

def find_test_ids_with_invalid_requirement_reference(
    test_cases: list[TestCase],
    expected_requirement_id: str,
) -> list[str]:
    """Return test IDs that reference the wrong requirement."""

    invalid_test_ids: list[str] = []

    for test_case in test_cases:
        if test_case.requirement_id != expected_requirement_id:
            invalid_test_ids.append(test_case.test_id)

    return invalid_test_ids

def find_test_ids_with_non_sequential_steps(
    test_cases: list[TestCase],
) -> list[str]:
    """Return test IDs whose step numbers are not sequential."""

    invalid_test_ids: list[str] = []

    for test_case in test_cases:
        actual_step_numbers = [
            step.step_number
            for step in test_case.steps
        ]

        expected_step_numbers = list(
            range(1, len(test_case.steps) + 1)
        )

        if actual_step_numbers != expected_step_numbers:
            invalid_test_ids.append(test_case.test_id)

    return invalid_test_ids

def find_unknown_assumption_ids(
    test_cases: list[TestCase],
    valid_assumption_ids: set[str],
) -> list[str]:
    """Return assumption IDs that do not exist in the analysis."""

    unknown_ids: list[str] = []
    recorded_unknown_ids: set[str] = set()

    for test_case in test_cases:
        for assumption_id in test_case.assumption_ids:
            if (
                assumption_id not in valid_assumption_ids
                and assumption_id not in recorded_unknown_ids
            ):
                unknown_ids.append(assumption_id)
                recorded_unknown_ids.add(assumption_id)

    return unknown_ids