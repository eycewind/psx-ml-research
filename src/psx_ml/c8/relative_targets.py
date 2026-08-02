from __future__ import annotations

from .benchmarks import date_local_rank,leave_one_out_median


def build_relative_target_columns(rows: list[dict], horizons=(5,10,20), minimum_sector_peers=5) -> dict[str,list]:
    """Build C8 targets for already-filtered point-in-time eligible equities."""
    dates=[r["trade_date"] for r in rows]; symbols=[r["symbol"] for r in rows]; sectors=[r.get("sector") for r in rows]
    result={}
    for h in horizons:
        absolute=[r.get(f"fwd_open_to_close_ret_{h}s_adj") for r in rows]
        market=leave_one_out_median(dates,absolute,symbols,minimum_peers=1)
        sector=leave_one_out_median(dates,absolute,symbols,sectors,minimum_peers=minimum_sector_peers)
        mr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,market)]
        sr=[None if a is None or b is None else float(a)-b for a,b in zip(absolute,sector)]
        result[f"market_loo_median_ret_{h}s"]=market
        result[f"sector_loo_median_ret_{h}s"]=sector
        result[f"fwd_market_relative_ret_{h}s"]=mr
        result[f"fwd_sector_relative_ret_{h}s"]=sr
        result[f"fwd_market_relative_rank_{h}s"]=date_local_rank(dates,mr,symbols)
        result[f"outperform_market_{h}s"]=[None if x is None else int(x>0) for x in mr]
        result[f"outperform_sector_{h}s"]=[None if x is None else int(x>0) for x in sr]
    return result

