"""Tests for deterministic requirement-analysis guardrails."""

import src.schemas as schemas

from src.analysis_validators import validate_analysis


def make_requirement() -> schemas.RequirementInput:
    """Create a small valid requirement for guardrail tests."""

    return schemas.RequirementInput(
        requirement_id="BR-001",
        title="Transfer money",
        domain="Retail Banking",
        feature="Payments",
        user_story=(
            "A customer transfers money to an existing beneficiary."
        ),
        acceptance_criteria=[
            schemas.AcceptanceCriterion(
                criterion_id="AC-001",
                description="The beneficiary must already exist.",
            ),
            schemas.AcceptanceCriterion(
                criterion_id="AC-002",
                description="The account must have sufficient funds.",
            ),
        ],
        known_risks=[
            "An incorrect transfer could cause financial loss.",
        ],
    )


def make_valid_analysis() -> schemas.RequirementAnalysis:
    """Create an analysis that satisfies all guardrails."""

    return schemas.RequirementAnalysis(
        requirement_summary=(
            "The customer transfers money to an existing beneficiary."
        ),
        business_rules=[
            schemas.BusinessRule(
                rule_id="RULE-001",
                description="The beneficiary must already exist.",
                source_criteria=["AC-001"],
            ),
            schemas.BusinessRule(
                rule_id="RULE-002",
                description="The account must have sufficient funds.",
                source_criteria=["AC-002"],
            ),
        ],
        ambiguities=[],
        assumptions=[],
        business_risks=[
            schemas.BusinessRisk(
                risk_id="RISK-001",
                description="An incorrect transfer may cause loss.",
                severity=schemas.Severity.HIGH,
                rationale=(
                    "Money could be transferred incorrectly."
                ),
                related_criteria=["AC-001", "AC-002"],
            ),
        ],
    )


def test_valid_analysis_returns_no_issues() -> None:
    """Verify that a compliant analysis passes the guardrail."""

    issues = validate_analysis(
        make_requirement(),
        make_valid_analysis(),
    )

    assert issues == []


def test_incorrect_identifier_prefixes_are_detected() -> None:
    """Verify incorrect agent-generated prefixes are reported."""

    analysis = make_valid_analysis()

    incorrect_rule = analysis.business_rules[0].model_copy(
        update={"rule_id": "BR-001"}
    )

    incorrect_risk = analysis.business_risks[0].model_copy(
        update={"risk_id": "BR-002"}
    )

    analysis = analysis.model_copy(
        update={
            "business_rules": [
                incorrect_rule,
                analysis.business_rules[1],
            ],
            "business_risks": [incorrect_risk],
        }
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert (
        "Business rule 'BR-001' must use the RULE- prefix."
        in issues
    )

    assert (
        "Business risk 'BR-002' must use the RISK- prefix."
        in issues
    )


def test_unknown_criterion_reference_is_detected() -> None:
    """Verify descriptive or invented references are rejected."""

    analysis = make_valid_analysis()

    invalid_rule = analysis.business_rules[0].model_copy(
        update={
            "source_criteria": [
                "AC-001: Existing beneficiary",
            ]
        }
    )

    analysis = analysis.model_copy(
        update={
            "business_rules": [
                invalid_rule,
                analysis.business_rules[1],
            ]
        }
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert any(
        "references unknown acceptance criterion" in issue
        for issue in issues
    )


def test_duplicate_generated_identifier_is_detected() -> None:
    """Verify identifiers cannot be reused across sections."""

    analysis = make_valid_analysis()

    duplicate_risk = analysis.business_risks[0].model_copy(
        update={"risk_id": "RULE-001"}
    )

    analysis = analysis.model_copy(
        update={"business_risks": [duplicate_risk]}
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert (
        "Generated identifier 'RULE-001' is duplicated."
        in issues
    )


def test_uncovered_acceptance_criterion_is_detected() -> None:
    """Verify every criterion is represented by a rule."""

    analysis = make_valid_analysis().model_copy(
        update={
            "business_rules": [
                make_valid_analysis().business_rules[0]
            ]
        }
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert (
        "Acceptance criteria not covered by extracted "
        "business rules: AC-002"
        in issues
    )


def test_unapproved_assumption_is_detected() -> None:
    """Verify assumptions must require human approval."""

    analysis = make_valid_analysis()

    assumption = schemas.Assumption(
        assumption_id="ASM-001",
        description="The customer is already authenticated.",
        related_criteria=["AC-001"],
        approval_required=False,
        status=schemas.AssumptionStatus.PROPOSED,
    )

    analysis = analysis.model_copy(
        update={"assumptions": [assumption]}
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert (
        "Assumption 'ASM-001' must require human approval."
        in issues
    )


def test_empty_analysis_is_detected() -> None:
    """Verify an empty but schema-valid analysis is rejected."""

    analysis = schemas.RequirementAnalysis(
        requirement_summary="Transfer money.",
        business_rules=[],
        ambiguities=[],
        assumptions=[],
        business_risks=[],
    )

    issues = validate_analysis(
        make_requirement(),
        analysis,
    )

    assert (
        "No business rules were extracted from the "
        "acceptance criteria."
        in issues
    )

    assert (
        "Known risks were supplied, but no business risks "
        "were generated."
        in issues
    )