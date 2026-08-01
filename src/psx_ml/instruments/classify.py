from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
import re
import pyarrow as pa
from .taxonomy import validate_type

_RIGHT = re.compile(r"R\d*$")
_GOVERNMENT = re.compile(r"^(?:P\d{2}(?:GIS|GHS|PIB|FRR|VRR|FRZ)|PK\d{2}TB)")
_DEBT = re.compile(r"(?:TFC|SC\d*$)")

def classify_observation(symbol: str, sector: str, config: dict) -> tuple[str,str,str]:
    manual={x["symbol"]:x for x in config.get("manual_mappings",())}
    if symbol in manual:
        row=manual[symbol]; return validate_type(row["instrument_type"]),"manual_mapping",row.get("confidence","high")
    if _GOVERNMENT.search(symbol): return "government_security","ticker_heuristic","low"
    if sector in config.get("sector_rules",{}): return validate_type(config["sector_rules"][sector]),"observed_sector_rule","low"
    if symbol.endswith("ETF"): return "ETF","ticker_heuristic","low"
    if _DEBT.search(symbol): return "debt_security","ticker_heuristic","low"
    if _RIGHT.search(symbol): return "right_or_entitlement","ticker_heuristic","low"
    if sector.startswith(config.get("ordinary_equity_sector_prefix","08")):
        if symbol.endswith(("PS","CPS")): return "preference_share","ticker_heuristic","low"
        return "ordinary_equity","observed_sector_rule","low"
    return "unknown","insufficient_metadata","unknown"

def classify_intervals(source: pa.Table, config: dict) -> pa.Table:
    required={"trade_date","symbol","sector"}
    if not required.issubset(source.column_names): raise ValueError(f"missing columns: {required-set(source.column_names)}")
    grouped=defaultdict(list)
    for r in source.select(sorted(required)).to_pylist():
        typ,src,confidence=classify_observation(r["symbol"],r["sector"] or "",config)
        grouped[r["symbol"]].append((r["trade_date"],typ,src,confidence,r["sector"] or ""))
    out=[]
    for symbol, rows in sorted(grouped.items()):
        rows=sorted(set(rows)); start=0
        for i in range(1,len(rows)+1):
            if i<len(rows) and rows[i][1:]==rows[start][1:]: continue
            d0=date.fromisoformat(rows[start][0]); d1=date.fromisoformat(rows[i-1][0])
            typ,src,confidence,sector=rows[start][1:]
            out.append({"symbol":symbol,"effective_from":d0.isoformat(),"effective_to":d1.isoformat(),"instrument_type":typ,
                        "classification_source":src,"classification_confidence":confidence,"observed_sector":sector})
            start=i
    return pa.Table.from_pylist(out)

def validate_intervals(table: pa.Table) -> None:
    last={}
    for r in sorted(table.to_pylist(),key=lambda x:(x["symbol"],x["effective_from"])):
        validate_type(r["instrument_type"])
        if r["effective_from"]>r["effective_to"]: raise ValueError("reversed effective interval")
        if r["symbol"] in last and r["effective_from"]<=last[r["symbol"]]: raise ValueError("overlapping effective intervals")
        last[r["symbol"]]=r["effective_to"]
