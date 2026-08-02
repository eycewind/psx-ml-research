from __future__ import annotations
import argparse,json,subprocess,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from psx_ml.features.manifest import git_state,logical_hash,write_json
from .inputs import load_config,validate_inputs,inside,sha256
from .policies import percentile_ranks,select,schedule_dates,apply_liquidity,sector_constraint
from .metrics import candidate_outcomes,date_ranking_metrics
from .turnover import turnover_metrics,retention,candidate_lifetimes
from .persistence import rank_persistence,rank_changes
from .agreement import average_rank_ensemble,model_agreement,intersection_union
from .concentration import concentration
from .bootstrap import moving_block_bootstrap,empirical_p_value
from .baselines import rank_baseline,random_distribution

def _write(table,path):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); pq.write_table(table,tmp,compression="zstd",use_dictionary=False,row_group_size=20000); tmp.replace(path)
def _mean(rows,key):
    x=[r[key] for r in rows if r.get(key) is not None]; return float(np.mean(x)) if x else None
def _aggregate(selected,universe,cfg,meta):
    outcomes=candidate_outcomes(selected,universe); turnover=turnover_metrics(selected); values=[r["mean_actual_market_relative_return"] for r in outcomes]; spreads=[r["spread_versus_unselected"] for r in outcomes if r["spread_versus_unselected"] is not None]; precision=[r["top_decile_hit_rate"] for r in outcomes]
    block=cfg["bootstrap"]; folds=[]
    for fold in sorted({r["fold_id"] for r in selected}):
        dates={r["trade_date"] for r in selected if r["fold_id"]==fold}; part=[r for r in outcomes if r["trade_date"] in dates]; folds.append({"fold_id":fold,"date_count":len(part),"mean_outcome":_mean(part,"mean_actual_market_relative_return"),"mean_spread":_mean(part,"spread_versus_unselected"),"precision":_mean(part,"top_decile_hit_rate")})
    return {**meta,"selection_rows":len(selected),"date_count":len(outcomes),"symbol_count":len({r["symbol"] for r in selected}),"sector_count":len({r.get("sector") for r in selected if r.get("sector")}),"mean_candidate_count":_mean(outcomes,"candidate_count"),"mean_outcome":_mean(outcomes,"mean_actual_market_relative_return"),"median_date_outcome":float(np.median(values)) if values else None,"positive_date_fraction":float(np.mean(np.asarray(values)>0)) if values else None,"mean_spread":_mean(outcomes,"spread_versus_unselected"),"precision":_mean(outcomes,"top_decile_hit_rate"),"outcome_ci":moving_block_bootstrap(values,block["block_length_sessions"],block["iterations"],cfg["study"]["seed"]),"spread_ci":moving_block_bootstrap(spreads,block["block_length_sessions"],block["iterations"],cfg["study"]["seed"]+1),"precision_ci":moving_block_bootstrap(precision,block["block_length_sessions"],block["iterations"],cfg["study"]["seed"]+2),"folds":folds,"fold_std":float(np.std([r["mean_outcome"] for r in folds])) if folds else None,"mean_turnover":_mean(turnover,"gross_candidate_turnover"),"median_turnover":_mean(turnover,"jaccard"),**concentration(selected)}
def _filter_schedule(rows,schedule):
    dates=set(schedule_dates([r["trade_date"] for r in rows],schedule)); return [r for r in rows if r["trade_date"] in dates]
def _policy(rows,kind,value,schedule,liquidity,sector):
    eligible=apply_liquidity(rows,liquidity); scheduled=_filter_schedule(eligible,schedule); chosen=select(scheduled,kind,value); constrained,skipped=sector_constraint(chosen,sector); return constrained,skipped,eligible
def _turnover_ranks(rows):
    grouped=defaultdict(list); out={}
    for r in rows:
        if r.get("turnover_median_20obs_adj") is not None: grouped[r["trade_date"]].append(r)
    for d,part in grouped.items():
        ordered=sorted(part,key=lambda r:(r["turnover_median_20obs_adj"],r["symbol"])); n=len(ordered)
        for i,r in enumerate(ordered): out[(d,r["symbol"])]=i/(n-1) if n>1 else .5
    return out
