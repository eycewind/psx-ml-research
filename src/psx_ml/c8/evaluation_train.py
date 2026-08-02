from __future__ import annotations
from collections import defaultdict
import math,time
from pathlib import Path
import hashlib,pickle
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import lightgbm as lgb
from psx_ml.tree_models.datasets import inner_chronological
from psx_ml.tree_models.models import hist_model,lgb_model,predict,xgb_model
from .evaluation_metrics import aggregate_folds,evaluate_predictions
from .feature_variants import stage1_matrix,stage2_matrix

TARGETS={
    "absolute":"fwd_open_to_close_ret_{h}s_adj",
    "market_relative":"fwd_market_relative_ret_{h}s",
    "sector_strict_5_peer":"fwd_sector_relative_ret_{h}s",
    "sector_relaxed_3_peer":"fwd_sector_relative_ret_{h}s_relaxed_3_peer",
    "sector_shrunk_3_peer":"fwd_sector_relative_ret_{h}s_shrunk_3_peer",
}

def _stopping_lgb(model):
    metric="l2"; vals=model.evals_result_.get("valid_0",{}).get(metric,[]); best=int(model.best_iteration_ or len(vals) or 1)
    return best,metric,float(vals[best-1]) if vals else None,float(vals[0]) if vals else None,len(vals)

def _stopping_xgb(model):
    vals=model.evals_result()["validation_0"]["rmse"]
    return int(model.best_iteration+1),"rmse",float(model.best_score),float(vals[0]),len(vals)

def _fit(model_name,x,y,train,valid,inner_train,inner_valid,cfg):
    seed=cfg["seed"]; threads=cfg["threads"]; cap=cfg["boosting_max_rounds"]; patience=cfg["early_stopping_rounds"]
    if model_name=="hist_gradient_boosting_cpu":
        model=hist_model("regression",cfg["hist"],seed,cfg["hist_max_iter"]); start=time.perf_counter(); model.fit(x[train],y[train]); fit=time.perf_counter()-start
        stopping=(cfg["hist_max_iter"],None,None,None,cfg["hist_max_iter"]); device="cpu"
    elif model_name=="lightgbm_cpu":
        inner=lgb_model("regression",cfg["lightgbm"],seed,cap,threads); inner.fit(x[inner_train],y[inner_train],eval_set=[(x[inner_valid],y[inner_valid])],callbacks=[lgb.early_stopping(patience,verbose=False)])
        stopping=_stopping_lgb(inner); model=lgb_model("regression",cfg["lightgbm"],seed,stopping[0],threads); start=time.perf_counter(); model.fit(x[train],y[train]); fit=time.perf_counter()-start; device="cpu"
    else:
        inner=xgb_model("regression",cfg["xgboost"],seed,cap,threads,"cuda"); inner.set_params(early_stopping_rounds=patience); inner.fit(x[inner_train],y[inner_train],eval_set=[(x[inner_valid],y[inner_valid])],verbose=False)
        stopping=_stopping_xgb(inner); model=xgb_model("regression",cfg["xgboost"],seed,stopping[0],threads,"cuda"); start=time.perf_counter(); model.fit(x[train],y[train]); fit=time.perf_counter()-start; device="cuda"
    start=time.perf_counter(); p=predict(model,x[valid],"regression"); pred=time.perf_counter()-start
    return model,np.asarray(p,float),fit,pred,stopping,device

def _importance(model,name,features,meta):
    if name=="hist_gradient_boosting_cpu": return []
    if name=="lightgbm_cpu": gain=model.booster_.feature_importance("gain"); count=model.booster_.feature_importance("split")
    else:
        score_gain=model.get_booster().get_score(importance_type="gain"); score_count=model.get_booster().get_score(importance_type="weight")
        gain=np.asarray([score_gain.get(f"f{i}",0.) for i in range(len(features))]); count=np.asarray([score_count.get(f"f{i}",0.) for i in range(len(features))])
    return [{**meta,"feature":f,"gain_importance":float(g),"split_importance":float(c)} for f,g,c in zip(features,gain,count)]

