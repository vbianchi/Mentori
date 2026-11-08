#!/usr/bin/env python3
"""bootstrap_upstream.py - put the upstream data inside this repo, and record what it is.

Valerio, 1 September 2026: "everything in one repo instead". Until now this repo read the raw
evaluation JSON out of a sibling checkout at a path that was true on one laptop. That laptop is
at the repair centre, and eighty-nine scripts stopped resolving. A verification layer whose
inputs live at an address only its author can reach is not a verification layer.

So this script populates data/upstream/publication/ with the files the analysis actually reads,
and writes data/upstream/MANIFEST.sha256 recording the sha256 of every byte it put there.

WHY THE BYTES ARE GITIGNORED AND THE MANIFEST IS COMMITTED.

README.md draws the trust boundary this repo is built on: the raw per-evaluation JSON is TRUSTED
and treated as the data; the original analysis scripts and the manuscript prose are DISTRUSTED and
re-derived. Trusting bytes only means something if you can say WHICH bytes. Two different things
are needed for that, and they are not the same thing:

  reachable   the analysis has to be able to open the file on this machine.  -> vendor it
  identified  the record has to say which file that was.                     -> commit its digest

Committing the bytes as well would answer neither question better and would make this repo a
second copy of a deposit that already has a DOI. notes/planning/REPRO_PACKAGE_SPEC.md settles who
owns that copy: two halves and one bridge, where the data half is "Zenodo, versioned, cited by
DOI" and the code half is the public repo. The upstream repo's own .gitignore says the same thing
in one line -- "The archive is the record; this directory is a working copy of it" -- and this
directory is a working copy of the same working copy. A working copy that forks into git history
is how the citable record and the thing people actually run drift apart, which is the failure mode
the whole revision is about.

This script is therefore not a third half. It is the SPEC's bridge, `download_results.sh`, pointed
at this repo instead of the paper repo, and it mints no new authority: the deposit's own checksum
comes from the file table S02_zenodo_verify.py already recorded in
findings/recompute/zenodo_manifest.json, rather than being copied into a constant here.

And it makes the SPEC's acceptance test runnable, the one Valerio set on 4 August: unpack into a
fresh folder as if a stranger had just downloaded it, and run it top to bottom there. A stranger
runs this, then runs it with --verify, and the answer to "are your bytes our bytes" is a checksum
rather than a promise. That is also what keeps the record honest in the other direction: a
manifest row that stops matching is a real difference, not a porting defect.

WHAT IS VENDORED, measured rather than assumed. Every publication/ path this repo names, from the
38 scripts that name one, resolved against the sibling checkout:

    publication/results                527 files   236.8 MB   raw evaluation JSON, exp* analysis*
    publication/results/deep_analyses   19 files     2.8 MB   the 19 deep analyses
    publication/figures                  3 files    11.8 MB   fig1_general_scheme.*, globbed by S04b
    publication/figures_regen           10 files     1.5 MB   the 5 carried figures S203 pins, + PDFs
    publication/scripts                 46 files     1.0 MB   read to confirm metric definitions
    publication/data                     2 files     0.3 MB   ground_truth, verification_report
                                       ---------------------
                                       607 files   254.3 MB

The 4.65 GB left behind is results/exp05_archive_contaminated/, results/end_to_end/ and
results/contextual_smoke/: working directories no script names and the deposit never carried.

THREE SOURCES, because no single one has all of it.

  1. a sibling checkout that already holds the data. Nothing to download.
  2. the Zenodo deposit, DOI 10.5281/zenodo.19476756, for a machine that has no sibling. Same
     archive, same URL and same rootedness ("results/") as publication/data/download_results.sh.
  3. a clone of the public repo, for what the deposit does not carry. This is the easy one to get
     wrong: publication/figures_regen exists ONLY in the public repo, and its five TIFFs are the
     ones whose sha256 prefixes S203_supp_carried_figures.py pins. The same-named TIFFs in
     publication/figures are DIFFERENT bytes and would fail that gate.

THE CORPUS IS OPTIONAL AND OFF BY DEFAULT. The 200 source PDFs are 528 MB and are copyrighted;
the manuscript says they are not redistributed, and the SPEC says download_papers.py rebuilds them
from source DOIs. Three scripts read 20 of them (S18_probe_preflight, S18_probe_context,
S18a_build_evidence) and they are the only reason to pass --corpus, on a machine that already has
a lawful copy.

Usage
    uv run python scripts/bootstrap_upstream.py                  # vendor from whatever is here
    uv run python scripts/bootstrap_upstream.py --dry-run        # say what it would do
    uv run python scripts/bootstrap_upstream.py --verify         # re-hash the tree, exit non-zero
    uv run python scripts/bootstrap_upstream.py --source zenodo  # ignore siblings, fetch the DOI
    uv run python scripts/bootstrap_upstream.py --corpus         # add the 200 PDFs
    uv run python scripts/bootstrap_upstream.py --force          # re-fetch and re-copy everything

Gates:
  G1  --verify has a manifest to verify against
  G2  every file the manifest names is present, with the digest it records
  G3  the vendored tree carries nothing the manifest does not name
  G4  a fetched deposit archive matches the checksum the deposit itself publishes
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys, tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, ROOT, SIBLINGS, UPSTREAM_MARK, VENDOR, rel, scratch   # noqa: E402

MANIFEST_NAME = "MANIFEST.sha256"
DOI = "10.5281/zenodo.19476756"
RECORD_ID = "19476756"
ARCHIVE = "mentori_results.tar.gz"
ARCHIVE_URL = f"https://zenodo.org/records/{RECORD_ID}/files/{ARCHIVE}?download=1"
# The deposit's own checksums, already fetched from the Zenodo API and committed by S02. Read
# rather than restated: a second hand-copied constant is a second thing that can go stale.
DEPOSIT_MANIFEST = RECOMPUTE / "zenodo_manifest.json"
PUBLIC_GIT = "https://github.com/vbianchi/Mentori.git"
# What proves a clone is the public repo and not an empty scaffold: figures_regen is the part
# only it has, so the mark is the file this whole third source exists to fetch.
PUBLIC_MARK = "publication/figures_regen/ed_fig1_retrieval_optimisation.tiff"
SCRATCH_NAME = "bootstrap_upstream"
NO_SOURCE = "*** no source on this machine ***"
# What a dry run says instead of reaching for it. --dry-run must not pull 47 MB off Zenodo to
# tell you what it would do.
FALLBACK = {"deposit": f"would fetch the deposit at {DOI}",
            "checkout": f"would clone {PUBLIC_GIT}"}

# (subpath under publication/, filename patterns, which fallback can supply it when no local
# checkout does). "deposit" is what the Zenodo archive carries; "checkout" is what only git has.
# Patterns are non-recursive on purpose: results/ is the top level only, and deep_analyses is its
# own row, so the six unreferenced subdirectories under results/ are never swept in.
PARTS = (
    ("results", ("*.json", "*.md", "*.txt", "*.csv", "*.png", "*.log"), "deposit"),
    ("results/deep_analyses", ("*.json",), "deposit"),
    ("figures", ("fig1_general_scheme.*",), "checkout"),
    ("figures_regen", ("ed_fig1_*", "ed_fig2_*", "ed_fig3_*", "ed_fig4_*", "ed_fig6_*"), "checkout"),
    ("scripts", ("*.py",), "checkout"),
    ("data", ("ground_truth.json", "verification_report.json"), "checkout"),
)
CORPUS_PART = ("data/corpus", ("core/*.pdf", "noise/*.pdf", "corpus_metadata.json"), "checkout")


def shown(p: Path) -> str:
    """A path as printed: relative to this repo when it is in it, symbolic when it is not."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return rel(p)


