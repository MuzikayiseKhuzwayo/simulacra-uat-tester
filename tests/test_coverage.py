"""Tests for deterministic acceptance-criterion coverage."""

import src.schemas as schemas

from src.coverage import calculate_coverage
from tests.test_validators import make_test_case


def make_requirement() -> schemas.RequirementInput:
    """Create a requirement containing two acceptance criteria."""

    return schemas.RequirementInput(
        requirement_id="BR-001",
        title="Transfer money",
        domain="Retail Banking",
        feature="Digital Payments",
        user_story="A customer transfers money to a beneficiary.",
        acceptance_criteria=[
            schemas.AcceptanceCriterion(
                criterion_id="AC-001",
                description="The customer must be authenticated.",
            ),
            schemas.AcceptanceCriterion(
                criterion_id="AC-002",
                description="The transfer must respect the daily limit.",
            ),
        ],
    )


def test_all_criteria_covered_returns_one_hundred_percent() -> None:
    """Verify complete criterion coverage."""

    requirement = make_requirement()

    first_test = make_test_case("UAT-001")

    second_test = make_test_case("UAT-002").model_copy(
        update={"acceptance_criteria_ids": ["AC-002"]}
    )

    summary = calculate_coverage(
        requirement,
        [first_test, second_test],
    )

    assert summary.total_criteria == 2
    assert summary.covered_criteria == ["AC-001", "AC-002"]
    assert summary.uncovered_criteria == []
    assert summary.coverage_percentage == 100.0


def test_uncovered_criterion_reduces_coverage() -> None:
    """Verify partial coverage is calculated correctly."""

    requirement = make_requirement()
    test_case = make_test_case("UAT-001")

    summary = calculate_coverage(
        requirement,
        [test_case],
    )

    assert summary.total_criteria == 2
    assert summary.covered_criteria == ["AC-001"]
    assert summary.uncovered_criteria == ["AC-002"]
    assert summary.coverage_percentage == 50.0


def test_wrong_requirement_reference_does_not_count_as_coverage() -> None:
    """Verify tests linked to another requirement are excluded."""

    requirement = make_requirement()

    wrong_requirement_test = make_test_case("UAT-001").model_copy(
        update={
            "requirement_id": "BR-999",
            "acceptance_criteria_ids": ["AC-001", "AC-002"],
        }
    )

    summary = calculate_coverage(
        requirement,
        [wrong_requirement_test],
    )

    assert summary.covered_criteria == []
    assert summary.uncovered_criteria == ["AC-001", "AC-002"]
    assert summary.coverage_percentage == 0.0