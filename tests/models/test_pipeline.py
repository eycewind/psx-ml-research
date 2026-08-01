import json,sqlite3
import pyarrow.parquet as pq
from psx_ml.models.pipeline import run_pipeline
from psx_ml.models.config import load_config
from psx_ml.models.validation import validate_inputs
from psx_ml.models.train import evaluate

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

def test_targets_outside_fold_do_not_change_fold_predictions(model_project):
    root,cfg=model_project; c=load_config(cfg,root); labelled,splits,*_=validate_inputs(c); one,_,_=evaluate(labelled,splits,c)
    rows=labelled.to_pylist()
    for r in rows:
        if r["trade_date"]>="2024-01-31":
            for target in c.regression_targets: r[target]+=1000
            for target in c.classification_targets: r[target]=1-r[target]
    two,_,_=evaluate(__import__('pyarrow').Table.from_pylist(rows,schema=labelled.schema),splits,c)
    def fold1(t): return [r for r in t.to_pylist() if r["fold_id"]=="f1"]
    assert fold1(one)==fold1(two)
