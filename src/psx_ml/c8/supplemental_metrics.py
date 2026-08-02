from __future__ import annotations

from collections import defaultdict
import math

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score


def _finite_spearman(a, b):
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return None
    value = float(spearmanr(a, b).statistic)
    return value if math.isfinite(value) else None


def _interval(values, seed, reps):
    values = np.asarray([v for v in values if v is not None and math.isfinite(v)], float)
    if not len(values):
        return {"lower": None, "upper": None, "finite_dates": 0, "replicates": reps}
    rng = np.random.default_rng(seed)
    samples = [np.mean(values[rng.integers(0, len(values), len(values))]) for _ in range(reps)]
    return {"lower": float(np.quantile(samples, .025)), "upper": float(np.quantile(samples, .975)), "finite_dates": len(values), "replicates": reps}


def rank_metrics(rank_target, outcome, prediction, dates, symbols, minimum=10, seed=42, reps=200):
    rank_target=np.asarray(rank_target,float); outcome=np.asarray(outcome,float); prediction=np.asarray(prediction,float)
    dates=np.asarray(dates,object); symbols=np.asarray(symbols,object); grouped=defaultdict(list)
    for i,d in enumerate(dates): grouped[d].append(i)
    daily=[]; buckets=np.full(len(prediction),-1,int)
    for d,idx0 in sorted(grouped.items()):
        idx=np.asarray(idx0); row={"trade_date":d,"row_count":len(idx)}
        if len(idx)<minimum:
            row.update({k:None for k in ("daily_ic","ndcg_5","ndcg_10","top_decile_capture","bottom_decile_capture","d10_d1_spread")})
            daily.append(row); continue
        order=np.asarray(sorted(idx,key=lambda i:(prediction[i],symbols[i],i)))
        for r,i in enumerate(order): buckets[i]=min(9,r*10//len(order))
        true_desc=np.asarray(sorted(idx,key=lambda i:(-rank_target[i],symbols[i],i)))
        true_asc=np.asarray(sorted(idx,key=lambda i:(rank_target[i],symbols[i],i)))
        k=max(1,len(idx)//10); pred_top=set(order[-k:]); pred_bottom=set(order[:k])
        hi=idx[buckets[idx]==9]; lo=idx[buckets[idx]==0]
        row.update({
            "daily_ic":_finite_spearman(rank_target[idx],prediction[idx]),
            "ndcg_5":float(ndcg_score(rank_target[idx][None,:],prediction[idx][None,:],k=min(5,len(idx)))),
            "ndcg_10":float(ndcg_score(rank_target[idx][None,:],prediction[idx][None,:],k=min(10,len(idx)))),
            "top_decile_capture":len(pred_top.intersection(true_desc[:k]))/k,
            "bottom_decile_capture":len(pred_bottom.intersection(true_asc[:k]))/k,
            "d10_d1_spread":float(np.mean(outcome[hi])-np.mean(outcome[lo])) if len(hi) and len(lo) else None,
        }); daily.append(row)
    def vals(k): return [r[k] for r in daily if r[k] is not None and math.isfinite(r[k])]
    ic=vals("daily_ic"); d10=vals("d10_d1_spread")
    bucket_means=[]
    for b in range(10):
        idx=np.flatnonzero(buckets==b); bucket_means.append(float(np.mean(outcome[idx])) if len(idx) else None)
    mono=_finite_spearman(np.arange(10),np.asarray(bucket_means)) if all(v is not None for v in bucket_means) else None
    def mean_or_none(key):
        value=vals(key); return float(np.mean(value)) if value else None
    result={"n":len(rank_target),"date_count":len(grouped),"finite_ic_date_count":len(ic),
        "mean_daily_ic":float(np.mean(ic)) if ic else None,"median_daily_ic":float(np.median(ic)) if ic else None,
        "daily_ic_std":float(np.std(ic)) if ic else None,"positive_ic_date_fraction":float(np.mean(np.asarray(ic)>0)) if ic else None,
        "ndcg_5":mean_or_none("ndcg_5"),"ndcg_10":mean_or_none("ndcg_10"),
        "top_decile_capture":mean_or_none("top_decile_capture"),"bottom_decile_capture":mean_or_none("bottom_decile_capture"),
        "d10_d1_spread":float(np.mean(d10)) if d10 else None,"bucket_monotonicity":mono,
        "bootstrap":{"mean_daily_ic":_interval(ic,seed,reps),"ndcg_5":_interval(vals("ndcg_5"),seed+1,reps),
          "ndcg_10":_interval(vals("ndcg_10"),seed+2,reps),"top_decile_capture":_interval(vals("top_decile_capture"),seed+3,reps),
          "d10_d1_spread":_interval(d10,seed+4,reps)}}
    return result,daily,bucket_means
