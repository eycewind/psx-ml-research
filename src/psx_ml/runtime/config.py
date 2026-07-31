from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class RuntimeConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class RuntimeConfig:
    device: str = "auto"
    seed: int = 42
    deterministic: bool = True
    allow_tf32: bool = False

    def __post_init__(self) -> None:
        if self.device not in {"auto", "cpu", "cuda"}:
            raise RuntimeConfigurationError(
                f"runtime.device must be auto, cpu, or cuda; got {self.device!r}")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise RuntimeConfigurationError("runtime.seed must be a non-negative integer")


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    values=tomllib.loads(Path(path).read_text()).get("runtime", {})
    allowed={"device","seed","deterministic","allow_tf32"}
    extra=set(values)-allowed
    if extra: raise RuntimeConfigurationError(f"Unknown runtime settings: {sorted(extra)}")
    return RuntimeConfig(**values)
