from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,tomllib

class TreeConfigError(ValueError): pass
@dataclass(frozen=True)
class TreeConfig:
    repo:Path; raw:dict
    def path(self,section,key):
        p=Path(self.raw[section][key]); return (self.repo/p).resolve() if not p.is_absolute() else p.resolve()
    @property
    def model(self): return self.raw["model_set"]
    def canonical(self): return self.raw
    def sha256(self): return hashlib.sha256(json.dumps(self.raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def load_config(path,repo):
    raw=tomllib.loads(Path(path).read_text()); repo=Path(repo).resolve()
    if set(raw)!={"input","output","model_set"}: raise TreeConfigError("tree config requires input/output/model_set")
    features=raw["model_set"]["features"]
    forbidden=("fwd_","up_","target_","entry_","split_","trade_date","symbol","instrument","universe")
    if len(features)!=len(set(features)) or any(x.startswith(forbidden) or x in {"fold_id","prediction"} for x in features): raise TreeConfigError("forbidden or duplicate predictor")
    if raw["model_set"]["canonical_universe"]!="pit_liquid_ordinary_equity_v1": raise TreeConfigError("C7 canonical universe is fixed")
    c=TreeConfig(repo,raw)
    for p in raw["output"].values():
        q=c.path("output",next(k for k,v in raw["output"].items() if v==p))
        if not q.is_relative_to(repo): raise TreeConfigError("output outside repository")
    return c
