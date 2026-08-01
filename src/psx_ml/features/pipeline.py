from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .base import validate_inputs
from .config import FeatureConfig,load_feature_config
from .manifest import git_state,logical_hash,runtime_versions,sha256_file,write_json
from .quality import average_tie_percentile,lag_return,rolling_stat
from .registry import build_registry,registry_hash


PRODUCTION_DB=Path("/home/hassan/psx-stock-watcher/data/psx_watcher.db")
WATCHER_ROOT=Path("/home/hassan/psx-stock-watcher")


class OutputBoundaryError(ValueError): pass


def validate_output_boundaries(config: FeatureConfig,repo: Path) -> None:
    repo=repo.resolve(); temp=Path(tempfile.gettempdir()).resolve()
    for p in (config.feature_path,config.output_manifest_path,config.report_path):
        r=p.resolve()
        if r==PRODUCTION_DB or r==WATCHER_ROOT or WATCHER_ROOT in r.parents:
            raise OutputBoundaryError(f"C3 refuses watcher/production output: {r}")
        if repo not in r.parents and r!=repo and temp not in r.parents and r!=temp:
            raise OutputBoundaryError(f"Output must be beneath research repo or temporary directory: {r}")


def _arr(table,name): return np.asarray(table[name].to_numpy(zero_copy_only=False),dtype=np.float64)


def _safe_ratio(a,b,subtract=False):
    out=np.full(len(a),np.nan); valid=np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
    out[valid]=a[valid]/b[valid]-(1 if subtract else 0); return out


