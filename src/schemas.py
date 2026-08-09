"""Pydantic data contracts shared across the TestScope AI application."""

from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
Identifier = NonEmptyString


class StrictModel(BaseModel):
    """Base model that rejects fields outside the documented contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AssumptionStatus(StrEnum):
    """Human-review state for an assumption."""

    PROPOSED = "Proposed"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class Severity(StrEnum):
    """Business-risk severity."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestType(StrEnum):
    """Supported UAT test categories."""

    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    BOUNDARY = "Boundary"
    END_TO_END = "End-to-End"
    ACCESSIBILITY = "Accessibility"


class Priority(StrEnum):
    """Test execution priority."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskLevel(StrEnum):
    """Business impact represented by a test case."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestStatus(StrEnum):
    """Review status for a generated test case."""

    DRAFT = "Draft"
    NEEDS_CLARIFICATION = "Needs Clarification"
    READY_FOR_REVIEW = "Ready for Review"


class AcceptanceCriterion(StrictModel):
    """One independently traceable acceptance criterion."""

    criterion_id: Identifier
    description: NonEmptyString


class RequirementInput(StrictModel):
    """Business requirement submitted for analysis."""

    requirement_id: Identifier
    title: NonEmptyString
    domain: NonEmptyString | None = None
    feature: NonEmptyString | None = None
    user_story: NonEmptyString
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    business_context: list[NonEmptyString] = Field(default_factory=list)
    known_risks: list[NonEmptyString] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_unique_criterion_ids(self) -> "RequirementInput":
        """Reject duplicate criterion IDs because they break traceability."""

        criterion_ids = [
            criterion.criterion_id for criterion in self.acceptance_criteria
        ]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("acceptance criterion IDs must be unique")
        return self


class BusinessRule(StrictModel):
    """Explicit rule extracted from the supplied requirement."""

    rule_id: Identifier
    description: NonEmptyString
    source_criteria: list[Identifier] = Field(min_length=1)


class Ambiguity(StrictModel):
    """Missing or unclear information requiring human clarification."""

    ambiguity_id: Identifier
    description: NonEmptyString
    impact: NonEmptyString
    clarification_question: NonEmptyString
    related_criteria: list[Identifier] = Field(min_length=1)


class Assumption(StrictModel):
    """Visible temporary interpretation requiring a review decision."""

    assumption_id: Identifier
    description: NonEmptyString
    related_criteria: list[Identifier] = Field(min_length=1)
    approval_required: bool
    status: AssumptionStatus


class BusinessRisk(StrictModel):
    """Business harm that should influence UAT design."""

    risk_id: Identifier
    description: NonEmptyString
    severity: Severity
    rationale: NonEmptyString
    related_criteria: list[Identifier] = Field(min_length=1)


class RequirementAnalysis(StrictModel):
    """Typed result produced by the requirement-analysis agent run."""

    requirement_summary: NonEmptyString
    business_rules: list[BusinessRule]
    ambiguities: list[Ambiguity]
    assumptions: list[Assumption]
    business_risks: list[BusinessRisk]


class TestStep(StrictModel):
    """One ordered action performed by a UAT tester."""

    step_number: int = Field(ge=1)
    action: NonEmptyString


class TestCase(StrictModel):
    """Structured and traceable UAT test case."""

    test_id: Identifier
    requirement_id: Identifier
    acceptance_criteria_ids: list[Identifier] = Field(min_length=1)
    title: NonEmptyString
    objective: NonEmptyString
    test_type: TestType
    priority: Priority
    risk_level: RiskLevel
    preconditions: list[NonEmptyString] = Field(min_length=1)
    test_data: list[NonEmptyString] = Field(min_length=1)
    steps: list[TestStep] = Field(min_length=1)
    expected_result: NonEmptyString
    assumption_ids: list[Identifier] = Field(default_factory=list)
    status: TestStatus

class GeneratedTestCases(StrictModel):
    """Structured test cases returned by the AI generator."""

    test_cases: list[TestCase] = Field(min_length=1)

class CoverageSummary(StrictModel):
    """Deterministically calculated traceability and quality summary."""

    total_criteria: int = Field(ge=0)
    covered_criteria: list[Identifier]
    uncovered_criteria: list[Identifier]
    coverage_percentage: float = Field(ge=0, le=100)
    tests_by_type: dict[TestType, int]
    high_risk_tests: list[Identifier]
    validation_warnings: list[NonEmptyString]


class TestPack(StrictModel):
    """Complete reviewable output of the TestScope AI workflow."""

    requirement: RequirementInput
    analysis: RequirementAnalysis
    test_cases: list[TestCase]
    coverage_summary: CoverageSummary
