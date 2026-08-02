from __future__ import annotations
from collections import defaultdict
import math
import numpy as np
from scipy.stats import spearmanr

def _finite_spearman(a,b):
    if len(a)<2 or np.std(a)==0 or np.std(b)==0: return None
    value=float(spearmanr(a,b).statistic); return value if math.isfinite(value) else None

def _bootstrap(values,seed,reps):
    v=np.asarray([x for x in values if x is not None and math.isfinite(float(x))],float)
    if not len(v): return {"lower":None,"upper":None,"replicates":reps,"finite_dates":0}
    rng=np.random.default_rng(seed); means=np.asarray([np.mean(v[rng.integers(0,len(v),len(v))]) for _ in range(reps)])
    return {"lower":float(np.quantile(means,.025)),"upper":float(np.quantile(means,.975)),"replicates":reps,"finite_dates":len(v)}

def evaluate_predictions(y,p,dates,symbols,seed=42,reps=200,minimum=10):
    y=np.asarray(y,float); p=np.asarray(p,float); dates=np.asarray(dates,object); symbols=np.asarray(symbols,object)
    grouped=defaultdict(list)
    for i,d in enumerate(dates): grouped[d].append(i)
    daily=[]; assignments=np.full(len(y),-1,int)
    counts={"validation_date_count":len(grouped),"population_eligible_date_count":0,"finite_ic_date_count":0,"constant_prediction_date_count":0,"constant_target_date_count":0,"nonfinite_ic_date_count":0}
    for d,idx in sorted(grouped.items()):
        idx=np.asarray(idx); ic=None; reason=None
        if len(idx)<minimum: reason="insufficient_population"
        else:
            counts["population_eligible_date_count"]+=1
            tc=np.std(y[idx])==0; pc=np.std(p[idx])==0
            counts["constant_target_date_count"]+=int(tc); counts["constant_prediction_date_count"]+=int(pc)
            if tc: reason="constant_target"
            elif pc: reason="constant_prediction"
            else:
                ic=_finite_spearman(y[idx],p[idx])
                if ic is None: counts["nonfinite_ic_date_count"]+=1; reason="nonfinite_ic"
                else: counts["finite_ic_date_count"]+=1
        order=sorted(idx,key=lambda i:(p[i],symbols[i],i)); n=len(order)
        if n>=minimum:
            for rank,i in enumerate(order): assignments[i]=min(9,rank*10//n)
        low=[i for i in idx if assignments[i]==0]; high=[i for i in idx if assignments[i]==9]
        d10=float(np.mean(y[high])-np.mean(y[low])) if low and high else None
        daily.append({"trade_date":d,"row_count":len(idx),"daily_ic":ic,"ic_undefined_reason":reason,"d10_d1_spread":d10})
    ic_values=[r["daily_ic"] for r in daily if r["daily_ic"] is not None]; d10_values=[r["d10_d1_spread"] for r in daily if r["d10_d1_spread"] is not None]
    bucket_rows=[]
    for bucket in range(10):
        idx=np.flatnonzero(assignments==bucket)
        bucket_rows.append({"bucket":bucket+1,"row_count":len(idx),"date_count":len(set(dates[idx])),"symbol_count":len(set(symbols[idx])),"target_mean":float(np.mean(y[idx])) if len(idx) else None,"target_median":float(np.median(y[idx])) if len(idx) else None})
    low=np.flatnonzero(assignments==0); high=np.flatnonzero(assignments==9); bottom2=np.flatnonzero((assignments>=0)&(assignments<=1)); top2=np.flatnonzero(assignments>=8)
    bucket_means=[r["target_mean"] for r in bucket_rows]; monotonicity=_finite_spearman(np.arange(1,11),np.asarray(bucket_means,float)) if all(x is not None for x in bucket_means) else None
    overall=_finite_spearman(y,p); residual=y-p
    metrics={"n":len(y),"date_count":len(set(dates)),"symbol_count":len(set(symbols)),"mae":float(np.mean(np.abs(residual))),"rmse":float(np.sqrt(np.mean(residual**2))),"spearman":overall,**counts,
             "mean_daily_ic":float(np.mean(ic_values)) if ic_values else None,"median_daily_ic":float(np.median(ic_values)) if ic_values else None,"daily_ic_std":float(np.std(ic_values)) if ic_values else None,"positive_ic_fraction":float(np.mean(np.asarray(ic_values)>0)) if ic_values else None,
             "d10_d1_mean_spread":float(np.mean(y[high])-np.mean(y[low])) if len(low) and len(high) else None,"d10_d1_median_spread":float(np.median(y[high])-np.median(y[low])) if len(low) and len(high) else None,"top2_bottom2_spread":float(np.mean(y[top2])-np.mean(y[bottom2])) if len(top2) and len(bottom2) else None,"bucket_monotonicity":monotonicity,
             "mean_daily_ic_ci95":_bootstrap(ic_values,seed,reps),"d10_d1_ci95":_bootstrap(d10_values,seed+1,reps)}
    return metrics,daily,bucket_rows,assignments

def aggregate_folds(metric_rows):
    grouped=defaultdict(list)
    for r in metric_rows: grouped[tuple(r[k] for k in ("stage","horizon","target_family","feature_variant","model_name","comparison_subset"))].append(r)
    out=[]
    for key,rows in sorted(grouped.items()):
        values=[r["mean_daily_ic"] for r in rows if r["mean_daily_ic"] is not None]
        spreads=[r["d10_d1_mean_spread"] for r in rows if r["d10_d1_mean_spread"] is not None]
        out.append(dict(zip(("stage","horizon","target_family","feature_variant","model_name","comparison_subset"),key),fold_count=len(rows),mean_daily_ic=float(np.mean(values)) if values else None,daily_ic_fold_std=float(np.std(values)) if values else None,worst_fold_ic=float(np.min(values)) if values else None,best_fold_ic=float(np.max(values)) if values else None,positive_ic_folds=sum(x>0 for x in values),mean_d10_d1=float(np.mean(spreads)) if spreads else None,positive_spread_folds=sum(x>0 for x in spreads),finite_ic_dates=sum(r["finite_ic_date_count"] for r in rows),undefined_ic_dates=sum(r["population_eligible_date_count"]-r["finite_ic_date_count"] for r in rows)))
    return out

def attach_aggregate_bootstrap(aggregates,daily_rows,seed=42,reps=200):
    keys=("stage","horizon","target_family","feature_variant","model_name","comparison_subset")
    grouped=defaultdict(list)
    for r in daily_rows: grouped[tuple(r[k] for k in keys)].append(r)
    lookup={tuple(r[k] for k in keys):r for r in aggregates}
    for key,rows in grouped.items():
        target=lookup[key]; target["aggregate_mean_daily_ic_ci95"]=_bootstrap([r["daily_ic"] for r in rows],seed,reps); target["aggregate_d10_d1_ci95"]=_bootstrap([r["d10_d1_spread"] for r in rows],seed+1,reps)
    return aggregates
