from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import quote


class SourceDatabaseError(RuntimeError):
    pass


def readonly_uri(path: str | Path) -> str:
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_file():
        raise SourceDatabaseError(f"Source database is not a file: {source}")
    return f"file:{quote(str(source), safe='/')}?mode=ro"


@contextmanager
def connect_readonly(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open an existing SQLite file with two independent write barriers."""
    uri = readonly_uri(path)
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA query_only=ON")
        if con.execute("PRAGMA query_only").fetchone()[0] != 1:
            raise SourceDatabaseError("SQLite query_only barrier did not engage")
        yield con
    finally:
        con.close()


def schema_snapshot(con: sqlite3.Connection) -> list[dict[str, object]]:
    result = []
    objects = con.execute(
        "SELECT name,type,sql FROM sqlite_master "
        "WHERE type IN ('table','view') ORDER BY name"
    )
    for obj in objects:
        name = obj["name"]
        result.append({
            "name": name,
            "type": obj["type"],
            "sql": obj["sql"],
            "columns": [dict(row) for row in con.execute(f'PRAGMA table_info("{name}")')],
            "indexes": [dict(row) for row in con.execute(f'PRAGMA index_list("{name}")')],
        })
    return result


def require_daily_schema(con: sqlite3.Connection, columns: list[str]) -> None:
    actual = {r["name"] for r in con.execute("PRAGMA table_info(daily_ohlc)")}
    missing = set(columns) - actual
    if missing:
        raise SourceDatabaseError(f"daily_ohlc missing required columns: {sorted(missing)}")
