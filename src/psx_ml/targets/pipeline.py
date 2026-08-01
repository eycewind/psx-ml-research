from __future__ import annotations

import argparse,json,tempfile
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.features.manifest import git_state,logical_hash,runtime_versions,sha256_file,write_json
from psx_ml.splits.walk_forward import generate_assignments
from .config import load_split_config,load_target_config
from .forward_returns import generate_targets
from .registry import build_registry,registry_hash
from .validation import validate_inputs

WATCHER=Path("/home/hassan/psx-stock-watcher"); DB=WATCHER/"data/psx_watcher.db"
class OutputBoundaryError(ValueError): pass

def _bound(paths,repo):
    repo=Path(repo).resolve(); temp=Path(tempfile.gettempdir()).resolve()
    for p in paths:
        r=p.resolve()
        if r==DB or r==WATCHER or WATCHER in r.parents: raise OutputBoundaryError(f"refusing production/watcher output: {r}")
        if repo not in r.parents and r!=repo and temp not in r.parents and r!=temp: raise OutputBoundaryError(f"output outside research/temp boundary: {r}")

def _write(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)

def _percentiles(table,name):
    x=np.asarray(table[name].to_numpy(zero_copy_only=False),dtype=float); x=x[np.isfinite(x)]
    return {f"p{p:02d}":float(np.percentile(x,p)) for p in (1,5,25,50,75,95,99)} if len(x) else {}

def _examples(targets,daily,horizon=20,count=3):
    prices={(d,s):(o,c) for d,s,o,c in zip(daily["trade_date"].to_pylist(),daily["symbol"].to_pylist(),daily["open_adj"].to_pylist(),daily["close_adj"].to_pylist())}
    out=[]
    for r in targets.select(["trade_date","symbol","entry_date",f"target_end_date_{horizon}s",f"fwd_open_to_close_ret_{horizon}s_adj"]).to_pylist():
        if r[f"fwd_open_to_close_ret_{horizon}s_adj"] is None: continue
        ep=prices[(r["entry_date"],r["symbol"])][0]; xp=prices[(r[f"target_end_date_{horizon}s"],r["symbol"])][1]
        out.append({**r,"entry_price":ep,"exit_price":xp,"recalculated_return":xp/ep-1})
        if len(out)>=count: break
    return out

def _target_report(m,path):
    lines=["# C4 Target Report","",f"Target set `{m['target_set']['name']}` v{m['target_set']['version']}; {m['output']['rows']:,} rows, {m['output']['symbols']:,} symbols, {m['output']['date_range']['min']} through {m['output']['date_range']['max']}.","",
      "## Timing and warning","","Features through close D enter only at adjusted open on the exact next exchange session. Exits use adjusted close exactly H sessions after entry. Targets are gross returns without costs and must not be described as profitable trades.","",
      "## Coverage, null reasons, percentiles, and class balance",""]
    for name,x in m["target_metrics"].items(): lines.append(f"- `{name}`: {json.dumps(x,sort_keys=True)}")
    lines += ["","Return percentiles:",""]
    for name,x in m["return_percentiles"].items(): lines.append(f"- `{name}`: {json.dumps(x,sort_keys=True)}")
    lines += ["","## PIT rank populations","",f"Ranks use only same-feature-date eligible rows with valid targets, deterministic average ties, and minimum population {m['target_configuration']['minimum_rank_population']}.","",
      "## Hand-reconciled examples","","| Symbol | Feature D | Entry | Entry price | End | Exit price | Stored return | Recalculated |","|---|---|---|---:|---|---:|---:|---:|"]
    for x in m["hand_reconciled_examples"]: lines.append(f"| {x['symbol']} | {x['trade_date']} | {x['entry_date']} | {x['entry_price']:.6g} | {x['target_end_date_20s']} | {x['exit_price']:.6g} | {x['fwd_open_to_close_ret_20s_adj']:.8f} | {x['recalculated_return']:.8f} |")
    lines += ["","Missing symbol observations are not forward-filled; missing/nonpositive prices and insufficient calendar horizons remain null with explicit reasons. Open/close outside high-low does not invalidate an otherwise valid target. No infinities remain.",""]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines))

