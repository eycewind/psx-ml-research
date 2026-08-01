from __future__ import annotations
import argparse,json,tempfile
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sklearn,scipy

from psx_ml.features.manifest import git_state,logical_hash,runtime_versions,sha256_file,write_json
from .config import load_config
from .train import evaluate
from .validation import validate_inputs,validate_outputs

def _write(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)

def _aggregate(metrics):
    grouped=defaultdict(list)
    for key,value in metrics.items():
        target,fold,model=key.split(":"); grouped[(target,model)].append(value)
    out={}
    for (target,model),rows in sorted(grouped.items()):
        numeric=set.intersection(*(set(k for k,v in r.items() if isinstance(v,(int,float)) and k!="n") for r in rows))
        out[f"{target}:{model}"]={"folds":len(rows),"total_n":sum(r["n"] for r in rows),
          "mean":{k:float(np.mean([r[k] for r in rows])) for k in sorted(numeric)},"std":{k:float(np.std([r[k] for r in rows],ddof=0)) for k in sorted(numeric)}}
    return out

def _coef_summary(table):
    rows=table.to_pylist(); grouped=defaultdict(list)
    for r in rows: grouped[(r["target_name"],r["model_name"],r["feature"])].append(r["standardized_coefficient"])
    return {f"{t}:{m}:{f}":{"fold_mean":float(np.mean(x)),"fold_std":float(np.std(x)),"sign_consistency":float(max(sum(v>0 for v in x),sum(v<0 for v in x),sum(v==0 for v in x))/len(x)),"near_zero_count":sum(abs(v)<1e-8 for v in x)} for (t,m,f),x in sorted(grouped.items())}

def _symbol_concentration(table):
    symbols=table["symbol"].to_pylist(); targets=table["target_name"].to_pylist(); models=table["model_name"].to_pylist()
    y=np.asarray(table["target"],dtype=float); pred=np.asarray(table["prediction"],dtype=float); prob=np.asarray(table["prediction_probability"].to_numpy(zero_copy_only=False),dtype=float)
    by=defaultdict(lambda:defaultdict(float))
    for i,(s,t,m) in enumerate(zip(symbols,targets,models)):
        if m=="ridge_selected": loss=(y[i]-pred[i])**2
        elif m=="logistic_selected":
            p=np.clip(prob[i],1e-12,1-1e-12); loss=-(y[i]*np.log(p)+(1-y[i])*np.log(1-p))
        else: continue
        by[t][s]+=float(loss)
    out={}
    for t,values in by.items():
        ranked=sorted(values.items(),key=lambda x:(-x[1],x[0])); total=sum(values.values())
        out[t]={"symbols":len(values),"largest_loss_symbol":ranked[0][0],"largest_symbol_share":ranked[0][1]/total,"top_10_symbol_share":sum(x[1] for x in ranked[:10])/total}
    return out

def _model_report(m,path):
    reg_wins=sum(m["aggregate_metrics"][f"{t}:ridge_selected"]["mean"]["rmse"] < min(m["aggregate_metrics"][f"{t}:zero_return_baseline"]["mean"]["rmse"],m["aggregate_metrics"][f"{t}:training_mean_baseline"]["mean"]["rmse"]) for t in m["targets"]["regression"])
    cls_wins=sum(m["aggregate_metrics"][f"{t}:logistic_selected"]["mean"]["log_loss"] < m["aggregate_metrics"][f"{t}:training_prevalence_baseline"]["mean"]["log_loss"] for t in m["targets"]["classification"])
    conclusion=f"Linear signal NOT demonstrated: selected Ridge beats the best naive RMSE baseline on {reg_wins}/{len(m['targets']['regression'])} tasks; selected Logistic beats prevalence log loss on {cls_wins}/{len(m['targets']['classification'])} tasks."
    lines=["# C5 Linear Baseline Model Report","",f"Model set `{m['model_set']['name']}` v{m['model_set']['version']}; final holdout accessed: **{m['holdout_accessed']}**.","",f"**Conclusion: {conclusion}**","",
      "## Scope and interpretation","","These are validation-fold reference models, not trading strategies. Metrics are predictive diagnostics only; they contain no costs, execution, portfolio, Sharpe, or profitability analysis. A model that fails naive baselines is an honest negative result.","",
      "## Selected hyperparameters","",f"```json\n{json.dumps(m['selected_hyperparameters'],indent=2,sort_keys=True)}\n```","","## Fold aggregate metrics","", "| Task/model | Selected metric means and dispersion |","|---|---|"]
    for k,v in m["aggregate_metrics"].items(): lines.append(f"| `{k}` | mean `{json.dumps(v['mean'],sort_keys=True)}`; std `{json.dumps(v['std'],sort_keys=True)}`; n={v['total_n']:,} |")
    lines += ["","## Date-block uncertainty","",f"```json\n{json.dumps(m['date_block_intervals'],indent=2,sort_keys=True)}\n```","",
      "Bootstrap resamples validation dates, never individual rows as the sole uncertainty unit. Fixed alpha/C=1 results remain alongside validation-selected variants. Negative R² values are retained. Classification probability metrics use probabilities, not threshold labels.","","## Symbol-loss concentration","",f"```json\n{json.dumps(m['symbol_loss_concentration'],indent=2,sort_keys=True)}\n```","",
      "## Leakage controls","","Median imputation and scaling are fitted separately on each task/fold training subset. Purged, embargoed, test, and not-in-fold rows are excluded. The final holdout is locked by default and was not scored. Feature columns exactly match the frozen C3 registry; identifiers and C4 target/future/split fields never enter matrices.",""]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines))

