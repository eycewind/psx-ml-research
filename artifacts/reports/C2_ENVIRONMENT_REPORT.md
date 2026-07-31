# C2 Environment Report

Generated 2026-07-31 19:47 UTC from C2 implementation commit `181dc61` on
`feature/c2-reproducible-ml-environment`.

## Host and environment

| Item | Live value |
|---|---|
| Environment | Conda `psx-ml-research` |
| Python | 3.12.13 |
| Executable | `/home/hassan/miniconda3/envs/psx-ml-research/bin/python` |
| Platform | Linux x86_64, WSL2 kernel 6.18.33.2 |
| NumPy | 2.4.4 |
| PyArrow | 21.0.0 |
| PyTorch | 2.11.0+cu128 |
| PyTorch CUDA runtime | 12.8 |
| NVIDIA driver | 592.07 |
| GPU | NVIDIA GeForce RTX 5070 Laptop GPU |
| GPU capability | 12.0 |
| GPU memory | 8,546,484,224 bytes |
| Wheel architectures | sm_75, sm_80, sm_86, sm_90, sm_100, sm_120 |

The driver advertises support independently of the CUDA 12.8 runtime bundled
inside the selected official PyTorch wheel. No system CUDA Toolkit was installed.

## Installation method

The pre-existing dedicated Conda environment was retained. The repository was
installed editable with `python -m pip install -e '.[dev]'`; the existing
official CUDA PyTorch 2.11.0+cu128 installation was not replaced. Import
verification resolved `psx_ml` to
`/home/hassan/psx-ml-research/src/psx_ml/__init__.py` without `PYTHONPATH`.

## Runtime verification

- Default policy: seed 42, deterministic algorithms enabled, TF32 disabled.
- Selected live device: CUDA.
- CPU smoke test: PASS.
- GPU 256×256 float32 matrix multiplication: PASS.
- CPU/GPU comparison: PASS at `atol=1e-4`, `rtol=1e-4`.
- Maximum absolute difference: 4.9591064453125e-05.
- Allocated bytes before smoke: 0.
- Allocated bytes after deletion, garbage collection, `empty_cache`, and
  synchronization: 8,519,680. This is bounded below the 16 MiB context-workspace
  allowance and is not counted as a leaked tensor allocation.

## Acceptance commands and results

```text
python -m pytest -s
19 passed in 3.51s

python -m pytest -s -m gpu
1 passed, 18 deselected in 1.35s

CUDA_VISIBLE_DEVICES="" python -m pytest -s -m "not gpu"
18 passed, 1 deselected in 3.08s

CUDA_VISIBLE_DEVICES="" python -m pytest -s
18 passed, 1 skipped in 3.17s
```

Diagnostics were also run in human and JSON modes. The machine-readable result
is committed as `C2_ENVIRONMENT_MANIFEST.json`.
With CUDA hidden, `auto` selected CPU, CPU smoke comparison passed exactly, and
all CUDA device fields degraded cleanly to unavailable/empty values.

## Known limitations

Deterministic settings improve repeatability within this runtime but do not
promise identical results across PyTorch versions, drivers, devices, operating
systems, or algorithms without deterministic implementations. CPU/GPU floating
point results are tolerance-compared rather than required to be bit-identical.
The CUDA runtime retains a small framework/context allocation after first use.
