from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
import re
import pyarrow as pa
from .taxonomy import validate_type

_RIGHT = re.compile(r"R\d*$")
_GOVERNMENT = re.compile(r"^(?:P\d{2}(?:GIS|GHS|PIB|FRR|VRR|FRZ)|PK\d{2}TB)")
_DEBT = re.compile(r"(?:TFC|SC\d*$)")

def matching_rules(symbol: str, sector: str, config: dict) -> list[tuple[str,str,str,str]]:
    matches=[]
    manual={x["symbol"]:x for x in config.get("manual_mappings",())}
    if symbol in manual:
        row=manual[symbol]; matches.append((validate_type(row["instrument_type"]),"manual_mapping",row.get("confidence","high"),f"manual_mapping:{symbol}"))
    if _GOVERNMENT.search(symbol): matches.append(("government_security","ticker_heuristic","low","ticker_regex:government_security"))
    if sector in config.get("sector_rules",{}): matches.append((validate_type(config["sector_rules"][sector]),"observed_sector_rule","low",f"sector_exact:{sector}"))
    if symbol.endswith("ETF"): matches.append(("ETF","ticker_heuristic","low","ticker_suffix:ETF"))
    if _DEBT.search(symbol): matches.append(("debt_security","ticker_heuristic","low","ticker_regex:debt_security"))
    if _RIGHT.search(symbol): matches.append(("right_or_entitlement","ticker_heuristic","low","ticker_regex:right_or_entitlement"))
    if sector.startswith(config.get("ordinary_equity_sector_prefix","08")):
        if symbol.endswith(("PS","CPS")): matches.append(("preference_share","ticker_heuristic","low","sector_prefix:08+preference_suffix"))
        matches.append(("ordinary_equity","sector_prefix_inference","low","sector_prefix:08"))
    return matches

def classify_observation(symbol: str, sector: str, config: dict) -> tuple[str,str,str,str]:
    matches=matching_rules(symbol,sector,config)
    return matches[0] if matches else ("unknown","insufficient_metadata","unknown","no_rule_matched")

def classify_intervals(source: pa.Table, config: dict) -> pa.Table:
    required={"trade_date","symbol","sector"}
    if not required.issubset(source.column_names): raise ValueError(f"missing columns: {required-set(source.column_names)}")
    grouped=defaultdict(list)
    for r in source.select(sorted(required)).to_pylist():
        typ,src,confidence,rule=classify_observation(r["symbol"],r["sector"] or "",config)
        grouped[r["symbol"]].append((r["trade_date"],typ,src,confidence,rule,r["sector"] or ""))
    out=[]
    for symbol, rows in sorted(grouped.items()):
        rows=sorted(set(rows)); start=0
        for i in range(1,len(rows)+1):
            if i<len(rows) and rows[i][1:]==rows[start][1:]: continue
            d0=date.fromisoformat(rows[start][0]); d1=date.fromisoformat(rows[i-1][0])
            typ,src,confidence,rule,sector=rows[start][1:]
            out.append({"symbol":symbol,"effective_from":d0.isoformat(),"effective_to":d1.isoformat(),"instrument_type":typ,
                        "classification_source":src,"classification_confidence":confidence,"classification_rule":rule,"observed_sector":sector})
            start=i
    return pa.Table.from_pylist(out)

def validate_intervals(table: pa.Table) -> None:
    last={}
    for r in sorted(table.to_pylist(),key=lambda x:(x["symbol"],x["effective_from"])):
        validate_type(r["instrument_type"])
        if r["effective_from"]>r["effective_to"]: raise ValueError("reversed effective interval")
        if r["symbol"] in last and r["effective_from"]<=last[r["symbol"]]: raise ValueError("overlapping effective intervals")
        last[r["symbol"]]=r["effective_to"]
