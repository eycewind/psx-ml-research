# psx-ml-research

Leakage-safe machine-learning research foundation for Pakistan Stock Exchange
daily data. C1 only audits and extracts source data; it does not implement
features, targets, models, or backtests.

The production watcher database is always opened with SQLite URI `mode=ro` and
`PRAGMA query_only=ON`. All generated files belong under this repository.

## Supported environment setup

Create and activate the dedicated environment **before installing anything**:

```bash
conda create -n psx-ml-research python=3.12 -y
conda activate psx-ml-research
cd ~/psx-ml-research
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Install a CUDA-enabled PyTorch wheel deliberately from the official PyTorch
wheel index. The verified RTX 5070 environment uses a CUDA 12.8 wheel:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
python -c "import psx_ml, torch; print(psx_ml.__file__); print(torch.__version__, torch.version.cuda)"
```

The CUDA level displayed by `nvidia-smi` is the maximum supported by the driver;
`torch.version.cuda` is the runtime bundled with the installed PyTorch wheel.
They need not match. A system CUDA Toolkit is not required because C2 compiles
no CUDA extensions.

## Runtime verification

```bash
python -m psx_ml.runtime.diagnostics
python -m psx_ml.runtime.diagnostics --json
python -m pytest -q
python -m pytest -q -m gpu
CUDA_VISIBLE_DEVICES="" python -m pytest -q -m "not gpu"
```

Copy `config/runtime.example.toml` for local configuration. `auto` uses CUDA
only after a real initialization succeeds; `cpu` never initializes CUDA work;
and explicit `cuda` raises an error instead of silently falling back. Defaults
are seed 42, deterministic algorithms enabled, and TF32 disabled.

If installation happened in the wrong Conda environment, uninstall the project
there, activate `psx-ml-research`, verify `which python`, and repeat the editable
installation. Upgrade PyTorch only as a deliberate operation: choose an official
wheel index, install it, rerun both diagnostic forms and all test suites, and
review the resulting environment report. Do not let an unrelated dependency
upgrade replace the tested PyTorch build incidentally.

Run the C1 extraction only when intentionally refreshing the local research
cache:

```bash
psx-c1 run --source-db /home/hassan/psx-stock-watcher/data/psx_watcher.db
```

See [the C1 contract](contracts/C01-CONTRACT.md) and
the C2 environment contract and generated reports under `artifacts/reports/`.
