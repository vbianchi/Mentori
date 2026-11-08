#!/usr/bin/env python3
"""S596 - windowed BERTScore on Figure 5's 516 draw-1 answerable answers, set against the judge as Figure 5 e reads
every evaluator (rulings page 6 Nov, RUN-BERTSCORE: O1).

WHY. Reviewer 1 and the editor (Reviewers_Nature_AIC/editor_review.txt:8) name BERTScore. L1 (S470's overlap stage)
computed it with S07.bertscore (bert_score.score, roberta-large, lang en, batch 32, no idf, no rescaling), but
bert_score cuts both texts at 512 word pieces (bert_score/utils.py:196-202), and LOCK.toml [text] scorer_input =
"whole" says an encoder with a fixed limit splits the text and never cuts it. So S470 wrote a null ("over the
encoder's 512-token limit") for every answer whose answer or key is longer, and Figure 5 e and Supplementary Figure 18
leave BERTScore out. This script scores every one of those texts whole, by windows.

WHAT THE CODE DOES.
  Texts       the answers S470.read_answers reads from G1's six runs (the frozen tar k1_inputs_runs, each run's
              answers.jsonl sha256 equal to L1's header), the key's expected_answer (S470.the_key, S373.AS_V1, v2.4,
              the reference L1 used). Each answer's sha256 must equal its L1 overlap row's.
  Tokens      roberta-large's tokenizer as bert_score loads it (bert_score.utils.get_tokenizer), sent_encode's call
              without the cut: tokenizer.encode(text.strip(), add_prefix_space=True). The word pieces between <s> and
              </s> are the text's content; the count must equal L1's detail.tokens.bertscore.
  Windows     content split into windows of at most 510 word pieces (512, roberta-large's model_max_length, less <s>
              and </s>), each starting 255 after the one before; the last window ends at the last word piece. Each
              window is encoded as <s> + its pieces + </s> by bert_score's own model (get_model("roberta-large", 17),
              layer 17, bert_encode, batches of 32 windows padded as bert_score.utils.padding pads). A word piece takes
              its embedding from the window where it lies furthest from an edge (the first such window on a tie), so
              every piece is encoded with at least 127 pieces of context on each side unless it is near the text's
              own start or end. The text's <s> comes from its first window, its </s> from its last. No word piece is
              dropped. A text of 510 pieces or fewer is one window, exactly bert_score's input.
  Matching    bert_score's greedy matching on the whole texts (greedy_cos_idf with idf off): each embedding scaled to
              length 1; precision is the mean over the answer's content pieces of the highest cosine with any piece
              of the key, <s> and </s> included as bert_score includes them; recall the same the other way; F1 =
              2PR/(P+R). An empty answer has no value ("no answer"), as in L1.
  Reader      S497.d200_data's table of answers, the one Figure 5 e and Supplementary Figure 18 read (draw 1,
              answerable, 516 rows), with this F1 added as "bs:windowed_f1", through S540.evaluator_rows: Spearman's
              rho with the judge's correctness and with its faithfulness, the 10,000 question-resample box and 95%
              interval (S540.rho_box), and the within-question rho (S540.within_rho).

GATES (README.md:75-79: reproduce before writing), each refusing with nothing written:
  G1  S540.evaluator_rows on S497's table gives every Fig. 5e row of figure5_numbers.json at HEAD, exactly.
  G2  every answer's sha256 equals its L1 overlap row's; every text's word-piece count equals L1's.
  G3  on every one of the 516 whose answer and key both fit (L1 has a BERTScore F1), this script's F1 equals L1's
      within 1e-4 (S470's tolerance for BERTScore).

COMMANDS. No model call (roberta-large is a local encoder), no network (HF_HUB_OFFLINE, as S470). CPU, as L1 ran.
    uv run --frozen python scripts/S596_windowed_bertscore.py run [--out <folder>] [--threads N]
    uv run --frozen python scripts/S596_windowed_bertscore_test.py
Outputs (default findings/recompute/S596_windowed_bertscore/): rows.jsonl (one row per answer: tokens, windows, P, R,
F1, L1's F1), evaluator_rows.json (the two Fig. 5e-form records, with provenance) and summary.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCRIPT = "scripts/S596_windowed_bertscore.py"
OUT = ROOT / "findings" / "recompute" / "S596_windowed_bertscore"
FIG5_NUMBERS = "findings/figures_provisional/fig5/figure6_numbers.json"   # D283: Figure 6 (5 until 6 Nov)
MODEL = "roberta-large"
LIMIT = 512                      # roberta-large model_max_length, S470.LIMITS["bertscore"]
WINDOW = LIMIT - 2               # content pieces per window: <s> and </s> take two
STRIDE = WINDOW // 2             # 255: half a window
BATCH = 32                       # S07.bertscore's batch_size
TOL = 1e-4                       # S470's BERTScore tolerance
KEY = "bs:windowed_f1"
LABEL = "BERTScore (windowed)"
NO_ANSWER = "no answer"


class Refused(SystemExit):
    pass


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------------------------
# windows: pure functions, tested without the model
# ---------------------------------------------------------------------------------------------------------------
def windows(n: int, size: int = WINDOW, stride: int = STRIDE) -> list:
    """(start, end) of each window over n content pieces; one window when n fits."""
    if size < 1 or not 0 < stride <= size:
        raise ValueError("size and stride")
    if n <= size:
        return [(0, n)]
    starts = list(range(0, n - size + 1, stride))
    if starts[-1] + size < n:
        starts.append(n - size)
    return [(s, s + size) for s in starts]


def assign(n: int, wins: list) -> list:
    """For each content piece, the window where it lies furthest from an edge; the first on a tie."""
    out = []
    for i in range(n):
        best, depth = None, -1
        for w, (s, e) in enumerate(wins):
            if s <= i < e:
                d = min(i - s, e - 1 - i)
                if d > depth:
                    best, depth = w, d
        if best is None:
            raise ValueError(f"piece {i} is in no window")
        out.append(best)
    return out


def assemble(win_embs: list, wins: list, n: int):
    """The text's embeddings, <s> + n content pieces + </s>, from each window's (len + 2, d) embeddings."""
    import torch
    if len(win_embs) != len(wins):
        raise ValueError("one embedding per window")
    owner = assign(n, wins)
    rows = [win_embs[0][0]]
    for i, w in enumerate(owner):
        s, e = wins[w]
        if win_embs[w].shape[0] != e - s + 2:
            raise ValueError(f"window {w}: {win_embs[w].shape[0]} rows, want {e - s + 2}")
        rows.append(win_embs[w][1 + i - s])
    rows.append(win_embs[-1][-1])
    return torch.stack(rows)


def greedy(hyp, ref) -> tuple:
    """bert_score's greedy_cos_idf for one pair with idf off: (P, R, F1). hyp and ref are (len, d) with <s> first and
    </s> last; specials are matched against but carry weight 0."""
    import torch
    h = hyp / torch.norm(hyp, dim=-1, keepdim=True)
    r = ref / torch.norm(ref, dim=-1, keepdim=True)
    sim = h @ r.T
    p = sim.max(dim=1)[0][1:-1].mean()
    rc = sim.max(dim=0)[0][1:-1].mean()
    f = 2 * p * rc / (p + rc)
    return float(p), float(rc), float(f)


# ---------------------------------------------------------------------------------------------------------------
# the encoder
# ---------------------------------------------------------------------------------------------------------------
class Encoder:
    def __init__(self, threads: int | None = None):
        import torch
        if threads:
            torch.set_num_threads(threads)
        S470 = s470()
        self.snapshot = S470.hf_snapshot(MODEL, S470.ROBERTA_SNAPSHOT)
        from bert_score.utils import get_model, get_tokenizer, model2layers
        self.layers = model2layers[MODEL]
        self.tok = get_tokenizer(MODEL, False)
        if self.tok.model_max_length != LIMIT:
            raise Refused(f"{MODEL} model_max_length {self.tok.model_max_length}, not {LIMIT}")
        self.model = get_model(MODEL, self.layers, False)
        self.model.to("cpu")

    def content(self, text: str) -> list:
        """The word pieces between <s> and </s>, uncut; refused unless they are sent_encode's when the text fits."""
        from bert_score.utils import sent_encode
        full = self.tok.encode(text.strip(), add_special_tokens=True, add_prefix_space=True)
        if full[0] != self.tok.cls_token_id or full[-1] != self.tok.sep_token_id:
            raise Refused("the tokenizer did not wrap the text in <s> and </s>")
        if len(full) <= LIMIT and sent_encode(self.tok, text) != full:
            raise Refused("this encoding is not bert_score's sent_encode on a text that fits")
        return full[1:-1]

    def embed(self, texts: list) -> list:
        """Whole-text embeddings for each text, through windows encoded in batches as bert_score encodes."""
        import torch
        from bert_score.utils import bert_encode, padding
        cls, sep, pad = self.tok.cls_token_id, self.tok.sep_token_id, self.tok.pad_token_id
        jobs, plan = [], []
        for t, text in enumerate(texts):
            ids = self.content(text)
            wins = windows(len(ids))
            plan.append((ids, wins))
            for w, (s, e) in enumerate(wins):
                jobs.append((t, w, [cls] + ids[s:e] + [sep]))
        order = sorted(range(len(jobs)), key=lambda j: -len(jobs[j][2]))
        got: dict = {}
        for b in range(0, len(order), BATCH):
            idx = order[b:b + BATCH]
            arr = [jobs[j][2] for j in idx]
            x, lens, mask = padding(arr, pad, dtype=torch.long)
            emb = bert_encode(self.model, x, attention_mask=mask, all_layers=False)
            for k, j in enumerate(idx):
                got[(jobs[j][0], jobs[j][1])] = emb[k, :lens[k]].clone()
        out = []
        for t, (ids, wins) in enumerate(plan):
            out.append({"emb": assemble([got[(t, w)] for w in range(len(wins))], wins, len(ids)),
                        "pieces": len(ids) + 2, "windows": len(wins)})
        return out


