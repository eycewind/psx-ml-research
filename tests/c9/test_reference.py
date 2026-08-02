import pytest
from pathlib import Path
from psx_ml.c9.reference_predictions import run

def test_reference_holdout_override_fails_before_reads(tmp_path):
    with pytest.raises(RuntimeError,match="holdout"):
        run(tmp_path,tmp_path/"missing.toml",allow_final_holdout=True)
