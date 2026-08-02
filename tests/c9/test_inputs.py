import pytest
from psx_ml.c9.inputs import inside

def test_outputs_outside_repo_rejected(tmp_path):
    with pytest.raises(ValueError): inside(tmp_path,"../escape")

def test_holdout_flag_is_rejected_without_reading_inputs(tmp_path):
    from psx_ml.c9.inputs import validate_inputs
    with pytest.raises(RuntimeError,match="holdout"):
        validate_inputs(tmp_path,{},allow_final_holdout=True)
