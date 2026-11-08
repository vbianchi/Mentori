#!/usr/bin/env python3
"""make_frozen_supp - D155: freeze the inputs of Figure 2 and Supplementary Figures 2, 11 and 12 that make_frozen.py
did not.

WHY. D155 (Valerio, 26 October): one command rebuilds every figure from frozen inputs, byte-equal to the committed
plate. Three inputs of these plates sat outside every frozen set on 26 October:
  1. Supplementary Figure 2 (S461) reads five records of the submitted deposit (publication/results/exp0*_latest.json)
     from a sibling checkout (scripts/machine.py, "<upstream>"), outside this repository; Figure 2 (S463, panel b)
     reads a sixth, exp00_phase2_latest.json, through S471's gate (S432's 107 values). Their sha256 are in
     data/upstream/MANIFEST.sha256 (and the five in Supplementary Figure 2's provenance, the sixth in S432's). They
     are 6.0 MB, so they are committed: findings/recompute/upstream_inputs/publication/results/.
  2. Supplementary Figure 11 (S457) reads the authors' RLM records at caps 5, 10 and 20, answers.jsonl and
     calls.jsonl, from the gitignored findings/runs/b4_rlm_ref__cap{5,10,20}__all135/. The D89 rerun of 24 October
     rewrote both files there; the bytes the plate read (sha256 in its provenance) survive only as
     findings/runs/<run>/discarded_D89/{answers,calls}.jsonl.before_rerun. The three calls files are 1.0 GB, so they
     go into a tar, g6_calls_before_d89.tar, kept outside git like the other tars (findings/recompute/frozen_inputs/
     README.md). The ten answers files of the same runs are frozen by another D155 step in
     findings/recompute/L2_inputs/g6/ (the same bytes); this script checks that copy and does not make a second one.
  3. Both S457 and S459 stamp their plate with the newest record's modification time ("records of ..."). A frozen
     copy does not keep it (git sets the checkout time; the tars hold mtime 0), so the source mtimes are written to
     g6_before_d89_mtimes.json, beside each file's sha256, and the scripts read them from there.

WHAT IT DOES (nothing is read from the Studio; nothing outside this folder, upstream_inputs/ and the tar folder is
written):
  - copies the six deposit records, each required equal to its line in data/upstream/MANIFEST.sha256 and (the five
    of Supplementary Figure 2) to the sha256 that plate's committed provenance records;
  - builds g6_calls_before_d89.tar in the tar folder (env FROZEN_TARS, default ~/Mentori_scratch_keep/
    frozen_2026-10-26): Python tarfile, PAX, uncompressed, members sorted under the top folder g6_calls_before_d89/,
    every member mtime 0, uid and gid 0, empty owner names, the source's mode (make_frozen.py's format); every member
    equal to its source and to the sha256 Supplementary Figure 11's provenance records; built twice, the same sha256;
  - writes members/g6_calls_before_d89.sha256 and g6_before_d89_mtimes.json;
  - prints the SHA256SUMS lines to add (the committed files and the tar), and writes nothing into SHA256SUMS itself
    (another D155 step holds uncommitted lines in it; the lines are added by hand, in sorted place).

    uv run python findings/recompute/frozen_inputs/make_frozen_supp.py [--check]

--check builds nothing: it re-reads every source and every frozen copy and requires the recorded sha256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
TAR_DIR = Path(os.environ.get("FROZEN_TARS", str(Path.home() / "Mentori_scratch_keep" / "frozen_2026-10-26")))
RUNS = REPO / "findings" / "runs"
UPSTREAM_OUT = REPO / "findings" / "recompute" / "upstream_inputs"
L2_G6 = REPO / "findings" / "recompute" / "L2_inputs" / "g6"
TOP = "g6_calls_before_d89"
TAR = f"{TOP}.tar"
MTIMES = HERE / "g6_before_d89_mtimes.json"
PROV2 = REPO / "findings/figures_provisional/supp_fig2/supplementary_figure2_provenance.json"
PROV11 = REPO / "findings/figures_provisional/supp_fig6_outcomes/supplementary_figure6_provenance.json"
PROV12 = REPO / "findings/figures_provisional/supp_fig10_package_caps/supplementary_figure10_provenance.json"
SUPP2_FILES = ["exp01_embedding_latest.json", "exp02_search_latest.json", "exp03a_chunking_latest.json",
               "exp03b_scalability_latest.json", "exp04_generation_latest.json"]
FIG2_FILES = ["exp00_phase2_latest.json"]          # S471's gate (S463 panel b); S471 checks it against S432's record
G6_ALL135 = [f"b4_rlm_ref__cap{c}__all135" for c in (5, 10, 20)]
G6_RUNS = G6_ALL135 + [f"b4_rlm_ref__cap{c}__depthsweep86" for c in (1, 2, 3, 7, 15, 30, 50)]


class Refused(SystemExit):
    pass


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def recorded(prov: Path) -> dict:
    """The plate's recorded inputs, keyed by the source names its provenance used before D155 (a rebuilt provenance
    names them by their frozen labels: those are mapped back, so --check holds before and after the rebuild)."""
    import re
    j = json.loads(prov.read_text())
    out = {}
    for k, v in (j.get("provenance") or j)["inputs_sha256"].items():
        k = re.sub(r"^frozen:upstream/", "<upstream>/", k)
        k = re.sub(r"^frozen:L2/g6/", "findings/runs/", k)
        k = re.sub(rf"^frozen:{TOP}\.tar/{TOP}/", "findings/runs/", k)
        out[k] = v
    return out


def upstream_manifest() -> dict:
    out = {}
    for ln in (REPO / "data/upstream/MANIFEST.sha256").read_text().splitlines():
        if ln.strip():
            h, p = ln.split(None, 1)
            out[p.strip()] = h
    return out


def supp2(check: bool) -> list[tuple[str, str]]:
    import machine
    man, rec = upstream_manifest(), recorded(PROV2)
    lines = []
    for n in SUPP2_FILES + FIG2_FILES:
        rel = f"publication/results/{n}"
        want = man.get(rel)
        if want is None or (n in SUPP2_FILES and rec.get(f"<upstream>/{rel}") != want):
            raise Refused(f"{rel}: data/upstream/MANIFEST.sha256 {str(want)[:12]} and the plate's provenance "
                          f"{str(rec.get(f'<upstream>/{rel}'))[:12]} do not agree")
        dst = UPSTREAM_OUT / rel
        if not check:
            src = machine.RESULTS / n
            if sha(src) != want:
                raise Refused(f"{src}: sha256 is not data/upstream/MANIFEST.sha256's {want[:12]}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        if sha(dst) != want:
            raise Refused(f"{dst}: sha256 is not {want[:12]}")
        lines.append((want, str(dst.relative_to(REPO))))
    print(f"upstream_inputs: {len(lines)} of {len(SUPP2_FILES + FIG2_FILES)} files equal to "
          f"data/upstream/MANIFEST.sha256 (and {len(SUPP2_FILES)} to Supplementary Figure 2's provenance)")
    return lines


def g6_sources() -> tuple[dict, dict]:
    """{run: (answers source, calls source or None)} from discarded_D89, each checked against the plates' records."""
    r11, r12 = recorded(PROV11), recorded(PROV12)
    want = {}
    for k, v in list(r11.items()) + list(r12.items()):
        if k.startswith("findings/runs/b4_rlm_ref__"):
            if want.setdefault(k, v) != v:
                raise Refused(f"{k}: the two plates record different sha256")
    src = {}
    for run in G6_RUNS:
        a = RUNS / run / "discarded_D89" / "answers.jsonl.before_rerun"
        c = RUNS / run / "discarded_D89" / "calls.jsonl.before_rerun" if run in G6_ALL135 else None
        for p, key in ((a, f"findings/runs/{run}/answers.jsonl"), (c, f"findings/runs/{run}/calls.jsonl")):
            if p is None:
                continue
            if key not in want:
                raise Refused(f"{key}: no plate records its sha256")
            got = sha(p)
            if got != want[key]:
                raise Refused(f"{p}: sha256 {got[:12]} is not the {want[key][:12]} the plates record for {key}")
        src[run] = (a, c)
    return src, want


