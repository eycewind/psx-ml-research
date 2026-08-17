# C2 — Reproducible ML Research Environment

## 1. Contract status

- **Project:** `psx-ml-research`
- **Contract:** `C2_REPRODUCIBLE_ML_ENVIRONMENT`
- **Required implementation branch:** `feature/c2-reproducible-ml-environment`
- **Base branch:** accepted C1 `main`
- **Merge rule:** implement and validate C2 entirely on its own feature branch. Merge into `main` only after all C2 acceptance tests pass and the delivery report has been reviewed and accepted.
- **C14 boundary:** do not modify, merge, rebase, cherry-pick, or otherwise interact with the pending C14 branch in `psx-stock-watcher`.
- **Source-system boundary:** the complete `psx-stock-watcher` repository and `psx_watcher.db` remain read-only and out of scope for modification.

## 2. Purpose

C2 establishes a clean, isolated, reproducible machine-learning runtime for `psx-ml-research` before any feature engineering, target construction, model training, prediction generation, or backtesting begins.

The objective is not to demonstrate model performance. The objective is to prove that:

1. the project can be installed into a dedicated environment;
2. CPU and CUDA execution paths work predictably;
3. the NVIDIA RTX 5070 is usable by the selected PyTorch build;
4. environment metadata and dependency versions are captured;
5. deterministic experiment controls exist;
6. research code can select CPU or GPU explicitly without silently changing behaviour; and
7. none of this work can modify production PSX data.

## 3. Verified host assumptions

The implementation may use the following verified development-machine facts as the initial supported environment:

```text
Operating context: Linux user environment
Conda environment: psx-ml-research
Python: 3.12.x
GPU: NVIDIA GeForce RTX 5070 Laptop GPU
GPU memory: approximately 8 GiB
NVIDIA driver reported by nvidia-smi: 592.07
Driver-supported CUDA level reported by nvidia-smi: 13.1
```

Important distinction:

- The CUDA version printed by `nvidia-smi` is the maximum CUDA level supported by the installed driver.
- PyTorch binary wheels provide their own CUDA runtime.
- C2 must record both the driver-reported CUDA level and `torch.version.cuda`.
- C2 must not require installation of the full system CUDA Toolkit unless a later contract explicitly introduces locally compiled CUDA extensions.

The selected PyTorch wheel must support the RTX 5070 architecture. The runtime verification must confirm the detected CUDA capability and successfully execute a real CUDA tensor operation. Do not treat `torch.cuda.is_available() == True` alone as sufficient proof.

## 4. Scope

### 4.1 In scope

C2 must define and implement:

- a dedicated project environment workflow;
- project dependency groups for core, development, and optional GPU dependencies;
- a reproducible installation procedure;
- environment diagnostics;
- CPU/GPU device selection;
- CUDA runtime verification;
- deterministic seed handling;
- reproducibility metadata capture;
- a minimal compute smoke test;
- a minimal memory cleanup check;
- CPU fallback behaviour;
- test markers for GPU-dependent tests;
- clear documentation for installation, verification, upgrades, and troubleshooting;
- an environment manifest/report generated from the live runtime;
- a C2 delivery and acceptance report.

### 4.2 Explicitly out of scope

C2 must not implement:

- technical indicators;
- price, volume, market, cross-sectional, or fundamental features;
- feature tables;
- labels or prediction targets;
- train/validation/test splits;
- walk-forward evaluation;
- model classes or model training;
- hyperparameter search;
- predictions;
- trading signals;
- portfolio construction;
- transaction-cost modelling;
- backtesting;
- profitability claims;
- writes to `psx_watcher.db`;
- changes to `psx-stock-watcher`.

Small random tensors created only to verify CPU/CUDA execution are allowed and are not considered model implementation.

## 5. Required repository changes

The implementation should add or update a structure similar to:

```text
psx-ml-research/
├── README.md
├── pyproject.toml
├── config/
│   └── runtime.example.toml
├── contracts/
│   └── C2_REPRODUCIBLE_ML_ENVIRONMENT/
│       └── CONTRACT.md
├── src/
│   └── psx_ml/
│       └── runtime/
│           ├── __init__.py
│           ├── device.py
│           ├── diagnostics.py
│           ├── metadata.py
│           └── reproducibility.py
├── tests/
│   ├── test_runtime_device.py
│   ├── test_runtime_diagnostics.py
│   ├── test_runtime_metadata.py
│   ├── test_runtime_reproducibility.py
│   └── test_runtime_source_safety.py
└── artifacts/
    └── reports/
        ├── C2_ENVIRONMENT_REPORT.md
        └── C2_DELIVERY.md
```

