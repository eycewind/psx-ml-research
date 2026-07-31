from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .manifest import sha256_file


class InputValidationError(RuntimeError): pass

REQUIRED_DAILY={"trade_date","symbol","open","high","low","close","volume",
 "open_adj","high_adj","low_adj","close_adj","volume_adj","adj_factor"}


def _unique(keys: list[tuple[str,str]]) -> bool: return len(keys)==len(set(keys))


def validate_inputs(config) -> tuple[object,object,dict]:
    for p in (config.daily_path,config.universe_path,config.input_manifest_path):
        if not p.is_file(): raise InputValidationError(f"Missing C1 input: {p}")
    manifest=json.loads(config.input_manifest_path.read_text())
    if manifest.get("manifest_version")!=1: raise InputValidationError("Unsupported C1 manifest version")
    daily=pq.read_table(config.daily_path); universe=pq.read_table(config.universe_path)
    if not REQUIRED_DAILY.issubset(daily.column_names): raise InputValidationError(f"Missing daily fields: {sorted(REQUIRED_DAILY-set(daily.column_names))}")
    required_u={"trade_date","symbol","eligible"}
    if not required_u.issubset(universe.column_names): raise InputValidationError(f"Missing universe fields: {sorted(required_u-set(universe.column_names))}")
    dkeys=list(zip(daily["trade_date"].to_pylist(),daily["symbol"].to_pylist()))
    ukeys=list(zip(universe["trade_date"].to_pylist(),universe["symbol"].to_pylist()))
    if not _unique(dkeys): raise InputValidationError("Duplicate daily (trade_date,symbol) keys")
    if not _unique(ukeys): raise InputValidationError("Duplicate universe (trade_date,symbol) keys")
    if set(dkeys)!=set(ukeys): raise InputValidationError("Daily and PIT universe keys do not reconcile")
    rows=len(dkeys); symbols=len({s for _,s in dkeys}); dates=[d for d,_ in dkeys]
    expected=(manifest.get("source_row_count"),manifest.get("symbol_count"),manifest.get("date_range"))
    actual=(rows,symbols,{"min":min(dates),"max":max(dates)})
    if expected!=actual: raise InputValidationError(f"Manifest reconciliation failed: expected {expected}, actual {actual}")
    outputs=manifest.get("outputs",{})
    if outputs.get("daily",{}).get("sha256")!=sha256_file(config.daily_path): raise InputValidationError("Daily Parquet hash mismatch")
    if outputs.get("point_in_time_universe",{}).get("sha256")!=sha256_file(config.universe_path): raise InputValidationError("Universe Parquet hash mismatch")
    return daily,universe,manifest