def build_tar(members: list[tuple[str, Path]], fobj) -> dict:
    """make_frozen.py's tar format; returns {member path: sha256 of the bytes written}."""
    written = {}
    dirs = sorted({str(Path(m).parent) for m, _ in members} - {"."})
    entries = [("", None)] + [(d + "/", None) for d in dirs] + sorted(members)
    entries.sort(key=lambda e: e[0])
    with tarfile.open(fileobj=fobj, mode="w|", format=tarfile.PAX_FORMAT) as tf:
        for rel, p in entries:
            ti = tarfile.TarInfo(TOP + ("/" + rel.rstrip("/") if rel else ""))
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
            if p is None:
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
                tf.addfile(ti)
                continue
            ti.type, ti.size, ti.mode = tarfile.REGTYPE, p.stat().st_size, p.stat().st_mode & 0o7777
            h = hashlib.sha256()

            class R:
                def __init__(self, f):
                    self.f = f

                def read(self, n=-1):
                    b = self.f.read(n)
                    h.update(b)
                    return b

            with open(p, "rb") as f:
                tf.addfile(ti, R(f))
            written[rel] = h.hexdigest()
    return written


class HashSink:
    def __init__(self, f=None):
        self.h, self.f = hashlib.sha256(), f

    def write(self, b):
        self.h.update(b)
        if self.f:
            self.f.write(b)
        return len(b)


