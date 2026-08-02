from __future__ import annotations
import hashlib,json,subprocess,tomllib
from pathlib import Path
import pyarrow.compute as pc
import pyarrow.parquet as pq
BRANCH="feature/c9-ranking-selection-robustness"
def inside(repo:Path,value:str)->Path:
    repo=repo.resolve(); path=(repo/value).resolve()
    if path!=repo and repo not in path.parents: raise ValueError(f"path outside repository: {path}")
    return path
def sha256(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load_config(path:Path): return tomllib.loads(path.read_text())
def validate_inputs(repo:Path,cfg:dict,allow_final_holdout=False):
    if allow_final_holdout: raise RuntimeError("C9 final 2026 holdout is locked")
    branch=subprocess.run(["git","-C",str(repo),"branch","--show-current"],check=True,capture_output=True,text=True).stdout.strip()
    if branch!=BRANCH: raise RuntimeError(f"C9 requires {BRANCH}, found {branch}")
    paths={k:inside(repo,v) for k,v in cfg["input"].items()}; manifest=json.loads(paths["c8_manifest_path"].read_text())
    if manifest.get("holdout_accessed") is not False or manifest.get("supplemental_evaluation",{}).get("holdout_accessed") is not False: raise RuntimeError("accepted C8 holdout provenance invalid")
    accepted=manifest["supplemental_evaluation"]["outputs"]["predictions"]["file_sha256"]
    if sha256(paths["c8_rank_predictions_path"])!=accepted: raise RuntimeError("C8 rank prediction hash mismatch")
    pf=pq.ParquetFile(paths["c8_rank_predictions_path"]); maximum=None
    for batch in pf.iter_batches(columns=["trade_date"]):
        value=pc.max(batch.column(0)).as_py(); maximum=value if maximum is None or value>maximum else maximum
    if str(maximum)>="2026-01-01": raise RuntimeError("2026 row detected in C9 input")
    return paths,manifest,{"branch":branch,"maximum_trade_date":str(maximum),"rank_prediction_rows":pf.metadata.num_rows,"hashes":{k:sha256(v) for k,v in paths.items()}}
