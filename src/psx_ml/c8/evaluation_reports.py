from __future__ import annotations
from collections import defaultdict
import json
import numpy as np

def importance_stability(rows):
    grouped=defaultdict(list)
    keys=("stage","horizon","target_family","feature_variant","model_name","feature")
    for r in rows: grouped[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,part in sorted(grouped.items()):
        gain=np.asarray([r["gain_importance"] for r in part],float)
        out.append({**dict(zip(keys,key)),"fold_count":len(part),"mean_gain":float(np.mean(gain)),"gain_std":float(np.std(gain)),"positive_gain_folds":int(np.sum(gain>0)),"mean_split":float(np.mean([r["split_importance"] for r in part]))})
    return out

def model_report(result,path):
    lines=["# C8 Model Evaluation Report","","These are leakage-safe predictive validation diagnostics, not signals, backtests, portfolios, or profitability results.","","## Fold stability","","| Stage | Horizon | Target | Features | Model | Subset | Mean daily IC | Fold std | Worst | Best | Positive folds | Mean D10-D1 | Positive spread folds |","|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in result["aggregate_metrics"]:
        def f(x): return "—" if x is None else f"{x:.6g}"
        lines.append(f"| {r['stage']} | {r['horizon']} | `{r['target_family']}` | `{r['feature_variant']}` | `{r['model_name']}` | `{r['comparison_subset']}` | {f(r['mean_daily_ic'])} | {f(r['daily_ic_fold_std'])} | {f(r['worst_fold_ic'])} | {f(r['best_fold_ic'])} | {r['positive_ic_folds']} | {f(r['mean_d10_d1'])} | {r['positive_spread_folds']} |")
    lines += ["","## Interpretation guardrails","","Natural-coverage sector results are always paired with strict-five-peer matched results. No result is called better solely because coverage or target variance changed. The 2026 final holdout remained locked."]
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
    candidates=[]
    for r in result["aggregate_metrics"]:
        if r["model_name"]=="lightgbm_cpu" and r["comparison_subset"]=="natural_coverage" and r["target_family"]!="absolute":
            promising=(r["mean_daily_ic"] is not None and r["mean_daily_ic"]>0 and r["positive_ic_folds"]>=2 and r["positive_spread_folds"]>=2 and r["worst_fold_ic"] is not None and r["worst_fold_ic"]>0)
            candidates.append((promising,r))
    selected=[r for ok,r in candidates if ok]; conclusion="At least one LightGBM relative-target configuration passed the preliminary fold-sign guardrails; bootstrap, matched-subset, sector dominance, and importance stability still govern the final interpretation." if selected else "No LightGBM relative-target configuration passed the preliminary multi-fold sign and spread guardrails. C8 has not demonstrated a stable practical improvement."
    lines=["# C8 Delivery Report","",f"Generation commit: `{manifest['code']['commit']}`; dirty: **{manifest['code']['dirty']}**; holdout accessed: **{manifest['holdout_accessed']}**.","",f"Prediction rows: **{manifest['evaluation_counts']['prediction_rows']}**; fitted model/task/fold combinations: **{manifest['evaluation_counts']['fit_count']}**.","","## Conclusion","",conclusion,"","No trade rules, fees, portfolio logic, backtest, or profitability claim is part of C8.","","## Verification","",json.dumps(manifest.get("verification",{}),indent=2,sort_keys=True)]
    path.write_text("\n".join(lines)+"\n")
