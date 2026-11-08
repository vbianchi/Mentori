"""The prompts mentori-cli exports as editable files: where each one lives in the paper's code and how it is filled.

Standard library only: the tool server process (experiments/mentori's own environment) imports this module too.

fill:
  "format"  the code fills it with str.format: placeholders are {name}; a literal brace is written {{ or }}
  "replace" the code fills it with str.replace on the placeholders named in `placeholders`; every other brace is literal
  "plain"   sent as it is, no placeholder
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    name: str            # the file name, prompts/<name>.txt
    component: str       # what it is, in words
    module: str          # the Python module of the paper's code that holds it
    attr: str            # the constant (or, for kind "f1", the function) in that module
    fill: str            # "format", "replace" or "plain"
    placeholders: tuple = ()   # for fill "replace": the exact texts the code replaces
    kind: str = "constant"     # "constant", or "f1": the distiller's F1 prompt, an f-string inside a function


ORCH = "backend.agents.orchestrator.prompts"

PROMPTS: tuple[Prompt, ...] = (
    # The orchestrator (strategy "orchestrator")
    Prompt("analyser", "orchestrator analyser: answers the question directly or sends it to a plan", ORCH,
           "ORCHESTRATOR_ANALYZER_PROMPT", "format"),
    Prompt("analyser_factual_to_documents", "orchestrator analyser, the factual_to_documents variant (component "
           "analyser = \"factual_to_documents\"); made from the analyser prompt when the paper's code is imported, so "
           "an edit of analyser.txt does not change it", ORCH, "ANALYZER_FACTUAL_TO_DOCUMENTS", "format"),
    Prompt("planner_system", "orchestrator planner, system message", ORCH, "PLANNER_SYSTEM_PROMPT", "plain"),
    Prompt("planner", "orchestrator planner: writes the plan of steps", ORCH, "ORCHESTRATOR_PLANNER_PROMPT", "format"),
    Prompt("step_evaluator", "orchestrator step evaluator: decides whether the plan continues after a step", ORCH,
           "ORCHESTRATOR_EVALUATOR_PROMPT", "format"),
    Prompt("supervisor_evaluation", "orchestrator supervisor: scores the quality of a step's result", ORCH,
           "SUPERVISOR_EVALUATION_PROMPT", "format"),
    Prompt("supervisor_micro_adjustment", "orchestrator supervisor: proposes a small change to a weak step", ORCH,
           "SUPERVISOR_MICRO_ADJUSTMENT_PROMPT", "format"),
    Prompt("synthesiser_system", "orchestrator synthesiser, system message", ORCH, "SYNTHESIZER_SYSTEM_PROMPT", "plain"),
    Prompt("synthesiser", "orchestrator synthesiser: writes the final cited answer from the steps' results", ORCH,
           "ORCHESTRATOR_SYNTHESIZER_PROMPT", "format"),
    Prompt("direct_answer", "orchestrator direct answer (the analyser chose to answer without a plan)", ORCH,
           "DIRECT_ANSWER_PROMPT", "format"),
    Prompt("librarian_memory", "orchestrator librarian: the memory record written after an answer", ORCH,
           "LIBRARIAN_CONSOLIDATION_PROMPT", "format"),
    Prompt("distiller", "observation distiller (component distiller = \"on\"): condenses a long tool output",
           "backend.agents.orchestrator.observation_distiller", "_DISTILL_PROMPT", "format"),
    Prompt("distiller_f1", "observation distiller, prompt F1 (component distiller = \"F1\"); the paper's code builds it "
           "in a function, so this file is its text with the two inputs written as placeholders",
           "backend.agents.orchestrator.observation_distiller", "_f1_prompt", "replace",
           ("{tool_name}", "{raw_observation}"), kind="f1"),
    # The RLM (strategy "rlm")
    Prompt("rlm_system", "RLM system prompt (search functions on, the default)", "backend.agents.prompts",
           "RLM_ORCHESTRATOR_PROMPT", "replace", ("{context_summary}", "{FILE_ORGANIZATION_RULES}")),
    Prompt("rlm_system_nosearch", "RLM system prompt with the search functions off (--off rlm_search); made from "
           "rlm_system when the paper's code is imported, so an edit of rlm_system.txt does not change it",
           "backend.agents.prompts", "RLM_ORCHESTRATOR_PROMPT_NOSEARCH", "replace",
           ("{context_summary}", "{FILE_ORGANIZATION_RULES}")),
    Prompt("rlm_cut_reply_note", "RLM turn message sent after a reply cut by the output limit",
           "backend.retrieval.rlm.orchestrator", "CUT_REPLY_NOTE", "plain"),
    # Single pass and multi-hop (strategies "single_pass", "multi_hop")
    Prompt("single_pass", "single pass: the one generation prompt", "tests.experiments.exp1_rlm_vs_singlepass",
           "SINGLE_PASS_PROMPT", "replace", ("{passages}", "{question}")),
    Prompt("multi_hop_system", "multi-hop, system message", "tests.experiments.exp1_rlm_vs_singlepass",
           "MULTI_HOP_SYSTEM", "plain"),
    Prompt("multi_hop_user", "multi-hop, the message of each hop", "tests.experiments.exp1_rlm_vs_singlepass",
           "MULTI_HOP_USER", "replace", ("{question}", "{search_num}", "{passages}", "{history}")),
    Prompt("multi_hop_closing_user", "multi-hop, the message of the closing hop (no more searches)",
           "tests.experiments.exp1_rlm_vs_singlepass", "MULTI_HOP_CLOSING_USER", "replace",
           ("{question}", "{search_num}", "{passages}", "{history}")),
    Prompt("multi_hop_cut_note", "multi-hop, the search-log line after a reply cut by the output limit",
           "tests.experiments.exp1_rlm_vs_singlepass", "MULTI_HOP_CUT_NOTE", "plain"),
    # Verified pass (strategy "verified_pass")
    Prompt("verified_pass_generation", "verified pass: the generation prompt", "backend.retrieval.pipeline",
           "GENERATION_PROMPT", "replace", ("{passages}", "{question}")),
    Prompt("verified_pass_verifier", "verified pass: the verifier that classifies each passage's relevance",
           "backend.retrieval.chunk_verifier", "VERIFICATION_PROMPT", "replace", ("{query}", "{passages}")),
)

BY_NAME = {p.name: p for p in PROMPTS}

# The F1 template: _f1_prompt(tool_name, content) called with these two markers, then each marker written as its
# placeholder (registry entry "distiller_f1")
F1_TOOL_MARK = "\x00MENTORI_CLI_TOOL_NAME\x00"
F1_CONTENT_MARK = "\x00MENTORI_CLI_RAW_OBSERVATION\x00"


def f1_render(template: str, tool_name: str, content: str) -> str:
    """The F1 prompt from its template: each placeholder replaced once, in one pass, as the f-string fills it."""
    import re
    return re.sub(r"\{tool_name\}|\{raw_observation\}",
                  lambda m: tool_name if m.group(0) == "{tool_name}" else content, template)
