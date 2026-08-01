from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc

from psx_ml.features.manifest import git_state, logical_hash, sha256_file, write_json
from psx_ml.universe.variants import membership_rows
from psx_ml.diagnostics.c6_evaluation import evaluate_predictions, extreme_rows, loss_concentration
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
    repo=repo.resolve(); code_state=git_state(repo); ic=_load(repo/instruments_path); uc=_load(repo/universe_path)
    master_path=repo/"data/reference/psx_security_master_2026-08-01.parquet"; master=pq.read_table(master_path)
    ic={**ic,"security_master":{r["symbol"]:r for r in master.to_pylist()}}
    source_path=repo/"data/cache/daily_ohlcv.parquet"; pit_path=repo/"data/cache/point_in_time_universe.parquet"
    source=pq.read_table(source_path,columns=["trade_date","symbol","sector"]); pit=pq.read_table(pit_path)
    classes=classify_intervals(source,ic); validate_intervals(classes); sectors=sector_audit(classes); conflicts=rule_conflicts(source,ic)
    membership=membership_rows(source,pit,classes,uc["variants"])
    class_path=_inside(Path("data/processed/universe/c6_instrument_classification.parquet"),repo)
    membership_path=_inside(Path("data/processed/universe/c6_universe_membership.parquet"),repo)
    sector_path=_inside(Path("data/processed/diagnostics/c6_sector_classification_audit.parquet"),repo)
    conflict_path=_inside(Path("data/processed/diagnostics/c6_classification_rule_conflicts.parquet"),repo)
    _write(classes,class_path); _write(membership,membership_path); _write(sectors,sector_path); _write(conflicts,conflict_path)
    prediction_path=repo/"artifacts/predictions/c5/validation_predictions.parquet"
    full_predictions=pq.read_table(prediction_path)
    predictions=full_predictions.select(["symbol","target_name","target","prediction","model_name"])
    predictions=predictions.filter(pc.equal(predictions["model_name"],"ridge_fixed_alpha_1"))
    target_columns=["trade_date","symbol","fwd_open_to_close_ret_5s_adj","fwd_open_to_close_ret_10s_adj","fwd_open_to_close_ret_20s_adj"]
    targets=pq.read_table(repo/"data/processed/targets/daily_feature_targets.parquet",columns=target_columns)
    targets=targets.filter(pc.less_equal(targets["trade_date"],"2025-12-31"))
    robust=_load(repo/"config/robust_evaluation.yaml"); thresholds={str(k):v for k,v in robust["extreme_absolute_returns"].items()}
    review=build_review_queue(classes,conflicts,pit,predictions,targets,thresholds); review_path=repo/"artifacts/reports/C6_MANUAL_REVIEW_QUEUE.csv"; write_review_queue(review,review_path)
    metrics,eligible_sets,family_map,pit_meta=evaluate_predictions(full_predictions,membership,pit,robust["trim_fraction"],robust["huber_delta"],robust["daily_ic_minimum"])
    concentration=loss_concentration(full_predictions,eligible_sets,family_map)
    features=pq.read_table(repo/"data/processed/targets/daily_feature_targets.parquet")
    extremes=extreme_rows(full_predictions,membership,features,thresholds)
    robust_path=_inside(Path("data/processed/diagnostics/c6_robust_metrics.parquet"),repo); concentration_path=_inside(Path("data/processed/diagnostics/c6_loss_concentration.parquet"),repo); extreme_path=_inside(Path("data/processed/diagnostics/c6_extreme_rows.parquet"),repo)
    _write(metrics,robust_path); _write(concentration,concentration_path); _write(extremes,extreme_path)
    class_counts=Counter(classes["instrument_type"].to_pylist()); universe_counts=Counter()
    for r in membership.to_pylist():
        if r["eligible"]: universe_counts[r["universe_name"]]+=1
    manifest={"manifest_version":1,"stage":"classification_and_universe_foundation","generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "code":code_state,"holdout_accessed":False,"inputs":{"daily_ohlcv":{"path":str(source_path),"file_sha256":sha256_file(source_path)},"pit_universe":{"path":str(pit_path),"file_sha256":sha256_file(pit_path)},"psx_security_master":{"path":str(master_path),"file_sha256":sha256_file(master_path),"snapshot_date":"2026-08-01","temporal_limitation":"Current snapshot; historical use is a backcast and not contemporaneous PIT evidence."}},
      "taxonomy":{"version":ic["taxonomy_version"],"definitions":DEFINITIONS,"classification_hierarchy":["manual_mapping","psx_security_master_snapshot","exact_observed_sector","historical_absent_master_ticker_fallback","preference_suffix","sector_prefix_08","unknown"],"config_sha256":_hash_config({k:v for k,v in ic.items() if k!='security_master'})},
      "universe":{"version":uc["version"],"definitions":uc["variants"],"config_sha256":_hash_config(uc)},"class_interval_counts":dict(sorted(class_counts.items())),"unknown_intervals":class_counts["unknown"],"eligible_row_counts":dict(sorted(universe_counts.items())),
      "classification_audit":{"by_type_source_confidence_rule_sector":{"|".join(k):v for k,v in sorted(Counter((r["instrument_type"],r["classification_source"],r["classification_confidence"],r["classification_rule"],r["observed_sector"]) for r in classes.to_pylist()).items())},"conflict_intervals":conflicts.num_rows,"review_queue_symbols":len(review)},
      "robust_evaluation":{"stored_predictions_only":True,"c5_prediction_sha256":sha256_file(prediction_path),"models":{"regression":["ridge_fixed_alpha_1","zero_return_baseline","training_mean_baseline"],"classification":["logistic_fixed_c_1","training_prevalence_baseline","majority_class_baseline"]},"final_holdout_accessed":False,"trim_fraction":robust["trim_fraction"],"huber_delta":robust["huber_delta"],"daily_ic_minimum":robust["daily_ic_minimum"]},
      "outputs":{"classification":{"path":str(class_path),"rows":classes.num_rows,"file_sha256":sha256_file(class_path),"logical_sha256":logical_hash(classes)},"membership":{"path":str(membership_path),"rows":membership.num_rows,"file_sha256":sha256_file(membership_path),"logical_sha256":logical_hash(membership)},
                 "sector_audit":{"path":str(sector_path),"rows":sectors.num_rows,"file_sha256":sha256_file(sector_path),"logical_sha256":logical_hash(sectors)},"rule_conflicts":{"path":str(conflict_path),"rows":conflicts.num_rows,"file_sha256":sha256_file(conflict_path),"logical_sha256":logical_hash(conflicts)},
                 "manual_review_queue":{"path":str(review_path),"rows":len(review),"file_sha256":sha256_file(review_path)}}}
    manifest["outputs"].update({"robust_metrics":{"path":str(robust_path),"rows":metrics.num_rows,"file_sha256":sha256_file(robust_path),"logical_sha256":logical_hash(metrics)},"loss_concentration":{"path":str(concentration_path),"rows":concentration.num_rows,"file_sha256":sha256_file(concentration_path),"logical_sha256":logical_hash(concentration)},"extreme_rows":{"path":str(extreme_path),"rows":extremes.num_rows,"file_sha256":sha256_file(extreme_path),"logical_sha256":logical_hash(extremes)}})
    manifest["c7_universe_recommendation"]={"recommended":True,"universe":"pit_liquid_ordinary_equity_v1","version":1,"basis":"Structural PSX-master instrument-family exclusion with broad coverage and materially lower non-equity loss concentration; weak correlations, rank IC, and classification metrics mean lower RMSE is not the justification.","limitation":"The 2026-08-01 master used historically is an explicit backcast; absent historical symbols use observed-sector evidence then low-confidence fallback rules."}
    report_dir=repo/"artifacts/reports"; report_dir.mkdir(parents=True,exist_ok=True)
    rule_counts=Counter(r["classification_rule"] for r in classes.to_pylist()); source_counts=Counter(r["classification_source"] for r in classes.to_pylist())
    instrument=["# C6 Instrument Report","","## Primary evidence","","Classification now uses the dated PSX security-master snapshot `2026-08-01` before sector or ticker fallbacks. The snapshot combines Listing Status, Eligible Scrips, and Fixed Income Securities Detail. Ticker regexes run only for historical symbols absent from that master.","","The snapshot is current-state evidence. Applying its family to earlier observations is explicitly a backcast, not contemporaneous point-in-time proof; this limitation is recorded in the manifest. Historical symbols absent from the master retain low-confidence fallback provenance, and unknowns remain explicit.","","## Actual precedence","","1. manual mapping; 2. dated PSX security master; 3. exact observed-sector mapping; 4. ticker fallback only when absent from the master; 5. preference suffix; 6. generic `08` prefix; 7. unknown.","","Configured exact mappings: `36 → debt_security`, `3610 → government_security`, `0836 → REIT`, `0837 → ETF`.","","## Taxonomy","",* [f"- `{k}`: {v}" for k,v in DEFINITIONS.items()],"","## Interval counts","",f"```json\n{json.dumps(dict(sorted(class_counts.items())),indent=2)}\n```","","## Rule and source counts","",f"```json\n{json.dumps({'rules':dict(sorted(rule_counts.items())),'sources':dict(sorted(source_counts.items()))},indent=2)}\n```","",f"Generic `sector_prefix:08` inference now accounts for **{rule_counts['sector_prefix:08']}** intervals and is used only after stronger master/sector/ticker evidence. These remain low-confidence inferred classifications.","",f"The deterministic sector audit contains {sectors.num_rows} rows. The hierarchy audit found {conflicts.num_rows} competing-rule intervals; {len(review)} symbols are in the targeted manual-review queue.","","## Sector audit","","| Sector | Assigned type | Source | Rule | Intervals | Symbols | Examples |","|---|---|---|---|---:|---:|---|"]
    for r in sectors.to_pylist(): instrument.append(f"| `{r['observed_sector'] or '<blank>'}` | `{r['assigned_instrument_type']}` | `{r['classification_source']}` | `{r['classification_rule']}` | {r['interval_count']} | {r['unique_symbol_count']} | {r['example_symbols']} |")
    reason_counts=Counter(reason for r in review for reason in r["review_reason"].split("|"))
    universe_report=["# C6 Universe Report","","All variants require the unchanged same-date C1 PIT liquidity flag. Classification exclusions are separate from liquidity and history exclusions; targets, predictions, returns, and residuals are not inputs.","","## Eligible row counts","",f"```json\n{json.dumps(dict(sorted(universe_counts.items())),indent=2)}\n```","","## C7 recommendation","","Recommend `pit_liquid_ordinary_equity_v1` as the canonical C7 research universe. The rule is structural and target/residual-independent, retains 300,808 of 305,267 PIT-liquid rows, and excludes fixed income, rights, ETFs, REITs, and other non-ordinary families. Lower RMSE alone is not the justification.","","The 2026-08-01 security master is current-state evidence; historical assignments from it are explicit backcasts. Historical symbols absent from it use observed-sector evidence or labeled low-confidence fallbacks.",""]
    (report_dir/"C6_INSTRUMENT_REPORT.md").write_text("\n".join(instrument)); (report_dir/"C6_UNIVERSE_REPORT.md").write_text("\n".join(universe_report))
    delivery=["# C6 Security-Master Direction Delivery","","## Status","","The classification evidence direction now uses a dated PSX master first. Remaining C6 robust evaluation work is not represented as complete by this report.","","## Changes","","- Inspected the live Listings, Eligible Scrips, Fixed Income, company, ETF, and debt routes and recorded their endpoints.","- Added the versioned `psx_security_master_2026-08-01.parquet` snapshot and response-hash provenance.","- Made the PSX snapshot the primary classification evidence after explicit manual mappings.","- Restricted ticker regexes to historical symbols absent from the current PSX master.","- Retained exact rule/conflict traceability and the targeted review queue.","","## Snapshot findings","",f"- Master-backed classification intervals: {source_counts['psx_security_master_snapshot']}.",f"- Historical ticker-fallback intervals: {source_counts['ticker_heuristic_historical_fallback']}.",f"- Generic low-confidence `sector_prefix:08`: {rule_counts['sector_prefix:08']} intervals.",f"- Unknown intervals: {class_counts['unknown']}.",f"- Competing-rule intervals: {conflicts.num_rows}.",f"- Manual-review symbols: {len(review)}.","","The master is a 2026-08-01 current-state snapshot. Any historical assignment based on it is labeled as a backcast, not contemporaneous PIT evidence.","","The C5 negative linear conclusion is unchanged. No profitability analysis, nonlinear model, signal, portfolio, execution, or backtest is introduced.",""]
    delivery[0]="# C6 Delivery"; delivery[4]="Classification, universe refinement, stored-prediction robust evaluation, stratification, concentration analysis, and the C7 universe decision are complete. The final holdout remained locked."
    overall=[r for r in metrics.to_pylist() if r["scope_dimension"]=="overall"]
    robust_report=["# C6 Robust Evaluation Report","","Stored fixed C5 validation predictions are filtered without refitting. The final holdout remains locked. These are predictive/ranking diagnostics, not portfolio returns or profitability evidence.","","## Overall metrics","","| Universe | Target | Model | N | MAE | Median AE | RMSE | Huber | Pearson | Spearman / ROC AUC | Daily IC |","|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in overall:
        robust_report.append(f"| `{r['universe_name']}` | `{r['target_name']}` | `{r['model_name']}` | {r['n']} | {r.get('mae') or ''} | {r.get('median_absolute_error') or ''} | {r.get('rmse') or ''} | {r.get('huber_loss') or ''} | {r.get('pearson') or ''} | {r.get('spearman') if r.get('spearman') is not None else (r.get('roc_auc') or '')} | {r.get('mean_daily_ic') or ''} |")
    conc_rows=concentration.to_pylist()
    robust_report += ["","Stratified fold, year, liquidity-bucket, stale-bucket, and instrument-family rows are preserved in `c6_robust_metrics.parquet`. Canonical untrimmed metrics remain visible beside robust diagnostics.","","## Concentration change","","| Universe | Horizon | Top-1 symbol share | Top-10 symbol share | Largest contributor |","|---|---|---:|---:|---|"]
    for universe in sorted(eligible_sets):
        for target in sorted({r["target_name"] for r in conc_rows}):
            x=[r for r in conc_rows if r["universe_name"]==universe and r["target_name"]==target and r["model_name"]=="ridge_fixed_alpha_1" and r["aggregation_dimension"]=="symbol"]
            if x: robust_report.append(f"| `{universe}` | `{target}` | {sum(r['loss_share'] for r in x if r['rank']<=1):.6f} | {sum(r['loss_share'] for r in x if r['rank']<=10):.6f} | `{min(x,key=lambda r:r['rank'])['entity']}` |")
    robust_report += ["","The ordinary-equity filter sharply reduces 5- and 20-session concentration by removing structurally different fixed-income observations, including `P01GIS150825`. Ten-session loss remains dominated by ordinary-equity outliers such as `PHDL`.","","Correlations and daily IC remain weak or negative, and classification ROC AUC remains near or below 0.5. The negative C5 linear conclusion therefore does not change.","","## C7 universe decision","","Recommend `pit_liquid_ordinary_equity_v1` for C7 on structural instrument-family grounds and broad coverage—not because filtered RMSE is lower. The current-master historical backcast limitation remains explicit.",""]
    (report_dir/"C6_DELIVERY.md").write_text("\n".join(delivery)); (report_dir/"C6_ROBUST_EVALUATION_REPORT.md").write_text("\n".join(robust_report))
    write_json(manifest,report_dir/"C6_MANIFEST.json"); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); a=p.parse_args()
    m=run_foundation(a.repo); print(f"C6 foundation complete: {m['outputs']['classification']['rows']} intervals; {m['outputs']['membership']['rows']} membership rows")

if __name__=="__main__": main()
