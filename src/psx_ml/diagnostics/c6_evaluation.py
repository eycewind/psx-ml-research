from __future__ import annotations
from collections import defaultdict
import json
import re
import numpy as np
import pyarrow as pa
from psx_ml.models.metrics import classification_metrics
from .robust_metrics import daily_ic, regression_robust

REG_MODELS={"ridge_fixed_alpha_1","zero_return_baseline","training_mean_baseline"}
CLS_MODELS={"logistic_fixed_c_1","training_prevalence_baseline","majority_class_baseline"}
CANONICAL={"ridge_fixed_alpha_1","logistic_fixed_c_1"}

def _bucket_turnover(x): return "lt_5m" if x<5_000_000 else ("5m_to_25m" if x<25_000_000 else "gte_25m")
def _bucket_stale(x): return "le_5pct" if x<=.05 else ("5_to_20pct" if x<=.2 else "gt_20pct")

def evaluate_predictions(predictions: pa.Table, membership: pa.Table, pit: pa.Table, trim=.01, huber=.1, ic_min=10):
    eligible=defaultdict(set); family={}
    for r in membership.to_pylist():
        key=(r["trade_date"],r["symbol"]); family[key]=r["instrument_type"]
        if r["eligible"]: eligible[r["universe_name"]].add(key)
    pit_meta={(r["trade_date"],r["symbol"]):(float(r["median_turnover_pkr"] or 0),float(r["stale_fraction"] or 0)) for r in pit.select(["trade_date","symbol","median_turnover_pkr","stale_fraction"]).to_pylist()}
    rows=predictions.to_pylist(); groups=defaultdict(list)
    for i,r in enumerate(rows):
        if r["model_name"] not in REG_MODELS|CLS_MODELS: continue
        key=(r["trade_date"],r["symbol"])
        for universe,keys in eligible.items():
            if key not in keys: continue
            groups[(universe,r["target_name"],r["model_name"],"overall","all")].append(i)
            if r["model_name"] in CANONICAL:
                turnover,stale=pit_meta[key]
                for dim,value in (("fold",r["fold_id"]),("year",r["trade_date"][:4]),("instrument_family",family[key]),("liquidity_bucket",_bucket_turnover(turnover)),("stale_bucket",_bucket_stale(stale))):
                    groups[(universe,r["target_name"],r["model_name"],dim,value)].append(i)
    metrics=[]
    for (universe,target,model,dimension,value),ix in sorted(groups.items()):
        selected=[rows[i] for i in ix]; y=np.array([r["target"] for r in selected],float)
        is_cls=target.startswith("up_")
        p=np.array([r["prediction_probability"] if is_cls else r["prediction"] for r in selected],float)
        if is_cls:
            m=classification_metrics(y,p); keep={k:m.get(k) for k in ("log_loss","brier","roc_auc","pr_auc","balanced_accuracy","precision","recall","f1","prevalence")}
        else:
            keep=regression_robust(y,p,trim,huber)
            ic=daily_ic([r["trade_date"] for r in selected],y,p,ic_min) if model=="ridge_fixed_alpha_1" else {"dates":0,"mean_daily_ic":None,"median_daily_ic":None,"daily_ic_std":None,"positive_ic_fraction":None}
            keep.update({"ic_dates":ic.pop("dates"),**ic})
            daily=defaultdict(list); cross_section=defaultdict(list)
            for r,e,pp,yy in zip(selected,np.abs(y-p),p,y):
                daily[r["trade_date"]].append(float(e)); cross_section[r["trade_date"]].append((float(pp),r["symbol"],float(yy)))
            keep["equal_date_mae"]=float(np.mean([np.mean(x) for x in daily.values()]))
            keep["date_level_median_absolute_error"]=float(np.mean([np.median(x) for x in daily.values()]))
            spreads=[]
            for d,day in sorted(cross_section.items()):
                if len(day)>=ic_min:
                    day.sort(key=lambda x:(x[0],x[1])); q=max(1,len(day)//5)
                    spreads.append(np.mean([x[2] for x in day[-q:]])-np.mean([x[2] for x in day[:q]]))
            keep["mean_daily_top_minus_bottom_target_spread"]=float(np.mean(spreads)) if spreads else None
            by_symbol=defaultdict(list)
            for r,e in zip(selected,np.abs(y-p)): by_symbol[r["symbol"]].append(float(e))
            keep["equal_symbol_mae"]=float(np.mean([np.mean(x) for x in by_symbol.values()]))
        metrics.append({"universe_name":universe,"target_name":target,"model_name":model,"scope_dimension":dimension,"scope_value":value,"n":len(ix),**keep})
    keys=sorted(set().union(*(r.keys() for r in metrics)))
    return pa.Table.from_pylist([{k:r.get(k) for k in keys} for r in metrics]), eligible, family, pit_meta

def loss_concentration(predictions: pa.Table, eligible: dict, family: dict):
    rows=predictions.to_pylist(); out=[]
    for universe,keys in sorted(eligible.items()):
        scoped=defaultdict(list)
        for r in rows:
            key=(r["trade_date"],r["symbol"])
            if key in keys and r["model_name"] in REG_MODELS and not r["target_name"].startswith("up_"): scoped[(r["target_name"],r["model_name"])].append(r)
        for (target,model),part in sorted(scoped.items()):
            for dimension,getter in (("symbol",lambda r:r["symbol"]),("date",lambda r:r["trade_date"]),("instrument_family",lambda r:family[(r["trade_date"],r["symbol"])])):
                values=defaultdict(float)
                for r in part: values[getter(r)]+=(r["target"]-r["prediction"])**2
                total=sum(values.values())
                for rank,(entity,loss) in enumerate(sorted(values.items(),key=lambda x:(-x[1],x[0])),1):
                    out.append({"universe_name":universe,"target_name":target,"model_name":model,"aggregation_dimension":dimension,"entity":entity,"squared_loss":loss,"loss_share":loss/total if total else 0.0,"rank":rank})
    return pa.Table.from_pylist(out)

def extreme_rows(predictions: pa.Table, membership: pa.Table, features: pa.Table, thresholds: dict):
    family={(r["trade_date"],r["symbol"]):r["instrument_type"] for r in membership.to_pylist()}
    meta={(r["trade_date"],r["symbol"]):r for r in features.select(["trade_date","symbol","listing_age_observations","turnover_median_20obs_adj","stale_close_run_length","days_since_previous_observation","missing_volume_flag","zero_volume_flag"]).to_pylist()}
    candidates=[]
    for r in predictions.to_pylist():
        if r["model_name"]!="ridge_fixed_alpha_1": continue
        match=re.search(r"_(\d+)s_adj$",r["target_name"]); h=match.group(1) if match else ""; threshold=thresholds.get(h)
        residual=r["target"]-r["prediction"]
        if threshold is not None and abs(r["target"])>threshold:
            m=meta.get((r["trade_date"],r["symbol"]),{})
            candidates.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"fold_id":r["fold_id"],"target_name":r["target_name"],"target":r["target"],"prediction":r["prediction"],"residual":residual,"squared_residual":residual**2,"instrument_family":family.get((r["trade_date"],r["symbol"]),"unknown"),"extreme_reason":f"absolute_target_gt_{threshold}",**{k:m.get(k) for k in ("listing_age_observations","turnover_median_20obs_adj","stale_close_run_length","days_since_previous_observation","missing_volume_flag","zero_volume_flag")}})
    return pa.Table.from_pylist(sorted(candidates,key=lambda r:(r["trade_date"],r["symbol"],r["target_name"])))
