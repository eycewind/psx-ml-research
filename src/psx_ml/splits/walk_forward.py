from __future__ import annotations

from collections import Counter

import numpy as np
import pyarrow as pa

def generate_assignments(targets,calendar,config,primary_horizon:int):
    dates=np.array(targets["trade_date"].to_pylist(),dtype=object); symbols=np.array(targets["symbol"].to_pylist(),dtype=object)
    end=np.array(targets[f"target_end_date_{primary_horizon}s"].to_pylist(),dtype=object); n=len(dates)
    out={"trade_date":[],"symbol":[],"fold_id":[],"split_role":[],"included":[],"exclusion_reason":[]}; counts={}
    cal=list(calendar)
    for fold in config.folds:
        after=[d for d in cal if d>fold.validation_end]; embargo=set(after[:config.embargo_sessions])
        roles=np.empty(n,dtype=object); reasons=np.empty(n,dtype=object); reasons[:]=None
        for i,d in enumerate(dates):
            if config.final_test_start<=d<=config.final_test_end: role="test"
            elif fold.validation_start<=d<=fold.validation_end: role="validation"
            elif fold.train_start<=d<fold.validation_start:
                if end[i] is None or end[i]>=fold.validation_start: role="purged"; reasons[i]="target_interval_overlaps_validation"
                else: role="train"
            elif d in embargo: role="embargoed"; reasons[i]="post_validation_embargo"
            else: role="not_in_fold"; reasons[i]="outside_fold_windows"
            roles[i]=role
        included=np.isin(roles,["train","validation","test"])
        out["trade_date"].extend(dates); out["symbol"].extend(symbols); out["fold_id"].extend([fold.id]*n); out["split_role"].extend(roles)
        out["included"].extend(included); out["exclusion_reason"].extend(reasons)
        counter=Counter(roles); counts[fold.id]={k:int(counter.get(k,0)) for k in ("train","validation","test","purged","embargoed","not_in_fold")}
        train_end_dates=[end[i] for i in range(n) if roles[i]=="train" and end[i] is not None]
        counts[fold.id]["maximum_training_target_end_date"]=max(train_end_dates) if train_end_dates else None
        counts[fold.id]["overlap_violations"]=sum(x>=fold.validation_start for x in train_end_dates)
        counts[fold.id]["embargo_dates"]=sorted(embargo-set(d for d in embargo if config.final_test_start<=d<=config.final_test_end))
    return pa.table({"trade_date":pa.array(out["trade_date"],type=pa.string()),"symbol":pa.array(out["symbol"],type=pa.string()),
      "fold_id":pa.array(out["fold_id"],type=pa.string()),"split_role":pa.array(out["split_role"],type=pa.string()),
      "included":pa.array(out["included"],type=pa.bool_()),"exclusion_reason":pa.array(out["exclusion_reason"],type=pa.string())}),counts
