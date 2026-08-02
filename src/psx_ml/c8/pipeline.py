from __future__ import annotations

import argparse,json,subprocess,tomllib
from datetime import datetime,timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import numpy as np
from psx_ml.features.manifest import git_state,logical_hash,sha256_file,write_json
from .relative_targets import build_relative_target_columns
from .sector_audit import sector_coverage_audit
from .context_features import build_context_features
from .sensitivity import sensitivity_audit
from .feature_variants import build_feature_variants
from .evaluation_train import run_evaluation
from .evaluation_reports import ablation_report,bucket_report,delivery_report,importance_stability,model_report

CANONICAL="pit_liquid_ordinary_equity_v1"

def _inside(repo:Path,value:str)->Path:
    p=(repo/value).resolve()
    if p!=repo and repo not in p.parents: raise ValueError(f"path outside repository: {p}")
    return p

def _write_parquet(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)

def run(config_path:Path,repo:Path,allow_final_holdout=False):
    if allow_final_holdout: raise RuntimeError("C8 final holdout access is locked")
    repo=repo.resolve(); raw=tomllib.loads(config_path.read_text()); code=git_state(repo)
    branch=subprocess.run(["git","-C",str(repo),"branch","--show-current"],check=True,capture_output=True,text=True).stdout.strip()
    code["branch"]=branch
    if branch!="feature/c8-market-relative-targets-and-context": raise RuntimeError("C8 must run on its required feature branch")
    paths={k:_inside(repo,v) for k,v in raw["input"].items()}
    universe=pq.read_table(paths["universe_path"],columns=["trade_date","symbol","universe_name","eligible","instrument_type"])
    mask=pc.and_(pc.equal(universe["universe_name"],CANONICAL),pc.and_(universe["eligible"],pc.equal(universe["instrument_type"],"ordinary_equity")))
    eligible={(r["trade_date"],r["symbol"]) for r in universe.filter(mask).to_pylist()}
    splits=pq.read_table(paths["split_path"],columns=["trade_date","symbol","fold_id","split_role"])
    split_rows=splits.to_pylist(); development_dates={r["trade_date"] for r in split_rows if r["split_role"] in {"train","validation"}}
    master=pq.read_table(paths["security_master_path"],columns=["symbol","sector"]).to_pylist(); sectors={r["symbol"]:r["sector"] for r in master if r["sector"]}
    c3=json.loads(paths["c3_manifest_path"].read_text()); c7_features=c3["ordered_features"]
    horizons=tuple(raw["target"]["horizons"]); cols=list(dict.fromkeys(["trade_date","symbol"]+c7_features+[f"fwd_open_to_close_ret_{h}s_adj" for h in horizons]))
    source=pq.read_table(paths["targets_path"],columns=cols)
    rows=[]
    for r in source.to_pylist():
        if (r["trade_date"],r["symbol"]) in eligible and r["trade_date"] in development_dates: rows.append({**r,"sector":sectors.get(r["symbol"])})
    derived=build_relative_target_columns(rows,horizons,int(raw["target"]["minimum_sector_peers"]),int(raw["target"]["relaxed_sector_peers"]),float(raw["target"]["shrinkage_strength"]))
    output_rows=[]
    for i,r in enumerate(rows): output_rows.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"sector":r["sector"],**{k:v[i] for k,v in derived.items()}})
    table=pa.Table.from_pylist(output_rows); out=_inside(repo,raw["output"]["relative_targets_path"]); _write_parquet(table,out)
    audit_rows,audit_summary,sector_coverage=sector_coverage_audit(rows,horizons,derived,int(raw["target"]["minimum_sector_peers"]))
    audit_table=pa.Table.from_pylist(audit_rows); coverage_table=pa.Table.from_pylist(sector_coverage)
    audit_path=_inside(repo,raw["output"]["sector_audit_path"]); coverage_path=_inside(repo,raw["output"]["sector_coverage_path"])
    _write_parquet(audit_table,audit_path); _write_parquet(coverage_table,coverage_path)
    sensitivity,sensitivity_coverage=sensitivity_audit(rows,horizons,derived)
    sensitivity_table=pa.Table.from_pylist(sensitivity); sensitivity_coverage_table=pa.Table.from_pylist(sensitivity_coverage)
    sensitivity_path=_inside(repo,raw["output"]["sector_sensitivity_path"]); sensitivity_coverage_path=_inside(repo,raw["output"]["sector_sensitivity_coverage_path"])
    _write_parquet(sensitivity_table,sensitivity_path); _write_parquet(sensitivity_coverage_table,sensitivity_coverage_path)
    context=build_context_features(rows,int(raw["target"]["minimum_sector_peers"]),60,30)
    keys=[{"trade_date":r["trade_date"],"symbol":r["symbol"],"sector":r["sector"]} for r in rows]
    def feature_table(names): return pa.Table.from_pylist([{**keys[i],**{n:context[n][i] for n in names}} for i in range(len(rows))])
    market_names=[n for n in context if n.startswith("market_") or n.startswith("eligible_symbol_count")]
    sector_names=[n for n in context if n.startswith("sector_")]
    relative_names=[n for n in context if n.startswith("stock_") or n.startswith("rolling_")]
    feature_outputs={}
    for label,names,path_key in (("market_features",market_names,"market_features_path"),("sector_features",sector_names,"sector_features_path"),("relative_features",relative_names,"relative_features_path")):
        ft=feature_table(names); fp=_inside(repo,raw["output"][path_key]); _write_parquet(ft,fp); feature_outputs[label]={"path":str(fp),"file_sha256":sha256_file(fp),"logical_sha256":logical_hash(ft),"features":names}
    row_index={(r["trade_date"],r["symbol"]):i for i,r in enumerate(rows)}; missing=[]
    for fold in sorted({r["fold_id"] for r in split_rows}):
        idx=sorted({row_index[(r["trade_date"],r["symbol"])] for r in split_rows if r["fold_id"]==fold and r["split_role"]=="validation" and (r["trade_date"],r["symbol"]) in row_index})
        for name,values in context.items():
            nulls=sum(values[i] is None for i in idx); missing.append({"fold_id":fold,"split_role":"validation","feature":name,"row_count":len(idx),"null_count":nulls,"null_fraction":nulls/len(idx) if idx else None})
    missing_table=pa.Table.from_pylist(missing); missing_path=_inside(repo,raw["output"]["feature_missingness_path"]); _write_parquet(missing_table,missing_path)
    folds=sorted({r["fold_id"] for r in split_rows}); roles={fold:np.full(len(rows),"not_in_fold",object) for fold in folds}
    for r in split_rows:
        i=row_index.get((r["trade_date"],r["symbol"]));
        if i is not None: roles[r["fold_id"]][i]=r["split_role"]
    variants=build_feature_variants(c7_features,market_names,sector_names,relative_names)
    eval_cfg={**raw["evaluation"],"horizons":tuple(raw["evaluation"]["horizons"])}
    pred_path=_inside(repo,raw["output"]["predictions_path"]); pred_tmp=pred_path.with_suffix(pred_path.suffix+".tmp")
    result=run_evaluation(rows,derived,context,roles,variants,eval_cfg,pred_tmp,_inside(repo,raw["output"]["models_root"])); pred_tmp.replace(pred_path)
    diagnostic_outputs={}
    for label,result_key,path_key in (("model_metrics","metrics","model_metrics_path"),("daily_ic","daily_ic","daily_ic_path"),("bucket_outcomes","buckets","bucket_outcomes_path"),("subgroup_metrics","subgroup_metrics","subgroup_metrics_path"),("feature_importance","feature_importance","feature_importance_path"),("training_diagnostics","training_diagnostics","training_diagnostics_path")):
        dt=pa.Table.from_pylist(result[result_key]); dp=_inside(repo,raw["output"][path_key]); _write_parquet(dt,dp); diagnostic_outputs[label]={"path":str(dp),"file_sha256":sha256_file(dp),"logical_sha256":logical_hash(dt),"rows":dt.num_rows}
    stability=importance_stability(result["feature_importance"])
    viewer={"manifest_version":1,"holdout_accessed":False,"aggregate_metrics":result["aggregate_metrics"],"artifacts":diagnostic_outputs,"feature_importance_stability":stability,"training_diagnostics":result["training_diagnostics"],"regime_thresholds":result["regime_thresholds"]}
    viewer_path=_inside(repo,raw["output"]["viewer_summary_path"]); write_json(viewer,viewer_path)
    counts={"rows":table.num_rows,"dates":len({r["trade_date"] for r in rows}),"symbols":len({r["symbol"] for r in rows}),"missing_sector_rows":sum(r["sector"] is None for r in rows)}
    for h in horizons:
        counts[f"valid_market_relative_{h}s"]=sum(x is not None for x in derived[f"fwd_market_relative_ret_{h}s"])
        counts[f"valid_sector_relative_{h}s"]=sum(x is not None for x in derived[f"fwd_sector_relative_ret_{h}s"])
    manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":code,"holdout_accessed":False,"canonical_universe":CANONICAL,"sector_provenance":"2026-08-01 security-master historical backcast","benchmark_definitions":{"market":"same-date eligible ordinary-equity leave-one-out median","sector":"same-date same-sector eligible ordinary-equity leave-one-out median","sector_minimum_policy":raw["target"]["sector_minimum_policy"],"minimum_sector_peers":raw["target"]["minimum_sector_peers"],"relaxed_sector_peers":raw["target"]["relaxed_sector_peers"],"shrinkage_rule":raw["target"]["shrinkage_rule"],"shrinkage_strength":raw["target"]["shrinkage_strength"]},"target_definitions":list(derived),"feature_definitions":{"market":market_names,"sector":sector_names,"relative":relative_names,"variants":variants,"ret_10obs":"compound current ret_5obs with the same symbol's five-observation-lag ret_5obs","rolling_window":60,"minimum_rolling_observations":30},"evaluation_configuration":eval_cfg,"selection_strategy":"fixed C7-derived configuration with train-internal chronological early stopping; outer validation never selects parameters","counts":counts,"evaluation_counts":{"prediction_rows":result["prediction_rows"],"fit_count":len(result["training_diagnostics"]),"metric_rows":len(result["metrics"]),"model_file_count":len(result["model_files"])},"aggregate_metrics":result["aggregate_metrics"],"sector_exclusion_summary":audit_summary,"sector_sensitivity_summary":sensitivity,"model_files":result["model_files"],"inputs":{k:{"path":str(v),"sha256":sha256_file(v)} for k,v in paths.items()},"outputs":{"relative_targets":{"path":str(out),"file_sha256":sha256_file(out),"logical_sha256":logical_hash(table)},"predictions":{"path":str(pred_path),"file_sha256":sha256_file(pred_path),"logical_sha256":sha256_file(pred_path)},"viewer_summary":{"path":str(viewer_path),"file_sha256":sha256_file(viewer_path)},"sector_audit":{"path":str(audit_path),"file_sha256":sha256_file(audit_path),"logical_sha256":logical_hash(audit_table)},"sector_coverage":{"path":str(coverage_path),"file_sha256":sha256_file(coverage_path),"logical_sha256":logical_hash(coverage_table)},"sector_sensitivity":{"path":str(sensitivity_path),"file_sha256":sha256_file(sensitivity_path),"logical_sha256":logical_hash(sensitivity_table)},"sector_sensitivity_coverage":{"path":str(sensitivity_coverage_path),"file_sha256":sha256_file(sensitivity_coverage_path),"logical_sha256":logical_hash(sensitivity_coverage_table)},"feature_missingness":{"path":str(missing_path),"file_sha256":sha256_file(missing_path),"logical_sha256":logical_hash(missing_table)},**feature_outputs,**diagnostic_outputs}}
    report=_inside(repo,raw["output"]["target_report_path"]); report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("# C8 Relative Target Report\n\nFinal holdout accessed: **false**.\n\nMarket and sector benchmarks are same-date leave-one-out medians. Sector eligibility requires five valid peers after exclusion. Sector labels retain the 2026-08-01 historical-backcast limitation.\n\n```json\n"+json.dumps(counts,indent=2,sort_keys=True)+"\n```\n")
    coverage_report=_inside(repo,raw["output"]["sector_coverage_report_path"])
    lines=["# C8 Sector Target Coverage Audit","","The canonical threshold remains five valid peers after leave-one-out. No lower-peer result is canonical.","","## Exclusion reasons","","| Horizon | Reason | Rows | Symbols | Dates | Sectors |","|---:|---|---:|---:|---:|---:|"]
    lines += [f"| {r['horizon']} | `{r['invalid_reason']}` | {r['row_count']} | {r['symbol_count']} | {r['date_count']} | {r['sector_count']} |" for r in audit_summary]
    lines += ["","## Coverage by sector","","| Horizon | Sector | Eligible rows | Valid rows | Coverage | Median valid peers | Minimum valid peers |","|---:|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {r['horizon']} | {r['sector']} | {r['eligible_rows']} | {r['valid_sector_relative_rows']} | {r['coverage_fraction']:.4f} | {r['median_peer_count']:.1f} | {r['minimum_peer_count']} |" for r in sector_coverage]
    lines += ["","## Frozen threshold sensitivity","","Strict five-peer remains canonical. Relaxed and shrunk variants require at least three valid peers. Shrinkage is `w=n/(n+5)` and was fixed before evaluation.","","| Horizon | Variant | Subset | Rows | Symbols | Dates | Sectors | Benchmark variance | Target variance | Newly usable sectors |","|---:|---|---|---:|---:|---:|---:|---:|---:|---|"]
    lines += [f"| {r['horizon']} | `{r['variant']}` | `{r['comparison_subset']}` | {r['valid_rows']} | {r['symbol_count']} | {r['date_count']} | {r['sector_count']} | {r['benchmark_variance']:.8g} | {r['target_variance']:.8g} | {r['newly_usable_sectors'] or '-'} |" for r in sensitivity]
    lines += ["","Daily IC, D10-D1 spread, and fold dispersion are model-dependent and will be appended after predictions exist; they are not inferred from target construction."]
    coverage_report.write_text("\n".join(lines)+"\n")
    feature_report=_inside(repo,raw["output"]["feature_report_path"])
    flines=["# C8 Context Feature Report","","All features use current or past observations only. Market and sector cross-sectional statistics are leave-one-out where the stock would otherwise contribute mechanically. Sector features require five valid peers; nulls remain explicit. The final 2026 holdout was inaccessible.","","## Feature families","",f"- Market context: {len(market_names)} features",f"- Sector context: {len(sector_names)} features",f"- Stock-relative: {len(relative_names)} features","","## Validation-fold missingness","","| Fold | Feature | Rows | Nulls | Null fraction |","|---|---|---:|---:|---:|"]
    flines += [f"| `{r['fold_id']}` | `{r['feature']}` | {r['row_count']} | {r['null_count']} | {r['null_fraction']:.4f} |" for r in missing]
    feature_report.write_text("\n".join(flines)+"\n")
    model_report(result,_inside(repo,raw["output"]["model_report_path"])); bucket_report(result,_inside(repo,raw["output"]["bucket_report_path"])); ablation_report(result,_inside(repo,raw["output"]["ablation_report_path"])); delivery_report(result,manifest,_inside(repo,raw["output"]["delivery_path"]))
    write_json(manifest,_inside(repo,raw["output"]["manifest_path"])); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--allow-final-holdout",action="store_true"); a=p.parse_args()
    result=run(a.config,a.repo,a.allow_final_holdout); print(f"C8 targets: {result['counts']['rows']} rows; holdout={result['holdout_accessed']}")

if __name__=="__main__": main()
