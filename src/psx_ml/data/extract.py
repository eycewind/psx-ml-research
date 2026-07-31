from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pyarrow as pa
import pyarrow.parquet as pq


def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_batches(records: Iterable[dict], path: Path, batch_size: int = 20000) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer=None; batch=[]; total=0
    try:
        for record in records:
            batch.append(record)
            if len(batch) >= batch_size:
                table=pa.Table.from_pylist(batch)
                writer = writer or pq.ParquetWriter(path, table.schema, compression="zstd", use_dictionary=False)
                writer.write_table(table, row_group_size=batch_size); total += len(batch); batch=[]
        if batch:
            table=pa.Table.from_pylist(batch)
            writer = writer or pq.ParquetWriter(path, table.schema, compression="zstd", use_dictionary=False)
            writer.write_table(table, row_group_size=batch_size); total += len(batch)
        if writer is None:
            raise ValueError("Cannot export an empty dataset")
    finally:
        if writer is not None: writer.close()
    return total


def export_daily(con: sqlite3.Connection, columns: list[str], path: Path) -> tuple[int,str]:
    quoted=",".join(f'"{c}"' for c in columns)
    sql=f"SELECT {quoted} FROM daily_ohlc ORDER BY trade_date,symbol"
    rows=(dict(r) for r in con.execute(sql))
    return _write_batches(rows,path), sql


def export_universe(records: Iterable[dict], path: Path) -> int:
    return _write_batches(records,path)


def git_version(repo: Path) -> str:
    try:
        return subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],check=True,
                              text=True,capture_output=True).stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return "uncommitted-or-unavailable"


def build_manifest(*, source_db: Path, source_stats: dict, symbols: list[str],
                   sql: str, repo: Path, config: dict, config_sha256: str,
                   daily_path: Path, daily_rows: int, universe_path: Path,
                   universe_rows: int, methodology: str) -> dict:
    return {
        "manifest_version":1,
        "source_database_path":str(source_db.resolve()),
        "source_database_sha256":sha256_file(source_db),
        "extraction_timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "maximum_source_trade_date":source_stats["max_date"],
        "source_row_count":source_stats["rows"],
        "symbols_included":symbols,
        "symbol_count":len(symbols),
        "date_range":{"min":source_stats["min_date"],"max":source_stats["max_date"]},
        "sql_extraction_definition":sql,
        "code_git_version":git_version(repo),
        "adjusted_raw_field_selection":config["extraction"]["columns"],
        "universe_methodology":methodology,
        "universe_configuration":config["universe"],
        "config_sha256":config_sha256,
        "outputs":{
            "daily":{"path":str(daily_path),"rows":daily_rows,"sha256":sha256_file(daily_path)},
            "point_in_time_universe":{"path":str(universe_path),"rows":universe_rows,"sha256":sha256_file(universe_path)},
        },
        "runtime":{"python":platform.python_version(),"pyarrow":pa.__version__},
    }


def write_json(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
