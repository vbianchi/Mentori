#!/usr/bin/env python3
"""One text file per paper, one string per page, for checking a key's quotes and for MiniCheck against the papers
(GUIDE.md steps 2 and 5).

    uv run --project experiments/mentori --frozen python experiments/reuse_demo/page_text.py \
        --corpus my_corpus/core --out my_corpus/text

For each PDF of --corpus, writes <out>/<file name>.pages.json: a JSON list holding the text pypdf extracts from each
page, in page order (page 1 first). An existing file is never overwritten: the key's quotes were checked against it,
so a new extraction would move the ground under them. The pypdf version is printed and written to <out>/pages.txt.

The I2 texts (experiments/reuse_demo/text/) were made on 16 October with a pypdf whose version was not recorded; the
pypdf in experiments/mentori's environment (6.7.5 on 27 October) gives text that differs from them on 44 of their 61
pages (182 characters in all, at most 15 on one page, by difflib's count), so they are kept as they are and this script refuses to write over
them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    import pypdf
    pdfs = sorted(a.corpus.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"REFUSED: {a.corpus} holds no PDF")
    exists = [p.name for p in pdfs if (a.out / f"{p.name}.pages.json").exists()]
    if exists:
        raise SystemExit(f"REFUSED: {a.out} already holds the text of {exists}; nothing written (never overwritten)")
    a.out.mkdir(parents=True, exist_ok=True)
    for p in pdfs:
        pages = [pg.extract_text() for pg in pypdf.PdfReader(str(p)).pages]
        (a.out / f"{p.name}.pages.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        print(f"{p.name}: {len(pages)} pages, {sum(map(len, pages)):,} characters")
    (a.out / "pages.txt").write_text(f"pypdf {pypdf.__version__}\n", encoding="utf-8")
    print(f"pypdf {pypdf.__version__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
