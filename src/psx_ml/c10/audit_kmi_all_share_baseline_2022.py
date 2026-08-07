from __future__ import annotations

from pathlib import Path
import csv
import json
import re

import pdfplumber

PDF = Path(
    "data/reference/kmi_all_share_sources/"
    "sharia_KMI_All_Share_list_June_2021_Final_27122021.pdf"
)
OUTPUT_DIR = Path(
    "data/reference/kmi_all_share_sources/"
    "baseline_2022_audit"
)
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_BASELINE_2022_AUDIT.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_BASELINE_2022_AUDIT.json"
)

EXPECTED_INDEX_COUNT = 250
EXPECTED_COMPLIANT_COUNT = 257


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def plausible_symbol(value: object) -> str:
    text = clean(value).upper()

    if (
        not text
        or text.isdigit()
        or not re.fullmatch(
            r"[A-Z0-9][A-Z0-9.-]{1,14}",
            text,
        )
        or not re.search(r"[A-Z]", text)
    ):
        return ""

    bad = {
        "TICKER",
        "SYMBOL",
        "COMPANY",
        "COMPANIES",
        "NAME",
        "STATUS",
        "COMPLIANT",
        "NON-COMPLIANT",
        "INCOMING",
        "OUTGOING",
        "S.NO",
        "SR.NO",
    }
    return "" if text in bad else text


def row_symbols(row: list[object]) -> list[str]:
    symbols = []
    for cell in row:
        symbol = plausible_symbol(cell)
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def write_table_csv(
    path: Path,
    table: list[list[object]],
) -> None:
    width = max(
        (len(row) for row in table),
        default=0,
    )
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle)
        for row in table:
            normalized = [
                clean(cell)
                for cell in row
            ]
            normalized.extend(
                [""] * (width - len(normalized))
            )
            writer.writerow(normalized)


def main() -> None:
    if not PDF.exists():
        raise FileNotFoundError(PDF)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = []

    with pdfplumber.open(PDF) as document:
        for page_index, page in enumerate(
            document.pages
        ):
            page_text = page.extract_text() or ""
            tables = page.extract_tables()

            for table_index, table in enumerate(
                tables
            ):
                output = (
                    OUTPUT_DIR
                    / (
                        f"page_{page_index + 1:02d}_"
                        f"table_{table_index + 1:02d}.csv"
                    )
                )
                write_table_csv(output, table)

                symbols = []
                for row in table:
                    for symbol in row_symbols(
                        list(row)
                    ):
                        if symbol not in symbols:
                            symbols.append(symbol)

                preview = " ".join(
                    clean(cell)
                    for row in table[:5]
                    for cell in row
                )

                records.append(
                    {
                        "page": page_index + 1,
                        "table": table_index + 1,
                        "rows": len(table),
                        "max_columns": max(
                            (
                                len(row)
                                for row in table
                            ),
                            default=0,
                        ),
                        "unique_plausible_symbols": (
                            len(symbols)
                        ),
                        "symbols": symbols,
                        "preview": preview[:500],
                        "output_path": str(output),
                        "page_mentions_final_list": bool(
                            re.search(
                                r"final\s+list|constituent",
                                page_text,
                                flags=re.IGNORECASE,
                            )
                        ),
                        "page_mentions_compliant": bool(
                            re.search(
                                r"\bcompliant\b",
                                page_text,
                                flags=re.IGNORECASE,
                            )
                        ),
                    }
                )

    candidate_tables = [
        record
        for record in records
        if record[
            "unique_plausible_symbols"
        ]
        in {
            EXPECTED_INDEX_COUNT,
            EXPECTED_COMPLIANT_COUNT,
        }
        or abs(
            record[
                "unique_plausible_symbols"
            ]
            - EXPECTED_INDEX_COUNT
        )
        <= 10
    ]

    lines = [
        "# C10 CP4B — 2022 KMI All Share Baseline Audit",
        "",
        f"- Official index count: {EXPECTED_INDEX_COUNT}",
        f"- Parsed compliant count: {EXPECTED_COMPLIANT_COUNT}",
        "",
        "| Page | Table | Rows | Columns | "
        "Plausible symbols | Final-list text | "
        "Compliant text |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]

    for record in records:
        lines.append(
            "| "
            f"{record['page']} | "
            f"{record['table']} | "
            f"{record['rows']} | "
            f"{record['max_columns']} | "
            f"{record['unique_plausible_symbols']} | "
            f"{record['page_mentions_final_list']} | "
            f"{record['page_mentions_compliant']} |"
        )

    lines.extend(
        [
            "",
            "## Candidate tables near the official count",
            "",
        ]
    )

    if candidate_tables:
        for record in candidate_tables:
            lines.append(
                "- "
                f"Page {record['page']}, "
                f"table {record['table']}: "
                f"{record['unique_plausible_symbols']} "
                f"plausible symbols — "
                f"`{record['output_path']}`"
            )
    else:
        lines.append(
            "- No single PDF table directly contains "
            "approximately 250 symbols."
        )

    lines.extend(
        [
            "",
            "## Stop condition",
            "",
            "This audit does not create membership. "
            "The baseline is accepted only when an "
            "official 250-symbol constituent set is "
            "identified or the exact seven exclusions "
            "from the 257 compliant rows are documented.",
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
                    "C10-CP4B-1-baseline-2022-audit"
                ),
                "holdout_accessed": False,
                "official_index_count": (
                    EXPECTED_INDEX_COUNT
                ),
                "parsed_compliant_count": (
                    EXPECTED_COMPLIANT_COUNT
                ),
                "records": records,
                "candidate_tables": (
                    candidate_tables
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