Equivalent naming is acceptable if responsibilities remain clearly separated.

## 6. Dependency and packaging requirements

### 6.1 Project installation

The project must continue to use a proper `src/` layout and must be installable with:

```bash
python -m pip install -e .
```

After installation, this must work without setting `PYTHONPATH`:

```bash
python -c "import psx_ml; print(psx_ml.__file__)"
```

Tests must not modify `sys.path` to make imports work.

### 6.2 Dependency groups

`pyproject.toml` should distinguish at least:

- core runtime dependencies;
- development/test dependencies;
- optional ML/GPU dependencies where practical.

Do not add large libraries merely because they may be useful later. C2 should remain narrow.

Expected dependencies may include:

```text
pytest
numpy
pyarrow
PyYAML or tomllib-compatible configuration support if needed
torch
```

`torchvision` is not required unless the implementation has a concrete runtime need. `torchaudio` is out of scope.

### 6.3 Version capture versus rigid pinning

C2 must capture exact installed versions in generated environment metadata.

The repository should avoid pretending that a single platform-specific PyTorch wheel declaration is portable across all machines. The documented installation flow may separate:

1. normal project installation; and
2. CUDA-specific PyTorch installation from the official PyTorch wheel index.

Any pinned or constrained versions must be justified in the contract delivery report.

## 7. Runtime configuration

Provide a small runtime configuration with at least:

```toml
[runtime]
device = "auto"          # auto | cpu | cuda
seed = 42
deterministic = true
allow_tf32 = false
```

Requirements:

- `auto` selects CUDA only when CUDA is available and passes basic initialization.
- `cpu` must never initialize work on CUDA.
- `cuda` must fail clearly if CUDA is unavailable; it must not silently fall back to CPU.
- Invalid device values must raise a clear configuration error.
- Configuration parsing must not read or alter the production database.
- Defaults must be documented.

## 8. Device-selection API

Implement a reusable API, for example:

```python
resolve_device(requested: str) -> torch.device
```

Required behaviour:

| Requested value | CUDA available | Required result |
|---|---:|---|
| `auto` | yes | CUDA device |
| `auto` | no | CPU device |
| `cpu` | yes/no | CPU device |
| `cuda` | yes | CUDA device |
| `cuda` | no | explicit error |
| invalid value | any | explicit error |

Do not cache a device decision in a way that makes tests dependent on execution order.

## 9. Environment diagnostics

Implement a command such as:

```bash
python -m psx_ml.runtime.diagnostics
```

or an equivalent console script such as:

```bash
psx-ml-env-report
```

The diagnostic output must include at least:

```text
UTC timestamp
Python version
Python executable
platform and operating system
project version or Git commit
active environment name when detectable
NumPy version
PyArrow version
PyTorch version
PyTorch CUDA runtime version
CUDA availability
selected/default device
GPU count
GPU name
GPU capability
architectures included in the PyTorch wheel when exposed
NVIDIA driver version when obtainable without fragile parsing
GPU total memory
reproducibility settings
TF32 setting
```

The command must work on CPU-only systems. GPU-only fields may be `null`, `not available`, or omitted with an explicit reason.

The command should support a machine-readable output form, preferably JSON:

```bash
python -m psx_ml.runtime.diagnostics --json
```

## 10. CUDA verification

C2 must implement a real CUDA smoke test when CUDA is available.

At minimum it must:

1. allocate deterministic input tensors;
2. run a nontrivial operation on the GPU, such as matrix multiplication;
3. synchronize the CUDA device before declaring success;
4. compute an equivalent CPU result;
5. compare CPU and GPU results using documented numerical tolerances;
6. record the result device and tensor shape;
7. release references and clear cached memory where appropriate;
8. confirm the process does not leave an unexpectedly large persistent allocation.

Do not require bit-for-bit equality between CPU and GPU floating-point results.

For the verified RTX 5070 machine, acceptance evidence must record:

