import json
import sqlite3

import pyarrow.parquet as pq

from psx_ml.features.pipeline import run_pipeline
from tests.features.conftest import write_inputs


def test_pipeline_determinism_manifest_report_and_no_sqlite(tmp_path,panel_rows,monkeypatch):
    cfg=write_inputs(tmp_path,panel_rows); calls=[]
    monkeypatch.setattr(sqlite3,"connect",lambda *a,**k:calls.append((a,k)))
    one=run_pipeline(cfg,tmp_path); two=run_pipeline(cfg,tmp_path)
    assert calls==[]
    assert one["output"]["logical_content_sha256"]==two["output"]["logical_content_sha256"]
    assert one["output"]["file_sha256"]==two["output"]["file_sha256"]
    out=pq.read_table(tmp_path/"data/processed/features.parquet")
    assert out.num_rows==one["output"]["rows"]==len(panel_rows)
    assert len(set(zip(out["trade_date"].to_pylist(),out["symbol"].to_pylist())))==out.num_rows
    assert one["ordered_features"]==[d["name"] for d in one["feature_registry"]]
    assert (tmp_path/"artifacts/reports/C3.md").read_text().find("Adjusted prices")>0
    saved=json.loads((tmp_path/"data/processed/manifest.json").read_text())
    assert saved["output"]["logical_content_sha256"]==one["output"]["logical_content_sha256"]
