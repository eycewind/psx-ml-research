from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import math

import pdfplumber

SOURCE_DIR = Path("data/reference/kmi_all_share_sources")
REPORT = Path(
    "artifacts/reports/"
    "C10_CP4B_KMI_ALL_SHARE_PDF_COLOR_PROBE.json"
)

PDFS = [
    "sharia_KMI_All_Share_list_June_2021_Final_27122021.pdf",
    "Copy_of_KMI_All_Share_June_-22_23122022.pdf",
    "Notice-_KMI-All-Index-Re-composition-Jun-30-2023-Final.pdf",
    "KMI-ALL-Share-Recomposition-Notice.pdf",
    "Notice-KMIALLshare-Notice-as-of-June-2024.pdf",
    "Merged_KMIALL_Notice_and_FinalList_June2025.pdf",
]


def norm_color(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return tuple(round(float(v), 4) for v in value)
    except Exception:
        return str(value)


def main() -> None:
    output = []

    for filename in PDFS:
        path = SOURCE_DIR / filename
        if not path.exists():
            raise FileNotFoundError(path)

        pdf_record = {
            "filename": filename,
            "pages": [],
        }

        with pdfplumber.open(path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                chars = page.chars
                nonstroke = Counter(
                    str(norm_color(c.get("non_stroking_color")))
                    for c in chars
                )
                stroke = Counter(
                    str(norm_color(c.get("stroking_color")))
                    for c in chars
                )

                samples = {}
                for c in chars:
                    key = (
                        str(norm_color(c.get("non_stroking_color"))),
                        str(norm_color(c.get("stroking_color"))),
                    )
                    samples.setdefault(key, "")
                    if len(samples[key]) < 200:
                        samples[key] += str(c.get("text", ""))

                page_record = {
                    "page": page_number,
                    "char_count": len(chars),
                    "non_stroking_colors": nonstroke.most_common(),
                    "stroking_colors": stroke.most_common(),
                    "color_samples": [
                        {
                            "non_stroking_color": key[0],
                            "stroking_color": key[1],
                            "sample_text": text,
                        }
                        for key, text in samples.items()
                    ],
                }
                pdf_record["pages"].append(page_record)

        output.append(pdf_record)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "checkpoint": "C10-CP4B-1-pdf-color-probe",
                "holdout_accessed": False,
                "records": output,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
