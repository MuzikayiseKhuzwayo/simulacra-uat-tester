"""Tests for the reusable TestScope AI workflow."""

import pytest

import src.workflow as workflow
from src.schemas import GeneratedTestCases
from src.workflow import WorkflowBlockedError
from tests.test_test_case_validators import (
    make_test_case,
    valid_analysis,
    valid_requirement,
)


def generated_tests() -> GeneratedTestCases:
    """Return valid generated tests for workflow testing."""

    return GeneratedTestCases(
        test_cases=[make_test_case()]
    )


def configure_successful_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replace Ollama calls with deterministic test doubles."""

    monkeypatch.setattr(
        workflow,
        "analyse_requirement",
        lambda requirement: valid_analysis(),
    )

    monkeypatch.setattr(
        workflow,
        "validate_analysis",
        lambda requirement, analysis: [],
    )

    monkeypatch.setattr(
        workflow,
        "generate_uat_tests",
        lambda requirement, analysis: generated_tests(),
    )

    monkeypatch.setattr(
        workflow,
        "enrich_test_traceability",
        lambda analysis, generated: generated,
    )

    monkeypatch.setattr(
        workflow,
        "validate_generated_test_cases",
        lambda requirement, analysis, generated: [],
    )


def test_successful_workflow_returns_test_pack(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_successful_workflow(monkeypatch)

    test_pack = workflow.run_uat_workflow(
        valid_requirement()
    )

    assert test_pack.requirement.requirement_id == "BR-001"
    assert len(test_pack.test_cases) == 1
    assert test_pack.coverage_summary.coverage_percentage == 100.0


def test_analysis_correction_is_attempted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = valid_analysis()
    validation_results = iter(
        [
            ["Analysis issue"],
            [],
        ]
    )
    correction_calls: list[bool] = []

    monkeypatch.setattr(
        workflow,
        "analyse_requirement",
        lambda requirement: analysis,
    )

    monkeypatch.setattr(
        workflow,
        "validate_analysis",
        lambda requirement, result: next(validation_results),
    )

    def correct(
        requirement,
        previous_analysis,
        issues,
    ):
        correction_calls.append(True)
        return analysis

    monkeypatch.setattr(
        workflow,
        "correct_analysis",
        correct,
    )

    result = workflow.obtain_validated_analysis(
        valid_requirement()
    )

    assert result == analysis
    assert len(correction_calls) == 1


def test_invalid_analysis_blocks_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = valid_analysis()

    monkeypatch.setattr(
        workflow,
        "analyse_requirement",
        lambda requirement: analysis,
    )

    monkeypatch.setattr(
        workflow,
        "validate_analysis",
        lambda requirement, result: ["Analysis remains invalid"],
    )

    monkeypatch.setattr(
        workflow,
        "correct_analysis",
        lambda requirement, previous, issues: analysis,
    )

    with pytest.raises(
        WorkflowBlockedError,
        match="requirement analysis",
    ):
        workflow.obtain_validated_analysis(
            valid_requirement()
        )


def test_test_case_correction_is_attempted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = valid_analysis()
    generated = generated_tests()
    validation_results = iter(
        [
            ["Test-case issue"],
            [],
        ]
    )
    correction_calls: list[bool] = []

    monkeypatch.setattr(
        workflow,
        "generate_uat_tests",
        lambda requirement, result: generated,
    )

    monkeypatch.setattr(
        workflow,
        "enrich_test_traceability",
        lambda result, tests: tests,
    )

    monkeypatch.setattr(
        workflow,
        "validate_generated_test_cases",
        lambda requirement, result, tests: next(
            validation_results
        ),
    )

    def correct(
        requirement,
        result,
        previous_tests,
        issues,
    ):
        correction_calls.append(True)
        return generated

    monkeypatch.setattr(
        workflow,
        "correct_generated_test_cases",
        correct,
    )

    result = workflow.obtain_validated_test_cases(
        valid_requirement(),
        analysis,
    )

    assert result == generated
    assert len(correction_calls) == 1


def test_invalid_test_cases_block_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = valid_analysis()
    generated = generated_tests()

    monkeypatch.setattr(
        workflow,
        "generate_uat_tests",
        lambda requirement, result: generated,
    )

    monkeypatch.setattr(
        workflow,
        "enrich_test_traceability",
        lambda result, tests: tests,
    )

    monkeypatch.setattr(
        workflow,
        "validate_generated_test_cases",
        lambda requirement, result, tests: [
            "Tests remain invalid"
        ],
    )

    monkeypatch.setattr(
        workflow,
        "correct_generated_test_cases",
        lambda requirement, result, previous, issues: generated,
    )

    with pytest.raises(
        WorkflowBlockedError,
        match="UAT test generation",
    ):
        workflow.obtain_validated_test_cases(
            valid_requirement(),
            analysis,
        )