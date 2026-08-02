from __future__ import annotations

from collections import Counter
import math
from .benchmarks import date_local_rank,leave_one_out_median


def build_relative_target_columns(rows: list[dict], horizons=(5,10,20), minimum_sector_peers=5, relaxed_sector_peers=3, shrinkage_strength=5.0) -> dict[str,list]:
    """Build C8 targets for already-filtered point-in-time eligible equities."""
    dates=[r["trade_date"] for r in rows]; symbols=[r["symbol"] for r in rows]; sectors=[r.get("sector") for r in rows]
    result={}
    for h in horizons:
        absolute=[r.get(f"fwd_open_to_close_ret_{h}s_adj") for r in rows]
        market=leave_one_out_median(dates,absolute,symbols,minimum_peers=1)
        sector=leave_one_out_median(dates,absolute,symbols,sectors,minimum_peers=minimum_sector_peers)
        relaxed=leave_one_out_median(dates,absolute,symbols,sectors,minimum_peers=relaxed_sector_peers)
        counts=Counter((d,g) for d,g,a in zip(dates,sectors,absolute) if g is not None and a is not None and math.isfinite(float(a)))
        peers=[0 if g is None else counts[(d,g)]-int(a is not None and math.isfinite(float(a))) for d,g,a in zip(dates,sectors,absolute)]
        weights=[None if n<relaxed_sector_peers else n/(n+shrinkage_strength) for n in peers]
        shrunk=[None if sm is None or mm is None or w is None else w*sm+(1-w)*mm for sm,mm,w in zip(relaxed,market,weights)]
        mr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,market)]
        sr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,sector)]
        relaxed_sr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,relaxed)]
        shrunk_sr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,shrunk)]
        result[f"market_loo_median_ret_{h}s"]=market
        result[f"sector_loo_median_ret_{h}s"]=sector
        result[f"sector_loo_median_ret_{h}s_relaxed_3_peer"]=relaxed
        result[f"sector_market_shrunk_benchmark_ret_{h}s"]=shrunk
        result[f"sector_valid_peer_count_{h}s"]=peers
        result[f"sector_benchmark_weight_{h}s"]=weights
        result[f"sector_benchmark_tier_{h}s"]=["strict_5_peer" if n>=minimum_sector_peers else "relaxed_3_peer" if n>=relaxed_sector_peers else "market_relative_only" for n in peers]
        result[f"sector_benchmark_confidence_{h}s"]=["high" if n>=minimum_sector_peers else "lower" if n>=relaxed_sector_peers else "unavailable" for n in peers]
        result[f"fwd_market_relative_ret_{h}s"]=mr
        result[f"fwd_sector_relative_ret_{h}s"]=sr
        result[f"fwd_sector_relative_ret_{h}s_relaxed_3_peer"]=relaxed_sr
        result[f"fwd_sector_relative_ret_{h}s_shrunk_3_peer"]=shrunk_sr
        result[f"strict_5_peer_matched_subset_{h}s"]=[x is not None for x in sr]
        result[f"fwd_market_relative_rank_{h}s"]=date_local_rank(dates,mr,symbols)
        result[f"outperform_market_{h}s"]=[None if x is None else int(x>0) for x in mr]
        result[f"outperform_sector_{h}s"]=[None if x is None else int(x>0) for x in sr]
        result[f"outperform_sector_{h}s_relaxed_3_peer"]=[None if x is None else int(x>0) for x in relaxed_sr]
        result[f"outperform_sector_{h}s_shrunk_3_peer"]=[None if x is None else int(x>0) for x in shrunk_sr]
    return result
