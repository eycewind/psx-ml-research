# PSX daily data source

## Production source

The immutable input is
`/home/hassan/psx-stock-watcher/data/psx_watcher.db`. It is an SQLite database
owned by the production watcher. Research opens it only through
`psx_ml.data.sqlite.connect_readonly`, which uses URI `mode=ro` and then enables
`PRAGMA query_only=ON`.

The source repository was inspected at Git commit
`404e3637637ca89d4455b9f7069c6191a3658d83` on branch
`c14-dynamic-kmi30-ss-alerts`. No branch operation or file mutation was made.

## Canonical daily dataset

Live schema and representative-row inspection confirms `daily_ohlc`, whose
primary key is `(trade_date, symbol)`. At inspection it had 621,794 rows, 821
symbols, and 1,615 distinct dates from 2020-01-01 through 2026-07-10.

| Meaning | Canonical columns | Treatment |
|---|---|---|
| Raw daily OHLCV | `open`, `high`, `low`, `close`, `volume` | Retain unchanged |
| Adjusted OHLCV | `open_adj`, `high_adj`, `low_adj`, `close_adj`, `volume_adj` | Retain with integrity audit |
| Adjustment multiplier | `adj_factor` | Prices should equal raw × factor; volume raw ÷ factor |
| Context/provenance | `trade_date`, `symbol`, `sector`, `ldcp`, `open_missing`, `source` | Retain unchanged |

The adjusted series covers split/bonus adjustments but does not establish cash
dividend adjustment. Watcher documentation also records a large quarantine set
of unreliable adjusted symbols. C1 therefore exports both selections and never
silently treats adjusted prices as universally authoritative.

## Observed semantics and cautions

- `open IS NULL` with `open_missing=1` represents a missing opening print.
- Zero-volume rows were discarded by upstream ingestion. A missing symbol-date
  may mean no trading, pre-listing/post-delisting, suspension, or a data gap.
- `close` can be outside `[low, high]`. Watcher documentation infers this is due
  to the PSX closing auction; this remains a soft exception until verified from
  an authoritative PSX source.
- `open` outside `[low, high]`, `high < low`, and nonpositive high/low/close are
  audited as impossible/suspect relationships rather than repaired.
- `universe` is a current/as-of-classification table and cannot be applied to
  earlier history. C1 does not use it for PIT eligibility.
- `tradeable_universe`, `indicators`, `signals`, and `forward_outcomes` are
  derived watcher research artifacts and are not C1 extraction inputs.

The full live schema snapshot is generated locally as
`artifacts/reports/C1_SCHEMA.json`; it is excluded from Git because it is a
generated report. The reviewed schema contract is recorded here and in C1's
contract.
