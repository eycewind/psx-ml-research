from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow
import torch

from .config import RuntimeConfig
from .device import resolve_device


def _git_commit(repo: Path) -> str:
    try:
        sha=subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
        dirty=bool(subprocess.run(["git","-C",str(repo),"status","--porcelain"],capture_output=True,text=True,check=True).stdout)
        return f"{sha}-dirty" if dirty else sha
    except Exception: return "unavailable"


def _driver_version() -> str | None:
    try:
        return subprocess.run(["nvidia-smi","--query-gpu=driver_version","--format=csv,noheader"],
            capture_output=True,text=True,check=True,timeout=10).stdout.splitlines()[0].strip()
    except Exception: return None


def collect_metadata(config: RuntimeConfig, repo: Path) -> dict:
    available=torch.cuda.is_available(); devices=[]
    if available:
        for i in range(torch.cuda.device_count()):
            p=torch.cuda.get_device_properties(i)
            devices.append({"index":i,"name":p.name,"capability":list(torch.cuda.get_device_capability(i)),
                            "total_memory_bytes":p.total_memory})
    selected=resolve_device(config.device)
    return {"manifest_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "git_commit":_git_commit(repo),
      "python":{"version":platform.python_version(),"executable":sys.executable},
      "platform":{"system":platform.system(),"release":platform.release(),"machine":platform.machine()},
      "environment":{"name":os.environ.get("CONDA_DEFAULT_ENV") or os.environ.get("VIRTUAL_ENV")},
      "packages":{"numpy":np.__version__,"pyarrow":pyarrow.__version__,"torch":torch.__version__},
      "cuda":{"available":available,"torch_runtime":torch.version.cuda,"driver_version":_driver_version(),
              "device_count":torch.cuda.device_count() if available else 0,"devices":devices,
              "wheel_architectures":torch.cuda.get_arch_list() if available else []},
      "selected_device":str(selected),
      "reproducibility":{"seed":config.seed,"deterministic":config.deterministic,"allow_tf32":config.allow_tf32}}


def write_manifest(metadata: dict, path: Path) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
