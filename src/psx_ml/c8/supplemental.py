from __future__ import annotations

import argparse, hashlib, json, pickle, time, tomllib
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.features.manifest import git_state, sha256_file, write_json
from psx_ml.models.metrics import classification_metrics
from psx_ml.tree_models.datasets import inner_chronological
from psx_ml.tree_models.models import lgb_model, predict, xgb_model
from .supplemental_metrics import rank_metrics

RANK_TASKS=[(h,v) for h in (5,10) for v in ("B_market_context","D_full_context")]
CLASS_TASKS=[(h,f) for h in (5,10) for f in ("market","sector")]
MODELS=("lightgbm_cpu","xgboost_gpu")

def _map(path): return {(r["trade_date"],r["symbol"]):r for r in pq.read_table(path).to_pylist()}

def _stop(model,name):
    if name=="lightgbm_cpu":
        vals=next(iter(model.evals_result_["valid_0"].values()))
        best=int(model.best_iteration_ or len(vals)); return best,float(vals[best-1]),float(vals[0]),len(vals)
    metric=next(iter(model.evals_result()["validation_0"])); vals=model.evals_result()["validation_0"][metric]
    return int(model.best_iteration+1),float(model.best_score),float(vals[0]),len(vals)

def _fit(kind,name,x,y,train,valid,dates,cfg):
    it,iv,boundary=inner_chronological(dates,train,cfg["inner_validation_fraction"]); rounds=cfg["boosting_max_rounds"]
    if name=="lightgbm_cpu":
        inner=lgb_model(kind,cfg["lightgbm"],cfg["seed"],rounds,cfg["threads"])
        inner.fit(x[it],y[it],eval_set=[(x[iv],y[iv])],callbacks=[lgb.early_stopping(cfg["early_stopping_rounds"],verbose=False)])
        stop=_stop(inner,name); model=lgb_model(kind,cfg["lightgbm"],cfg["seed"],stop[0],cfg["threads"]); device="cpu"
    else:
        inner=xgb_model(kind,cfg["xgboost"],cfg["seed"],rounds,cfg["threads"],"cuda"); inner.set_params(early_stopping_rounds=cfg["early_stopping_rounds"])
        inner.fit(x[it],y[it],eval_set=[(x[iv],y[iv])],verbose=False); stop=_stop(inner,name)
        model=xgb_model(kind,cfg["xgboost"],cfg["seed"],stop[0],cfg["threads"],"cuda"); device="cuda"
    start=time.perf_counter(); model.fit(x[train],y[train]); fit=time.perf_counter()-start
    return model,predict(model,x[valid],kind),stop,boundary,device,fit

def _save(model,name,stem,root):
    root.mkdir(parents=True,exist_ok=True)
    if name=="lightgbm_cpu": path=root/f"{stem}.txt"; model.booster_.save_model(str(path))
    else: path=root/f"{stem}.json"; model.save_model(path)
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def _aggregate(rows,metric):
    values=[r[metric] for r in rows if r.get(metric) is not None]
    return float(np.mean(values)) if values else None

