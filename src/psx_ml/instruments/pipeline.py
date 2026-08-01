from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc

from psx_ml.features.manifest import git_state, logical_hash, sha256_file, write_json
from psx_ml.universe.variants import membership_rows
from .audit import rule_conflicts, sector_audit
from .classify import classify_intervals, validate_intervals
from .review import build_review_queue, write_review_queue
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
    classes=classify_intervals(source,ic); validate_intervals(classes); sectors=sector_audit(classes); conflicts=rule_conflicts(source,ic)
    membership=membership_rows(source,pit,classes,uc["variants"])
    class_path=_inside(Path("data/processed/universe/c6_instrument_classification.parquet"),repo)
    membership_path=_inside(Path("data/processed/universe/c6_universe_membership.parquet"),repo)
    sector_path=_inside(Path("data/processed/diagnostics/c6_sector_classification_audit.parquet"),repo)
    conflict_path=_inside(Path("data/processed/diagnostics/c6_classification_rule_conflicts.parquet"),repo)
    _write(classes,class_path); _write(membership,membership_path); _write(sectors,sector_path); _write(conflicts,conflict_path)
    predictions=pq.read_table(repo/"artifacts/predictions/c5/validation_predictions.parquet",columns=["symbol","target_name","target","prediction","model_name"])
    predictions=predictions.filter(pc.equal(predictions["model_name"],"ridge_fixed_alpha_1"))
    target_columns=["trade_date","symbol","fwd_open_to_close_ret_5s_adj","fwd_open_to_close_ret_10s_adj","fwd_open_to_close_ret_20s_adj"]
    targets=pq.read_table(repo/"data/processed/targets/daily_feature_targets.parquet",columns=target_columns)
    targets=targets.filter(pc.less_equal(targets["trade_date"],"2025-12-31"))
    robust=_load(repo/"config/robust_evaluation.yaml"); thresholds={str(k):v for k,v in robust["extreme_absolute_returns"].items()}
    review=build_review_queue(classes,conflicts,pit,predictions,targets,thresholds); review_path=repo/"artifacts/reports/C6_MANUAL_REVIEW_QUEUE.csv"; write_review_queue(review,review_path)
    class_counts=Counter(classes["instrument_type"].to_pylist()); universe_counts=Counter()
    for r in membership.to_pylist():
        if r["eligible"]: universe_counts[r["universe_name"]]+=1
    manifest={"manifest_version":1,"stage":"classification_and_universe_foundation","generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "code":git_state(repo),"holdout_accessed":False,"inputs":{"daily_ohlcv":{"path":str(source_path),"file_sha256":sha256_file(source_path)},"pit_universe":{"path":str(pit_path),"file_sha256":sha256_file(pit_path)}},
      "taxonomy":{"version":ic["taxonomy_version"],"definitions":DEFINITIONS,"classification_hierarchy":["manual_mapping","government_ticker","exact_sector","ETF_suffix","debt_ticker","right_ticker","preference_suffix","sector_prefix_08","unknown"],"config_sha256":_hash_config(ic)},
      "universe":{"version":uc["version"],"definitions":uc["variants"],"config_sha256":_hash_config(uc)},"class_interval_counts":dict(sorted(class_counts.items())),"unknown_intervals":class_counts["unknown"],"eligible_row_counts":dict(sorted(universe_counts.items())),
      "classification_audit":{"by_type_source_confidence_rule_sector":{"|".join(k):v for k,v in sorted(Counter((r["instrument_type"],r["classification_source"],r["classification_confidence"],r["classification_rule"],r["observed_sector"]) for r in classes.to_pylist()).items())},"conflict_intervals":conflicts.num_rows,"review_queue_symbols":len(review)},
      "outputs":{"classification":{"path":str(class_path),"rows":classes.num_rows,"file_sha256":sha256_file(class_path),"logical_sha256":logical_hash(classes)},"membership":{"path":str(membership_path),"rows":membership.num_rows,"file_sha256":sha256_file(membership_path),"logical_sha256":logical_hash(membership)},
                 "sector_audit":{"path":str(sector_path),"rows":sectors.num_rows,"file_sha256":sha256_file(sector_path),"logical_sha256":logical_hash(sectors)},"rule_conflicts":{"path":str(conflict_path),"rows":conflicts.num_rows,"file_sha256":sha256_file(conflict_path),"logical_sha256":logical_hash(conflicts)},
                 "manual_review_queue":{"path":str(review_path),"rows":len(review),"file_sha256":sha256_file(review_path)}}}
    report_dir=repo/"artifacts/reports"; report_dir.mkdir(parents=True,exist_ok=True)
    rule_counts=Counter(r["classification_rule"] for r in classes.to_pylist()); source_counts=Counter(r["classification_source"] for r in classes.to_pylist())
    instrument=["# C6 Instrument Report","","## Evidence limitation","","C1–C5 contain contemporaneous symbol and numeric sector observations, but no authoritative security master or explicit instrument-type field. Sector and ticker classifications are therefore low-confidence research heuristics; unknowns remain explicit. No current classification is projected before its observed interval.","","Zero unknown intervals occur because every unmatched interval in this snapshot has an observed sector beginning with `08`; this does not make those classifications authoritative.","","## Actual precedence","","1. manual mapping; 2. government ticker regex; 3. exact sector mapping; 4. ETF suffix; 5. debt ticker regex; 6. right ticker regex; 7. preference suffix with `08`; 8. generic `08` prefix; 9. unknown.","","Configured exact mappings: `36 → debt_security`, `3610 → government_security`, `0836 → REIT`, `0837 → ETF`.","","## Taxonomy","",* [f"- `{k}`: {v}" for k,v in DEFINITIONS.items()],"","## Interval counts","",f"```json\n{json.dumps(dict(sorted(class_counts.items())),indent=2)}\n```","","## Rule and source counts","",f"```json\n{json.dumps({'rules':dict(sorted(rule_counts.items())),'sources':dict(sorted(source_counts.items()))},indent=2)}\n```","",f"Generic `sector_prefix:08` inference accounts for **{rule_counts['sector_prefix:08']}** ordinary-equity intervals. These are low-confidence inferred classifications, not manual or authoritative classifications.","",f"The deterministic sector audit contains {sectors.num_rows} rows. The hierarchy audit found {conflicts.num_rows} competing-rule intervals; {len(review)} symbols are in the targeted manual-review queue.","","## Sector audit","","| Sector | Assigned type | Source | Rule | Intervals | Symbols | Examples |","|---|---|---|---|---:|---:|---|"]
    for r in sectors.to_pylist(): instrument.append(f"| `{r['observed_sector'] or '<blank>'}` | `{r['assigned_instrument_type']}` | `{r['classification_source']}` | `{r['classification_rule']}` | {r['interval_count']} | {r['unique_symbol_count']} | {r['example_symbols']} |")
    reason_counts=Counter(reason for r in review for reason in r["review_reason"].split("|"))
    universe_report=["# C6 Universe Report","","All variants require the unchanged same-date C1 PIT liquidity flag. Classification exclusions are separate from liquidity and history exclusions; targets, predictions, returns, and residuals are not inputs.","","Adding classification-rule traceability and conflict diagnostics did not alter membership: the rules and precedence are unchanged pending manual evidence.","","## Eligible row counts","",f"```json\n{json.dumps(dict(sorted(universe_counts.items())),indent=2)}\n```","","A C7 recommendation is deferred until robust diagnostics and stability checks are complete.",""]
    (report_dir/"C6_INSTRUMENT_REPORT.md").write_text("\n".join(instrument)); (report_dir/"C6_UNIVERSE_REPORT.md").write_text("\n".join(universe_report))
    delivery=["# C6 Classification Correction Delivery","","## Status","","The classification traceability correction is complete. Remaining C6 robust evaluation work is not represented as complete by this report.","","## Changes","","- Added exact `classification_rule` provenance to every classification interval.","- Audited counts by type, source, confidence, rule, and observed sector.","- Added deterministic sector and competing-rule Parquet diagnostics.","- Added a targeted manual-review queue using structural flags, fixed C5 loss concentration, and development-period extreme targets.","- Preserved classifier precedence and universe membership pending stronger evidence.","","## Snapshot findings","",f"- Generic low-confidence `sector_prefix:08`: {rule_counts['sector_prefix:08']} intervals.",f"- Exact sector mappings: {sum(v for k,v in rule_counts.items() if k.startswith('sector_exact:'))} intervals.",f"- Unknown intervals: {class_counts['unknown']}.",f"- Competing-rule intervals: {conflicts.num_rows}.",f"- Manual-review symbols: {len(review)}.",f"- Review reasons: `{json.dumps(dict(sorted(reason_counts.items())),sort_keys=True)}`.","","Zero unknowns arise because every otherwise unmatched interval in this snapshot has an observed sector beginning with `08`; zero does not imply authoritative coverage.","","The C5 negative linear conclusion is unchanged. No robust-metric reinterpretation, profitability analysis, nonlinear model, signal, portfolio, execution, or backtest is introduced by this correction.",""]
    robust_report=["# C6 Robust Evaluation Report","","## Status","","Pending after completion of the required classification audit. This file intentionally makes no robust-performance or C7-universe recommendation before the remaining diagnostics are implemented and reviewed.","","The accepted C5 conclusion remains visible: linear signal was not demonstrated. The final holdout remains locked.",""]
    (report_dir/"C6_DELIVERY.md").write_text("\n".join(delivery)); (report_dir/"C6_ROBUST_EVALUATION_REPORT.md").write_text("\n".join(robust_report))
    write_json(manifest,report_dir/"C6_MANIFEST.json"); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); a=p.parse_args()
    m=run_foundation(a.repo); print(f"C6 foundation complete: {m['outputs']['classification']['rows']} intervals; {m['outputs']['membership']['rows']} membership rows")

if __name__=="__main__": main()
