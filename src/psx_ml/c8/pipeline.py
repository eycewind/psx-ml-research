from __future__ import annotations

import argparse,json,subprocess,tomllib
from datetime import datetime,timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from psx_ml.features.manifest import git_state,logical_hash,sha256_file,write_json
from .relative_targets import build_relative_target_columns

CANONICAL="pit_liquid_ordinary_equity_v1"

def _inside(repo:Path,value:str)->Path:
    p=(repo/value).resolve()
    if p!=repo and repo not in p.parents: raise ValueError(f"path outside repository: {p}")
    return p

def run(config_path:Path,repo:Path,allow_final_holdout=False):
    if allow_final_holdout: raise RuntimeError("C8 final holdout access is locked")
    repo=repo.resolve(); raw=tomllib.loads(config_path.read_text()); code=git_state(repo)
    branch=subprocess.run(["git","-C",str(repo),"branch","--show-current"],check=True,capture_output=True,text=True).stdout.strip()
    code["branch"]=branch
    if branch!="feature/c8-market-relative-targets-and-context": raise RuntimeError("C8 must run on its required feature branch")
    paths={k:_inside(repo,v) for k,v in raw["input"].items()}
    universe=pq.read_table(paths["universe_path"],columns=["trade_date","symbol","universe_name","eligible","instrument_type"])
    mask=pc.and_(pc.equal(universe["universe_name"],CANONICAL),pc.and_(universe["eligible"],pc.equal(universe["instrument_type"],"ordinary_equity")))
    eligible={(r["trade_date"],r["symbol"]) for r in universe.filter(mask).to_pylist()}
    splits=pq.read_table(paths["split_path"],columns=["trade_date","split_role"])
    development_dates={r["trade_date"] for r in splits.to_pylist() if r["split_role"] in {"train","validation"}}
    master=pq.read_table(paths["security_master_path"],columns=["symbol","sector"]).to_pylist(); sectors={r["symbol"]:r["sector"] for r in master if r["sector"]}
    horizons=tuple(raw["target"]["horizons"]); cols=["trade_date","symbol"]+[f"fwd_open_to_close_ret_{h}s_adj" for h in horizons]
    source=pq.read_table(paths["targets_path"],columns=cols)
    rows=[]
    for r in source.to_pylist():
        if (r["trade_date"],r["symbol"]) in eligible and r["trade_date"] in development_dates: rows.append({**r,"sector":sectors.get(r["symbol"])})
    derived=build_relative_target_columns(rows,horizons,int(raw["target"]["minimum_sector_peers"]))
    output_rows=[]
    for i,r in enumerate(rows): output_rows.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"sector":r["sector"],**{k:v[i] for k,v in derived.items()}})
    table=pa.Table.from_pylist(output_rows); out=_inside(repo,raw["output"]["relative_targets_path"]); out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(".parquet.tmp"); pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(out)
    counts={"rows":table.num_rows,"dates":len({r["trade_date"] for r in rows}),"symbols":len({r["symbol"] for r in rows}),"missing_sector_rows":sum(r["sector"] is None for r in rows)}
    for h in horizons:
        counts[f"valid_market_relative_{h}s"]=sum(x is not None for x in derived[f"fwd_market_relative_ret_{h}s"])
        counts[f"valid_sector_relative_{h}s"]=sum(x is not None for x in derived[f"fwd_sector_relative_ret_{h}s"])
    manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":code,"holdout_accessed":False,"canonical_universe":CANONICAL,"sector_provenance":"2026-08-01 security-master historical backcast","benchmark_definitions":{"market":"same-date eligible ordinary-equity leave-one-out median","sector":"same-date same-sector eligible ordinary-equity leave-one-out median","sector_minimum_policy":raw["target"]["sector_minimum_policy"],"minimum_sector_peers":raw["target"]["minimum_sector_peers"]},"target_definitions":list(derived),"counts":counts,"inputs":{k:{"path":str(v),"sha256":sha256_file(v)} for k,v in paths.items()},"outputs":{"relative_targets":{"path":str(out),"file_sha256":sha256_file(out),"logical_sha256":logical_hash(table)}}}
    report=_inside(repo,raw["output"]["target_report_path"]); report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("# C8 Relative Target Report\n\nFinal holdout accessed: **false**.\n\nMarket and sector benchmarks are same-date leave-one-out medians. Sector eligibility requires five valid peers after exclusion. Sector labels retain the 2026-08-01 historical-backcast limitation.\n\n```json\n"+json.dumps(counts,indent=2,sort_keys=True)+"\n```\n")
    write_json(manifest,_inside(repo,raw["output"]["manifest_path"])); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--allow-final-holdout",action="store_true"); a=p.parse_args()
    result=run(a.config,a.repo,a.allow_final_holdout); print(f"C8 targets: {result['counts']['rows']} rows; holdout={result['holdout_accessed']}")

if __name__=="__main__": main()
