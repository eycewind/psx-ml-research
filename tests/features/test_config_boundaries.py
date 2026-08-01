from pathlib import Path

import pytest

from psx_ml.features.config import FeatureConfigurationError,load_feature_config
from psx_ml.features.pipeline import OutputBoundaryError,validate_output_boundaries
from tests.features.conftest import write_inputs


def test_family_mixing_and_unknowns_fail(tmp_path,panel_rows):
    cfg=write_inputs(tmp_path,panel_rows)
    text=cfg.read_text().replace('volume_family="adjusted"','volume_family="raw"'); cfg.write_text(text)
    with pytest.raises(FeatureConfigurationError,match="must match"): load_feature_config(cfg,tmp_path)


def test_production_and_outside_outputs_refused(tmp_path,panel_rows):
    cfg=write_inputs(tmp_path,panel_rows)
    text=cfg.read_text().replace('feature_path="data/processed/features.parquet"','feature_path="/home/hassan/psx-stock-watcher/data/psx_watcher.db"'); cfg.write_text(text)
    parsed=load_feature_config(cfg,tmp_path)
    with pytest.raises(OutputBoundaryError): validate_output_boundaries(parsed,tmp_path)
