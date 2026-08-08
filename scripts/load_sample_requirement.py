"""Load and validate the synthetic sample requirement."""

from pathlib import Path

from pydantic import ValidationError

from src.schemas import RequirementInput


# Locate the main project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Create the complete path to the JSON file.
SAMPLE_FILE = PROJECT_ROOT / "data" / "sample_requirement.json"


def load_sample_requirement() -> RequirementInput:
    """Read the JSON file and validate it using RequirementInput."""

    json_content = SAMPLE_FILE.read_text(encoding="utf-8")

    requirement = RequirementInput.model_validate_json(json_content)

    return requirement


def main() -> None:
    """Run the sample-requirement validation."""

    print("TestScope AI — Sample Requirement Loader")
    print("=" * 48)

    try:
        requirement = load_sample_requirement()

    except FileNotFoundError:
        print("FAILED: The sample requirement file was not found.")
        print(f"Expected file: {SAMPLE_FILE}")
        return

    except ValidationError as error:
        print("FAILED: The requirement does not match the schema.")
        print(error)
        return

    print("Result: SAMPLE REQUIREMENT ACCEPTED")
    print(f"Requirement ID: {requirement.requirement_id}")
    print(f"Title: {requirement.title}")
    print(f"Domain: {requirement.domain}")
    print(f"Feature: {requirement.feature}")
    print(f"Acceptance criteria: {len(requirement.acceptance_criteria)}")
    print(f"Business context items: {len(requirement.business_context)}")
    print(f"Known risks: {len(requirement.known_risks)}")

    print("\nAcceptance Criteria")

    for criterion in requirement.acceptance_criteria:
        print(f"- {criterion.criterion_id}: {criterion.description}")


if __name__ == "__main__":
    main()