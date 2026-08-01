from __future__ import annotations
import argparse,json,platform,time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import sklearn,lightgbm,xgboost
from psx_ml.features.manifest import git_state,logical_hash,sha256_file,write_json,runtime_versions
from .config import load_config
from .metrics import classification,regression
from .train import evaluate

def _write(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)
def _load_json(p): return json.loads(p.read_text())
def _aggregate(metrics):
    grouped=defaultdict(list)
    for key,v in metrics.items(): target,fold,model=key.split(":"); grouped[(target,model)].append(v)
    out={}
    for (target,model),rows in sorted(grouped.items()):
        names=sorted(set.intersection(*(set(k for k,v in r.items() if isinstance(v,(int,float)) and not isinstance(v,bool)) for r in rows)))
        out[f"{target}:{model}"]={"folds":len(rows),"mean":{k:float(np.mean([r[k] for r in rows])) for k in names},"std":{k:float(np.std([r[k] for r in rows])) for k in names},"total_n":sum(r["n"] for r in rows)}
    return out
def _baseline_rows(c5,keys):
    allowed={"zero_return_baseline","training_mean_baseline","ridge_fixed_alpha_1","majority_class_baseline","training_prevalence_baseline","logistic_fixed_c_1"}; out=[]
    for r in c5.to_pylist():
        if (r["trade_date"],r["symbol"]) in keys and r["model_name"] in allowed: out.append({**r,"universe_name":"pit_liquid_ordinary_equity_v1","device":"stored_c5"})
    return out
def _add_baseline_metrics(rows,metrics,seed,reps):
    grouped=defaultdict(list)
    for r in rows: grouped[(r["target_name"],r["fold_id"],r["model_name"])].append(r)
    for (target,fold,model),part in grouped.items():
        y=np.array([r["target"] for r in part]); dates=[r["trade_date"] for r in part]
        if target.startswith("up_"): p=np.array([r["prediction_probability"] for r in part]); met=classification(y,p,dates,seed,reps)
        else: p=np.array([r["prediction"] for r in part]); met=regression(y,p,dates,[r["symbol"] for r in part],seed,reps)
        metrics[f"{target}:{fold}:{model}"]=met
def _report(manifest,path):
    a=manifest["aggregate_metrics"]; lines=["# C7 Gradient-Boosted Tree Model Report","",f"Final holdout accessed: **{manifest['holdout_accessed']}**. Canonical universe: `{manifest['canonical_universe']}`.","","These are predictive validation diagnostics, not signals, portfolios, backtests, or profitability results.","","## Aggregate fold metrics","","| Task/model | Means | Fold standard deviations | N |","|---|---|---|---:|"]
    for k,v in a.items(): lines.append(f"| `{k}` | `{json.dumps(v['mean'],sort_keys=True)}` | `{json.dumps(v['std'],sort_keys=True)}` | {v['total_n']} |")
    lines += ["","## Selection policy","","LightGBM fold 2023 uses the fixed conservative default. Fold 2024 selection uses only fold 2023 evidence; fold 2025 uses only folds 2023–2024. Inner early stopping uses the chronological tail of the outer training period. HistGradientBoosting is fixed; XGBoost GPU is an independent fixed-configuration verification model.","",f"```json\n{json.dumps(manifest['selected_parameters'],indent=2,sort_keys=True)}\n```","","The final 2026 holdout remained locked.",""]
    path.write_text("\n".join(lines))
def _importance_report(table,path):
    rows=table.to_pylist(); grouped=defaultdict(list)
    for r in rows: grouped[(r["model_name"],r["feature"])].append(r["permutation_importance"])
    ranked=sorted(((m,f,float(np.mean(v)),float(np.std(v))) for (m,f),v in grouped.items()),key=lambda x:(x[0],-abs(x[2]),x[1]))
    lines=["# C7 Feature Importance Report","","Importance is associational, not causal. Permutation importance uses deterministic validation samples without refitting.","","| Model | Feature | Mean permutation importance | Fold/task std |","|---|---|---:|---:|"]+[f"| `{m}` | `{f}` | {mean:.8g} | {std:.8g} |" for m,f,mean,std in ranked]
    path.write_text("\n".join(lines)+"\n")
