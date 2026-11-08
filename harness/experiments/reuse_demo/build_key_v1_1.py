"""Build experiments/reuse_demo/key_v1_1.json: key v1 (key_v1.json, signed off 16 October, D75) with the fixes of the
25 October re-read (experiments/reuse_demo/reread_2026-10-25.json, the items confirmed by the second reader and kept in
the verdict given to Valerio) and D137 (PB_005: a hedged "probably RXLR" answer). Valerio, 25 Oct: "go with v1.1"; he
signed it off on 26 Oct ("Go with it", Q-I2a, D153). key_v1.json and build_key.py are not changed.

Run from the repository root:  uv run --frozen python experiments/reuse_demo/build_key_v1_1.py

Every edit names the exact v1 text it replaces and refuses to run when that text is not there once. New evidence goes
at the end of each record's list, so every v1 evidence index, key concept index and synthesis reference keeps its
meaning. The checks are build_key.py's: every evidence sentence on its page (qtext.find), every key concept a substring
of its evidence sentence, no em dash; the script refuses to write otherwise.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from qtext import find  # noqa: E402

V1 = HERE / "key_v1.json"
OUT = HERE / "key_v1_1.json"
P1, P2, P3, P4, P5 = ("01_parra2021_dm_genes", "02_simko2013_qtl", "03_christopoulou2015_mrc",
                      "04_giesbers2017_blr31", "05_pelgrom2019_blr38")
FILES = {p: p + ".pdf" for p in (P1, P2, P3, P4, P5)}

v1_bytes = V1.read_bytes()
v1 = json.loads(v1_bytes)
key = copy.deepcopy(v1)
R = {r["id"]: r for r in key["records"]}
bad = []


def sub(rid, field, old, new):
    r = R[rid]
    n = r[field].count(old)
    if n != 1:
        bad.append(f"{rid} {field}: the v1 text is there {n} times, not once: {old[:70]}")
        return
    r[field] = r[field].replace(old, new)


def add_ev(rid, paper, page, sentence, supports):
    R[rid]["evidence"].append({"paper": paper, "page": page, "sentence": sentence, "supports": supports})
    return len(R[rid]["evidence"]) - 1


# ---------------------------------------------------------------- PB_001 (Simko 2013)
sub("PB_001", "short_answer", "No QTL x QTL or QTL x environment interaction was detected.",
    "No QTL x QTL or QTL x environment interaction was significant at P ≤ 0.001.")
i = add_ev("PB_001", P2, 4, "However, alignment of the lettuce genome sequence and the ultra- high density linkage map "
           "revealed that qDM5.1 is located close to a gene potentially encoding a TIR-NBS-LRR disease resistance "
           "protein for pathogen recognition.",
           "Context: a predicted TIR-NBS-LRR gene near qDM5.1, not a known Dm cluster.")
sub("PB_001", "question_issues", "which is context, not part of the answer.",
    "which is context, not part of the answer. Page 4 also places qDM5.1 close to a gene potentially encoding a "
    f"TIR-NBS-LRR protein (evidence {i}); that gene is not a known Dm cluster, so an answer that mentions it does not "
    "contradict \"not in a Dm cluster\". The interaction statement is the paper's test at P ≤ 0.001 (evidence 12): "
    "none was significant at that level.")

# ---------------------------------------------------------------- PB_002 (Christopoulou 2015)
kc = R["PB_002"]["key_concepts"]
want = ["Dm3 and Dm18 were abrogated by trigger sequences derived from both the NB and LRR domains",
        "Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence",
        "Dm6 was compromised by the NB-derived trigger sequences", "chimeric Type I gene",
        "more closely related to Dm3 than Dm6", "Dm14, Dm16, Dm18"]
if [k["phrase"] for k in kc] != want:
    bad.append("PB_002: the v1 key concepts are not the expected six")
R["PB_002"]["key_concepts"] = [
    {"phrase": want[0], "evidence_index": 0},
    {"phrase": "Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence but not the NB-derived trigger "
               "sequence", "evidence_index": 0},
    {"phrase": "Dm6 was compromised by the NB-derived trigger sequences but not those derived from the LRR",
     "evidence_index": 1},
    {"phrase": "chimeric Type I gene", "evidence_index": 2},
    {"phrase": "LRR domain that is more closely related to Dm3 than Dm6", "evidence_index": 2},
    {"phrase": "with a more distantly related NB domain", "evidence_index": 2},
]
sub("PB_002", "question_issues", "the question uses the text's name.",
    "the question uses the text's name. (5) Key concepts 2 and 3 carry both halves of each contrast (Dm16 lost with "
    "the LRR trigger but not the NB trigger; Dm6 the reverse), and concepts 5 and 6 both halves of the chimera "
    "inference (LRR close to Dm3, NB more distant), because the question asks what the authors inferred from the "
    "difference. Concept 2 keeps the paper's wording, which also names Dm14; by (1), an answer that says Dm14 was not "
    "tested with the NB construct is right. Evidence 3 stays as support but carries no concept.")

# ---------------------------------------------------------------- PB_003 (Giesbers 2017, Pelgrom 2019)
e108 = add_ev("PB_003", P5, 8, "To further substantiate the linkage between BLR38 recognition and resistance against "
              "B. lactucae, a leaf disc assay with Bl:22 was performed on L. serriola LS102 × L. sativa GreenTowers F3 "
              "family #108, which segregates for the two loci required for BLR38 recognition.",
              "The joint mapping of resistance and recognition is for Bl:22, in F3 family #108.")
eq = add_ev("PB_003", P4, 6, "In previous studies, we have shown that the resistance of L. saligna CGN05271 to "
            "B. lactucae is probably based on QTLs and did not show evidence for monogenic dominant resistance loci "
            "(Jeuken & Lindhout, 2002; Jeuken et al., 2008; Zhang et al., 2009a).",
            "CGN05271: resistance probably quantitative, no monogenic dominant locus.")
ep = add_ev("PB_003", P4, 8, "BLN08-responsive preBIL6.2 plants ( n = 2) of L. saligna CGN05271 were as susceptible "
            "to Bl:24 as L. sativa cv Olof (susceptible parent).",
            "CGN05271: BLN08-responsive plants were fully susceptible to Bl:24.")
ea = add_ev("PB_003", P5, 8, "Yet, the effector variants with non-synonymous SNPs were all still recognized in "
            "L. serriola LS102 (Fig. S6, see Supporting Information), suggesting that the identified alleles have not "
            "evolved to escape detection by the L. serriola LS102 resistance proteins.",
            "BLR38 variants of the other races are all still recognized.")
eb = add_ev("PB_003", P5, 9, "The three BLR38 variants with amino acid substitutions were still recognized in "
            "L. serriola LS102, indicating that BLR38 allelic variation in these races did not evolve to overcome "
            "resistance mediated by L. serriola LS102 encoded genes.",
            "Discussion: allelic variation in BLR38 did not evolve to overcome the resistance.")
eh = add_ev("PB_003", P5, 8, "Heterozygous plants (AaBb) were moderately resistant (average infection severity, 6.5%).",
            "Bl:22, family #108: AaBb moderately resistant.")
er = add_ev("PB_003", P5, 8, "AABB, AaBB and AABb plants were highly resistant (average infection severity, "
            "0.03%–1.34%) (Fig. 6c).",
            "Bl:22, family #108: the recognizing loci give strong resistance.")
sub("PB_003", "short_answer", "Bl:28 and Bl:31, and resistance and recognition map to the same markers.",
    "Bl:28 and Bl:31, and in F3 family #108 resistance to Bl:22 and BLR38 recognition map to the same markers on "
    "chromosomes 4 and 8.")
sub("PB_003", "short_answer", "In both systems Bl:24 resistance maps to chromosome 1, apart from the "
    "effector-recognition locus.",
    "In L. saligna CGN05318 and L. serriola LS102 Bl:24 resistance maps to chromosome 1, apart from the "
    "effector-recognition locus; in L. saligna CGN05271 resistance is probably quantitative, and BLN08-responsive "
    "plants were as susceptible to Bl:24 as cv. Olof.")
sub("PB_003", "synthesis_statement", "and resistance co-maps with recognition [17, 24, 25, 23].",
    f"and, in F3 family #108, resistance to Bl:22 co-maps with recognition [17, 24, 25, 23, {e108}].")
sub("PB_003", "synthesis_statement", "In both papers Bl:24 resistance maps to chromosome 1 [7, 24].",
    f"In L. saligna CGN05318 and L. serriola LS102 Bl:24 resistance maps to chromosome 1 [7, 24]; in L. saligna "
    f"CGN05271 it is probably quantitative [{eq}, {ep}].")
sub("PB_003", "question_issues", "only the exclusion of incomplete resistance is tested on BLN08 data.",
    "only the exclusion of incomplete resistance is tested on BLN08 data. (8) Points an answer gets credit for, "
    "though the short answer does not need them: Bl:23 and Bl:28 carry the same BLR38 allele as Bl:24 and are still "
    f"resisted, and every BLR38 variant is still recognized (evidence {ea}, {eb}; the sentence naming Bl:23, Bl:24 "
    "and Bl:28 as homozygous for the Bl:24 allele crosses the page 7 to 8 break with figure text between and is not "
    "quoted), so Bl:24's escape does not lie in the BLR38 sequence, which supports the suppression reading; "
    "Pelgrom's \"at least five\" suppressed Bl:24 effectors (evidence 28) follow page 9's four effectors unlinked to "
    "Bl:24 resistance, BLN08 among them (evidence 26), plus BLR38; the five are not named, but the count implies "
    "that Pelgrom apply the suppression postulate to BLN08 too; the BLR38 loci give strong resistance to Bl:22 (evidence "
    f"{eh}, {er}), which counts against the \"another pathogen\" and \"incomplete resistance\" explanations for "
    f"BLR38. (9) The joint mapping of resistance and recognition was done for Bl:22 in F3 family #108 only (evidence "
    f"{e108}, 23); linkage to the other four races rests on comparing fixed F3 families (evidence 25). (10) The "
    f"chromosome 1 resistance holds for CGN05318 and LS102; in CGN05271 it is probably quantitative (evidence {eq}, "
    f"{ep}).")

# ---------------------------------------------------------------- PB_004 (Parra 2021)
e31 = add_ev("PB_004", P1, 8, "Phenotyping of F3 families followed by QTL mapping narrowed down the region to 31 Mb "
             "and confirmed the discrepancy between the susceptible genotype and phenotype; F3 data also demonstrated "
             "cosegregation of resistance to an additional B. lactucae isolate, C15L1752 (Supplementary Fig. 2).",
             "UC07106: the F3 families narrowed the region to 31 Mb.")
sub("PB_004", "short_answer", "UC07106's resistance (MRC1, a region of about 40 Mb;",
    "UC07106's resistance (MRC1, a region of about 40 Mb in the F2, narrowed to 31 Mb with F3 families;")
sub("PB_004", "question_issues", "(c) The UC07108 isolate is printed C13C1407 in the text and C13O1407 in Table 2.",
    "(c) The UC07108 isolate is printed C13C1407 in the text and C13O1407 in Table 2. (d) Table 2 prints a "
    "chi-square of 3.59 for UC07106 (evidence 7), but its counts, 90R/44S against 3:1 (expected 100.5 and 33.5), "
    "give 1.10 + 3.29 = 4.39, above 3.84 (1 df, P = 0.05); the recomputed value agrees with the page 8 text, which "
    "says the segregation deviated (evidence 9). An answer that calls UC07106 3:1 is not wrong, since the key counts "
    f"it among the 3:1 populations. (e) UC07106's about 40 Mb is the F2 association; F3 families narrowed it to 31 Mb "
    f"(evidence {e31}), and an answer giving either is right.")

# ---------------------------------------------------------------- PB_005 (not answerable)
et = add_ev("PB_005", P5, 2, "BLR38 260 1–18 RLLR 46 – – No",
            "Paper 05 Table 1 row: BLR38, an RXLR-like effector with an RLLR motif.")
em = add_ev("PB_005", P5, 4, "Recognition of BLR38 maps to loci on chromosomes (chr) 4 and 8, whereas resistance to "
            "Bremia lactucae Bl:24 maps to chr 1.",
            "BLR38 recognition maps to chromosomes 4 and 8, not to MRC2.")
sub("PB_005", "question_issues", "Three traps.", "Four traps.")
sub("PB_005", "question_issues", "Paper 04's germplasm included",
    f"(4) BLR38, the effector of paper 05, is RXLR-like with an RLLR motif (Table 1, evidence {et}); its recognition "
    f"in L. serriola LS102 maps to two loci on chromosomes 4 and 8 (evidence {em}), not to MRC2, and paper 05 never "
    "mentions Dm3. An answer naming BLR38 as Dm3's effector is wrong. Paper 04's germplasm included")
sub("PB_005", "question_issues", "The v2.4 category for not-answerable questions is out_of_domain.",
    "D137 (Valerio, 25 October): the papers mention RXLR only as background on oomycete effectors (paper 04 page 1, "
    "paper 05 page 1), and paper 05 page 2 lists recognized effectors without an RXLR motif (BLG01 GKLR, BLN08, "
    "evidence 5). An answer that adds \"probably an RXLR effector, as oomycete effectors often are\" is acceptable "
    "only when it is clear that the answer is not in the papers and that there are no supporting data; an answer "
    "that gives RXLR, or any motif or effector, as the answer is wrong. The v2.4 category for not-answerable "
    "questions is out_of_domain.")

# ---------------------------------------------------------------- checks and support (as build_key.py)
for r in key["records"]:
    r["evidence_check"] = []
    for i, e in enumerate(r["evidence"]):
        how = find(e["paper"], e["page"], e["sentence"])
        if how is None:
            bad.append(f"{r['id']} evidence {i}: not found on {e['paper']} p{e['page']}: {e['sentence'][:80]}")
        r["evidence_check"].append("exact" if how else "NOT EXACT")
    for k in r["key_concepts"]:
        if k["phrase"] not in r["evidence"][k["evidence_index"]]["sentence"]:
            bad.append(f"{r['id']} key concept not in its evidence: {k['phrase']}")
    r["support"] = [{"paper": FILES[e["paper"]], "page": e["page"], "quote": e["sentence"]} for e in r["evidence"]]
    if chr(0x2014) in json.dumps(r, ensure_ascii=False):
        bad.append(f"{r['id']}: em dash")
    for m in re.finditer(r"\[([0-9, ]+)\]", r.get("synthesis_statement", "")):
        for n in m.group(1).split(","):
            if int(n) >= len(r["evidence"]):
                bad.append(f"{r['id']}: synthesis reference {n} out of range")
for a, b in zip(v1["records"], key["records"]):   # every v1 evidence item is unchanged and in its place
    if b["evidence"][:len(a["evidence"])] != a["evidence"]:
        bad.append(f"{a['id']}: a v1 evidence item changed or moved")
if bad:
    print("\n".join(bad))
    sys.exit(1)

out = {
    "version": "PB v1.1",
    "status": "signed off by Valerio Bianchi, 26 October 2026 (Q-I2a \"Go with it\", D153); the key of the I2 run",
    "based_on": {"file": "experiments/reuse_demo/key_v1.json", "sha256": hashlib.sha256(v1_bytes).hexdigest(),
                 "signed_off": v1["signed_off"]},
    "drafted": "2026-10-25",
    "revision": "v1.1 (25 October): the 25 October re-read (experiments/reuse_demo/reread_2026-10-25.json; fresh "
                "readers against the five papers, each flag checked by a second reader) and D137. PB_001 interaction "
                "at P ≤ 0.001, TIR-NBS-LRR note; PB_002 key concepts carry both halves of each contrast and of the "
                "chimera inference, concept 6 dropped; PB_003 joint mapping scoped to Bl:22 in family #108, chromosome "
                "1 resistance scoped to CGN05318 and LS102, credit points (8) to (10); PB_004 31 Mb, chi-square note; "
                "PB_005 BLR38 trap and D137. Changes listed in experiments/reuse_demo/V1_1_CHANGES.md. Before: "
                + v1["revision"],
    **{k: v1[k] for k in v1 if k not in ("version", "status", "signed_off", "drafted", "revision", "records")},
    "records": key["records"],
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("wrote", OUT, len(out["records"]), "records;", sum(len(r["evidence"]) for r in out["records"]),
      "evidence items, all exact; key_v1.json sha256", hashlib.sha256(V1.read_bytes()).hexdigest()[:16], "unchanged")