def compute_features(daily,universe,config: FeatureConfig):
    dates=np.array(daily["trade_date"].to_pylist(),dtype=object); symbols=np.array(daily["symbol"].to_pylist(),dtype=object)
    ukeys={(d,s):bool(e) for d,s,e in zip(universe["trade_date"].to_pylist(),universe["symbol"].to_pylist(),universe["eligible"].to_pylist())}
    eligible=np.array([ukeys[(d,s)] for d,s in zip(dates,symbols)],dtype=bool)
    order=np.lexsort((dates,symbols)); inv=np.empty(len(order),dtype=int); inv[order]=np.arange(len(order))
    sd,ss=dates[order],symbols[order]; se=eligible[order]
    suffix="adj" if config.price_family=="adjusted" else "raw"
    pn=lambda base: f"{base}_adj" if config.price_family=="adjusted" else base
    close,open_,high,low,volume=[_arr(daily,pn(x))[order] for x in ("close","open","high","low","volume")]
    n=len(order); features:dict[str,np.ndarray]={}
    for name in [f"ret_{w}obs_{suffix}" for w in (1,5,20)]+[f"log_ret_{w}obs_{suffix}" for w in (1,20)]: features[name]=np.full(n,np.nan)
    for name in (f"close_to_open_1obs_{suffix}",f"open_gap_1obs_{suffix}",f"close_to_mean_20obs_{suffix}",f"close_to_max_20obs_{suffix}",
                 f"log1p_volume_{suffix}",f"volume_ratio_median_20obs_{suffix}",f"turnover_1obs_{suffix}",f"turnover_median_20obs_{suffix}",
                 f"rv_20obs_{suffix}",f"true_range_1obs_{suffix}",f"atr_mean_20obs_{suffix}",f"amihud_mean_20obs_{suffix}",
                 "stale_close_run_length","unchanged_close_fraction_20obs","days_since_previous_observation","strict_high_below_low_flag","missing_volume_flag","zero_volume_flag"):
        features[name]=np.full(n,np.nan)
    starts=np.r_[0,np.flatnonzero(ss[1:]!=ss[:-1])+1,n]
    for a,b in zip(starts[:-1],starts[1:]):
        c,o,h,l,v=close[a:b],open_[a:b],high[a:b],low[a:b],volume[a:b]; m=b-a
        rets={w:lag_return(c,w) for w in (1,5,20)}
        for w,x in rets.items(): features[f"ret_{w}obs_{suffix}"][a:b]=x
        for w in (1,20): features[f"log_ret_{w}obs_{suffix}"][a:b]=lag_return(c,w,True)
        features[f"close_to_open_1obs_{suffix}"][a:b]=_safe_ratio(c,o,True)
        prev=np.r_[np.nan,c[:-1]]; features[f"open_gap_1obs_{suffix}"][a:b]=_safe_ratio(o,prev,True)
        mean20=rolling_stat(c,20,np.mean); max20=rolling_stat(c,20,np.max)
        features[f"close_to_mean_20obs_{suffix}"][a:b]=_safe_ratio(c,mean20,True)
        features[f"close_to_max_20obs_{suffix}"][a:b]=_safe_ratio(c,max20,True)
        lv=np.full(m,np.nan); validv=np.isfinite(v)&(v>=0); lv[validv]=np.log1p(v[validv]); features[f"log1p_volume_{suffix}"][a:b]=lv
        medv=rolling_stat(v,20,np.median); features[f"volume_ratio_median_20obs_{suffix}"][a:b]=_safe_ratio(v,medv)
        turnover=np.where(np.isfinite(c)&np.isfinite(v)&(c>0)&(v>=0),c*v,np.nan)
        features[f"turnover_1obs_{suffix}"][a:b]=turnover
        features[f"turnover_median_20obs_{suffix}"][a:b]=rolling_stat(turnover,20,np.median)
        lr1=lag_return(c,1,True); features[f"rv_20obs_{suffix}"][a:b]=rolling_stat(lr1,20,lambda x:np.std(x,ddof=1))
        tr=np.full(m,np.nan)
        valid=np.isfinite(h)&np.isfinite(l)&(h>=l)&np.isfinite(prev)&(prev>0)
        tr[valid]=np.maximum.reduce([h[valid]-l[valid],np.abs(h[valid]-prev[valid]),np.abs(l[valid]-prev[valid])])
        features[f"true_range_1obs_{suffix}"][a:b]=tr; features[f"atr_mean_20obs_{suffix}"][a:b]=rolling_stat(tr,20,np.mean)
        illiq=np.full(m,np.nan); ok=np.isfinite(rets[1])&np.isfinite(turnover)&(turnover>0); illiq[ok]=np.abs(rets[1][ok])/turnover[ok]
        features[f"amihud_mean_20obs_{suffix}"][a:b]=rolling_stat(illiq,20,np.mean)
        unchanged=np.zeros(m); run=np.zeros(m)
        for i in range(1,m):
            if np.isfinite(c[i]) and c[i]==c[i-1]: unchanged[i]=1; run[i]=run[i-1]+1
        features["stale_close_run_length"][a:b]=run
        features["unchanged_close_fraction_20obs"][a:b]=rolling_stat(unchanged,20,np.mean)
        gap=np.full(m,np.nan)
        if m>1: gap[1:]=(np.array(sd[a+1:b],dtype="datetime64[D]")-np.array(sd[a:b-1],dtype="datetime64[D]")).astype(int)
        features["days_since_previous_observation"][a:b]=gap
        features["strict_high_below_low_flag"][a:b]=(np.isfinite(h)&np.isfinite(l)&(h<l)).astype(float)
        features["missing_volume_flag"][a:b]=(~np.isfinite(v)).astype(float); features["zero_volume_flag"][a:b]=(v==0).astype(float)
    # Reorder symbol calculations to canonical trade_date,symbol order.
    canonical=np.lexsort((ss,sd)); cd,cs,se=sd[canonical],ss[canonical],se[canonical]
    features={k:v[canonical] for k,v in features.items()}
    # Date-isolated cross-sectional and market context features.
    for name in (f"ret_20obs_rank_{suffix}",f"turnover_rank_{suffix}",f"market_median_ret_1obs_{suffix}","eligible_symbol_count"):
        features[name]=np.full(n,np.nan)
    dst=np.r_[0,np.flatnonzero(cd[1:]!=cd[:-1])+1,n]
    populations=[]
    for a,b in zip(dst[:-1],dst[1:]):
        mask=se[a:b]; populations.append(int(mask.sum()))
        for src,outname in ((f"ret_20obs_{suffix}",f"ret_20obs_rank_{suffix}"),(f"turnover_1obs_{suffix}",f"turnover_rank_{suffix}")):
            vals=np.where(mask,features[src][a:b],np.nan); features[outname][a:b]=average_tie_percentile(vals,config.minimum_cross_section_size)
        valid=mask&np.isfinite(features[f"ret_1obs_{suffix}"][a:b])
        if valid.sum()>=config.minimum_cross_section_size:
            features[f"market_median_ret_1obs_{suffix}"][a:b][mask]=np.median(features[f"ret_1obs_{suffix}"][a:b][valid])
            features["eligible_symbol_count"][a:b][mask]=mask.sum()
    registry=build_registry(config.price_family)
    expected=[x.name for x in registry]
    if list(features)!=expected: raise RuntimeError(f"Registry/output mismatch: {set(features)^set(expected)}")
    arrays={"trade_date":pa.array(cd,type=pa.string()),"symbol":pa.array(cs,type=pa.string()),
            "point_in_time_eligible":pa.array(se),"source_observation_present":pa.array(np.ones(n,dtype=bool)),
            "listing_age_observations":pa.array(np.concatenate([np.arange(1,b-a+1) for a,b in zip(starts[:-1],starts[1:])])[canonical],type=pa.int32())}
    infinity_before=0
    for name in expected:
        x=features[name]; infinity_before+=int(np.isinf(x).sum()); x[~np.isfinite(x)]=np.nan; arrays[name]=pa.array(x,mask=np.isnan(x),type=pa.float64())
    table=pa.table(arrays)
    quality={"infinity_before_sanitation":infinity_before,"infinity_after_sanitation":0,
             "strict_high_below_low_rows":int(np.nansum(features["strict_high_below_low_flag"])),
             "missing_volume_rows":int(np.nansum(features["missing_volume_flag"])),"zero_volume_rows":int(np.nansum(features["zero_volume_flag"])),
             "cross_section_population":{"min":min(populations),"median":float(np.median(populations)),"max":max(populations)}}
    return table,registry,quality


