from __future__ import annotations
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr
def average_rank_ensemble(lightgbm,xgboost):
    x={(r["trade_date"],r["symbol"]):r for r in xgboost}; return [{**r,"model_name":"average_rank_ensemble","prediction_percentile_rank":.5*(r["prediction_percentile_rank"]+x[(r["trade_date"],r["symbol"])]["prediction_percentile_rank"])} for r in lightgbm if (r["trade_date"],r["symbol"]) in x]
def model_agreement(lightgbm,xgboost):
    lg=defaultdict(dict); xg=defaultdict(dict)
    for r in lightgbm: lg[r["trade_date"]][r["symbol"]]=r["prediction_percentile_rank"]
    for r in xgboost: xg[r["trade_date"]][r["symbol"]]=r["prediction_percentile_rank"]
    out=[]
    for d in sorted(set(lg)&set(xg)):
        syms=sorted(set(lg[d])&set(xg[d])); a=np.asarray([lg[d][s] for s in syms]); b=np.asarray([xg[d][s] for s in syms]); row={"trade_date":d,"symbol_count":len(syms),"rank_correlation":float(spearmanr(a,b).statistic)}; oa=sorted(syms,key=lambda s:(-lg[d][s],s)); ob=sorted(syms,key=lambda s:(-xg[d][s],s))
        for k in (5,10,20): row[f"top_{k}_overlap"]=len(set(oa[:k])&set(ob[:k]))/min(k,len(syms))
        n=max(1,int(np.ceil(.1*len(syms)))); row["top_decile_overlap"]=len(set(oa[:n])&set(ob[:n]))/n; row["bottom_decile_overlap"]=len(set(oa[-n:])&set(ob[-n:]))/n; out.append(row)
    return out
def intersection_union(a,b):
    ka={(r["trade_date"],r["symbol"]):r for r in a}; kb={(r["trade_date"],r["symbol"]):r for r in b}; return [ka[k] for k in sorted(set(ka)&set(kb))],[ka[k] if k in ka else kb[k] for k in sorted(set(ka)|set(kb))]
