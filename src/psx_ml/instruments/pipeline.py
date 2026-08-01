from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq

from psx_ml.features.manifest import git_state, logical_hash, sha256_file, write_json
from psx_ml.universe.variants import membership_rows
from .classify import classify_intervals, validate_intervals
from .taxonomy import DEFINITIONS

def _load(path: Path) -> dict: return json.loads(path.read_text())
def _hash_config(obj: dict) -> str: return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _inside(path: Path, repo: Path) -> Path:
    p=(repo/path).resolve() if not path.is_absolute() else path.resolve()
    if not p.is_relative_to(repo): raise ValueError(f"C6 output outside repository: {p}")
    return p
def _write(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)

def run_foundation(repo: Path, instruments_path=Path("config/instruments.yaml"), universe_path=Path("config/universe_c6.yaml")):
    repo=repo.resolve(); ic=_load(repo/instruments_path); uc=_load(repo/universe_path)
    source_path=repo/"data/cache/daily_ohlcv.parquet"; pit_path=repo/"data/cache/point_in_time_universe.parquet"
    source=pq.read_table(source_path,columns=["trade_date","symbol","sector"]); pit=pq.read_table(pit_path)
    classes=classify_intervals(source,ic); validate_intervals(classes)
    membership=membership_rows(source,pit,classes,uc["variants"])
    class_path=_inside(Path("data/processed/universe/c6_instrument_classification.parquet"),repo)
    membership_path=_inside(Path("data/processed/universe/c6_universe_membership.parquet"),repo)
    _write(classes,class_path); _write(membership,membership_path)
    class_counts=Counter(classes["instrument_type"].to_pylist()); universe_counts=Counter()
    for r in membership.to_pylist():
        if r["eligible"]: universe_counts[r["universe_name"]]+=1
    manifest={"manifest_version":1,"stage":"classification_and_universe_foundation","generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "code":git_state(repo),"holdout_accessed":False,"inputs":{"daily_ohlcv":{"path":str(source_path),"file_sha256":sha256_file(source_path)},"pit_universe":{"path":str(pit_path),"file_sha256":sha256_file(pit_path)}},
      "taxonomy":{"version":ic["taxonomy_version"],"definitions":DEFINITIONS,"classification_hierarchy":["manual_mapping","observed_sector_rule","ticker_heuristic","unknown"],"config_sha256":_hash_config(ic)},
      "universe":{"version":uc["version"],"definitions":uc["variants"],"config_sha256":_hash_config(uc)},"class_interval_counts":dict(sorted(class_counts.items())),"unknown_intervals":class_counts["unknown"],"eligible_row_counts":dict(sorted(universe_counts.items())),
      "outputs":{"classification":{"path":str(class_path),"rows":classes.num_rows,"file_sha256":sha256_file(class_path),"logical_sha256":logical_hash(classes)},"membership":{"path":str(membership_path),"rows":membership.num_rows,"file_sha256":sha256_file(membership_path),"logical_sha256":logical_hash(membership)}}}
    report_dir=repo/"artifacts/reports"; report_dir.mkdir(parents=True,exist_ok=True)
    instrument=["# C6 Instrument Report","","## Evidence limitation","","C1–C5 contain contemporaneous symbol and numeric sector observations, but no authoritative security master or explicit instrument-type field. Sector and ticker classifications are therefore low-confidence research heuristics; unknowns remain explicit. No current classification is projected before its observed interval.","","## Taxonomy","",* [f"- `{k}`: {v}" for k,v in DEFINITIONS.items()],"","## Interval counts","",f"```json\n{json.dumps(dict(sorted(class_counts.items())),indent=2)}\n```",""]
    universe_report=["# C6 Universe Report","","All variants require the unchanged same-date C1 PIT liquidity flag. Classification exclusions are separate from liquidity and history exclusions; targets, predictions, returns, and residuals are not inputs.","","## Eligible row counts","",f"```json\n{json.dumps(dict(sorted(universe_counts.items())),indent=2)}\n```","","A C7 recommendation is deferred until robust diagnostics and stability checks are complete.",""]
    (report_dir/"C6_INSTRUMENT_REPORT.md").write_text("\n".join(instrument)); (report_dir/"C6_UNIVERSE_REPORT.md").write_text("\n".join(universe_report))
    write_json(manifest,report_dir/"C6_MANIFEST.json"); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); a=p.parse_args()
    m=run_foundation(a.repo); print(f"C6 foundation complete: {m['outputs']['classification']['rows']} intervals; {m['outputs']['membership']['rows']} membership rows")

if __name__=="__main__": main()
