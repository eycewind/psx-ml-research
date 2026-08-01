from __future__ import annotations
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr
from psx_ml.diagnostics.robust_metrics import regression_robust
from psx_ml.models.metrics import classification_metrics,date_block_interval

def quantile_spread(dates,symbols,y,p,q=5,minimum=10):
    grouped=defaultdict(list)
    for d,s,a,b in zip(dates,symbols,p,y): grouped[d].append((float(a),s,float(b)))
    values=[]
    for _,rows in sorted(grouped.items()):
        if len(rows)<minimum: continue
        rows.sort(key=lambda x:(x[0],x[1])); n=max(1,len(rows)//q); values.append(np.mean([x[2] for x in rows[-n:]])-np.mean([x[2] for x in rows[:n]]))
    return float(np.mean(values)) if values else None

def daily_ic_metrics(dates,y,p,minimum=10):
    grouped=defaultdict(list)
    for d,a,b in zip(dates,y,p): grouped[d].append((float(a),float(b)))
    counts={"validation_date_count":len(grouped),"population_eligible_date_count":0,"finite_ic_date_count":0,"constant_prediction_date_count":0,"constant_target_date_count":0,"nonfinite_ic_date_count":0}
    values=[]
    for _,rows in sorted(grouped.items()):
        if len(rows)<minimum: continue
        counts["population_eligible_date_count"]+=1
        a=np.asarray([r[0] for r in rows]); b=np.asarray([r[1] for r in rows])
        tc=not np.isfinite(np.std(a)) or np.std(a)==0; pc=not np.isfinite(np.std(b)) or np.std(b)==0
        counts["constant_target_date_count"]+=int(tc); counts["constant_prediction_date_count"]+=int(pc)
        if tc or pc: continue
        value=float(spearmanr(a,b).statistic)
        if np.isfinite(value): values.append(value)
        else: counts["nonfinite_ic_date_count"]+=1
    counts["finite_ic_date_count"]=len(values)
    stats={"mean_daily_ic":None,"median_daily_ic":None,"daily_ic_std":None,"positive_ic_fraction":None}
    if values:
        v=np.asarray(values); stats={"mean_daily_ic":float(np.mean(v)),"median_daily_ic":float(np.median(v)),"daily_ic_std":float(np.std(v)),"positive_ic_fraction":float(np.mean(v>0))}
    return {**counts,**stats}

def regression(y,p,dates,symbols,seed,reps):
    m=regression_robust(y,p,.0,.1); m["r2"]=float(1-np.sum((np.asarray(y)-p)**2)/np.sum((np.asarray(y)-np.mean(y))**2))
    m.update(daily_ic_metrics(dates,y,p,10)); m["quantile_spread"]=quantile_spread(dates,symbols,y,p)
    m["uncertainty"]=date_block_interval(dates,np.abs(np.asarray(y)-p),seed,reps); return m

def classification(y,p,dates,seed,reps):
    m=classification_metrics(y,p); m["uncertainty"]=date_block_interval(dates,-(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1))),seed,reps); return m

def selection_loss(kind,m): return m["rmse"] if kind=="regression" else m["log_loss"]
