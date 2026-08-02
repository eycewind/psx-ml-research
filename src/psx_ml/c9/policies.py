from __future__ import annotations
from collections import defaultdict
from datetime import date
import math
def percentile_ranks(rows,score="prediction"):
    grouped=defaultdict(list)
    for r in rows: grouped[r["trade_date"]].append(r)
    out=[]
    for _,part in sorted(grouped.items()):
        ordered=sorted(part,key=lambda r:(r[score],r["symbol"])); n=len(ordered)
        for i,r in enumerate(ordered): out.append({**r,"prediction_percentile_rank":i/(n-1) if n>1 else .5})
    return out
def select(rows,kind,value,tail="top"):
    grouped=defaultdict(list)
    for r in rows: grouped[r["trade_date"]].append(r)
    out=[]
    for d,part in sorted(grouped.items()):
        ordered=sorted(part,key=lambda r:(r["prediction_percentile_rank"],r["symbol"]),reverse=tail=="top")
        if kind=="fixed": n=min(int(value),len(ordered))
        elif kind=="percentile": n=max(1,math.ceil(len(ordered)*float(value)))
        elif kind=="threshold":
            chosen=[r for r in ordered if (r["prediction_percentile_rank"]>=value if tail=="top" else r["prediction_percentile_rank"]<=value)]
            out += [{**r,"selection_date":d,"selection_tail":tail} for r in chosen]; continue
        else: raise ValueError(kind)
        out += [{**r,"selection_date":d,"selection_tail":tail} for r in ordered[:n]]
    return out
def schedule_dates(dates,schedule):
    dates=sorted(set(dates))
    if schedule=="daily": return dates
    if schedule=="every_2_sessions": return dates[::2]
    if schedule=="non_overlapping_5_session": return dates[::5]
    grouped=defaultdict(list)
    for d in dates:
        x=date.fromisoformat(str(d)); grouped[x.isocalendar()[:2]].append(d)
    if schedule=="weekly_first_session": return [min(v) for _,v in sorted(grouped.items())]
    if schedule=="weekly_last_session": return [max(v) for _,v in sorted(grouped.items())]
    if schedule=="Monday_only": return [d for d in dates if date.fromisoformat(str(d)).weekday()==0]
    if schedule=="Friday_only": return [d for d in dates if date.fromisoformat(str(d)).weekday()==4]
    raise ValueError(schedule)
def apply_liquidity(rows,screen):
    if screen=="L0": return list(rows)
    cutoff={"L1":.25,"L2":.50}.get(screen)
    if cutoff is None: raise ValueError(screen)
    return [r for r in rows if r.get("turnover_percentile_rank") is not None and r["turnover_percentile_rank"]>=cutoff]
def sector_constraint(rows,constraint):
    if constraint=="S0": return list(rows),[]
    grouped=defaultdict(list)
    for r in rows: grouped[r["trade_date"]].append(r)
    out=[]; skipped=[]
    for d,part in sorted(grouped.items()):
        ordered=sorted(part,key=lambda r:(-r["prediction_percentile_rank"],r["symbol"]))
        if constraint in {"S1","S2"}:
            cap=2 if constraint=="S1" else 1; counts=defaultdict(int)
            for r in ordered:
                sector=r.get("sector")
                if not sector: skipped.append({"trade_date":d,"symbol":r["symbol"],"reason":"missing_sector"}); continue
                if counts[sector]<cap: out.append(r); counts[sector]+=1
        elif constraint=="S3":
            sectors=defaultdict(list)
            for r in ordered: sectors[r.get("sector")].append(r)
            for sector,candidates in sorted(sectors.items(),key=lambda x:str(x[0])):
                if not sector: skipped += [{"trade_date":d,"symbol":r["symbol"],"reason":"missing_sector"} for r in candidates]
                else: out.append(candidates[0])
        else: raise ValueError(constraint)
    return out,skipped
