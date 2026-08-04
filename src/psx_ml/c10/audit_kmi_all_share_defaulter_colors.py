from __future__ import annotations

from pathlib import Path
import json
import math
import re

import pandas as pd
import pdfplumber

SOURCE_DIR = Path("data/reference/kmi_all_share_sources")
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_DEFAULTER_COLOR_AUDIT.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_DEFAULTER_COLOR_AUDIT.json"
)
CSV_OUTPUT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_DEFAULTER_COLOR_AUDIT.csv"
)

SOURCES = [
    {
        "source_id": "review_2021_h1",
        "effective_from": "2022-01-03",
        "filename": (
            "sharia_KMI_All_Share_list_"
            "June_2021_Final_27122021.pdf"
        ),
        "official_count": 250,
    },
    {
        "source_id": "review_2022_h1",
        "effective_from": "2023-01-12",
        "filename": (
            "Copy_of_KMI_All_Share_"
            "June_-22_23122022.pdf"
        ),
        "official_count": 261,
    },
    {
        "source_id": "review_2023_h1",
        "effective_from": "2023-12-26",
        "filename": (
            "Notice-_KMI-All-Index-Re-composition-"
            "Jun-30-2023-Final.pdf"
        ),
        "official_count": 258,
    },
    {
        "source_id": "review_2023_h2",
        "effective_from": "2024-06-25",
        "filename": "KMI-ALL-Share-Recomposition-Notice.pdf",
        "official_count": 255,
    },
    {
        "source_id": "review_2024_h1",
        "effective_from": "2025-01-03",
        "filename": (
            "Notice-KMIALLshare-Notice-"
            "as-of-June-2024.pdf"
        ),
        "official_count": 264,
    },
    {
        "source_id": "review_2025_h1",
        "effective_from": "2025-12-02",
        "filename": (
            "Merged_KMIALL_Notice_and_"
            "FinalList_June2025.pdf"
        ),
        "official_count": 281,
    },
]


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def color_is_red(color: object) -> bool:
    if color is None:
        return False

    if isinstance(color, (int, float)):
        return False

    try:
        values = tuple(float(v) for v in color)
    except Exception:
        return False

    if len(values) == 3:
        r, g, b = values
        # pdfplumber usually exposes RGB in 0..1.
        if max(values) <= 1.0:
            return (
                r >= 0.55
                and r >= g * 1.35
                and r >= b * 1.35
            )
        return (
            r >= 140
            and r >= g * 1.35
            and r >= b * 1.35
        )

    if len(values) == 4:
        c, m, y, k = values
        # Red in CMYK is typically low cyan, high magenta/yellow.
        return (
            c <= 0.35
            and m >= 0.45
            and y >= 0.35
        )

    return False


def words_with_color(page) -> list[dict[str, object]]:
    words = page.extract_words(
        use_text_flow=True,
        keep_blank_chars=False,
        extra_attrs=["non_stroking_color"],
    )
    return words


