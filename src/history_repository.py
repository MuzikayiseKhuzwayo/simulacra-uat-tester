"""SQLite persistence for generated TestScope execution history."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT / "data" / "testscope_history.db"
)

STATUS_RUNNING = "RUNNING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"


@dataclass(frozen=True)
class ExecutionSummary:
    """Summary information displayed in execution history."""

    execution_id: int
    requirement_id: str
    title: str
    created_at: str
    test_count: int
    coverage_percentage: float
    status: str
    started_at: str
    completed_at: str | None
    duration_seconds: float | None
    failure_stage: str | None
    error_message: str | None


def connect(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> sqlite3.Connection:
    """Open the SQLite database and return rows by column name."""

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Create or upgrade the execution-history table."""

    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                test_count INTEGER NOT NULL,
                coverage_percentage REAL NOT NULL,
                test_pack_json TEXT NOT NULL
            )
            """
        )

        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(executions)"
            ).fetchall()
        }

        additional_columns = {
            "status": (
                "TEXT NOT NULL DEFAULT 'COMPLETED'"
            ),
            "started_at": "TEXT",
            "completed_at": "TEXT",
            "duration_seconds": "REAL",
            "failure_stage": "TEXT",
            "error_message": "TEXT",
        }

        for column_name, column_definition in (
            additional_columns.items()
        ):
            if column_name not in existing_columns:
                connection.execute(
                    "ALTER TABLE executions "
                    f"ADD COLUMN {column_name} "
                    f"{column_definition}"
                )

        # Records created before observability was introduced
        # represent successful completed executions.
        connection.execute(
            """
            UPDATE executions
            SET started_at = created_at
            WHERE started_at IS NULL
            """
        )

        connection.execute(
            """
            UPDATE executions
            SET completed_at = created_at
            WHERE status = 'COMPLETED'
              AND completed_at IS NULL
            """
        )

        connection.commit()


def start_execution(
    requirement_id: str,
    title: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Create a RUNNING execution and return its ID."""

    if not requirement_id.strip():
        raise ValueError(
            "requirement_id must not be blank."
        )

    if not title.strip():
        raise ValueError(
            "title must not be blank."
        )

    initialize_database(database_path)

    started_at = datetime.now(timezone.utc).isoformat()

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO executions (
                requirement_id,
                title,
                created_at,
                test_count,
                coverage_percentage,
                test_pack_json,
                status,
                started_at,
                completed_at,
                duration_seconds,
                failure_stage,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                requirement_id.strip(),
                title.strip(),
                started_at,
                0,
                0.0,
                "{}",
                STATUS_RUNNING,
                started_at,
                None,
                None,
                None,
                None,
            ),
        )
        connection.commit()

        if cursor.lastrowid is None:
            raise RuntimeError(
                "SQLite did not return an execution ID."
            )

        return cursor.lastrowid


def complete_execution(
    execution_id: int,
    test_count: int,
    coverage_percentage: float,
    test_pack_json: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Mark a RUNNING execution as successfully completed."""

    if test_count < 0:
        raise ValueError(
            "test_count must not be negative."
        )

    if not 0 <= coverage_percentage <= 100:
        raise ValueError(
            "coverage_percentage must be between 0 and 100."
        )

    # Verify that the supplied TestPack is valid JSON.
    json.loads(test_pack_json)

    initialize_database(database_path)

    with connect(database_path) as connection:
        execution = connection.execute(
            """
            SELECT
                status,
                started_at,
                created_at
            FROM executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        ).fetchone()

        if execution is None:
            raise ValueError(
                f"Execution {execution_id} does not exist."
            )

        if execution["status"] != STATUS_RUNNING:
            raise ValueError(
                f"Execution {execution_id} is not RUNNING."
            )

        completed_datetime = datetime.now(timezone.utc)
        completed_at = completed_datetime.isoformat()

        started_at = (
            execution["started_at"]
            or execution["created_at"]
        )
        started_datetime = datetime.fromisoformat(
            started_at
        )

        duration_seconds = max(
            0.0,
            (
                completed_datetime - started_datetime
            ).total_seconds(),
        )

        connection.execute(
            """
            UPDATE executions
            SET
                status = ?,
                completed_at = ?,
                duration_seconds = ?,
                test_count = ?,
                coverage_percentage = ?,
                test_pack_json = ?,
                failure_stage = NULL,
                error_message = NULL
            WHERE execution_id = ?
            """,
            (
                STATUS_COMPLETED,
                completed_at,
                duration_seconds,
                test_count,
                coverage_percentage,
                test_pack_json,
                execution_id,
            ),
        )

        connection.commit()

