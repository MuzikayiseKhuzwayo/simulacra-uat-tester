"""Tests for deterministic UAT traceability enrichment."""

from src.schemas import (
    Ambiguity,
    AssumptionStatus,
    GeneratedTestCases,
    TestStatus as UATTestStatus,
)
from src.test_case_enrichment import enrich_test_traceability
from tests.test_test_case_validators import (
    make_test_case,
    valid_analysis,
)


def analysis_with_related_findings(
    assumption_status: AssumptionStatus,
):
    """Create analysis findings related to AC-002."""

    analysis = valid_analysis(assumption_status)

    return analysis.model_copy(
        update={
            "ambiguities": [
                Ambiguity(
                    ambiguity_id="AMB-001",
                    description="The daily-limit window is unclear.",
                    impact="The boundary test cannot be finalized.",
                    clarification_question=(
                        "Is the limit calculated by calendar day "
                        "or rolling 24 hours?"
                    ),
                    related_criteria=["AC-002"],
                )
            ]
        }
    )


def test_related_findings_are_added_to_test_case() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-002"],
                risk_ids=[],
                ambiguity_ids=[],
                assumption_ids=[],
                status=UATTestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    enriched = enrich_test_traceability(
        analysis_with_related_findings(
            AssumptionStatus.PROPOSED
        ),
        generated,
    )

    test_case = enriched.test_cases[0]

    assert test_case.risk_ids == ["RISK-001"]
    assert test_case.ambiguity_ids == ["AMB-001"]
    assert test_case.assumption_ids == ["ASM-001"]
    assert test_case.status is UATTestStatus.NEEDS_CLARIFICATION


def test_unrelated_findings_are_not_added() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-001"],
                risk_ids=[],
                ambiguity_ids=[],
                assumption_ids=[],
                status=UATTestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    enriched = enrich_test_traceability(
        analysis_with_related_findings(
            AssumptionStatus.PROPOSED
        ),
        generated,
    )

    test_case = enriched.test_cases[0]

    assert test_case.risk_ids == []
    assert test_case.ambiguity_ids == []
    assert test_case.assumption_ids == []
    assert test_case.status is UATTestStatus.READY_FOR_REVIEW


def test_rejected_assumption_is_not_added() -> None:
    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-002"],
                risk_ids=[],
                ambiguity_ids=[],
                assumption_ids=[],
                status=UATTestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    analysis = valid_analysis(
        AssumptionStatus.REJECTED
    )

    enriched = enrich_test_traceability(
        analysis,
        generated,
    )

    test_case = enriched.test_cases[0]

    assert test_case.risk_ids == ["RISK-001"]
    assert test_case.assumption_ids == []
    assert test_case.status is UATTestStatus.READY_FOR_REVIEW

def test_unrelated_ai_supplied_finding_ids_are_removed() -> None:
    """AI-provided IDs must not bypass deterministic matching."""

    generated = GeneratedTestCases(
        test_cases=[
            make_test_case(
                criterion_ids=["AC-001"],
                risk_ids=["RISK-001"],
                ambiguity_ids=["AMB-001"],
                assumption_ids=["ASM-001"],
                status=UATTestStatus.READY_FOR_REVIEW,
            )
        ]
    )

    enriched = enrich_test_traceability(
        analysis_with_related_findings(
            AssumptionStatus.PROPOSED
        ),
        generated,
    )

    test_case = enriched.test_cases[0]

    assert test_case.risk_ids == []
    assert test_case.ambiguity_ids == []
    assert test_case.assumption_ids == []
    assert test_case.status is UATTestStatus.READY_FOR_REVIEW