from __future__ import annotations

import numpy as np

def exchange_calendar(trade_dates) -> tuple[np.ndarray,dict[str,int]]:
    dates=np.array(sorted(set(trade_dates)),dtype=object)
    return dates,{d:i for i,d in enumerate(dates)}

def dense_row_lookup(dates,symbols,calendar,date_index):
    unique_symbols=np.array(sorted(set(symbols)),dtype=object); sym_index={s:i for i,s in enumerate(unique_symbols)}
    lookup=np.full((len(calendar),len(unique_symbols)),-1,dtype=np.int32)
    for row,(d,s) in enumerate(zip(dates,symbols)):
        di,si=date_index[d],sym_index[s]
        if lookup[di,si]>=0: raise ValueError(f"duplicate daily key {(d,s)}")
        lookup[di,si]=row
    return unique_symbols,sym_index,lookup
