from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from psx_ml.data.sqlite import connect_readonly

TABLE = "c17_eod_symbol_exclusions"
SOURCE = TABLE
REQUIRED_CONSUMER = "ML Phase A"


def _date(value: object) -> str:
    return pd.Timestamp(value).normalize().date().isoformat()


def _require_table(con: sqlite3.Connection) -> None:
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (TABLE,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Required watcher EOD exclusion table missing: {TABLE}")
    actual = {r["name"] for r in con.execute(f'PRAGMA table_info("{TABLE}")')}
    required = {"signal_date", "symbol", "reason"}
    missing = sorted(required - actual)
    if missing:
        raise ValueError(f"{TABLE} missing required columns: {missing}")


def load_eod_symbol_exclusions(source_db: Path, signal_date: object) -> list[dict[str, str]]:
    day = _date(signal_date)
    with connect_readonly(source_db) as con:
        _require_table(con)
        rows = [
            dict(row)
            for row in con.execute(
                f"""
                SELECT symbol, reason
                FROM {TABLE}
                WHERE signal_date = ?
                ORDER BY symbol, reason
                """,
                (day,),
            )
        ]

    normalized: list[dict[str, str]] = []
    for row in rows:
        symbol = "" if row["symbol"] is None else str(row["symbol"]).strip().upper()
        reason = "" if row["reason"] is None else str(row["reason"]).strip()
        if not symbol or not reason:
            raise ValueError(f"Malformed EOD symbol exclusion row for {day}: {row}")
        normalized.append({"symbol": symbol, "reason": reason})

    reasons_by_symbol: dict[str, set[str]] = {}
    for row in normalized:
        reasons_by_symbol.setdefault(row["symbol"], set()).add(row["reason"])
    conflicting = {
        symbol: sorted(reasons)
        for symbol, reasons in reasons_by_symbol.items()
        if len(reasons) > 1
    }
    if conflicting:
        raise ValueError(f"Conflicting EOD exclusion reasons for {day}: {conflicting}")

    return [
        {"symbol": symbol, "reason": sorted(reasons)[0]}
        for symbol, reasons in sorted(reasons_by_symbol.items())
    ]


def exclusion_symbols(exclusions: list[dict[str, str]]) -> set[str]:
    return {row["symbol"] for row in exclusions}
