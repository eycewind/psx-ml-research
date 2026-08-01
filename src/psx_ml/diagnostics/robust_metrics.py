from __future__ import annotations
import numpy as np
from scipy.stats import pearsonr, spearmanr

def regression_robust(y,p,trim_fraction=.01,huber_delta=.1):
    y=np.asarray(y,float); p=np.asarray(p,float); e=y-p; ae=np.abs(e); keep=max(1,int(np.floor(len(e)*(1-trim_fraction))))
    trimmed=np.partition(e*e,keep-1)[:keep]
    huber=np.where(ae<=huber_delta,.5*e*e,huber_delta*(ae-.5*huber_delta))
    corr=lambda fn: float(fn(y,p).statistic) if len(y)>1 and np.std(y)>0 and np.std(p)>0 else None
    return {"n":len(y),"mae":float(ae.mean()),"median_absolute_error":float(np.median(ae)),"rmse":float(np.sqrt(np.mean(e*e))),
            "trimmed_rmse":float(np.sqrt(trimmed.mean())),"huber_loss":float(huber.mean()),"pearson":corr(pearsonr),"spearman":corr(spearmanr),
            "directional_accuracy":float(np.mean((y>0)==(p>0)))}

def daily_ic(dates,y,p,minimum=10):
    dates=np.asarray(dates,object); y=np.asarray(y,float); p=np.asarray(p,float); values=[]
    for d in sorted(set(dates)):
        m=dates==d
        if m.sum()>=minimum and np.std(y[m])>0 and np.std(p[m])>0: values.append(float(spearmanr(y[m],p[m]).statistic))
    return {"dates":len(values),"mean_daily_ic":float(np.mean(values)) if values else None,"median_daily_ic":float(np.median(values)) if values else None,
            "daily_ic_std":float(np.std(values)) if values else None,"positive_ic_fraction":float(np.mean(np.asarray(values)>0)) if values else None}
