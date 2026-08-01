from __future__ import annotations
import json,tempfile
from pathlib import Path
import pyarrow.parquet as pq
from psx_ml.features.manifest import sha256_file

class ModelInputError(RuntimeError): pass
class HoldoutLockedError(PermissionError): pass
class OutputBoundaryError(ValueError): pass
WATCHER=Path('/home/hassan/psx-stock-watcher')

def validate_inputs(c):
    for p in (c.labelled_path,c.split_path,c.c4_manifest_path,c.c3_manifest_path,c.c2_manifest_path):
        if not p.is_file(): raise ModelInputError(f"missing research input {p}")
    c4=json.loads(c.c4_manifest_path.read_text()); c3=json.loads(c.c3_manifest_path.read_text()); c2=json.loads(c.c2_manifest_path.read_text())
    if sha256_file(c.labelled_path)!=c4["output"]["labelled"]["file_sha256"] or sha256_file(c.split_path)!=c4["output"]["splits"]["file_sha256"]: raise ModelInputError("C4 input hash mismatch")
    if list(c.features)!=c3["ordered_features"]: raise ModelInputError("feature allowlist must exactly match ordered C3 registry")
    labelled=pq.read_table(c.labelled_path); splits=pq.read_table(c.split_path)
    for f in c.features:
        if f not in labelled.column_names: raise ModelInputError(f"missing feature {f}")
    return labelled,splits,c4,c3,c2

def require_holdout_access(allow:bool):
    if not allow: raise HoldoutLockedError("final holdout is locked; pass --allow-final-holdout explicitly")

def validate_outputs(paths,repo):
    repo=Path(repo).resolve(); temp=Path(tempfile.gettempdir()).resolve()
    for p in paths:
        r=p.resolve()
        if r==WATCHER or WATCHER in r.parents: raise OutputBoundaryError(f"watcher output refused: {r}")
        if repo not in r.parents and r!=repo and temp not in r.parents and r!=temp: raise OutputBoundaryError(f"output outside research/temp: {r}")
