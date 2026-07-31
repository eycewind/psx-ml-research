from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import RuntimeConfig, load_runtime_config
from .device import resolve_device
from .metadata import collect_metadata, write_manifest
from .reproducibility import configure_reproducibility
from .smoke import compute_smoke


def diagnose(config: RuntimeConfig, repo: Path, run_smoke: bool = True) -> dict:
    state=configure_reproducibility(config.seed,config.deterministic,config.allow_tf32)
    result=collect_metadata(config,repo)
    if run_smoke: result["smoke_test"]=compute_smoke(resolve_device(config.device)).to_dict()
    return result


def main() -> None:
    p=argparse.ArgumentParser(description="Report the PSX ML runtime without accessing market data")
    p.add_argument("--config",type=Path)
    p.add_argument("--repo",type=Path,default=Path.cwd())
    p.add_argument("--device",choices=["auto","cpu","cuda"])
    p.add_argument("--json",action="store_true")
    p.add_argument("--output",type=Path)
    a=p.parse_args(); repo=a.repo.resolve()
    config=load_runtime_config(a.config) if a.config else RuntimeConfig()
    if a.device: config=RuntimeConfig(a.device,config.seed,config.deterministic,config.allow_tf32)
    result=diagnose(config,repo)
    if a.output: write_manifest(result,a.output)
    if a.json: print(json.dumps(result,sort_keys=True))
    else:
        print(f"Python: {result['python']['version']} ({result['python']['executable']})")
        print(f"Environment: {result['environment']['name']}")
        print(f"PyTorch: {result['packages']['torch']} (CUDA runtime {result['cuda']['torch_runtime']})")
        print(f"CUDA available: {result['cuda']['available']}; selected: {result['selected_device']}")
        for d in result['cuda']['devices']:
            print(f"GPU {d['index']}: {d['name']}; capability {d['capability']}; memory {d['total_memory_bytes']}")
        print(f"Smoke: {'PASS' if result['smoke_test']['comparison_passed'] else 'FAIL'}; {result['smoke_test']}")


if __name__ == "__main__": main()
