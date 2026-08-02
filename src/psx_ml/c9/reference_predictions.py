from __future__ import annotations
import argparse,json,tomllib
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from psx_ml.c8.supplemental import _fit,_save
from psx_ml.features.manifest import git_state,sha256_file,write_json
from .inputs import validate_inputs,load_config

def run(repo:Path,config_path:Path,allow_final_holdout=False):
    if allow_final_holdout: raise RuntimeError("C9 final 2026 holdout is locked")
    repo=repo.resolve(); cfg=load_config(config_path); paths,c8,provenance=validate_inputs(repo,cfg,False); raw=tomllib.loads((repo/"config/c8.example.toml").read_text()); ecfg=raw["evaluation"]
    relative=pq.read_table(paths["relative_targets_path"],columns=["trade_date","symbol","fwd_market_relative_rank_5s","fwd_market_relative_ret_5s"])
    if str(pc.max(relative["trade_date"]).as_py())>="2026-01-01": raise RuntimeError("C9 reference input crossed holdout boundary")
    keys=list(zip(relative["trade_date"].to_pylist(),relative["symbol"].to_pylist())); source=pq.read_table(paths["feature_targets_path"]); source_map={(r["trade_date"],r["symbol"]):r for r in source.to_pylist()}; features=c8["feature_definitions"]["variants"]["A_c7_only"]
    x=np.asarray([[np.nan if source_map[k].get(f) is None else source_map[k][f] for f in features] for k in keys],float); y=np.asarray(relative["fwd_market_relative_rank_5s"].to_pylist(),float); outcome=np.asarray(relative["fwd_market_relative_ret_5s"].to_pylist(),float); dates=np.asarray([k[0] for k in keys],object); symbols=np.asarray([k[1] for k in keys],object)
    split_rows=pq.read_table(repo/"data/processed/datasets/temporal_split_assignments.parquet",columns=["trade_date","symbol","fold_id","split_role"]).to_pylist(); index={k:i for i,k in enumerate(keys)}; folds=sorted({r["fold_id"] for r in split_rows}); roles={f:np.full(len(keys),"not_in_fold",object) for f in folds}
    for r in split_rows:
        i=index.get((r["trade_date"],r["symbol"]));
        if i is not None: roles[r["fold_id"]][i]=r["split_role"]
    predictions=[]; diagnostics=[]; models=[]
    for fold in folds:
        train=(roles[fold]=="train")&np.isfinite(y); valid=(roles[fold]=="validation")&np.isfinite(y)&np.isfinite(outcome)
        for name in ("lightgbm_cpu","xgboost_gpu"):
            model,p,stop,boundary,device,fit=_fit("regression",name,x,y,train,valid,dates,ecfg); meta={"task_type":"rank","target_name":"fwd_market_relative_rank_5s","horizon":5,"feature_variant":"A_c7_only","model_name":name,"fold_id":fold}; models.append({**meta,**_save(model,name,f"c9_reference_A_5_{fold}_{name}",repo/"artifacts/c9/models")}); diagnostics.append({**meta,"device":device,"best_iteration":stop[0],"best_inner_score":stop[1],"first_iteration_score":stop[2],"last_evaluated_iteration":stop[3],"inner_boundary":boundary,"fit_seconds":fit,"train_rows":int(train.sum()),"validation_rows":int(valid.sum())})
            predictions += [{**meta,"trade_date":d,"symbol":s,"target":float(a),"outcome":float(o),"prediction":float(q),"prediction_probability":None} for d,s,a,o,q in zip(dates[valid],symbols[valid],y[valid],outcome[valid],p)]
    table=pa.Table.from_pylist(predictions); path=repo/"artifacts/c9/reference_rank_predictions.parquet"; path.parent.mkdir(parents=True,exist_ok=True); pq.write_table(table,path,compression="zstd")
    manifest={"manifest_version":1,"code":git_state(repo),"holdout_accessed":False,"c8_prediction_provenance":provenance,"target":"fwd_market_relative_rank_5s","feature_variant":"A_c7_only","models":models,"diagnostics":diagnostics,"prediction_rows":table.num_rows,"prediction_path":str(path),"prediction_sha256":sha256_file(path)}; write_json(manifest,repo/"artifacts/c9/reference_rank_manifest.json"); print(f"C9 reference: {len(models)} fits, {table.num_rows} predictions, holdout=false")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--config",type=Path,required=True); p.add_argument("--allow-final-holdout",action="store_true"); a=p.parse_args(); run(a.repo,a.config,a.allow_final_holdout)
if __name__=="__main__": main()
