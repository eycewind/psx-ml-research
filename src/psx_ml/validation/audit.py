from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date
from statistics import median


def _count(con: sqlite3.Connection, where: str) -> int:
    return con.execute(f"SELECT COUNT(*) FROM daily_ohlc WHERE {where}").fetchone()[0]


def audit_daily(con: sqlite3.Connection, stale_run_sessions: int = 5,
                factor_tolerance: float = 1e-6) -> dict:
    rows = con.execute(
        "SELECT trade_date,symbol,open,high,low,close,volume,open_missing,"
        "open_adj,high_adj,low_adj,close_adj,volume_adj,adj_factor "
        "FROM daily_ohlc ORDER BY symbol,trade_date"
    )
    base = dict(con.execute(
        "SELECT COUNT(*) rows,COUNT(DISTINCT symbol) symbols,"
        "COUNT(DISTINCT trade_date) dates,MIN(trade_date) min_date,"
        "MAX(trade_date) max_date FROM daily_ohlc"
    ).fetchone())
    duplicates = con.execute(
        "SELECT COUNT(*) FROM (SELECT trade_date,symbol,COUNT(*) n "
        "FROM daily_ohlc GROUP BY trade_date,symbol HAVING n>1)"
    ).fetchone()[0]
    nulls = {c: _count(con, f'"{c}" IS NULL') for c in (
        "trade_date","symbol","open","high","low","close","volume","ldcp",
        "open_adj","high_adj","low_adj","close_adj","volume_adj","adj_factor")}
    metric_names=("invalid_dates","missing_volume","zero_volume","negative_volume",
        "invalid_open_missing_flag","open_missing_inconsistent","nonpositive_raw_price",
        "high_below_low","open_outside_range","close_outside_range","null_adj_factor",
        "nonpositive_adj_factor","nonpositive_adjusted_price","adjusted_price_factor_mismatch",
        "adjusted_volume_factor_mismatch","adjusted_high_below_low",
        "adjusted_open_outside_range","stale_close_transitions",
        "stale_runs_at_least_threshold")
    metrics = defaultdict(int, {name:0 for name in metric_names})
    histories: dict[str, dict] = {}
    dates_by_symbol: dict[str, list[str]] = defaultdict(list)
    all_dates: list[str] = []
    previous: dict[str, tuple[float | None, int]] = {}
    stale_runs: list[int] = []
    for r in rows:
        d, sym = r["trade_date"], r["symbol"]
        try:
            if date.fromisoformat(d).isoformat() != d:
                metrics["invalid_dates"] += 1
        except (TypeError, ValueError):
            metrics["invalid_dates"] += 1
        dates_by_symbol[sym].append(d)
        all_dates.append(d)
        o,h,l,c,v = r["open"],r["high"],r["low"],r["close"],r["volume"]
        if v is None: metrics["missing_volume"] += 1
        elif v == 0: metrics["zero_volume"] += 1
        elif v < 0: metrics["negative_volume"] += 1
        if r["open_missing"] not in (0,1): metrics["invalid_open_missing_flag"] += 1
        if (o is None) != (r["open_missing"] == 1): metrics["open_missing_inconsistent"] += 1
        if any(x is not None and x <= 0 for x in (h,l,c)):
            metrics["nonpositive_raw_price"] += 1
        if h is not None and l is not None and h < l:
            metrics["high_below_low"] += 1
        if None not in (o,h,l) and not (l <= o <= h):
            metrics["open_outside_range"] += 1
        if None not in (c,h,l) and not (l <= c <= h):
            metrics["close_outside_range"] += 1
        factor = r["adj_factor"]
        if factor is None: metrics["null_adj_factor"] += 1
        elif factor <= 0: metrics["nonpositive_adj_factor"] += 1
        for raw, adj in ((o,r["open_adj"]),(h,r["high_adj"]),(l,r["low_adj"]),(c,r["close_adj"])):
            if adj is not None and adj <= 0: metrics["nonpositive_adjusted_price"] += 1
            if raw is not None and adj is not None and factor and abs(adj - raw*factor) > factor_tolerance*max(1,abs(adj)):
                metrics["adjusted_price_factor_mismatch"] += 1
        if v is not None and r["volume_adj"] is not None and factor and abs(r["volume_adj"] - v/factor) > factor_tolerance*max(1,abs(r["volume_adj"])):
            metrics["adjusted_volume_factor_mismatch"] += 1
        ah,al,ao = r["high_adj"],r["low_adj"],r["open_adj"]
        if None not in (ah,al) and ah < al: metrics["adjusted_high_below_low"] += 1
        if None not in (ao,ah,al) and not (al <= ao <= ah): metrics["adjusted_open_outside_range"] += 1
        prev_close, run = previous.get(sym, (None,0))
        run = run + 1 if prev_close is not None and c == prev_close else 0
        if run: metrics["stale_close_transitions"] += 1
        if run == stale_run_sessions - 1: metrics["stale_runs_at_least_threshold"] += 1
        previous[sym] = (c,run)
    exchange_dates = sorted(set(all_dates))
    date_pos = {d:i for i,d in enumerate(exchange_dates)}
    gap_rates=[]
    for sym, dates in sorted(dates_by_symbol.items()):
        valid=[d for d in dates if d in date_pos]
        if not valid: continue
        span=date_pos[valid[-1]]-date_pos[valid[0]]+1
        missing=span-len(valid)
        gap_rates.append(missing/span)
        histories[sym]={"first_date":valid[0],"last_date":valid[-1],"observed_rows":len(valid),"exchange_dates_in_span":span,"missing_dates":missing,"missing_rate":missing/span}
    return {
        "summary": base,
        "duplicates": duplicates,
        "null_counts": nulls,
        "quality_metrics": dict(sorted(metrics.items())),
        "history_summary": {
            "symbols": len(histories),
            "median_missing_rate": median(gap_rates) if gap_rates else None,
            "symbols_with_gaps": sum(v["missing_dates"]>0 for v in histories.values()),
        },
        "symbol_histories": histories,
        "definitions": {"stale_run_sessions":stale_run_sessions,"factor_tolerance":factor_tolerance},
    }
