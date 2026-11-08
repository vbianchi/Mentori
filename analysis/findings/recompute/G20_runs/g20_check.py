"""G20 (D260): G19's ablation repeated on qwen3-coder:30b. The checks are G19's (findings/recompute/G19_runs/
g19_check.py), imported and run with G20's names, so nothing of G19's folder changes (G19's launcher R1 holds its
scripts to its PIN). README.md beside this file.

What differs from G19 (set on the imported module before any command runs):
  MODEL qwen3-coder:30b (GEN_MODEL ollama::qwen3-coder:30b, run tag +qwen3-coder-30b), so every call is checked against
  lock.ollama(qwen3-coder:30b, generator, draw 1) and LOCK [models]'s digest 06c1097e;
  A_EXPERIMENT b4_rlm_ref_qwen3coder (run_rlm_ref.OLLAMA_EXPERIMENTS), so A's run is b4_rlm_ref_qwen3coder__cap10__d239a46;
  MANIFEST g20_stored_R.json (here), whose decision is D260 and whose sources name qwen3-coder's T2 and T2X runs.
  g19_check.DECISION stays D249 O2: it is the decision the questions file records, so the file checks as G19's.
D261 (Valerio, 6 Nov, "G20-A: O1"): the smoke counts a call the server refused for a prompt over num_ctx (HTTP 400) as
a visible length outcome, as it counts "length" (smoke_verdict below); verify and every other check are G19's.
What is the same: the 46 questions (G19_runs/g19_questions.json, read, never written: `questions --write` is refused),
draw 1, cap 10, index exp_v4_s20_n0, the arms' switches, every refusal and count.

    uv run --project experiments/mentori --frozen python findings/recompute/G20_runs/g20_check.py <g19_check command>
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
G19 = HERE.parent / "G19_runs"
if str(G19) not in sys.path:
    sys.path.insert(0, str(G19))

import g19_check as G  # noqa: E402

DECISION = "D260"
MODEL = "qwen3-coder:30b"
SLUG = "qwen3-coder-30b"
A_EXPERIMENT = "b4_rlm_ref_qwen3coder"
MANIFEST = HERE / "g20_stored_R.json"
SOURCES = {"T2": "T2's qwen3-coder:30b rlm_10 draw 1 on D98's 29 (the T2 qwen3-coder clone's sink; judged in set "
                 "S6WT2LQCODER, collect findings/recompute/S518_inputs/qwen3-coder/collect.jsonl)",
           "T2X": "T2X's qwen3-coder:30b rlm_10 draw 1 on the 17 (D241, D243; the T2X clone's sink; judged by "
                  "judge_t2x.sh, collect T2X_runs/collect/t2xqcoder_collect.jsonl)"}

_manifest = G.manifest
_smoke_verdict = G.smoke_verdict
CONTEXT_REFUSED = ("exceed_context_size", "exceeds the available context size")


def context_refused(c: dict) -> bool:
    """D261 (Valerio, 6 Nov, "G20-A: O1"): a call the server refused because its prompt is longer than the context
    (HTTP 400 over num_ctx; LOCK truncate false, so nothing is cut) is a visible length outcome, as status "length" is.
    Only a call that was sent (options_sent recorded) and that the server answered with that refusal."""
    e = str(c.get("error") or "")
    return (c.get("status") == "error" and c.get("options_sent") is not None and e.startswith("HTTP 400")
            and any(m in e for m in CONTEXT_REFUSED))


def smoke_verdict(arm: str, root: Path, server: str, want_lock: str = G.LOCK_WANT) -> tuple:
    """g19_check.smoke_verdict with D261's one change: a context_refused call is not a smoke failure. Every other
    problem it names is G19's. G19's own smoke rule is unchanged."""
    ok, problems, facts = _smoke_verdict(arm, root, server, want_lock)
    sink = Path(root) / G.run_id(arm, smoke=True)
    refused = {c.get("seq") for c in G.read_jsonl(sink / "calls.jsonl") if context_refused(c)}
    kept = []
    for p in problems:
        if p.startswith("call seq "):
            seq_s, _, rest = p[len("call seq "):].partition(": ")
            parts = [x for x in rest.split("; ") if not (x.startswith("status 'error'") and seq_s.isdigit()
                                                          and int(seq_s) in refused)]
            if parts:
                kept.append(f"call seq {seq_s}: " + "; ".join(parts))
            continue
        kept.append(p)
    facts = {**facts, "context_refused_calls": len(refused), "rule": "D261: a context refusal counts as length"}
    return not kept, kept, facts


def manifest(*args, **kw) -> dict:
    m = _manifest(*args, **kw)
    m["sources"] = dict(SOURCES)
    m["decision"] = DECISION
    return m


def install() -> None:
    """G20's names on the imported g19_check (module docstring); idempotent."""
    G.MODEL = MODEL
    G.GEN_MODEL = f"ollama::{MODEL}"
    G.TAG = f"+{SLUG}"
    G.A_EXPERIMENT = A_EXPERIMENT
    G.MANIFEST = MANIFEST
    G.ESTIMATE = HERE / "g20_estimate.json"
    G.ARM_LABEL = {**G.ARM_LABEL, "R": "Mentori RLM-10 (stored, qwen3-coder:30b)"}
    G.manifest = manifest
    G.smoke_verdict = smoke_verdict


install()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["questions"] and "--write" in argv:
        print("REFUSED: G20 reads G19's questions file; it never writes it")
        return 1
    if argv[:1] == ["estimate"]:
        print("REFUSED: G20 has no estimate of its own (G19's reads gemma3's records)")
        return 1
    return G.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
