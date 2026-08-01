import json,sqlite3
import pyarrow.parquet as pq
from psx_ml.models.pipeline import run_pipeline

def test_pipeline_determinism_scope_manifest_and_no_sqlite(model_project,monkeypatch):
    root,cfg=model_project; calls=[]; monkeypatch.setattr(sqlite3,"connect",lambda *a,**k:calls.append(1))
    one=run_pipeline(cfg,root); two=run_pipeline(cfg,root)
    assert calls==[] and one["holdout_accessed"] is False
    assert one["outputs"]["predictions"]["logical_sha256"]==two["outputs"]["predictions"]["logical_sha256"]
    assert one["outputs"]["coefficients"]["logical_sha256"]==two["outputs"]["coefficients"]["logical_sha256"]
    pred=pq.read_table(root/"out/pred.parquet"); assert set(pred["split_role"].to_pylist())=={"validation"}
    assert set(pred["model_name"].to_pylist()) >= {"zero_return_baseline","training_mean_baseline","ridge_selected","majority_class_baseline","training_prevalence_baseline","logistic_selected"}
    assert one["ordered_feature_allowlist"]==["f1","f2"] and one["counts"]["coefficient_rows"]>0
    assert "profitability" in (root/"art/model.md").read_text()

