"""Tests for the SQLite execution-history repository."""

import json
from pathlib import Path

import pytest

from src.history_repository import (
    complete_execution,
    delete_execution,
    fail_execution,
    get_execution_json,
    initialize_database,
    list_executions,
    save_execution,
    start_execution,
)


def sample_test_pack_json() -> str:
    """Return a small valid TestPack JSON document."""

    return json.dumps(
        {
            "requirement_id": "BR-001",
            "test_cases": [
                {
                    "test_id": "UAT-001",
                    "title": "Verify successful transfer",
                }
            ],
        }
    )


def save_sample_execution(database_path: Path) -> int:
    """Save one reusable sample execution."""

    return save_execution(
        requirement_id="BR-001",
        title="Transfer money to an existing UK beneficiary",
        test_count=1,
        coverage_percentage=100.0,
        test_pack_json=sample_test_pack_json(),
        database_path=database_path,
    )


def test_initialize_database_creates_database_file(
    tmp_path: Path,
) -> None:
    """Database initialization must create the SQLite file."""

    database_path = tmp_path / "history.db"

    initialize_database(database_path)

    assert database_path.exists()


def test_saved_execution_appears_in_history(
    tmp_path: Path,
) -> None:
    """A saved execution must appear in the history list."""

    database_path = tmp_path / "history.db"

    execution_id = save_sample_execution(database_path)
    executions = list_executions(database_path)

    assert execution_id == 1
    assert len(executions) == 1
    assert executions[0].requirement_id == "BR-001"
    assert executions[0].test_count == 1
    assert executions[0].coverage_percentage == 100.0


def test_execution_history_is_newest_first(
    tmp_path: Path,
) -> None:
    """The most recently saved execution must appear first."""

    database_path = tmp_path / "history.db"

    first_id = save_sample_execution(database_path)

    second_id = save_execution(
        requirement_id="BR-002",
        title="Create a new beneficiary",
        test_count=2,
        coverage_percentage=100.0,
        test_pack_json=sample_test_pack_json(),
        database_path=database_path,
    )

    executions = list_executions(database_path)

    assert executions[0].execution_id == second_id
    assert executions[1].execution_id == first_id


def test_saved_test_pack_json_can_be_retrieved(
    tmp_path: Path,
) -> None:
    """The complete TestPack JSON must be retrievable."""

    database_path = tmp_path / "history.db"
    execution_id = save_sample_execution(database_path)

    stored_json = get_execution_json(
        execution_id,
        database_path,
    )

    assert stored_json is not None
    assert json.loads(stored_json) == json.loads(
        sample_test_pack_json()
    )


def test_missing_execution_returns_none(
    tmp_path: Path,
) -> None:
    """An unknown execution ID must return None."""

    database_path = tmp_path / "history.db"

    assert get_execution_json(999, database_path) is None


def test_execution_can_be_deleted(
    tmp_path: Path,
) -> None:
    """Deleting an execution must remove it from history."""

    database_path = tmp_path / "history.db"
    execution_id = save_sample_execution(database_path)

    deleted = delete_execution(execution_id, database_path)

    assert deleted is True
    assert list_executions(database_path) == []


def test_invalid_json_is_not_saved(
    tmp_path: Path,
) -> None:
    """The repository must reject malformed TestPack JSON."""

    database_path = tmp_path / "history.db"

    with pytest.raises(json.JSONDecodeError):
        save_execution(
            requirement_id="BR-001",
            title="Invalid TestPack",
            test_count=1,
            coverage_percentage=100.0,
            test_pack_json="this is not JSON",
            database_path=database_path,
        )

    assert list_executions(database_path) == []

def test_execution_can_be_started(
    tmp_path: Path,
) -> None:
    """A new workflow must initially have RUNNING status."""

    database_path = tmp_path / "history.db"

    execution_id = start_execution(
        requirement_id="BR-001",
        title="Transfer money",
        database_path=database_path,
    )

    executions = list_executions(database_path)

    assert execution_id == 1
    assert len(executions) == 1
    assert executions[0].status == "RUNNING"
    assert executions[0].started_at is not None
    assert executions[0].completed_at is None
    assert executions[0].duration_seconds is None

def test_running_execution_can_be_completed(
    tmp_path: Path,
) -> None:
    """A successful workflow must update its RUNNING record."""

    database_path = tmp_path / "history.db"

    execution_id = start_execution(
        requirement_id="BR-001",
        title="Transfer money",
        database_path=database_path,
    )

    complete_execution(
        execution_id=execution_id,
        test_count=1,
        coverage_percentage=100.0,
        test_pack_json=sample_test_pack_json(),
        database_path=database_path,
    )

    executions = list_executions(database_path)

    assert len(executions) == 1
    assert executions[0].status == "COMPLETED"
    assert executions[0].test_count == 1
    assert executions[0].coverage_percentage == 100.0
    assert executions[0].completed_at is not None
    assert executions[0].duration_seconds is not None

    stored_json = get_execution_json(
        execution_id,
        database_path,
    )

    assert stored_json is not None
    assert json.loads(stored_json) == json.loads(
        sample_test_pack_json()
    )

def test_running_execution_can_be_failed(
    tmp_path: Path,
) -> None:
    """A failed workflow must retain its failure details."""

    database_path = tmp_path / "history.db"

    execution_id = start_execution(
        requirement_id="BR-001",
        title="Transfer money",
        database_path=database_path,
    )

    fail_execution(
        execution_id=execution_id,
        failure_stage="analysis",
        error_message="Ollama request timed out.",
        database_path=database_path,
    )

    executions = list_executions(database_path)

    assert len(executions) == 1
    assert executions[0].status == "FAILED"
    assert executions[0].failure_stage == "analysis"
    assert (
        executions[0].error_message
        == "Ollama request timed out."
    )
    assert executions[0].completed_at is not None
    assert executions[0].duration_seconds is not None

    # Failed executions do not contain a valid TestPack.
    assert (
        get_execution_json(
            execution_id,
            database_path,
        )
        is None
    )

    