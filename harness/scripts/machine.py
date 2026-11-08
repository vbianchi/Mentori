#!/usr/bin/env python3
"""The machine registry: one place that owns where things are on THIS computer.

Every path in this repo used to be spelled out in full, ninety-odd times, always as an absolute
path under one user's home directory. That was true on one laptop and false everywhere else, and
on 1 September 2026 the laptop went to the repair centre. The work moved to Linux and eighty-nine
scripts stopped resolving.

So the rule this module exists to enforce: a script names WHAT it wants, never WHERE it is.

    from machine import RESULTS, ROOT
    raw = json.loads((RESULTS / "exp04_generation_latest.json").read_text())

Four roots, and they are not the same root, which is the trap this module is mostly here to
close:

  ROOT        this repo, always derived from __file__, never configured
  UPSTREAM    the paper repo whose publication/ tree holds the raw evaluation JSON. On the mac
              that was ~/projects/Mentori-paper; here it is data/upstream or a sibling checkout
  HARNESS     the git repo whose branch is restore-harness, which S01b and S62 interrogate with
              `git -C`. It is a DIFFERENT checkout from UPSTREAM: on the mac, Mentori-paper had
              origin Mentori.git while Mentori had origin Mentori-Old.git, and the names have
              not travelled. One variable cannot serve both, so there are two
  CORPUS        the 200 source PDFs, core/ and noise/. The three scripts that read them named a
              Mentori-backup checkout that exists on no current machine; the same bytes are in
              the upstream corpus, verified by the sha256 already recorded in
              findings/recompute/S18_evidence_manifest.json

Resolution, in order, for each of the three configurable roots: the environment variable, then
the vendored copy under data/upstream, then a sibling checkout beside this repo that actually
carries the goods. Nothing is guessed from the operating system, so the same rules give the same
answer on macOS and on Linux.

    MENTORI_PAPER     upstream data root      (default: data/upstream, then a sibling)
    MENTORI_HARNESS   the restore-harness git checkout
    MENTORI_CHROME    the Chrome binary, for the two scripts that rasterise SVG through it
    MENTORI_SCRATCH   scratch directory       (default: the platform temp dir)

Import is always cheap and never fails: a root that cannot be found resolves to where it OUGHT
to be, so a script that only wants ROOT is never blocked by absent upstream data. A script that
does need the data calls require() and gets one sentence saying what to run.

Provenance blocks call rel(), not str(). A recorded path must say which root it hangs off rather
than which machine wrote it, because doctor_rerun diffs today's artifact against the committed
one and does not treat a path as volatile. Absolute paths in that block make every re-run a
false DIFFERS; symbolic ones make the artifact mean the same thing on both machines.

An artifact that ships in the deposit records its paths through shown(): deposit/<path> for the
upstream data, the repository-relative path for this repo. Those are the names a reader of the
Zenodo deposit finds on disk, and no shipped file then names a machine's home directory
(Valerio, 30 September).
"""
from __future__ import annotations
import os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "data/upstream"

# Sibling checkouts, in preference order. Mentori-paper is the name the mac used and the name
# README.md still documents; Mentori-Old is what the same repo is called on this machine; Mentori
# is the public one, whose publication/results is empty until download_results.sh has run.
SIBLINGS = ("Mentori-paper", "Mentori-Old", "Mentori")

# What makes a candidate the real thing rather than an empty scaffold. The public repo ships
# publication/results/README.md and nothing else, so presence of the directory proves nothing.
UPSTREAM_MARK = "publication/results/exp04_generation_latest.json"
HARNESS_BRANCH = "restore-harness"

# Helvetica first because that is what the figures were drawn in and what the gates name. The
# rest are metric-compatible clones: same advance widths, so a plate set in one of them lays out
# identically and only the outlines differ. DejaVu is NOT on this list -- it is 13.7% wider, it
# is what matplotlib falls back to when it finds nothing else, and a plate drawn in it is the
# failure the font gates exist to catch.
HELVETICA_METRIC = ("Helvetica", "Arial", "Liberation Sans", "Nimbus Sans", "Helvetica Neue")

CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
CHROME_BUNDLES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
)