def digest(p: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def human(nbytes: float) -> str:
    return f"{nbytes / 1e6:.1f} MB"


def read_manifest(path: Path) -> dict:
    """name -> sha256, in the shape data/replication_inputs/MANIFEST.sha256 already uses."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            got, name = line.split(maxsplit=1)
            out[name] = got
    return out


def write_manifest(path: Path, rows: dict) -> None:
    path.write_text("".join(f"{rows[n]}  {n}\n" for n in sorted(rows)), encoding="utf-8")


def collect(pub: Path, subpath: str, patterns: tuple) -> list:
    """The files one source offers for one part, as (source path, name under the vendor root).

    Dotfiles are skipped. The deposit was tarred on a mac and carries an AppleDouble `._<name>`
    beside every member plus a .DS_Store; they match `*.json` and they are not data.
    """
    base = pub / subpath
    if not base.is_dir():
        return []
    found = set()
    for pat in patterns:
        for p in base.glob(pat):
            parts = p.relative_to(base).parts
            if p.is_file() and not any(s.startswith(".") for s in parts):
                found.add(p)
    return [(p, f"publication/{subpath}/{p.relative_to(base).as_posix()}") for p in sorted(found)]


def checkouts() -> list:
    """Every publication/ beside this repo that could supply a part, in preference order."""
    return [ROOT.parent / name / "publication" for name in SIBLINGS
            if (ROOT.parent / name / "publication").is_dir()]


def carries_data(pub: Path) -> bool:
    """Does this checkout hold the raw evaluation outputs, or only the scaffold?

    machine.py asks the same question the same way, and it has to be asked: the public repo
    ships publication/results/README.md and nothing else, and a lone README matches `*.md`.
    Without this, a machine that has only the public clone would satisfy the whole results part
    with one file, and the deposit it actually needs would never be fetched.
    """
    return (pub.parent / UPSTREAM_MARK).exists()


def is_public(pub: Path) -> bool:
    """Is this checkout the published repo, rather than someone's working copy of it?

    It matters for the git-tracked parts, and it cost a reproduction to learn. A working copy
    accumulates files the repo never tracked: the sibling here carries 46 files under
    publication/scripts where the public repo tracks 32, the extra 14 being reviewer analyses
    that were run ad hoc and never committed. S05_evalmode_table counts the scripts that mention
    strategy_replication and the committed artifact records none, because the machine that wrote
    it read the published tree; vendoring the working copy instead makes that count 2 and the
    artifact stops reproducing. So for anything git tracks, the published tree is the record and
    is preferred, and a working copy is only the fallback.
    """
    return (pub.parent / PUBLIC_MARK).exists()


def deposit_checksum() -> str:
    """The archive's md5, as the deposit itself publishes it, via S02's recorded file table."""
    if not DEPOSIT_MANIFEST.exists():
        return ""
    files = json.loads(DEPOSIT_MANIFEST.read_text(encoding="utf-8")).get("files", [])
    for f in files:
        if f.get("key") == ARCHIVE and str(f.get("checksum", "")).startswith("md5:"):
            return f["checksum"].split(":", 1)[1]
    return ""


def fetch_deposit(force: bool) -> Path:
    """Unpack the Zenodo archive into scratch and return the publication/ it stands in for.

    The tarball is rooted at "results/", exactly as publication/data/download_results.sh
    documents, so unpacking it into a directory makes that directory a publication/.
    """
    import httpx                             # imported here: most runs copy locally, no network

    work = scratch(SCRATCH_NAME)
    pub = work / "publication"
    archive = work / ARCHIVE
    want = deposit_checksum()
    if force and archive.exists():
        archive.unlink()
    if archive.exists() and want and digest(archive, "md5") != want:
        archive.unlink()
    if not archive.exists():
        print(f"  fetching {ARCHIVE} from {DOI}")
        with httpx.Client(follow_redirects=True, timeout=120) as client:
            with client.stream("GET", ARCHIVE_URL) as r:
                r.raise_for_status()
                with archive.open("wb") as fh:
                    for chunk in r.iter_bytes(chunk_size=1 << 20):
                        fh.write(chunk)
    got = digest(archive, "md5")
    if want and got != want:
        raise SystemExit(f"G4: {ARCHIVE} is md5 {got[:12]}, the deposit records {want[:12]}. "
                         f"Do not vendor an archive that is not the deposited one.")
    if not want:
        print(f"  no deposit checksum in {shown(DEPOSIT_MANIFEST)}; archive md5 is {got[:12]}")
    if force and pub.exists():
        shutil.rmtree(pub)
    pub.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(pub, filter="data")
    return pub


def clone_public(force: bool) -> Path:
    """A shallow clone of the public repo, for the parts the deposit does not carry."""
    work = scratch(SCRATCH_NAME)
    repo = work / "Mentori"
    if force and repo.exists():
        shutil.rmtree(repo)
    if not (repo / PUBLIC_MARK).exists():
        if repo.exists():
            shutil.rmtree(repo)
        print(f"  cloning {PUBLIC_GIT}")
        r = subprocess.run(["git", "clone", "--depth", "1", PUBLIC_GIT, str(repo)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"git clone {PUBLIC_GIT} failed:\n{r.stderr.strip()}")
    return repo / "publication"


def plan(parts: tuple, source: str, force: bool, fetch: bool) -> list:
    """(part, where it came from as printed, files), reaching for a remote source only if needed."""
    local = checkouts()
    fetched = {}
    out = []
    for subpath, patterns, where in parts:
        label, files = "", []
        forced = (source == "zenodo" and where == "deposit") or \
                 (source == "git" and where == "checkout")
        # A deposit part needs a checkout that actually holds the raw outputs; a checkout part
        # needs the PUBLISHED tree, so the public clone is tried before any working copy.
        pool = ([c for c in local if carries_data(c)] if where == "deposit"
                else sorted(local, key=lambda c: not is_public(c)))
        if not forced:
            for cand in pool:
                files = collect(cand, subpath, patterns)
                if files:
                    label = shown(cand / subpath)
                    break
        if not files and source != "sibling":
            if not fetch:
                label = FALLBACK[where]
            else:
                if where not in fetched:
                    fetched[where] = (fetch_deposit(force) if where == "deposit"
                                      else clone_public(force))
                files = collect(fetched[where], subpath, patterns)
                label = shown(fetched[where] / subpath)
        out.append((subpath, label or NO_SOURCE, files))
    return out


def vendor(files: list, dest: Path, force: bool, digests: dict) -> tuple:
    """Copy what is not already there with the right bytes. Twice in a row copies nothing."""
    copied = current = 0
    for src, name in files:
        want = digest(src)
        digests[name] = want
        out = dest / name
        if not force and out.exists() and digest(out) == want:
            current += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        copied += 1
    return copied, current


def tree(dest: Path) -> list:
    """Every vendored file, manifest excluded: the manifest describes the tree, not itself."""
    return sorted(p for p in dest.rglob("*")
                  if p.is_file() and p.name != MANIFEST_NAME
                  and not any(s.startswith(".") for s in p.relative_to(dest).parts))


def verify(dest: Path) -> int:
    recorded = read_manifest(dest / MANIFEST_NAME)
    if not recorded:                                                             # G1
        raise SystemExit(f"G1: no manifest at {shown(dest / MANIFEST_NAME)}. Nothing has been "
                         f"vendored here yet, so there is nothing to verify.\n"
                         f"    uv run python scripts/bootstrap_upstream.py")
    print(f"verify {shown(dest)}  against {len(recorded)} recorded file(s)\n")
    missing, wrong, nbytes = [], [], 0
    for name in sorted(recorded):
        p = dest / name
        if not p.exists():                                                       # G2
            missing.append(name)
            continue
        nbytes += p.stat().st_size
        got = digest(p)
        if got != recorded[name]:
            wrong.append((name, got, recorded[name]))
    have = {p.relative_to(dest).as_posix() for p in tree(dest)}
    extra = sorted(have - set(recorded))                                         # G3

    if missing or wrong or extra:
        print("FAILED")
        for name in missing[:20]:
            print(f"  missing        {name}")
        if len(missing) > 20:
            print(f"  missing        ... and {len(missing) - 20} more")
        for name, got, want in wrong[:20]:
            print(f"  digest         {name} is {got[:12]}, recorded {want[:12]}")
        if len(wrong) > 20:
            print(f"  digest         ... and {len(wrong) - 20} more")
        for name in extra[:20]:
            print(f"  not recorded   {name}")
        if len(extra) > 20:
            print(f"  not recorded   ... and {len(extra) - 20} more")
        print(f"\n{len(recorded) - len(missing) - len(wrong)} of {len(recorded)} verified. "
              f"Re-vendor with --force, or say why these bytes differ before using them.")
        return 1
    print(f"PASSED  {len(recorded)} files, {human(nbytes)}, every digest matches "
          f"{shown(dest / MANIFEST_NAME)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=("auto", "sibling", "zenodo", "git"), default="auto",
                    help="auto prefers a sibling checkout, then the Zenodo deposit for results/ "
                         "and a clone of the public repo for the rest; sibling refuses to touch "
                         "the network; zenodo forces the deposit for results/; git forces the "
                         "clone for figures_regen, figures, scripts and data")
    ap.add_argument("--corpus", action="store_true",
                    help="also copy the 200 source PDFs (528 MB, copyrighted, not redistributed; "
                         "off by default, and only three scripts read them)")
    ap.add_argument("--verify", action="store_true",
                    help="re-hash the vendored tree against the manifest and copy nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be vendored, from where, and write nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-fetch and re-copy everything, matching digests included")
    ap.add_argument("--dest", default=None,
                    help=f"where to vendor (default {shown(VENDOR)}); a temporary directory here "
                         f"exercises the copy without touching the working tree")
    a = ap.parse_args()

    dest = Path(a.dest).expanduser().resolve() if a.dest else VENDOR
    if a.verify:
        return verify(dest)

    parts = (PARTS + (CORPUS_PART,)) if a.corpus else PARTS
    print(f"bootstrap_upstream  ->  {shown(dest)}\n")
    rows = plan(parts, a.source, a.force, not a.dry_run)

    print(f"  {'part':<22} {'files':>6} {'size':>10}  source")
    print("  " + "-" * 86)
    total = nbytes = 0
    for subpath, label, files in rows:
        size = sum(p.stat().st_size for p, _ in files)
        total += len(files)
        nbytes += size
        print(f"  {subpath:<22} {len(files):>6} {human(size):>10}  {label}")
    print("  " + "-" * 86)
    print(f"  {'total':<22} {total:>6} {human(nbytes):>10}")

    empty = [subpath for subpath, label, _files in rows if label == NO_SOURCE]
    if empty:
        print("\nFAILED")
        for subpath in empty:
            print(f"  publication/{subpath} is on no source this run could reach")
        print(f"\nA sibling checkout, the deposit at {DOI}, or {PUBLIC_GIT} carries all of it "
              f"between them.\nDrop --source to let all three be tried.")
        return 1

    if a.dry_run:
        print(f"\ndry run: nothing copied, {shown(dest / MANIFEST_NAME)} not written")
        return 0

    print()
    digests, copied, current = {}, 0, 0
    for subpath, _label, files in rows:
        c, k = vendor(files, dest, a.force, digests)
        copied += c
        current += k
        print(f"  {subpath:<22} {c:>6} copied {k:>6} already current")

    # The manifest describes the tree as it stands, not just this run's plan, so a file the tree
    # carries and the record does not name cannot exist. That is what makes --verify exact.
    for p in tree(dest):
        name = p.relative_to(dest).as_posix()
        if name not in digests:
            digests[name] = digest(p)
    write_manifest(dest / MANIFEST_NAME, digests)
    size = sum((dest / n).stat().st_size for n in digests)

    print(f"\nPASSED  {len(digests)} files, {human(size)} under {shown(dest)} "
          f"({copied} copied, {current} already current)")
    print(f"        recorded in {shown(dest / MANIFEST_NAME)}; the bytes are gitignored, "
          f"the record is not")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
