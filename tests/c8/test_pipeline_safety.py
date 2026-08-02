from pathlib import Path
import pytest
from psx_ml.c8.pipeline import _inside,run


def test_output_boundary_rejects_escape(tmp_path):
    repo=tmp_path/"repo"; repo.mkdir()
    with pytest.raises(ValueError,match="outside repository"): _inside(repo,"../escape.parquet")


def test_holdout_flag_fails_before_any_read(tmp_path):
    config=tmp_path/"missing.toml"
    with pytest.raises(RuntimeError,match="holdout access is locked"): run(config,tmp_path,allow_final_holdout=True)
