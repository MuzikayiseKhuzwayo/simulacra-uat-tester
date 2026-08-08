"""Tests for deterministic test-case validation."""

import src.schemas as schemas

from src.validators import (
    find_duplicate_test_ids,
    find_unknown_criterion_ids,
)


def make_test_case(test_id: str) -> schemas.TestCase:
    """Create a valid test case with a configurable ID."""

    return schemas.TestCase(
        test_id=test_id,
        requirement_id="BR-001",
        acceptance_criteria_ids=["AC-001"],
        title="Verify a valid transfer",
        objective="Verify that a valid transfer can be submitted.",
        test_type=schemas.TestType.POSITIVE,
        priority=schemas.Priority.HIGH,
        risk_level=schemas.RiskLevel.HIGH,
        preconditions=["The customer is authenticated."],
        test_data=["Transfer amount: GBP 100.00"],
        steps=[
            schemas.TestStep(
                step_number=1,
                action="Open the transfer feature.",
            ),
            schemas.TestStep(
                step_number=2,
                action="Submit the transfer.",
            ),
        ],
        expected_result="The transfer is completed successfully.",
        assumption_ids=[],
        status=schemas.TestStatus.READY_FOR_REVIEW,
    )


def test_no_duplicate_test_ids_returns_empty_list() -> None:
    """Verify that unique test IDs produce no validation issue."""

    test_cases = [
        make_test_case("UAT-001"),
        make_test_case("UAT-002"),
    ]

    duplicates = find_duplicate_test_ids(test_cases)

    assert duplicates == []


def test_duplicate_test_id_is_detected() -> None:
    """Verify that one duplicate test ID is returned."""

    test_cases = [
        make_test_case("UAT-001"),
        make_test_case("UAT-002"),
        make_test_case("UAT-001"),
    ]

    duplicates = find_duplicate_test_ids(test_cases)

    assert duplicates == ["UAT-001"]


def test_duplicate_id_is_reported_only_once() -> None:
    """Verify that a repeatedly duplicated ID appears only once."""

    test_cases = [
        make_test_case("UAT-001"),
        make_test_case("UAT-001"),
        make_test_case("UAT-001"),
    ]

    duplicates = find_duplicate_test_ids(test_cases)

    assert duplicates == ["UAT-001"]


def test_valid_criterion_references_return_empty_list() -> None:
    """Verify that known criterion IDs produce no validation issue."""

    test_cases = [
        make_test_case("UAT-001"),
        make_test_case("UAT-002"),
    ]

    valid_criterion_ids = {"AC-001", "AC-002"}

    unknown_ids = find_unknown_criterion_ids(
        test_cases,
        valid_criterion_ids,
    )

    assert unknown_ids == []


def test_unknown_criterion_reference_is_detected() -> None:
    """Verify that an invented criterion ID is detected."""

    test_case = make_test_case("UAT-001")

    updated_test_case = test_case.model_copy(
        update={"acceptance_criteria_ids": ["AC-001", "AC-999"]}
    )

    unknown_ids = find_unknown_criterion_ids(
        [updated_test_case],
        {"AC-001", "AC-002"},
    )

    assert unknown_ids == ["AC-999"]


from src.validators import (
    find_duplicate_test_ids,
    find_test_ids_with_invalid_requirement_reference,
    find_test_ids_with_non_sequential_steps,
    find_unknown_assumption_ids,
    find_unknown_criterion_ids,
)

def test_valid_requirement_references_return_empty_list() -> None:
    """Verify that correct requirement references are accepted."""

    test_cases = [
        make_test_case("UAT-001"),
        make_test_case("UAT-002"),
    ]

    invalid_test_ids = find_test_ids_with_invalid_requirement_reference(
        test_cases,
        "BR-001",
    )

    assert invalid_test_ids == []


def test_invalid_requirement_reference_is_detected() -> None:
    """Verify that a test linked to the wrong requirement is detected."""

    test_case = make_test_case("UAT-001")

    invalid_test_case = test_case.model_copy(
        update={"requirement_id": "BR-999"}
    )

    invalid_test_ids = find_test_ids_with_invalid_requirement_reference(
        [invalid_test_case],
        "BR-001",
    )

    assert invalid_test_ids == ["UAT-001"]


def test_sequential_steps_return_empty_list() -> None:
    """Verify correctly ordered steps are accepted."""

    test_case = make_test_case("UAT-001")

    invalid_test_ids = find_test_ids_with_non_sequential_steps(
        [test_case]
    )

    assert invalid_test_ids == []


def test_non_sequential_steps_are_detected() -> None:
    """Verify missing step numbers are detected."""

    test_case = make_test_case("UAT-001")

    invalid_test_case = test_case.model_copy(
        update={
            "steps": [
                schemas.TestStep(
                    step_number=1,
                    action="Open the transfer feature.",
                ),
                schemas.TestStep(
                    step_number=3,
                    action="Submit the transfer.",
                ),
            ]
        }
    )

    invalid_test_ids = find_test_ids_with_non_sequential_steps(
        [invalid_test_case]
    )

    assert invalid_test_ids == ["UAT-001"]

def test_valid_assumption_references_return_empty_list() -> None:
    """Verify that known assumption IDs are accepted."""

    test_case = make_test_case("UAT-001")

    updated_test_case = test_case.model_copy(
        update={"assumption_ids": ["ASM-001"]}
    )

    unknown_ids = find_unknown_assumption_ids(
        [updated_test_case],
        {"ASM-001", "ASM-002"},
    )

    assert unknown_ids == []


def test_unknown_assumption_reference_is_detected() -> None:
    """Verify that an invented assumption ID is detected."""

    test_case = make_test_case("UAT-001")

    updated_test_case = test_case.model_copy(
        update={"assumption_ids": ["ASM-001", "ASM-999"]}
    )

    unknown_ids = find_unknown_assumption_ids(
        [updated_test_case],
        {"ASM-001", "ASM-002"},
    )

    assert unknown_ids == ["ASM-999"]