# ---------------------------------------------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------------------------------------------
def s470():
    return _load("S470", ROOT / "scripts" / "S470_l1_signals.py")


def s497():
    return _load("S497", ROOT / "scripts" / "S497_fig5_d166.py")


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout


def gate_reader(dat: dict) -> str:
    """G1."""
    S540 = s497().S540
    head = json.loads(git("show", f"HEAD:{FIG5_NUMBERS}"))["sheets"]["Fig. 6e"]
    got = [[r[c] for c in head["columns"]] for r in S540.evaluator_rows(dat["table"], drawn=s497().E_ROWS_DRAWN)]
    src = head["columns"].index("source")
    drawn = [(g, h) for g, h in zip(got, head["rows"]) if h[src] != S540.HELD]   # a row HEAD holds has no number
    if len(got) != len(head["rows"]) or any(g != h for g, h in drawn):
        raise Refused(f"G1: S540.evaluator_rows on S497's table differs from {FIG5_NUMBERS} at HEAD; nothing written")
    return (f"G1: S540.evaluator_rows on S497's table equals all {len(drawn)} drawn Fig. 6e records of {FIG5_NUMBERS} "
            f"at HEAD ({len(got) - len(drawn)} held there, D195, not compared)")


def read_texts(tmp: Path) -> tuple:
    """S470's reader over the frozen runs; each run's answers.jsonl is the frozen copy whose sha256 is L1's header's:
    single pass and multi-hop from k1_inputs_runs.tar, verified pass and the RLMs from fig2_g1r15_inputs.tar (the
    records after D89's re-run, which L1 read; k1_inputs_runs.tar holds those four runs before it)."""
    S470 = s470()
    FR = s497().FR
    copies = [FR.frozen("k1_inputs_runs", "k1_inputs_runs"), FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs")]
    inputs = tmp / "inputs"
    (inputs / "runs").mkdir(parents=True)
    header = json.loads((FR.frozen("fig5_1028", "l1/header.json")).read_text())
    for run, want in header["identity"]["inputs"]["answers_sha256"].items():
        hit = [c / run for c in copies if (c / run / "answers.jsonl").exists()
               and sha256_file(c / run / "answers.jsonl") == want]
        if not hit:
            raise Refused(f"{run}/answers.jsonl: no frozen copy has L1's header's sha256 {want[:12]}")
        (inputs / "runs" / run).mkdir()
        (inputs / "runs" / run / "answers.jsonl").symlink_to(hit[0] / "answers.jsonl")
    key = S470.the_key()
    if key["sha256"] != header["identity"]["key"]["sha256"]:
        raise Refused("the key is not L1's")
    answers, _sel = S470.read_answers(inputs, key)
    return {(a["config"], a["question_id"], a["draw"]): a for a in answers}, key, header


def run(out: Path, threads: int | None) -> dict:
    S497 = s497()
    S540 = S497.S540
    import time
    t0 = time.time()
    rep = []
    with tempfile.TemporaryDirectory(prefix="S596_") as t:
        tmp = Path(t)
        (tmp / "d200").mkdir()
        R, dat, _srcs, _d200 = S497.d200_data(tmp / "d200")
        rep.append(gate_reader(dat))
        overlap = R["l1"]["stages"]["overlap"]
        answers, key, l1_header = read_texts(tmp)
    table = dat["table"]
    cells = [(r["config"], r["question_id"], 1) for r in table]
    if len(cells) != S540.N_ANSWERABLE_ANSWERS:
        raise Refused(f"the table holds {len(cells)} answers, not {S540.N_ANSWERABLE_ANSWERS}")
    ov = {}
    for k in cells:
        row = overlap.get(k)
        if row is None:
            raise Refused(f"G2: no L1 overlap row for {k}")
        a = answers[k]
        if a["answer_sha256"] != row["answer_sha256"]:
            raise Refused(f"G2: {k}: answer sha256 differs from L1's overlap row")
        ov[k] = row
    enc = Encoder(threads)
    qs = sorted({q for _, q, _ in cells})
    refs = dict(zip(qs, enc.embed([key["questions"][q]["expected_answer"] for q in qs])))
    todo = [k for k in cells if answers[k]["answer"].strip()]
    hyps = dict(zip(todo, enc.embed([answers[k]["answer"] for k in todo])))
    rows, bad_tok, g3 = [], [], []
    for k in cells:
        row, tok = ov[k], (ov[k].get("detail") or {}).get("tokens", {}).get("bertscore") or {}
        l1f = (row.get("signals") or {}).get("bertscore_f1")
        ref = refs[k[1]]
        rec = {"config": k[0], "question_id": k[1], "draw": 1, "answer_sha256": row["answer_sha256"],
               "key_pieces": ref["pieces"], "key_windows": ref["windows"], "l1_bertscore_f1": l1f,
               "l1_null_reason": (row.get("null_reasons") or {}).get("bertscore_f1")}
        if tok.get("key") is not None and tok["key"] != ref["pieces"]:
            bad_tok.append((k, "key", tok["key"], ref["pieces"]))
        if k in hyps:
            h = hyps[k]
            p, r, f = greedy(h["emb"], ref["emb"])
            rec.update(answer_pieces=h["pieces"], answer_windows=h["windows"], precision=p, recall=r, f1=f,
                       null_reason=None)
            if tok.get("answer") is not None and tok["answer"] != h["pieces"]:
                bad_tok.append((k, "answer", tok["answer"], h["pieces"]))
            if l1f is not None:
                g3.append((k, abs(f - l1f), h["windows"] == 1 and ref["windows"] == 1))
        else:
            rec.update(answer_pieces=None, answer_windows=0, precision=None, recall=None, f1=None,
                       null_reason=NO_ANSWER)
        rows.append(rec)
    if bad_tok:
        raise Refused(f"G2: {len(bad_tok)} word-piece counts differ from L1's, first {bad_tok[0]}; nothing written")
    rep.append(f"G2: all {len(cells)} answers' sha256 equal L1's overlap rows; every word-piece count equals L1's")
    worst = max(g3, key=lambda x: x[1])
    if worst[1] > TOL or not all(one for *_, one in g3):
        raise Refused(f"G3: windowed F1 differs from L1's by {worst[1]:.2e} at {worst[0]}; nothing written")
    rep.append(f"G3: on the {len(g3)} answers L1 scored (answer and key within {LIMIT}), the windowed F1 equals "
               f"L1's BERTScore F1, largest difference {worst[1]:.1e} (tolerance {TOL})")
    by = {(r["config"], r["question_id"], 1): r["f1"] for r in rows}
    table2 = [{**r, KEY: by[(r["config"], r["question_id"], 1)]} for r in table]
    e_rows = S540.evaluator_rows(table2, rows=((LABEL, "simple", KEY),))
    fits = [{**r, KEY: by[(r["config"], r["question_id"], 1)]} for r in table
            if ov[(r["config"], r["question_id"], 1)]["signals"].get("bertscore_f1") is not None]
    e_fit = S540.evaluator_rows(fits, rows=(("BERTScore, answers that fit 512 only", "simple", KEY),))
    counts = {"answers": len(rows), "scored": sum(r["f1"] is not None for r in rows),
              "no_answer": sum(r["null_reason"] == NO_ANSWER for r in rows),
              "l1_over_limit": sum(r["l1_null_reason"] == f"over the encoder's {LIMIT}-token limit" for r in rows),
              "l1_no_answer": sum(r["l1_null_reason"] == NO_ANSWER for r in rows),
              "l1_scored": sum(r["l1_bertscore_f1"] is not None for r in rows),
              "answers_over_one_window": sum((r["answer_windows"] or 0) > 1 for r in rows),
              "keys_over_one_window": sum(v["windows"] > 1 for v in refs.values()),
              "keys": len(refs), "longest_answer_pieces": max(r["answer_pieces"] or 0 for r in rows),
              "most_windows": max(r["answer_windows"] for r in rows)}
    import bert_score
    import torch
    import transformers
    prov = {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT), "git_head": git("rev-parse", "HEAD").strip(),
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "command": f"uv run --frozen python {SCRIPT} run", "ruling": "rulings page 6 Nov, RUN-BERTSCORE: O1",
            "imports_sha256": {p: sha256_file(ROOT / p) for p in ("scripts/S497_fig5_d166.py",
                                                                  "scripts/S540_fig5_evaluators.py",
                                                                  "scripts/S470_l1_signals.py")},
            "inputs": {"key": {"path": key["path"], "sha256": key["sha256"]},
                       "answers_sha256": l1_header["identity"]["inputs"]["answers_sha256"],
                       "reader": "S497.d200_data table, S540.evaluator_rows",
                       "fig5_numbers_at_head": FIG5_NUMBERS},
            "encoder": {**enc.snapshot, "layer": enc.layers, "idf": False, "rescale_with_baseline": False,
                        "window_pieces": WINDOW, "stride": STRIDE, "limit": LIMIT, "batch": BATCH, "device": "cpu",
                        "threads": torch.get_num_threads()},
            "lock_sha256": sha256_file(ROOT / "experiments" / "LOCK.toml"),
            "versions": {"bert_score": bert_score.__version__, "transformers": transformers.__version__,
                         "torch": torch.__version__, "python": platform.python_version()},
            "gates": rep, "wall_s": round(time.time() - t0, 1)}
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "rows.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    res = {"_provenance": prov, "counts": counts, "fig5e_form": e_rows, "fits_512_only": e_fit}
    (out / "evaluator_rows.json").write_text(json.dumps(res, indent=1) + "\n")
    (out / "summary.md").write_text(summary(res))
    return res


