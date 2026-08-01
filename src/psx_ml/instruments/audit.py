from __future__ import annotations
from collections import defaultdict
import pyarrow as pa
from .classify import classify_observation, matching_rules

def sector_audit(intervals: pa.Table) -> pa.Table:
    groups=defaultdict(lambda:{"intervals":0,"symbols":set()})
    for r in intervals.to_pylist():
        key=(r["observed_sector"],r["instrument_type"],r["classification_source"],r["classification_rule"])
        groups[key]["intervals"]+=1; groups[key]["symbols"].add(r["symbol"])
    rows=[]
    for key,v in sorted(groups.items()):
        sector,typ,source,rule=key; symbols=sorted(v["symbols"])
        rows.append({"observed_sector":sector,"assigned_instrument_type":typ,"classification_source":source,"classification_rule":rule,
                     "interval_count":v["intervals"],"unique_symbol_count":len(symbols),"example_symbols":"|".join(symbols[:10])})
    return pa.Table.from_pylist(rows)

def rule_conflicts(source: pa.Table, config: dict) -> pa.Table:
    grouped=defaultdict(list)
    for r in source.select(["trade_date","symbol","sector"]).to_pylist():
        sector=r["sector"] or ""; matches=matching_rules(r["symbol"],sector,config)
        if len(matches)>1:
            win=classify_observation(r["symbol"],sector,config); competitors=sorted(x[3] for x in matches[1:])
            grouped[(r["symbol"],sector,win[3],win[0],"|".join(competitors))].append(r["trade_date"])
    rows=[]
    for (symbol,sector,rule,typ,competing),dates in sorted(grouped.items()):
        rows.append({"symbol":symbol,"observed_sector":sector,"winning_rule":rule,"winning_type":typ,"competing_rules":competing,
                     "effective_from":min(dates),"effective_to":max(dates)})
    return pa.Table.from_pylist(rows,schema=pa.schema([
        ("symbol",pa.string()),("observed_sector",pa.string()),("winning_rule",pa.string()),("winning_type",pa.string()),
        ("competing_rules",pa.string()),("effective_from",pa.string()),("effective_to",pa.string())]))
