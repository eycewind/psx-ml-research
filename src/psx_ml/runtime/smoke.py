from __future__ import annotations

import gc
from dataclasses import asdict, dataclass

import torch


@dataclass(frozen=True)
class SmokeResult:
    device: str
    tensor_shape: list[int]
    comparison_passed: bool
    max_absolute_error: float
    atol: float
    rtol: float
    allocated_before: int | None
    allocated_after_cleanup: int | None

    def to_dict(self): return asdict(self)


def compute_smoke(device: torch.device, size: int = 256,
                  atol: float = 1e-4, rtol: float = 1e-4) -> SmokeResult:
    gen=torch.Generator(device="cpu").manual_seed(12345)
    a=torch.randn((size,size),generator=gen,dtype=torch.float32)
    b=torch.randn((size,size),generator=gen,dtype=torch.float32)
    expected=a @ b
    before=torch.cuda.memory_allocated() if device.type == "cuda" else None
    da=a.to(device); db=b.to(device); actual=da @ db
    if device.type == "cuda": torch.cuda.synchronize()
    observed=actual.cpu()
    passed=torch.allclose(expected,observed,atol=atol,rtol=rtol)
    error=float(torch.max(torch.abs(expected-observed)).item())
    del da,db,actual,observed,a,b,expected
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache(); torch.cuda.synchronize(); after=torch.cuda.memory_allocated()
    else: after=None
    return SmokeResult(str(device),[size,size],bool(passed),error,atol,rtol,before,after)
