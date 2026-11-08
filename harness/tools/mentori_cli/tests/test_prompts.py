"""The exported prompt files hold the paper's prompts byte for byte, so untouched files run the paper's prompts.

These tests import the paper's modules (no model, no network)."""

import importlib

import pytest

from mentori_cli import inject, paths, prompts as pr, registry

paths.setup_sys_path()


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    folder = tmp_path_factory.mktemp("prompts")
    pr.export(folder, pr.paper_prompts())
    return folder


def test_one_file_per_prompt(exported):
    assert sorted(f.stem for f in exported.glob("*.txt")) == sorted(registry.BY_NAME)


@pytest.mark.parametrize("p", [p for p in registry.PROMPTS if p.kind == "constant"], ids=lambda p: p.name)
def test_body_is_the_paper_constant_byte_for_byte(exported, p):
    raw = (exported / f"{p.name}.txt").read_bytes()
    constant = getattr(importlib.import_module(p.module), p.attr)
    assert pr.body(raw.decode("utf-8")).encode("utf-8") == constant.encode("utf-8")
    assert raw.endswith(constant.encode("utf-8"))


def test_f1_template_renders_the_paper_prompt(exported):
    mod = importlib.import_module("backend.agents.orchestrator.observation_distiller")
    template = pr.body((exported / "distiller_f1.txt").read_text(encoding="utf-8"))
    for tool, content in [("smart_query", "Table 2: 45.6% (n=342)"), ("x", ""), ("{tool_name}", "{raw_observation}"),
                          ("a\nb", "unicode µg/mL → ok")]:
        assert registry.f1_render(template, tool, content).encode() == mod._f1_prompt(tool, content).encode()


def test_header_names_component_and_source_line(exported):
    for p in registry.PROMPTS:
        text = (exported / f"{p.name}.txt").read_text(encoding="utf-8")
        assert text.startswith(pr.HEADER_MARK + f"component: {p.name}, ")
        src = next(line for line in text.splitlines() if line.startswith(pr.HEADER_MARK + "source: "))
        loc = src.split("source: ", 1)[1].split(" ")[0]
        file, line = loc.rsplit(":", 1)
        code = (paths.repo() / file).read_text(encoding="utf-8").splitlines()[int(line) - 1]
        assert code.startswith(f"def {p.attr}(" if p.kind == "f1" else f"{p.attr} =") or code.startswith(f"{p.attr}=")


def test_untouched_folder_edits_nothing(exported):
    info = pr.load(exported, pr.paper_prompts())
    assert info["edited"] == []
    assert set(info["sha256"]) == set(registry.BY_NAME)


def test_file_without_header_is_read_whole_and_unknown_file_refused(tmp_path):
    defaults = pr.paper_prompts()
    (tmp_path / "single_pass.txt").write_text("My prompt {passages} {question}")
    info = pr.load(tmp_path, defaults)
    assert info["edited"] == ["single_pass"] and info["used"]["single_pass"] == "My prompt {passages} {question}"
    (tmp_path / "planer.txt").write_text("typo")
    with pytest.raises(SystemExit, match="not prompt names"):
        pr.load(tmp_path, defaults)


def test_installed_prompt_reaches_the_importing_modules():
    planner = importlib.import_module("backend.agents.orchestrator.planner")
    exp1 = importlib.import_module("tests.experiments.exp1_rlm_vs_singlepass")
    dist = importlib.import_module("backend.agents.orchestrator.observation_distiller")
    paper = pr.paper_prompts()
    try:
        inject.install_prompts({"planner": "EDITED {user_query}", "single_pass": "EDITED SP {question}",
                                "distiller_f1": "F1 EDITED {tool_name} / {raw_observation}"})
        assert planner.ORCHESTRATOR_PLANNER_PROMPT == "EDITED {user_query}"
        assert importlib.import_module(registry.ORCH).ORCHESTRATOR_PLANNER_PROMPT == "EDITED {user_query}"
        assert exp1.single_pass_prompt("Q?", []) == "EDITED SP Q?"
        assert dist.distiller_prompt("tool", "raw", "F1") == "F1 EDITED tool / raw"
        assert pr.paper_prompts() == paper          # the paper's values stay readable after an install
    finally:
        inject.install_prompts({k: paper[k] for k in ("planner", "single_pass")})
        dist._f1_prompt = getattr(dist, inject.PAPER_PREFIX + "_f1_prompt")
    assert planner.ORCHESTRATOR_PLANNER_PROMPT == paper["planner"]
    assert exp1.SINGLE_PASS_PROMPT == paper["single_pass"]
