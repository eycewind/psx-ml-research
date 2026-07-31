from __future__ import annotations

from pathlib import Path


def write_report(audit: dict, manifest: dict, path: Path) -> None:
    s=audit["summary"]; q=audit["quality_metrics"]
    lines=["# C1 Data Foundation and Audit Report","",
           f"Generated from `{manifest['source_database_path']}` in enforced read-only mode.","",
           "## Coverage","",
           f"- Rows: {s['rows']:,}",f"- Symbols: {s['symbols']:,}",f"- Trade dates: {s['dates']:,}",
           f"- Range: {s['min_date']} through {s['max_date']}",f"- Duplicate symbol-dates: {audit['duplicates']:,}","",
           "## Canonical fields","",
           "Raw OHLCV: `open`, `high`, `low`, `close`, `volume`. Adjusted fields: "
           "`open_adj`, `high_adj`, `low_adj`, `close_adj`, `volume_adj`, governed by `adj_factor`. "
           "Both are exported; adjusted integrity exceptions are not hidden.","",
           "## Quality metrics","",
           "| Metric | Count |","|---|---:|"]
    lines += [f"| `{k}` | {v:,} |" for k,v in q.items()]
    lines += ["","## Null counts","","| Field | Count |","|---|---:|"]
    lines += [f"| `{k}` | {v:,} |" for k,v in audit["null_counts"].items()]
    h=audit["history_summary"]
    lines += ["","## Missing and listing histories","",
              f"Histories are bounded by each symbol's first and last observation. {h['symbols']:,} symbols "
              f"were assessed; {h['symbols_with_gaps']:,} have gaps within their observed listing span; "
              f"median missing rate is {h['median_missing_rate']:.4%}.","",
              "## Point-in-time liquid universe proposal","",
              manifest["universe_methodology"],"",
              f"The proposal marks {manifest['universe_summary']['eligible_symbol_dates']:,} observed symbol-dates eligible; "
              f"{manifest['universe_summary']['latest_eligible_symbols']:,} symbols are eligible on the latest observed "
              f"date ({manifest['universe_summary']['latest_observed_date']}).","",
              "The calculation consumes observations in ascending date order and never consults a future row. "
              "The current/as-of-now watcher `universe` table is deliberately not used.","",
              "## Extraction provenance","",
              f"- Source SHA-256: `{manifest['source_database_sha256']}`",
              f"- Daily Parquet: {manifest['outputs']['daily']['rows']:,} rows, `{manifest['outputs']['daily']['sha256']}`",
              f"- PIT universe: {manifest['outputs']['point_in_time_universe']['rows']:,} rows, `{manifest['outputs']['point_in_time_universe']['sha256']}`","",
              "## Interpretation cautions","",
              "A close outside high/low is reported separately because the source documentation attributes this "
              "to PSX closing-auction behavior, an inference still awaiting authoritative verification. Zero-volume "
              "rows were omitted upstream, so missing observations cannot automatically be classified as data loss. "
              "Cash-dividend adjustment is not established by this dataset.",""]
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("\n".join(lines))
