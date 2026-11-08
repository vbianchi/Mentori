"""The record of each answer; keys only from the environment, never printed."""

import json

import pytest
from conftest import fake_state

from mentori_cli import inject, registry, runner

FIELDS = {"tool", "question_id", "question", "answer", "error", "stop_reason", "strategy", "arm", "rlm_turns",
          "components", "reranker", "models", "draw", "departs_from_lock", "lock", "prompts", "settings_sent",
          "n_model_calls", "sources", "store", "index", "run_id", "sink"}


def ask(cfg, engine, environ=None, **opts):
    printed = []
    recs = runner.ask(cfg, [{"id": "q1", "question": "Which gene?"}], engine=engine,
                      server_state=lambda u: fake_state(), out=printed.append,
                      environ={} if environ is None else environ, **opts)
    return recs, "\n".join(printed)


def test_record_fields(cfg, engine):
    recs, printed = ask(cfg, engine)
    r = recs[0]
    assert set(r) == FIELDS
    assert r["answer"] == "answer by single_pass" and r["question_id"] == "q1"
    assert r["settings_sent"][0]["options_sent"] == {"temperature": 1.0, "seed": 1, "num_ctx": 131072}
    assert "prompt_sent" not in r["settings_sent"][0]              # what was sent, without the prompt text
    assert set(r["prompts"]["sha256"]) == set(registry.BY_NAME) and r["prompts"]["edited"] == []
    assert r["sources"] == [{"id": "p1", "file": "01_a.pdf", "page": 2}]
    assert r["models"] == {"generator": "ollama::gemma3:27b"}
    assert json.loads(printed.split("--- record\n", 1)[1]) == r     # the printed record is the JSON record
    assert engine.stored == recs


def test_edited_prompt_is_named_and_hashed(cfg, engine, tmp_path):
    d = tmp_path / "lab_prompts"
    d.mkdir()
    (d / "single_pass.txt").write_text("Lab prompt {question}")
    recs, _ = ask(cfg, engine, prompts_dir=d)
    assert recs[0]["prompts"]["edited"] == ["single_pass"]
    assert engine.spec["prompts"] == {"single_pass": "Lab prompt {question}"}


def test_key_from_named_variable_never_printed(cfg, engine):
    secret = "sk-test-SECRET-0123456789"
    cfg["model"].update(provider="gemini", name="gemini-3-flash-preview", api_key_env="LAB_GEMINI")
    env = {"LAB_GEMINI": secret}
    recs, printed = ask(cfg, engine, environ=env)
    assert env["GEMINI_API_KEY"] == secret                         # copied to the name the paper's client reads
    assert secret not in printed and secret not in json.dumps(recs) and secret not in json.dumps(engine.spec)


def test_missing_key_refused_before_anything_runs(cfg, engine):
    cfg["model"].update(provider="anthropic", name="claude-haiku-4-5")
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        ask(cfg, engine, environ={})
    assert engine.prepared is False


def test_keys_file_is_never_read():
    from experiments.runner import gemini_client
    before = gemini_client.KEYS
    try:
        inject.block_keys_file()
        assert gemini_client.KEYS == inject.NO_KEYS_FILE and not gemini_client.KEYS.exists()
        with pytest.raises(RuntimeError, match="no MENTORI_CLI_NOT_SET"):
            gemini_client.key("MENTORI_CLI_NOT_SET")
    finally:
        gemini_client.KEYS = before


def test_questions_file(tmp_path):
    f = tmp_path / "q.jsonl"
    f.write_text('{"question": "A?"}\n\n{"id": "PB_2", "question": "B?"}\n')
    assert runner.read_questions(None, f) == [{"id": "q1", "question": "A?"}, {"id": "PB_2", "question": "B?"}]
    f.write_text('{"id": "bad id", "question": "A?"}\n')
    with pytest.raises(SystemExit, match="short name"):
        runner.read_questions(None, f)
    with pytest.raises(SystemExit, match="not both"):
        runner.read_questions("A?", f)


def test_batch_gives_one_record_per_question(cfg, engine, tmp_path):
    qs = [{"id": "a", "question": "A?"}, {"id": "b", "question": "B?"}]
    recs = runner.ask(cfg, qs, engine=engine, server_state=lambda u: fake_state(), out=lambda *a: None, environ={},
                      strategy="rlm", rlm_turns=5)
    assert [r["question_id"] for r in recs] == ["a", "b"] and recs[0]["rlm_turns"] == 5
    assert recs[0]["components"] == {"rlm_gate": "on", "rlm_search": "on"}