def _save_model(model,name,meta,root):
    root.mkdir(parents=True,exist_ok=True); stem="_".join(str(meta[k]) for k in ("stage","horizon","target_family","feature_variant","fold_id","model_name"))
    if name=="lightgbm_cpu": path=root/f"{stem}.txt"; model.booster_.save_model(str(path))
    elif name=="xgboost_gpu": path=root/f"{stem}.json"; model.save_model(path)
    else: path=root/f"{stem}.pkl"; path.write_bytes(pickle.dumps(model,protocol=5))
    return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),**meta}

def _regime(values,train,valid):
    a=np.asarray(values,float); finite=a[train&np.isfinite(a)]
    if not len(finite): return np.asarray([None]*valid.sum(),object),[None,None]
    q=np.quantile(finite,[1/3,2/3]); labels=np.where(a[valid]<=q[0],"low",np.where(a[valid]<=q[1],"medium","high")).astype(object); labels[~np.isfinite(a[valid])]=None
    return labels,[float(q[0]),float(q[1])]

def _peer_bucket(n):
    if n<3:return "0-2"
    if n<5:return "3-4"
    if n<10:return "5-9"
    return "10+"

def _subgroup_rows(meta,pred_rows,minimum=10):
    out=[]
    dimensions=("sector","sector_benchmark_tier","peer_count_bucket","market_trend_regime","market_volatility_regime","market_breadth_regime","market_dispersion_regime")
    for dimension in dimensions:
        grouped=defaultdict(list)
        for r in pred_rows: grouped[r.get(dimension)].append(r)
        for value,part in sorted(grouped.items(),key=lambda x:str(x[0])):
            if value is None or len(part)<minimum: continue
            y=np.asarray([r["target"] for r in part]); p=np.asarray([r["prediction"] for r in part]); d=[r["trade_date"] for r in part]; s=[r["symbol"] for r in part]
            met,_,_,_=evaluate_predictions(y,p,d,s,42,10,minimum)
            out.append({**meta,"comparison_subset":"natural_coverage","dimension":dimension,"value":str(value),"row_count":len(part),"date_count":met["date_count"],"symbol_count":met["symbol_count"],"mae":met["mae"],"rmse":met["rmse"],"spearman":met["spearman"],"mean_daily_ic":met["mean_daily_ic"],"finite_ic_date_count":met["finite_ic_date_count"]})
    return out