```text
CUDA available: true
GPU name: contains RTX 5070
CUDA capability: reported by PyTorch
actual CUDA tensor operation: PASS
CPU/GPU result comparison: PASS
```

The contract does not hard-code a capability value as the only valid architecture because PyTorch reporting and future hardware may differ. The live report must record the actual value.

## 11. Reproducibility controls

Provide a reusable function, for example:

```python
configure_reproducibility(
    seed: int,
    deterministic: bool = True,
    allow_tf32: bool = False,
) -> ReproducibilityState
```

It must seed, where applicable:

- Python's `random` module;
- NumPy;
- PyTorch CPU;
- PyTorch CUDA devices when available.

When deterministic mode is requested, configure PyTorch deterministic behaviour using supported public APIs. The implementation must clearly document that deterministic settings improve repeatability but do not guarantee identical results across different PyTorch releases, platforms, drivers, devices, or algorithms.

TF32 behaviour must be explicit. Default it to disabled for the initial research baseline unless C2 delivery documents and justifies another choice.

Tests must prove that resetting the same seed reproduces the same test tensors within the same environment.

## 12. Metadata and provenance

Generate a small, version-controlled example/schema and a live environment report.

A machine-readable environment manifest should record at least:

```json
{
  "manifest_version": 1,
  "generated_at_utc": "<ISO-8601 UTC>",
  "git_commit": "<Git SHA or explicit dirty/unavailable state>",
  "python": {
    "version": "<version>",
    "executable": "<path>"
  },
  "platform": {
    "system": "<system>",
    "release": "<release>",
    "machine": "<architecture>"
  },
  "environment": {
    "name": "<environment name or null>"
  },
  "packages": {
    "numpy": "<version>",
    "pyarrow": "<version>",
    "torch": "<version>"
  },
  "cuda": {
    "available": true,
    "torch_runtime": "<torch.version.cuda>",
    "driver_version": "<driver or null>",
    "device_count": 1,
    "devices": [
      {
        "index": 0,
        "name": "<GPU name>",
        "capability": [12, 0],
        "total_memory_bytes": "<integer>"
      }
    ]
  },
  "reproducibility": {
    "seed": 42,
    "deterministic": true,
    "allow_tf32": false
  }
}
```

The capability shown above is illustrative. The generated manifest must use the live value.

Generated reports must not contain secrets, access tokens, complete environment-variable dumps, or unrelated personal paths beyond paths necessary to explain the active Python runtime and repository.

## 13. Source-data safety

C2 must preserve all C1 safety boundaries.

Tests must prove that:

- runtime diagnostics do not open `psx_watcher.db`;
- reproducibility utilities do not open `psx_watcher.db`;
- CUDA smoke tests do not open `psx_watcher.db`;
- no C2 test writes into `psx-stock-watcher`;
- C2 tests use temporary directories for generated output;
- no source database, watcher file, or watcher Git state changes during C2 acceptance.

A before/after production fingerprint should be included in the C2 delivery report if live acceptance is run on the same machine as the source repository:

```text
source database SHA-256
source database size
source database mtime
watcher Git HEAD
watcher porcelain status
```

If the production source is not mounted during a C2-only test run, the test/report must say so rather than fabricate a fingerprint.

## 14. Git and artifact policy

### 14.1 Must be committed

Commit:

- C2 contract;
- source code;
- tests;
- configuration examples;
- environment manifest schema/example;
- Markdown environment report;
- C2 delivery report;
- dependency declarations;
- documentation.

### 14.2 Must not be committed

Exclude:

- Conda environments;
- virtual environments;
- downloaded PyTorch wheels;
- pip/Conda caches;
- CUDA caches;
- compiled extension caches;
- large binary reports;
- generated model files;
- notebooks with large embedded outputs;
- local secrets;
- local `.env` files;
- production databases;
- copied watcher data.

Relevant ignore patterns should include or cover:

```gitignore
.venv/
venv/
.env
*.db
*.sqlite
*.sqlite3
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.ipynb_checkpoints/
artifacts/models/
data/cache/
data/processed/
*.pt
*.pth
*.ckpt
```

Do not ignore the small Markdown and JSON acceptance/provenance reports intended for version control.

## 15. Documentation requirements

Update `README.md` or add focused documentation covering:

