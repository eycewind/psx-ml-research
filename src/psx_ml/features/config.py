from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path


class FeatureConfigurationError(ValueError): pass


@dataclass(frozen=True)
class FeatureConfig:
    daily_path: Path
    universe_path: Path
    input_manifest_path: Path
    feature_path: Path
    output_manifest_path: Path
    report_path: Path
    price_family: str
    volume_family: str
    return_windows: tuple[int,...]
    rolling_windows: tuple[int,...]
    minimum_history: int
    stale_run_threshold: int
    minimum_cross_section_size: int
    engine: str
    float_precision: str

    def canonical(self) -> dict:
        d=asdict(self)
        for k,v in list(d.items()):
            if isinstance(v,Path): d[k]=str(v)
        d["return_windows"]=list(self.return_windows); d["rolling_windows"]=list(self.rolling_windows)
        return d

    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def _resolve(repo: Path, value: str) -> Path:
    p=Path(value).expanduser(); return (repo/p).resolve() if not p.is_absolute() else p.resolve()


def load_feature_config(path: str|Path, repo: str|Path) -> FeatureConfig:
    repo=Path(repo).resolve(); raw=tomllib.loads(Path(path).read_text())
    expected={"input":{"daily_path","universe_path","manifest_path"},
      "output":{"feature_path","manifest_path","report_path"},"fields":{"price_family","volume_family"},
      "windows":{"returns","rolling"},"quality":{"minimum_history","stale_run_threshold","minimum_cross_section_size"},
      "execution":{"engine","float_precision"}}
    if set(raw)!=set(expected): raise FeatureConfigurationError(f"Required sections: {sorted(expected)}")
    for section,keys in expected.items():
        if set(raw[section])!=keys: raise FeatureConfigurationError(f"Invalid keys in [{section}]: {sorted(set(raw[section])^keys)}")
    fields=raw["fields"]
    if fields["price_family"] not in {"raw","adjusted"} or fields["volume_family"] not in {"raw","adjusted"}:
        raise FeatureConfigurationError("field families must be raw or adjusted")
    if fields["price_family"] != fields["volume_family"]:
        raise FeatureConfigurationError("price and volume families must match for adjustment-consistent turnover")
    rw=tuple(raw["windows"]["returns"]); roll=tuple(raw["windows"]["rolling"])
    for name,values in (("returns",rw),("rolling",roll)):
        if not values or any(isinstance(x,bool) or not isinstance(x,int) or x<=0 for x in values) or len(set(values))!=len(values):
            raise FeatureConfigurationError(f"{name} windows must be unique positive integers")
    if rw!=(1,5,20) or roll!=(5,20,60):
        raise FeatureConfigurationError("C3 feature-set v1 requires returns=[1,5,20] and rolling=[5,20,60]")
    q=raw["quality"]
    if any(isinstance(q[k],bool) or not isinstance(q[k],int) or q[k]<=0 for k in q):
        raise FeatureConfigurationError("quality thresholds must be positive integers")
    ex=raw["execution"]
    if ex!={"engine":"cpu","float_precision":"float64"}:
        raise FeatureConfigurationError("C3 supports only CPU float64 execution")
    i,o=raw["input"],raw["output"]
    outputs=[_resolve(repo,o[k]) for k in ("feature_path","manifest_path","report_path")]
    if len(set(outputs))!=3: raise FeatureConfigurationError("output paths must be distinct")
    return FeatureConfig(_resolve(repo,i["daily_path"]),_resolve(repo,i["universe_path"]),_resolve(repo,i["manifest_path"]),
      *outputs,fields["price_family"],fields["volume_family"],rw,roll,q["minimum_history"],q["stale_run_threshold"],q["minimum_cross_section_size"],ex["engine"],ex["float_precision"])
