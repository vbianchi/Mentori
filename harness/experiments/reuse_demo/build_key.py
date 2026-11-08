"""Build experiments/reuse_demo/key_draft.json and key_v1.json (PB_001..PB_005) in answer key v2.4's record format.

Run from the repository root:  uv run python experiments/reuse_demo/build_key.py

Every evidence sentence is checked against the page text in experiments/reuse_demo/text/ (whitespace collapsed;
a word broken across a line with a hyphen is accepted joined or with the hyphen kept; qtext.py). Every key concept
must be a substring of the evidence sentence it points to, as in v2.4. The script refuses to write otherwise.
Draft 2 (16 October): the five findings of the quote, answerability and expert reviews are applied.
Draft 3 = v1 (16 October, D75): the three sign-off cards decided as recommended. Q53 (SIGNOFF.md Q1) and Q55 (Q3)
keep the draft's reading; Q54 (Q2) drops the outside-the-corpus race dates from PB_003 note (2). key_v1.json is the
signed-off key; key_draft.json holds the same records under the draft header.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from qtext import find  # noqa: E402

ROOT = HERE.parent.parent
OUT = HERE / "key_draft.json"
OUT_V1 = HERE / "key_v1.json"
V24 = ROOT / "data/ground_truth_v2/all_v2_4.json"

P1, P2, P3, P4, P5 = ("01_parra2021_dm_genes", "02_simko2013_qtl", "03_christopoulou2015_mrc",
                      "04_giesbers2017_blr31", "05_pelgrom2019_blr38")


def ev(paper, page, sentence, supports, tag=None):
    return {"paper": paper, "page": page, "sentence": sentence, "supports": supports, "_tag": tag}


def kc(phrase, i):
    return {"phrase": phrase, "evidence_index": i}


R = []

# ---------------------------------------------------------------- PB_001 extractive, factual_recall (paper 2)
E1 = [
    ev(P2, 1, "We developed a population of recombinant inbred lines (RILs) originating from a cross between "
              "these two legacy cultivars, constructed a linkage map, and identified two QTLs for resistance "
              "on linkage groups 2 ( qDM2.1) and 5 (qDM5.1) that determined resistance under field conditions "
              "in California and the Netherlands.",
       "Abstract: two QTLs, qDM2.1 on linkage group 2 and qDM5.1 on linkage group 5, effective under field "
       "conditions in California and the Netherlands."),
    ev(P2, 1, "Alleles conferring elevated resistance at both QTLs originate from cultivar Iceberg.",
       "Abstract: Iceberg contributes the resistance alleles at qDM2.1 and qDM5.1."),
    ev(P2, 1, "An additional QTL on linkage group 9 (qDM9.1) was detected through simultaneous analysis of all "
              "experiments with mixed-model approach.",
       "Abstract: a third QTL, qDM9.1, from the mixed-model analysis of all experiments together."),
    ev(P2, 1, "Alleles for elevated resistance at this locus originate from cultivar Grand Rapids.",
       "Abstract: Grand Rapids contributes the resistance allele at qDM9.1."),
    ev(P2, 4, "The two QTLs were located on LG 2b ( qDM2.1) and LG 5a ( qDM5.1).",
       "Results: the linkage subgroups, LG 2b and LG 5a."),
    ev(P2, 4, "This QTL was not detected as significant when experiments were analyzed separately, with LOD "
              "scores ranging from 0.9 to 2.1.",
       "Results: qDM9.1 is found only in the combined mixed-model analysis."),
    ev(P2, 4, "The additive effect of this QTL assessed on combined data was 0.088 what is ca. 60% to 75% of the "
              "additive effects of QTLs qDM5.1 and qDM2.1, respectively.",
       "Results: qDM9.1 is the smaller effect, about 60% to 75% of the other two."),
    ev(P2, 4, "Neither of the QTLs mapped to the clusters of known Dm genes.",
       "Results: qDM2.1 and qDM5.1 are outside the Dm clusters."),
    ev(P2, 7, "None of qDM2.1, qDM5.1,o r qDM9.1 is located in these resistance gene clusters.",
       "Discussion: all three QTLs are outside the Dm clusters (on LG 1, 2, 3 and 4)."),
    ev(P2, 7, "The QTL on LG 2b is well separated from the Dm gene cluster on LG 2a.",
       "Discussion: the linkage group 2 QTL is not the linkage group 2 Dm cluster."),
    ev(P2, 7, "Two significant QTLs for downy mildew resistance were detected in the present study when "
              "experiments were analyzed individually.",
       "Discussion: qDM2.1 and qDM5.1 are significant in single experiments."),
    ev(P2, 7, "The two QTLs were effective both in Salinas, California and The Netherlands field experiments.",
       "Discussion: the two main QTLs worked at both locations."),
    ev(P2, 4, "No significant QTL 3 QTL or QTL 3 environment interaction was detected for these three QTLs at "
              "P # 0.001.",
       "Context: no QTL x QTL or QTL x environment interaction (the text layer prints the multiplication "
       "sign as '3' and the less-or-equal sign as '#')."),
]
R.append({
    "id": "PB_001",
    "question": "In the Grand Rapids x Iceberg recombinant inbred line population, which QTLs for downy mildew "
                "resistance were found, which legacy cultivar contributes the resistance allele at each, and do "
                "any of them map to the known clusters of Dm genes?",
    "category": "factual_recall",
    "answer_type": "extractive",
    "question_answerable": True,
    "evidence": E1,
    "short_answer": "Three QTLs. qDM2.1 on LG 2b and qDM5.1 on LG 5a were significant in individual experiments "
                    "and were effective in field experiments both in Salinas, California and in the Netherlands; "
                    "the alleles for elevated resistance at both come from cultivar Iceberg. A third QTL, qDM9.1 "
                    "on linkage group 9, was found only by the mixed-model analysis of all experiments together "
                    "(LOD 0.9 to 2.1 when experiments were analysed separately); its additive effect was about "
                    "60% to 75% of those of qDM5.1 and qDM2.1, and its resistance allele comes from Grand Rapids. "
                    "None of the three is located in the clusters of known Dm genes; the LG 2b QTL is well "
                    "separated from the Dm cluster on LG 2a. No QTL x QTL or QTL x environment interaction was "
                    "detected.",
    "key_concepts": [
        kc("qDM2.1", 0), kc("qDM5.1", 0), kc("originate from cultivar Iceberg", 1), kc("qDM9.1", 2),
        kc("originate from cultivar Grand Rapids", 3),
        kc("Neither of the QTLs mapped to the clusters of known Dm genes", 7),
        kc("well separated from the Dm gene cluster", 9),
    ],
    "question_issues": "The paper uses \"QTLs\" for two levels of evidence. qDM2.1 and qDM5.1 were significant in "
                       "individual experiments; qDM9.1 was significant only in the mixed-model analysis of all "
                       "seven experiments. An answer that names only the two main QTLs is incomplete but not wrong "
                       "in substance. The page 4 sentence \"Neither of the QTLs mapped to the clusters of known Dm "
                       "genes\" is about the two main QTLs; page 7 extends it to all three (evidence 8). The key "
                       "concept for the clusters points at the page 4 sentence because the page 7 one carries a "
                       "text-layer artifact (\",o r\"). Linked markers, if an answer gives them: BYET and BISR for "
                       "qDM2.1, AFLP E45/M49-286.64 for qDM5.1 (page 4). The paper places qDM2.1 in the same region "
                       "as rbq5 (quantitative resistance from L. saligna), which is context, not part of the answer.",
    "notes": "Source: experiments/reuse_demo/text/02_simko2013_qtl.pdf.pages.json (pypdf). Pages are the 1-based "
             "index in that file. The text layer prints the multiplication sign as \"3\" (\"Grand Rapids 3 "
             "Iceberg\", \"QTL 3 QTL\") and the less-or-equal sign as \"#\"; quotes keep the text layer. "
             "Key concepts are substrings of their evidence sentences, as in v2.4. min_core is "
             "5: the reuse corpus has one core size, its five papers.",
    "evidence_check": [],
    "checks": [],
    "disagreements": "",
})

# ---------------------------------------------------------------- PB_002 extractive, technical (paper 3)
E2 = [
    ev(P3, 10, "Dm3 and Dm18 were abrogated by trigger sequences derived from both the NB and LRR domains "
               "ofDm3; however, Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence but not the "
               "NB-derived trigger sequence (Dm14 was not tested with the NB-RNAi construct).",
       "Dm3 and Dm18 lost with both triggers; Dm14 and Dm16 lost with the LRR trigger; Dm14 untested with NB."),
    ev(P3, 10, "Conversely, Dm6 was compromised by the NB-derived trigger sequences but not those derived "
               "from the LRR.",
       "Dm6 lost with the NB trigger only."),
    ev(P3, 10, "This was surprising because NB domains tend to be more conserved than LRR domains; this "
               "suggests thatDm16 is a chimeric Type I gene with a LRR domain that is more closely related to "
               "Dm3 than Dm6 but with a more distantly related NB domain.",
       "The inference about Dm16: a chimeric Type I gene."),
    ev(P3, 2, "A fragment of the LRR-encoding sequence of RGC2B used as the trigger sequence for RNA "
              "interference (RNAi) abrogated the resistance mediated by not only Dm3 but also Dm14, Dm16, "
              "Dm18,a n d Ra, suggesting that these linked resistance phenotypes also are encoded by RGC2 "
              "family members (Wroblewski et al. 2007).",
       "The LRR trigger also abrogated Ra; this result is from Wroblewski et al. 2007."),
    ev(P3, 4, "RGC2B_LRR_RNAie (chr 2) RGC2B 11/20 RGC2 Dm1 , Dm3, Dm2, Dm6, Dm14, Dm15, Dm16, Dm18, Ra Dm3, "
              "Dm14, Dm16, Dm18, Ra pGollum",
       "Table 1 row, LRR trigger: tested Dm1, Dm3, Dm2, Dm6, Dm14, Dm15, Dm16, Dm18 and Ra; silenced Dm3, "
       "Dm14, Dm16, Dm18 and Ra (predicted to target 11 of 20 RGC2 members)."),
    ev(P3, 4, "RGC2B_NB_RNAi (chr 2) RGC2B 12/20 RGC2 Dm2 , Dm3, Dm6, Dm15, Dm16, Dm18 Dm3, Dm6, Dm18 pGollum",
       "Table 1 row, NB trigger: tested Dm2, Dm3, Dm6, Dm15, Dm16 and Dm18; silenced Dm3, Dm6 and Dm18 "
       "(predicted to target 12 of 20 RGC2 members)."),
    ev(P3, 10, "The two cv. Diana transgenics with the greatest levels of silencing were crossed to different "
               "genotypes to test forDm2, Dm6, Dm15, Dm16, and Dm18 speciﬁcities.",
       "The specificities tested with the NB transgenics (Dm3 is in Diana itself); Dm14 is not among them."),
    ev(P3, 8, "Eight Dm genes and resistance to root aphid (Ra) are clustered near one end of chromosome 2 that "
              "genetically de ﬁne the borders of MRC2 (McHale et al. 2009) ( Table S2 ).",
       "Ra is resistance to root aphid."),
]
R.append({
    "id": "PB_002",
    "question": "In the RNAi tester stocks for the RGC2 family at MRC2, which Dm specificities were abrogated by "
                "the trigger sequence from the NB-encoding domain of RGC2B and which by the LRR-derived trigger, "
                "and what did the authors infer about Dm16 from the difference?",
    "category": "technical",
    "answer_type": "extractive",
    "question_answerable": True,
    "evidence": E2,
    "short_answer": "The NB-derived RGC2B trigger abrogated Dm3, Dm6 and Dm18. The LRR-derived trigger abrogated "
                    "Dm3, Dm14, Dm16 and Dm18, and also Ra (resistance to root aphid); the LRR result is from "
                    "Wroblewski et al. 2007. So Dm3 and Dm18 were lost with both triggers, Dm16 only with the LRR "
                    "trigger, and Dm6 only with the NB trigger; Dm14 was lost with the LRR trigger and was not "
                    "tested with the NB construct. Dm2 and Dm15 were tested with both constructs and lost with "
                    "neither, and Dm1 was tested with the LRR construct and not lost (Table 1). Because NB domains "
                    "are usually more conserved than LRR domains, the authors found this surprising and inferred "
                    "that Dm16 is a chimeric Type I gene whose LRR domain is more closely related to Dm3 than to "
                    "Dm6, but whose NB domain is more distantly related.",
    "key_concepts": [
        kc("Dm3 and Dm18 were abrogated by trigger sequences derived from both the NB and LRR domains", 0),
        kc("Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence", 0),
        kc("Dm6 was compromised by the NB-derived trigger sequences", 1),
        kc("chimeric Type I gene", 2),
        kc("more closely related to Dm3 than Dm6", 2),
        kc("Dm14, Dm16, Dm18", 3),
    ],
    "question_issues": "(1) The page 10 sentence is loosely worded, not contradictory: \"but not the NB-derived "
                       "trigger sequence\" is true of Dm16, and the parenthesis says Dm14 \"was not tested with the "
                       "NB-RNAi construct\". The list of specificities tested with the NB transgenics (page 10) and "
                       "the Table 1 NB row both leave Dm14 out. The answer treats Dm14 as lost with the LRR trigger "
                       "and untested with NB. (2) The LRR result (Dm3, Dm14, Dm16, Dm18, Ra) was published earlier "
                       "(Wroblewski et al. 2007) and is restated here; the NB construct is this paper's. (3) The "
                       "prose names Dm2 and Dm15 among the specificities tested with the NB transgenics; only "
                       "Table 1 states that they were not lost, and only Table 1 shows Dm1 tested with the LRR "
                       "construct. (4) The figure 4 caption on page 11 calls the Dm3 gene \"RGC2DB\" while the text "
                       "calls it RGC2B; the question uses the text's name.",
    "notes": "Source: experiments/reuse_demo/text/03_christopoulou2015_mrc.pdf.pages.json (pypdf). The text layer "
             "of this paper drops or inserts spaces (\"ofDm3\", \"thatDm16\", \"Dm18,a n d Ra\", \"de ﬁne\"); "
             "quotes keep the text layer as printed, and \"se-\\nquences\" is joined. The two Table 1 rows are "
             "quoted as the text layer gives them on page 4 (columns: construct, gene model, RGC members "
             "targeted, Dm specificities tested, effectors, silenced phenotypes, vector). Key concepts avoid "
             "the spacing artifacts.",
    "evidence_check": [],
    "checks": [],
    "disagreements": "",
})

# ---------------------------------------------------------------- PB_003 synthesis, cross_document (papers 4, 5)
E3 = [
    # Giesbers 2017: BLN08 inheritance and position
    ev(P4, 1, "BLN08 induced a hypersensitive response (HR) in 55% of the L. saligna accessions, but "
              "responsiveness did not co -segregate with resistance to Bl:24.",
       "BLN08: broad recognition in L. saligna, not linked to Bl:24 resistance.", "g_55"),
    ev(P4, 8, "In BC1_CGN05318, a range of responses to BLN08 from 0.3 to 1.7 was observed in 32 (53%) of 60 "
              "plants (Table S4).",
       "Names the population and effector the next sentence maps.", "g_bc1"),
    ev(P4, 8, "The response was mapped as a dominant gene on C8 from 20 to 33 cM.",
       "BLN08 response in BC1_CGN05318: a single dominant gene on chromosome 8.", "g_c8"),
    ev(P4, 8, "For both L. saligna accessions CGN05271 and CGN05318, the gene causing responsiveness to BLN08 "
              "may overlap with resistance cluster MRC8A or B in L. sativa cv Salinas (Fig. 5).",
       "The BLN08 gene may overlap MRC8A or B, in two accessions.", "g_mrc8_may"),
    ev(P4, 9, "However, the response to BLN08 was mapped to C8 and co-localized with MRC8(A –B) on C8 in "
              "L. sativa.",
       "Discussion: BLN08 response co-localizes with MRC8A to B.", "g_mrc8"),
    ev(P4, 9, "MRC8A and MRC8B contain 42 NLR-encoding genes (Christopoulou et al., 2015) without known Dm "
              "genes (Parra et al., 2016).",
       "The BLN08 region holds NLR genes but no known Dm gene.", "g_42"),
    ev(P4, 8, "Instead, an R gene on C1 that was not associated with BLN08 responsiveness was identiﬁed in "
              "L. saligna CGN05318.",
       "Bl:24 resistance in CGN05318 comes from a separate gene on chromosome 1.", "g_c1"),
    ev(P4, 8, "This gene mapped on C1 between 32 –73 cM, which overlaps with MRC1 in L. sativa cv Salinas "
              "(Fig. S4).",
       "That chromosome 1 gene overlaps MRC1.", "g_c1pos"),
    ev(P4, 8, "Average responses to effectors were signiﬁcantly higher (P < 0.001) for plants with two "
              "L. saligna alleles compared with plants with one L. saligna allele in all accessions, except for "
              "CGN05310 ( P > 0.1) (Fig. S5).",
       "The \"dominant\" BLN08 response is also dose dependent (CGN05318 is one of the accessions).", "g_dose"),
    # Giesbers 2017: the explanations
    ev(P4, 9, "A potential explanation for the lack of co-segregation between responsiveness to an effector "
              "and resistance is that the R gene is not functional against the B. lactucae isolate from "
              "which the effector has been cloned, because other effectors in this isolate suppress the "
              "resistance response (King et al., 2014; Teper et al., 2014).",
       "Explanation: suppression by other effectors of the same isolate.", "g_x1"),
    ev(P4, 9, "It is possible that the R gene is effective against older downy mildew isolates, in which the "
              "R gene-suppressing effectors have not yet evolved.",
       "Explanation continued: the R gene may work against older isolates.", "g_x1b"),
    ev(P4, 9, "Another possibility is that a second unlinked gene is required for resistance (Cooley et al., "
              "2000; Kachroo et al., 2000).",
       "Explanation: a second unlinked gene required for resistance.", "g_x2"),
    ev(P4, 9, "Or, a functional version of a second tightly linked gene, as in NLR pairs (Cesari et al., 2014; "
              "Williams et al., 2014), may be required as an inducer of disease resistance signalling.",
       "Explanation: a second tightly linked gene, as in NLR pairs.", "g_x3"),
    ev(P4, 9, "The R gene might also confer resistance against another pathogen and recognize the downy mildew "
              "effector as a side effect.",
       "Explanation: the R gene targets another pathogen.", "g_x4"),
    ev(P4, 9, "Other explanations for the absence of co-segregation between responsiveness to an effector and "
              "disease resistance may be a lack of proper effector translocation in the host, mis-timed "
              "expression of the effector or the R gene, or incomplete resistance mediated by the R gene "
              "(Krasileva et al., 2011; Goritschnig et al., 2012).",
       "Explanations: translocation, timing, incomplete resistance.", "g_x5"),
    ev(P4, 9, "The latter explanation can be excluded, as the average resistance level of BLN08-responsive "
              "BC1 plants was not signiﬁcantly lower than that of BLN08-nonresponsive BC1 plants.",
       "Incomplete resistance is excluded for BLN08.", "g_excl"),
    ev(P4, 9, "The induced response to BLR31 in a narrow range of accessions was associated with Bl:24 "
              "resistance, whereas the response to BLN08 in a broad range of accessions was not.",
       "Contrast within paper 04: BLR31 is linked to Bl:24 resistance, BLN08 is not.", "g_blr31"),
    # Pelgrom 2019: BLR38
    ev(P5, 1, "The recognition of effector BLR38 in Lactuca serriola LS102 did not co-segregate with "
              "resistance against race Bl:24, but was linked to resistance against multiple other "
              "B. lactucae races.",
       "BLR38: not linked to Bl:24 resistance, linked to resistance to other races.", "p_abs"),
    ev(P5, 1, "Two unlinked loci are both required for effector recognition and are located near known major "
              "resistance clusters.",
       "BLR38 recognition needs two unlinked loci near MRCs.", "p_two"),
    ev(P5, 5, "In the absence of at least one of the L. serriola LS102 loci at either chr 4 and/or chr 8 (aabb, "
              "AAbb, aaBB, aaBb, Aabb), plants were, without exception, unresponsive to BLR38 (Fig. 3b).",
       "Without either locus there is no recognition at all.", "p_noresp"),
    ev(P5, 5, "In conclusion, the L. serriola LS102 loci on chr 4 and chr 8 are semi-dominant and are both "
              "required to mediate the recognition of BLR38.",
       "Inheritance of BLR38 recognition: two semi-dominant loci, both required.", "p_semi"),
    ev(P5, 5, "The observed requirement for both loci was confirmed by the segregation ratio in the F2 "
              "population, where the response segregates in a 7 : 4 : 5 (unresponsive : chlorosis : necrosis) "
              "ratio (tested ratio, 7 : 4 : 5; χ2 = 0.89; df = 2; 95% confidence cut-off χ2 ≤ 5.991).",
       "F2 segregation 7:4:5 for the two-locus model.", "p_745"),
    ev(P5, 8, "The smallest mapping interval on chr 4 partially overlapped with the upstream border of MRC4 "
              "(Fig. 7a), whereas the smallest mapping interval on chr 8 was located just downstream of "
              "MRC8A (Fig. 7b).",
       "Positions of the two BLR38 loci relative to MRC4 and MRC8A.", "p_pos"),
    ev(P5, 8, "Mapping of either disease resistance or BLR38 recognition resulted in maximum LOD scores at the "
              "same marker positions on chr 4 and chr 8, confirming previous results.",
       "Resistance (to Bl:22, F3 family #108) and recognition map to the same markers.", "p_comap"),
    ev(P5, 7, "Disease resistance to Bl:24 was mapped to a single, highly significant peak at the top of "
              "chromosome 1 with a LOD score of 79 (Fig. 2c), corresponding to the reported location of Dm17 "
              "(Maisonneuve et al., 1994).",
       "Bl:24 resistance in LS102 is Dm17 on chromosome 1, separate from the BLR38 loci.", "p_dm17"),
    ev(P5, 7, "In summary, these results demonstrate that the recognition of BLR38 is linked to resistance "
              "against races Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31.",
       "BLR38 recognition gives resistance to five other races.", "p_races"),
    ev(P5, 9, "In addition, the recognition of effectors BLG01, BLG03, BLN06 and BLN08 was not genetically "
              "linked to resistance against Bl:24, whereas the recognition of BLR31 did provide resistance to "
              "Bl:24 (Giesbers et al., 2017; Stassen et al., 2013).",
       "Paper 05 places BLN08 beside BLR38 and BLR31 beside them as the contrast.", "p_list"),
    ev(P5, 9, "Yet, our data contrasted with previously characterized B. lactucae effector responses that "
              "mapped to single loci (Giesbers et al., 2017; Stassen et al., 2013).",
       "Paper 05 contrasts its two loci with paper 04's single loci.", "p_contrast"),
    ev(P5, 10, "Race Bl:24 is thought to suppress the recognition or response to at least five Bl:24-derived "
               "effectors, but not to that recognized by Dm17.",
       "Paper 05 adopts the suppression explanation for Bl:24.", "p_supp"),
    ev(P5, 10, "To determine whether the loci mediating BLR38 recognition constitute a ‘sensor’ and ‘helper’ NLR "
               "pair, sequencing of the corresponding regions in the L. serriola LS102 genome is required.",
       "Model 1 for the two loci: a sensor and helper NLR pair.", "p_pair"),
    ev(P5, 10, "Alternatively, the loci mediating BLR38 recognition could constitute an R protein and an effector "
               "target.",
       "Model 2 for the two loci: an R protein and its guardee or decoy.", "p_guard"),
    ev(P5, 2, "BLR31 recognition also co-segregated with resistance to B. lactucae race 24 (Bl:24) and was "
              "mapped to MRC2 (Giesbers et al., 2017).",
       "BLR31, the contrast: linked to Bl:24 resistance and mapped to MRC2.", "p_blr31"),
]
T3 = {e["_tag"]: i for i, e in enumerate(E3)}


def refs(text):
    return re.sub(r"\{([a-z0-9_ ,]+)\}",
                  lambda m: "[" + ", ".join(str(T3[t.strip()]) for t in m.group(1).split(",")) + "]", text)


R.append({
    "id": "PB_003",
    "question": "Two Bremia lactucae effectors cloned from race Bl:24, BLN08 in Lactuca saligna and BLR38 in "
                "L. serriola LS102, trigger a hypersensitive response, yet recognition of neither co-segregates "
                "with Bl:24 resistance. Comparing the two studies, how is each recognition inherited, where does "
                "it map relative to the major resistance clusters, and how do the BLR38 results bear on the "
                "explanations Giesbers et al. give for effector recognition that does not co-segregate with "
                "resistance?",
    "category": "cross_document",
    "answer_type": "synthesis",
    "question_answerable": True,
    "evidence": E3,
    "short_answer": "BLN08 (Giesbers et al. 2017) triggered an HR in 55% of L. saligna accessions. In "
                    "BC1_CGN05318 the response was mapped as one dominant gene on chromosome 8 (20 to 33 cM), and "
                    "in CGN05271 and CGN05318 it co-localizes with MRC8A to B, a region with 42 NLR-encoding genes "
                    "and no known Dm gene. It did not co-segregate with Bl:24 resistance, which in CGN05318 came "
                    "from a separate dominant R gene on chromosome 1 (32 to 73 cM, overlapping MRC1). BLR31, by "
                    "contrast, did co-segregate with Bl:24 resistance and mapped to MRC2. Giesbers et al. list "
                    "explanations for recognition without resistance: other effectors of the isolate suppress the "
                    "resistance, so the R gene may be effective against \"older\" isolates in which the "
                    "suppressors have not yet evolved; a second unlinked gene is required for resistance; a second "
                    "tightly linked gene, as in NLR pairs; the R gene targets another pathogen; poor effector "
                    "translocation; mis-timed expression; or incomplete resistance, which they exclude for BLN08. "
                    "BLR38 (Pelgrom et al. 2019) recognition in L. serriola LS102 needs two unlinked, "
                    "semi-dominant loci (F2 7:4:5, unresponsive : chlorosis : necrosis), one on chromosome 4 "
                    "partly overlapping the upstream border of MRC4 and one on chromosome 8 just downstream of "
                    "MRC8A; plants lacking either locus never responded. Recognition is not linked to Bl:24 "
                    "resistance, which in LS102 is Dm17 at the top of chromosome 1, but it is linked to resistance "
                    "against Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31, and resistance and recognition map to the same "
                    "markers. Pelgrom et al. explain the missing Bl:24 link by suppression: Bl:24 is thought to "
                    "suppress recognition of, or response to, at least five of its own effectors, but not the one "
                    "recognized by Dm17. So BLR38 fits the suppression explanation: the resistance works, but not "
                    "against the effector's own race. The corpus does not say whether the five races are older "
                    "than Bl:24. The two-locus requirement concerns recognition itself, so BLR38 is not a case of "
                    "Giesbers' second unlinked gene required for resistance. Pelgrom et al. suggest the two loci "
                    "may be a sensor and helper NLR pair, or an R protein and an effector target; this relates to "
                    "Giesbers' NLR-pair explanation, though there the second gene is tightly linked and the BLR38 "
                    "loci are unlinked. In both systems Bl:24 resistance maps to chromosome 1, apart from the "
                    "effector-recognition locus.",
    "synthesis_statement": refs(
        "Giesbers et al. (paper 04) map BLN08 recognition in L. saligna as one dominant gene on chromosome 8 "
        "that co-localizes with MRC8A to B, a region with NLR genes and no known Dm gene, and find it unlinked "
        "to Bl:24 resistance {g_55, g_bc1, g_c8, g_mrc8_may, g_mrc8, g_42}; Bl:24 resistance in that population "
        "is a separate R gene on chromosome 1 overlapping MRC1 {g_c1, g_c1pos}, and BLR31, unlike BLN08, is "
        "linked to Bl:24 resistance and maps to MRC2 {g_blr31, p_blr31}. They list explanations for recognition without resistance, "
        "suppression by other effectors of the isolate with the R gene effective against older isolates, a "
        "second unlinked or tightly linked gene, another pathogen as the R gene's target, translocation and "
        "timing, and exclude incomplete resistance for BLN08 {g_x1, g_x1b, g_x2, g_x3, g_x4, g_x5, g_excl}. "
        "Pelgrom et al. (paper 05) find that BLR38 recognition in L. serriola LS102 needs two unlinked "
        "semi-dominant loci, segregating 7:4:5, partly overlapping MRC4 on chromosome 4 and just downstream of "
        "MRC8A on chromosome 8 {p_two, p_noresp, p_semi, p_745, p_pos}, which they contrast with paper 04's "
        "single loci {p_contrast}. BLR38 recognition is unlinked to Bl:24 resistance, which is Dm17 on "
        "chromosome 1, but linked to resistance against five other races, and resistance co-maps with "
        "recognition {p_abs, p_dm17, p_races, p_comap}. Paper 05 lists BLN08 among effectors whose recognition "
        "is unlinked to Bl:24 resistance and attributes this to suppression by Bl:24 {p_list, p_supp}. BLR38 "
        "therefore fits paper 04's suppression explanation, while its second locus is needed for recognition, "
        "not for resistance after recognition, so it does not illustrate the second-unlinked-gene explanation; "
        "paper 05's sensor and helper or guardee models {p_pair, p_guard} bear on paper 04's NLR-pair "
        "explanation, although the BLR38 loci are unlinked. In both papers Bl:24 resistance maps to "
        "chromosome 1 {g_c1pos, p_dm17}."),
    "key_concepts": [
        kc("55% of the L. saligna accessions", T3["g_55"]),
        kc("dominant gene on C8", T3["g_c8"]),
        kc("co-localized with MRC8", T3["g_mrc8"]),
        kc("other effectors in this isolate suppress the resistance response", T3["g_x1"]),
        kc("both required to mediate the recognition of BLR38", T3["p_semi"]),
        kc("7 : 4 : 5", T3["p_745"]),
        kc("upstream border of MRC4", T3["p_pos"]),
        kc("just downstream of MRC8A", T3["p_pos"]),
        kc("maximum LOD scores at the same marker positions", T3["p_comap"]),
        kc("corresponding to the reported location of Dm17", T3["p_dm17"]),
        kc("Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31", T3["p_races"]),
        kc("suppress the recognition or response to at least five Bl:24-derived effectors", T3["p_supp"]),
    ],
    "question_issues": "(1) How far the papers compare. Pelgrom et al. cite Giesbers et al., contrast their two "
                       "loci with Giesbers' single loci, list BLN08 among effectors unlinked to Bl:24 resistance, "
                       "and adopt the suppression postulate. Matching BLR38 against each explanation in Giesbers' "
                       "list is this key's own reading: it fits suppression; it is not an instance of \"a second "
                       "unlinked gene is required for resistance\", because both BLR38 loci are needed for "
                       "recognition itself and resistance co-maps with recognition. An answer saying BLR38 "
                       "confirms the second-gene explanation is wrong. An answer linking Pelgrom's sensor and "
                       "helper model to Giesbers' NLR-pair explanation is right if it notes the BLR38 loci are "
                       "unlinked. (2) \"Older\". Giesbers et al. write \"older downy mildew isolates\". The corpus "
                       "does not date Bl:22 to Bl:31, so an answer should not call them older. (3) Dominance. "
                       "Giesbers et al. call "
                       "the BLN08 response dominant but measured a dose effect too: two alleles gave higher "
                       "responses than one in every accession except CGN05310, and in CGN05318 the ranges did not "
                       "overlap (page 8). The difference the papers show is one locus against two loci both "
                       "required, not dominant against semi-dominant. (4) Species differ: BLN08 was mapped in "
                       "L. saligna (CGN05318 and CGN05271 progeny), BLR38 in L. serriola LS102; MRC positions in "
                       "both papers are positions in the L. sativa cv. Salinas reference. (5) Both involve "
                       "chromosome 8 near MRC8A, but Giesbers et al. give a genetic interval (C8, 20 to 33 cM, "
                       "\"may overlap with resistance cluster MRC8A or B\") and Pelgrom et al. a physical one (just "
                       "downstream of MRC8A). Neither paper claims the same locus, and an answer that equates them "
                       "goes beyond the text. (6) BLN08 recognition in L. saligna CGN05947 was absent from its F1 "
                       "and BC1 progeny (page 8), so \"one dominant gene\" holds for CGN05318 and CGN05271 progeny "
                       "only. (7) Giesbers' explanations are written about lack of co-segregation in general; only "
                       "the exclusion of incomplete resistance is tested on BLN08 data.",
    "notes": "Sources: experiments/reuse_demo/text/04_giesbers2017_blr31.pdf.pages.json and "
             "05_pelgrom2019_blr38.pdf.pages.json (pypdf). The Giesbers text layer keeps the 'ﬁ' ligature "
             "(\"signiﬁcantly\", \"identiﬁed\") and prints \"co -segregate\", \"32 –73\" and \"MRC8(A –B)\" with "
             "stray spaces; quotes keep them. Words broken across lines (\"sup-\\npress\", \"resis -\\ntance\") "
             "are joined. Pelgrom's sentence \"It has been postulated previously that B. lactucae expresses "
             "additional effectors that suppress effector recognition or downstream immune signalling "
             "(Giesbers et al., 2017; ...)\" crosses the page 9 to 10 break with figure text between and is not "
             "quoted; evidence \"Race Bl:24 is thought...\" follows it. Paper 03 is not needed and is not cited. "
             "min_core 5.",
    "evidence_check": [],
    "checks": [],
    "disagreements": "",
})

# ---------------------------------------------------------------- PB_004 refutation (paper 1)
E4 = [
    ev(P1, 5, "The F2 populations derived from UC07108 and UC12101 showed a segregation ratio of 9:7, "
              "consistent with two dominant genes being required for resistance.",
       "Refutes \"every 3:1\": two populations segregated 9:7, two dominant genes required."),
    ev(P1, 5, "The population derived from UC07107 had a segregation ratio of 1:3 between resistant and "
              "susceptible individuals, consistent with the presence of a recessive resistance gene.",
       "Refutes \"every dominant\": one recessive resistance, 1:3."),
    ev(P1, 5, "The F2 populations derived from UC02202, UC02204, UC02206, UC07105, UC07106, UC12100, UC12102, "
              "and UC12103 showed a segregation ratio of 3:1 between resistant and susceptible individuals, "
              "consistent with one dominant resistant gene conferring resistance to downy mildew.",
       "The part of the premise that holds: eight populations segregated 3:1."),
    ev(P1, 5, "The F2 population derived from UC07108 was screened for resistance to B. lactucae isolate "
              "C13C1407 rather than C11O1326 because the latter isolate was virulent on UC07108.",
       "The isolate differs for UC07108 (Table 2 prints C13O1407)."),
    ev(P1, 5, "The resistances to C11O1326 present in UC02202, UC02204, UC02206, UC12100, and UC12103 mapped "
              "outside the MRC regions (Fig. 3).",
       "Refutes \"inside an MRC\": five resistances mapped outside the MRCs."),
    ev(P1, 5, "For the resistance genes present in the F2 populations derived from UC07108 and UC12101, which "
              "had segregation ratios of 9:7, the resistances were mapped to MRC2 and MRC4, and MRC1 and "
              "MRC2, respectively.",
       "Where the two-gene resistances map."),
    ev(P1, 5, "The recessive resistance to B. lactucae isolate C11O1326 present in UC07107 was positioned "
              "inside MRC1, while the resistance to the same isolate present in UC07105 and UC12102 was "
              "positioned inside MRC4.",
       "Resistances inside MRCs."),
    ev(P1, 4, "UC07106 C11O1326 90R/44S ~3:1 3.59 1 Dominant C15L1752 96 MRC1 R42",
       "Table 2 row: UC07106, approximately 3:1, one dominant gene, R-gene position MRC1."),
    ev(P1, 8, "For UC07106, a ~ 40 Mb region in MRC1 was significantly associated with resistance to isolate "
              "C11O1326 (Supplementary Fig. 2), although not all the susceptible individuals had a homozygous "
              "susceptible genotype, indicative of incomplete penetrance of this resistance.",
       "UC07106 resistance is in MRC1."),
    ev(P1, 8, "Segregation in the Salinas x UC07106 F2 population deviated from simple Mendelian expected "
              "ratios; however, the closest fit was to a 3:1 segregation ratio, consistent with the presence of "
              "a dominant resistance gene.",
       "UC07106 is 3:1 only as the closest fit."),
    ev(P1, 8, "Therefore, we hypothesize that the resistance gene in line UC07106 is located in a chromosomal "
              "region that is not present in the reference genome.",
       "Caveat on the UC07106 position."),
    ev(P1, 5, "Moreover, we found an additional resistance gene in UC12103 that confers resistance to "
              "C15L1691, which was positioned inside MRC1.",
       "UC12103 has a second resistance gene, inside MRC1."),
    ev(P1, 8, "Two NILs, UC07108 and UC12101, had an F2 segregation ratio that indicates that two dominant genes "
              "are required for the resistance phenotype.",
       "Names the lines the next sentence is about."),
    ev(P1, 8, "The two genes in both lines are genetically unlinked, making it unlikely for them to be NLR "
              "pairs.",
       "The two genes in each 9:7 line are unlinked."),
    ev(P1, 8, "However, the second gene was mapped to Chr2, with only a few markers to support this location.",
       "UC12101's chromosome 2 gene has weak support."),
]
R.append({
    "id": "PB_004",
    "question": "According to the Parra et al. study of eleven near-isogenic lines, every new downy mildew "
                "resistance it mapped segregated 3:1 in F2 as a single dominant Dm gene and mapped inside one of "
                "the major resistance clusters. Is this correct?",
    "category": "out_of_domain",
    "answer_type": "refutation",
    "question_answerable": True,
    "evidence": E4,
    "short_answer": "No, on both counts. Segregation: eight F2 populations (from UC02202, UC02204, UC02206, "
                    "UC07105, UC07106, UC12100, UC12102 and UC12103) fitted 3:1, one dominant gene, UC07106 only "
                    "as the closest fit to a ratio that deviated from simple Mendelian ratios. The populations from "
                    "UC07108 and UC12101 segregated 9:7, consistent with two dominant genes being required for "
                    "resistance; the two genes in each line are genetically unlinked, so the authors think them "
                    "unlikely to be NLR pairs. The population from UC07107 segregated 1:3, consistent with a "
                    "recessive gene. Position: the resistances to isolate C11O1326 in UC02202, UC02204, UC02206, "
                    "UC12100 and UC12103 mapped outside the MRCs. Inside MRCs were UC07107's recessive gene "
                    "(MRC1), UC07106's resistance (MRC1, a region of about 40 Mb; the authors suspect the gene "
                    "itself lies in sequence missing from the reference genome), the resistance of UC07105 and UC12102 (MRC4), the two "
                    "genes of UC07108 (MRC2 and MRC4) and of UC12101 (MRC1 and MRC2, the chromosome 2 gene "
                    "supported by only a few markers), and a second gene in UC12103, for resistance to isolate "
                    "C15L1691 (MRC1). So UC12103 has one resistance outside the MRCs and one inside MRC1. All F2 "
                    "populations were screened with isolate C11O1326 except UC07108's, screened with C13O1407 "
                    "because C11O1326 was virulent on it.",
    "key_concepts": [
        kc("9:7", 0), kc("two dominant genes being required for resistance", 0),
        kc("recessive resistance gene", 1), kc("1:3", 1),
        kc("mapped outside the MRC regions", 4),
        kc("genetically unlinked", 13),
    ],
    "question_issues": "False premise with two parts, both contradicted by paper 01 (Parra et al. 2021, TAG). "
                       "(1) Not all 3:1: two 9:7 populations and one 1:3 population. (2) Not all inside MRCs: five "
                       "resistances to C11O1326 mapped outside. Inconsistencies in the paper: (a) page 5 lists eight "
                       "3:1 populations by name, then says \"From the nine populations with simple Mendelian "
                       "segregation (3:1), six had resistance that mapped to Chr 1, while two populations had "
                       "resistance that mapped to Chr 4\" (six plus two is eight). Table 2 has nine 3:1 rows, "
                       "counting UC12103's second gene (22R/10S), which may be the ninth. The key states eight "
                       "populations, as named. (b) For UC07106 the page 5 prose says only \"a region in Chr 1\"; "
                       "Table 2 and page 8 put it in MRC1. (c) The UC07108 isolate is printed C13C1407 in the text "
                       "and C13O1407 in Table 2. The category follows v2.4, where all ten refutation questions "
                       "carry category out_of_domain.",
    "notes": "Source: experiments/reuse_demo/text/01_parra2021_dm_genes.pdf.pages.json (pypdf). \"F2\" is printed "
             "with a leading space in the text layer (\" F2\"); whitespace is collapsed in the check. Words "
             "broken across lines are joined. Evidence 7 is a Table 2 row as the text layer prints it on page 4 "
             "(columns: line, F2 isolate, R/S counts, ratio, chi-square, genetics, F3 isolate, number "
             "sequenced, R-gene position, Dm gene). The refutation question form follows v2.4 OOD_041 to "
             "OOD_050 (\"According to ... Is this correct?\"). min_core 5.",
    "evidence_check": [],
    "checks": [],
    "disagreements": "",
})

# ---------------------------------------------------------------- PB_005 not answerable
E5 = [
    ev(P4, 5, "The map interval overlaps with the Dm3 region within Major Resistance gene Cluster 2 (MRC2) in "
              "L. sativa cv Salinas (Christopoulou et al., 2015).",
       "Trap 1: the L. saligna gene recognizing BLR31 maps to the Dm3 region of MRC2."),
    ev(P4, 9, "This resistance locus is new for the species L. saligna.",
       "It is the first R gene mapped to this position in L. saligna (see the next sentence)."),
    ev(P4, 9, "All other R genes against B. lactucae that have been mapped in L. saligna are located on C1 "
              "( n = 3) and C9 (n = 1) (Parra et al., 2016).",
       "What \"new for the species\" means: other L. saligna R genes are on C1 and C9."),
    ev(P4, 9, "In L. sativa, MRC2 contains 61 NLR-encoding genes (Christopoulou et al., 2015) and nine known "
              "Dm genes, of which Dm3 is cloned and explained by an NLR gene (Parra et al., 2016).",
       "Dm3 is cloned and is an NLR; no effector is named for it."),
    ev(P3, 2, "Sequencing ofdm3 mutants and transgenic complementation establishedRGC2B a st h eg e n ec o n f e "
              "rring Dm3 (Shen et al. 2002).",
       "Dm3 is RGC2B (text layer spacing as printed)."),
    ev(P5, 2, "Effectors BLG01 (GKLR motif), BLN08 (no RXLR motif) and BLR31 (RXLR motif) were specifically "
              "recognized in multiple L. saligna accessions.",
       "BLR31 carries an RXLR motif and is recognized in L. saligna."),
    ev(P5, 2, "Finally, BLG03 (GKLR motif) is recognized in L. sativa cv. Amplus and UCDM2 that harbour the "
              "resistance gene Dm2.",
       "Trap 2: the only effector tied to a named Dm gene in the corpus is BLG03, with Dm2."),
    ev(P3, 6, "Diana Dm1, Dm3, Dm5/8, Dm7 IM25P11 (Avr3)",
       "Table 2: isolate IM25P11 carries Avr3 and tests Dm3. It names an avirulence phenotype, not a protein."),
    ev(P3, 6, "Ninja Dm3, Dm11, Dm36 AvrB, AvrRpm1, AvrRpt2 CG1 (Avr36)",
       "Trap 3: a line carrying Dm3 gives an HR to three bacterial effectors (column \"HR to Bacterial "
       "Effectors\")."),
    ev(P3, 3, "QGF16M04_LRR_RNAid (chr 1) Lsa039421.1 (88%), RGC1 15/22 RGC1 Dm10 , Dm43, Dm5/8, Dm17, Dm45, "
              "Dm36 AvrB, Avrpm1, AvrRpt2 Dm5/8, Dm45, HR-AvrB, HR-AvrRpm1, HR-AvrRpt2 pGollum",
       "Table 1: those HRs are silenced by a chromosome 1 RGC1 construct, not an RGC2 one."),
]
R.append({
    "id": "PB_005",
    "question": "Which Bremia lactucae effector is recognized by the cloned Dm3 resistance protein (RGC2B), and "
                "does it carry an RXLR motif?",
    "category": "out_of_domain",
    "answer_type": "not_answerable",
    "question_answerable": False,
    "evidence": E5,
    "short_answer": "Not answerable from the five papers. They say Dm3 is RGC2B, an NLR gene in MRC2 on "
                    "chromosome 2, and test Dm3 with isolate IM25P11, listed as carrying Avr3, but no paper names "
                    "the effector protein that Dm3 recognizes or describes its motifs.",
    "key_concepts": [],
    "question_issues": "Plausible for the topic (a standard question about the best-studied Dm gene) and in the "
                       "corpus's domain, but none of the five papers answers it. Searched, case-insensitive, over "
                       "the page text of all five papers: \"Dm3\" (papers 02, 03, 04: cluster membership, cloning "
                       "as RGC2B, RNAi abrogation, the Dm3 region of MRC2, the BLR31 map interval), \"Avr3\" (paper "
                       "03 Table 2, isolate IM25P11 only; paper 02 hits are Avr36, Avr37, Avr38), \"RGC2B\" and "
                       "\"RGC2DB\" (paper 03 only, no effector), \"RXLR\", \"avirulen\" (paper 02: isolate "
                       "phenotypes; paper 04: BLR31 as a candidate avirulence effector of its own L. saligna R "
                       "gene), \"cognate\" (paper 04, BLR31 and its L. saligna R gene), \"recognized in\" and "
                       "\"recognized by\", \"BLG0\" (BLG01, BLG03; BLG03 with Dm2), \"Dm2\". Three traps. (1) BLR31 "
                       "(RXLR) is recognized by an L. saligna gene on C2 in the Dm3 region of MRC2. The paper calls "
                       "the locus new for L. saligna (the first R gene mapped there in that species) and says it "
                       "may be an NLR gene; the corpus neither identifies this gene with Dm3 nor tests BLR31 "
                       "against Dm3 or RGC2B. (2) BLG03 goes with Dm2, not Dm3. (3) Cv. Ninja carries Dm3, Dm11 and "
                       "Dm36 and gives an HR to AvrB, AvrRpm1 and AvrRpt2, which are bacterial effectors (paper 03 "
                       "Table 2 column \"HR to Bacterial Effectors\"; Table 1 shows these HRs silenced by a "
                       "chromosome 1 RGC1 construct). Paper 04's germplasm included \"a differential set of "
                       "L. sativa cultivars with single dominant R genes\" and BLR31 triggered an HR only in "
                       "L. saligna accessions, which suggests but does not show that Dm3 lines do not recognize "
                       "BLR31 (Table S1, which would show it, is not in the corpus). The expert reviewer searched "
                       "the published literature twice and found no source naming Dm3's B. lactucae effector; two "
                       "searches cannot prove there is none. The v2.4 category for not-answerable questions is "
                       "out_of_domain.",
    "notes": "Sources: page text of papers 03, 04 and 05 in experiments/reuse_demo/text/ (pypdf). Evidence 4 keeps "
             "the text layer's broken spacing (\"establishedRGC2B a st h eg e n ec o n f e rring\"; \"confer-\" "
             "is joined across the line). Evidence 7 and 8 are Table 2 rows as printed on page 6 (columns: line, "
             "resistance specificity, HR to bacterial effectors, isolates tested with relevant Avr); evidence 9 "
             "is a Table 1 row on page 3. Key concepts are empty, as for every not-answerable record in v2.4. "
             "min_core is null, as for v2.4's not-answerable questions in the v1 form.",
    "evidence_check": [],
    "checks": [],
    "disagreements": "",
})

# ---------------------------------------------------------------- checks and support
FILES = {P1: "01_parra2021_dm_genes.pdf", P2: "02_simko2013_qtl.pdf", P3: "03_christopoulou2015_mrc.pdf",
         P4: "04_giesbers2017_blr31.pdf", P5: "05_pelgrom2019_blr38.pdf"}
bad = []
for r in R:
    for e in r["evidence"]:
        e.pop("_tag", None)
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
    r["min_core"] = 5 if r["question_answerable"] else None
    blob = json.dumps(r, ensure_ascii=False)
    if chr(0x2014) in blob:
        bad.append(f"{r['id']}: em dash")
    for m in re.finditer(r"\[([0-9, ]+)\]", r.get("synthesis_statement", "")):
        for n in m.group(1).split(","):
            if int(n) >= len(r["evidence"]):
                bad.append(f"{r['id']}: synthesis reference {n} out of range")
if bad:
    print("\n".join(bad))
    sys.exit(1)

ORDER = ["id", "question_answerable", "question_issues", "answer_type", "evidence", "short_answer", "key_concepts",
         "notes", "question", "category", "evidence_check", "checks", "disagreements", "synthesis_statement",
         "support", "min_core"]
recs = [{k: r[k] for k in ORDER if k in r} for r in R]
out = {
    "version": "PB draft 3",
    "status": "draft 3, the content signed off as key_v1.json (D75). D74: drafted by Claude, signed off by Valerio",
    "drafted": "2026-10-16",
    "revision": "draft 3: D75 (Q53 to Q55 as recommended; Q54 drops the outside-the-corpus race dates from PB_003 "
                "note (2)); draft 2: findings of the quote, answerability and expert reviews applied (PB_001 to "
                "PB_005)",
    "format": {"file": "data/ground_truth_v2/all_v2_4.json",
               "sha256": hashlib.sha256(V24.read_bytes()).hexdigest(), "version": "2.4"},
    "added_fields": {
        "support": "per evidence item: {paper: PDF filename, page: 1-based page in the text file, quote: the "
                   "evidence sentence verbatim}; the same items as evidence, in the form the task asked for",
        "min_core": "the v1 field (ground_truth_v2_4_as_v1.json): the smallest core size whose index holds the "
                    "source papers; 5 for every answerable question here (one corpus of five), null for the "
                    "not-answerable one",
        "disagreements": "empty: one drafter, no A/B reconciliation (v2.4 records were reconciled from two drafts)",
    },
    "corpus": {"manifest": "experiments/reuse_demo/corpus_papers.csv",
               "text": "experiments/reuse_demo/text/<filename>.pages.json (pypdf, one string per page)"},
    "evidence_check_rule": "\"exact\": the sentence occurs on that page once whitespace is collapsed and a word "
                           "broken across a line by a hyphen is joined or keeps its hyphen",
    "records": recs,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("wrote", OUT, len(recs), "records;", sum(len(r["evidence"]) for r in recs), "evidence items, all exact")
v1 = dict(out)
v1["version"] = "PB v1"
v1["status"] = "signed off by Valerio Bianchi, 16 October 2026 (D75)"
v1["signed_off"] = {"by": "Valerio Bianchi", "date": "2026-10-16", "decision": "D75",
                    "cards": "Q53 (BLR38 fits suppression only), Q54 (PB_003 note (2) keeps the corpus part, drops "
                             "the outside date), Q55 (PB_004 states eight 3:1 populations), each as recommended on "
                             "experiments/fix_design/decisions_round3.html"}
v1 = {k: v1[k] for k in ["version", "status", "signed_off", *[k for k in out if k not in ("version", "status")]]}
OUT_V1.write_text(json.dumps(v1, ensure_ascii=False, indent=1))
print("wrote", OUT_V1, "same records, header:", v1["status"])