1. creating the dedicated Conda environment;
2. activating it;
3. installing the repository in editable mode;
4. installing the official CUDA-enabled PyTorch wheel;
5. verifying imports;
6. running the environment diagnostic;
7. running CPU-only tests;
8. running GPU tests;
9. interpreting `nvidia-smi` CUDA versus `torch.version.cuda`;
10. selecting `auto`, `cpu`, or `cuda`;
11. recovering from installation in the wrong Conda environment;
12. upgrading PyTorch deliberately rather than incidentally.

The primary supported setup instructions should begin with environment creation, before any package installation.

Example ordering:

```bash
conda create -n psx-ml-research python=3.12 -y
conda activate psx-ml-research
cd ~/psx-ml-research
python -m pip install --upgrade pip
python -m pip install -e .
# Install the selected official CUDA-enabled PyTorch wheel next.
```

## 16. Test strategy

### 16.1 CPU-safe default suite

The normal test suite must run on a CPU-only machine without failing merely because CUDA is absent:

```bash
python -m pytest -q
```

GPU-specific tests should skip with a clear reason when CUDA is unavailable.

### 16.2 GPU test marker

Register a marker such as:

```ini
markers =
    gpu: requires a working CUDA-capable PyTorch runtime
```

Allow explicit GPU validation with a command such as:

```bash
python -m pytest -q -m gpu
```

The delivery report must include results from both the full suite and the explicit GPU suite on the RTX 5070 machine.

### 16.3 Test isolation

All tests that write reports or metadata must use `tmp_path` or another temporary location. Tests must not depend on files generated by a prior test run.

## 17. Acceptance tests

C2 is accepted only when all applicable tests below pass.

### AT-C2-01 — Dedicated environment identity

**Given** the `psx-ml-research` Conda environment is active  
**When** environment diagnostics run  
**Then** the Python executable and detected environment identify the dedicated project environment rather than `stockwicks-local`.

### AT-C2-02 — Editable project installation

**Given** a fresh dedicated environment  
**When** the documented installation procedure is followed  
**Then** `import psx_ml` succeeds without `PYTHONPATH` changes or test-side path manipulation.

### AT-C2-03 — Required dependency imports

**When** the environment is installed  
**Then** NumPy, PyArrow, pytest, and PyTorch import successfully and their versions are reportable.

### AT-C2-04 — CPU device selection

**Given** `device = "cpu"`  
**When** the device resolver runs  
**Then** it returns a CPU device even when CUDA is available.

### AT-C2-05 — Automatic device selection

**Given** `device = "auto"`  
**When** CUDA is usable  
**Then** CUDA is selected; otherwise CPU is selected.

### AT-C2-06 — Explicit CUDA failure

**Given** `device = "cuda"`  
**When** CUDA is unavailable or initialization fails  
**Then** the resolver raises a clear error and does not silently use CPU.

### AT-C2-07 — Invalid device rejection

**Given** an unsupported device value  
**When** configuration is loaded  
**Then** a clear validation error is raised.

### AT-C2-08 — RTX 5070 discovery

**On the target development machine**, diagnostics must report:

- CUDA available;
- one or more CUDA devices;
- a GPU name containing `RTX 5070`;
- the capability reported by PyTorch;
- total GPU memory;
- the PyTorch CUDA runtime version.

### AT-C2-09 — Actual CUDA computation

**Given** a working CUDA runtime  
**When** the smoke test executes  
**Then** a nontrivial tensor operation completes on CUDA, synchronization succeeds, and the output resides on the CUDA device.

### AT-C2-10 — CPU/GPU numerical reconciliation

**Given** deterministic input tensors  
**When** equivalent CPU and GPU operations run  
**Then** their results agree within a documented tolerance.

### AT-C2-11 — GPU memory cleanup

**When** the CUDA smoke test releases its tensors and performs documented cleanup  
**Then** allocated memory returns near the pre-test baseline within a reasonable tolerance. The test must avoid brittle expectations about framework-reserved cache memory.

### AT-C2-12 — Seed reproducibility

**Given** the same seed and runtime configuration  
**When** Python, NumPy, and PyTorch test values are generated twice after reseeding  
**Then** the corresponding values match within the same environment.

### AT-C2-13 — Different seeds differ

**Given** two different seeds  
**When** test tensors are generated  
**Then** they are not identical, preventing a false-positive reproducibility test.

### AT-C2-14 — Deterministic configuration reporting