def _env_root(var: str) -> Path | None:
    """A configured root. Set and wrong is an error; unset is not."""
    raw = os.environ.get(var)
    if not raw:
        return None
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        raise SystemExit(f"{var} is set to {p}, which is not a directory")
    return p


def _find_upstream() -> Path:
    p = _env_root("MENTORI_PAPER")
    if p:
        return p
    for cand in (VENDOR, *(ROOT.parent / name for name in SIBLINGS)):
        if (cand / UPSTREAM_MARK).exists():
            return cand
    return VENDOR                      # where it ought to be, so the message names one place


def _find_harness() -> Path:
    """The checkout S01b and S62 read git metadata from, identified by its branch, not its name."""
    p = _env_root("MENTORI_HARNESS")
    if p:
        return p
    for cand in (ROOT.parent / name for name in SIBLINGS):
        if not (cand / ".git").exists():
            continue
        # A fresh clone carries the branch only as a remote-tracking ref, so ask for both.
        for ref in (HARNESS_BRANCH, f"origin/{HARNESS_BRANCH}"):
            r = subprocess.run(["git", "-C", str(cand), "rev-parse", "--verify", ref],
                               capture_output=True, text=True)
            if r.returncode == 0:
                return cand
    return UPSTREAM


UPSTREAM = _find_upstream()
PUB = UPSTREAM / "publication"
RESULTS = PUB / "results"
DEEP = RESULTS / "deep_analyses"
PUB_DATA = PUB / "data"
PUB_SCRIPTS = PUB / "scripts"
FIGURES = PUB / "figures"
FIGURES_REGEN = PUB / "figures_regen"
CORPUS = PUB_DATA / "corpus"

# HARNESS is found on first use, not at import (D155): finding it runs `git -C` on each sibling
# checkout, and a figure build that imports this module for ROOT or rel() must not reach a sibling
# (scripts/fig_read_audit.py fails a step that does). `from machine import HARNESS` and
# machine.HARNESS still work, through the module __getattr__ below.
_HARNESS: Path | None = None


def _harness() -> Path:
    global _HARNESS
    if _HARNESS is None:
        _HARNESS = _find_harness()
    return _HARNESS


def __getattr__(name: str):
    if name == "HARNESS":
        return _harness()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

RECOMPUTE = ROOT / "findings/recompute"


def have_upstream() -> bool:
    return (UPSTREAM / UPSTREAM_MARK).exists()


def require(*paths: Path) -> None:
    """Refuse to start, naming the one command that fixes it, rather than dying on a read."""
    missing = [p for p in (paths or (UPSTREAM / UPSTREAM_MARK,)) if not Path(p).exists()]
    if not missing:
        return
    lines = ["this script needs upstream data that is not on this machine:"]
    lines += [f"    {rel(p)}" for p in missing]
    lines.append("")
    lines.append("    uv run python scripts/bootstrap_upstream.py")
    lines.append("")
    lines.append(f"populates {rel(VENDOR)} from a sibling checkout or from the Zenodo deposit.")
    lines.append("Or point MENTORI_PAPER at a checkout that already has it.")
    raise SystemExit("\n".join(lines))


def corpus_pdf(name: str) -> Path:
    """A source PDF by filename. The corpus is split core/ and noise/; callers know neither."""
    for sub in ("core", "noise"):
        p = CORPUS / sub / name
        if p.exists():
            return p
    hits = sorted(CORPUS.rglob(name))
    if hits:
        return hits[0]
    require(CORPUS / "core" / name)
    raise SystemExit(f"no {name} anywhere under {rel(CORPUS)}")


def chrome() -> Path | None:
    """The Chrome binary, or None. Two scripts rasterise SVG through it and say so when absent."""
    raw = os.environ.get("MENTORI_CHROME")
    if raw:
        p = Path(raw).expanduser()
        return p if p.exists() else None
    for name in CHROME_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found)
    for bundle in CHROME_BUNDLES:
        if Path(bundle).exists():
            return Path(bundle)
    return None


