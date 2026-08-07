from __future__ import annotations

from pathlib import Path
import csv
import json
import re

import pdfplumber

SOURCE_DIR = Path("data/reference/kmi_all_share_sources")
OUTPUT_DIR = SOURCE_DIR / "parsed_change_tables"
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_CHANGE_EXTRACTION.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_CHANGE_EXTRACTION.json"
)

SOURCES = [
    {
        "source_id": "review_2021_h1",
        "filename": (
            "sharia_KMI_All_Share_list_"
            "June_2021_Final_27122021.pdf"
        ),
        "effective_from": "2022-01-03",
        "pages": [
            {"page": 1, "mode": "paired"},
            {"page": 2, "mode": "incoming_only"},
        ],
        "expected_incoming": 37,
        "expected_outgoing": 13,
    },
    {
        "source_id": "review_2021_h2",
        "filename": (
            "Notice-_KMI_All_Shares_Index_"
            "Recomposition_30-June-22_(M).pdf"
        ),
        "effective_from": "2022-07-15",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 30,
        "expected_outgoing": 25,
    },
    {
        "source_id": "review_2022_h1",
        "filename": (
            "Copy_of_KMI_All_Share_"
            "June_-22_23122022.pdf"
        ),
        "effective_from": "2023-01-12",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 30,
        "expected_outgoing": 21,
    },
    {
        "source_id": "review_2022_h2",
        "filename": (
            "Notice-666_KMI_All_Share_Index_"
            "re-composition_for_Dec-22.pdf"
        ),
        "effective_from": "2023-07-10",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 26,
        "expected_outgoing": 33,
    },
    {
        "source_id": "review_2023_h1",
        "filename": (
            "Notice-_KMI-All-Index-Re-composition-"
            "Jun-30-2023-Final.pdf"
        ),
        "effective_from": "2023-12-26",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 32,
        "expected_outgoing": 24,
    },
    {
        "source_id": "review_2023_h2",
        "filename": "KMI-ALL-Share-Recomposition-Notice.pdf",
        "effective_from": "2024-06-25",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 28,
        "expected_outgoing": 29,
    },
    {
        "source_id": "review_2024_h1",
        "filename": (
            "Notice-KMIALLshare-Notice-"
            "as-of-June-2024.pdf"
        ),
        "effective_from": "2025-01-03",
        "pages": [{"page": 1, "mode": "paired"}],
        "expected_incoming": 26,
        "expected_outgoing": 13,
    },
    {
        "source_id": "review_2024_h2",
        "filename": (
            "KMI-All-share-Notice-Recomposition-"
            "as-of-Dec-_2024-Final.pdf"
        ),
        "effective_from": "2025-06-10",
        "pages": [{"page": 0, "mode": "paired"}],
        "expected_incoming": 15,
        "expected_outgoing": 22,
    },
    {
        "source_id": "review_2025_h1",
        "filename": (
            "Merged_KMIALL_Notice_and_"
            "FinalList_June2025.pdf"
        ),
        "effective_from": "2025-12-02",
        "pages": [{"page": 0, "mode": "paired"}],
        "expected_incoming": 35,
        "expected_outgoing": 12,
    },
]

BAD_TOKENS = {
    "SR",
    "S.NO",
    "S.NO.",
    "SR.NO",
    "SR.NO.",
    "TICKER",
    "INCOMING",
    "OUTGOING",
    "COMPANY",
    "COMPANIES",
    "NAME",
    "NOTICE",
}


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def ticker(value: object) -> str:
    text = clean(value).upper()

    if (
        not text
        or text in BAD_TOKENS
        or text.isdigit()
        or not re.fullmatch(
            r"[A-Z0-9][A-Z0-9.-]{1,14}",
            text,
        )
        or not re.search(r"[A-Z]", text)
    ):
        return ""

    return text


def first_ticker(cells: list[object]) -> str:
    for cell in cells:
        candidate = ticker(cell)
        if candidate:
            return candidate
    return ""


def locate_paired_table(
    tables: list[list[list[object]]],
) -> list[list[object]]:
    candidates = []

    for table in tables:
        preview = " ".join(
            clean(cell)
            for row in table[:6]
            for cell in row
        ).lower()

        if (
            "incoming" in preview
            and "outgoing" in preview
        ):
            candidates.append(table)

    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one paired change table; "
            f"found {len(candidates)}"
        )

    return candidates[0]


def locate_continuation_table(
    tables: list[list[list[object]]],
) -> list[list[object]]:
    candidates = [
        table
        for table in tables
        if table
        and max(len(row) for row in table) <= 4
    ]

    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one continuation table; "
            f"found {len(candidates)}"
        )

    return candidates[0]


def parse_paired_table(
    table: list[list[object]],
    *,
    page_number: int,
) -> list[dict[str, object]]:
    records = []

    for raw_row in table:
        row = list(raw_row)
        if len(row) < 4:
            continue

        midpoint = len(row) // 2
        incoming_symbol = first_ticker(row[:midpoint])
        outgoing_symbol = first_ticker(row[midpoint:])

        if not incoming_symbol and not outgoing_symbol:
            continue

        records.append(
            {
                "page_number": page_number,
                "incoming_symbol": incoming_symbol,
                "outgoing_symbol": outgoing_symbol,
                "raw_cells_json": json.dumps(
                    [clean(cell) for cell in row],
                    ensure_ascii=False,
                ),
            }
        )

    return records


