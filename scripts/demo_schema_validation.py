"""Demonstrate how TestScope AI validates structured input."""

from pydantic import ValidationError

from src.schemas import AcceptanceCriterion, RequirementInput


def demonstrate_valid_input() -> None:
    """Create and display a valid requirement."""

    requirement = RequirementInput(
        requirement_id="BR-001",
        title="Transfer money to a UK beneficiary",
        domain="Banking",
        feature="Payments",
        user_story=(
            "As an authenticated customer, I want to transfer money to an "
            "existing UK beneficiary so that I can make a payment."
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
        business_context=["Transfers are made in GBP."],
        known_risks=["A customer could exceed the permitted daily limit."],
    )

    print("\n1. VALID REQUIREMENT")
    print("Result: ACCEPTED by Pydantic")
    print(requirement.model_dump_json(indent=2))


def print_validation_errors(error: ValidationError) -> None:
    """Print Pydantic errors in a beginner-friendly format."""

    for number, problem in enumerate(error.errors(), start=1):
        location = " -> ".join(str(part) for part in problem["loc"]) or "input"
        print(f"  {number}. {location}: {problem['msg']}")


def demonstrate_blank_title() -> None:
    """Show rejection of a required blank field."""

    print("\n2. INVALID REQUIREMENT — BLANK TITLE")
    try:
        RequirementInput(
            requirement_id="BR-002",
            title="   ",
            user_story="A customer transfers money.",
            acceptance_criteria=[
                {
                    "criterion_id": "AC-001",
                    "description": "The customer must be authenticated.",
                }
            ],
        )
    except ValidationError as error:
        print("Result: REJECTED by Pydantic")
        print_validation_errors(error)


def demonstrate_duplicate_ids() -> None:
    """Show rejection of duplicate traceability identifiers."""

    print("\n3. INVALID REQUIREMENT — DUPLICATE CRITERION IDs")
    try:
        RequirementInput(
            requirement_id="BR-003",
            title="Transfer money",
            user_story="A customer transfers money.",
            acceptance_criteria=[
                {
                    "criterion_id": "AC-001",
                    "description": "The customer must be authenticated.",
                },
                {
                    "criterion_id": "AC-001",
                    "description": "The transfer must respect the limit.",
                },
            ],
        )
    except ValidationError as error:
        print("Result: REJECTED by Pydantic")
        print_validation_errors(error)


def main() -> None:
    print("TestScope AI — Schema Validation Demonstration")
    print("=" * 48)
    demonstrate_valid_input()
    demonstrate_blank_title()
    demonstrate_duplicate_ids()
    print("\nThe application continues only when the input is valid.")


if __name__ == "__main__":
    main()
