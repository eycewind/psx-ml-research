from __future__ import annotations

from collections import Counter,defaultdict
import math
import numpy as np


def sector_coverage_audit(rows,horizons,relative,minimum_peers):
    """Return row reasons, reason summary, and sector coverage by horizon."""
    member_counts=Counter((r["trade_date"],r.get("sector")) for r in rows if r.get("sector") is not None)
    valid_counts={}
    for h in horizons:
        c=Counter()
        for r in rows:
            value=r.get(f"fwd_open_to_close_ret_{h}s_adj")
            if r.get("sector") is not None and value is not None and math.isfinite(float(value)): c[(r["trade_date"],r["sector"])]+=1
        valid_counts[h]=c
    row_audit=[]
    for i,r in enumerate(rows):
        sector=r.get("sector")
        for h in horizons:
            own=r.get(f"fwd_open_to_close_ret_{h}s_adj"); own_valid=own is not None and math.isfinite(float(own))
            eligible_peers=0 if sector is None else member_counts[(r["trade_date"],sector)]-1
            valid_peers=0 if sector is None else valid_counts[h][(r["trade_date"],sector)]-int(own_valid)
            result=relative[f"fwd_sector_relative_ret_{h}s"][i]
            if not own_valid: reason="stock_target_missing"
            elif sector is None: reason="missing_sector"
            elif eligible_peers<minimum_peers: reason="insufficient_sector_peers"
            elif valid_peers<minimum_peers: reason="peer_targets_insufficient"
            elif result is None: reason="other"
            else: reason="valid"
            row_audit.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"sector":sector,"horizon":h,"eligible_peer_count":eligible_peers,"valid_target_peer_count":valid_peers,"invalid_reason":reason})
    summary=[]
    grouped=defaultdict(list)
    for r in row_audit: grouped[(r["horizon"],r["invalid_reason"])].append(r)
    for (h,reason),part in sorted(grouped.items()):
        summary.append({"horizon":h,"invalid_reason":reason,"row_count":len(part),"symbol_count":len({x["symbol"] for x in part}),"date_count":len({x["trade_date"] for x in part}),"sector_count":len({x["sector"] for x in part if x["sector"] is not None})})
    coverage=[]
    grouped=defaultdict(list)
    for r in row_audit:
        if r["sector"] is not None: grouped[(r["horizon"],r["sector"])].append(r)
    for (h,sector),part in sorted(grouped.items()):
        peers=np.asarray([r["valid_target_peer_count"] for r in part],float); valid=sum(r["invalid_reason"]=="valid" for r in part)
        coverage.append({"horizon":h,"sector":sector,"eligible_rows":len(part),"valid_sector_relative_rows":valid,"coverage_fraction":valid/len(part),"median_peer_count":float(np.median(peers)),"minimum_peer_count":int(np.min(peers))})
    return row_audit,summary,coverage
