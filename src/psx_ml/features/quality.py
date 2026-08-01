from __future__ import annotations

import numpy as np


def rolling_stat(values: np.ndarray, window: int, fn, minobs: int|None=None) -> np.ndarray:
    out=np.full(len(values),np.nan); need=minobs or window
    for i in range(len(values)):
        x=values[max(0,i-window+1):i+1]; finite=x[np.isfinite(x)]
        if len(finite)>=need: out[i]=fn(finite)
    return out


def lag_return(values: np.ndarray, lag: int, logarithmic: bool=False) -> np.ndarray:
    out=np.full(len(values),np.nan)
    for i in range(lag,len(values)):
        a,b=values[i],values[i-lag]
        if np.isfinite(a) and np.isfinite(b) and a>0 and b>0:
            ratio=a/b; out[i]=np.log(ratio) if logarithmic else ratio-1.0
    return out


def average_tie_percentile(values: np.ndarray, minimum_size: int) -> np.ndarray:
    out=np.full(len(values),np.nan); valid=np.flatnonzero(np.isfinite(values)); n=len(valid)
    if n<minimum_size: return out
    order=valid[np.argsort(values[valid],kind="mergesort")]
    pos=0
    while pos<n:
        end=pos+1
        while end<n and values[order[end]]==values[order[pos]]: end+=1
        avg=(pos+end-1)/2
        percentile=0.5 if n==1 else avg/(n-1)
        out[order[pos:end]]=percentile; pos=end
    return out
