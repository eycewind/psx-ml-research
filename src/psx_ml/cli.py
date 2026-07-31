from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

from .config import load_config
from .data.extract import build_manifest, export_daily, export_universe, write_json
from .data.sqlite import connect_readonly, require_daily_schema, schema_snapshot
from .reporting.audit_report import write_report
from .universe.point_in_time import build_point_in_time
from .validation.audit import audit_daily


METHODOLOGY=("For each observed symbol-date D, use at most the last 60 observations through D; "
             "require at least 40 observations, median raw close*volume of at least PKR 1,000,000, "
             "and unchanged-close fraction no greater than 20%. No row after D is consulted.")


def run(source_db: Path, repo: Path, config_path: Path) -> dict:
    config,config_hash=load_config(config_path)
    cache=repo/"data/cache"; reports=repo/"artifacts/reports"
    daily=cache/"daily_ohlcv.parquet"; universe=cache/"point_in_time_universe.parquet"
    with connect_readonly(source_db) as con:
        columns=config["extraction"]["columns"]
        require_daily_schema(con,columns)
        schema=schema_snapshot(con)
        audit=audit_daily(con,**config["audit"])
        daily_rows,sql=export_daily(con,columns,daily)
        u=config["universe"]
        universe_rows=export_universe(build_point_in_time(con,**u),universe)
        symbols=[r[0] for r in con.execute("SELECT DISTINCT symbol FROM daily_ohlc ORDER BY symbol")]
    manifest=build_manifest(source_db=source_db,source_stats=audit["summary"],symbols=symbols,
        sql=sql,repo=repo,config=config,config_sha256=config_hash,daily_path=daily,
        daily_rows=daily_rows,universe_path=universe,universe_rows=universe_rows,methodology=METHODOLOGY)
    ut=pq.read_table(universe,columns=["trade_date","eligible"])
    last=pc.max(ut["trade_date"]).as_py()
    last_mask=pc.equal(ut["trade_date"],last)
    manifest["universe_summary"]={
        "eligible_symbol_dates":pc.sum(pc.cast(ut["eligible"],"int64")).as_py(),
        "latest_observed_date":last,
        "latest_eligible_symbols":pc.sum(pc.cast(pc.filter(ut["eligible"],last_mask),"int64")).as_py(),
    }
    write_json(schema,reports/"C1_SCHEMA.json")
    write_json(audit,reports/"C1_AUDIT.json")
    write_json(manifest,reports/"C1_MANIFEST.json")
    write_report(audit,manifest,reports/"C1_AUDIT_REPORT.md")
    return manifest


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["run"])
    p.add_argument("--source-db",type=Path,required=True)
    p.add_argument("--repo",type=Path,default=Path.cwd())
    p.add_argument("--config",type=Path)
    a=p.parse_args(); repo=a.repo.resolve(); config=a.config or repo/"config/c1.toml"
    manifest=run(a.source_db,repo,config)
    print(f"C1 complete: {manifest['source_row_count']} rows; {manifest['maximum_source_trade_date']}")


if __name__ == "__main__": main()
