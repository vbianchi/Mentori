"""A curated answer key other than the paper's v2.4, in the form the runner, the judge and the scorers read (I2, D160 (14)).

    from experiments.reuse_demo import plant_key as PK
    key = PK.load()                       # key_v1_1.json, sha256-pinned (KEY_SHA256), checked as below
    key.questions()                       # the runner's FIELDS dicts (experiments/runner/experiment.py FIELDS), key order
    key.key_questions()                   # id -> {id, question, answerable, answer_type, ...}: records.py's key_questions form
    key.v2(), key.v1()                    # S373's two dicts: key_of / key_hash read v2, judged_answerable reads v1
    PK.load("my_key.json", sha256=None)   # a reader's own key (GUIDE.md step 2); None: no pin, the sha256 is reported

WHY. Every runner and scorer of the paper reads answer key v2.4 (data/ground_truth_v2/all_v2_4.json) and refuses any
other (i2_plan.md F2 to F4). The plant-science key (experiments/reuse_demo/key_v1_1.json, signed off 26 October, D153)
has the v2.4 record format (its "format" field names it) plus "support" and "min_core". This module reads such a key
and gives it in the forms those programs read, so the I2 wrappers (i2_generate.py, i2_judge.py) can hand it to the
unchanged paper code. Nothing here changes what any paper script does by default: the wrappers replace the key only
inside their own process.

WHAT IS CHECKED (KeyProblem on any failure, before anything is returned):
  - the file's sha256 equals the pin (when one is given);
  - "format" names v2.4 and "records" is a non-empty list with unique ids;
  - every record has the v2.4 fields the programs read: id, question, category, question_answerable (a bool),
    answer_type (extractive, synthesis, refutation or not_answerable, the four Rule 8 places), short_answer,
    key_concepts (a list of {"phrase": text});
  - question_answerable is False exactly for not_answerable (a refutation is answerable: Q51, D5);
  - a not-answerable record has no key concepts (as in v2.4);
  - an answerable record has an integer min_core; a not-answerable one has min_core None (the v1 form, S381).
The runner's "answerable" is question_answerable, as experiment.py _key() reads v2.4's.

Standard library only: it runs in Mentori's environment (the generation driver) and in the repository's (the judge).
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KEY = HERE / "key_v1_1.json"
KEY_SHA256 = "eb58a724f10382f478a25c68ec3b52260c398ce912e071ff8ba5a7647d9e5487"   # signed-off status stamped 27 Oct (A9)
FORMAT_VERSION = "2.4"
ANSWER_TYPES = ("extractive", "synthesis", "refutation", "not_answerable")
FIELDS = ("id", "question", "category", "answerable", "answer_type", "short_answer", "key_concepts", "min_core")


class KeyProblem(Exception):
    """A key that is not in the form the programs read."""


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Key:
    """One checked key: path, sha256, the records in file order."""

    def __init__(self, path: Path, digest: str, data: dict):
        self.path, self.sha256, self.data = Path(path), digest, data
        self.records = data["records"]
        self.ids = [r["id"] for r in self.records]

    def questions(self) -> list[dict]:
        """The runner's question dicts (experiment.py FIELDS), in the key's order, fresh copies."""
        return [{"id": r["id"], "question": r["question"], "category": r["category"],
                 "answerable": r["question_answerable"], "answer_type": r["answer_type"],
                 "short_answer": r["short_answer"], "key_concepts": copy.deepcopy(r["key_concepts"]),
                 "min_core": r.get("min_core")} for r in self.records]

    def key_questions(self) -> dict:
        """id -> question, the form records.py key_questions() gives (experiment.py _key() entries)."""
        return {q["id"]: q for q in self.questions()}

    def v2(self) -> dict:
        """id -> record (S373 key_of, key_hash, refutation read this)."""
        return {r["id"]: r for r in self.records}

    def v1(self) -> dict:
        """id -> {"id", "answerable"} (S373 judged_answerable reads v1[qid]["answerable"])."""
        return {r["id"]: {"id": r["id"], "answerable": r["question_answerable"]} for r in self.records}

    def describe(self) -> dict:
        """What a run records about its key."""
        return {"path": str(self.path), "sha256": self.sha256, "version": self.data.get("version"),
                "n_questions": len(self.records),
                "answer_types": {t: sum(r["answer_type"] == t for r in self.records) for t in ANSWER_TYPES}}


def check(data: dict) -> list[str]:
    """Every problem of a key's content (WHAT IS CHECKED, the sha256 aside); empty when it is in the readers' form."""
    bad = []
    fmt = data.get("format") if isinstance(data, dict) else None
    if not isinstance(fmt, dict) or fmt.get("version") != FORMAT_VERSION:
        bad.append(f"format: {fmt!r}, not the v{FORMAT_VERSION} record format")
    recs = data.get("records") if isinstance(data, dict) else None
    if not isinstance(recs, list) or not recs:
        return bad + ["records: not a non-empty list"]
    seen = set()
    for i, r in enumerate(recs):
        rid = r.get("id") if isinstance(r, dict) else None
        where = f"record {i} ({rid})"
        if not isinstance(rid, str) or not rid or any(c in rid for c in " |"):
            bad.append(f"{where}: id must be a string without spaces or '|'")
        elif rid in seen:
            bad.append(f"{where}: id repeated")
        seen.add(rid)
        if not isinstance(r, dict):
            continue
        for f in ("question", "category", "short_answer"):
            if not isinstance(r.get(f), str) or not r[f].strip():
                bad.append(f"{where}: {f} missing or empty")
        if not isinstance(r.get("question_answerable"), bool):
            bad.append(f"{where}: question_answerable {r.get('question_answerable')!r}, not a bool")
        at = r.get("answer_type")
        if at not in ANSWER_TYPES:
            bad.append(f"{where}: answer_type {at!r}, not one of {ANSWER_TYPES}")
        kc = r.get("key_concepts")
        if not isinstance(kc, list) or not all(isinstance(k, dict) and isinstance(k.get("phrase"), str)
                                               and k["phrase"].strip() for k in kc):
            bad.append(f"{where}: key_concepts must be a list of {{'phrase': text}}")
            kc = None
        if at in ANSWER_TYPES and isinstance(r.get("question_answerable"), bool):
            if r["question_answerable"] != (at != "not_answerable"):
                bad.append(f"{where}: question_answerable {r['question_answerable']} with answer_type {at}")
        mc = r.get("min_core")
        if at == "not_answerable":
            if kc:
                bad.append(f"{where}: a not-answerable record has key concepts")
            if mc is not None:
                bad.append(f"{where}: a not-answerable record has min_core {mc!r}, not None")
        elif at in ANSWER_TYPES and (isinstance(mc, bool) or not isinstance(mc, int) or mc < 1):
            bad.append(f"{where}: an answerable record needs an integer min_core, got {mc!r}")
        if "synthesis_statement" in r and not isinstance(r["synthesis_statement"], str):
            bad.append(f"{where}: synthesis_statement is not text")
    return bad


def load(path: Path | str = KEY, sha256: str | None = KEY_SHA256) -> Key:
    """The checked key at path. sha256: the pin (KEY_SHA256 for the default key); None reads without a pin."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise KeyProblem(f"{path}: cannot read ({e})") from None
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and digest != sha256:
        raise KeyProblem(f"{path} has sha256 {digest}, not the pinned {sha256}")
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise KeyProblem(f"{path}: not JSON ({e})") from None
    bad = check(data)
    if bad:
        raise KeyProblem(f"{path}: {len(bad)} problems: " + "; ".join(bad[:6]))
    return Key(path, digest, data)


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else KEY
    k = load(p, KEY_SHA256 if Path(p).resolve() == KEY.resolve() else None)
    print(json.dumps(k.describe(), indent=1))
