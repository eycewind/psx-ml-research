from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re

import pandas as pd
import pdfplumber
import pyarrow as pa
import pyarrow.parquet as pq

PDF = Path(
    "data/reference/kmi_all_share_sources/"
    "sharia_KMI_All_Share_list_June_2021_Final_27122021.pdf"
)
CSV_OUTPUT = Path(
    "data/reference/"
    "kmi_all_share_baseline_2022_01_03.csv"
)
PARQUET_OUTPUT = Path(
    "data/reference/"
    "kmi_all_share_baseline_2022_01_03.parquet"
)
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_BASELINE_2022_REPORT.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_BASELINE_2022_MANIFEST.json"
)

EFFECTIVE_FROM = pd.Timestamp("2022-01-03")
EXPECTED_SCREENED_COMPLIANT = 256
EXPECTED_DEFAULTERS = {
    "CLOV",
    "DMTX",
    "JUBS",
    "LMSM",
    "NCML",
    "RUBY",
}
EXPECTED_INDEX_COUNT = 250

# PDF pages containing the compliant-security tables.
# Zero-based page indexes.
COMPLIANT_TABLE_PAGES = (3, 4, 5, 6)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(
        r"\s+",
        " ",
        str(value).replace("\n", " "),
    ).strip()


def normalize_symbol(value: object) -> str:
    return clean(value).upper()


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


def extract_compliant_rows() -> pd.DataFrame:
    records: list[dict[str, object]] = []

    with pdfplumber.open(PDF) as document:
        for page_index in COMPLIANT_TABLE_PAGES:
            page = document.pages[page_index]
            tables = page.extract_tables()

            if len(tables) != 1:
                raise ValueError(
                    f"Expected one table on PDF page "
                    f"{page_index + 1}; found {len(tables)}"
                )

            table = tables[0]
            if not table:
                raise ValueError(
                    f"Empty table on PDF page "
                    f"{page_index + 1}"
                )

            header = [
                clean(cell)
                for cell in table[0]
            ]

            try:
                number_col = header.index("No.")
                ticker_col = header.index("Ticker")
                company_col = header.index("Company Name")
                status_col = header.index(
                    "Final Shariah Status"
                )
            except ValueError as exc:
                raise ValueError(
                    f"Unexpected baseline table header on "
                    f"PDF page {page_index + 1}: {header}"
                ) from exc

            for raw_row in table[1:]:
                row = [
                    clean(cell)
                    for cell in raw_row
                ]

                if len(row) <= max(
                    number_col,
                    ticker_col,
                    company_col,
                    status_col,
                ):
                    continue

                number = row[number_col]
                symbol = normalize_symbol(
                    row[ticker_col]
                )
                company = row[company_col]
                status = row[status_col]

                if not number.isdigit():
                    continue
                if not symbol:
                    continue
                if not status.lower().startswith(
                    "compliant"
                ):
                    continue

                records.append(
                    {
                        "source_row_number": int(number),
                        "symbol": symbol,
                        "company_name": company,
                        "final_shariah_status": status,
                        "pdf_page": page_index + 1,
                    }
                )

    frame = pd.DataFrame(records)

    if len(frame) != EXPECTED_SCREENED_COMPLIANT:
        raise ValueError(
            "Screened compliant-row count mismatch: "
            f"{len(frame)} != "
            f"{EXPECTED_SCREENED_COMPLIANT}"
        )

    if frame["symbol"].duplicated().any():
        duplicates = sorted(
            frame.loc[
                frame["symbol"].duplicated(
                    keep=False
                ),
                "symbol",
            ].unique()
        )
        raise ValueError(
            f"Duplicate compliant symbols: {duplicates}"
        )

    if set(frame["source_row_number"]) != set(
        range(
            1,
            EXPECTED_SCREENED_COMPLIANT + 1,
        )
    ):
        raise ValueError(
            "Baseline source row numbers are not exactly "
            "1 through 256"
        )

    return frame.sort_values(
        "source_row_number"
    ).reset_index(drop=True)


