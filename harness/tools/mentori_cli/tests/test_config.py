import pytest

from mentori_cli import config as c


def test_round_trip_defaults():
    d = c.check({})
    assert c.loads(c.dumps(d)) == d


def test_round_trip_every_value_changed():
    d = c.check({})
    d["model"].update(provider="gemini", name="gemini-3-flash-preview", api_key_env="LAB_GEMINI_KEY",
                      server_url="http://10.0.0.5:11434")
    d["verifier"].update(provider="ollama", name="qwen3-coder:30b", server_url="http://10.0.0.6:11434")
    d["corpus"].update(papers="pdfs", store="/data/store", index="lettuce")
    d["run"].update(strategy="rlm", rlm_turns=7, draw=3, thinking="off", strict=True, out_dir="out", prompts_dir="")
    d["components"].update(analyser="factual_to_documents", distiller="F1", distiller_trigger="every_step",
                           rlm_gate="off", rlm_search="off", planner="off", supervisor="off", synthesiser="off")
    d["sampling"] = {"temperature": 0.2, "num_ctx": 32768}
    text = c.dumps(d)
    assert c.loads(text) == d
    assert "LAB_GEMINI_KEY" in text      # the variable's name is written, as asked


def test_unknown_key_and_wrong_type_refused():
    with pytest.raises(SystemExit, match="unknown key"):
        c.check({"model": {"nme": "x"}})
    with pytest.raises(SystemExit, match="unknown section"):
        c.check({"models": {}})
    with pytest.raises(SystemExit, match="a int"):
        c.check({"run": {"rlm_turns": "10"}})
    with pytest.raises(SystemExit, match="OpenAI is a later item"):
        c.check({"model": {"provider": "openai"}})
    with pytest.raises(SystemExit, match="not a setting"):
        c.check({"sampling": {"seed": 3}})
    with pytest.raises(SystemExit, match="one of"):
        c.check({"components": {"planner": "maybe"}})


def test_parse_model():
    assert c.parse_model("ollama:gemma3:27b") == ("ollama", "gemma3:27b")
    assert c.parse_model("ollama::gemma3:27b") == ("ollama", "gemma3:27b")
    assert c.parse_model("gemini:gemini-3-flash-preview") == ("gemini", "gemini-3-flash-preview")
    assert c.parse_model("anthropic:claude-haiku-4-5") == ("anthropic", "claude-haiku-4-5")
    with pytest.raises(SystemExit):
        c.parse_model("openai:gpt-5")
    with pytest.raises(SystemExit):
        c.parse_model("gemma3")


def test_paths_are_read_against_the_config_folder(tmp_path):
    f = tmp_path / "mentori.toml"
    f.write_text(c.dumps(c.check({})))
    d = c.load(f)
    assert c.resolve_path(d, d["corpus"]["store"]) == tmp_path / "store"
    assert c.resolve_path(d, "") is None
