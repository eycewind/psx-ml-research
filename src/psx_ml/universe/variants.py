from __future__ import annotations
import pyarrow as pa

def membership_rows(source: pa.Table, pit: pa.Table, intervals: pa.Table, variants: dict) -> pa.Table:
    pit_map={(r["trade_date"],r["symbol"]):bool(r["eligible"]) for r in pit.select(["trade_date","symbol","eligible"]).to_pylist()}
    by_symbol={}
    for r in intervals.to_pylist(): by_symbol.setdefault(r["symbol"],[]).append(r)
    out=[]
    for r in source.select(["trade_date","symbol"]).to_pylist():
        key=(r["trade_date"],r["symbol"]); typ="unknown"; classification_found=False
        for c in by_symbol.get(r["symbol"],()):
            if c["effective_from"]<=r["trade_date"]<=c["effective_to"]: typ=c["instrument_type"]; classification_found=True; break
        liquid=pit_map.get(key,False)
        for name,rule in variants.items():
            permitted=rule.get("instrument_types"); eligible=liquid and classification_found and (permitted is None or typ in permitted)
            reason=None if eligible else ("liquidity_exclusion" if not liquid else ("history_exclusion" if not classification_found else "classification_exclusion"))
            out.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"universe_name":name,"eligible":eligible,
                        "instrument_type":typ,"exclusion_reason":reason})
    return pa.Table.from_pylist(out)
