from __future__ import annotations

from pathlib import Path
import hashlib
import json
import urllib.request

INVENTORY = Path(
    "data/reference/kmi_all_share_sources/source_inventory.json"
)
OUTPUT_DIR = INVENTORY.parent
MANIFEST = OUTPUT_DIR / "download_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, output: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 PSX-ML-Research/"
                "C10-CP4B-source-audit"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()

    if not data.startswith(b"%PDF"):
        prefix = data[:120]
        raise ValueError(
            f"{url} did not return a PDF; prefix={prefix!r}"
        )

    output.write_bytes(data)


def main() -> None:
    inventory = json.loads(
        INVENTORY.read_text(encoding="utf-8")
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    failures = []

    for source in inventory:
        output = OUTPUT_DIR / source["filename"]
        try:
            if not output.exists():
                print(f"Downloading {source['source_id']}...")
                download(source["url"], output)
            else:
                print(f"Using existing {output}")

            record = dict(source)
            record.update(
                {
                    "path": str(output),
                    "bytes": output.stat().st_size,
                    "sha256": sha256(output),
                    "status": "downloaded",
                }
            )
            records.append(record)
        except Exception as exc:
            failures.append(
                {
                    "source_id": source["source_id"],
                    "url": source["url"],
                    "error": repr(exc),
                }
            )

    result = {
        "checkpoint": "C10-CP4B-1-source-acquisition",
        "holdout_accessed": False,
        "downloaded": records,
        "failures": failures,
    }
    MANIFEST.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print()
    print(f"Downloaded: {len(records)}")
    print(f"Failures:   {len(failures)}")
    print(f"Manifest:   {MANIFEST}")

    if failures:
        for failure in failures:
            print(
                f"FAILED {failure['source_id']}: "
                f"{failure['error']}"
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
