from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from psx_ml.c10.build_kmi_all_share_baseline_2022 import (
    extract_compliant_rows,
)

SOURCE_AUDIT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SOURCE_AUDIT.json"
)
CSV_OUTPUT = Path(
    "data/reference/"
    "kmi_all_share_screened_universe_history.csv"
)
PARQUET_OUTPUT = Path(
    "data/reference/"
    "kmi_all_share_screened_universe_history.parquet"
)
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SCREENED_UNIVERSE_HISTORY.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SCREENED_UNIVERSE_HISTORY.json"
)

# Full official screening tables available in the source set.
SNAPSHOT_DATES = (
    "2022-01-03",
    "2023-01-12",
    "2023-12-26",
    "2024-06-25",
    "2025-01-03",
    "2025-12-02",
)

# Notice dates without a trustworthy full screening table.
CARRY_FORWARD_DATES = (
    "2022-07-15",
    "2023-07-10",
    "2025-06-10",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def write_parquet(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    table = pa.Table.from_pandas(
        frame,
        preserve_index=False,
    )
    with path.open("wb") as handle:
        pq.write_table(table, handle)


def normalize_symbols(values) -> list[str]:
    return sorted(
        {
            str(value).strip().upper()
            for value in values
            if str(value).strip()
        }
    )


def load_snapshots() -> dict[str, dict[str, object]]:
    audit = json.loads(
        SOURCE_AUDIT.read_text(encoding="utf-8")
    )

    by_date = {
        record["effective_from"]: record
        for record in audit["records"]
    }

    snapshots: dict[str, dict[str, object]] = {}

    baseline = extract_compliant_rows()
    snapshots["2022-01-03"] = {
        "symbols": normalize_symbols(
            baseline["symbol"]
        ),
        "membership_source": "official_full_screening_table",
        "membership_confidence": "high",
        "source_id": "review_2021_h1",
        "source_note": (
            "Directly parsed compliant rows from official PSX "
            "screening table; includes compliant defaulter rows "
            "because this artifact is a screening universe, not "
            "exact index membership."
        ),
    }

    for effective in SNAPSHOT_DATES[1:]:
        record = by_date.get(effective)
        if record is None:
            raise ValueError(
                f"Missing source-audit record for {effective}"
            )

        symbols = normalize_symbols(
            record.get(
                "parsed_compliant_symbols",
                [],
            )
        )
        if not symbols:
            raise ValueError(
                f"No parsed compliant symbols for {effective}"
            )

        snapshots[effective] = {
            "symbols": symbols,
            "membership_source": "official_full_screening_table",
            "membership_confidence": "medium",
            "source_id": record["source_id"],
            "source_note": (
                "Directly parsed compliant rows from official PSX "
                "screening table. Exact index membership may differ "
                "because defaulter formatting and other exclusions "
                "are not consistently machine-readable."
            ),
        }

    return snapshots


def main() -> None:
    snapshots = load_snapshots()

    timeline = sorted(
        set(SNAPSHOT_DATES) | set(CARRY_FORWARD_DATES)
    )

    rows: list[dict[str, object]] = []
    current_snapshot_date: str | None = None

    for idx, effective in enumerate(timeline):
        if effective in snapshots:
            current_snapshot_date = effective
            snapshot = snapshots[effective]
            source = snapshot["membership_source"]
            confidence = snapshot["membership_confidence"]
            source_id = snapshot["source_id"]
            note = snapshot["source_note"]
        else:
            if current_snapshot_date is None:
                raise ValueError(
                    f"No prior snapshot for carry-forward date {effective}"
                )
            snapshot = snapshots[current_snapshot_date]
            source = "carried_forward_screening_snapshot"
            confidence = "low"
            source_id = snapshot["source_id"]
            note = (
                f"Carried forward from {current_snapshot_date}; "
                "no trustworthy full screening table was available "
                "for this notice date."
            )

        effective_to = (
            timeline[idx + 1]
            if idx + 1 < len(timeline)
            else None
        )

        for symbol in snapshot["symbols"]:
            rows.append(
                {
                    "symbol": symbol,
                    "effective_from": effective,
                    "effective_to": effective_to,
                    "screening_snapshot_date": current_snapshot_date,
                    "membership_source": source,
                    "membership_confidence": confidence,
                    "source_id": source_id,
                    "source_note": note,
                    "is_exact_index_membership": False,
                    "is_shariah_screened_eligible": True,
                }
            )

    frame = pd.DataFrame(rows)
    frame["effective_from"] = pd.to_datetime(
        frame["effective_from"]
    )
    frame["effective_to"] = pd.to_datetime(
        frame["effective_to"]
    )

    if frame.duplicated(
        ["symbol", "effective_from"]
    ).any():
        raise ValueError(
            "Duplicate symbol/effective_from rows"
        )

    if (
        frame["effective_from"].dt.year >= 2026
    ).any():
        raise ValueError("2026 data must not be used")

    counts = (
        frame.groupby(
            [
                "effective_from",
                "membership_source",
                "membership_confidence",
                "screening_snapshot_date",
            ],
            dropna=False,
        )["symbol"]
        .nunique()
        .reset_index(name="symbol_count")
    )

    CSV_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_frame = frame.copy()
    csv_frame["effective_from"] = (
        csv_frame["effective_from"]
        .dt.date.astype(str)
    )
    csv_frame["effective_to"] = (
        csv_frame["effective_to"]
        .dt.date.astype("string")
    )
    csv_frame.to_csv(
        CSV_OUTPUT,
        index=False,
    )
    write_parquet(
        frame,
        PARQUET_OUTPUT,
    )

    lines = [
        "# C10 CP4B — KMI All Share Screened Universe History",
        "",
        "This artifact is a point-in-time Shariah-screened universe, "
        "not an assertion of exact PSX-KMI All Share index membership.",
        "",
        "| Effective | Snapshot used | Symbols | Source | Confidence |",
        "|---|---|---:|---|---|",
    ]

    for row in counts.itertuples(index=False):
        lines.append(
            f"| {row.effective_from.date().isoformat()} | "
            f"{row.screening_snapshot_date} | "
            f"{row.symbol_count} | "
            f"{row.membership_source} | "
            f"{row.membership_confidence} |"
        )

    lines.extend(
        [
            "",
            "## Research policy",
            "",
            "- High/medium-confidence rows come from an official full "
            "screening table.",
            "- Low-confidence rows carry the latest full screening "
            "snapshot forward to a notice date that lacks a reliable "
            "full table.",
            "- Incoming/outgoing notices are not treated as complete "
            "event ledgers.",
            "- P5 results must be labelled as a screened-universe "
            "backtest and compared separately with strict KMI-30 P4.",
            "",
        ]
    )

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    manifest = {
        "checkpoint": (
            "C10-CP4B-2-screened-universe-history"
        ),
        "holdout_accessed": False,
        "definition": (
            "point-in-time official Shariah screening universe; "
            "not exact index membership"
        ),
        "interval_count": int(
            frame["effective_from"].nunique()
        ),
        "row_count": int(len(frame)),
        "counts": [
            {
                "effective_from": (
                    row.effective_from.date().isoformat()
                ),
                "screening_snapshot_date": (
                    row.screening_snapshot_date
                ),
                "symbol_count": int(row.symbol_count),
                "membership_source": (
                    row.membership_source
                ),
                "membership_confidence": (
                    row.membership_confidence
                ),
            }
            for row in counts.itertuples(index=False)
        ],
        "outputs": {
            str(CSV_OUTPUT): {
                "rows": int(len(frame)),
                "sha256": sha256(CSV_OUTPUT),
            },
            str(PARQUET_OUTPUT): {
                "rows": int(len(frame)),
                "sha256": sha256(PARQUET_OUTPUT),
            },
            str(REPORT): {
                "sha256": sha256(REPORT),
            },
        },
    }

    MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("\n".join(lines))
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
