"""Prompt files: export the paper's prompts, read a prompts folder back, tell which ones were edited.

A prompt file is a header of lines that start with HEADER_MARK, ending with the SEPARATOR line, then the prompt itself.
Everything after the separator line is sent to the model exactly (its bytes); the header is never sent. A file without
the header is read whole as the prompt.
"""

from __future__ import annotations

import hashlib
import importlib
import re
import string
from pathlib import Path

from mentori_cli import paths, registry

HEADER_MARK = "##mentori-cli## "
SEPARATOR = HEADER_MARK + "---- the prompt starts on the next line; everything below is sent to the model ----\n"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def paper_prompts() -> dict[str, str]:
    """Every registry prompt as the paper's code holds it (imports the paper's modules; paths.setup_sys_path first).
    F1 is the text of _f1_prompt with its two inputs written as placeholders."""
    out = {}
    for p in registry.PROMPTS:
        owner = importlib.import_module(p.module)
        value = getattr(owner, "_mentori_cli_paper_" + p.attr, None) or getattr(owner, p.attr)   # inject.PAPER_PREFIX
        if p.kind == "f1":
            t = value(registry.F1_TOOL_MARK, registry.F1_CONTENT_MARK)
            if t.count(registry.F1_TOOL_MARK) != 1 or t.count(registry.F1_CONTENT_MARK) != 1:
                raise RuntimeError("the F1 prompt does not hold each of its two inputs once; its template is unknown")
            if "{tool_name}" in t or "{raw_observation}" in t:
                raise RuntimeError("the F1 prompt already holds a placeholder text; its template would be ambiguous")
            value = t.replace(registry.F1_TOOL_MARK, "{tool_name}").replace(registry.F1_CONTENT_MARK,
                                                                              "{raw_observation}")
        if not isinstance(value, str):
            raise RuntimeError(f"{p.module}.{p.attr} is not a string")
        out[p.name] = value
    return out


def source_of(p: registry.Prompt) -> str:
    """experiments/mentori/<module path>.py:<line> of the constant's assignment (or the function's def)."""
    rel = Path(*p.module.split(".")).with_suffix(".py")
    f = paths.mentori() / rel
    pat = re.compile(rf"^def {re.escape(p.attr)}\(" if p.kind == "f1" else rf"^{re.escape(p.attr)}\s*=")
    line = next((i for i, s in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if pat.match(s)), None)
    return f"experiments/mentori/{rel.as_posix()}:{line} {p.attr}"


def _fill_line(p: registry.Prompt, text: str) -> str:
    if p.fill == "format":
        names = sorted({f for _, f, _, _ in string.Formatter().parse(text) if f})
        return ("filled with Python's str.format: placeholders " + (" ".join("{" + n + "}" for n in names) or "none")
                + "; a literal brace is written twice, {{ or }}")
    if p.fill == "replace":
        return ("filled by replacing the placeholders " + " ".join(p.placeholders)
                + "; every other brace is sent as written")
    return "sent as written (no placeholder)"


def header(p: registry.Prompt, text: str) -> str:
    lines = [
        f"component: {p.name}, {p.component}",
        f"source: {source_of(p)}",
        _fill_line(p, text),
        f"paper sha256: {sha256(text)}",
        "edit the text below to change what is sent; delete this file to use the paper's prompt",
    ]
    return "".join(HEADER_MARK + s + "\n" for s in lines) + SEPARATOR


def export(folder: Path, defaults: dict[str, str], overwrite: bool = False) -> list[Path]:
    """One file per registry prompt, prompts/<name>.txt: the header, then the paper's prompt, byte for byte."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for p in registry.PROMPTS:
        f = folder / f"{p.name}.txt"
        if f.exists() and not overwrite:
            raise SystemExit(f"mentori-cli: {f} exists; nothing written (move it aside, or pass --force)")
        f.write_bytes((header(p, defaults[p.name]) + defaults[p.name]).encode("utf-8"))
        written.append(f)
    return written


def body(raw: str) -> str:
    """The prompt of a file's text: what follows the SEPARATOR line of a header, else the whole text."""
    if not raw.startswith(HEADER_MARK):
        return raw
    pos = 0
    for line in raw.splitlines(keepends=True):
        pos += len(line)
        if line == SEPARATOR:
            return raw[pos:]
        if not line.startswith(HEADER_MARK):
            break
    raise SystemExit("mentori-cli: a prompt file starts with a header but has no separator line "
                     f"({SEPARATOR.strip()!r}); nothing run")


def placeholders(p: registry.Prompt, text: str) -> set[str]:
    """The placeholders a prompt text holds, as the paper's code fills it: for fill "format", every {name} that
    str.format would fill (a text str.format cannot read is refused); for fill "replace", each of the registry's
    placeholder texts the prompt holds; for fill "plain", none."""
    if p.fill == "format":
        try:
            return {"{" + f + "}" for _, f, _, _ in string.Formatter().parse(text) if f is not None}
        except ValueError as e:
            raise SystemExit(f"mentori-cli: prompt {p.name}: str.format cannot read it ({e}); a literal brace is "
                             "written twice, {{ or }}; nothing run") from None
    if p.fill == "replace":
        return {ph for ph in p.placeholders if ph in text}
    return set()


def check_placeholders(p: registry.Prompt, text: str, paper: str, where: str) -> None:
    """An edited prompt keeps every placeholder of the paper's prompt and adds none, so the question, the passages
    and the other inputs still reach the model. Refused otherwise, before anything runs."""
    want, got = placeholders(p, paper), placeholders(p, text)
    if want == got:
        return
    parts = []
    if want - got:
        parts.append("missing " + " ".join(sorted(want - got)))
    if got - want:
        parts.append("not in the paper's prompt " + " ".join(sorted(got - want)))
    raise SystemExit(f"mentori-cli: {where}: the placeholders differ from the paper's prompt ({'; '.join(parts)}). "
                     f"The paper's code fills exactly {' '.join(sorted(want)) or 'none'}; a prompt without them would "
                     "run without its inputs (the question, the passages). Put them back, or delete the file to use "
                     "the paper's prompt; nothing run")


def load(folder: Path | None, defaults: dict[str, str]) -> dict:
    """The prompts a run uses: {"used": {name: text}, "sha256": {name: hex}, "edited": [names], "dir": str|None}.
    A name with no file in the folder is the paper's prompt. A .txt file whose name is not a registry prompt is
    refused, so a misnamed file is never silently ignored, and so is an edited prompt whose placeholders are not the
    paper's prompt's (check_placeholders)."""
    used = dict(defaults)
    if folder is not None:
        folder = Path(folder)
        if not folder.is_dir():
            raise SystemExit(f"mentori-cli: prompts folder {folder} does not exist; nothing run")
        unknown = sorted(f.name for f in folder.glob("*.txt") if f.stem not in registry.BY_NAME)
        if unknown:
            raise SystemExit(f"mentori-cli: {folder} holds {unknown}, which are not prompt names "
                             f"({', '.join(registry.BY_NAME)}); nothing run")
        for p in registry.PROMPTS:
            f = folder / f"{p.name}.txt"
            if f.exists():
                used[p.name] = body(f.read_bytes().decode("utf-8"))
                if used[p.name] != defaults[p.name]:
                    check_placeholders(p, used[p.name], defaults[p.name], str(f))
    edited = [p.name for p in registry.PROMPTS if used[p.name] != defaults[p.name]]
    return {"dir": None if folder is None else str(Path(folder).resolve()), "used": used,
            "sha256": {k: sha256(v) for k, v in used.items()}, "edited": edited}
