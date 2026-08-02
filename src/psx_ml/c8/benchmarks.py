from __future__ import annotations

from collections import defaultdict
import math
from typing import Iterable


def _median_sorted(values: list[float]) -> float:
    n=len(values); mid=n//2
    return values[mid] if n%2 else (values[mid-1]+values[mid])/2.0


def leave_one_out_median(
    dates: Iterable[str], values: Iterable[float | None], symbols: Iterable[str],
    groups: Iterable[str | None] | None=None, minimum_peers: int=1,
) -> list[float | None]:
    """Same-date/group median excluding the row itself.

    ``minimum_peers`` is evaluated after exclusion. Non-finite values and null
    groups neither contribute nor receive a benchmark. Ties are ordered by
    symbol and original row position, although the median itself is tie invariant.
    """
    d=list(dates); v=list(values); s=list(symbols); g=list(groups) if groups is not None else ["__market__"]*len(d)
    if not (len(d)==len(v)==len(s)==len(g)): raise ValueError("benchmark inputs have unequal lengths")
    members=defaultdict(list)
    for i,(date,value,symbol,group) in enumerate(zip(d,v,s,g)):
        if group is not None and value is not None and math.isfinite(float(value)):
            members[(date,group)].append((float(value),symbol,i))
    out=[None]*len(d)
    for rows in members.values():
        rows.sort(key=lambda x:(x[0],x[1],x[2])); n=len(rows)
        if n-1<minimum_peers: continue
        ordered=[x[0] for x in rows]; remaining_n=n-1
        for rank,(_,_,original) in enumerate(rows):
            def retained(position): return ordered[position+(position>=rank)]
            mid=remaining_n//2
            out[original]=retained(mid) if remaining_n%2 else (retained(mid-1)+retained(mid))/2.0
    return out


def date_local_rank(dates: Iterable[str], values: Iterable[float | None], symbols: Iterable[str]) -> list[float | None]:
    """Deterministic [0,1] same-date ordinal rank; ties break by symbol."""
    d=list(dates); v=list(values); s=list(symbols)
    if not len(d)==len(v)==len(s): raise ValueError("rank inputs have unequal lengths")
    groups=defaultdict(list); out=[None]*len(d)
    for i,(date,value,symbol) in enumerate(zip(d,v,s)):
        if value is not None and math.isfinite(float(value)): groups[date].append((float(value),symbol,i))
    for rows in groups.values():
        rows.sort(key=lambda x:(x[0],x[1],x[2])); denominator=max(1,len(rows)-1)
        for rank,(_,_,original) in enumerate(rows): out[original]=rank/denominator if len(rows)>1 else 0.5
    return out