def red_overlap_fraction(
    words: list[dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> float:
    x0, top, x1, bottom = bbox
    matching = []
    red = []

    for word in words:
        wx0 = float(word["x0"])
        wx1 = float(word["x1"])
        wtop = float(word["top"])
        wbottom = float(word["bottom"])

        horizontal = min(x1, wx1) - max(x0, wx0)
        vertical = min(bottom, wbottom) - max(top, wtop)

        if horizontal <= 0 or vertical <= 0:
            continue

        matching.append(word)
        if color_is_red(
            word.get("non_stroking_color")
        ):
            red.append(word)

    if not matching:
        return 0.0

    total_chars = sum(
        len(str(word.get("text", "")))
        for word in matching
    )
    red_chars = sum(
        len(str(word.get("text", "")))
        for word in red
    )

    if total_chars <= 0:
        return 0.0
    return red_chars / total_chars


def extract_source(source: dict[str, object]) -> list[dict[str, object]]:
    path = SOURCE_DIR / str(source["filename"])
    records: list[dict[str, object]] = []

    with pdfplumber.open(path) as document:
        for page_index, page in enumerate(document.pages):
            tables = page.find_tables()
            words = words_with_color(page)

            for table_index, table in enumerate(tables):
                raw = table.extract()
                if not raw:
                    continue

                header = [clean(cell) for cell in raw[0]]
                if "Ticker" not in header:
                    continue

                status_candidates = [
                    i
                    for i, value in enumerate(header)
                    if "shariah" in value.lower()
                    and "status" in value.lower()
                ]
                company_candidates = [
                    i
                    for i, value in enumerate(header)
                    if "company" in value.lower()
                    and "name" in value.lower()
                ]
                number_candidates = [
                    i
                    for i, value in enumerate(header)
                    if value.lower() in {
                        "no.",
                        "no",
                        "s.no.",
                        "sr.no.",
                    }
                ]

                if (
                    not status_candidates
                    or not company_candidates
                ):
                    continue

                ticker_col = header.index("Ticker")
                company_col = company_candidates[0]
                status_col = status_candidates[0]
                number_col = (
                    number_candidates[0]
                    if number_candidates
                    else None
                )

                cells = table.cells
                row_count = len(raw)
                col_count = len(header)

                if len(cells) < row_count * col_count:
                    continue

                for row_idx, row in enumerate(raw[1:], start=1):
                    normalized = [clean(cell) for cell in row]
                    if len(normalized) <= max(
                        ticker_col,
                        company_col,
                        status_col,
                    ):
                        continue

                    symbol = normalized[ticker_col].upper()
                    company = normalized[company_col]
                    status = normalized[status_col]
                    number = (
                        normalized[number_col]
                        if number_col is not None
                        and number_col < len(normalized)
                        else ""
                    )

                    if (
                        not symbol
                        or not re.fullmatch(
                            r"[A-Z0-9][A-Z0-9.-]{1,14}",
                            symbol,
                        )
                        or not re.search(r"[A-Z]", symbol)
                        or not status.lower().startswith(
                            "compliant"
                        )
                    ):
                        continue

                    # table.cells is row-major for extracted tables.
                    company_cell_index = (
                        row_idx * col_count
                        + company_col
                    )
                    if company_cell_index >= len(cells):
                        continue

                    company_bbox = cells[
                        company_cell_index
                    ]
                    red_fraction = red_overlap_fraction(
                        words,
                        company_bbox,
                    )

                    records.append(
                        {
                            "source_id": source["source_id"],
                            "effective_from": source["effective_from"],
                            "official_count": source["official_count"],
                            "filename": source["filename"],
                            "pdf_page": page_index + 1,
                            "table_index": table_index + 1,
                            "source_row_number": number,
                            "symbol": symbol,
                            "company_name": company,
                            "final_shariah_status": status,
                            "company_red_fraction": red_fraction,
                            "is_red_candidate": red_fraction >= 0.50,
                        }
                    )

    return records


def main() -> None:
    all_records: list[dict[str, object]] = []
    source_summaries = []

    for source in SOURCES:
        records = extract_source(source)
        frame = pd.DataFrame(records)

        if frame.empty:
            source_summaries.append(
                {
                    **source,
                    "compliant_count": 0,
                    "red_candidate_count": 0,
                    "derived_member_count": 0,
                    "derived_matches_official": False,
                    "red_candidate_symbols": [],
                }
            )
            continue

        duplicate_symbols = sorted(
            frame.loc[
                frame["symbol"].duplicated(
                    keep=False
                ),
                "symbol",
            ].unique()
        )

        unique = (
            frame.sort_values(
                [
                    "symbol",
                    "company_red_fraction",
                ],
                ascending=[True, False],
            )
            .drop_duplicates(
                "symbol",
                keep="first",
            )
            .reset_index(drop=True)
        )

        red_symbols = sorted(
            unique.loc[
                unique["is_red_candidate"],
                "symbol",
            ].tolist()
        )
        compliant_count = len(unique)
        derived_count = (
            compliant_count - len(red_symbols)
        )

        source_summaries.append(
            {
                **source,
                "compliant_count": compliant_count,
                "red_candidate_count": len(
                    red_symbols
                ),
                "derived_member_count": derived_count,
                "derived_matches_official": (
                    derived_count
                    == source["official_count"]
                ),
                "red_candidate_symbols": red_symbols,
                "duplicate_symbols": duplicate_symbols,
            }
        )
        all_records.extend(
            unique.to_dict("records")
        )

    output_frame = pd.DataFrame(all_records)
    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_frame.to_csv(
        CSV_OUTPUT,
        index=False,
    )

    lines = [
        "# C10 CP4B — KMI All Share Defaulter-Color Audit",
        "",
        "This audit tests whether each official final constituent "
        "count can be reproduced as compliant rows minus "
        "company-name cells printed in red.",
        "",
        "| Effective | Source | Compliant rows | Red candidates | "
        "Derived members | Official | Match |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    for summary in source_summaries:
        lines.append(
            "| "
            f"{summary['effective_from']} | "
            f"{summary['source_id']} | "
            f"{summary['compliant_count']} | "
            f"{summary['red_candidate_count']} | "
            f"{summary['derived_member_count']} | "
            f"{summary['official_count']} | "
            f"{summary['derived_matches_official']} |"
        )

    lines.extend(
        [
            "",
            "## Red candidate symbols",
            "",
        ]
    )

    for summary in source_summaries:
        lines.append(
            f"- {summary['effective_from']}: "
            + (
                ", ".join(
                    summary["red_candidate_symbols"]
                )
                or "none detected"
            )
        )

    lines.extend(
        [
            "",
            "## Status",
            "",
        ]
    )

    all_match = all(
        summary["derived_matches_official"]
        for summary in source_summaries
    )
    lines.append(
        "PASS: every directly available official final list "
        "matches compliant rows minus red defaulter rows."
        if all_match
        else (
            "REVIEW REQUIRED: one or more sources do not "
            "reproduce the official count using red-row "
            "detection."
        )
    )
    lines.append("")

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            {
                "checkpoint": (
                    "C10-CP4B-1-defaulter-color-audit"
                ),
                "holdout_accessed": False,
                "all_direct_sources_match": all_match,
                "records": source_summaries,
                "row_output": str(CSV_OUTPUT),
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
