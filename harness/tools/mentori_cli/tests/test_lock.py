"""Defaults from experiments/LOCK.toml; every departure named; --strict refuses before anything is sent."""

import copy

import pytest
from conftest import fake_state, paper_lock_d

from mentori_cli import inject, lockfx, runner

URL = "http://127.0.0.1:11434"


def gen(provider, name, role="generator", url=URL):
    return {"role": role, "provider": provider, "name": name, "url": url}


def test_paper_model_on_a_paper_server_departs_from_nothing():
    d0 = paper_lock_d()
    d, dep = lockfx.effective(d0, [gen("ollama", "gemma3:27b")], {}, "default", {URL: fake_state()})
    assert dep == [] and d == d0


def test_other_ollama_version_is_a_departure():
    d, dep = lockfx.effective(paper_lock_d(), [gen("ollama", "gemma3:27b")], {}, "default",
                              {URL: fake_state(version="0.12.0")})
    assert len(dep) == 1 and dep[0].startswith("departs from LOCK: Ollama") and "0.12.0" in dep[0]
    assert d["server"]["ollama_version"] == "0.12.0"       # what ollama_client checks before each call
    other = "http://10.0.0.2:11434"
    with pytest.raises(SystemExit, match="different versions"):
        lockfx.effective(paper_lock_d(), [gen("ollama", "gemma3:27b"), gen("ollama", "gpt-oss:20b", "verifier", other)],
                         {}, "default", {URL: fake_state(version="0.12.0"), other: fake_state()})


def test_model_the_lock_does_not_name_runs_and_is_marked():
    st = fake_state(tags={"mistral-small:24b": "ab" * 32})
    d, dep = lockfx.effective(paper_lock_d(), [gen("ollama", "mistral-small:24b")], {"temperature": 0.3}, "default",
                              {URL: st})
    assert d["models"]["mistral-small:24b"]["digest"] == "ab" * 32
    assert any("no row in [models]" in x for x in dep) and any("[sampling.models]" in x for x in dep)
    assert any("temperature = 0.3" in x for x in dep)
    assert all(x.startswith("departs from LOCK: ") for x in dep)


def test_other_digest_and_missing_date_copy_are_departures():
    st = fake_state()
    st["tags"]["gemma3:27b"] = "cd" * 32
    st["tags"].pop("gpt-oss:20b-date20261010")
    st["tags"]["gpt-oss:20b"] = "ef" * 32
    d, dep = lockfx.effective(paper_lock_d(), [gen("ollama", "gemma3:27b"), gen("ollama", "gpt-oss:20b", "verifier")],
                              {}, "default", {URL: st})
    assert any("gemma3:27b on" in x and "digest" in x for x in dep)
    assert "gpt-oss:20b" not in d["date"]["model_copy"]
    assert any("date fixed" in x for x in dep)


def test_model_missing_on_the_server_is_refused():
    with pytest.raises(SystemExit, match="ollama pull"):
        lockfx.effective(paper_lock_d(), [gen("ollama", "nothere:1b")], {}, "default", {URL: fake_state()})


def test_cloud_departures():
    d, dep = lockfx.effective(paper_lock_d(), [gen("gemini", "gemini-3-flash-preview")], {}, "default", {})
    assert dep == []
    d, dep = lockfx.effective(paper_lock_d(), [gen("gemini", "gemini-3-pro")], {"temperature": 0.5}, "default", {})
    assert d["gemini"]["temperature"] == 0.5 and len(dep) == 2
    d, dep = lockfx.effective(paper_lock_d(), [gen("anthropic", "claude-haiku-4-5")], {}, "default", {})
    assert dep == []
    d, dep = lockfx.effective(paper_lock_d(), [gen("anthropic", "claude-sonnet-4-5")], {}, "default", {})
    assert d["anthropic"]["model_id"] == "claude-sonnet-4-5" and len(dep) == 2


def test_installed_lock_is_what_the_paper_runner_reads():
    from experiments.runner import lock as L
    st = fake_state(tags={"mistral-small:24b": "ab" * 32})
    d, dep = lockfx.effective(paper_lock_d(), [gen("ollama", "mistral-small:24b")], {"temperature": 0.3}, "default",
                              {URL: st})
    raw = L.LOCK.read_bytes()
    sha = lockfx.run_sha256(raw, d)
    before = L.load
    try:
        inject.install_lock(d, sha)
        lk = L.load()
        assert lk.sha256 == sha and lk.sha256 != L.Lock(raw).sha256
        call = lk.ollama("mistral-small:24b", role="generator", draw=2)
        assert call.options["temperature"] == 0.3 and call.options["seed"] == 2 and call.digest == "ab" * 32
        from experiments.runner import ollama_client
        assert ollama_client.load is L.load            # the runner's own modules read the same lock
    finally:
        paper = L._mentori_cli_paper_load
        inject._rebind(L.load, paper)
        L.load = paper
    assert L.load() .sha256 == L.Lock(raw).sha256 and before is not None


def test_strict_refuses_before_anything_is_prepared(cfg, engine):
    cfg["model"]["name"] = "mistral-small:24b"
    cfg["run"]["strict"] = True
    state = lambda url: fake_state(tags={"mistral-small:24b": "ab" * 32})   # noqa: E731
    with pytest.raises(SystemExit, match="--strict: this run departs from the paper's lock"):
        runner.ask(cfg, [{"id": "q1", "question": "?"}], engine=engine, server_state=state, out=lambda *a: None)
    assert engine.prepared is False and engine.spec is None


def test_without_strict_the_departure_runs_and_is_recorded(cfg, engine):
    cfg["model"]["name"] = "mistral-small:24b"
    state = lambda url: fake_state(tags={"mistral-small:24b": "ab" * 32})   # noqa: E731
    recs = runner.ask(cfg, [{"id": "q1", "question": "?"}], engine=engine, server_state=state, out=lambda *a: None)
    assert recs[0]["departs_from_lock"] and engine.spec["lock"] is not None
    assert recs[0]["lock"]["run_sha256"] != recs[0]["lock"]["paper_sha256"]


def test_no_departure_installs_no_lock(cfg, engine):
    recs = runner.ask(cfg, [{"id": "q1", "question": "?"}], engine=engine, server_state=lambda u: fake_state(),
                      out=lambda *a: None)
    assert engine.spec["lock"] is None and recs[0]["departs_from_lock"] == []
    assert recs[0]["lock"]["run_sha256"] == recs[0]["lock"]["paper_sha256"]


def test_effective_does_not_change_the_paper_dict():
    d0 = paper_lock_d()
    keep = copy.deepcopy(d0)
    lockfx.effective(d0, [gen("anthropic", "claude-sonnet-4-5")], {"temperature": 0.1}, "off", {})
    assert d0 == keep
