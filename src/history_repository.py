"""SQLite persistence for generated TestScope execution history."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "testscope_history.db"


@dataclass(frozen=True)
class ExecutionSummary:
    """Summary information displayed in execution history."""

    execution_id: int
    requirement_id: str
    title: str
    created_at: str
    test_count: int
    coverage_percentage: float


def connect(database_path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open the SQLite database and return rows by column name."""

    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Create the execution-history table when it does not exist."""

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
        connection.commit()


def save_execution(
    requirement_id: str,
    title: str,
    test_count: int,
    coverage_percentage: float,
    test_pack_json: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Save a generated TestPack and return its execution ID."""

    if not requirement_id.strip():
        raise ValueError("requirement_id must not be blank.")

    if not title.strip():
        raise ValueError("title must not be blank.")

    if test_count < 0:
        raise ValueError("test_count must not be negative.")

    if not 0 <= coverage_percentage <= 100:
        raise ValueError(
            "coverage_percentage must be between 0 and 100."
        )

    # Ensure the supplied TestPack is valid JSON before saving it.
    json.loads(test_pack_json)

    initialize_database(database_path)

    created_at = datetime.now(timezone.utc).isoformat()

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO executions (
                requirement_id,
                title,
                created_at,
                test_count,
                coverage_percentage,
                test_pack_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                requirement_id.strip(),
                title.strip(),
                created_at,
                test_count,
                coverage_percentage,
                test_pack_json,
            ),
        )
        connection.commit()

        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return an execution ID.")

        return cursor.lastrowid


def list_executions(
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[ExecutionSummary]:
    """Return saved executions with the newest execution first."""

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
                coverage_percentage
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
            coverage_percentage=row["coverage_percentage"],
        )
        for row in rows
    ]


def get_execution_json(
    execution_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> str | None:
    """Return the saved TestPack JSON for one execution."""

    initialize_database(database_path)

    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT test_pack_json
            FROM executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        ).fetchone()

    if row is None:
        return None

    return str(row["test_pack_json"])


def delete_execution(
    execution_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """Delete one saved execution and report whether it existed."""

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