from pathlib import Path
import pytest
from psx_ml.tree_models.config import TreeConfigError,load_config

def test_forbidden_feature_and_output_boundary(tmp_path):
    text=Path("config/tree_models.example.toml").read_text().replace('"ret_1obs_adj",','"target_leak",')
    p=tmp_path/"bad.toml"; p.write_text(text)
    with pytest.raises(TreeConfigError): load_config(p,tmp_path)
    text=Path("config/tree_models.example.toml").read_text().replace('model_report_path = "artifacts/reports/C7_MODEL_REPORT.md"','model_report_path = "/outside/report.md"')
    p.write_text(text)
    with pytest.raises(TreeConfigError): load_config(p,tmp_path)

def test_config_hash_changes(tmp_path):
    p=Path("config/tree_models.example.toml"); one=load_config(p,Path.cwd()); changed=tmp_path/"c.toml"; changed.write_text(p.read_text().replace("hist_max_iter = 150","hist_max_iter = 151")); two=load_config(changed,Path.cwd())
    assert one.sha256()!=two.sha256()