def _split_report(m,path):
    lines=["# C4 Temporal Split Report","",f"Split set `{m['split_set']['name']}` v{m['split_set']['version']}. All symbols on a feature date share a role; no random row split exists.","",
      f"Final untouched holdout: {m['split_configuration']['final_test_start']} through {m['split_configuration']['final_test_end']}. Primary purge horizon: {m['target_configuration']['primary_horizon']} sessions. Embargo: {m['split_configuration']['embargo_sessions']} exchange sessions.","", "## Fold evidence",""]
    for f in m["split_configuration"]["folds"]:
        c=m["fold_counts"][f["id"]]; lines += [f"### {f['id']}","",f"Train begins {f['train_start']}; validation {f['validation_start']} through {f['validation_end']}.","",f"Counts: `{json.dumps(c,sort_keys=True)}`",""]
    lines += ["Every included training row satisfies `target_end_date_20s < validation_start`; overlap violations are zero. Rows at the boundary that violate this condition are explicitly `purged`. Configured post-validation session dates are `embargoed` unless they belong to the higher-priority untouched final test window.",""]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines))

def run_pipeline(target_config_path,split_config_path,repo):
    repo=Path(repo).resolve(); tc=load_target_config(target_config_path,repo); sc=load_split_config(split_config_path,repo)
    _bound((tc.labelled_path,tc.target_manifest_path,sc.assignment_path,sc.manifest_path,sc.target_report_path,sc.split_report_path),repo)
    features,daily,fm,c1=validate_inputs(tc); targets,metrics,calendar=generate_targets(features,daily,tc)
    registry=build_registry(tc); expected=[x.name for x in registry]
    actual=[x for x in targets.column_names if x.startswith("fwd_open_to_close_ret_") or x.startswith("up_") or x.startswith("fwd_ret_")]
    if actual!=expected: raise RuntimeError(f"target registry/output mismatch: {actual} vs {expected}")
    assignments,fold_counts=generate_assignments(targets,calendar,sc,tc.primary_horizon)
    _write(targets,tc.labelled_path); _write(assignments,sc.assignment_path)
    dates=targets["trade_date"].to_pylist(); symbols=targets["symbol"].to_pylist()
    manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":git_state(repo),
      "target_set":{"name":tc.name,"version":tc.version},"split_set":{"name":sc.name,"version":sc.version},
      "inputs":{"c3_features":{"path":str(tc.feature_path),"sha256":sha256_file(tc.feature_path),"manifest_sha256":sha256_file(tc.feature_manifest_path)},
                "c1_daily":{"path":str(tc.daily_path),"sha256":sha256_file(tc.daily_path),"manifest_sha256":sha256_file(tc.c1_manifest_path)}},
      "input_identity":{"c3_logical_hash":fm["output"]["logical_content_sha256"],"maximum_trade_date":c1["maximum_source_trade_date"]},
      "target_configuration":tc.canonical(),"target_configuration_sha256":tc.sha256(),"split_configuration":sc.canonical(),"split_configuration_sha256":sc.sha256(),
      "target_registry":[x.as_dict() for x in registry],"target_registry_sha256":registry_hash(registry),
      "entry_exit_convention":"after-close D; adjusted open exact next exchange session; adjusted close H exchange sessions after entry",
      "classification_definition":"1 iff gross_return > 0; 0 iff <= 0; null iff regression null",
      "cross_sectional_method":"same-date PIT eligible valid targets; average ties; ascending percentile",
      "purge_embargo_policy":"actual primary target_end_date must be before validation start; configured post-validation exchange-session embargo",
      "target_metrics":metrics,"return_percentiles":{f"fwd_open_to_close_ret_{h}s_adj":_percentiles(targets,f"fwd_open_to_close_ret_{h}s_adj") for h in tc.horizons},
      "hand_reconciled_examples":_examples(targets,daily),"fold_counts":fold_counts,
      "output":{"rows":targets.num_rows,"symbols":len(set(symbols)),"pit_eligible":int(np.asarray(targets["point_in_time_eligible"]).sum()),"date_range":{"min":min(dates),"max":max(dates)},
                "labelled":{"path":str(tc.labelled_path),"file_sha256":sha256_file(tc.labelled_path),"logical_sha256":logical_hash(targets)},
                "splits":{"path":str(sc.assignment_path),"rows":assignments.num_rows,"file_sha256":sha256_file(sc.assignment_path),"logical_sha256":logical_hash(assignments)}},
      "packages":runtime_versions()}
    write_json(manifest,tc.target_manifest_path); write_json(manifest,sc.manifest_path); _target_report(manifest,sc.target_report_path); _split_report(manifest,sc.split_report_path)
    return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--targets-config",type=Path,required=True); p.add_argument("--splits-config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd())
    a=p.parse_args(); m=run_pipeline(a.targets_config,a.splits_config,a.repo)
    print(f"C4 complete: {m['output']['rows']} target rows; {m['output']['splits']['rows']} split rows")
    print(f"Target logical: {m['output']['labelled']['logical_sha256']}"); print(f"Split logical: {m['output']['splits']['logical_sha256']}")

if __name__=="__main__": main()
