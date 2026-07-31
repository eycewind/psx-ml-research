from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path


def load_config(path: str | Path) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    return tomllib.loads(raw.decode()), hashlib.sha256(raw).hexdigest()
