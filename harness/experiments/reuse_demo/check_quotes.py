"""Adversarial quote check for experiments/reuse_demo/key_draft.json (or the key file named as the second argument,
e.g. key_v1.json).

For every support entry: is the quote on that page of text/<file>.pages.json?
Levels, first that matches wins:
  raw        exact substring of the page string
  ws         whitespace runs collapsed to one space on both sides
  hyph-join  as ws, and on the page 'x-<newline>y' joined to 'xy'
  hyph-keep  as ws, and on the page 'x-<newline>y' kept as 'x-y'
  nospace    all whitespace removed on both sides (spacing differences inside words)
  MISSING    none of the above; closest window printed
Also: occurrences on other pages, evidence[i].sentence == support[i].quote, same page and paper,
key concept phrase is a substring of its evidence sentence.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
KEY = sys.argv[2] if len(sys.argv) > 2 else "key_draft.json"
key = json.loads((ROOT / KEY).read_text())
pages_cache = {}


def pages(fname):
    if fname not in pages_cache:
        pages_cache[fname] = json.loads((ROOT / "text" / f"{fname}.pages.json").read_text())
    return pages_cache[fname]


def ws(s):
    return re.sub(r"\s+", " ", s).strip()


def hyph_join(s):
    return re.sub(r"(\w) ?- ?\n\s*(\w)", r"\1\2", s)


def hyph_keep(s):
    return re.sub(r"(\w) ?- ?\n\s*(\w)", r"\1-\2", s)


def nospace(s):
    return re.sub(r"\s+", "", s)


def level(quote, page):
    if quote in page:
        return "raw", page.count(quote)
    q = ws(quote)
    for name, f in (("ws", lambda p: p), ("hyph-join", hyph_join), ("hyph-keep", hyph_keep)):
        p = ws(f(page))
        if q in p:
            return name, p.count(q)
    for f in (lambda p: p, hyph_join, hyph_keep):
        if nospace(quote) in nospace(f(page)):
            return "nospace", nospace(f(page)).count(nospace(quote))
    return "MISSING", 0


def closest(quote, page):
    q = ws(quote)
    p = ws(hyph_join(page))
    sm = difflib.SequenceMatcher(None, p, q, autojunk=False)
    m = sm.find_longest_match(0, len(p), 0, len(q))
    start = max(0, m.a - m.b - 20)
    return p[start:start + len(q) + 40]


bad = 0
for rec in key["records"]:
    rid = rec["id"]
    ev = rec["evidence"]
    sup = rec["support"]
    if len(ev) != len(sup):
        print(f"{rid} DEFECT evidence has {len(ev)} items, support has {len(sup)}")
        bad += 1
    for i, s in enumerate(sup):
        fname, pg, quote = s["paper"], s["page"], s["quote"]
        pp = pages(fname)
        lv, n = level(quote, pp[pg - 1])
        others = [j + 1 for j, p in enumerate(pp) if j != pg - 1 and level(quote, p)[0] != "MISSING"]
        flag = "" if lv != "MISSING" and n == 1 and not others else "  <-- CHECK"
        print(f"{rid} s{i} {fname[:2]} p{pg} level={lv} count_on_page={n} also_on_pages={others}{flag}")
        if lv == "MISSING":
            bad += 1
            print("    quote  :", ws(quote))
            print("    closest:", closest(quote, pp[pg - 1]))
        if lv == "hyph-join" or lv == "hyph-keep" or lv == "nospace":
            # show the page passage raw so the difference can be reported
            q0 = nospace(quote)[:25]
            raw = pp[pg - 1]
            idx = nospace(raw).find(q0)
            print(f"    note: matched only at level {lv}")
        if i < len(ev):
            e = ev[i]
            if e["sentence"] != quote:
                print(f"    DEFECT evidence[{i}].sentence differs from support quote")
                bad += 1
            if e["page"] != pg or e["paper"] + ".pdf" != fname:
                print(f"    DEFECT evidence[{i}] paper/page {e['paper']} p{e['page']} vs support {fname} p{pg}")
                bad += 1
    for k in rec["key_concepts"]:
        sent = ev[k["evidence_index"]]["sentence"]
        if k["phrase"] not in sent:
            print(f"{rid} DEFECT key concept {k['phrase']!r} not in evidence[{k['evidence_index']}]")
            bad += 1
        else:
            print(f"{rid} kc ok {k['phrase']!r} -> evidence[{k['evidence_index']}]")

print(f"\n{KEY}: TOTAL support entries: {sum(len(r['support']) for r in key['records'])}; defects: {bad}")