def main() -> None:
    if not PDF.exists():
        raise FileNotFoundError(PDF)

    screened = extract_compliant_rows()

    detected_defaulters = set(
        screened.loc[
            screened["symbol"].isin(
                EXPECTED_DEFAULTERS
            ),
            "symbol",
        ]
    )

    if detected_defaulters != EXPECTED_DEFAULTERS:
        raise ValueError(
            "Expected defaulter symbols missing from "
            f"compliant table: "
            f"{sorted(EXPECTED_DEFAULTERS - detected_defaulters)}"
        )

    baseline = screened.loc[
        ~screened["symbol"].isin(
            EXPECTED_DEFAULTERS
        )
    ].copy()

    if len(baseline) != EXPECTED_INDEX_COUNT:
        raise ValueError(
            "Official baseline index count mismatch: "
            f"{len(baseline)} != {EXPECTED_INDEX_COUNT}"
        )

    baseline["effective_from"] = EFFECTIVE_FROM
    baseline["shariah_compliant"] = True
    baseline["index_member"] = True
    baseline["exclusion_reason"] = ""
    baseline["source_url"] = (
        "https://www.psx.com.pk/psx/themes/psx/"
        "uploads/sharia_KMI_All_Share_list_"
        "June_2021_Final_27122021.pdf"
    )
    baseline["source_notice_no"] = "PSX/N-1504"
    baseline["source_notice_date"] = pd.Timestamp(
        "2021-12-24"
    )
    baseline["source_type"] = (
        "official_psx_recomposition"
    )

    columns = [
        "symbol",
        "company_name",
        "effective_from",
        "shariah_compliant",
        "index_member",
        "source_row_number",
        "pdf_page",
        "final_shariah_status",
        "source_notice_no",
        "source_notice_date",
        "source_url",
        "source_type",
    ]
    baseline = baseline[columns].sort_values(
        "symbol"
    ).reset_index(drop=True)

    CSV_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    baseline.to_csv(
        CSV_OUTPUT,
        index=False,
    )
    write_parquet(
        baseline,
        PARQUET_OUTPUT,
    )

    defaulters = screened.loc[
        screened["symbol"].isin(
            EXPECTED_DEFAULTERS
        ),
        [
            "symbol",
            "company_name",
            "source_row_number",
            "pdf_page",
        ],
    ].sort_values("symbol")

    report_lines = [
        "# C10 CP4B — KMI All Share Baseline 2022",
        "",
        "## Reconciliation",
        "",
        f"- Screened compliant securities: "
        f"{len(screened)}",
        f"- Compliant securities marked as defaulters: "
        f"{len(defaulters)}",
        f"- Official index constituents: "
        f"{len(baseline)}",
        "",
        "The PDF footnote states that companies marked "
        "in red are on the defaulters list. Those rows "
        "are Shariah-compliant under the financial "
        "screen but are not part of the 250-company "
        "recomposed index.",
        "",
        "## Excluded defaulter rows",
        "",
        "| Symbol | Company | Source row | PDF page |",
        "|---|---|---:|---:|",
    ]

    for row in defaulters.itertuples(
        index=False
    ):
        report_lines.append(
            f"| {row.symbol} | "
            f"{row.company_name} | "
            f"{row.source_row_number} | "
            f"{row.pdf_page} |"
        )

    report_lines.extend(
        [
            "",
            "## Baseline",
            "",
            f"- Effective from: "
            f"{EFFECTIVE_FROM.date().isoformat()}",
            f"- Constituent count: {len(baseline)}",
            f"- CSV: `{CSV_OUTPUT}`",
            f"- Parquet: `{PARQUET_OUTPUT}`",
            "",
        ]
    )

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    manifest = {
        "checkpoint": (
            "C10-CP4B-1-baseline-2022"
        ),
        "holdout_accessed": False,
        "effective_from": (
            EFFECTIVE_FROM.date().isoformat()
        ),
        "screened_compliant_count": int(
            len(screened)
        ),
        "excluded_defaulter_count": int(
            len(defaulters)
        ),
        "excluded_defaulter_symbols": sorted(
            EXPECTED_DEFAULTERS
        ),
        "official_index_count": int(
            len(baseline)
        ),
        "source_pdf": str(PDF),
        "source_pdf_sha256": sha256(PDF),
        "outputs": {
            str(CSV_OUTPUT): {
                "rows": int(len(baseline)),
                "sha256": sha256(CSV_OUTPUT),
            },
            str(PARQUET_OUTPUT): {
                "rows": int(len(baseline)),
                "sha256": sha256(
                    PARQUET_OUTPUT
                ),
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

    print("\n".join(report_lines))
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
