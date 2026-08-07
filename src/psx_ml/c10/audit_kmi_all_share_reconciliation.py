from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

BASELINE = Path(
    "data/reference/"
    "kmi_all_share_baseline_2022_01_03.csv"
)
CHANGES = Path(
    "data/reference/kmi_all_share_sources/"
    "parsed_change_tables/all_changes.csv"
)
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_RECONCILIATION_AUDIT.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_RECONCILIATION_AUDIT.json"
)

OFFICIAL_COUNTS = {
    "2022-01-03": 250,
    "2022-07-15": 252,
    "2023-01-12": 261,
    "2023-07-10": 251,
    "2023-12-26": 258,
    "2024-06-25": 255,
    "2025-01-03": 264,
    "2025-06-10": 257,
    "2025-12-02": 281,
}

SKIP_SOURCE_IDS = {
    # Already incorporated into the authoritative
    # 2022-01-03 baseline.
    "review_2021_h1",
}


def main() -> None:
    baseline = pd.read_csv(BASELINE)
    changes = pd.read_csv(CHANGES)

    members = set(
        baseline["symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if len(members) != 250:
        raise ValueError(
            f"Baseline must contain 250 unique symbols; "
            f"found {len(members)}"
        )

    rows = [
        {
            "source_id": "baseline",
            "effective_from": "2022-01-03",
            "starting_count": None,
            "incoming_count": 0,
            "outgoing_count": 0,
            "missing_outgoing_count": 0,
            "already_present_incoming_count": 0,
            "computed_count": len(members),
            "official_count": OFFICIAL_COUNTS[
                "2022-01-03"
            ],
            "count_gap": (
                len(members)
                - OFFICIAL_COUNTS["2022-01-03"]
            ),
            "missing_outgoing_symbols": [],
            "already_present_incoming_symbols": [],
        }
    ]

    ordered = (
        changes.assign(
            effective_from=pd.to_datetime(
                changes["effective_from"]
            )
        )
        .sort_values(
            [
                "effective_from",
                "source_id",
                "sequence",
            ]
        )
    )

    for source_id, group in ordered.groupby(
        "source_id",
        sort=False,
    ):
        if source_id in SKIP_SOURCE_IDS:
            continue

        effective = (
            group["effective_from"]
            .iloc[0]
            .date()
            .isoformat()
        )
        incoming = {
            str(value).strip().upper()
            for value in group[
                "incoming_symbol"
            ].dropna()
            if str(value).strip()
        }
        outgoing = {
            str(value).strip().upper()
            for value in group[
                "outgoing_symbol"
            ].dropna()
            if str(value).strip()
        }

        starting_count = len(members)
        missing_outgoing = sorted(
            outgoing - members
        )
        already_present_incoming = sorted(
            incoming & members
        )

        members = (
            members - outgoing
        ) | incoming

        official_count = OFFICIAL_COUNTS.get(
            effective
        )
        computed_count = len(members)

        rows.append(
            {
                "source_id": source_id,
                "effective_from": effective,
                "starting_count": starting_count,
                "incoming_count": len(incoming),
                "outgoing_count": len(outgoing),
                "missing_outgoing_count": len(
                    missing_outgoing
                ),
                "already_present_incoming_count": len(
                    already_present_incoming
                ),
                "computed_count": computed_count,
                "official_count": official_count,
                "count_gap": (
                    None
                    if official_count is None
                    else computed_count
                    - official_count
                ),
                "missing_outgoing_symbols": (
                    missing_outgoing
                ),
                "already_present_incoming_symbols": (
                    already_present_incoming
                ),
            }
        )

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "# C10 CP4B — KMI All Share Reconciliation Audit",
        "",
        "This audit applies official incoming/outgoing tables "
        "to the accepted 2022 baseline. It intentionally "
        "does not write final membership history.",
        "",
        "| Effective | Source | Start | Incoming | Outgoing | "
        "Computed | Official | Gap | Missing outgoing | "
        "Already-present incoming |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| "
            f"{row['effective_from']} | "
            f"{row['source_id']} | "
            f"{row['starting_count']} | "
            f"{row['incoming_count']} | "
            f"{row['outgoing_count']} | "
            f"{row['computed_count']} | "
            f"{row['official_count']} | "
            f"{row['count_gap']} | "
            f"{row['missing_outgoing_count']} | "
            f"{row['already_present_incoming_count']} |"
        )

    lines.extend(
        [
            "",
            "## Exceptions requiring source reconciliation",
            "",
        ]
    )

    for row in rows:
        problems = []
        if row["count_gap"] not in (0, None):
            problems.append(
                f"count gap {row['count_gap']:+d}"
            )
        if row["missing_outgoing_symbols"]:
            problems.append(
                "missing outgoing: "
                + ", ".join(
                    row[
                        "missing_outgoing_symbols"
                    ]
                )
            )
        if row[
            "already_present_incoming_symbols"
        ]:
            problems.append(
                "already present incoming: "
                + ", ".join(
                    row[
                        "already_present_incoming_symbols"
                    ]
                )
            )

        if problems:
            lines.append(
                f"- {row['effective_from']} "
                f"({row['source_id']}): "
                + "; ".join(problems)
            )

    lines.extend(
        [
            "",
            "## Stop condition",
            "",
            "Do not create final membership intervals while "
            "any official-count gap or impossible outgoing "
            "symbol remains unresolved.",
            "",
        ]
    )

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            {
                "checkpoint": (
                    "C10-CP4B-1-reconciliation-audit"
                ),
                "holdout_accessed": False,
                "records": rows,
                "final_computed_members": sorted(
                    members
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("\n".join(lines))
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
