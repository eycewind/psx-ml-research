from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import pyarrow.parquet as pq
from psx_ml.features.manifest import git_state,sha256_file,write_json
from .supplemental_metrics import _interval
from .evaluation_metrics import aggregate_folds,attach_aggregate_bootstrap
from .evaluation_reports import ablation_report,bucket_report,delivery_report,importance_fold_stability,importance_stability,model_report

def _rows(path): return pq.read_table(path).to_pylist()

def refresh(repo:Path,cpu_result:str,gpu_result:str):
    repo=repo.resolve(); manifest_path=repo/"artifacts/reports/C8_MANIFEST.json"; manifest=json.loads(manifest_path.read_text())
    outputs=manifest["outputs"]; metrics=_rows(outputs["model_metrics"]["path"]); daily=_rows(outputs["daily_ic"]["path"]); buckets=_rows(outputs["bucket_outcomes"]["path"]); subgroup=_rows(outputs["subgroup_metrics"]["path"]); importance=_rows(outputs["feature_importance"]["path"]); diagnostics=_rows(outputs["training_diagnostics"]["path"])
    aggregates=attach_aggregate_bootstrap(aggregate_folds(metrics),daily,manifest["evaluation_configuration"]["seed"],manifest["evaluation_configuration"]["bootstrap_replicates"])
    result={"metrics":metrics,"aggregate_metrics":aggregates,"daily_ic":daily,"buckets":buckets,"subgroup_metrics":subgroup,"feature_importance":importance,"training_diagnostics":diagnostics}
    current=git_state(repo); current["branch"]=subprocess.run(["git","-C",str(repo),"branch","--show-current"],check=True,capture_output=True,text=True).stdout.strip()
    manifest["evaluation_generation_code"]=manifest["code"]; manifest["code"]=current; manifest["aggregate_metrics"]=aggregates; manifest["feature_importance_fold_stability"]=importance_fold_stability(importance); manifest["verification"]={"cpu_suite":cpu_result,"c8_gpu_suite":gpu_result}
    c7_path=repo/"artifacts/models/c7/feature_importance.parquet"; c7_stability=[]
    if c7_path.exists():
        transformed=[]
        for r in _rows(c7_path):
            horizon=next((h for h in (5,10,20) if f"_{h}s_" in r["target_name"]),None)
            if horizon in (5,10): transformed.append({**r,"stage":0,"horizon":horizon,"target_family":"absolute","feature_variant":"A_c7_only"})
        c7_stability=importance_fold_stability(transformed); manifest["c7_feature_importance_fold_stability"]=c7_stability
    viewer={"manifest_version":1,"holdout_accessed":False,"aggregate_metrics":aggregates,"artifacts":{k:v for k,v in outputs.items() if k in {"model_metrics","daily_ic","bucket_outcomes","subgroup_metrics","feature_importance","training_diagnostics"}},"feature_importance_stability":importance_stability(importance),"feature_importance_fold_stability":manifest["feature_importance_fold_stability"],"training_diagnostics":diagnostics}
    viewer_path=Path(outputs["viewer_summary"]["path"]); write_json(viewer,viewer_path); outputs["viewer_summary"]["file_sha256"]=sha256_file(viewer_path)
    model_path=repo/"artifacts/reports/C8_MODEL_REPORT.md"; model_report(result,model_path)
    selected=[r for r in manifest["feature_importance_fold_stability"] if r["model_name"]=="lightgbm_cpu" and ((r["target_family"]=="market_relative" and r["feature_variant"]=="A_c7_only") or (r["target_family"]=="sector_shrunk_3_peer" and r["feature_variant"]=="C_sector_context"))]
    with model_path.open("a") as f:
        f.write("\n## Feature-importance fold stability\n\nMean pairwise gain-rank correlation is reported below. Higher is more stable; negative values indicate fold reversal.\n\n| Source | Horizon | Target | Features | Mean pairwise rank correlation | Minimum |\n|---|---:|---|---|---:|---:|\n")
        for r in c7_stability:
            if r["model_name"]=="lightgbm_cpu": f.write(f"| C7 | {r['horizon']} | absolute | A | {r['mean_pairwise_gain_rank_correlation']} | {r['minimum_pairwise_gain_rank_correlation']} |\n")
        for r in selected: f.write(f"| C8 | {r['horizon']} | {r['target_family']} | {r['feature_variant']} | {r['mean_pairwise_gain_rank_correlation']} | {r['minimum_pairwise_gain_rank_correlation']} |\n")
    supplemental_path=repo/"data/processed/diagnostics/c8_supplemental_evaluation.json"
    supplemental=json.loads(supplemental_path.read_text()) if supplemental_path.exists() else None
    if supplemental:
        if supplemental.get("holdout_accessed") is not False: raise RuntimeError("supplemental evaluation accessed holdout")
        pred_path=Path(supplemental["prediction_path"])
        manifest["supplemental_evaluation"]={"generation_code":supplemental["code"],"holdout_accessed":False,"fitted_model_count":len(supplemental["models"]),"prediction_rows":supplemental["prediction_rows"],"rank_summary":supplemental["summary"]["rank"],"classification_summary":supplemental["summary"]["classification"],"models":supplemental["models"],"outputs":{"structured":{"path":str(supplemental_path),"file_sha256":sha256_file(supplemental_path)},"predictions":{"path":str(pred_path),"file_sha256":sha256_file(pred_path)}}}
        manifest["evaluation_counts"]["supplemental_fit_count"]=len(supplemental["models"]); manifest["evaluation_counts"]["supplemental_prediction_rows"]=supplemental["prediction_rows"]
        rank_lookup={(r["horizon"],r["feature_variant"],r["model_name"]):r for r in supplemental["summary"]["rank"]}
        with model_path.open("a") as f:
            f.write("\n## Direct market-relative rank-target models\n\nRank targets use deterministic same-date percentile relevance (`0=lowest`, `1=highest`). NDCG uses that non-negative relevance directly. D10-D1 is measured on the underlying market-relative return, not on percentile labels. B and D share identical target populations within each horizon.\n\n| Horizon | Features | Model | Mean IC | Median IC | Positive-date fraction | Fold ICs | Fold std | NDCG@5 | NDCG@10 | Top-decile capture | D10-D1 | Monotonicity | IC 95% CI | D10 95% CI |\n|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---|\n")
            for key,s in sorted(rank_lookup.items()):
                part=[r for r in supplemental["rank"] if (r["horizon"],r["feature_variant"],r["model_name"])==key]; daily=[d for r in part for d in r["fold_daily_metrics"]]
                ic=_interval([d["daily_ic"] for d in daily],42,200); spread=_interval([d["d10_d1_spread"] for d in daily],46,200)
                ci="—" if ic["lower"] is None else f"[{ic['lower']:.5g}, {ic['upper']:.5g}]"; si="—" if spread["lower"] is None else f"[{spread['lower']:.5g}, {spread['upper']:.5g}]"
                folds=", ".join(f"{v:.5g}" for v in s["fold_ic"])
                f.write(f"| {s['horizon']} | `{s['feature_variant']}` | `{s['model_name']}` | {s['mean_daily_ic']:.6g} | {s['median_daily_ic']:.6g} | {s['positive_ic_date_fraction']:.4f} | {folds} | {s['fold_ic_std']:.6g} | {s['ndcg_5']:.6g} | {s['ndcg_10']:.6g} | {s['top_decile_capture']:.6g} | {s['d10_d1_spread']:.6g} | {s['bucket_monotonicity']:.6g} | {ci} | {si} |\n")
            f.write("\n## Relative classification models\n\nSector classification uses the strict five-peer target population. The prevalence baseline is estimated from each fold's training rows. Calibration is retained as ten deterministic probability bins per task/model/fold; ECE below is the row-weighted absolute calibration gap.\n\n| Target | Model | ROC AUC | PR AUC | Log loss | Brier | Balanced accuracy | Prevalence | Fold ROC AUCs | Fold std | Mean ECE |\n|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|\n")
            for s in supplemental["summary"]["classification"]:
                cal=[r for r in supplemental["calibration"] if r["target_name"]==s["target_name"] and r["model_name"]==s["model_name"]]
                eces=[]
                for r in cal:
                    n=sum(b["n"] for b in r["bins"]); eces.append(sum(b["n"]*abs(b["mean_probability"]-b["observed_rate"]) for b in r["bins"] if b["n"])/n)
                folds=", ".join(f"{v:.5g}" for v in s["fold_roc_auc"])
                f.write(f"| `{s['target_name']}` | `{s['model_name']}` | {s['roc_auc']:.6g} | {s['pr_auc']:.6g} | {s['log_loss']:.6g} | {s['brier']:.6g} | {s['balanced_accuracy']:.6g} | {s['prevalence']:.6g} | {folds} | {s['fold_roc_auc_std']:.6g} | {sum(eces)/len(eces):.6g} |\n")
    bucket_report(result,repo/"artifacts/reports/C8_BUCKET_REPORT.md"); ablation_report(result,repo/"artifacts/reports/C8_ABLATION_REPORT.md"); delivery_report(result,manifest,repo/"contracts/C08-DELIVERY.md")
    if supplemental:
        delivery=repo/"contracts/C08-DELIVERY.md"
        with delivery.open("a") as f:
            best=next(r for r in supplemental["summary"]["rank"] if r["horizon"]==5 and r["feature_variant"]=="B_market_context" and r["model_name"]=="lightgbm_cpu")
            cls=next(r for r in supplemental["summary"]["classification"] if r["target_name"]=="outperform_market_5s" and r["model_name"]=="lightgbm_cpu")
            f.write(f"\n## Remaining contract matrix\n\nDirect rank-target and relative-classification models were added from clean commit `{supplemental['code']['commit']}`. They add **{len(supplemental['models'])}** fitted models and **{supplemental['prediction_rows']}** validation predictions. Five-session rank/B LightGBM mean daily IC is `{best['mean_daily_ic']:.6g}` with fold ICs `{best['fold_ic']}`. Five-session market-outperformance LightGBM ROC AUC is `{cls['roc_auc']:.6g}` versus `0.5` for the prevalence baseline. Full rank, NDCG, capture, spread, classification, calibration, and fold-stability results are in C8_MODEL_REPORT.md and the structured supplemental artifact. The 2026 holdout remained untouched.\n")
    coverage=repo/"artifacts/reports/C8_SECTOR_COVERAGE_REPORT.md"; text=coverage.read_text().replace("Daily IC, D10-D1 spread, and fold dispersion are model-dependent and will be appended after predictions exist; they are not inferred from target construction.","Model-dependent daily IC, D10-D1, fold dispersion, natural-coverage, and strict-matched results are now reported in C8_MODEL_REPORT.md and the structured model diagnostics."); coverage.write_text(text)
    write_json(manifest,manifest_path); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--cpu-result",required=True); p.add_argument("--gpu-result",required=True); a=p.parse_args(); m=refresh(a.repo,a.cpu_result,a.gpu_result); print(f"C8 reports refreshed: dirty={m['code']['dirty']} holdout={m['holdout_accessed']}")

if __name__=="__main__": main()
