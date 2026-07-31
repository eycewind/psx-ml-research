import pytest
import torch

from psx_ml.runtime.device import resolve_device
from psx_ml.runtime.smoke import compute_smoke


pytestmark=pytest.mark.gpu


@pytest.mark.skipif(not torch.cuda.is_available(),reason="CUDA is not available")
def test_real_cuda_compute_reconciliation_and_cleanup():
    device=resolve_device("cuda")
    before=torch.cuda.memory_allocated()
    result=compute_smoke(device,size=256)
    assert result.device.startswith("cuda")
    assert result.comparison_passed
    assert result.allocated_after_cleanup is not None
    # CUDA/cuBLAS may retain a small context workspace even after empty_cache;
    # bound it without confusing framework context memory with leaked tensors.
    assert result.allocated_after_cleanup <= before + 16*1024*1024
    assert "RTX 5070" in torch.cuda.get_device_name(0)