def _write_parquet_atomic(table,path: Path) -> None:
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000,write_statistics=True)
    tmp.replace(path)


def _feature_stats(table,registry) -> dict:
    result={}; age=np.asarray(table["listing_age_observations"]); eligible=np.asarray(table["point_in_time_eligible"])
    for d in registry:
        x=np.asarray(table[d.name].to_numpy(zero_copy_only=False),dtype=float); finite=x[np.isfinite(x)]
        null=~np.isfinite(x)
        warmup=null&(age<d.minimum_observations) if d.scope=="symbol" else np.zeros(len(x),dtype=bool)
        ineligible=null&(~eligible) if d.scope in {"cross_sectional","market"} else np.zeros(len(x),dtype=bool)
        other=null&(~warmup)&(~ineligible)
        result[d.name]={"non_null":int(len(finite)),"null":int(len(x)-len(finite)),"non_null_pct":100*len(finite)/len(x),
          "warmup_null":int(warmup.sum()),"ineligible_population_null":int(ineligible.sum()),"invalid_or_insufficient_population_null":int(other.sum()),
          "p01":float(np.percentile(finite,1)) if len(finite) else None,"median":float(np.median(finite)) if len(finite) else None,
          "p99":float(np.percentile(finite,99)) if len(finite) else None}
    return result


