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
SOURCE_AUDIT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SOURCE_AUDIT.json"
)
OUTPUT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_GAP_DIAGNOSIS.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_GAP_DIAGNOSIS.json"
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

# Known ticker-renaming / corporate-action candidates.
# These are diagnostics only. They are NOT applied automatically.
ALIAS_CANDIDATES = {
    "BYCO": "CNERGY",
    "ICI": "LCI",
    "ENGRO": "ENGROH",
}


def normalize(values) -> set[str]:
    return {
        str(value).strip().upper()
        for value in values
        if pd.notna(value)
        and str(value).strip()
    }


def main() -> None:
    baseline = pd.read_csv(BASELINE)
    changes = pd.read_csv(CHANGES)
    audit = json.loads(
        SOURCE_AUDIT.read_text(encoding="utf-8")
    )

    screening_by_effective = {
        record["effective_from"]: set(
            record.get(
                "parsed_compliant_symbols",
                [],
            )
        )
        for record in audit["records"]
    }

    members = normalize(baseline["symbol"])
    records = []

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
        if source_id == "review_2021_h1":
            continue

        effective = (
            group["effective_from"]
            .iloc[0]
            .date()
            .isoformat()
        )
        incoming = normalize(
            group["incoming_symbol"]
        )
        outgoing = normalize(
            group["outgoing_symbol"]
        )

        before = set(members)
        missing_outgoing = sorted(
            outgoing - before
        )

        after = (
            before - outgoing
        ) | incoming

        screening = screening_by_effective.get(
            effective,
            set(),
        )

        extra_vs_screening = sorted(
            after - screening
        )
        missing_vs_screening = sorted(
            screening - after
        )

        alias_hits = []
        for old, new in ALIAS_CANDIDATES.items():
            if old in before and new in outgoing:
                alias_hits.append(
                    f"{old}->{new} outgoing mismatch"
                )
            if old in after and new in screening:
                alias_hits.append(
                    f"{old}->{new} possible rename"
                )

        official = OFFICIAL_COUNTS[effective]

        records.append(
            {
                "source_id": source_id,
                "effective_from": effective,
                "computed_count": len(after),
                "official_count": official,
                "count_gap": len(after) - official,
                "missing_outgoing": missing_outgoing,
                "screening_count": len(screening),
                "extra_vs_screening": extra_vs_screening,
                "missing_vs_screening": (
                    missing_vs_screening
                ),
                "alias_candidates": alias_hits,
            }
        )

        members = after

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "# C10 CP4B — KMI All Share Gap Diagnosis",
        "",
        "This report diagnoses why simple chaining of "
        "incoming/outgoing tables does not reproduce "
        "the official constituent counts.",
        "",
        "| Effective | Computed | Official | Gap | "
        "Screening symbols | Extra vs screening | "
        "Missing vs screening |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for record in records:
        lines.append(
            "| "
            f"{record['effective_from']} | "
            f"{record['computed_count']} | "
            f"{record['official_count']} | "
            f"{record['count_gap']} | "
            f"{record['screening_count']} | "
            f"{len(record['extra_vs_screening'])} | "
            f"{len(record['missing_vs_screening'])} |"
        )

    lines.extend(
        [
            "",
            "## Detailed exceptions",
            "",
        ]
    )

    for record in records:
        lines.append(
            f"### {record['effective_from']} "
            f"({record['source_id']})"
        )
        lines.append("")
        lines.append(
            "- Missing outgoing symbols: "
            + (
                ", ".join(
                    record["missing_outgoing"]
                )
                or "none"
            )
        )
        lines.append(
            "- Computed members absent from screening list: "
            + (
                ", ".join(
                    record["extra_vs_screening"]
                )
                or "none"
            )
        )
        lines.append(
            "- Screening symbols absent from computed members: "
            + (
                ", ".join(
                    record["missing_vs_screening"]
                )
                or "none"
            )
        )
        lines.append(
            "- Alias/corporate-action candidates: "
            + (
                ", ".join(
                    record["alias_candidates"]
                )
                or "none"
            )
        )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "A non-zero gap means the official change table "
            "is not a complete event ledger. Delistings, "
            "defaulter-list changes, newly listed securities, "
            "ticker renames, mergers, and other corporate "
            "actions may be reflected in the official final "
            "count without appearing as ordinary incoming/"
            "outgoing rows.",
            "",
            "Do not force counts by deleting arbitrary symbols. "
            "Use this report to identify each unexplained event "
            "against the relevant official source.",
            "",
        ]
    )

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            {
                "checkpoint": (
                    "C10-CP4B-1-gap-diagnosis"
                ),
                "holdout_accessed": False,
                "records": records,
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
