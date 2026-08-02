from __future__ import annotations

from collections import defaultdict
import math
import numpy as np
from .benchmarks import date_local_rank,leave_one_out_median

def _finite(x): return x is not None and math.isfinite(float(x))

def _derive_ret10(rows):
    by_symbol=defaultdict(list); out=[None]*len(rows)
    for i,r in sorted(enumerate(rows),key=lambda z:(z[1]["symbol"],z[1]["trade_date"])):
        history=by_symbol[r["symbol"]]; current=r.get("ret_5obs_adj")
        if len(history)>=5 and _finite(current) and _finite(history[-5]): out[i]=(1+float(current))*(1+float(history[-5]))-1
        history.append(current)
    return out

def _loo_stat(dates,groups,values,minimum,kind):
    if kind=="median": return leave_one_out_median(dates,values,[str(i) for i in range(len(dates))],groups,minimum)
    buckets=defaultdict(list); out=[None]*len(dates)
    for i,(d,g,v) in enumerate(zip(dates,groups,values)):
        if g is not None and _finite(v): buckets[(d,g)].append((i,float(v)))
    for part in buckets.values():
        count=len(part); total=sum(v for _,v in part); total_sq=sum(v*v for _,v in part); positives=sum(v>0 for _,v in part)
        for i,value in part:
            peers=count-1
            if peers<minimum: continue
            if kind=="positive": out[i]=(positives-int(value>0))/peers
            elif kind=="std":
                mean=(total-value)/peers; variance=max(0.0,(total_sq-value*value)/peers-mean*mean); out[i]=math.sqrt(variance)
    return out

def _rolling_pair(rows,x,y,window=60,minimum=30):
    by_symbol=defaultdict(list); beta=[None]*len(rows); corr=[None]*len(rows)
    for i,r in sorted(enumerate(rows),key=lambda z:(z[1]["symbol"],z[1]["trade_date"])):
        history=by_symbol[r["symbol"]]
        if _finite(x[i]) and _finite(y[i]): history.append((float(x[i]),float(y[i])))
        sample=history[-window:]
        if len(sample)>=minimum:
            a=np.asarray([z[0] for z in sample]); b=np.asarray([z[1] for z in sample]); variance=float(np.var(b))
            beta[i]=float(np.cov(a,b,ddof=0)[0,1]/variance) if variance>0 else None
            corr[i]=float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else None
    return beta,corr

