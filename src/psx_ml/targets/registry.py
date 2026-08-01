from __future__ import annotations

import hashlib,json
from dataclasses import asdict,dataclass

@dataclass(frozen=True)
class TargetDefinition:
    name:str; version:int; kind:str; horizon_sessions:int; formula:str; entry_convention:str
    exit_convention:str; availability:str; null_reasons:tuple[str,...]; price_family:str="adjusted"
    def as_dict(self):
        d=asdict(self); d["null_reasons"]=list(self.null_reasons); return d

REASONS=("missing_next_session_observation","missing_entry_open","nonpositive_entry_open",
 "missing_exit_observation","missing_exit_close","nonpositive_exit_close","insufficient_future_sessions")

def build_registry(config):
    entry="adjusted open on exact next global exchange session after feature date"
    out=[]
    for h in config.horizons:
        out.append(TargetDefinition(f"fwd_open_to_close_ret_{h}s_adj",1,"regression",h,"exit_close/entry_open-1",entry,
          f"adjusted close exactly {h} exchange sessions after entry",f"known only after target_end_date_{h}s",REASONS))
    for h in config.classification_horizons:
        out.append(TargetDefinition(f"up_{h}s",1,"classification",h,"1 when regression>0 else 0; null follows regression",entry,
          f"derived from fwd_open_to_close_ret_{h}s_adj",f"known only after target_end_date_{h}s",REASONS))
    for h in config.rank_horizons:
        out.append(TargetDefinition(f"fwd_ret_{h}s_rank",1,"cross_sectional",h,"same-date eligible valid average-tie percentile rank",entry,
          f"derived from fwd_open_to_close_ret_{h}s_adj",f"known only after target_end_date_{h}s",REASONS))
    return out

def registry_hash(registry):
    return hashlib.sha256(json.dumps([x.as_dict() for x in registry],sort_keys=True,separators=(",",":")).encode()).hexdigest()
