from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
import subprocess

SOURCE_DIR = Path(
    "data/reference/kmi_all_share_sources"
)
INVENTORY = SOURCE_DIR / "source_inventory.json"
OUTPUT_DIR = SOURCE_DIR / "extracted_text"
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SOURCE_AUDIT.md"
)
MANIFEST = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_SOURCE_AUDIT.json"
)

OFFICIAL_COUNTS = {
    "review_2021_h1": 250,
    "review_2021_h2": 252,
    "review_2022_h1": 261,
    "review_2022_h2": None,
    "review_2023_h1": 258,
    "review_2023_h2": 255,
    "review_2024_h1": 264,
    "review_2024_h2": None,
    "review_2025_h1": 281,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def extract_text(pdf: Path, text: Path) -> None:
    result = subprocess.run(
        [
            "pdftotext",
            "-layout",
            str(pdf),
            str(text),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"pdftotext failed for {pdf}: "
            f"{result.stderr.strip()}"
        )


def parse_notice_metadata(text: str) -> dict:
    count_match = re.search(
        r"comprise of\s+(\d+)\s+companies",
        text,
        flags=re.IGNORECASE,
    )
    incoming_match = re.search(
        r"out of which\s+(\d+)\s+new companies",
        text,
        flags=re.IGNORECASE,
    )
    outgoing_match = re.search(
        r"whereas,\s+(\d+)\s+companies "
        r"(?:have been|has been|are)\s+removed",
        text,
        flags=re.IGNORECASE,
    )
    effective_match = re.search(
        r"(?:implemented|implementation)"
        r"(?:\s+w\.e\.f\.?|\s+with effect from)?"
        r"[^.\n]{0,80}?"
        r"((?:Monday|Tuesday|Wednesday|Thursday|"
        r"Friday|Saturday|Sunday)?\s*,?\s*"
        r"(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|"
        r"December)\s+\d{1,2},?\s+\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    return {
        "notice_constituent_count": (
            int(count_match.group(1))
            if count_match
            else None
        ),
        "notice_incoming_count": (
            int(incoming_match.group(1))
            if incoming_match
            else None
        ),
        "notice_outgoing_count": (
            int(outgoing_match.group(1))
            if outgoing_match
            else None
        ),
        "notice_effective_text": (
            effective_match.group(1).strip()
            if effective_match
            else None
        ),
    }


def parse_screening_rows(text: str) -> dict:
    compliant = []
    noncompliant = []
    no_opinion = []

    row_pattern = re.compile(
        r"^\s*(\d+)\s+"
        r"([A-Z0-9][A-Z0-9-]{1,14})\s+"
    )

    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        match = row_pattern.match(line)
        if not match:
            continue

        number = int(match.group(1))
        symbol = match.group(2)
        tail = line.strip()

        if re.search(
            r"\bNon-Compliant\d*\s*$",
            tail,
        ):
            status = "non_compliant"
            noncompliant.append(
                (number, symbol, line_number)
            )
        elif re.search(
            r"\bCompliant(?:\s*\*\*)?\d*\s*$",
            tail,
        ):
            status = "compliant"
            compliant.append(
                (number, symbol, line_number)
            )
        elif re.search(
            r"\bNo Opinion!?\d*\s*$",
            tail,
            flags=re.IGNORECASE,
        ):
            status = "no_opinion"
            no_opinion.append(
                (number, symbol, line_number)
            )
        else:
            continue

    return {
        "compliant_rows": compliant,
        "noncompliant_rows": noncompliant,
        "no_opinion_rows": no_opinion,
        "compliant_unique": sorted(
            {row[1] for row in compliant}
        ),
        "noncompliant_unique": sorted(
            {row[1] for row in noncompliant}
        ),
        "no_opinion_unique": sorted(
            {row[1] for row in no_opinion}
        ),
    }


def main() -> None:
    inventory = json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    records = []

    for source in inventory:
        pdf = SOURCE_DIR / source["filename"]
        if not pdf.exists():
            raise FileNotFoundError(pdf)

        text_path = OUTPUT_DIR / (
            pdf.stem + ".txt"
        )
        extract_text(pdf, text_path)
        text = text_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        metadata = parse_notice_metadata(text)
        screening = parse_screening_rows(text)

        record = {
            **source,
            **metadata,
            "expected_constituent_count": (
                OFFICIAL_COUNTS.get(
                    source["source_id"]
                )
            ),
            "pdf_path": str(pdf),
            "pdf_bytes": pdf.stat().st_size,
            "pdf_sha256": sha256(pdf),
            "text_path": str(text_path),
            "text_sha256": sha256(text_path),
            "parsed_compliant_rows": len(
                screening["compliant_rows"]
            ),
            "parsed_compliant_unique": len(
                screening["compliant_unique"]
            ),
            "parsed_noncompliant_unique": len(
                screening["noncompliant_unique"]
            ),
            "parsed_no_opinion_unique": len(
                screening["no_opinion_unique"]
            ),
            "screening_table_present": bool(
                screening["compliant_rows"]
                or screening["noncompliant_rows"]
                or screening["no_opinion_rows"]
            ),
            "parsed_compliant_symbols": (
                screening["compliant_unique"]
            ),
        }
        records.append(record)

    lines = [
        "# C10 CP4B — KMI All Share Source Audit",
        "",
        "This report audits the downloaded official PSX notices "
        "before any historical membership table is built.",
        "",
        "| Source | Effective from | Notice count | "
        "Parsed compliant | Screening table |",
        "|---|---:|---:|---:|---|",
    ]

    for record in records:
        lines.append(
            "| "
            f"{record['source_id']} | "
            f"{record['effective_from']} | "
            f"{record['notice_constituent_count']} | "
            f"{record['parsed_compliant_unique']} | "
            f"{record['screening_table_present']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A parsed screening-table count is diagnostic only.",
            "- It must not automatically become an index-membership "
            "count.",
            "- Some PDFs contain incoming/outgoing changes only.",
            "- Some screening tables cover the full listed universe "
            "and include non-index or special-status rows.",
            "- Membership will be reconstructed from a reviewed "
            "baseline and official effective-date changes.",
            "",
            "## Required stop condition",
            "",
            "Do not generate the final membership CSV until every "
            "notice's incoming/outgoing list has been extracted and "
            "the reconstructed counts reconcile with the notice.",
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
                    "C10-CP4B-1-source-audit"
                ),
                "holdout_accessed": False,
                "records": records,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(
        "\n".join(
            [
                "source_id  notice_count  "
                "parsed_compliant  screening_table",
                *[
                    (
                        f"{r['source_id']:16} "
                        f"{str(r['notice_constituent_count']):>12} "
                        f"{r['parsed_compliant_unique']:>17} "
                        f"{str(r['screening_table_present']):>16}"
                    )
                    for r in records
                ],
            ]
        )
    )
    print()
    print(f"Report:   {REPORT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
