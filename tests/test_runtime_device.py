import pytest
import torch

from psx_ml.runtime import device
from psx_ml.runtime.device import DeviceUnavailableError, resolve_device


def test_cpu_never_checks_or_initializes_cuda(monkeypatch):
    monkeypatch.setattr(torch.cuda,"is_available",lambda: (_ for _ in ()).throw(AssertionError("CUDA touched")))
    assert resolve_device("cpu").type == "cpu"


def test_auto_falls_back_to_cpu(monkeypatch):
    monkeypatch.setattr(device,"_cuda_usable",lambda:(False,"hidden"))
    assert resolve_device("auto").type == "cpu"


def test_auto_and_cuda_select_working_cuda(monkeypatch):
    monkeypatch.setattr(device,"_cuda_usable",lambda:(True,None))
    assert resolve_device("auto").type == "cuda"
    assert resolve_device("cuda").type == "cuda"


def test_explicit_cuda_failure_is_clear(monkeypatch):
    monkeypatch.setattr(device,"_cuda_usable",lambda:(False,"driver unavailable"))
    with pytest.raises(DeviceUnavailableError,match="driver unavailable"): resolve_device("cuda")


def test_invalid_device_rejected():
    with pytest.raises(ValueError,match="Unsupported device"): resolve_device("gpu")
