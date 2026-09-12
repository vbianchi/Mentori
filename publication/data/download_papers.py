#!/usr/bin/env python3
"""Download the 200-paper evaluation corpus described by corpus_papers.csv.

The corpus is not redistributed here: most of the papers are under publisher copyright. This
script rebuilds it from `corpus_papers.csv`, the manifest shipped beside it, which is the same
file as in the Zenodo deposit and the single source of truth for what each paper is. One row per
paper: `paper_id` (1 to 50 core, 51 to 200 noise), `bucket`, `filename`, `title`, `domain`,
`doi`, `pmcid`, `arxiv_id`, `source_url`, `license`, `redistributable`.

Files are written to `<output>/<bucket>/<filename>`, the layout the experiment harness reads
(`publication/data/corpus/core/01_sarek.pdf` and so on). A response that is not a PDF is
reported as a failure with the URL, so a paywalled or moved paper can be fetched by hand.

    python3 download_papers.py                      # everything, into ./corpus/
    python3 download_papers.py --only core          # the 50 core papers
    python3 download_papers.py --dry-run            # list what would be fetched
    python3 download_papers.py --output /path/to/corpus --limit 5

This script holds no list of papers. Earlier versions did, and the list drifted from the
corpus: two papers swapped, four pointing at unrelated articles, five missing. Edit the CSV,
never this file, to change what the corpus is.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "corpus_papers.csv"
USER_AGENT = "Mozilla/5.0 (corpus_reproducer/1.0) https://github.com/vbianchi/Mentori"
TIMEOUT = 60
SLEEP_BETWEEN = 0.5


def download_one(url: str, dest: Path) -> tuple[str, str]:
    if dest.exists() and dest.stat().st_size > 1024:
        return "SKIP", f"already exists ({dest.stat().st_size // 1024} KB)"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            content = resp.read()
    except urllib.error.HTTPError as e:
        return "FAIL", f"HTTP {e.code}"
    except Exception as e:                                           # noqa: BLE001
        return "FAIL", f"network error: {type(e).__name__}: {str(e)[:60]}"
    if not content.startswith(b"%PDF"):
        return "FAIL", "response is not a PDF (a paywall or an HTML page)"
    dest.write_bytes(content)
    return "OK", f"{len(content) // 1024} KB"


def main() -> int:
    ap = argparse.ArgumentParser(description="Download the 200-paper corpus from corpus_papers.csv")
    ap.add_argument("--csv", default=str(MANIFEST), help=f"the manifest; default {MANIFEST.name} beside this script")
    ap.add_argument("--output", default="./corpus", help="output directory (default ./corpus)")
    ap.add_argument("--only", choices=["core", "noise"], help="one bucket only")
    ap.add_argument("--limit", type=int, default=None, help="stop after N papers")
    ap.add_argument("--dry-run", action="store_true", help="list the papers and URLs, download nothing")
    a = ap.parse_args()

    csv_path = Path(a.csv)
    if not csv_path.exists():
        print(f"ERROR: manifest not found: {csv_path}", file=sys.stderr)
        return 1
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if a.only:
        rows = [r for r in rows if r["bucket"] == a.only]
    if a.limit:
        rows = rows[: a.limit]
    out = Path(a.output)

    print(f"Manifest: {csv_path}")
    print(f"Output:   {out}")
    print(f"Papers:   {len(rows)}")
    print("=" * 78)

    if a.dry_run:
        for r in rows:
            print(f"[{r['paper_id']:>3}] {r['bucket']:5s} {r['filename']:38s} {r['source_url']}")
        return 0

    counts = {"OK": 0, "SKIP": 0, "FAIL": 0}
    failures = []
    for i, r in enumerate(rows, 1):
        dest = out / r["bucket"] / r["filename"]
        status, msg = download_one(r["source_url"], dest)
        counts[status] += 1
        print(f"[{i:3d}/{len(rows)}] [{status:4s}] {r['filename']:38s} {msg}")
        if status == "FAIL":
            failures.append(r)
        if status != "SKIP":
            time.sleep(SLEEP_BETWEEN)

    print("=" * 78)
    print(f"Summary:  OK {counts['OK']}   SKIP {counts['SKIP']}   FAIL {counts['FAIL']}")
    if failures:
        print("\nFailed downloads, fetch by hand and place under the output directory:")
        for r in failures:
            print(f"  paper_id={r['paper_id']:>3} {r['bucket']}/{r['filename']}  doi={r['doi'] or '-'}  pmcid={r['pmcid'] or '-'}")
            print(f"      {r['source_url']}")
    return 0 if counts["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
