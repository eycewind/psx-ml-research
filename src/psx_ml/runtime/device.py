from __future__ import annotations

import torch


class DeviceUnavailableError(RuntimeError):
    pass


def _cuda_usable() -> tuple[bool, str | None]:
    if not torch.cuda.is_available(): return False, "PyTorch reports CUDA unavailable"
    try:
        torch.empty(1, device="cuda")
        torch.cuda.synchronize()
        return True, None
    except Exception as exc:  # driver/runtime failures vary by build
        return False, f"CUDA initialization failed: {exc}"


def resolve_device(requested: str) -> torch.device:
    if requested not in {"auto","cpu","cuda"}:
        raise ValueError(f"Unsupported device {requested!r}; expected auto, cpu, or cuda")
    if requested == "cpu": return torch.device("cpu")
    usable,reason=_cuda_usable()
    if requested == "cuda" and not usable:
        raise DeviceUnavailableError(reason or "CUDA unavailable")
    return torch.device("cuda" if usable else "cpu")
