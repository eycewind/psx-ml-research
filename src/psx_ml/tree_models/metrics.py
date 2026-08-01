from __future__ import annotations
from collections import defaultdict
import numpy as np
from psx_ml.diagnostics.robust_metrics import daily_ic,regression_robust
from psx_ml.models.metrics import classification_metrics,date_block_interval

def quantile_spread(dates,symbols,y,p,q=5,minimum=10):
    grouped=defaultdict(list)
    for d,s,a,b in zip(dates,symbols,p,y): grouped[d].append((float(a),s,float(b)))
    values=[]
    for _,rows in sorted(grouped.items()):
        if len(rows)<minimum: continue
        rows.sort(key=lambda x:(x[0],x[1])); n=max(1,len(rows)//q); values.append(np.mean([x[2] for x in rows[-n:]])-np.mean([x[2] for x in rows[:n]]))
    return float(np.mean(values)) if values else None

def regression(y,p,dates,symbols,seed,reps):
    m=regression_robust(y,p,.0,.1); m["r2"]=float(1-np.sum((np.asarray(y)-p)**2)/np.sum((np.asarray(y)-np.mean(y))**2))
    ic=daily_ic(dates,y,p,10); m.update({"ic_dates":ic.pop("dates"),**ic}); m["quantile_spread"]=quantile_spread(dates,symbols,y,p)
    m["uncertainty"]=date_block_interval(dates,np.abs(np.asarray(y)-p),seed,reps); return m

def classification(y,p,dates,seed,reps):
    m=classification_metrics(y,p); m["uncertainty"]=date_block_interval(dates,-(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1))),seed,reps); return m

def selection_loss(kind,m): return m["rmse"] if kind=="regression" else m["log_loss"]
