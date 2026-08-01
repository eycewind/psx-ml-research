from __future__ import annotations

import hashlib,json,tomllib
from dataclasses import asdict,dataclass
from datetime import date
from pathlib import Path


class TargetConfigurationError(ValueError): pass

@dataclass(frozen=True)
class TargetConfig:
    feature_path:Path; feature_manifest_path:Path; daily_path:Path; c1_manifest_path:Path
    labelled_path:Path; target_manifest_path:Path; name:str; version:int; price_family:str
    horizons:tuple[int,...]; classification_horizons:tuple[int,...]; rank_horizons:tuple[int,...]
    minimum_rank_population:int; primary_horizon:int
    def canonical(self):
        d=asdict(self)
        for k,v in list(d.items()):
            if isinstance(v,Path): d[k]=str(v)
            elif isinstance(v,tuple): d[k]=list(v)
        return d
    def sha256(self): return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class FoldConfig:
    id:str; train_start:str; validation_start:str; validation_end:str

@dataclass(frozen=True)
class SplitConfig:
    assignment_path:Path; manifest_path:Path; target_report_path:Path; split_report_path:Path
    name:str; version:int; embargo_sessions:int; final_test_start:str; final_test_end:str; folds:tuple[FoldConfig,...]
    def canonical(self):
        d=asdict(self)
        for k,v in list(d.items()):
            if isinstance(v,Path): d[k]=str(v)
        return d
    def sha256(self): return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _p(repo,value):
    p=Path(value).expanduser(); return (Path(repo)/p).resolve() if not p.is_absolute() else p.resolve()

def load_target_config(path,repo)->TargetConfig:
    r=tomllib.loads(Path(path).read_text());
    if set(r)!={"input","output","targets"}: raise TargetConfigurationError("targets config requires input, output, targets")
    i,o,t=r["input"],r["output"],r["targets"]
    expected_i={"feature_path","feature_manifest_path","daily_path","c1_manifest_path"}; expected_o={"labelled_path","target_manifest_path"}
    expected_t={"name","version","price_family","horizons","classification_horizons","rank_horizons","minimum_rank_population","primary_horizon"}
    if set(i)!=expected_i or set(o)!=expected_o or set(t)!=expected_t: raise TargetConfigurationError("unknown or missing target configuration keys")
    horizons=tuple(t["horizons"]); cls=tuple(t["classification_horizons"]); ranks=tuple(t["rank_horizons"])
    if horizons!=(1,5,10,20) or len(set(horizons))!=len(horizons): raise TargetConfigurationError("target-set v1 horizons must be [1,5,10,20]")
    if not set(cls).issubset(horizons) or not set(ranks).issubset(horizons) or t["primary_horizon"] not in horizons: raise TargetConfigurationError("derived/primary horizons must belong to horizons")
    if t["price_family"]!="adjusted" or t["version"]<=0 or t["minimum_rank_population"]<=0: raise TargetConfigurationError("C4 v1 requires adjusted positive-version configuration")
    return TargetConfig(*[_p(repo,i[k]) for k in ("feature_path","feature_manifest_path","daily_path","c1_manifest_path")],
      *[_p(repo,o[k]) for k in ("labelled_path","target_manifest_path")],t["name"],t["version"],t["price_family"],horizons,cls,ranks,t["minimum_rank_population"],t["primary_horizon"])

def load_split_config(path,repo)->SplitConfig:
    r=tomllib.loads(Path(path).read_text());
    if set(r)!={"output","splits","folds"}: raise TargetConfigurationError("splits config requires output, splits, folds")
    o,s=r["output"],r["splits"]
    if set(o)!={"assignment_path","manifest_path","target_report_path","split_report_path"}: raise TargetConfigurationError("invalid split output keys")
    if set(s)!={"name","version","embargo_sessions","final_test_start","final_test_end"}: raise TargetConfigurationError("invalid split keys")
    folds=[]; ids=set()
    for f in r["folds"]:
        if set(f)!={"id","train_start","validation_start","validation_end"}: raise TargetConfigurationError("invalid fold keys")
        if f["id"] in ids: raise TargetConfigurationError("duplicate fold id")
        ids.add(f["id"])
        for k in ("train_start","validation_start","validation_end"): date.fromisoformat(f[k])
        if not f["train_start"]<f["validation_start"]<=f["validation_end"]: raise TargetConfigurationError("invalid chronological fold")
        folds.append(FoldConfig(**f))
    date.fromisoformat(s["final_test_start"]); date.fromisoformat(s["final_test_end"])
    if s["final_test_start"]>s["final_test_end"] or s["embargo_sessions"]<0 or s["version"]<=0: raise TargetConfigurationError("invalid test/embargo/version")
    return SplitConfig(*[_p(repo,o[k]) for k in ("assignment_path","manifest_path","target_report_path","split_report_path")],
      s["name"],s["version"],s["embargo_sessions"],s["final_test_start"],s["final_test_end"],tuple(folds))
