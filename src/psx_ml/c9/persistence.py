from __future__ import annotations
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr

def rank_persistence(rows,lags=(1,2,5)):
    by_date=defaultdict(dict)
    for r in rows: by_date[r["trade_date"]][r["symbol"]]=r["prediction_percentile_rank"]
    dates=sorted(by_date); out=[]
    for lag in lags:
        correlations=[]; top=[]; bottom=[]; below=[]; entering=[]
        for i in range(len(dates)-lag):
            a=by_date[dates[i]]; b=by_date[dates[i+lag]]; symbols=sorted(set(a)&set(b))
            if len(symbols)>1:
                x=np.asarray([a[s] for s in symbols]); y=np.asarray([b[s] for s in symbols])
                if np.std(x)>0 and np.std(y)>0: correlations.append(float(spearmanr(x,y).statistic))
            atop={s for s,v in a.items() if v>=.9}; btop={s for s,v in b.items() if v>=.9}; abottom={s for s,v in a.items() if v<=.1}; bbottom={s for s,v in b.items() if v<=.1}
            if atop: top.append(len(atop&btop)/len(atop)); below.append(len({s for s in atop if s in b and b[s]<.5})/len(atop))
            if abottom: bottom.append(len(abottom&bbottom)/len(abottom))
            unselected={s for s,v in a.items() if v<.9}
            if unselected: entering.append(len(unselected&btop)/len(unselected))
        mean=lambda x:float(np.mean(x)) if x else None
        out.append({"lag_sessions":lag,"rank_autocorrelation":mean(correlations),"top_decile_persistence":mean(top),"bottom_decile_persistence":mean(bottom),"selected_falling_below_median":mean(below),"unselected_entering_top_tail":mean(entering)})
    return out

def rank_changes(rows):
    by_date=defaultdict(dict)
    for r in rows: by_date[r["trade_date"]][r["symbol"]]=r["prediction_percentile_rank"]
    dates=sorted(by_date); values=[]
    for i in range(1,len(dates)):
        a=by_date[dates[i-1]]; b=by_date[dates[i]]
        values += [b[s]-a[s] for s in sorted(set(a)&set(b))]
    a=np.asarray(values,float)
    return {"count":len(a),"mean":float(np.mean(a)) if len(a) else None,"median":float(np.median(a)) if len(a) else None,"p05":float(np.quantile(a,.05)) if len(a) else None,"p95":float(np.quantile(a,.95)) if len(a) else None}
