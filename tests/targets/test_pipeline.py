import json,sqlite3

import pyarrow.parquet as pq

from psx_ml.targets.pipeline import run_pipeline
from tests.targets.conftest import write_pipeline_inputs

def test_pipeline_determinism_manifest_reports_no_sqlite(tmp_path,target_rows,monkeypatch):
    tc,sc=write_pipeline_inputs(tmp_path,target_rows); calls=[]; monkeypatch.setattr(sqlite3,"connect",lambda *a,**k:calls.append((a,k)))
    one=run_pipeline(tc,sc,tmp_path); two=run_pipeline(tc,sc,tmp_path)
    assert calls==[]
    assert one["output"]["labelled"]["logical_sha256"]==two["output"]["labelled"]["logical_sha256"]
    assert one["output"]["splits"]["logical_sha256"]==two["output"]["splits"]["logical_sha256"]
    assert one["output"]["labelled"]["file_sha256"]==two["output"]["labelled"]["file_sha256"]
    assert one["output"]["splits"]["file_sha256"]==two["output"]["splits"]["file_sha256"]
    assert pq.read_metadata(tmp_path/"data/out/targets.parquet").num_rows==len(target_rows)
    assert json.loads((tmp_path/"data/out/manifest.json").read_text())["fold_counts"]==one["fold_counts"]
    assert "gross returns" in (tmp_path/"artifacts/target.md").read_text()
