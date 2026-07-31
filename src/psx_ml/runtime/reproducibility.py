from __future__ import annotations

import os
import random
from dataclasses import asdict, dataclass

import numpy as np
import torch


@dataclass(frozen=True)
class ReproducibilityState:
    seed: int
    deterministic: bool
    allow_tf32: bool

    def to_dict(self) -> dict: return asdict(self)


def configure_reproducibility(seed: int, deterministic: bool = True,
                              allow_tf32: bool = False) -> ReproducibilityState:
    if isinstance(seed,bool) or not isinstance(seed,int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(deterministic, warn_only=False)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark=False
        torch.backends.cudnn.deterministic=deterministic
        torch.backends.cudnn.allow_tf32=allow_tf32
    if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "matmul"):
        torch.backends.cuda.matmul.allow_tf32=allow_tf32
    os.environ["PYTHONHASHSEED"]=str(seed)
    return ReproducibilityState(seed,deterministic,allow_tf32)