def run_evaluation(rows,derived,context,roles,variants,cfg,prediction_path,models_root):
    dates=np.asarray([r["trade_date"] for r in rows],object); symbols=np.asarray([r["symbol"] for r in rows],object); sectors=np.asarray([r.get("sector") for r in rows],object)
    all_values={k:np.asarray(v,float) for k,v in context.items()}
    for feature in variants["A_c7_only"]: all_values[feature]=np.asarray([np.nan if r.get(feature) is None else r[feature] for r in rows],float)
    relative_values={k:np.asarray([np.nan if x is None or isinstance(x,str) else x for x in v],float) for k,v in derived.items() if k.startswith("fwd_")}
    for h in cfg["horizons"]: relative_values[f"fwd_open_to_close_ret_{h}s_adj"]=np.asarray([np.nan if r.get(f"fwd_open_to_close_ret_{h}s_adj") is None else r[f"fwd_open_to_close_ret_{h}s_adj"] for r in rows],float)
    folds=sorted(roles); metrics=[]; daily_rows=[]; bucket_rows=[]; importance=[]; diagnostics=[]; thresholds=[]; subgroup=[]
    prediction_path.parent.mkdir(parents=True,exist_ok=True); writer=None; prediction_count=0; model_files=[]
    try:
      for stage,matrix,models in ((1,stage1_matrix(),("hist_gradient_boosting_cpu","lightgbm_cpu","xgboost_gpu")),(2,stage2_matrix(),("lightgbm_cpu","xgboost_gpu"))):
        for horizon in cfg["horizons"]:
          stage1_common=np.isfinite(relative_values[f"fwd_open_to_close_ret_{horizon}s_adj"])&np.isfinite(relative_values[f"fwd_market_relative_ret_{horizon}s"])
          strict=np.isfinite(relative_values[f"fwd_sector_relative_ret_{horizon}s"])
          for family,variant in matrix:
            target_name=TARGETS[family].format(h=horizon); y=relative_values[target_name]; features=variants[variant]; x=np.column_stack([all_values[f] for f in features])
            for fold in folds:
              role=roles[fold]; train=(role=="train")&np.isfinite(y); valid=(role=="validation")&np.isfinite(y)
              it,iv,boundary=inner_chronological(dates,train,cfg["inner_validation_fraction"])
              for model_name in models:
                model,p,fit_s,pred_s,stop,device=_fit(model_name,x,y,train,valid,it,iv,cfg)
                valid_idx=np.flatnonzero(valid); meta={"stage":stage,"horizon":horizon,"target_family":family,"target_name":target_name,"feature_variant":variant,"model_name":model_name,"fold_id":fold}
                trend,trend_q=_regime(context["market_median_ret_20obs"],train,valid); vol,vol_q=_regime(context["market_realized_volatility_20obs"],train,valid); breadth,breadth_q=_regime(context["market_breadth_positive_5obs"],train,valid); dispersion,disp_q=_regime(context["market_cross_sectional_dispersion_20obs"],train,valid)
                thresholds.append({**meta,"trend_quantiles":trend_q,"volatility_quantiles":vol_q,"breadth_quantiles":breadth_q,"dispersion_quantiles":disp_q,"inner_boundary":boundary})
                peer=derived[f"sector_valid_peer_count_{horizon}s"]; tier=derived[f"sector_benchmark_tier_{horizon}s"]
                pred_rows=[{**meta,"trade_date":dates[i],"symbol":symbols[i],"sector":sectors[i],"target":float(y[i]),"prediction":float(p[j]),"comparison_subset_natural":True,"strict_5_peer_matched":bool(strict[i]),"stage1_common_matched":bool(stage1_common[i]),"sector_peer_count":int(peer[i]),"peer_count_bucket":_peer_bucket(peer[i]),"sector_benchmark_tier":tier[i],"market_trend_regime":trend[j],"market_volatility_regime":vol[j],"market_breadth_regime":breadth[j],"market_dispersion_regime":dispersion[j],"device":device} for j,i in enumerate(valid_idx)]
                table=pa.Table.from_pylist(pred_rows)
                if writer is None: writer=pq.ParquetWriter(prediction_path,table.schema,compression="zstd",use_dictionary=True)
                writer.write_table(table,row_group_size=20000); prediction_count+=len(pred_rows)
                subsets=[("natural_coverage",np.ones(len(p),bool))]
                subsets.append(("stage1_common_matched",stage1_common[valid])) if stage==1 else subsets.append(("strict_5_peer_matched",strict[valid]))
                for subset,mask in subsets:
                    if not mask.any(): continue
                    met,daily,buckets,_=evaluate_predictions(y[valid][mask],p[mask],dates[valid][mask],symbols[valid][mask],cfg["seed"],cfg["bootstrap_replicates"],cfg["minimum_daily_population"])
                    metrics.append({**meta,"comparison_subset":subset,"sector_count":len(set(x for x in sectors[valid][mask] if x is not None)),**met})
                    daily_rows += [{**meta,"comparison_subset":subset,**r} for r in daily]
                    bucket_rows += [{**meta,"comparison_subset":subset,**r} for r in buckets]
                importance += _importance(model,model_name,features,meta)
                model_files.append(_save_model(model,model_name,meta,models_root))
                diagnostics.append({**meta,"device":device,"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"feature_count":len(features),"fit_seconds":fit_s,"predict_seconds":pred_s,"best_iteration":stop[0],"early_stopping_metric":stop[1],"best_inner_score":stop[2],"first_iteration_score":stop[3],"last_evaluated_iteration":stop[4],"prediction_mean":float(np.mean(p)),"prediction_std":float(np.std(p)),"prediction_min":float(np.min(p)),"prediction_max":float(np.max(p)),"unique_prediction_count":int(np.unique(np.round(p,12)).size),"near_constant":bool(np.std(p)<=cfg["near_constant_std"])})
                subgroup += _subgroup_rows(meta,pred_rows,cfg["minimum_daily_population"])
    finally:
      if writer is not None: writer.close()
    aggregates=aggregate_folds(metrics)
    return {"metrics":metrics,"aggregate_metrics":aggregates,"daily_ic":daily_rows,"buckets":bucket_rows,"feature_importance":importance,"training_diagnostics":diagnostics,"regime_thresholds":thresholds,"subgroup_metrics":subgroup,"model_files":model_files,"prediction_rows":prediction_count}
