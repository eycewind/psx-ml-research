from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from psx_ml.features.manifest import sha256_file

class TargetInputError(RuntimeError): pass

def validate_inputs(config):
    for p in (config.feature_path,config.feature_manifest_path,config.daily_path,config.c1_manifest_path):
        if not p.is_file(): raise TargetInputError(f"missing research input: {p}")
    fm=json.loads(config.feature_manifest_path.read_text()); c1=json.loads(config.c1_manifest_path.read_text())
    if fm.get("manifest_version")!=1 or c1.get("manifest_version")!=1: raise TargetInputError("unsupported input manifest version")
    features=pq.read_table(config.feature_path); daily=pq.read_table(config.daily_path)
    if sha256_file(config.feature_path)!=fm["output"]["file_sha256"]: raise TargetInputError("C3 feature hash mismatch")
    if sha256_file(config.daily_path)!=c1["outputs"]["daily"]["sha256"]: raise TargetInputError("C1 daily hash mismatch")
    if features.num_rows!=fm["output"]["rows"] or daily.num_rows!=c1["source_row_count"]: raise TargetInputError("input row count mismatch")
    required_f={"trade_date","symbol","point_in_time_eligible"}; required_d={"trade_date","symbol","open_adj","close_adj"}
    if not required_f.issubset(features.column_names) or not required_d.issubset(daily.column_names): raise TargetInputError("required target input columns missing")
    fk=list(zip(features["trade_date"].to_pylist(),features["symbol"].to_pylist())); dk=list(zip(daily["trade_date"].to_pylist(),daily["symbol"].to_pylist()))
    if len(fk)!=len(set(fk)) or len(dk)!=len(set(dk)): raise TargetInputError("duplicate input keys")
    if set(fk)!=set(dk): raise TargetInputError("feature/daily keys do not reconcile")
    return features,daily,fm,c1
