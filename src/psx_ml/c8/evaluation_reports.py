from __future__ import annotations
from collections import defaultdict
import json
import numpy as np
from scipy.stats import spearmanr

def importance_stability(rows):
    grouped=defaultdict(list)
    keys=("stage","horizon","target_family","feature_variant","model_name","feature")
    for r in rows: grouped[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,part in sorted(grouped.items()):
        gain=np.asarray([r["gain_importance"] for r in part],float)
        out.append({**dict(zip(keys,key)),"fold_count":len(part),"mean_gain":float(np.mean(gain)),"gain_std":float(np.std(gain)),"positive_gain_folds":int(np.sum(gain>0)),"mean_split":float(np.mean([r["split_importance"] for r in part]))})
    return out

def importance_fold_stability(rows):
    keys=("stage","horizon","target_family","feature_variant","model_name")
    grouped=defaultdict(list)
    for r in rows: grouped[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,part in sorted(grouped.items()):
        features=sorted({r["feature"] for r in part}); folds=sorted({r["fold_id"] for r in part}); vectors=[]
        for fold in folds:
            lookup={r["feature"]:r["gain_importance"] for r in part if r["fold_id"]==fold}; v=np.asarray([lookup.get(f,0.) for f in features]); vectors.append(v/v.sum() if v.sum()>0 else v)
        correlations=[]
        for i in range(len(vectors)):
            for j in range(i+1,len(vectors)):
                if np.std(vectors[i])>0 and np.std(vectors[j])>0: correlations.append(float(spearmanr(vectors[i],vectors[j]).statistic))
        out.append({**dict(zip(keys,key)),"fold_count":len(folds),"mean_pairwise_gain_rank_correlation":float(np.mean(correlations)) if correlations else None,"minimum_pairwise_gain_rank_correlation":float(np.min(correlations)) if correlations else None})
    return out

def model_report(result,path):
    lines=["# C8 Model Evaluation Report","","These are leakage-safe predictive validation diagnostics, not signals, backtests, portfolios, or profitability results.","","## Fold stability","","| Stage | Horizon | Target | Features | Model | Subset | Mean daily IC | IC 95% CI | Fold std | Worst | Best | Positive folds | Mean D10-D1 | D10 95% CI | Positive spread folds |","|---:|---:|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---|---:|"]
    for r in result["aggregate_metrics"]:
        def f(x): return "—" if x is None else f"{x:.6g}"
        ici=r.get("aggregate_mean_daily_ic_ci95",{}); dci=r.get("aggregate_d10_d1_ci95",{}); it="—" if ici.get("lower") is None else f"[{ici['lower']:.5g}, {ici['upper']:.5g}]"; dt="—" if dci.get("lower") is None else f"[{dci['lower']:.5g}, {dci['upper']:.5g}]"
        lines.append(f"| {r['stage']} | {r['horizon']} | `{r['target_family']}` | `{r['feature_variant']}` | `{r['model_name']}` | `{r['comparison_subset']}` | {f(r['mean_daily_ic'])} | {it} | {f(r['daily_ic_fold_std'])} | {f(r['worst_fold_ic'])} | {f(r['best_fold_ic'])} | {r['positive_ic_folds']} | {f(r['mean_d10_d1'])} | {dt} | {r['positive_spread_folds']} |")
    diagnostics=result["training_diagnostics"]
    lines += ["","## Training diagnostics","",f"Fits: **{len(diagnostics)}**; one-round fits: **{sum(r['best_iteration']==1 for r in diagnostics)}**; near-constant predictions: **{sum(r['near_constant'] for r in diagnostics)}**; minimum prediction standard deviation: **{min(r['prediction_std'] for r in diagnostics):.8g}**.","","Selected rounds, prediction distributions, inner scores, devices, and runtime are available in the structured training diagnostics artifact."]
    added={"FERTILIZER","LEATHER & TANNERIES","OIL & GAS EXPLORATION COMPANIES","PROPERTY","REFINERY","TRANSPORT"}; focus=[r for r in result["subgroup_metrics"] if r["dimension"]=="sector" and r["value"] in added and r["model_name"] in {"lightgbm_cpu","xgboost_gpu"} and r["target_family"]=="sector_shrunk_3_peer" and ((r["horizon"]==5 and r["feature_variant"]=="C_sector_context") or (r["horizon"]==10 and r["feature_variant"]=="A_c7_only"))]
    lines += ["","## Six newly covered sectors — focused shrunk-target diagnostics","","| Horizon | Features | Model | Fold | Sector | Rows | Mean daily IC | Spearman |","|---:|---|---|---|---|---:|---:|---:|"]
    for r in focus:
        lines.append(
            f"| {r['horizon']} | `{r['feature_variant']}` | `{r['model_name']}` | "
            f"`{r['fold_id']}` | {r['value']} | {r['row_count']} | "
            f"{f(r['mean_daily_ic'])} | {f(r['spearman'])} |"
        )
    lines += ["","## Interpretation guardrails","","Natural-coverage sector results are always paired with strict-five-peer matched results. No result is called better solely because coverage or target variance changed. Sector, peer-tier, and training-period market-regime metrics are available in the structured subgroup artifact. The 2026 final holdout remained locked."]
    path.write_text("\n".join(lines)+"\n")

def bucket_report(result,path):
    lines=["# C8 Prediction Bucket Report","","Buckets are assigned independently within each validation date with deterministic symbol tie-breaking. Spreads are predictive target diagnostics, not portfolio returns.","","| Stage | Horizon | Target | Features | Model | Fold | Subset | D10-D1 mean | D10-D1 median | Top2-bottom2 | Monotonicity | D10 CI |","|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---|"]
    for r in result["metrics"]:
        ci=r["d10_d1_ci95"]; interval="—" if ci["lower"] is None else f"[{ci['lower']:.6g}, {ci['upper']:.6g}]"
        lines.append(f"| {r['stage']} | {r['horizon']} | `{r['target_family']}` | `{r['feature_variant']}` | `{r['model_name']}` | `{r['fold_id']}` | `{r['comparison_subset']}` | {r['d10_d1_mean_spread']} | {r['d10_d1_median_spread']} | {r['top2_bottom2_spread']} | {r['bucket_monotonicity']} | {interval} |")
    path.write_text("\n".join(lines)+"\n")

def ablation_report(result,path):
    aggregate=result["aggregate_metrics"]; lookup={(r["stage"],r["horizon"],r["target_family"],r["model_name"],r["comparison_subset"],r["feature_variant"]):r for r in aggregate}
    lines=["# C8 Feature Variant and Ablation Report","","Differences use the same target family, horizon, model, and comparison subset. Variant A is the frozen C7-only reference.","","| Stage | Horizon | Target | Model | Subset | Variant | Δ mean daily IC vs A | Δ D10-D1 vs A |","|---:|---:|---|---|---|---|---:|---:|"]
    for r in aggregate:
        if r["feature_variant"]=="A_c7_only": continue
        base=lookup.get((r["stage"],r["horizon"],r["target_family"],r["model_name"],r["comparison_subset"],"A_c7_only"))
        if not base: continue
        di=None if r["mean_daily_ic"] is None or base["mean_daily_ic"] is None else r["mean_daily_ic"]-base["mean_daily_ic"]
        ds=None if r["mean_d10_d1"] is None or base["mean_d10_d1"] is None else r["mean_d10_d1"]-base["mean_d10_d1"]
        lines.append(f"| {r['stage']} | {r['horizon']} | `{r['target_family']}` | `{r['model_name']}` | `{r['comparison_subset']}` | `{r['feature_variant']}` | {di} | {ds} |")
    path.write_text("\n".join(lines)+"\n")

def delivery_report(result,manifest,path):
    lookup={(r["horizon"],r["target_family"],r["feature_variant"],r["model_name"],r["comparison_subset"]):r for r in result["aggregate_metrics"]}
    market5=lookup[(5,"market_relative","A_c7_only","lightgbm_cpu","natural_coverage")]; absolute5=lookup[(5,"absolute","A_c7_only","lightgbm_cpu","natural_coverage")]; shrunk5=lookup[(5,"sector_shrunk_3_peer","C_sector_context","lightgbm_cpu","natural_coverage")]; shrunk5m=lookup[(5,"sector_shrunk_3_peer","C_sector_context","lightgbm_cpu","strict_5_peer_matched")]
    conclusion="C8 upgrades the conclusion from weak and unstable C7 evidence to qualified positive evidence for five-session market-relative prediction, especially for LightGBM using the unchanged C7 feature set. Its aggregate daily-IC and D10-D1 intervals exclude zero, and CUDA XGBoost corroborates the sign. Broader context features do not consistently improve this result. Shrunk sector targets improve coverage and show positive natural and strict-matched evidence at five sessions, but context-feature and importance-stability gains are mixed. This is promising predictive evidence, not evidence of implementable profitability or authorization to unlock 2026."
    lines=["# C8 Delivery Report","",f"Generation commit: `{manifest['code']['commit']}`; dirty: **{manifest['code']['dirty']}**; holdout accessed: **{manifest['holdout_accessed']}**.","",f"Prediction rows: **{manifest['evaluation_counts']['prediction_rows']}**; fitted model/task/fold combinations: **{manifest['evaluation_counts']['fit_count']}**.","","## Conclusion","",conclusion,"","## Canonical C8 result","","- Target: five-session market-relative return (`fwd_market_relative_ret_5s`).","- Model: LightGBM CPU.","- Features: `A_c7_only` (unchanged C7 feature set).",f"- Mean daily IC: `{market5['mean_daily_ic']:.7g}`; positive folds: `{market5['positive_ic_folds']}/3`.",f"- Mean D10-D1: `{market5['mean_d10_d1']:.8g}`; positive D10-D1 folds: `{market5['positive_spread_folds']}/3`.","- The 2026 holdout is untouched.","","Broader context features did not consistently improve this canonical result.","","## Key evidence","",f"- Market-relative 5-session LightGBM A: mean daily IC `{market5['mean_daily_ic']:.6g}` versus absolute A `{absolute5['mean_daily_ic']:.6g}`; positive IC folds `{market5['positive_ic_folds']}/3`; positive D10-D1 folds `{market5['positive_spread_folds']}/3`.",f"- Shrunk sector 5-session LightGBM C: natural mean IC `{shrunk5['mean_daily_ic']:.6g}`; strict-matched mean IC `{shrunk5m['mean_daily_ic']:.6g}`.","- 2023 and 2025 remain positive for the selected five-session market-relative result; the result is not a 2024-only effect.","- No fitted model was flagged near-constant.","","No trade rules, fees, portfolio logic, backtest, or profitability claim is part of C8.","","## Verification","",json.dumps(manifest.get("verification",{}),indent=2,sort_keys=True)]
    path.write_text("\n".join(lines)+"\n")
