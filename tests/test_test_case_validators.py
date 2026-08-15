"""Tests for deterministic validation of generated UAT test cases."""

from src.schemas import (
    AcceptanceCriterion,
    Ambiguity,
    Assumption,
    AssumptionStatus,
    BusinessRisk,
    GeneratedTestCases,
    Priority,
    RequirementAnalysis,
    RequirementInput,
    RiskLevel,
    Severity,
    TestCase,
    TestStatus,
    TestStep,
    TestType,
)
from src.test_case_validators import validate_generated_test_cases


def valid_requirement() -> RequirementInput:
    """Return a valid requirement containing two criteria."""

    return RequirementInput(
        requirement_id="BR-001",
        title="Transfer money",
        domain="Banking",
        feature="Payments",
        user_story=(
            "As an authenticated customer, I want to transfer money "
            "to an existing UK beneficiary."
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


def valid_analysis(
    assumption_status: AssumptionStatus = AssumptionStatus.APPROVED,
) -> RequirementAnalysis:
    """Return a valid analysis used by test-case validation."""

    return RequirementAnalysis(
        requirement_summary="An authenticated customer transfers money.",
        business_rules=[],
        ambiguities=[],
        assumptions=[
            Assumption(
                assumption_id="ASM-001",
                description="The limit is calculated per calendar day.",
                related_criteria=["AC-002"],
                approval_required=True,
                status=assumption_status,
            )
        ],
        business_risks=[
            BusinessRisk(
                risk_id="RISK-001",
                description="A transfer may exceed the daily limit.",
                severity=Severity.HIGH,
                rationale="This could cause a financial loss.",
                related_criteria=["AC-002"],
            )
        ],
    )


def analysis_with_ambiguity() -> RequirementAnalysis:
    """Return an analysis containing one unresolved ambiguity."""

    analysis = valid_analysis()

    return analysis.model_copy(
        update={
            "ambiguities": [
                Ambiguity(
                    ambiguity_id="AMB-001",
                    description="The daily-limit time window is unclear.",
                    impact="Boundary tests cannot be finalized.",
                    clarification_question=(
                        "Is the limit based on a calendar day "
                        "or a rolling 24-hour period?"
                    ),
                    related_criteria=["AC-002"],
                )
            ]
        }
    )

def make_test_case(
    test_id: str = "UAT-001",
    title: str = "Complete a valid transfer",
    requirement_id: str = "BR-001",
    criterion_ids: list[str] | None = None,
    risk_ids: list[str] | None = None,
    ambiguity_ids: list[str] | None = None,
    assumption_ids: list[str] | None = None,
    risk_level: RiskLevel = RiskLevel.HIGH,
    status: TestStatus = TestStatus.READY_FOR_REVIEW,
    step_numbers: list[int] | None = None,
) -> TestCase:
    """Create a test case with configurable validation properties."""

    criterion_ids = (
        ["AC-001", "AC-002"]
        if criterion_ids is None
        else criterion_ids
    )
    risk_ids = (
        ["RISK-001"]
        if risk_ids is None
        else risk_ids
    )
    ambiguity_ids = (
        []
        if ambiguity_ids is None
        else ambiguity_ids
    )
    assumption_ids = (
        []
        if assumption_ids is None
        else assumption_ids
    )
    step_numbers = (
        [1, 2]
        if step_numbers is None
        else step_numbers
    )

    return TestCase(
        test_id=test_id,
        requirement_id=requirement_id,
        acceptance_criteria_ids=criterion_ids,
        title=title,
        objective="Verify that an eligible customer can transfer money.",
        test_type=TestType.POSITIVE,
        priority=Priority.HIGH,
        risk_level=risk_level,
        preconditions=["The customer has an active account."],
        test_data=["Transfer amount: GBP 100.00"],
        steps=[
            TestStep(
                step_number=number,
                action=f"Perform transfer action {number}.",
            )
            for number in step_numbers
        ],
        expected_result=(
            "The transfer succeeds and a transaction reference is displayed."
        ),
        risk_ids=risk_ids,
        ambiguity_ids=ambiguity_ids,
        assumption_ids=assumption_ids,
        status=status,
    )


def validate(
    generated: GeneratedTestCases,
    analysis: RequirementAnalysis | None = None,
) -> list[str]:
    """Run the validator using standard valid inputs."""

    return validate_generated_test_cases(
        valid_requirement(),
        analysis or valid_analysis(),
        generated,
    )


def test_valid_generated_tests_return_no_issues() -> None:
    generated = GeneratedTestCases(
        test_cases=[make_test_case()]
    )

    assert validate(generated) == []


def test_duplicate_test_identifier_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                test_id="UAT-001",
                title="First transfer test",
            ),
            make_test_case(
                test_id="UAT-001",
                title="Second transfer test",
            ),
        ]
    )

    issues = validate(generated)

    assert (
        "Generated test identifier 'UAT-001' is duplicated."
        in issues
    )


