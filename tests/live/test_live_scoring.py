from pathlib import Path
import json
import pytest
from psx_ml.live.live_scoring import _load_c8_feature_order, _verify_frozen_model

def test_feature_order_requires_56(tmp_path: Path):
    p=tmp_path/"m.json"; features=[f"f{i}" for i in range(56)]
    p.write_text(json.dumps({"feature_definitions":{"variants":{"B_market_context":features}}}))
    assert _load_c8_feature_order(p)==features

def test_feature_order_rejects_wrong_count(tmp_path: Path):
    p=tmp_path/"m.json"; p.write_text(json.dumps({"feature_definitions":{"variants":{"B_market_context":["a","b"]}}}))
    with pytest.raises(ValueError,match="Expected 56"): _load_c8_feature_order(p)

def test_model_hash_guard(tmp_path: Path):
    p=tmp_path/"model.txt"; p.write_text("wrong")
    with pytest.raises(ValueError,match="SHA-256 mismatch"): _verify_frozen_model(p)