def _write_report(manifest: dict,path: Path) -> None:
    q=manifest["quality"]; lines=["# C3 Point-in-Time Feature Report","",
      f"Feature set `{manifest['feature_set']['name']}` v{manifest['feature_set']['version']} from C1 input `{manifest['inputs']['daily']['sha256']}`.","",
      "## Coverage","",f"- Rows: {manifest['output']['rows']:,}",f"- Symbols: {manifest['output']['symbols']:,}",
      f"- Dates: {manifest['output']['date_range']['min']} through {manifest['output']['date_range']['max']}",
      f"- Features: {len(manifest['ordered_features'])}",f"- PIT eligible rows: {manifest['output']['eligible_rows']:,}","",
      "## Field and timing policy","",manifest["field_policy"],"",manifest["availability_convention"],"",
      "Adjusted prices and volume are algebraically consistent with C1 factors, but C1 did not establish complete dividend adjustment or universal adjusted-series reliability. These features must not be described as verified total returns.","",
      "## Quality","",f"- Strict `high < low` rows flagged/masked in range calculations: {q['strict_high_below_low_rows']:,}",
      f"- Stored null-volume rows: {q['missing_volume_rows']:,}",f"- Stored zero-volume rows: {q['zero_volume_rows']:,}",
      f"- Infinity values before sanitation: {q['infinity_before_sanitation']:,}",f"- Infinity values after sanitation: {q['infinity_after_sanitation']:,}",
      f"- Eligible population per date: min {q['cross_section_population']['min']}, median {q['cross_section_population']['median']:.0f}, max {q['cross_section_population']['max']}","",
      "Open or close outside high/low rows are preserved without clipping or rejection. Only strict high-below-low rows mask true-range calculations. Missing observations are never synthesized as zero-volume candles; observation-count lookbacks and calendar-day gap metadata remain distinct.","",
      "## Per-feature coverage, null reasons, and selected percentiles","",
      "`Other null` means an invalid denominator/source value or insufficient permitted cross-sectional population after warm-up and ineligible-population nulls are removed.","",
      "| Feature | Non-null | Coverage | Warm-up null | Ineligible null | Other null | p01 | Median | p99 |","|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name in manifest["ordered_features"]:
        s=manifest["feature_statistics"][name]
        fmt=lambda v:"null" if v is None else f"{v:.6g}"
        lines.append(f"| `{name}` | {s['non_null']:,} | {s['non_null_pct']:.2f}% | {s['warmup_null']:,} | {s['ineligible_population_null']:,} | {s['invalid_or_insufficient_population_null']:,} | {fmt(s['p01'])} | {fmt(s['median'])} | {fmt(s['p99'])} |")
    lines += ["","## Stale and history behavior","",
      "Stale-close run length and trailing unchanged-close fraction operate on stored observations. Newly listed and ragged histories warm up feature-by-feature; no backward fill, future interpolation, or global short-history deletion occurs. `days_since_previous_observation` reports calendar gaps while returns retain observation-count names.","",
      "## Determinism and provenance","",f"- Output file SHA-256: `{manifest['output']['file_sha256']}`",f"- Logical-content SHA-256: `{manifest['output']['logical_content_sha256']}`",
      f"- Registry SHA-256: `{manifest['feature_registry_sha256']}`",f"- Configuration SHA-256: `{manifest['configuration_sha256']}`","",
      "The logical hash excludes generation time and is computed from canonical ordered Arrow values and schema. Repeated live execution evidence is recorded in C3 delivery.","",
      "## Known limitations and next-contract guidance","",
      "These are transparent primitives, not target-selected predictors. No claims about predictive value or profitability are made. Later target/execution work must treat each row as available only after its session close and may act no earlier than the following trading session.",""]
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text("\n".join(lines)); tmp.replace(path)


def run_pipeline(config_path: Path,repo: Path) -> dict:
    repo=repo.resolve(); config=load_feature_config(config_path,repo); validate_output_boundaries(config,repo)
    daily,universe,c1=validate_inputs(config); table,registry,quality=compute_features(daily,universe,config)
    _write_parquet_atomic(table,config.feature_path)
    dates=table["trade_date"].to_pylist(); symbols=table["symbol"].to_pylist(); eligible=np.asarray(table["point_in_time_eligible"])
    manifest={"manifest_version":1,"feature_set":{"name":"psx_daily_primitives","version":1},
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":git_state(repo),
      "inputs":{"daily":{"path":str(config.daily_path),"sha256":sha256_file(config.daily_path),"rows":daily.num_rows},
                "universe":{"path":str(config.universe_path),"sha256":sha256_file(config.universe_path),"rows":universe.num_rows},
                "c1_manifest":{"path":str(config.input_manifest_path),"sha256":sha256_file(config.input_manifest_path),"maximum_trade_date":c1["maximum_source_trade_date"]}},
      "input_summary":{"rows":daily.num_rows,"symbols":len(set(symbols)),"date_range":{"min":min(dates),"max":max(dates)}},
      "output":{"path":str(config.feature_path),"rows":table.num_rows,"symbols":len(set(symbols)),"eligible_rows":int(eligible.sum()),
                "date_range":{"min":min(dates),"max":max(dates)},"file_sha256":sha256_file(config.feature_path),"logical_content_sha256":logical_hash(table)},
      "ordered_features":[x.name for x in registry],"feature_registry":[x.as_dict() for x in registry],"feature_registry_sha256":registry_hash(registry),
      "configuration":config.canonical(),"configuration_sha256":config.sha256(),
      "field_policy":f"{config.price_family} price OHLC and {config.volume_family} volume are paired consistently; raw fields are not mixed into formulas",
      "point_in_time_universe_methodology":"Exact (trade_date,symbol) join to C1 eligibility; no fill and no latest-list projection",
      "availability_convention":"Features for D use observations through D and are available only after market close on D; earliest decision is the next session",
      "window_definitions":{"return_observations":list(config.return_windows),"rolling_observations":list(config.rolling_windows)},
      "minimum_history_rules":{"global_reporting_threshold":config.minimum_history,"feature_specific":"registry minimum_observations"},
      "null_infinity_policy":"No imputation; insufficient history and invalid/nonpositive denominators are null; infinities are sanitized to null",
      "float_precision":config.float_precision,"packages":runtime_versions(),"quality":quality,"feature_statistics":_feature_stats(table,registry)}
    write_json(manifest,config.output_manifest_path); _write_report(manifest,config.report_path)
    return manifest


def main() -> None:
    p=argparse.ArgumentParser(description="Generate trailing-only PSX daily features from C1 artifacts")
    p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd())
    a=p.parse_args(); m=run_pipeline(a.config,a.repo)
    print(f"C3 complete: {m['output']['rows']} rows, {len(m['ordered_features'])} features, logical {m['output']['logical_content_sha256']}")
    print(f"Manifest: {m['configuration']['output_manifest_path']}")


if __name__=="__main__": main()