def g6(check: bool) -> tuple[str, str]:
    src, want = g6_sources()
    members = [(f"{run}/calls.jsonl", src[run][1]) for run in G6_ALL135]
    expect = {m: want[f"findings/runs/{m}"] for m, _ in members}
    tar = TAR_DIR / TAR
    if not check:
        if tar.exists():
            raise Refused(f"{tar} exists; remove it to build again, or run --check")
        TAR_DIR.mkdir(parents=True, exist_ok=True)
        with open(tar, "xb") as f:
            sink = HashSink(f)
            written = build_tar(members, sink)
        if written != expect:
            raise Refused(f"{TAR}: member bytes differ from the recorded sha256")
        again = HashSink()
        build_tar(members, again)
        if again.h.hexdigest() != sink.h.hexdigest():
            raise Refused(f"{TAR}: a second build gives another sha256; not deterministic")
        (HERE / "members" / f"{TOP}.sha256").write_text("".join(f"{expect[m]}  {TOP}/{m}\n" for m in sorted(expect)))
    tar_sha = sha(tar)
    with tarfile.open(tar) as tf:
        names = sorted(m.name for m in tf.getmembers() if m.isfile())
    if names != sorted(f"{TOP}/{m}" for m in expect):
        raise Refused(f"{TAR}: members {names} are not the three calls files")
    listed = dict(reversed(ln.split("  ", 1)) for ln in (HERE / "members" / f"{TOP}.sha256").read_text().splitlines())
    if listed != {f"{TOP}/{m}": h for m, h in expect.items()}:
        raise Refused(f"members/{TOP}.sha256 does not list the recorded sha256")
    print(f"{TAR}: {tar.stat().st_size / 1e6:.1f} MB, {len(names)} files, sha256 {tar_sha}, every member equal to "
          f"Supplementary Figure 11's recorded sha256" + ("" if check else "; a second build gave the same sha256"))
    # the answers: frozen once, by the L2 step, in L2_inputs/g6/
    for run in G6_RUNS:
        p = L2_G6 / run / "answers.jsonl"
        k = f"findings/runs/{run}/answers.jsonl"
        if not p.exists() or sha(p) != want[k]:
            raise Refused(f"{p}: missing or not the {want[k][:12]} the plates record (L2_inputs/g6 is another D155 "
                          f"step's set)")
    print(f"L2_inputs/g6: {len(G6_RUNS)} of {len(G6_RUNS)} answers files equal to the plates' recorded sha256")
    # mtimes of the sources (the plates' stamps); kept from the first build, checked against the sources after
    rec = {}
    for run in G6_RUNS:
        a, c = src[run]
        rec[f"findings/runs/{run}/answers.jsonl"] = {"sha256": want[f"findings/runs/{run}/answers.jsonl"],
                                                     "mtime": int(a.stat().st_mtime), "source": str(a.relative_to(REPO))}
        if c is not None:
            rec[f"findings/runs/{run}/calls.jsonl"] = {"sha256": want[f"findings/runs/{run}/calls.jsonl"],
                                                       "mtime": int(c.stat().st_mtime),
                                                       "source": str(c.relative_to(REPO))}
    body = {"what": "the modification time (seconds since 1970, UTC) each G6 record had when Supplementary Figures 11 "
                    "and 12 read it (23 October 2026), read from its surviving copy findings/runs/<run>/discarded_D89/"
                    "<file>.before_rerun (the D89 rerun of 24 October moved the files there, keeping their mtimes); "
                    "the plates' stamps print the newest. Keyed by the path the plates' provenance names.",
            "frozen_at": {"answers": "findings/recompute/L2_inputs/g6/<run>/answers.jsonl",
                          "calls": f"{TAR}: {TOP}/<run>/calls.jsonl"},
            "files": rec}
    text = json.dumps(body, indent=1, sort_keys=True) + "\n"
    if check:
        if MTIMES.read_text() != text:
            raise Refused(f"{MTIMES.name}: differs from the sources now")
    else:
        MTIMES.write_text(text)
    print(f"{MTIMES.name}: {len(rec)} files, newest {max(v['mtime'] for v in rec.values())}")
    return tar_sha, TAR


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    lines = supp2(a.check)
    tar_sha, tname = g6(a.check)
    lines.append((sha(MTIMES), str(MTIMES.relative_to(REPO))))
    print("SHA256SUMS lines (committed files, then the tar):")
    for h, n in lines + [(tar_sha, tname)]:
        print(f"{h}  {n}")
    print("PASS")


if __name__ == "__main__":
    main()