def run_pipeline(config_path,repo,allow_final_holdout=False):
    repo=Path(repo).resolve(); cfg=load_config(config_path,repo); code=git_state(repo)
    if allow_final_holdout: raise RuntimeError("C7 development pipeline does not score the final holdout")
    inp=cfg.raw["input"]; labelled=pq.read_table(cfg.path("input","labelled_path")); splits=pq.read_table(cfg.path("input","split_path")); universe=pq.read_table(cfg.path("input","universe_path"))
    c3=_load_json(cfg.path("input","c3_manifest_path"));
    if cfg.model["features"]!=c3["ordered_features"]: raise ValueError("C7 feature list differs from frozen C3 registry")
    predictions,importance,evidence=evaluate(labelled,splits,universe,cfg)
    keys={(r["trade_date"],r["symbol"]) for r in universe.to_pylist() if r["universe_name"]==cfg.model["canonical_universe"] and r["eligible"] and r["instrument_type"]=="ordinary_equity"}
    baselines=_baseline_rows(pq.read_table(cfg.path("input","c5_predictions_path")),keys); _add_baseline_metrics(baselines,evidence["metrics"],cfg.model["seed"],cfg.model["bootstrap_replicates"])
    all_rows=predictions.to_pylist()+baselines; all_rows.sort(key=lambda r:(r["target_name"],r["fold_id"],r["model_name"],r["trade_date"],r["symbol"])); predictions=pa.Table.from_pylist(all_rows)
    pred_path=cfg.path("output","predictions_path"); imp_path=cfg.path("output","importance_path"); _write(predictions,pred_path); _write(importance,imp_path)
    manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":code,"holdout_accessed":False,"canonical_universe":cfg.model["canonical_universe"],"historical_master_limitation":"C6 2026-08-01 PSX master classifications used historically are explicit backcasts.","configuration":cfg.canonical(),"configuration_sha256":cfg.sha256(),"ordered_features":cfg.model["features"],"targets":{"regression":cfg.model["regression_targets"],"classification":cfg.model["classification_targets"]},"selection_strategy":"sequential_walk_forward_with_train_internal_chronological_early_stopping","selected_parameters":evidence["selections"],"per_fold_metrics":evidence["metrics"],"aggregate_metrics":_aggregate(evidence["metrics"]),"runtime_statistics":evidence["runtimes"],"warnings":evidence["warnings"],"libraries":{"python":platform.python_version(),"sklearn":sklearn.__version__,"lightgbm":lightgbm.__version__,"xgboost":xgboost.__version__},"device":{"canonical":"cpu","xgboost_verification":"cuda","gpu":"NVIDIA GeForce RTX 5070 Laptop GPU"},"inputs":{k:{"path":str(cfg.path('input',k)),"file_sha256":sha256_file(cfg.path('input',k))} for k in inp},"counts":{"prediction_rows":predictions.num_rows,"importance_rows":importance.num_rows,"dates":len(set(predictions["trade_date"].to_pylist())),"symbols":len(set(predictions["symbol"].to_pylist()))},"outputs":{"predictions":{"path":str(pred_path),"file_sha256":sha256_file(pred_path),"logical_sha256":logical_hash(predictions)},"importance":{"path":str(imp_path),"file_sha256":sha256_file(imp_path),"logical_sha256":logical_hash(importance)}}}
    out=cfg.raw["output"]; report_dir=cfg.path("output","model_report_path").parent; report_dir.mkdir(parents=True,exist_ok=True); _report(manifest,cfg.path("output","model_report_path")); _importance_report(importance,cfg.path("output","importance_report_path"))
    runtime=["# C7 Runtime Report","",f"Canonical CPU mode uses one thread; XGBoost verification uses CUDA on `{manifest['device']['gpu']}`.","","| Task | Fold | Model | Device | Fit s | Predict s | Rounds | Train rows | Validation rows |","|---|---|---|---|---:|---:|---:|---:|---:|"]+[f"| `{r['target']}` | `{r['fold']}` | `{r['model']}` | `{r['device']}` | {r['fit_seconds']:.4f} | {r['predict_seconds']:.4f} | {r['rounds']} | {r['train_rows']} | {r['validation_rows']} |" for r in evidence["runtimes"]]; cfg.path("output","runtime_report_path").write_text("\n".join(runtime)+"\n")
    write_json(manifest,cfg.path("output","manifest_path")); return manifest
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--allow-final-holdout",action="store_true"); a=p.parse_args(); m=run_pipeline(a.config,a.repo,a.allow_final_holdout); print(f"C7 complete: {m['counts']['prediction_rows']} predictions; holdout={m['holdout_accessed']}")
if __name__=="__main__": main()