def parse_incoming_only_table(
    table: list[list[object]],
    *,
    page_number: int,
) -> list[dict[str, object]]:
    records = []

    for raw_row in table:
        incoming_symbol = first_ticker(
            list(raw_row)
        )
        if not incoming_symbol:
            continue

        records.append(
            {
                "page_number": page_number,
                "incoming_symbol": incoming_symbol,
                "outgoing_symbol": "",
                "raw_cells_json": json.dumps(
                    [clean(cell) for cell in raw_row],
                    ensure_ascii=False,
                ),
            }
        )

    return records


def write_csv(
    path: Path,
    records: list[dict[str, object]],
) -> None:
    fieldnames = [
        "source_id",
        "effective_from",
        "sequence",
        "page_number",
        "incoming_symbol",
        "outgoing_symbol",
        "raw_cells_json",
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    manifest_records = []
    all_records = []

    for source in SOURCES:
        pdf_path = SOURCE_DIR / source["filename"]
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        extracted: list[dict[str, object]] = []

        with pdfplumber.open(pdf_path) as document:
            for page_spec in source["pages"]:
                page_index = page_spec["page"]
                mode = page_spec["mode"]
                tables = document.pages[
                    page_index
                ].extract_tables()

                if mode == "paired":
                    table = locate_paired_table(tables)
                    extracted.extend(
                        parse_paired_table(
                            table,
                            page_number=page_index + 1,
                        )
                    )
                elif mode == "incoming_only":
                    table = locate_continuation_table(
                        tables
                    )
                    extracted.extend(
                        parse_incoming_only_table(
                            table,
                            page_number=page_index + 1,
                        )
                    )
                else:
                    raise ValueError(
                        f"Unsupported mode: {mode}"
                    )

        # Remove repeated header rows and duplicates while
        # preserving source order.
        seen_pairs: set[tuple[str, str]] = set()
        normalized: list[dict[str, object]] = []

        for record in extracted:
            pair = (
                str(record["incoming_symbol"]),
                str(record["outgoing_symbol"]),
            )

            if pair == ("", "") or pair in seen_pairs:
                continue

            seen_pairs.add(pair)
            normalized.append(record)

        for sequence, record in enumerate(
            normalized,
            start=1,
        ):
            record.update(
                {
                    "source_id": source["source_id"],
                    "effective_from": (
                        source["effective_from"]
                    ),
                    "sequence": sequence,
                }
            )

        incoming = sorted(
            {
                str(row["incoming_symbol"])
                for row in normalized
                if row["incoming_symbol"]
            }
        )
        outgoing = sorted(
            {
                str(row["outgoing_symbol"])
                for row in normalized
                if row["outgoing_symbol"]
            }
        )

        output_path = (
            OUTPUT_DIR
            / f"{source['source_id']}_changes.csv"
        )
        write_csv(output_path, normalized)

        incoming_matches = (
            len(incoming)
            == source["expected_incoming"]
        )
        outgoing_matches = (
            len(outgoing)
            == source["expected_outgoing"]
        )

        manifest_records.append(
            {
                **source,
                "output_path": str(output_path),
                "extracted_rows": len(normalized),
                "incoming_count": len(incoming),
                "outgoing_count": len(outgoing),
                "incoming_symbols": incoming,
                "outgoing_symbols": outgoing,
                "incoming_count_matches": (
                    incoming_matches
                ),
                "outgoing_count_matches": (
                    outgoing_matches
                ),
            }
        )
        all_records.extend(normalized)

    combined_path = OUTPUT_DIR / "all_changes.csv"
    write_csv(combined_path, all_records)

    all_pass = all(
        record["incoming_count_matches"]
        and record["outgoing_count_matches"]
        for record in manifest_records
    )

    lines = [
        "# C10 CP4B — KMI All Share Change Extraction",
        "",
        "| Source | Effective | Incoming | Expected | "
        "Outgoing | Expected | Pass |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for record in manifest_records:
        passed = (
            record["incoming_count_matches"]
            and record["outgoing_count_matches"]
        )
        lines.append(
            "| "
            f"{record['source_id']} | "
            f"{record['effective_from']} | "
            f"{record['incoming_count']} | "
            f"{record['expected_incoming']} | "
            f"{record['outgoing_count']} | "
            f"{record['expected_outgoing']} | "
            f"{passed} |"
        )

    lines.extend(
        [
            "",
            "## Status",
            "",
            (
                "PASS: all incoming/outgoing counts match."
                if all_pass
                else (
                    "REVIEW REQUIRED: one or more extracted "
                    "counts do not match the notice."
                )
            ),
            "",
            "This extraction is not yet the final membership "
            "history. The official 2022 baseline constituent "
            "set must still be reconstructed and reconciled.",
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
                    "C10-CP4B-1-change-extraction"
                ),
                "holdout_accessed": False,
                "all_known_counts_match": all_pass,
                "records": manifest_records,
                "combined_output": str(combined_path),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("\n".join(lines))
    print(f"Manifest: {MANIFEST}")

    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
