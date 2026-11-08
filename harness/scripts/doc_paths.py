"""Where the live documents are: the letter and the six manuscript documents.

Valerio, 4 November 2026: "Ideally the folder resubmission/ had everything we want to send back to journal"
(resubmission/README.md). The letter and the manuscript are edited in resubmission/, as tracked changes. The submitted
text every mark is diffed against stays in manuscript/submission/baseline/, and the figures, source, supplementary
plates and Source Data stay in manuscript/submission/ (ASSETS_DIR).

Each location is given as a Path and as a repo-relative string (the *_REL names), the form `git show HEAD:<rel>` takes.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LETTER_REL = "resubmission/02_response_to_reviewers/Point_by_point_response_all_reviewers.docx"
MANUSCRIPT_DIR_REL = "resubmission/04_manuscript"
SUPPLEMENTARY_DIR_REL = "resubmission/06_supplementary"
# D305 (Valerio, 8 Nov: "deleting the October Supplementary files and renaming the Word copy to
# Supplementary_Information.docx"): the live SI is S602's build, renamed from Supplementary_Information_20261107.docx;
# the October 06_Supplementary_Information.docx is deleted. Scripts still name it "06_Supplementary_Information.docx"
# (DOCS6, doc()), which resolves here.
SUPPLEMENTARY_DOCX_REL = f"{SUPPLEMENTARY_DIR_REL}/Supplementary_Information.docx"
BASELINE_DIR_REL = "manuscript/submission/baseline"
ASSETS_DIR_REL = "manuscript/submission"

LETTER = ROOT / LETTER_REL
MANUSCRIPT_DIR = ROOT / MANUSCRIPT_DIR_REL
SUPPLEMENTARY_DIR = ROOT / SUPPLEMENTARY_DIR_REL
SUPPLEMENTARY_DOCX = ROOT / SUPPLEMENTARY_DOCX_REL
BASELINE_DIR = ROOT / BASELINE_DIR_REL
ASSETS_DIR = ROOT / ASSETS_DIR_REL

# The six manuscript documents, in order; 01_ to 05_ live in MANUSCRIPT_DIR, 06_ in SUPPLEMENTARY_DIR (as SUPPLEMENTARY_DOCX).
DOCS5 = ("01_Title_Abstract.docx", "02_Main_Text.docx", "03_Methods.docx", "04_Figures_Tables.docx",
         "05_References.docx")
DOCS6 = DOCS5 + ("06_Supplementary_Information.docx",)


def doc_rel(name: str) -> str:
    """The repo-relative live path of a manuscript document, by file name ("03_Methods.docx")."""
    if name == "06_Supplementary_Information.docx":   # the SI's name in DOCS6; its file is SUPPLEMENTARY_DOCX_REL (D305)
        return SUPPLEMENTARY_DOCX_REL
    if name[:3] in ("01_", "02_", "03_", "04_", "05_"):
        return f"{MANUSCRIPT_DIR_REL}/{name}"
    raise ValueError(f"not a manuscript document: {name!r}")


def doc(name: str) -> Path:
    """The live path of a manuscript document, by file name."""
    return ROOT / doc_rel(name)


# Where each live document was before 4 November, for reading it at a commit made before the move: a gate that
# compares with HEAD reads the old path until the move is committed, and a script pinned to an older commit always does.
# Before commit d158ca68 the new paths held S347's packed copies (6 October), never the live documents, so at such a
# commit the old path is the document and the new path is not.
MOVED_FROM = {LETTER_REL: "response/Point_by_point_response_all_reviewers.docx",
              **{doc_rel(n): f"manuscript/submission/{n}" for n in DOCS6}}


def git_show(rev: str, rel: str, root: Path = ROOT):
    """`git show <rev>:<rel>` for a live document's repo-relative path: its path before the move when rev holds that
    one (every commit before the move is committed), else rel. Returns the CompletedProcess (stdout bytes)."""
    import subprocess
    if rel in MOVED_FROM:
        r = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{MOVED_FROM[rel]}"], capture_output=True)
        if r.returncode == 0:
            return r
    return subprocess.run(["git", "-C", str(root), "show", f"{rev}:{rel}"], capture_output=True)


def live_docs() -> list[Path]:
    """The six live manuscript documents that exist on disk, in order."""
    return [p for p in (doc(n) for n in DOCS6) if p.exists()]
