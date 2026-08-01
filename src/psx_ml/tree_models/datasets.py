from __future__ import annotations
from collections import defaultdict
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

def canonical_mask(labelled,universe,name):
    eligible={(r["trade_date"],r["symbol"]) for r in universe.to_pylist() if r["universe_name"]==name and r["eligible"] and r["instrument_type"]=="ordinary_equity"}
    return np.array([(d,s) in eligible for d,s in zip(labelled["trade_date"].to_pylist(),labelled["symbol"].to_pylist())],bool)

def fold_roles(labelled,splits):
    keys=list(zip(labelled["trade_date"].to_pylist(),labelled["symbol"].to_pylist())); out={}
    for fold in sorted(set(splits["fold_id"].to_pylist())):
        part=splits.filter(pc.equal(splits["fold_id"],fold)); pkeys=list(zip(part["trade_date"].to_pylist(),part["symbol"].to_pylist()))
        if pkeys!=keys: raise ValueError(f"split keys do not reconcile: {fold}")
        out[fold]=np.array(part["split_role"].to_pylist(),object)
    return out

def matrix(table,features): return np.column_stack([np.asarray(table[f].to_numpy(zero_copy_only=False),float) for f in features])

def inner_chronological(dates,train_mask,fraction):
    unique=sorted(set(dates[train_mask])); cut=max(1,int(len(unique)*(1-fraction))); boundary=unique[cut]
    inner_train=train_mask & (dates<boundary); inner_valid=train_mask & (dates>=boundary)
    if not inner_train.any() or not inner_valid.any(): raise ValueError("empty inner chronological split")
    return inner_train,inner_valid,boundary
