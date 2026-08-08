"""Tests for the synthetic sample requirement."""

from scripts.load_sample_requirement import load_sample_requirement


def test_sample_requirement_matches_the_schema() -> None:
    """Verify that the sample JSON produces a valid requirement."""

    requirement = load_sample_requirement()

    assert requirement.requirement_id == "BR-001"
    assert requirement.title == "Transfer money to an existing UK beneficiary"
    assert requirement.domain == "Retail Banking"
    assert requirement.feature == "Digital Payments"
    assert len(requirement.acceptance_criteria) == 7
    assert len(requirement.business_context) == 4
    assert len(requirement.known_risks) == 4


def test_sample_requirement_has_unique_criterion_ids() -> None:
    """Verify that every acceptance criterion has a unique ID."""

    requirement = load_sample_requirement()

    criterion_ids = [
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    ]

    assert len(criterion_ids) == len(set(criterion_ids))


def test_sample_requirement_contains_expected_criterion_ids() -> None:
    """Verify the expected traceability identifiers."""

    requirement = load_sample_requirement()

    criterion_ids = [
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    ]

    assert criterion_ids == [
        "AC-001",
        "AC-002",
        "AC-003",
        "AC-004",
        "AC-005",
        "AC-006",
        "AC-007",
    ]