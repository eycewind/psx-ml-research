from __future__ import annotations

import hashlib
import json
from pathlib import Path

from psx_ml.c10.inputs import (
    C9_SELECTIONS_PATH,
    FEATURE_PATH,
    PRICE_PATH,
    audit_frame,
    load_c9_selections,
    load_execution_prices,
    load_liquidity_features,
)
from psx_ml.c10.policies import FROZEN_POLICIES
from psx_ml.c10.prices import map_next_session_entries


REPORT_DIR = Path("artifacts/reports")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    selections = load_c9_selections()
    maximum_source_date = selections["trade_date"].max()

    prices = load_execution_prices(
        maximum_date=maximum_source_date,
    )

    liquidity = load_liquidity_features(
        maximum_date=maximum_source_date,
    )

    mapped = map_next_session_entries(
        selections,
        prices,
    )

    selection_audit = audit_frame(
        selections,
        path=C9_SELECTIONS_PATH,
        key_columns=(
            "policy_id",
            "trade_date",
            "symbol",
        ),
    )

    price_audit = audit_frame(
        prices,
        path=PRICE_PATH,
    )

    liquidity_audit = audit_frame(
        liquidity,
        path=FEATURE_PATH,
    )

    availability = (
        mapped.groupby("policy_id", dropna=False)
        .agg(
            selection_rows=("symbol", "size"),
            available_entries=("entry_available", "sum"),
            missing_entries=(
                "entry_available",
                lambda values: int((~values).sum()),
            ),
            selection_dates=("trade_date", "nunique"),
            symbols=("symbol", "nunique"),
        )
        .reset_index()
    )

    availability["availability_rate"] = (
        availability["available_entries"]
        / availability["selection_rows"]
    )

    missing_reasons = (
        mapped.loc[~mapped["entry_available"]]
        .groupby(
            ["policy_id", "entry_missing_reason"],
            dropna=False,
        )
        .size()
        .reset_index(name="rows")
    )

    frozen_policies_json = json.dumps(
        {
            key: value.to_dict()
            for key, value in FROZEN_POLICIES.items()
        },
        indent=2,
    )

    input_report = f"""# C10 Input Audit

## Frozen policies

```json
{frozen_policies_json}
```

## C9 selections

- Path: `{selection_audit.path}`
- Rows: `{selection_audit.rows}`
- Symbols: `{selection_audit.symbols}`
- Minimum date: `{selection_audit.min_date}`
- Maximum date: `{selection_audit.max_date}`
- Holdout rows: `{selection_audit.holdout_rows}`
- Duplicate date-symbol keys: `{selection_audit.duplicate_keys}`

## Liquidity features

- Path: `{liquidity_audit.path}`
- Rows: `{liquidity_audit.rows}`
- Symbols: `{liquidity_audit.symbols}`
- Minimum date: `{liquidity_audit.min_date}`
- Maximum date: `{liquidity_audit.max_date}`
- Holdout rows: `{liquidity_audit.holdout_rows}`
- Duplicate date-symbol keys: `{liquidity_audit.duplicate_keys}`

The 2026 final holdout remained inaccessible.
"""

    if len(missing_reasons):
        missing_reason_text = missing_reasons.to_markdown(index=False)
    else:
        missing_reason_text = "No missing entries."

    price_report = f"""# C10 Price Audit

## Source

- Path: `{price_audit.path}`
- Rows loaded after holdout restriction: `{price_audit.rows}`
- Symbols: `{price_audit.symbols}`
- Minimum date: `{price_audit.min_date}`
- Maximum date: `{price_audit.max_date}`
- Holdout rows: `{price_audit.holdout_rows}`
- Duplicate date-symbol keys: `{price_audit.duplicate_keys}`

## Canonical price basis

- Entry: next valid market session `open_adj`
- Daily valuation: `close_adj`
- Volume: `volume_adj`
- Adjustment identity: `adj_factor`

Raw and adjusted OHLC columns both exist in the source, but C10 uses the adjusted basis consistently.

## Entry availability

{availability.to_markdown(index=False)}

## Missing-entry reasons

{missing_reason_text}
"""

    manifest = {
        "contract": "C10",
        "checkpoint": 1,
        "holdout_accessed": False,
        "inputs": {
            str(C9_SELECTIONS_PATH): sha256_file(
                C9_SELECTIONS_PATH
            ),
            str(PRICE_PATH): sha256_file(PRICE_PATH),
            str(FEATURE_PATH): sha256_file(FEATURE_PATH),
        },
        "selection_audit": selection_audit.__dict__,
        "price_audit": price_audit.__dict__,
        "liquidity_audit": liquidity_audit.__dict__,
        "entry_availability": availability.to_dict(
            orient="records"
        ),
        "missing_reasons": missing_reasons.to_dict(
            orient="records"
        ),
        "canonical_price_basis": {
            "entry": "next_session_open_adj",
            "valuation": "close_adj",
            "volume": "volume_adj",
        },
    }

    delivery = """# C10 Checkpoint 1 Delivery

Status: **COMPLETE**

Checkpoint 1 established:

- frozen C9 P1 and P2 policy identities;
- authoritative C9 candidate-selection input;
- adjusted next-session open execution basis;
- adjusted close valuation basis;
- point-in-time liquidity inputs;
- explicit next-session entry availability;
- explicit missing-entry reasons;
- final 2026 holdout protection.

Portfolio construction, transaction costs and profitability were not evaluated in this checkpoint.
"""

    (REPORT_DIR / "C10_INPUT_AUDIT.md").write_text(
        input_report,
        encoding="utf-8",
    )

    (REPORT_DIR / "C10_PRICE_AUDIT.md").write_text(
        price_report,
        encoding="utf-8",
    )

    (
        REPORT_DIR / "C10_CHECKPOINT1_MANIFEST.json"
    ).write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    (
        REPORT_DIR / "C10_CHECKPOINT1_DELIVERY.md"
    ).write_text(
        delivery,
        encoding="utf-8",
    )

    print(availability.to_string(index=False))

    if len(missing_reasons):
        print("\nMissing reasons:")
        print(missing_reasons.to_string(index=False))


if __name__ == "__main__":
    main()