**When** reproducibility is configured  
**Then** diagnostics and the environment manifest record the requested seed, deterministic mode, and TF32 policy.

### AT-C2-15 — CPU-only compatibility

**Given** CUDA is hidden or mocked unavailable  
**When** the default test suite and environment diagnostics run  
**Then** they complete successfully, GPU tests skip clearly, and CPU mode remains functional.

A subprocess test may use:

```bash
CUDA_VISIBLE_DEVICES="" python -m pytest -q <relevant-tests>
```

provided this is reliable in the target environment.

### AT-C2-16 — Machine-readable diagnostics

**When** diagnostics run with JSON output  
**Then** valid JSON is produced and contains all mandatory metadata fields with stable field names.

### AT-C2-17 — No secret leakage

**When** the environment report is generated  
**Then** it does not dump arbitrary environment variables, tokens, credentials, or unrelated secrets.

### AT-C2-18 — Temporary output isolation

**When** tests generate reports or manifests  
**Then** output is written only beneath temporary test directories and does not alter tracked acceptance artifacts.

### AT-C2-19 — Production source safety

**When** the complete C2 suite and live diagnostic are run  
**Then** no source database or watcher repository file is opened for writing or modified.

Where live source fingerprints are available, before/after values must match.

### AT-C2-20 — No premature research implementation

**When** the C2 diff is reviewed  
**Then** it contains no indicators, features, targets, training routines, predictions, strategies, or backtests.

### AT-C2-21 — Documentation ordering

**When** a new user follows the setup guide  
**Then** the dedicated environment is created and activated before any project or PyTorch package installation.

### AT-C2-22 — Clean Git state and branch isolation

**When** C2 is delivered  
**Then**:

- implementation exists on `feature/c2-reproducible-ml-environment`;
- the branch is based on accepted C1 `main`;
- `psx-stock-watcher` is unchanged;
- the pending C14 branch is untouched;
- generated caches and binary artifacts are not tracked.

## 18. Suggested acceptance commands

```bash
conda activate psx-ml-research
cd ~/psx-ml-research

which python
python --version
python -m pip --version
python -c "import psx_ml; print(psx_ml.__file__)"

python -m psx_ml.runtime.diagnostics
python -m psx_ml.runtime.diagnostics --json

python -m pytest -q
python -m pytest -q -m gpu

git status --short
git log -1 --oneline
```

A CPU fallback acceptance run should also be included, for example:

```bash
CUDA_VISIBLE_DEVICES="" python -m pytest -q -m "not gpu"
```

## 19. Required reports

### 19.1 Environment report

Create:

```text
artifacts/reports/C2_ENVIRONMENT_REPORT.md
```

It must contain:

- host/runtime summary;
- exact package versions;
- GPU and CUDA details;
- selected installation method;
- CPU smoke-test result;
- GPU smoke-test result;
- reproducibility settings;
- known limitations;
- commands used to reproduce the checks.

### 19.2 Delivery report

Create:

```text
contracts/C02-DELIVERY.md
```

It must contain:

- delivery summary;
- branch and commit;
- files added or changed;
- dependency decisions;
- acceptance-test mapping and results;
- CPU-only test evidence;
- RTX 5070 GPU test evidence;
- source-safety evidence;
- deviations from this contract;
- explicit statement that C2 introduced no features, targets, models, predictions, or backtests;
- acceptance recommendation.

## 20. Implementation sequence

Implement in this order:

1. Confirm C1 is merged and the working tree is clean.
2. Create `feature/c2-reproducible-ml-environment` from accepted `main`.
3. Add this contract.
4. Review `pyproject.toml` and dependency boundaries.
5. Implement runtime configuration and device resolution.
6. Implement reproducibility controls.
7. Implement diagnostics and JSON metadata output.
8. Implement CPU smoke tests.
9. Implement optional/skippable GPU tests.
10. Run live RTX 5070 acceptance.
11. Run CPU-fallback acceptance.
12. Verify production source and watcher safety.
13. Generate the environment and delivery reports.
14. Commit and push the feature branch.
15. Do not merge until C2 is reviewed and accepted.

## 21. Completion boundary

C2 ends when the project has a verified, documented, isolated, CPU/GPU-capable and reproducible runtime.

The next contract may begin feature and target research, but C2 must not do so.
