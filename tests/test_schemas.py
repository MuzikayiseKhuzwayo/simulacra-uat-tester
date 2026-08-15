"""Unit tests for the shared Pydantic data contracts."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    AcceptanceCriterion,
    Assumption,
    AssumptionStatus,
    BusinessRisk,
    BusinessRule,
    CoverageSummary,
    GeneratedTestCases,
    Priority,
    RequirementAnalysis,
    RequirementInput,
    RiskLevel,
    Severity,
    TestCase as UATTestCase,
    TestPack as UATTestPack,
    TestStatus as UATTestStatus,
    TestStep as UATTestStep,
    TestType as UATTestType,
)


def valid_requirement() -> RequirementInput:
    return RequirementInput(
        requirement_id="BR-001",
        title="Transfer money",
        domain="Banking",
        feature="Payments",
        user_story=(
            "As an authenticated customer, I want to transfer money to an "
            "existing UK beneficiary."
        ),
        acceptance_criteria=[
            AcceptanceCriterion(
                criterion_id="AC-001",
                description="The customer must be authenticated.",
            ),
            AcceptanceCriterion(
                criterion_id="AC-002",
                description="The transfer must respect the daily limit.",
            ),
        ],
    )


def valid_analysis() -> RequirementAnalysis:
    return RequirementAnalysis(
        requirement_summary="An authenticated customer transfers money.",
        business_rules=[
            BusinessRule(
                rule_id="RULE-001",
                description="The customer must be authenticated.",
                source_criteria=["AC-001"],
            )
        ],
        ambiguities=[],
        assumptions=[
            Assumption(
                assumption_id="ASM-001",
                description="The limit is calculated per calendar day.",
                related_criteria=["AC-002"],
                approval_required=True,
                status=AssumptionStatus.APPROVED,
            )
        ],
        business_risks=[
            BusinessRisk(
                risk_id="RISK-001",
                description="A transfer may exceed the allowed limit.",
                severity=Severity.HIGH,
                rationale="This could create a financial loss.",
                related_criteria=["AC-002"],
            )
        ],
    )


def valid_test_case() -> UATTestCase:
    return UATTestCase(
        test_id="UAT-001",
        requirement_id="BR-001",
        acceptance_criteria_ids=["AC-001", "AC-002"],
        title="Complete a transfer below the daily limit",
        objective="Verify a valid transfer succeeds.",
        test_type=UATTestType.POSITIVE,
        priority=Priority.HIGH,
        risk_level=RiskLevel.HIGH,
        preconditions=["The customer is authenticated."],
        test_data=["Transfer amount: GBP 100.00"],
        steps=[
            UATTestStep(step_number=1, action="Open the transfer feature."),
            UATTestStep(step_number=2, action="Submit the transfer."),
        ],
        expected_result="The transfer succeeds and a reference is displayed.",
        assumption_ids=["ASM-001"],
        status=UATTestStatus.READY_FOR_REVIEW,
    )


def valid_test_pack() -> UATTestPack:
    return UATTestPack(
        requirement=valid_requirement(),
        analysis=valid_analysis(),
        test_cases=[valid_test_case()],
        coverage_summary=CoverageSummary(
            total_criteria=2,
            covered_criteria=["AC-001", "AC-002"],
            uncovered_criteria=[],
            coverage_percentage=100,
            tests_by_type={UATTestType.POSITIVE: 1},
            high_risk_tests=["UAT-001"],
            validation_warnings=[],
        ),
    )


def test_valid_requirement_is_accepted() -> None:
    requirement = valid_requirement()

    assert requirement.requirement_id == "BR-001"
    assert len(requirement.acceptance_criteria) == 2


def test_duplicate_acceptance_criterion_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="criterion IDs must be unique"):
        RequirementInput(
            requirement_id="BR-001",
            title="Transfer money",
            user_story="A customer transfers money.",
            acceptance_criteria=[
                {"criterion_id": "AC-001", "description": "First rule"},
                {"criterion_id": "AC-001", "description": "Second rule"},
            ],
        )


def test_requirement_must_have_an_acceptance_criterion() -> None:
    with pytest.raises(ValidationError):
        RequirementInput(
            requirement_id="BR-001",
            title="Transfer money",
            user_story="A customer transfers money.",
            acceptance_criteria=[],
        )


def test_blank_required_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AcceptanceCriterion(criterion_id="AC-001", description="   ")


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AcceptanceCriterion(
            criterion_id="AC-001",
            description="The customer is authenticated.",
            invented_by_model="unexpected value",
        )


def test_unsupported_controlled_value_is_rejected() -> None:
    test_case = valid_test_case().model_dump()
    test_case["priority"] = "Critical"

    with pytest.raises(ValidationError):
        UATTestCase.model_validate(test_case)


def test_step_number_must_begin_at_one_or_greater() -> None:
    with pytest.raises(ValidationError):
        UATTestStep(step_number=0, action="Open the transfer feature.")


def test_test_case_requires_steps() -> None:
    test_case = valid_test_case().model_dump()
    test_case["steps"] = []

    with pytest.raises(ValidationError):
        UATTestCase.model_validate(test_case)


def test_coverage_percentage_must_be_between_zero_and_one_hundred() -> None:
    with pytest.raises(ValidationError):
        CoverageSummary(
            total_criteria=1,
            covered_criteria=["AC-001"],
            uncovered_criteria=[],
            coverage_percentage=101,
            tests_by_type={UATTestType.POSITIVE: 1},
            high_risk_tests=[],
            validation_warnings=[],
        )


def test_complete_pack_round_trips_through_json() -> None:
    original = valid_test_pack()

    restored = UATTestPack.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.test_cases[0].test_type is UATTestType.POSITIVE

def test_generated_test_cases_accepts_valid_test_case() -> None:
    generated = GeneratedTestCases(
        test_cases=[valid_test_case()]
    )

    assert len(generated.test_cases) == 1
    assert generated.test_cases[0].test_id == "UAT-001"


def test_generated_test_cases_requires_at_least_one_test() -> None:
    with pytest.raises(ValidationError):
        GeneratedTestCases(test_cases=[])

def test_test_case_preserves_semantic_traceability() -> None:
    test_case_data = valid_test_case().model_dump()

    test_case_data["risk_ids"] = ["RISK-001"]
    test_case_data["ambiguity_ids"] = ["AMB-001"]
    test_case_data["assumption_ids"] = ["ASM-001"]

    test_case = UATTestCase.model_validate(test_case_data)

    assert test_case.risk_ids == ["RISK-001"]
    assert test_case.ambiguity_ids == ["AMB-001"]
    assert test_case.assumption_ids == ["ASM-001"]
