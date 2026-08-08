"""Deterministic validation for AI-generated requirement analysis."""

from collections import Counter

from src.schemas import RequirementAnalysis, RequirementInput


def validate_analysis(
    requirement: RequirementInput,
    analysis: RequirementAnalysis,
) -> list[str]:
    """Return semantic and traceability issues in an AI analysis."""

    issues: list[str] = []

    valid_criterion_ids = {
        criterion.criterion_id
        for criterion in requirement.acceptance_criteria
    }

    # The agent should extract rules when criteria are available.
    if requirement.acceptance_criteria and not analysis.business_rules:
        issues.append(
            "No business rules were extracted from the acceptance criteria."
        )

    # Known risks should result in business-risk analysis.
    if requirement.known_risks and not analysis.business_risks:
        issues.append(
            "Known risks were supplied, but no business risks were generated."
        )

    # Check identifier prefixes.
    for rule in analysis.business_rules:
        if not rule.rule_id.startswith("RULE-"):
            issues.append(
                f"Business rule '{rule.rule_id}' must use the RULE- prefix."
            )

    for ambiguity in analysis.ambiguities:
        if not ambiguity.ambiguity_id.startswith("AMB-"):
            issues.append(
                f"Ambiguity '{ambiguity.ambiguity_id}' must use "
                "the AMB- prefix."
            )

    for assumption in analysis.assumptions:
        if not assumption.assumption_id.startswith("ASM-"):
            issues.append(
                f"Assumption '{assumption.assumption_id}' must use "
                "the ASM- prefix."
            )

        if not assumption.approval_required:
            issues.append(
                f"Assumption '{assumption.assumption_id}' must require "
                "human approval."
            )

    for risk in analysis.business_risks:
        if not risk.risk_id.startswith("RISK-"):
            issues.append(
                f"Business risk '{risk.risk_id}' must use "
                "the RISK- prefix."
            )

    # Check that generated identifiers are globally unique.
    generated_ids = [
        rule.rule_id
        for rule in analysis.business_rules
    ]

    generated_ids.extend(
        ambiguity.ambiguity_id
        for ambiguity in analysis.ambiguities
    )

    generated_ids.extend(
        assumption.assumption_id
        for assumption in analysis.assumptions
    )

    generated_ids.extend(
        risk.risk_id
        for risk in analysis.business_risks
    )

    duplicate_ids = sorted(
        identifier
        for identifier, count in Counter(generated_ids).items()
        if count > 1
    )

    for identifier in duplicate_ids:
        issues.append(
            f"Generated identifier '{identifier}' is duplicated."
        )

    # Check exact acceptance-criterion references.
    for rule in analysis.business_rules:
        for criterion_id in rule.source_criteria:
            if criterion_id not in valid_criterion_ids:
                issues.append(
                    f"Business rule '{rule.rule_id}' references unknown "
                    f"acceptance criterion '{criterion_id}'."
                )

    for ambiguity in analysis.ambiguities:
        for criterion_id in ambiguity.related_criteria:
            if criterion_id not in valid_criterion_ids:
                issues.append(
                    f"Ambiguity '{ambiguity.ambiguity_id}' references "
                    f"unknown acceptance criterion '{criterion_id}'."
                )

    for assumption in analysis.assumptions:
        for criterion_id in assumption.related_criteria:
            if criterion_id not in valid_criterion_ids:
                issues.append(
                    f"Assumption '{assumption.assumption_id}' references "
                    f"unknown acceptance criterion '{criterion_id}'."
                )

    for risk in analysis.business_risks:
        for criterion_id in risk.related_criteria:
            if criterion_id not in valid_criterion_ids:
                issues.append(
                    f"Business risk '{risk.risk_id}' references unknown "
                    f"acceptance criterion '{criterion_id}'."
                )

    # Check rule coverage of acceptance criteria.
    covered_criterion_ids = {
        criterion_id
        for rule in analysis.business_rules
        for criterion_id in rule.source_criteria
        if criterion_id in valid_criterion_ids
    }

    uncovered_criterion_ids = sorted(
        valid_criterion_ids - covered_criterion_ids
    )

    if uncovered_criterion_ids:
        issues.append(
            "Acceptance criteria not covered by extracted business rules: "
            + ", ".join(uncovered_criterion_ids)
        )

    return issues