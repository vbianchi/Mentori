"""The lock, read once: what every model call in the experiments sends.

A caller names the model, its role, the draw and whether thinking is the row's factor (D22); it cannot
pass options of its own. Everything else comes from experiments/LOCK.toml:

    from experiments.runner.lock import load
    lock = load()
    call = lock.ollama("gemma3:27b", draw=1)          # call.options, call.fields, call.digest
    call = lock.ollama("qwen3-coder:30b", draw=2, candidate=3)   # candidate 3 of a best-of-n step: seed 2003
    call = lock.ollama("qwen3-coder:30b", draw=2, retry=1)       # retry 1 after a transient failure: seed 1000002
    lock.check_digest("gemma3:27b", served)           # refuses a model whose build differs
    lock.retrieval()                                  # Mentori's in-process encoders ([retrieval])

load() refuses a lock whose status is not "agreed". ollama() refuses a model with no digest in [models]
or no row in [sampling.models], so a model the lock does not name cannot run. A generator's seed is its draw d;
candidate k of an n-candidate step inside draw d sends d * 1000 + k ([generation] candidate_seed, Q32); d and k are
integers from 1 to 999. A candidate needs a draw, and an instrument (judge, scorer) refuses one.
D85: the judge role accepts [judge] model (the main judge) or [judge] second_model, both at the [judge] settings
(lock.judges()); the scorer role accepts [scorers] model only, and only while it is the main judge.
D81 (Q136): a generator call retried after a transient error sends that call's own seed (d, or d * 1000 + k)
+ 1,000,000 * r ([generation] retry_seed), r (1 to 3) being the step's running count of transient retries (Mentori's
own counter, step_executor.py); every draw and candidate seed is below 1,000,000, so no retry seed equals a draw or
candidate seed (two retries with the same r in one draw do share one, as two first tries share the draw). A lock without retry_seed refuses a retry (it never resends the first
try's seed), and an instrument refuses a retry number as it refuses a candidate.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "LOCK.toml"
SAMPLING_KEYS = ("temperature", "top_p", "top_k", "min_p", "repeat_penalty", "presence_penalty")
MAX_RETRIES = 3       # D81: retries 1 to 3, Mentori's MAX_TRANSIENT_RETRIES (step_executor.py), as the rule states


class LockError(Exception):
    pass


@dataclass(frozen=True)
class OllamaCall:
    model: str
    options: dict
    fields: dict          # top-level request fields: think, truncate, shift, keep_alive
    digest: str
    lock_sha256: str
    role: str
    draw: int | None = None
    thinking: bool = False
    system: str | None = None     # the model's built-in system prompt with the date fixed ([date]), else None
    notes: tuple = field(default_factory=tuple)
    requested: str = ""           # the model as the caller named it (model is the tag that runs)
    candidate: int | None = None  # k of an n-candidate step inside the draw (the seed is draw * 1000 + k), else None
    retry: int | None = None      # D81: r of a retry after a transient failure (seed + 1,000,000 * r), else None

    def payload(self, prompt: str) -> dict:
        p = {"model": self.model, "prompt": prompt, "stream": True, "options": dict(self.options), **self.fields}
        if self.system is not None:
            p["system"] = self.system
        return p


def _lookup(table: dict, tag: str):
    """A table row by exact tag, else the tag without ':latest', else the model family before ':'."""
    for key in (tag, tag.removesuffix(":latest"), tag.split(":")[0]):
        if key in table:
            return key, table[key]
    return None, None


class Lock:
    def __init__(self, raw: bytes, path: Path = LOCK):
        self.path = path
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.d = tomllib.loads(raw.decode("utf-8"))
        if self.d.get("status") != "agreed":
            raise LockError(f"{path}: status is {self.d.get('status')!r}, not 'agreed'")

    def _think(self, value: str):
        # off -> false; a level ('low') -> that level; always -> true (thinking returned apart);
        # omit -> not sent (the model has no thinking mode)
        return {"off": False, "always": True, "omit": None}.get(value, value)

    def _seed(self, draw: int | None, candidate: int | None, retry: int | None = None) -> int:
        """The seed for seed = "draw": the draw d, or d * 1000 + k for candidate k ([generation] candidate_seed).
        d and k are integers from 1 to 999, so no two calls of a run share a seed (d alone is below 1000).
        retry r (D81, [generation] retry_seed): that seed + 1,000,000 * r, r an integer from 1 to MAX_RETRIES."""
        if draw is None:
            raise LockError("a generator call needs its draw number (the seed)"
                            + (", and a candidate needs a draw" if candidate is not None else ""))
        if isinstance(draw, bool) or not isinstance(draw, int) or not 1 <= draw <= 999:
            raise LockError(f"draw {draw!r}: a draw number is an integer from 1 to 999")
        seed = draw
        if candidate is not None:
            rule = self.d["generation"].get("candidate_seed")
            if rule != "draw * 1000 + candidate":
                raise LockError(f"[generation] candidate_seed is {rule!r}; this reader knows only "
                                "'draw * 1000 + candidate'")
            if isinstance(candidate, bool) or not isinstance(candidate, int) or not 1 <= candidate <= 999:
                raise LockError(f"candidate {candidate!r}: a candidate number is an integer from 1 to 999")
            seed = draw * 1000 + candidate
        if retry is None:
            return seed
        rule = self.d["generation"].get("retry_seed")
        if rule is None:
            raise LockError("the lock has no [generation] retry_seed (D81, Q136): a retried call would resend its "
                            "first try's seed; nothing was sent")
        if rule != "seed + 1000000 * retry":
            raise LockError(f"[generation] retry_seed is {rule!r}; this reader knows only 'seed + 1000000 * retry'")
        if isinstance(retry, bool) or not isinstance(retry, int) or not 1 <= retry <= MAX_RETRIES:
            raise LockError(f"retry {retry!r}: a retry number is an integer from 1 to {MAX_RETRIES} (D81)")
        return seed + 1_000_000 * retry

    def ollama(self, model: str, role: str = "generator", draw: int | None = None,
               thinking: bool | str | None = None, candidate: int | None = None,
               retry: int | None = None) -> OllamaCall:
        """thinking (generators only): None = the role's rule ([thinking] generator, "default" since D66);
        "default" or True = the maker's default ([sampling.thinking_on], or always/omit from [sampling.models]);
        "off" or False = think off or the lowest level; a level named in [sampling.thinking_levels].
        candidate (generators only): k (1-based) of an n-candidate step inside the draw; the seed is draw * 1000 + k.
        retry (generators only, D81): r (1 to MAX_RETRIES) of a retry after a transient failure; the seed is the
        call's own seed + 1,000,000 * r ([generation] retry_seed)."""
        g, s = self.d["generation"], self.d["server"]
        run, digest = self._run_tag(model)
        if not digest:
            raise LockError(f"{run}: no digest in [models]; the lock does not let it run")
        sys_path = self.d.get("date", {}).get("system_prompt", {}).get(model)
        system = (self.path.parents[1] / sys_path).read_text() if sys_path else None
        options = {"num_ctx": g["num_ctx"], "num_predict": g["num_predict"], "num_batch": g["num_batch"]}
        _, exc = _lookup(self.d.get("exceptions", {}), model)
        if exc:
            options.update(exc)
        fields = {"truncate": s["truncate"], "shift": s["shift"], "keep_alive": s["keep_alive"]}
        notes = []
        if role in ("judge", "scorer"):
            # [scorers]: RAGAS and RAGChecker run "at the judge's settings", so both roles send the same
            j = self.d["judge"]
            if role == "judge":
                if model not in self.judges():
                    raise LockError(f"{model} is not one of the lock's judges ({', '.join(self.judges())})")
            else:
                want = self.d["scorers"]["model"]
                if model != want or want != j["model"]:
                    raise LockError(f"{model} is not the lock's {role} ({want})")
            if thinking not in (None, False, "off"):
                raise LockError("instruments run with thinking off")
            if candidate is not None:
                raise LockError("instruments take no candidate number (their seed is 'none')")
            if retry is not None:
                raise LockError("instruments take no retry number (their seed is 'none'; D81's retry_seed changes "
                                "a generator's seed)")
            options["temperature"] = j["temperature"]
            options["num_predict"] = j["num_predict"]
            if j.get("seed", "none") != "none":
                raise LockError("the judge's seed is not 'none'; this reader does not know what to send")
            fields["think"] = self._think(g["think"])
        elif role == "generator":
            key, samp = _lookup(self.d["sampling"]["models"], model)
            if samp is None:
                raise LockError(f"{model}: no row in [sampling.models]")
            samp = dict(samp)
            asked_on = thinking is True                      # thinking on as the row's factor (not "default")
            mode = self.d["thinking"]["generator"] if thinking is None else (
                "default" if thinking is True else "off" if thinking is False else thinking)
            _, on = _lookup(self.d["sampling"].get("thinking_on", {}), model)
            if mode == "default":
                if on is not None:
                    samp.update({k: v for k, v in on.items() if k != "think"})
                    samp["think"] = on.get("think", "always")
                elif samp.get("think") in ("off",) or (asked_on and samp.get("think") == "omit"):
                    raise LockError(f"{model}: no maker's default thinking in [sampling.thinking_on]"
                                    + (" (the model has no thinking mode)" if samp.get("think") == "omit" else ""))
                # always (cannot be off) and omit (no thinking mode) stay as [sampling.models] gives them
            elif mode != "off":
                levels = self.d["sampling"].get("thinking_levels", {}).get(model, [])
                if mode not in levels:
                    raise LockError(f"{model}: thinking level {mode!r} is not in [sampling.thinking_levels]")
                samp["think"] = mode
            thinking = mode
            options.update({k: samp[k] for k in SAMPLING_KEYS if k in samp})
            if g["seed"] != "draw":
                raise LockError(f"[generation] seed is {g['seed']!r}; this reader knows only 'draw'")
            options["seed"] = self._seed(draw, candidate, retry)
            think = self._think(samp.get("think", g["think"]))
            if think is not None:
                fields["think"] = think
            notes.append(f"sampling row {key!r}")
        else:
            raise LockError(f"unknown role {role!r}")
        return OllamaCall(run, options, fields, digest, self.sha256, role, draw, thinking, system, tuple(notes), model,
                          candidate, retry)

    def judges(self) -> tuple[str, ...]:
        """The models the judge role accepts: [judge] model (the main judge), then second_model where the lock names
        one (D85). Both run at the [judge] settings. The scorer role stays [scorers] model, which must be the main
        judge. Refuses a second_model that is not a tag or repeats the main judge: the same tag, the same tag with or
        without ':latest' (as [models] is looked up), or a tag that runs the main judge's digest."""
        j = self.d["judge"]
        second = j.get("second_model")
        if second is None:
            return (j["model"],)
        if not isinstance(second, str) or not second:
            raise LockError(f"[judge] second_model {second!r} is not a second judge's tag")
        main_digest, second_digest = self._run_tag(j["model"])[1], self._run_tag(second)[1]
        if (second.removesuffix(":latest") == j["model"].removesuffix(":latest")
                or (second_digest is not None and second_digest == main_digest)):
            raise LockError(f"[judge] second_model {second!r} is the main judge {j['model']!r} again")
        return (j["model"], second)

    def _run_tag(self, model: str) -> tuple[str, str | None]:
        """The tag that runs (the date-fixed copy where [date] names one) and its digest from [models]."""
        run = self.d.get("date", {}).get("model_copy", {}).get(model, model)
        _, row = _lookup(self.d.get("models", {}), run)
        return run, (row["digest"] if row else None)

    def check_digest(self, model: str, served: str) -> None:
        """served: the server's digest, whole (64 hex) or as the 12-hex id `ollama list` prints, or longer. A prefix
        under 12 hex characters is refused (Valerio, 17 October, O1): a one-character prefix matched any build."""
        _, digest = self._run_tag(model)
        short = len(served or "") < 12 or any(c not in "0123456789abcdef" for c in served or "")
        if not digest or short or not (digest == served if len(served) == 64 else digest.startswith(served)):
            raise LockError(f"{model}: the server holds {served!r}, the lock names {digest!r}")

    def gemini(self, model: str, draw: int, thinking: bool | str | None = None, candidate: int | None = None) -> dict:
        """thinking None: the generator rule ([thinking] generator, "default" since D66); "default" or True: Google's
        default (no thinking setting sent); "off" or False: the lowest level [gemini] thinking_off names.
        candidate: k (1-based) of an n-candidate step inside the draw; the seed is draw * 1000 + k."""
        mode = self.d["thinking"]["generator"] if thinking is None else (
            "default" if thinking in (True, "default") else "off" if thinking in (False, "off") else thinking)
        if mode not in ("default", "off"):
            raise LockError(f"{model}: Gemini thinking is 'default' or 'off', not {mode!r}")
        thinking = mode == "default"
        gm = self.d["gemini"]
        if model not in gm["thinking_off"]:
            raise LockError(f"{model}: no row in [gemini] thinking_off")
        if gm["seed"] != "draw":
            raise LockError(f"[gemini] seed is {gm['seed']!r}; this reader knows only 'draw'")
        cfg = {"temperature": gm["temperature"], "top_p": gm["top_p"], "top_k": gm["top_k"],
               "max_output_tokens": gm["max_output_tokens"], "seed": self._seed(draw, candidate)}
        if not thinking:
            level = gm["thinking_off"][model]
            cfg["thinking_config"] = {"thinking_budget": level} if isinstance(level, int) else {"thinking_level": level}
        return cfg

    def anthropic(self, model: str) -> dict:
        key, samp = _lookup(self.d["sampling"]["models"], model)
        if samp is None:
            raise LockError(f"{model}: no row in [sampling.models]")
        return {"model": self.d["anthropic"]["model_id"], "temperature": samp["temperature"],
                "max_tokens": self.d["anthropic"]["max_tokens"]}

    def retrieval(self) -> dict:
        """[retrieval]: Mentori's in-process encoders by role (embedding, reranker), each with hf_repo, revision (the
        Hugging Face snapshot commit), local_files_only and device. Refuses a row that is not a table, misses one of
        the four, names a revision that is not a 40-hex commit (a branch such as 'main' moves), or allows downloads."""
        table = self.d.get("retrieval")
        if not table or not isinstance(table, dict):
            raise LockError("the lock has no [retrieval] table")
        out = {}
        for role, row in table.items():
            if not isinstance(row, dict):
                raise LockError(f"[retrieval] {role}: {row!r} is not a table")
            missing = [k for k in ("hf_repo", "revision", "local_files_only", "device") if k not in row]
            if missing:
                raise LockError(f"[retrieval] {role}: no {', '.join(missing)}")
            rev = row["revision"]
            if not isinstance(rev, str) or len(rev) != 40 or any(ch not in "0123456789abcdef" for ch in rev):
                raise LockError(f"[retrieval] {role}: revision {rev!r} is not a 40-hex snapshot commit")
            if row["local_files_only"] is not True:
                raise LockError(f"[retrieval] {role}: local_files_only is {row['local_files_only']!r}, not true")
            if not isinstance(row["device"], str) or not row["device"]:
                raise LockError(f"[retrieval] {role}: no device named")
            out[role] = dict(row)
        return out


def load(path: Path = LOCK) -> Lock:
    return Lock(path.read_bytes(), path)