def scratch(name: str = "mentori") -> Path:
    """A writable scratch directory. The mac wrote to /private/tmp/claude-501, which is nowhere."""
    base = os.environ.get("MENTORI_SCRATCH") or tempfile.gettempdir()
    p = Path(base).expanduser() / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def sans_family() -> str:
    """The first Helvetica-metric face matplotlib can actually resolve on this machine.

    matplotlib does not consult fontconfig aliases, so asking for Helvetica on a box that has
    only Liberation Sans silently yields DejaVu Sans while still writing "Helvetica" into the
    SVG. That is how a font gate certifies a plate it never inspected. Ask this instead, and the
    name written is the name resolved.
    """
    from matplotlib import font_manager as fm         # imported here: most callers never plot

    have = {f.name for f in fm.fontManager.ttflist}
    for family in HELVETICA_METRIC:
        if family in have:
            return family
    raise SystemExit(
        "no Helvetica-metric font on this machine, so any plate drawn here would be set in\n"
        "DejaVu Sans, which is 13.7% wider and fails the figure specification. Install one:\n"
        "    sudo apt install fonts-liberation      # Linux, metric-compatible with Helvetica\n"
        f"tried: {', '.join(HELVETICA_METRIC)}")


def is_metric_helvetica(family: str) -> bool:
    """Does this family carry Helvetica's metrics? The question every font gate means to ask."""
    return family.strip().strip("'\"") in HELVETICA_METRIC


def torch_device() -> str:
    """mps on the mac, cuda where there is one, else cpu.

    Embeddings computed on a different device differ in the last bits, which is past
    doctor_rerun's 1e-9 tolerance. A script whose artifact was built on mps and is re-run on cpu
    is expected to DIFFER, and that is a real difference, not a porting defect.
    """
    try:
        import torch
    except ImportError:
        return "cpu"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def rel(p) -> str:
    """A path as it should be RECORDED: which root it hangs off, not which machine wrote it.

        <repo>/findings/recompute/S03_master.csv
        <upstream>/publication/results/exp04_generation_latest.json

    Anything under no known root is returned whole, because hiding it would be worse.
    """
    q = Path(p).expanduser()
    q = q.resolve() if q.is_absolute() else (ROOT / q).resolve()
    for base, tag in ((ROOT, "<repo>"), (UPSTREAM, "<upstream>")):
        try:
            return f"{tag}/{q.relative_to(base).as_posix()}"
        except ValueError:
            continue
    # HARNESS is a sibling checkout, MENTORI_HARNESS or UPSTREAM (_find_harness); UPSTREAM is tried above, so a path
    # under none of the others cannot be under HARNESS, and HARNESS is not looked for (no `git -C`).
    env = os.environ.get("MENTORI_HARNESS")
    could = [ROOT.parent / name for name in SIBLINGS] + ([Path(env).expanduser().resolve()] if env else [])
    if any(q.is_relative_to(c) for c in could):
        try:
            return f"<harness>/{q.relative_to(_harness()).as_posix()}"
        except ValueError:
            pass
    return str(q)


def shown(p) -> str:
    """A path as a SHIPPED artifact records it: deposit/<path> under the upstream data root, the
    repository-relative posix path under this repo, else the path unchanged.

    The deposit root is tried first because the vendored copy, data/upstream, sits inside this
    repo and must still read as deposit/. Only what is written changes; code that reads a file
    keeps the real path.
    """
    q = Path(p).expanduser()
    q = q.resolve() if q.is_absolute() else (ROOT / q).resolve()
    for base, prefix in ((UPSTREAM, "deposit/"), (ROOT, "")):
        try:
            return prefix + q.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return str(p)


def summary() -> list[tuple[str, str, bool]]:
    """(what, where, is it there) for every root, for doctor_env and for provenance headers."""
    return [
        ("repo", str(ROOT), True),
        ("upstream", str(UPSTREAM), have_upstream()),
        ("harness git", str(_harness()), (_harness() / ".git").exists()),
        ("corpus", str(CORPUS), CORPUS.is_dir()),
        ("chrome", str(chrome() or "not found"), chrome() is not None),
        ("platform", f"{platform.system()} {platform.machine()}, python {sys.version.split()[0]}", True),
    ]


if __name__ == "__main__":
    print("machine registry\n")
    for what, where, ok in summary():
        print(f"  {'ok ' if ok else 'MISSING'}  {what:<12} {where}")
