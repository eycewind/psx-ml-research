from __future__ import annotations
from collections import Counter, defaultdict
import csv, re
from pathlib import Path
import pyarrow as pa

_MATURITY = re.compile(r"\d{6,}$")

def build_review_queue(intervals: pa.Table, conflicts: pa.Table, pit: pa.Table, predictions: pa.Table, targets: pa.Table, thresholds: dict) -> list[dict]:
    interval_rows=intervals.to_pylist(); by_symbol=defaultdict(list)
    for r in interval_rows: by_symbol[r["symbol"]].append(r)
    eligible=Counter(r["symbol"] for r in pit.select(["symbol","eligible"]).to_pylist() if r["eligible"])
    loss=defaultdict(float); target_total=defaultdict(float); by_target=defaultdict(lambda:defaultdict(float))
    for r in predictions.to_pylist():
        value=(r["target"]-r["prediction"])**2; by_target[r["target_name"]][r["symbol"]]+=value; target_total[r["target_name"]]+=value
    top_loss=set()
    for values in by_target.values(): top_loss.update(s for s,_ in sorted(values.items(),key=lambda x:(-x[1],x[0]))[:10])
    for target,values in by_target.items():
        for symbol,value in values.items(): loss[symbol]+=value/target_total[target] if target_total[target] else 0
    extreme=Counter()
    for r in targets.to_pylist():
        for h,threshold in thresholds.items():
            value=r.get(f"fwd_open_to_close_ret_{h}s_adj")
            if value is not None and abs(value)>threshold: extreme[r["symbol"]]+=1
    conflict_symbols={r["symbol"] for r in conflicts.to_pylist()}; reasons=defaultdict(set)
    for s in top_loss: reasons[s].add("top_c5_squared_loss")
    for s in conflict_symbols: reasons[s].add("classification_rule_conflict")
    for s,rows in by_symbol.items():
        if len(rows)>1: reasons[s].add("multiple_classification_intervals")
        if eligible[s] and any(r["instrument_type"] in {"government_security","debt_security","sukuk","commercial_paper"} for r in rows): reasons[s].add("special_security_entered_pit_universe")
        days=sum((__import__('datetime').date.fromisoformat(r["effective_to"])-__import__('datetime').date.fromisoformat(r["effective_from"])).days+1 for r in rows)
        if days<=20 or _MATURITY.search(s): reasons[s].add("short_interval_or_maturity_like_ticker")
        if any(r["classification_rule"]=="sector_prefix:08" for r in rows) and (any(c.isdigit() for c in s) or len(s)>7 or len(rows)>1): reasons[s].add("unusual_prefix_inferred_equity")
    for s,n in extreme.items():
        if n: reasons[s].add("extreme_c4_target")
    output=[]
    priority_order={"top_c5_squared_loss":0,"classification_rule_conflict":1,"special_security_entered_pit_universe":2,"extreme_c4_target":3,"multiple_classification_intervals":4,"unusual_prefix_inferred_equity":5,"short_interval_or_maturity_like_ticker":6}
    for symbol in sorted(reasons,key=lambda s:(min(priority_order[x] for x in reasons[s]),s)):
        first=sorted(by_symbol[symbol],key=lambda x:x["effective_from"])[0]; why=sorted(reasons[symbol],key=lambda x:priority_order[x])
        output.append({**{k:first[k] for k in ("symbol","effective_from","effective_to","instrument_type","classification_source","classification_confidence","classification_rule","observed_sector")},
                       "pit_eligible_row_count":eligible[symbol],"c5_loss_contribution":loss[symbol],"extreme_target_count":extreme[symbol],
                       "review_priority":min(priority_order[x] for x in why)+1,"review_reason":"|".join(why)})
    return output

def write_review_queue(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=["symbol","effective_from","effective_to","instrument_type","classification_source","classification_confidence","classification_rule","observed_sector","pit_eligible_row_count","c5_loss_contribution","extreme_target_count","review_priority","review_reason"]
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)
