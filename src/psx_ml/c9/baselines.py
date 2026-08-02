from __future__ import annotations
from collections import defaultdict
import numpy as np

def deterministic_random_same_count(universe,counts,seed=42,repetition=0):
    grouped=defaultdict(list)
    for r in universe: grouped[r["trade_date"]].append(r)
    out=[]
    for j,(d,part) in enumerate(sorted(grouped.items())):
        n=min(counts.get(d,0),len(part)); rng=np.random.default_rng(seed+repetition*1_000_003+j); idx=rng.choice(len(part),n,replace=False) if n else []
        out += [{**part[i],"baseline":"random_same_count","repetition":repetition} for i in sorted(idx)]
    return out

def random_distribution(universe,counts,repetitions=1000,seed=42):
    values=[]
    for repetition in range(repetitions):
        selected=deterministic_random_same_count(universe,counts,seed,repetition)
        grouped=defaultdict(list)
        for r in selected: grouped[r["trade_date"]].append(r["actual_market_relative_return"])
        values.append(float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None)
    return values

def rank_baseline(rows,field,name):
    grouped=defaultdict(list); out=[]
    for r in rows: grouped[r["trade_date"]].append(r)
    for _,part in sorted(grouped.items()):
        valid=[r for r in part if r.get(field) is not None and np.isfinite(r[field])]; ordered=sorted(valid,key=lambda r:(r[field],r["symbol"])); n=len(ordered)
        for i,r in enumerate(ordered): out.append({**r,"model_name":name,"prediction_percentile_rank":i/(n-1) if n>1 else .5})
    return out
