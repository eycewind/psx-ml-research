import pytest

from psx_ml.targets.config import TargetConfigurationError,load_target_config
from psx_ml.targets.pipeline import OutputBoundaryError,_bound
from tests.targets.conftest import write_pipeline_inputs

def test_invalid_horizon_config_rejected(tmp_path,target_rows):
    tc,_=write_pipeline_inputs(tmp_path,target_rows); tc.write_text(tc.read_text().replace("horizons=[1,5,10,20]","horizons=[1,5,20]"))
    with pytest.raises(TargetConfigurationError): load_target_config(tc,tmp_path)

def test_output_boundary_rejects_watcher_and_outside(tmp_path):
    with pytest.raises(OutputBoundaryError): _bound([__import__('pathlib').Path('/home/hassan/c4-outside')],tmp_path/"repo")
    with pytest.raises(OutputBoundaryError): _bound([__import__('pathlib').Path('/home/hassan/psx-stock-watcher/data/x')],tmp_path)
