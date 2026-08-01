from __future__ import annotations

from collections import Counter

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from psx_ml.features.quality import average_tie_percentile
from .calendar import dense_row_lookup,exchange_calendar

def _float(table,name): return np.asarray(table[name].to_numpy(zero_copy_only=False),dtype=float)

def generate_targets(features,daily,config):
    features=features.take(pc.sort_indices(features,sort_keys=[("trade_date","ascending"),("symbol","ascending")]))
    daily=daily.take(pc.sort_indices(daily,sort_keys=[("trade_date","ascending"),("symbol","ascending")]))
    fd=np.array(features["trade_date"].to_pylist(),dtype=object); fs=np.array(features["symbol"].to_pylist(),dtype=object)
    dd=np.array(daily["trade_date"].to_pylist(),dtype=object); ds=np.array(daily["symbol"].to_pylist(),dtype=object)
    cal,date_index=exchange_calendar(dd); syms,sym_index,lookup=dense_row_lookup(dd,ds,cal,date_index)
    fdi=np.array([date_index[d] for d in fd],dtype=np.int32); fsi=np.array([sym_index[s] for s in fs],dtype=np.int32)
    open_adj=_float(daily,"open_adj"); close_adj=_float(daily,"close_adj")
    eligible=np.asarray(features["point_in_time_eligible"].to_numpy(zero_copy_only=False),dtype=bool)
    arrays={}; metrics={}; n=len(fd)
    entry_idx=fdi+1; entry_exists=entry_idx<len(cal); entry_dates=np.empty(n,dtype=object); entry_dates[:]=None; entry_dates[entry_exists]=cal[entry_idx[entry_exists]]
    entry_rows=np.full(n,-1,dtype=np.int32); valid_calendar=np.flatnonzero(entry_exists); entry_rows[valid_calendar]=lookup[entry_idx[valid_calendar],fsi[valid_calendar]]
    arrays["entry_date"]=pa.array(entry_dates,type=pa.string())
    returns={}; reasons={}
    for h in config.horizons:
        end_idx=entry_idx+h; end_exists=end_idx<len(cal); end_dates=np.empty(n,dtype=object); end_dates[:]=None; end_dates[end_exists]=cal[end_idx[end_exists]]
        exit_rows=np.full(n,-1,dtype=np.int32); valid_end=np.flatnonzero(end_exists); exit_rows[valid_end]=lookup[end_idx[valid_end],fsi[valid_end]]
        ret=np.full(n,np.nan); reason=np.empty(n,dtype=object); reason[:]=None
        for i in range(n):
            if not entry_exists[i]: reason[i]="insufficient_future_sessions"; continue
            er=entry_rows[i]
            if er<0: reason[i]="missing_next_session_observation"; continue
            ep=open_adj[er]
            if not np.isfinite(ep): reason[i]="missing_entry_open"; continue
            if ep<=0: reason[i]="nonpositive_entry_open"; continue
            if not end_exists[i]: reason[i]="insufficient_future_sessions"; continue
            xr=exit_rows[i]
            if xr<0: reason[i]="missing_exit_observation"; continue
            xp=close_adj[xr]
            if not np.isfinite(xp): reason[i]="missing_exit_close"; continue
            if xp<=0: reason[i]="nonpositive_exit_close"; continue
            ret[i]=xp/ep-1.0
        name=f"fwd_open_to_close_ret_{h}s_adj"; returns[h]=ret; reasons[h]=reason
        arrays[f"target_end_date_{h}s"]=pa.array(end_dates,type=pa.string())
        arrays[name]=pa.array(ret,mask=~np.isfinite(ret),type=pa.float64())
        arrays[f"target_null_reason_{h}s"]=pa.array(reason,type=pa.string())
        metrics[name]={"valid":int(np.isfinite(ret).sum()),"null":int((~np.isfinite(ret)).sum()),"null_reasons":dict(sorted(Counter(x for x in reason if x).items()))}
    for h in config.classification_horizons:
        x=returns[h]; y=np.where(np.isfinite(x),(x>0).astype(float),np.nan)
        arrays[f"up_{h}s"]=pa.array(y,mask=~np.isfinite(y),type=pa.float64())
        metrics[f"up_{h}s"]={"valid":int(np.isfinite(y).sum()),"positive":int(np.nansum(y)),"negative_or_zero":int(np.isfinite(y).sum()-np.nansum(y))}
    # Feature input is canonical date/symbol ordered; group exact feature dates.
    starts=np.r_[0,np.flatnonzero(fd[1:]!=fd[:-1])+1,n]
    rank_population={h:[] for h in config.rank_horizons}
    for h in config.rank_horizons:
        rank=np.full(n,np.nan)
        for a,b in zip(starts[:-1],starts[1:]):
            values=np.where(eligible[a:b],returns[h][a:b],np.nan); rank[a:b]=average_tie_percentile(values,config.minimum_rank_population)
            rank_population[h].append(int(np.isfinite(values).sum()))
        arrays[f"fwd_ret_{h}s_rank"]=pa.array(rank,mask=~np.isfinite(rank),type=pa.float64())
        metrics[f"fwd_ret_{h}s_rank"]={"valid":int(np.isfinite(rank).sum()),"population_min":min(rank_population[h]),"population_median":float(np.median(rank_population[h])),"population_max":max(rank_population[h])}
    output=features
    for name,array in arrays.items(): output=output.append_column(name,array)
    return output,metrics,cal
