"""0.1.1: the walkthrough's defects. F2 an edited prompt keeps the paper's placeholders; F5 --draw is checked before
anything runs, the paper's Gemini warning reaches the terminal only for Gemini runs, ask exits 1 when an answer
errored, and init's hint names `uv run`. No model, no network."""

import pytest
from conftest import FakeEngine, fake_state

from mentori_cli import cli, config as c, prompts as pr, registry, runner


def ask(cfg, engine, environ=None, out=None, **opts):
    return runner.ask(cfg, [{"id": "q1", "question": "Which gene?"}], engine=engine,
                      server_state=lambda u: fake_state(), out=(out if out is not None else (lambda s: None)),
                      environ={} if environ is None else environ, **opts)


# ---- F2: placeholders ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("p", registry.PROMPTS, ids=lambda p: p.name)
def test_every_paper_prompt_passes_its_own_check(p):
    paper = pr.paper_prompts()[p.name]
    pr.check_placeholders(p, paper, paper, p.name)
    if p.fill == "replace":
        assert pr.placeholders(p, paper), f"{p.name}: the paper's prompt holds none of its placeholders"


def test_paper_single_pass_without_question_is_refused(tmp_path):
    defaults = pr.paper_prompts()
    pr.export(tmp_path, defaults)
    f = tmp_path / "single_pass.txt"
    f.write_text(f.read_text(encoding="utf-8").replace("{question}", "the question"), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"single_pass\.txt: the placeholders differ.*missing \{question\}"):
        pr.load(tmp_path, defaults)


def test_every_placeholder_removed_is_refused(tmp_path):
    defaults = pr.paper_prompts()
    (tmp_path / "single_pass.txt").write_text("Answer the question from the passages.")
    with pytest.raises(SystemExit, match=r"missing \{passages\} \{question\}"):
        pr.load(tmp_path, defaults)


def test_format_prompt_missing_added_and_unreadable(tmp_path):
    defaults = pr.paper_prompts()
    p = registry.BY_NAME["planner"]
    names = pr.placeholders(p, defaults["planner"])
    assert "{user_query}" in names
    f = tmp_path / "planner.txt"
    f.write_text(defaults["planner"].replace("{user_query}", "the query"))
    with pytest.raises(SystemExit, match=r"missing \{user_query\}"):
        pr.load(tmp_path, defaults)
    f.write_text(defaults["planner"] + "\nLab note: {lab_note}")
    with pytest.raises(SystemExit, match=r"not in the paper's prompt \{lab_note\}"):
        pr.load(tmp_path, defaults)
    f.write_text(defaults["planner"] + "\nA single brace { is unreadable")
    with pytest.raises(SystemExit, match="str.format cannot read it"):
        pr.load(tmp_path, defaults)
    f.write_text(defaults["planner"] + "\nA literal {{brace}} is fine.")
    assert pr.load(tmp_path, defaults)["edited"] == ["planner"]


def test_f1_prompt_without_raw_observation_is_refused(tmp_path):
    defaults = pr.paper_prompts()
    (tmp_path / "distiller_f1.txt").write_text(defaults["distiller_f1"].replace("{raw_observation}", "x"))
    with pytest.raises(SystemExit, match=r"missing \{raw_observation\}"):
        pr.load(tmp_path, defaults)


def test_ask_with_a_prompt_missing_its_placeholder_runs_nothing(cfg, engine, tmp_path):
    d = tmp_path / "lab_prompts"
    d.mkdir()
    (d / "single_pass.txt").write_text("Lab prompt with no inputs")
    with pytest.raises(SystemExit, match=r"missing \{question\}"):
        ask(cfg, engine, prompts_dir=d)
    assert engine.spec is None and engine.stored == []        # nothing installed, nothing answered


# ---- F5: --draw ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("draw", [0, -1, 1000])
def test_draw_out_of_range_refused_before_anything_runs(cfg, engine, draw):
    with pytest.raises(SystemExit, match=r"--draw .*from 1 to 999"):
        ask(cfg, engine, draw=draw)
    assert engine.prepared is False


def test_cli_draw_zero_leaves_no_run_folder(tmp_path):
    f = tmp_path / "mentori.toml"
    f.write_text(c.dumps(c.check({})), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"--draw 0"):
        cli.main(["ask", "Which gene?", "--config", str(f), "--draw", "0"])
    assert not (tmp_path / "runs").exists()


# ---- F5: the paper's Gemini warning -------------------------------------------------------------------------------

class WarningEngine(FakeEngine):
    """Prints what the paper's ModelRouter() prints when GEMINI_API_KEY is unset, as MentoriEngine.run does."""

    async def run(self, questions, st, spec):
        print(runner.GEMINI_WARNING)
        print("another line from the paper's code")
        return await super().run(questions, st, spec)


def test_gemini_warning_dropped_for_an_ollama_run(cfg, tmp_path, capsys):
    ask(cfg, WarningEngine(tmp_path / "sink"))
    o = capsys.readouterr()
    assert runner.GEMINI_WARNING not in o.out and runner.GEMINI_WARNING not in o.err
    assert "another line from the paper's code" in o.out          # every other line passes unchanged


def test_gemini_warning_on_stderr_for_a_gemini_run(cfg, tmp_path, capsys):
    cfg["model"].update(provider="gemini", name="gemini-3-flash-preview")
    ask(cfg, WarningEngine(tmp_path / "sink"), environ={"GEMINI_API_KEY": "k"})
    o = capsys.readouterr()
    assert runner.GEMINI_WARNING not in o.out and runner.GEMINI_WARNING in o.err


# ---- F5: exit status and init's hint ------------------------------------------------------------------------------

@pytest.mark.parametrize("errors,status", [([None, None], 0), ([None, "TimeoutError: x"], 1), (["e", "e"], 1)])
def test_ask_exit_status(monkeypatch, tmp_path, errors, status):
    f = tmp_path / "mentori.toml"
    f.write_text(c.dumps(c.check({})), encoding="utf-8")
    recs = [{"question_id": f"q{i}", "error": e} for i, e in enumerate(errors, 1)]
    monkeypatch.setattr(runner, "ask", lambda *a, **k: recs)
    assert cli.main(["ask", "Which gene?", "--config", str(f)]) == status


def test_init_hint_says_uv_run(tmp_path, capsys):
    assert cli.main(["init", str(tmp_path / "lab")]) == 0
    assert "then: uv run mentori-cli index --config " in capsys.readouterr().out