def test_duplicate_test_title_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                test_id="UAT-001",
                title="Duplicate transfer title",
            ),
            make_test_case(
                test_id="UAT-002",
                title="Duplicate transfer title",
            ),
        ]
    )

    issues = validate(generated)

    assert any(
        "test title" in issue.lower() and "duplicated" in issue
        for issue in issues
    )


def test_incorrect_test_id_prefix_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(test_id="TEST-001")
        ]
    )

    issues = validate(generated)

    assert any("must use the UAT- prefix" in issue for issue in issues)


def test_incorrect_requirement_reference_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(requirement_id="BR-999")
        ]
    )

    issues = validate(generated)

    assert any(
        "references requirement 'BR-999'" in issue
        for issue in issues
    )


def test_unknown_acceptance_criterion_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-001", "AC-999"]
            )
        ]
    )

    issues = validate(generated)

    assert any(
        "unknown acceptance criterion 'AC-999'" in issue
        for issue in issues
    )


def test_uncovered_acceptance_criterion_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-001"]
            )
        ]
    )

    issues = validate(generated)

    assert (
        "Acceptance criteria not covered by generated tests: AC-002"
        in issues
    )


def test_non_sequential_steps_are_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(step_numbers=[1, 3])
        ]
    )

    issues = validate(generated)

    assert any(
        "step numbers must begin at 1 and remain sequential" in issue
        for issue in issues
    )


def test_unknown_assumption_reference_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                assumption_ids=["ASM-999"]
            )
        ]
    )

    issues = validate(generated)

    assert any(
        "unknown assumption 'ASM-999'" in issue
        for issue in issues
    )


def test_unapproved_assumption_requires_clarification_status() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                assumption_ids=["ASM-001"],
                status=TestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    issues = validate(
        generated,
        analysis=valid_analysis(AssumptionStatus.PROPOSED),
    )

    assert any(
        "must have status 'Needs Clarification'" in issue
        for issue in issues
    )


def test_high_risk_criterion_requires_high_risk_test() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(risk_level=RiskLevel.MEDIUM)
        ]
    )

    issues = validate(generated)

    assert (
        "High-risk acceptance criteria without a High-risk test: AC-002"
        in issues
    )

def test_unknown_business_risk_reference_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(risk_ids=["RISK-999"])
        ]
    )

    issues = validate(generated)

    assert any(
        "unknown business risk 'RISK-999'" in issue
        for issue in issues
    )


def test_uncovered_business_risk_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(risk_ids=[])
        ]
    )

    issues = validate(generated)

    assert (
        "Business risks not covered by generated tests: RISK-001"
        in issues
    )


def test_unknown_ambiguity_reference_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(ambiguity_ids=["AMB-999"])
        ]
    )

    issues = validate(generated)

    assert any(
        "unknown ambiguity 'AMB-999'" in issue
        for issue in issues
    )


def test_uncovered_ambiguity_is_detected() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(ambiguity_ids=[])
        ]
    )

    issues = validate(
        generated,
        analysis=analysis_with_ambiguity(),
    )

    assert (
        "Ambiguities not represented by generated tests: AMB-001"
        in issues
    )


def test_unresolved_ambiguity_requires_clarification() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                ambiguity_ids=["AMB-001"],
                status=TestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    issues = validate(
        generated,
        analysis=analysis_with_ambiguity(),
    )

    assert any(
        "must have status 'Needs Clarification'" in issue
        for issue in issues
    )


def test_ambiguity_with_clarification_status_is_valid() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                ambiguity_ids=["AMB-001"],
                status=TestStatus.NEEDS_CLARIFICATION,
            )
        ]
    )

    issues = validate(
        generated,
        analysis=analysis_with_ambiguity(),
    )

    assert issues == []