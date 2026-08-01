from __future__ import annotations
import hashlib,json,tomllib
from dataclasses import asdict,dataclass
from pathlib import Path

class ModelConfigurationError(ValueError): pass

@dataclass(frozen=True)
class ModelConfig:
    labelled_path:Path; split_path:Path; c4_manifest_path:Path; c3_manifest_path:Path; c2_manifest_path:Path
    predictions_path:Path; coefficients_path:Path; manifest_path:Path; model_report_path:Path; coefficient_report_path:Path
    name:str; version:int; seed:int; ridge_alphas:tuple[float,...]; logistic_cs:tuple[float,...]; logistic_max_iter:int; bootstrap_replicates:int
    features:tuple[str,...]; regression_targets:tuple[str,...]; classification_targets:tuple[str,...]
    def canonical(self):
        d=asdict(self)
        for k,v in list(d.items()):
            if isinstance(v,Path): d[k]=str(v)
            elif isinstance(v,tuple): d[k]=list(v)
        return d
    def sha256(self): return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _p(repo,x):
    p=Path(x).expanduser(); return (Path(repo)/p).resolve() if not p.is_absolute() else p.resolve()

def load_config(path,repo):
    r=tomllib.loads(Path(path).read_text())
    if set(r)!={"input","output","model_set"}: raise ModelConfigurationError("model config requires input/output/model_set")
    i,o,m=r["input"],r["output"],r["model_set"]
    ik=("labelled_path","split_path","c4_manifest_path","c3_manifest_path","c2_manifest_path")
    ok=("predictions_path","coefficients_path","manifest_path","model_report_path","coefficient_report_path")
    mk=("name","version","seed","ridge_alphas","logistic_cs","logistic_max_iter","bootstrap_replicates","features","regression_targets","classification_targets")
    if set(i)!=set(ik) or set(o)!=set(ok) or set(m)!=set(mk): raise ModelConfigurationError("unknown or missing model config keys")
    if m["version"]<=0 or m["seed"]<0 or m["logistic_max_iter"]<=0 or m["bootstrap_replicates"]<=0: raise ModelConfigurationError("invalid positive model settings")
    for key in ("ridge_alphas","logistic_cs"):
        if not m[key] or len(set(m[key]))!=len(m[key]) or any(x<=0 for x in m[key]): raise ModelConfigurationError(f"invalid {key}")
    if len(m["features"])!=len(set(m["features"])): raise ModelConfigurationError("duplicate features")
    forbidden=("fwd_","up_","target_","entry_","split_","trade_date","symbol")
    if any(f.startswith(forbidden) or f in {"trade_date","symbol","fold_id"} for f in m["features"]): raise ModelConfigurationError("forbidden predictor in allowlist")
    return ModelConfig(*[_p(repo,i[k]) for k in ik],*[_p(repo,o[k]) for k in ok],m["name"],m["version"],m["seed"],
      tuple(m["ridge_alphas"]),tuple(m["logistic_cs"]),m["logistic_max_iter"],m["bootstrap_replicates"],tuple(m["features"]),tuple(m["regression_targets"]),tuple(m["classification_targets"]))
