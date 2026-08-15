"""Deterministic traceability enrichment for generated UAT tests."""

from src.schemas import (
    AssumptionStatus,
    GeneratedTestCases,
    RequirementAnalysis,
    TestStatus,
)


def enrich_test_traceability(
    analysis: RequirementAnalysis,
    generated: GeneratedTestCases,
) -> GeneratedTestCases:
    """Link tests to findings that share acceptance criteria."""

    enriched_tests = []

    for test_case in generated.test_cases:
        criterion_ids = set(
            test_case.acceptance_criteria_ids
        )

        matched_risk_ids = [
            risk.risk_id
            for risk in analysis.business_risks
            if criterion_ids.intersection(risk.related_criteria)
        ]

        matched_ambiguity_ids = [
            ambiguity.ambiguity_id
            for ambiguity in analysis.ambiguities
            if criterion_ids.intersection(
                ambiguity.related_criteria
            )
        ]

        matched_assumptions = [
            assumption
            for assumption in analysis.assumptions
            if (
                assumption.status is not AssumptionStatus.REJECTED
                and criterion_ids.intersection(
                    assumption.related_criteria
                )
            )
        ]

        # The deterministic acceptance-criterion relationship is
        # the source of truth. AI-supplied IDs are not preserved
        # unless they are independently matched here.
        risk_ids = list(
            dict.fromkeys(matched_risk_ids)
        )

        ambiguity_ids = list(
            dict.fromkeys(matched_ambiguity_ids)
        )

        assumption_ids = list(
            dict.fromkeys(
                assumption.assumption_id
                for assumption in matched_assumptions
            )
        )

        requires_clarification = (
            bool(ambiguity_ids)
            or any(
                assumption.status
                is not AssumptionStatus.APPROVED
                for assumption in matched_assumptions
            )
        )

        status = (
            TestStatus.NEEDS_CLARIFICATION
            if requires_clarification
            else test_case.status
        )

        enriched_tests.append(
            test_case.model_copy(
                update={
                    "risk_ids": risk_ids,
                    "ambiguity_ids": ambiguity_ids,
                    "assumption_ids": assumption_ids,
                    "status": status,
                }
            )
        )

    return GeneratedTestCases(
        test_cases=enriched_tests
    )