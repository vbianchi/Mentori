"""Each switch reaches the paper's strategy function, with the paper's own names and values."""

import asyncio

import pytest
from conftest import Recorder

from mentori_cli import config as c, runner


def run(cfg, **opts):
    st = runner.resolve(cfg, **opts)
    rec = Recorder()
    asyncio.run(runner.dispatch(st, "Q?", rec, "retriever", "coll", "router", "uid", "task"))
    return st, rec.calls[0]


@pytest.mark.parametrize("name", c.ORCH_COMPONENTS)
def test_orchestrator_off_switch_reaches_the_orchestrator(cfg, name):
    st, (fn, kw) = run(cfg, strategy="orchestrator", off=[name])
    assert fn == "orchestrator" and kw["switches"] == {name: "off"}


def test_orchestrator_defaults_send_no_switch(cfg):
    _, (fn, kw) = run(cfg, strategy="orchestrator")
    assert kw["switches"] == {}          # Mentori as built: exp_03's full_orchestrator passes {}


def test_config_values_other_than_off(cfg):
    cfg["components"].update(distiller="F1", analyser="factual_to_documents", distiller_trigger="every_step")
    _, (fn, kw) = run(cfg, strategy="orchestrator", off=["planner"])
    assert kw["switches"] == {"distiller": "F1", "analyser": "factual_to_documents",
                              "distiller_trigger": "every_step", "planner": "off"}


def test_switch_names_and_values_are_the_papers():
    from backend.agents.orchestrator import schemas
    assert set(runner.ORCH_DEFAULTS) == set(schemas.ORCHESTRATOR_SWITCHES)
    assert runner.ORCH_DEFAULTS == {k: v[0] for k, v in schemas.ORCHESTRATOR_SWITCHES.items()}
    for k in c.ORCH_COMPONENTS:
        assert "off" in schemas.ORCHESTRATOR_SWITCHES[k]


def test_rlm_switches_and_turns(cfg):
    _, (fn, kw) = run(cfg, strategy="rlm")
    assert (kw["max_turns"], kw["quality_gate"], kw["search_tools"], kw["config_name"]) == (10, True, True, "rlm_10")
    _, (fn, kw) = run(cfg, strategy="rlm", off=["rlm_gate"], rlm_turns=7)
    assert (kw["max_turns"], kw["quality_gate"], kw["search_tools"], kw["config_name"]) == (7, False, True, "rlm_7")
    _, (fn, kw) = run(cfg, strategy="rlm", off=["rlm_search"])
    assert (kw["quality_gate"], kw["search_tools"]) == (True, False)


@pytest.mark.parametrize("strategy", ["single_pass", "multi_hop", "verified_pass"])
def test_plain_strategies(cfg, strategy):
    st, (fn, kw) = run(cfg, strategy=strategy, model=("gemini", "gemini-3-flash-preview"))
    assert fn == strategy and kw["gen"] == "gemini::gemini-3-flash-preview"
    if strategy == "verified_pass":
        assert st["models"] == {"generator": "gemini::gemini-3-flash-preview", "verifier": "ollama::gpt-oss:20b"}
    else:
        assert st["models"] == {"generator": "gemini::gemini-3-flash-preview"}


@pytest.mark.parametrize("strategy,off", [("single_pass", "planner"), ("rlm", "supervisor"),
                                          ("orchestrator", "rlm_gate"), ("multi_hop", "rlm_search")])
def test_switch_of_another_strategy_is_refused(cfg, strategy, off):
    with pytest.raises(SystemExit, match="has no such component"):
        runner.resolve(cfg, strategy=strategy, off=[off])


def test_unknown_switch_and_turns_without_rlm_refused(cfg):
    with pytest.raises(SystemExit, match="--off 'reranker'"):
        runner.resolve(cfg, strategy="rlm", off=["reranker"])     # the reranker stays on (D40)
    with pytest.raises(SystemExit, match="--rlm-turns is for strategy rlm"):
        runner.resolve(cfg, strategy="single_pass", rlm_turns=5)


def test_other_verifier_is_injected(cfg, engine):
    from conftest import fake_state
    cfg["verifier"]["name"] = "qwen3-coder:30b"
    runner.ask(cfg, [{"id": "q1", "question": "?"}], engine=engine, strategy="verified_pass",
               server_state=lambda u: fake_state(), out=lambda *a: None)
    assert engine.spec["verifier"] == "ollama::qwen3-coder:30b"
    cfg["verifier"]["name"] = "gpt-oss:20b"
    runner.ask(cfg, [{"id": "q1", "question": "?"}], engine=engine, strategy="verified_pass",
               server_state=lambda u: fake_state(), out=lambda *a: None)
    assert engine.spec["verifier"] is None        # the paper's verifier: nothing injected