def build_context_features(rows,minimum_sector_peers=5,rolling_window=60,minimum_rolling=30):
    """Build current/past-only C8 market, sector and stock-relative features."""
    dates=[r["trade_date"] for r in rows]; symbols=[r["symbol"] for r in rows]; sectors=[r.get("sector") for r in rows]; market_group=["market"]*len(rows)
    ret={1:[r.get("ret_1obs_adj") for r in rows],5:[r.get("ret_5obs_adj") for r in rows],10:_derive_ret10(rows),20:[r.get("ret_20obs_adj") for r in rows]}
    result={}
    for h,values in ret.items():
        result[f"market_median_ret_{h}obs"]=_loo_stat(dates,market_group,values,1,"median")
        by_date=defaultdict(list)
        for d,v in zip(dates,values):
            if _finite(v): by_date[d].append(float(v))
        result[f"market_mean_ret_{h}obs"]=[float(np.mean(by_date[d])) if by_date[d] else None for d in dates]
        result[f"sector_median_ret_{h}obs"]=_loo_stat(dates,sectors,values,minimum_sector_peers,"median")
    for h in (1,5):
        result[f"market_breadth_positive_{h}obs"]=_loo_stat(dates,market_group,ret[h],1,"positive")
        result[f"sector_breadth_positive_{h}obs"]=_loo_stat(dates,sectors,ret[h],minimum_sector_peers,"positive")
        result[f"market_advance_decline_ratio_{h}obs"]=[None if x is None or x>=1 else x/(1-x) for x in result[f"market_breadth_positive_{h}obs"]]
    above=[None if not _finite(r.get("close_to_mean_20obs_adj")) else float(r["close_to_mean_20obs_adj"])>0 for r in rows]
    by_date=defaultdict(list)
    for d,v in zip(dates,above):
        if v is not None: by_date[d].append(v)
    result["market_breadth_above_20obs_mean"]=[float(np.mean(by_date[d])) if by_date[d] else None for d in dates]
    for h in (1,5,20): result[f"market_cross_sectional_dispersion_{h}obs"]=_loo_stat(dates,market_group,ret[h],1,"std")
    for h in (1,20): result[f"sector_cross_sectional_dispersion_{h}obs"]=_loo_stat(dates,sectors,ret[h],minimum_sector_peers,"std")
    turnover1=[r.get("turnover_1obs_adj") for r in rows]; turnover20=[r.get("turnover_median_20obs_adj") for r in rows]
    result["market_turnover_median_1obs"]=_loo_stat(dates,market_group,turnover1,1,"median")
    result["market_turnover_median_20obs"]=_loo_stat(dates,market_group,turnover20,1,"median")
    result["sector_turnover_median_20obs"]=_loo_stat(dates,sectors,turnover20,minimum_sector_peers,"median")
    counts=defaultdict(int)
    for d in dates: counts[d]+=1
    ordered=sorted(counts); lag5={d:(counts[d]-counts[ordered[i-5]] if i>=5 else None) for i,d in enumerate(ordered)}
    result["eligible_symbol_count"]=[float(counts[d]) for d in dates]; result["eligible_symbol_count_change_5obs"]=[None if lag5[d] is None else float(lag5[d]) for d in dates]
    sector_counts=defaultdict(int)
    for d,g in zip(dates,sectors):
        if g is not None: sector_counts[(d,g)]+=1
    result["sector_eligible_symbol_count"]=[None if g is None else float(sector_counts[(d,g)]-1) for d,g in zip(dates,sectors)]
    # Rolling volatility of each row's leave-one-out benchmark series.
    for scope in ("market","sector"):
        base=result[f"{scope}_median_ret_1obs"]
        for w in (5,20):
            by_symbol=defaultdict(list); values=[None]*len(rows)
            for i,r in sorted(enumerate(rows),key=lambda z:(z[1]["symbol"],z[1]["trade_date"])):
                if _finite(base[i]): by_symbol[r["symbol"]].append(float(base[i]))
                history=by_symbol[r["symbol"]][-w:]
                if len(history)==w: values[i]=float(np.std(history))
            result[f"{scope}_realized_volatility_{w}obs"]=values
    for h in (1,5,20):
        market=result[f"market_median_ret_{h}obs"]; sector=result[f"sector_median_ret_{h}obs"]
        sm=[None if not _finite(a) or not _finite(b) else float(a)-float(b) for a,b in zip(ret[h],market)]
        ss=[None if not _finite(a) or not _finite(b) else float(a)-float(b) for a,b in zip(ret[h],sector)]
        result[f"stock_minus_market_ret_{h}obs"]=sm; result[f"stock_minus_sector_ret_{h}obs"]=ss
        result[f"stock_market_relative_rank_{h}obs"]=date_local_rank(dates,sm,symbols)
        # Date+sector local rank via composite date key; null sectors stay null.
        keys=[None if g is None else f"{d}\0{g}" for d,g in zip(dates,sectors)]
        ranks=date_local_rank(keys,ss,symbols); result[f"stock_sector_relative_rank_{h}obs"]=[None if sectors[i] is None else ranks[i] for i in range(len(rows))]
    mb,mc=_rolling_pair(rows,ret[1],result["market_median_ret_1obs"],rolling_window,minimum_rolling)
    sb,sc=_rolling_pair(rows,ret[1],result["sector_median_ret_1obs"],rolling_window,minimum_rolling)
    result.update({"rolling_beta_market_60obs":mb,"rolling_corr_market_60obs":mc,"rolling_beta_sector_60obs":sb,"rolling_corr_sector_60obs":sc})
    return result