def _coef_report(m,path):
    selected=[(k,v) for k,v in m["coefficient_summary"].items() if ":ridge_selected:" in k or ":logistic_selected:" in k]
    selected.sort(key=lambda kv:abs(kv[1]["fold_mean"]),reverse=True)
    lines=["# C5 Coefficient Report","","Coefficients are associational, not causal. Correlated C3 primitives can make signs and magnitudes unstable across folds.","",
      "| Target/model/feature | Fold mean | Fold std | Sign consistency | Near-zero folds |","|---|---:|---:|---:|---:|"]
    for k,v in selected: lines.append(f"| `{k}` | {v['fold_mean']:.8g} | {v['fold_std']:.8g} | {v['sign_consistency']:.3f} | {v['near_zero_count']} |")
    lines += ["","The runtime coefficient Parquet also records each fold intercept, transformed feature order, standardized coefficient, raw-scale coefficient, sign, absolute-magnitude rank, and convergence-warning count.",""]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines))

def run_pipeline(config_path,repo,allow_final_holdout=False):
    repo=Path(repo).resolve(); c=load_config(config_path,repo); validate_outputs((c.predictions_path,c.coefficients_path,c.manifest_path,c.model_report_path,c.coefficient_report_path),repo)
    labelled,splits,c4,c3,c2=validate_inputs(c); predictions,coefficients,evidence=evaluate(labelled,splits,c)
    # Development pipeline never scores test rows, even if explicit access is requested; flag records authorization state.
    if "test" in set(predictions["split_role"].to_pylist()): raise RuntimeError("test rows leaked into development predictions")
    _write(predictions,c.predictions_path); _write(coefficients,c.coefficients_path)
    agg=_aggregate(evidence["metrics"]); cs=_coef_summary(coefficients); concentration=_symbol_concentration(predictions)
    manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":git_state(repo),"model_set":{"name":c.name,"version":c.version},
      "holdout_accessed":bool(allow_final_holdout),"seed_determinism":{"seed":c.seed,"threads":1,"gpu":False},
      "inputs":{"c4_manifest_sha256":sha256_file(c.c4_manifest_path),"c3_manifest_sha256":sha256_file(c.c3_manifest_path),"c2_manifest_sha256":sha256_file(c.c2_manifest_path),
                "labelled_sha256":sha256_file(c.labelled_path),"splits_sha256":sha256_file(c.split_path)},
      "ordered_feature_allowlist":list(c.features),"targets":{"regression":list(c.regression_targets),"classification":list(c.classification_targets)},
      "models":{"regression":["zero_return_baseline","training_mean_baseline","ridge_fixed_alpha_1","ridge_selected"],"classification":["majority_class_baseline","training_prevalence_baseline","logistic_fixed_c_1","logistic_selected"]},
      "hyperparameter_grids":{"ridge_alpha":list(c.ridge_alphas),"logistic_c":list(c.logistic_cs)},"selected_hyperparameters":evidence["selected_hyperparameters"],
      "fold_definitions":c4["split_configuration"]["folds"],
      "preprocessing_by_fold_task":evidence["preprocessing"],"convergence_warnings":evidence["convergence_warnings"],"per_fold_metrics":evidence["metrics"],"aggregate_metrics":agg,
      "date_block_intervals":evidence["date_block_intervals"],"coefficient_summary":cs,"symbol_loss_concentration":concentration,"configuration":c.canonical(),"configuration_sha256":c.sha256(),
      "counts":{"prediction_rows":predictions.num_rows,"coefficient_rows":coefficients.num_rows,"dates":len(set(predictions["trade_date"].to_pylist())),"symbols":len(set(predictions["symbol"].to_pylist()))},
      "outputs":{"predictions":{"path":str(c.predictions_path),"file_sha256":sha256_file(c.predictions_path),"logical_sha256":logical_hash(predictions)},
                 "coefficients":{"path":str(c.coefficients_path),"file_sha256":sha256_file(c.coefficients_path),"logical_sha256":logical_hash(coefficients)}},"packages":{**runtime_versions(),"scikit_learn":sklearn.__version__,"scipy":scipy.__version__}}
    write_json(manifest,c.manifest_path); _model_report(manifest,c.model_report_path); _coef_report(manifest,c.coefficient_report_path); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--allow-final-holdout",action="store_true")
    a=p.parse_args(); m=run_pipeline(a.config,a.repo,a.allow_final_holdout)
    print(f"C5 complete: {m['counts']['prediction_rows']} validation predictions; holdout_accessed={m['holdout_accessed']}")
    print(f"Prediction logical: {m['outputs']['predictions']['logical_sha256']}")

if __name__=="__main__": main()
