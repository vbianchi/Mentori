"""Q82 (D75): does the distiller fire in Mentori as built? Counts, in the full pipeline's stored answers, the step attempts
whose output passed Mentori's distiller threshold (int(0.40 x LOCK num_ctx) x 4 = 209,712 characters,
observation_distiller._distill_threshold_chars) and reports the largest step output measured.

    uv run --project experiments/mentori --frozen python experiments/mentori/orchestrator/distiller_firing.py \
        [findings/runs/exp_03__full_orchestrator__exp_v4_s20_n0/answers.json]

The decision it informs (Q82's recommended text): run the full pipeline first. If no step passed the threshold, report
that the distiller never fired in Mentori as built (with the largest step output measured), and do not present the
"distiller off" and "distiller with prompt F1" set-ups as measurements: they would send Gemini the same text as the full
pipeline. F1's effect on whole answers, if still wanted, is the separately named stress condition (switch
distiller_trigger "every_step", with Mentori's prompt and with F1), labelled as not Mentori's default.

A step is counted from its record: over_distill_threshold when the record has it (executor.py, D75), else the length of
its stored raw_content against the threshold. Reads only; writes nothing.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from experiments.runner.lock import load  # noqa: E402

DEFAULT = ROOT / "findings" / "runs" / "exp_03__full_orchestrator__exp_v4_s20_n0" / "answers.json"
DISTILL_FRACTION = 0.40   # observation_distiller._DISTILL_FRACTION


def threshold_chars() -> int:
    """observation_distiller._distill_threshold_chars, from the lock without importing Mentori."""
    return int(load().d["generation"]["num_ctx"] * DISTILL_FRACTION) * 4


def count(answers_path: Path) -> dict:
    threshold = threshold_chars()
    data = json.loads(Path(answers_path).read_text())
    answers = steps = over = 0
    largest = {"chars": 0, "answer_key": None, "step_id": None, "attempt_no": None}
    fired = {}
    for row in data.get("results", []):
        answers += 1
        for st in (row.get("generation") or {}).get("steps") or []:
            steps += 1
            n = len(st.get("raw_content") or "")
            is_over = st["over_distill_threshold"] if "over_distill_threshold" in st else n > threshold
            over += bool(is_over)
            status = (st.get("distill") or {}).get("status") or "not_asked"
            fired[status] = fired.get(status, 0) + 1
            if n > largest["chars"]:
                largest = {"chars": n, "answer_key": row.get("answer_key"), "step_id": st.get("step_id"),
                           "attempt_no": st.get("attempt_no")}
    return {"answers_path": str(answers_path), "threshold_chars": threshold, "answers": answers,
            "step_attempts": steps, "steps_over_threshold": over, "distill_status": fired,
            "largest_step_output": largest,
            "distiller_fired_in_mentori_as_built": over > 0}


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    if not path.is_file():
        raise SystemExit(f"{path}: no answers file (run the full pipeline first, Q82)")
    out = count(path)
    print(json.dumps(out, indent=2))
    if out["answers"] and not out["distiller_fired_in_mentori_as_built"]:
        print(f"\nNo step output passed {out['threshold_chars']:,} characters in {out['step_attempts']} step attempts "
              f"of {out['answers']} answers (largest {out['largest_step_output']['chars']:,}): the distiller never "
              f"fired in Mentori as built; 'distiller off' and 'distiller with prompt F1' are not measurements (Q82).")


if __name__ == "__main__":
    main(sys.argv)