def run(repo:Path,config:Path):
    repo=repo.resolve(); raw=tomllib.loads(config.read_text()); cfg=raw["evaluation"]
    manifest=json.loads((repo/"artifacts/reports/C8_MANIFEST.json").read_text()); assert manifest["holdout_accessed"] is False
    rel=_map(repo/raw["output"]["relative_targets_path"]); source=_map(repo/raw["input"]["targets_path"])
    market=_map(repo/raw["output"]["market_features_path"]); sector=_map(repo/raw["output"]["sector_features_path"]); relative=_map(repo/raw["output"]["relative_features_path"])
    keys=sorted(rel); rows=[]
    for key in keys: rows.append({**source[key],**rel[key],**market[key],**sector[key],**relative[key]})
    dates=np.asarray([k[0] for k in keys],object); symbols=np.asarray([k[1] for k in keys],object)
    split=pq.read_table(repo/raw["input"]["split_path"]).to_pylist(); index={k:i for i,k in enumerate(keys)}; folds=sorted({r["fold_id"] for r in split})
    roles={f:np.full(len(rows),"not_in_fold",object) for f in folds}
    for r in split:
        i=index.get((r["trade_date"],r["symbol"]));
        if i is not None: roles[r["fold_id"]][i]=r["split_role"]
    variants=manifest["feature_definitions"]["variants"]; result={"rank":[],"classification":[],"calibration":[],"diagnostics":[],"models":[],"predictions":[]}
    for h,variant in RANK_TASKS:
        target=f"fwd_market_relative_rank_{h}s"; outcome=f"fwd_market_relative_ret_{h}s"; features=variants[variant]
        x=np.asarray([[np.nan if r.get(f) is None else r[f] for f in features] for r in rows],float); y=np.asarray([np.nan if r.get(target) is None else r[target] for r in rows]); out=np.asarray([np.nan if r.get(outcome) is None else r[outcome] for r in rows])
        for fold in folds:
            train=(roles[fold]=="train")&np.isfinite(y); valid=(roles[fold]=="validation")&np.isfinite(y)&np.isfinite(out)
            for name in MODELS:
                model,p,stop,boundary,device,fit=_fit("regression",name,x,y,train,valid,dates,cfg)
                met,daily,buckets=rank_metrics(y[valid],out[valid],p,dates[valid],symbols[valid],cfg["minimum_daily_population"],cfg["seed"],cfg["bootstrap_replicates"])
                meta={"task_type":"rank","target_name":target,"horizon":h,"feature_variant":variant,"model_name":name,"fold_id":fold}
                result["rank"].append({**meta,**met,"fold_daily_metrics":daily,"bucket_outcome_means":buckets})
                stem=f"rank_{h}_{variant}_{fold}_{name}"; result["models"].append({**meta,**_save(model,name,stem,repo/"artifacts/models/c8_supplemental")})
                result["diagnostics"].append({**meta,"device":device,"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"best_iteration":stop[0],"best_inner_score":stop[1],"first_iteration_score":stop[2],"last_evaluated_iteration":stop[3],"inner_boundary":boundary,"fit_seconds":fit,"prediction_std":float(np.std(p))})
                result["predictions"] += [{**meta,"trade_date":d,"symbol":s,"target":float(a),"outcome":float(o),"prediction":float(q),"prediction_probability":None} for d,s,a,o,q in zip(dates[valid],symbols[valid],y[valid],out[valid],p)]
    for h,family in CLASS_TASKS:
        target=f"outperform_{family}_{h}s"; variant="B_market_context" if family=="market" else "D_full_context"; features=variants[variant]
        x=np.asarray([[np.nan if r.get(f) is None else r[f] for f in features] for r in rows],float); y=np.asarray([np.nan if r.get(target) is None else r[target] for r in rows])
        for fold in folds:
            train=(roles[fold]=="train")&np.isfinite(y); valid=(roles[fold]=="validation")&np.isfinite(y); prevalence=float(np.mean(y[train])); base=np.full(valid.sum(),prevalence)
            base_metric=classification_metrics(y[valid],base); meta={"task_type":"classification","target_name":target,"horizon":h,"feature_variant":variant,"model_name":"prevalence_baseline","fold_id":fold}
            result["classification"].append({**meta,**base_metric}); result["calibration"].append({**meta,"bins":base_metric.pop("calibration_bins")})
            for name in MODELS:
                model,p,stop,boundary,device,fit=_fit("classification",name,x,y,train,valid,dates,cfg); met=classification_metrics(y[valid],p)
                meta={**meta,"model_name":name}; bins=met.pop("calibration_bins"); result["classification"].append({**meta,**met}); result["calibration"].append({**meta,"bins":bins})
                stem=f"classification_{family}_{h}_{variant}_{fold}_{name}"; result["models"].append({**meta,**_save(model,name,stem,repo/"artifacts/models/c8_supplemental")})
                result["diagnostics"].append({**meta,"device":device,"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"best_iteration":stop[0],"best_inner_score":stop[1],"first_iteration_score":stop[2],"last_evaluated_iteration":stop[3],"inner_boundary":boundary,"fit_seconds":fit,"prediction_std":float(np.std(p))})
                result["predictions"] += [{**meta,"trade_date":d,"symbol":s,"target":float(a),"outcome":None,"prediction":float(q>=.5),"prediction_probability":float(q)} for d,s,a,q in zip(dates[valid],symbols[valid],y[valid],p)]
    result["summary"]={"rank":[],"classification":[]}
    for h,v in RANK_TASKS:
      for name in MODELS:
        part=[r for r in result["rank"] if r["horizon"]==h and r["feature_variant"]==v and r["model_name"]==name]
        result["summary"]["rank"].append({"horizon":h,"feature_variant":v,"model_name":name,"fold_ic":[r["mean_daily_ic"] for r in part],"mean_daily_ic":_aggregate(part,"mean_daily_ic"),"median_daily_ic":_aggregate(part,"median_daily_ic"),"positive_ic_date_fraction":_aggregate(part,"positive_ic_date_fraction"),"fold_ic_std":float(np.std([r["mean_daily_ic"] for r in part])),"ndcg_5":_aggregate(part,"ndcg_5"),"ndcg_10":_aggregate(part,"ndcg_10"),"top_decile_capture":_aggregate(part,"top_decile_capture"),"d10_d1_spread":_aggregate(part,"d10_d1_spread"),"bucket_monotonicity":_aggregate(part,"bucket_monotonicity")})
    for h,family in CLASS_TASKS:
      for name in (*MODELS,"prevalence_baseline"):
        part=[r for r in result["classification"] if r["horizon"]==h and r["target_name"]==f"outperform_{family}_{h}s" and r["model_name"]==name]
        result["summary"]["classification"].append({"horizon":h,"target_name":f"outperform_{family}_{h}s","model_name":name,**{k:_aggregate(part,k) for k in ("roc_auc","pr_auc","log_loss","brier","balanced_accuracy","precision","recall","f1","prevalence")},"fold_roc_auc":[r["roc_auc"] for r in part],"fold_roc_auc_std":float(np.std([r["roc_auc"] for r in part]))})
    pred=pa.Table.from_pylist(result.pop("predictions")); pred_path=repo/"artifacts/predictions/c8/supplemental_predictions.parquet"; pred_path.parent.mkdir(parents=True,exist_ok=True); pq.write_table(pred,pred_path,compression="zstd")
    result["generated_at_utc"]=datetime.now(timezone.utc).isoformat(); result["code"]=git_state(repo); result["holdout_accessed"]=False; result["prediction_rows"]=pred.num_rows; result["prediction_path"]=str(pred_path); result["prediction_sha256"]=sha256_file(pred_path)
    out=repo/"data/processed/diagnostics/c8_supplemental_evaluation.json"; write_json(result,out); print(f"C8 supplemental: {len(result['models'])} fitted models, {pred.num_rows} predictions, holdout=false")
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--config",type=Path,default=Path("config/c8.example.toml")); a=p.parse_args(); run(a.repo,a.repo/a.config)
if __name__=="__main__": main()
