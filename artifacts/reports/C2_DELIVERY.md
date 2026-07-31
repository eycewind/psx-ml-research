# C2 Delivery and Acceptance Report

## Delivery summary

C2 delivers an isolated, editable, CPU/CUDA-capable runtime with validated
device selection, deterministic seed controls, JSON diagnostics, environment
provenance, real compute smoke testing, CUDA cleanup checks, CPU fallback, and
GPU-marked tests. It is implemented on
`feature/c2-reproducible-ml-environment`; implementation commit is `181dc61`.

Changed areas: `pyproject.toml`, setup documentation, runtime configuration,
`psx_ml.runtime`, C2 tests, the formal contract and manifest example, ignore
policy, and C2 reports.

## Dependency decisions

- Core: NumPy and PyArrow, constrained only to compatible major/ranges.
- Development: pytest.
- Optional ML: PyTorch. CUDA installation is documented separately through the
  official PyTorch wheel index because a platform-specific CUDA wheel is not a
  portable project dependency.
- `torchvision`, `torchaudio`, and the system CUDA Toolkit were not added.
- Exact live versions are captured in the environment manifest instead of
  pretending a single lock applies across CPU/GPU platforms.

## Acceptance mapping

| Contract tests | Evidence |
|---|---|
| AT-C2-01–03 environment/install/imports | Dedicated Conda environment; editable import resolves to this repository; required versions recorded |
| AT-C2-04–07 device resolution/errors | Unit tests cover CPU, auto, explicit CUDA failure, and invalid values |
| AT-C2-08–11 RTX compute/accuracy/cleanup | RTX 5070 detected; capability 12.0; real CUDA matmul passes; maximum error 4.96e-05; post-cleanup allocation bounded |
| AT-C2-12–14 seeds/reporting | Same seeds reproduce Python/NumPy/PyTorch; different seeds differ; deterministic/TF32 policy reported |
| AT-C2-15 CPU compatibility | 18 tests pass with `CUDA_VISIBLE_DEVICES=""`; GPU test excluded/skippable |
| AT-C2-16–18 JSON/secrets/temp outputs | Stable JSON schema; no environment dump; test reports use `tmp_path` |
| AT-C2-19 source safety | Runtime SQLite-connect canary passes; live fingerprints unchanged |
| AT-C2-20–22 scope/docs/Git | No research implementation; environment-first docs; isolated C2 branch and ignored binary caches |

Full live results:

```text
19 passed in 3.51s
1 passed, 18 deselected in 1.35s       # explicit GPU suite
18 passed, 1 deselected in 3.08s       # CUDA hidden, non-GPU suite
18 passed, 1 skipped in 3.17s          # CUDA hidden, complete default suite
```

## Production safety evidence

Before and after C2 acceptance:

```text
source DB SHA-256: e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b
source DB size: 304885760
source DB mtime: 1785003631
watcher HEAD: 404e3637637ca89d4455b9f7069c6191a3658d83
watcher porcelain status: <empty>
```

No runtime module accepts a source-database path or imports the C1 SQLite access
layer. A test monkeypatches `sqlite3.connect` and proves diagnostics and
reproducibility make zero SQLite calls.

## Deviations and judgments

- The dedicated Conda environment and correct CUDA-enabled PyTorch build already
  existed, so C2 retained them instead of recreating or replacing working state.
- Initial pytest runs with output capture enabled failed during teardown because
  the execution host removed pytest's capture temporary file. Capture-disabled
  runs (`-s`) exercised the same tests and passed; this was an environment I/O
  issue, not a product-test failure.
- A proposed 1 MiB CUDA cleanup tolerance was rejected by live evidence: cuBLAS/
  PyTorch retained 8,519,680 allocated bytes after tensor deletion and cache
  cleanup. The canary uses a documented 16 MiB allowance, still low enough to
  catch retained 256×256 test tensors or repeated growth without asserting that
  CUDA context memory disappears.
- `torch>=2.8` is an optional portable declaration; the verified live wheel is
  installed explicitly from the CUDA 12.8 index and reported exactly.

## Scope statement and recommendation

C2 introduced no indicators, features, targets, splits, model classes, model
training, predictions, signals, strategies, transaction-cost logic, or
backtests. The watcher C14 branch was not modified or interacted with.

C2 is recommended for acceptance after review. It must not be merged before
that review.
