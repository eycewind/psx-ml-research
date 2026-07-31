from __future__ import annotations

import sqlite3
from collections import deque
from statistics import median


def build_point_in_time(con: sqlite3.Connection, lookback_sessions: int,
                        minimum_history_sessions: int,
                        minimum_median_turnover_pkr: float,
                        maximum_stale_fraction: float):
    """Eligibility at D uses only observations for that symbol through D."""
    by_symbol: dict[str, deque] = {}
    rows=con.execute(
        "SELECT trade_date,symbol,close,volume FROM daily_ohlc "
        "ORDER BY trade_date,symbol"
    )
    for r in rows:
        sym=r["symbol"]
        q=by_symbol.setdefault(sym, deque(maxlen=lookback_sessions))
        turnover = (r["close"] * r["volume"]) if r["close"] is not None and r["volume"] is not None else None
        stale = bool(q and r["close"] == q[-1][1])
        q.append((r["trade_date"], r["close"], turnover, stale))
        turnovers=[x[2] for x in q if x[2] is not None]
        n=len(q); med=median(turnovers) if turnovers else None
        stale_fraction=sum(x[3] for x in q)/n if n else None
        reasons=[]
        if n < minimum_history_sessions: reasons.append("insufficient_history")
        if med is None or med < minimum_median_turnover_pkr: reasons.append("low_turnover")
        if stale_fraction is None or stale_fraction > maximum_stale_fraction: reasons.append("stale_price")
        yield {"trade_date":r["trade_date"],"symbol":sym,
                    "window_start":q[0][0],"window_end":r["trade_date"],
                    "observations":n,"median_turnover_pkr":med,
                    "stale_fraction":stale_fraction,"eligible":not reasons,
                    "reason":"eligible" if not reasons else ";".join(reasons)}
