from __future__ import annotations
from collections import defaultdict
import numpy as np
def turnover_metrics(selected):
    grouped=defaultdict(set)
    for r in selected: grouped[r["trade_date"]].add(r["symbol"])
    dates=sorted(grouped); out=[]
    for i,d in enumerate(dates):
        current=grouped[d]; previous=grouped[dates[i-1]] if i else set(); union=current|previous
        out.append({"trade_date":d,"candidate_count":len(current),"retained":len(current&previous),"entries":len(current-previous),"exits":len(previous-current),"jaccard":len(current&previous)/len(union) if union else 1.,"gross_candidate_turnover":(len(current-previous)+len(previous-current))/(len(current)+len(previous)) if current or previous else 0.})
    return out
def retention(selected,lags=(1,2,5)):
    grouped=defaultdict(set)
    for r in selected: grouped[r["trade_date"]].add(r["symbol"])
    dates=sorted(grouped); result=[]
    for lag in lags:
        values=[len(grouped[dates[i]]&grouped[dates[i+lag]])/len(grouped[dates[i]]) for i in range(len(dates)-lag) if grouped[dates[i]]]; result.append({"lag_sessions":lag,"mean_retention":float(np.mean(values)) if values else None,"median_retention":float(np.median(values)) if values else None})
    return result
def candidate_lifetimes(selected):
    grouped=defaultdict(set)
    for r in selected: grouped[r["trade_date"]].add(r["symbol"])
    active={}; result=[]
    for d in sorted(grouped):
        current=grouped[d]
        for s in list(active):
            if s not in current: result.append({"symbol":s,"start_date":active[s][0],"end_date":active[s][1],"sessions":active[s][2]}); del active[s]
        for s in current: active[s]=(active[s][0],d,active[s][2]+1) if s in active else (d,d,1)
    result += [{"symbol":s,"start_date":v[0],"end_date":v[1],"sessions":v[2]} for s,v in active.items()]
    return sorted(result,key=lambda r:(r["symbol"],r["start_date"]))