def summary(res: dict) -> str:
    c, p = res["counts"], res["_provenance"]
    f2 = lambda v: "n/a" if v is None else f"{v:.2f}"   # noqa: E731
    lines = [f"# S596, windowed BERTScore against the judge (Figure 5 e form)", "",
             f"Written by `{p['command']}` at {p['at']}, git {p['git_head'][:8]}, script {p['script_sha256'][:12]}. "
             f"{p['ruling']}.", "",
             f"Answers: {c['answers']} draw-1 answerable (Figure 5 e's table); scored {c['scored']}, no answer "
             f"{c['no_answer']}. L1 had scored {c['l1_scored']}: {c['l1_over_limit']} over the {LIMIT}-token limit, "
             f"{c['l1_no_answer']} no answer. Here {c['answers_over_one_window']} answers and {c['keys_over_one_window']} "
             f"of {c['keys']} keys span more than one window; longest answer {c['longest_answer_pieces']:,} word "
             f"pieces, {c['most_windows']} windows.", "",
             "| row | judge signal | rho | 95% interval | resample quartiles | within-question rho | answers | questions |",
             "|---|---|---|---|---|---|---|---|"]
    for r in res["fig5e_form"] + res["fits_512_only"]:
        lines.append(f"| {r['row']} | {r['judge_signal']} | {f2(r['rho'])} | {f2(r['interval_lo'])} to "
                     f"{f2(r['interval_hi'])} | {f2(r['resample_q25'])}, {f2(r['resample_median'])}, "
                     f"{f2(r['resample_q75'])} | {f2(r['within_question_rho'])} | {r['answers']} | {r['questions']} |")
    lines += ["", "Gates:"] + [f"- {g}" for g in p["gates"]] + [""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", default=str(OUT))
    r.add_argument("--threads", type=int)
    a = ap.parse_args(argv)
    res = run(Path(a.out).resolve(), a.threads)
    print(summary(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