def fail_execution(
    execution_id: int,
    failure_stage: str,
    error_message: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Mark a RUNNING execution as failed."""

    if not failure_stage.strip():
        raise ValueError(
            "failure_stage must not be blank."
        )

    if not error_message.strip():
        raise ValueError(
            "error_message must not be blank."
        )

    initialize_database(database_path)

    with connect(database_path) as connection:
        execution = connection.execute(
            """
            SELECT
                status,
                started_at,
                created_at
            FROM executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        ).fetchone()

        if execution is None:
            raise ValueError(
                f"Execution {execution_id} does not exist."
            )

        if execution["status"] != STATUS_RUNNING:
            raise ValueError(
                f"Execution {execution_id} is not RUNNING."
            )

        completed_datetime = datetime.now(timezone.utc)
        completed_at = completed_datetime.isoformat()

        started_at = (
            execution["started_at"]
            or execution["created_at"]
        )
        started_datetime = datetime.fromisoformat(
            started_at
        )

        duration_seconds = max(
            0.0,
            (
                completed_datetime - started_datetime
            ).total_seconds(),
        )

        connection.execute(
            """
            UPDATE executions
            SET
                status = ?,
                completed_at = ?,
                duration_seconds = ?,
                failure_stage = ?,
                error_message = ?
            WHERE execution_id = ?
            """,
            (
                STATUS_FAILED,
                completed_at,
                duration_seconds,
                failure_stage.strip(),
                error_message.strip(),
                execution_id,
            ),
        )

        connection.commit()


def save_execution(
    requirement_id: str,
    title: str,
    test_count: int,
    coverage_percentage: float,
    test_pack_json: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Save an already completed TestPack execution."""

    if not requirement_id.strip():
        raise ValueError(
            "requirement_id must not be blank."
        )

    if not title.strip():
        raise ValueError(
            "title must not be blank."
        )

    if test_count < 0:
        raise ValueError(
            "test_count must not be negative."
        )

    if not 0 <= coverage_percentage <= 100:
        raise ValueError(
            "coverage_percentage must be between 0 and 100."
        )

    # Verify that the supplied TestPack is valid JSON.
    json.loads(test_pack_json)

    initialize_database(database_path)

    completed_at = datetime.now(timezone.utc).isoformat()

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO executions (
                requirement_id,
                title,
                created_at,
                test_count,
                coverage_percentage,
                test_pack_json,
                status,
                started_at,
                completed_at,
                duration_seconds,
                failure_stage,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                requirement_id.strip(),
                title.strip(),
                completed_at,
                test_count,
                coverage_percentage,
                test_pack_json,
                STATUS_COMPLETED,
                completed_at,
                completed_at,
                0.0,
                None,
                None,
            ),
        )

        connection.commit()

        if cursor.lastrowid is None:
            raise RuntimeError(
                "SQLite did not return an execution ID."
            )

        return cursor.lastrowid


def list_executions(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[ExecutionSummary]:
    """Return saved executions with the newest first."""

    initialize_database(database_path)

    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                execution_id,
                requirement_id,
                title,
                created_at,
                test_count,
                coverage_percentage,
                status,
                started_at,
                completed_at,
                duration_seconds,
                failure_stage,
                error_message
            FROM executions
            ORDER BY execution_id DESC
            """
        ).fetchall()

    return [
        ExecutionSummary(
            execution_id=row["execution_id"],
            requirement_id=row["requirement_id"],
            title=row["title"],
            created_at=row["created_at"],
            test_count=row["test_count"],
            coverage_percentage=row[
                "coverage_percentage"
            ],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            duration_seconds=row["duration_seconds"],
            failure_stage=row["failure_stage"],
            error_message=row["error_message"],
        )
        for row in rows
    ]


def get_execution_json(
    execution_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> str | None:
    """Return JSON for a successfully completed execution."""

    initialize_database(database_path)

    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT test_pack_json
            FROM executions
            WHERE execution_id = ?
              AND status = ?
            """,
            (
                execution_id,
                STATUS_COMPLETED,
            ),
        ).fetchone()

    if row is None:
        return None

    return str(row["test_pack_json"])


def delete_execution(
    execution_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """Delete one saved execution."""

    initialize_database(database_path)

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        connection.commit()

        return cursor.rowcount > 0