def _prepare(paths,manifest):
    rank=[r for r in pq.read_table(paths["c8_rank_predictions_path"]).to_pylist() if r["task_type"]=="rank"]
    features={(r["trade_date"],r["symbol"]):r for r in pq.read_table(paths["feature_targets_path"],columns=["trade_date","symbol","turnover_median_20obs_adj","turnover_rank_adj","ret_20obs_rank_adj"]).to_pylist()}
    relative={(r["trade_date"],r["symbol"]):r for r in pq.read_table(paths["relative_targets_path"],columns=["trade_date","symbol","sector"]).to_pylist()}
    reg=[r for r in pq.read_table(paths["c8_regression_predictions_path"]).to_pylist() if r["horizon"]==5 and r["target_family"]=="market_relative" and r["feature_variant"]=="B_market_context" and r["model_name"]=="lightgbm_cpu" and r["comparison_subset_natural"]]
    regmap={(r["fold_id"],r["trade_date"],r["symbol"]):r for r in reg}; turnover=_turnover_ranks(features.values()); out=[]
    provenance=manifest["supplemental_evaluation"]["generation_code"]["commit"]
    for r in rank:
        key=(r["trade_date"],r["symbol"]); f=features.get(key,{}); q=relative.get(key,{}); g=regmap.get((r["fold_id"],*key),{})
        out.append({"trade_date":r["trade_date"],"symbol":r["symbol"],"fold_id":r["fold_id"],"horizon":r["horizon"],"target_family":"market_relative_rank","feature_variant":r["feature_variant"],"model_name":r["model_name"],"prediction":r["prediction"],"actual_rank_target":r["target"],"actual_market_relative_return":r["outcome"],"sector":q.get("sector"),"turnover_median_20obs_adj":f.get("turnover_median_20obs_adj"),"turnover_percentile_rank":turnover.get(key),"momentum_rank":f.get("ret_20obs_rank_adj"),"liquidity_rank":f.get("turnover_rank_adj"),"market_trend_regime":g.get("market_trend_regime"),"market_volatility_regime":g.get("market_volatility_regime"),"market_breadth_regime":g.get("market_breadth_regime"),"market_dispersion_regime":g.get("market_dispersion_regime"),"prediction_provenance":provenance})
    return out
