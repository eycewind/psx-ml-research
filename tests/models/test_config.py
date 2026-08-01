from dataclasses import replace
import pytest
from psx_ml.models.config import ModelConfigurationError,load_config
from psx_ml.models.validation import OutputBoundaryError,validate_outputs

def test_forbidden_feature_and_config_hash(model_project):
    root,cfg=model_project; c=load_config(cfg,root); assert replace(c,seed=43).sha256()!=c.sha256()
    cfg.write_text(cfg.read_text().replace('features=["f1","f2"]','features=["f1","target_end_date_20s"]'))
    with pytest.raises(ModelConfigurationError): load_config(cfg,root)

def test_output_boundary(tmp_path):
    with pytest.raises(OutputBoundaryError): validate_outputs([__import__('pathlib').Path('/home/hassan/outside-c5')],tmp_path)
    with pytest.raises(OutputBoundaryError): validate_outputs([__import__('pathlib').Path('/home/hassan/psx-stock-watcher/x')],tmp_path)
