from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import pyarrow.parquet as pq
from psx_ml.features.manifest import git_state,sha256_file,write_json
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
    bucket_report(result,repo/"artifacts/reports/C8_BUCKET_REPORT.md"); ablation_report(result,repo/"artifacts/reports/C8_ABLATION_REPORT.md"); delivery_report(result,manifest,repo/"artifacts/reports/C8_DELIVERY.md")
    coverage=repo/"artifacts/reports/C8_SECTOR_COVERAGE_REPORT.md"; text=coverage.read_text().replace("Daily IC, D10-D1 spread, and fold dispersion are model-dependent and will be appended after predictions exist; they are not inferred from target construction.","Model-dependent daily IC, D10-D1, fold dispersion, natural-coverage, and strict-matched results are now reported in C8_MODEL_REPORT.md and the structured model diagnostics."); coverage.write_text(text)
    write_json(manifest,manifest_path); return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--cpu-result",required=True); p.add_argument("--gpu-result",required=True); a=p.parse_args(); m=refresh(a.repo,a.cpu_result,a.gpu_result); print(f"C8 reports refreshed: dirty={m['code']['dirty']} holdout={m['holdout_accessed']}")

if __name__=="__main__": main()
