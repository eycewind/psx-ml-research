from __future__ import annotations
from pathlib import Path
import hashlib
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

INPUT = Path("data/reference/kmi30_membership_history.csv")
OUTPUT = Path("data/reference/kmi30_membership_history.parquet")
REPORT = Path("artifacts/reports/C10_CP4A_KMI30_MEMBERSHIP_AUDIT.md")
MANIFEST = Path("artifacts/reports/C10_CP4A_KMI30_MEMBERSHIP_MANIFEST.json")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table=pa.Table.from_pandas(frame, preserve_index=False)
    with path.open("wb") as f:
        pq.write_table(table, f)

def main() -> None:
    df=pd.read_csv(INPUT, dtype=str)
    required={"symbol","effective_from","effective_to","review_as_of","notice_date","notice_no","source_url","source_type"}
    missing=sorted(required-set(df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    for c in ["effective_from","review_as_of","notice_date"]:
        df[c]=pd.to_datetime(df[c], errors="raise").dt.normalize()
    # Keep 9999 sentinel as string to avoid pandas datetime overflow.
    finite_end=df["effective_to"]!="9999-12-31"
    parsed_end=pd.to_datetime(df.loc[finite_end,"effective_to"], errors="raise").dt.normalize()
    df.loc[finite_end,"effective_to"]=parsed_end.dt.strftime("%Y-%m-%d")

    counts=df.groupby(["effective_from","effective_to"], dropna=False)["symbol"].nunique()
    if not (counts==30).all():
        raise ValueError(f"Every interval must contain 30 unique symbols:\n{counts}")

    if df.duplicated(["effective_from","symbol"]).any():
        raise ValueError("Duplicate symbol inside an effective interval")

    intervals=(df[["effective_from","effective_to","review_as_of","notice_date","notice_no","source_url"]]
               .drop_duplicates().sort_values("effective_from").reset_index(drop=True))

    for i in range(len(intervals)-1):
        current_end=pd.Timestamp(intervals.loc[i,"effective_to"])
        next_start=pd.Timestamp(intervals.loc[i+1,"effective_from"])
        if current_end + pd.Timedelta(days=1) != next_start:
            raise ValueError(f"Gap/overlap between {current_end.date()} and {next_start.date()}")

    if (df["notice_date"] > df["effective_from"]).any():
        raise ValueError("Notice date occurs after effective date")

    df=df.sort_values(["effective_from","symbol"]).reset_index(drop=True)
    write_parquet(df, OUTPUT)

    interval_table=intervals.copy()
    for c in ["effective_from","review_as_of","notice_date"]:
        interval_table[c]=interval_table[c].dt.date.astype(str)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# C10 CP4A KMI-30 Membership Audit\n\n"
        "Status: **PASS**\n\n"
        f"- Rows: {len(df)}\n"
        f"- Effective intervals: {len(intervals)}\n"
        "- Members per interval: exactly 30\n"
        "- Interval gaps/overlaps: none\n"
        "- Notice used before effective date: none\n"
        "- Source: official PSX recomposition notices\n\n"
        "## Effective intervals\n\n"
        + interval_table.to_markdown(index=False)
        + "\n",
        encoding="utf-8",
    )

    manifest={
        "contract":"C10","checkpoint":"CP4A-membership","status":"COMPLETE",
        "holdout_accessed":False,
        "input":{"path":str(INPUT),"sha256":sha256(INPUT),"rows":len(df)},
        "output":{"path":str(OUTPUT),"sha256":sha256(OUTPUT),"rows":len(df)},
        "interval_count":len(intervals),
        "members_per_interval":30,
        "source_notice_numbers":sorted(df["notice_no"].unique().tolist()),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(interval_table.to_string(index=False))
    print(f"\nRows: {len(df)} -> {OUTPUT}")
    print(f"Report: {REPORT}")
    print(f"Manifest: {MANIFEST}")

if __name__=="__main__":
    main()
