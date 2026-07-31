from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FeatureDefinition:
    name: str; version: int; description: str; category: str; formula: str
    inputs: tuple[str,...]; field_family: str; lookback: int; minimum_observations: int
    scope: str; availability: str; null_policy: str; missing_observation_policy: str
    stale_price_sensitivity: str; output_dtype: str = "float64"

    def as_dict(self):
        d=asdict(self); d["inputs"]=list(self.inputs); return d


AVAILABILITY="after market close on trade_date; earliest downstream decision is next session"
NULL="null on insufficient history or invalid/nonpositive denominator; never imputed"
MISSING="observation-count windows; absent symbol-dates are not synthesized"


def build_registry(family: str) -> list[FeatureDefinition]:
    suffix="adj" if family=="adjusted" else "raw"
    close="close_adj" if family=="adjusted" else "close"
    volume="volume_adj" if family=="adjusted" else "volume"
    D=[]
    def add(name,desc,cat,formula,inputs,lookback,minobs,scope="symbol",stale="sensitive"):
        D.append(FeatureDefinition(name,1,desc,cat,formula,tuple(inputs),family,lookback,minobs,scope,AVAILABILITY,NULL,MISSING,stale))
    for w in (1,5,20):
        add(f"ret_{w}obs_{suffix}",f"Simple return over {w} prior observations","price",f"close[t]/close[t-{w}]-1",[close],w+1,w+1)
    for w in (1,20):
        add(f"log_ret_{w}obs_{suffix}",f"Log return over {w} prior observations","price",f"ln(close[t]/close[t-{w}])",[close],w+1,w+1)
    add(f"close_to_open_1obs_{suffix}","Current close/open return","price","close/open-1",[close,"open_adj" if family=="adjusted" else "open"],1,1)
    add(f"open_gap_1obs_{suffix}","Current open versus prior observed close","price","open[t]/close[t-1]-1",["open_adj" if family=="adjusted" else "open",close],2,2)
    add(f"close_to_mean_20obs_{suffix}","Close relative to trailing mean close","price","close/mean20(close)-1",[close],20,20)
    add(f"close_to_max_20obs_{suffix}","Close relative to trailing maximum close","price","close/max20(close)-1",[close],20,20)
    add(f"log1p_volume_{suffix}","Natural log of one plus volume","volume","log1p(volume)",[volume],1,1,stale="independent")
    add(f"volume_ratio_median_20obs_{suffix}","Volume divided by trailing median volume","volume","volume/median20(volume)",[volume],20,20,stale="independent")
    add(f"turnover_1obs_{suffix}","Adjustment-consistent close times volume","liquidity","close*volume",[close,volume],1,1,stale="independent")
    add(f"turnover_median_20obs_{suffix}","Trailing median turnover","liquidity","median20(close*volume)",[close,volume],20,20,stale="independent")
    add(f"rv_20obs_{suffix}","Sample standard deviation of one-observation log returns","volatility","std20(log_ret_1)",[close],21,21)
    add(f"true_range_1obs_{suffix}","Max range including prior close without clipping open/close","volatility","max(high-low,abs(high-prev_close),abs(low-prev_close))",["high_adj" if family=="adjusted" else "high","low_adj" if family=="adjusted" else "low",close],2,2)
    add(f"atr_mean_20obs_{suffix}","Mean of 20 true-range observations","volatility","mean20(true_range)",["high_adj" if family=="adjusted" else "high","low_adj" if family=="adjusted" else "low",close],21,21)
    add(f"amihud_mean_20obs_{suffix}","Mean absolute return divided by turnover","liquidity","mean20(abs(ret1)/turnover)",[close,volume],21,21)
    add("stale_close_run_length","Consecutive unchanged observed closes","quality","run_length(close[t]==close[t-1])",[close],2,1,stale="defines")
    add("unchanged_close_fraction_20obs","Fraction unchanged transitions in trailing observations","quality","mean20(close[t]==close[t-1])",[close],20,20,stale="defines")
    add("days_since_previous_observation","Calendar days since prior stored observation","quality","trade_date[t]-trade_date[t-1]",["trade_date"],2,2,stale="independent")
    add("strict_high_below_low_flag","Strict impossible range flag","quality","high<low",["high_adj" if family=="adjusted" else "high","low_adj" if family=="adjusted" else "low"],1,1,stale="independent")
    add("missing_volume_flag","Stored observation has null volume","quality","is_null(volume)",[volume],1,1,stale="independent")
    add("zero_volume_flag","Stored observation has zero volume","quality","volume==0",[volume],1,1,stale="independent")
    add(f"ret_20obs_rank_{suffix}","Eligible-universe percentile rank of 20-observation return","cross_sectional","average-tie percentile rank by date",[f"ret_20obs_{suffix}"],1,1,"cross_sectional")
    add(f"turnover_rank_{suffix}","Eligible-universe percentile rank of current turnover","cross_sectional","average-tie percentile rank by date",[f"turnover_1obs_{suffix}"],1,1,"cross_sectional",stale="independent")
    add(f"market_median_ret_1obs_{suffix}","Eligible-universe median one-observation return","market","median by date",[f"ret_1obs_{suffix}"],1,1,"market")
    add("eligible_symbol_count","Eligible symbols with stored rows on date","market","count eligible by date",["point_in_time_eligible"],1,1,"market",stale="independent")
    return D


def registry_hash(registry: list[FeatureDefinition]) -> str:
    payload=json.dumps([x.as_dict() for x in registry],sort_keys=True,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()