def run(config_path:Path,repo:Path,allow_final_holdout=False):
    started=time.perf_counter(); cfg=load_config(config_path); paths,c8,input_provenance=validate_inputs(repo,cfg,allow_final_holdout); rows=_prepare(paths,c8)
    canonical=[r for r in rows if r["horizon"]==5 and r["feature_variant"]=="B_market_context" and r["model_name"] in cfg["study"]["models"]]; ranked=[]
    for key in sorted({(r["model_name"],r["fold_id"]) for r in canonical}): ranked += percentile_ranks([r for r in canonical if (r["model_name"],r["fold_id"])==key])
    lgb=[r for r in ranked if r["model_name"]=="lightgbm_cpu"]; xgb=[r for r in ranked if r["model_name"]=="xgboost_gpu"]; ensemble=average_rank_ensemble(lgb,xgb); model_sets={"E0_lightgbm":lgb,"E1_xgboost":xgb,"E2_average_rank":ensemble}
    selection_metrics=[]; selection_rows=[]; skipped=[]
    definitions=[("percentile",x,f"top_{int(x*100)}pct") for x in cfg["selection"]["percentiles"]]+[("fixed",x,f"top_{x}") for x in cfg["selection"]["fixed_counts"]]
    for model,model_rows in model_sets.items():
      for kind,value,name in definitions:
       for schedule in cfg["selection"]["rebalance_schedules"]:
        for liquidity in cfg["selection"]["liquidity_screens"]:
         for sector in ("S0","S1","S2"):
          chosen,skip,eligible=_policy(model_rows,kind,value,schedule,liquidity,sector); meta={"policy_id":"|".join(map(str,(model,name,schedule,liquidity,sector))),"model":model,"selection_policy":name,"selection_kind":kind,"threshold":value,"rebalance_schedule":schedule,"liquidity_screen":liquidity,"sector_constraint":sector}
          selection_metrics.append(_aggregate(chosen,eligible,cfg,meta)); skipped += [{**meta,**r} for r in skip]
          selection_rows += [{**meta,**r} for r in chosen]
    for model,model_rows in model_sets.items():
        chosen,skip,eligible=_policy(model_rows,"percentile",1.,"weekly_first_session","L0","S3"); meta={"policy_id":f"{model}|sector_neutral","model":model,"selection_policy":"sector_neutral","selection_kind":"sector_neutral","threshold":None,"rebalance_schedule":"weekly_first_session","liquidity_screen":"L0","sector_constraint":"S3"}; selection_metrics.append(_aggregate(chosen,eligible,cfg,meta)); skipped += [{**meta,**r} for r in skip]; selection_rows += [{**meta,**r} for r in chosen]
    p1,_skip,p1u=_policy(lgb,"percentile",.10,"weekly_first_session","L0","S1"); lt=select(_filter_schedule(apply_liquidity(lgb,"L1"),"weekly_first_session"),"percentile",.10); xt=select(_filter_schedule(apply_liquidity(xgb,"L1"),"weekly_first_session"),"percentile",.10); consensus,_=intersection_union(lt,xt); p2,_=sector_constraint(consensus,"S1"); p3,_skip,p3u=_policy(ensemble,"percentile",.05,"non_overlapping_5_session","L2","S2")
    candidates={"P1_broad_canonical":(p1,p1u),"P2_conservative_consensus":(p2,apply_liquidity(lgb,"L1")),"P3_high_conviction":(p3,p3u)}; policy_metrics=[_aggregate(v[0],v[1],cfg,{"policy_id":k}) for k,v in candidates.items()]
    agreement=model_agreement(lgb,xgb); ranking=date_ranking_metrics(lgb); persistence=rank_persistence(lgb); rank_change=rank_changes(lgb); retention_rows=[]; lifetime_rows=[]; turnover_rows=[]
    for k,(chosen,_) in candidates.items(): retention_rows += [{"policy_id":k,**r} for r in retention(chosen)]; lifetime_rows += [{"policy_id":k,**r} for r in candidate_lifetimes(chosen)]; turnover_rows += [{"policy_id":k,**r} for r in turnover_metrics(chosen)]
    baselines=[]; p1_counts=Counter(r["trade_date"] for r in p1); random=random_distribution(p1u,p1_counts,cfg["baseline"]["random_repetitions"],cfg["baseline"]["seed"]); observed=policy_metrics[0]["mean_outcome"]
    baselines.append({"baseline":"random_same_count","policy_id":"P1_broad_canonical","repetitions":len(random),"mean":float(np.mean(random)),"std":float(np.std(random)),"p05":float(np.quantile(random,.05)),"p95":float(np.quantile(random,.95)),"empirical_p_value":empirical_p_value(observed,random)})
    for field,name in (("momentum_rank","relative_momentum"),("liquidity_rank","liquidity_rank")):
        b=rank_baseline(p1u,field,name); chosen,_skip,eligible=_policy(b,"percentile",.10,"weekly_first_session","L0","S1"); baselines.append(_aggregate(chosen,eligible,cfg,{"baseline":name,"policy_id":"P1_broad_canonical"}))
    base_lookup={(r["fold_id"],r["trade_date"],r["symbol"]):r for r in p1u}
    stored_baselines=(
        (paths["c7_predictions_path"],[("target_name","=","fwd_open_to_close_ret_5s_adj"),("model_name","=","lightgbm_cpu")],"c7_absolute_return_model"),
        (paths["c8_regression_predictions_path"],[("horizon","=",5),("target_family","=","market_relative"),("feature_variant","=","B_market_context"),("model_name","=","lightgbm_cpu")],"c8_market_relative_regression"),
    )
    for path,filters,name in stored_baselines:
        stored=pq.read_table(path,columns=["fold_id","trade_date","symbol","prediction"],filters=filters).to_pylist(); joined=[]
        for r in stored:
            base=base_lookup.get((r["fold_id"],r["trade_date"],r["symbol"]))
            if base is not None: joined.append({**base,"stored_model_prediction":r["prediction"]})
        b=rank_baseline(joined,"stored_model_prediction",name); chosen,_skip,eligible=_policy(b,"percentile",.10,"weekly_first_session","L0","S1"); baselines.append(_aggregate(chosen,eligible,cfg,{"baseline":name,"policy_id":"P1_broad_canonical"}))
    regimes=[]
    for dim in ("market_trend_regime","market_volatility_regime","market_breadth_regime","market_dispersion_regime"):
      for value in sorted({r.get(dim) for r in p1 if r.get(dim)}):
        chosen=[r for r in p1 if r.get(dim)==value]; dates={r["trade_date"] for r in chosen}; universe=[r for r in p1u if r["trade_date"] in dates]; regimes.append(_aggregate(chosen,universe,cfg,{"policy_id":"P1_broad_canonical","regime_dimension":dim,"regime_value":value}))
    decision=[]
    for r in policy_metrics:
        fold_positive=all((f["mean_outcome"] or 0)>0 for f in r["folds"]); ci_positive=(r["outcome_ci"]["lower_95"] or -1)>0; decision.append({"policy_id":r["policy_id"],"positive_all_folds":fold_positive,"positive_ci":ci_positive,"passes_core_gate":fold_positive and ci_positive})
    passing=[r["policy_id"] for r in decision if r["passes_core_gate"]]; selected_primary=passing[0] if passing else None; selected_conservative=passing[1] if len(passing)>1 else None; status="ACCEPT" if len(passing)>=2 else ("ACCEPT WITH LIMITATIONS" if passing else "REJECT")
    processed=inside(repo,cfg["output"]["processed_root"]); artifacts=inside(repo,cfg["output"]["artifact_root"]); reports=inside(repo,cfg["output"]["report_root"])
    tables={"candidate_selections":pa.Table.from_pylist(selection_rows),"candidate_outcomes":pa.Table.from_pylist([{"policy_id":k,**r} for k,v in candidates.items() for r in candidate_outcomes(v[0],v[1])]),"turnover_metrics":pa.Table.from_pylist(turnover_rows),"model_agreement":pa.Table.from_pylist(agreement),"regime_metrics":pa.Table.from_pylist(regimes),"concentration_metrics":pa.Table.from_pylist([{**{k:r[k] for k in ("policy_id","model","selection_policy","rebalance_schedule","liquidity_screen","sector_constraint")},**{k:r[k] for k in concentration([]) if k in r}} for r in selection_metrics]),"baseline_metrics":pa.Table.from_pylist(baselines)}
    outputs={}
    for name,table in tables.items(): path=processed/f"{name}.parquet"; _write(table,path); outputs[name]={"path":str(path),"rows":table.num_rows,"file_sha256":sha256(path),"logical_sha256":logical_hash(table)}
    structured={"selection_metrics":pa.Table.from_pylist(selection_metrics),"policy_metrics":pa.Table.from_pylist(policy_metrics),"bootstrap_metrics":pa.Table.from_pylist([{"policy_id":r["policy_id"],"metric":"outcome",**r["outcome_ci"]} for r in selection_metrics])}
    for name,table in structured.items(): path=artifacts/f"{name}.parquet"; _write(table,path); outputs[name]={"path":str(path),"rows":table.num_rows,"file_sha256":sha256(path),"logical_sha256":logical_hash(table)}
    viewer={"manifest_version":1,"holdout_accessed":False,"selection_metrics":selection_metrics,"policy_metrics":policy_metrics,"ranking_metrics":ranking,"model_agreement":agreement,"persistence":persistence,"rank_change":rank_change,"retention":retention_rows,"baselines":baselines,"regimes":regimes,"policy_decision":decision}; viewer_path=artifacts/"viewer_summary.json"; write_json(viewer,viewer_path); outputs["viewer_summary"]={"path":str(viewer_path),"file_sha256":sha256(viewer_path)}
    code=git_state(repo); code["branch"]=subprocess.run(["git","-C",str(repo),"branch","--show-current"],capture_output=True,text=True,check=True).stdout.strip(); manifest={"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"code":code,"holdout_accessed":False,"input_provenance":input_provenance,"c8_manifest_sha256":sha256(paths["c8_manifest_path"]),"models":cfg["study"]["models"],"target":cfg["study"]["canonical_target"],"feature_sets":{"canonical":cfg["study"]["canonical_features"],"reference":cfg["study"]["reference_features"]},"folds":sorted({r["fold_id"] for r in canonical}),"definitions":{"selection":cfg["selection"],"ensemble":{"E0":"LightGBM","E1":"XGBoost","E2":"0.5 rank + 0.5 rank","E3":"intersection"},"bootstrap":cfg["bootstrap"],"baseline":cfg["baseline"]},"counts":{"enriched_prediction_rows":len(rows),"canonical_prediction_rows":len(canonical),"selection_metric_rows":len(selection_metrics),"selection_rows":len(selection_rows),"dates":len({r["trade_date"] for r in canonical}),"symbols":len({r["symbol"] for r in canonical}),"sectors":len({r.get("sector") for r in canonical if r.get("sector")})},"ranking_metrics":ranking,"persistence":persistence,"rank_change":rank_change,"model_agreement_summary":{k:_mean(agreement,k) for k in ("rank_correlation","top_5_overlap","top_10_overlap","top_20_overlap","top_decile_overlap","bottom_decile_overlap")},"selected_primary_policy":selected_primary,"selected_conservative_policy":selected_conservative,"decision_status":status,"policy_decision":decision,"outputs":outputs,"runtime_seconds":time.perf_counter()-started,"limitations":["C8 trend/volatility/breadth/dispersion regimes retain the accepted quantile labels low/medium/high.","Candidate outcomes are predictive diagnostics, not portfolio returns or profitability."]}
    reports.mkdir(parents=True,exist_ok=True); _reports(reports,manifest,selection_metrics,policy_metrics,agreement,turnover_rows,baselines); write_json(manifest,reports/"C9_MANIFEST.json"); return manifest
def _reports(root,m,selection,policies,agreement,turnover,baselines):
    def table(rows,cols): return "\n".join(["| "+" | ".join(cols)+" |","|"+"|".join(["---"]*len(cols))+"|"]+["| "+" | ".join(str(r.get(c,"—")) for c in cols)+" |" for r in rows])
    cols=["policy_id","mean_outcome","mean_spread","precision","positive_date_fraction","fold_std","mean_turnover"]
    (root/"C9_SELECTION_REPORT.md").write_text("# C9 Candidate Selection Report\n\nPredictive candidate outcomes only; no portfolio accounting or profitability claim.\n\n"+table(selection,cols)+"\n")
    (root/"C9_ROBUSTNESS_REPORT.md").write_text("# C9 Robustness Report\n\nAll folds, thresholds, schedules, liquidity screens and sector caps retain explicit counts. C8 regime labels are preserved as accepted quantile labels.\n\n"+table(policies,cols)+"\n")
    (root/"C9_TURNOVER_REPORT.md").write_text("# C9 Turnover and Persistence Report\n\nTurnover is diagnostic; costs belong to C10.\n\n"+table(turnover[:100],["policy_id","trade_date","candidate_count","retained","entries","exits","jaccard","gross_candidate_turnover"])+"\n")
    (root/"C9_MODEL_AGREEMENT_REPORT.md").write_text("# C9 Model Agreement Report\n\n"+table(agreement[:100],["trade_date","rank_correlation","top_5_overlap","top_10_overlap","top_20_overlap","top_decile_overlap"])+"\n")
    (root/"C9_BASELINE_REPORT.md").write_text("# C9 Baseline Report\n\nRandom selection preserves same-date candidate counts. Momentum and liquidity use point-in-time ranks.\n\n"+table(baselines,list(baselines[0]))+"\n")
    (root/"C9_POLICY_DECISION.md").write_text(f"# C9 Policy Decision\n\nStatus: **{m['decision_status']}**\n\nPrimary: `{m['selected_primary_policy']}`\n\nConservative: `{m['selected_conservative_policy']}`\n\nNo C10 policy is justified unless every frozen robustness gate is met. The 2026 holdout remains locked.\n")
    (root/"C9_DELIVERY.md").write_text(f"# C9 Delivery Report\n\nStatus: **{m['decision_status']}**\n\nGeneration commit: `{m['code']['commit']}`; dirty: **{m['code']['dirty']}**; holdout accessed: **false**.\n\nC9 evaluates candidate-selection robustness only. It does not include costs, portfolio accounting, Sharpe, drawdown, live signals or a profitability claim.\n")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--allow-final-holdout",action="store_true"); a=p.parse_args(); m=run(a.config,a.repo,a.allow_final_holdout); print(f"C9 {m['decision_status']}: {m['counts']['selection_metric_rows']} policy comparisons; holdout=false")
if __name__=="__main__": main()
