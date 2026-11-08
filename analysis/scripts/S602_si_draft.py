"""S602: build the combined Supplementary Information (editor rows 23 and 24: one combined SI PDF), and a .docx of it.

Two steps.

  extract MD TXT   reads the agreed manuscript tab's export (markdown and plain text of the same revision), checks that every
                   Supplementary paragraph of the markdown equals the plain text once markup is removed, and writes
                   resubmission/06_supplementary/si_text_from_doc_20261107.md: the Supplementary Items the main text and
                   Methods cite, the Supplementary Figure legends and Supplementary Notes 1 to 8, verbatim. It also lists the
                   figures whose legend differs from the plate folder's legend_draft.md (the doc text wins).
  build            (default) reads that committed file and writes
                   resubmission/06_supplementary/Supplementary_Information.pdf and
                   resubmission/06_supplementary/Supplementary_Information.docx (named so on 8 Nov, D305; was
                   Supplementary_Information_20261107.docx):
                   an overview with contents, Supplementary Notes 1 to 8 (each from a fresh page), Supplementary Figures 1 to
                   18 (each plate at full size from its D302 folder, its legend below it or on the next page), Supplementary
                   Tables 1 to 3 rendered from findings/figures_provisional/supp_tables/*.md on landscape pages, and the
                   Supplementary Data 1 to 8 listed as separate files with captions in the agreed text's own words. Then it
                   checks: every cited Supplementary item is in both files, every data row of every Supplementary Table .md
                   is in the PDF text, fonts embedded and none Type 3, no soft hyphen (U+00AD) and no font outside Arial and
                   the plates' own in the PDF, no em dash, every legend under 350 words. Exit 1 on any failed check.

Usage: uv run python scripts/S602_si_draft.py [build]
       uv run python scripts/S602_si_draft.py extract <manuscript.md> <manuscript.txt>
The text font is Arial from /System/Library/Fonts/Supplemental (macOS), embedded in the PDF. MuPDF's Story does not split a
table across pages (it draws past the page's foot), so tables are paginated here row by row, the header repeated on every
page. Arial maps one glyph to both U+002D and U+00AD and MuPDF's ToUnicode picks U+00AD, so the hyphen's ToUnicode entry is
rewritten to U+002D after saving (likewise no-break space and Greek question
mark to space and semicolon). Superscript characters Arial lacks (10\u207b\u2077) are set as <sup> in Arial's own glyphs.
"""
import glob
import hashlib
import html
import io
import os
import re
import sys

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP = os.path.join(ROOT, "findings/figures_provisional")
OUTDIR = os.path.join(ROOT, "resubmission/06_supplementary")
SI_TEXT = os.path.join(OUTDIR, "si_text_from_doc_20261107.md")
OUT_PDF = os.path.join(OUTDIR, "Supplementary_Information.pdf")
OUT_DOCX = os.path.join(OUTDIR, "Supplementary_Information.docx")   # D305 (8 Nov): was Supplementary_Information_20261107.docx
FONT_DIR = "/System/Library/Fonts/Supplemental"
FONTS = {"regular": "Arial.ttf", "bold": "Arial Bold.ttf", "italic": "Arial Italic.ttf", "bolditalic": "Arial Bold Italic.ttf"}
N_FIGS, N_NOTES, N_TABLES = 18, 8, 3
LEGEND_WORDS_UNDER = 350   # FIGURE_LOCK.toml [legend] words_under
EM_DASH = "\u2014"

A4 = fitz.paper_rect("a4")
A4L = fitz.Rect(0, 0, A4.height, A4.width)
M = 34.0  # 12 mm margin, so a 183 mm plate sits at full size
CONTENT_W = A4.width - 2 * M


def font_css(size=9):
    faces = "".join(
        f'@font-face {{font-family: A; src: url("{f}"); {"font-weight: bold;" if "bold" in k else ""} {"font-style: italic;" if "italic" in k else ""}}}'
        for k, f in FONTS.items())
    return faces + (
        f"* {{font-family: A; font-size: {size}pt; line-height: 1.3;}} p {{margin: 0 0 5pt 0;}} "
        "h1 {font-size: 14pt; margin: 0 0 8pt 0;} h2 {font-size: 11pt; margin: 10pt 0 5pt 0;} "
        "h3 {font-size: 10pt; margin: 8pt 0 4pt 0;} "
        f"td, th {{font-size: {size}pt; padding: 1.5pt 4pt 1.5pt 0; vertical-align: top; text-align: left;}} "
        "th {font-weight: bold;}")


# ---------------------------------------------------------------------------------------------------------------- text
def plain(s):
    """Markdown of the tab's export to its plain text: drop bold/italic markers and backslash escapes."""
    s = html.unescape(s)
    s = s.replace("**", "")
    s = re.sub(r"\\([\[\]_*#|\\])", r"\1", s)
    return s


SUPER = dict(zip("\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b", "0123456789+\u2212"))
SUPER_MISSING = set("\u2070\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b")   # superscripts Arial has no glyph for


def sup_html(s):
    """A run of superscript characters that Arial lacks, as <sup> of Arial's digits and minus sign (U+2212)."""
    return re.sub("[" + "".join(SUPER) + "]+",
                  lambda m: f"<sup>{''.join(SUPER[c] for c in m.group(0))}</sup>" if set(m.group(0)) & SUPER_MISSING else m.group(0), s)


def md_inline(s):
    """Inline markdown (bold, italic, escapes) to HTML."""
    return sup_html(_md_inline(s))


def _md_inline(s):
    s = html.unescape(s)
    s = re.sub(r"\\([\[\]_*#|\\])", lambda m: f"\x00{ord(m.group(1))}\x00", s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: html.escape(chr(int(m.group(1)))), s)


def runs(s):
    """Inline markdown to (text, bold, italic) runs, for the .docx."""
    s = html.unescape(s)
    s = re.sub(r"\\([\[\]_*#|\\])", lambda m: f"\x00{ord(m.group(1))}\x00", s)
    out = []
    for i, part in enumerate(re.split(r"\*\*", s)):
        for j, sub in enumerate(re.split(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", part)):
            if sub:
                out.append((re.sub(r"\x00(\d+)\x00", lambda m: chr(int(m.group(1))), sub), i % 2 == 1, j % 2 == 1))
    return out


CITE_RE = re.compile(r"Supplementary (Figs?\.|Figures?|Tables?|Notes?|Data)\s+((?:\d+[a-z]*(?:\s*,\s*|\s+to\s+|\s+and\s+|\s*[\u2013-]\s*)?)+)")
KIND = {"Fig": "Figure", "Figs": "Figure", "Figure": "Figure", "Figures": "Figure", "Table": "Table", "Tables": "Table",
        "Note": "Note", "Notes": "Note", "Data": "Data"}


def cited_items(text):
    items = set()
    for m in CITE_RE.finditer(text):
        kind = KIND[m.group(1).rstrip(".")]
        g = m.group(2)
        for a, b in re.findall(r"(\d+)[a-z]*\s*(?:to|\u2013|-)\s*(\d+)", g):
            items.update((kind, n) for n in range(int(a), int(b) + 1))
        items.update((kind, int(n)) for n in re.findall(r"\d+", g))
    return sorted(items)


def extract(md_path, txt_path):
    md = open(md_path, encoding="utf-8").read().split("\n")
    txt = open(txt_path, encoding="utf-8").read().split("\n")
    assert len(md) == len(txt), (len(md), len(txt))
    ref = [i for i, l in enumerate(md) if l.strip() == "## References"]
    leg = [i for i, l in enumerate(md) if l.strip().lower() == "## supplementary figure legends"]
    assert len(ref) == 1 and len(leg) == 1, (ref, leg)
    for i in range(leg[0], len(md)):                                    # md equals txt line by line in the SI part
        a, b = plain(md[i]).lstrip("#").strip(), txt[i].strip()
        assert a == b, f"line {i + 1}: markdown and plain text differ\n{a[:200]}\n{b[:200]}"
    main_text = "\n".join(plain(l) for l in md[:ref[0]])
    cited = cited_items(main_text)
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    out = ["# Supplementary Information text, from the manuscript tab", "",
           f"Extracted by scripts/S602_si_draft.py extract from the tab's export at revision 3688 (7 November 2026): "
           f"{os.path.basename(md_path)} sha256 {sha(md_path)}, {os.path.basename(txt_path)} sha256 {sha(txt_path)}. "
           "Every paragraph below is the tab's markdown, verbatim, from its 'Supplementary figure legends' heading to its "
           "end; each equals the plain-text export once markup is removed. S602 build reads this file.", "",
           "## Cited in the main text and Methods", ""]
    out += [f"- Supplementary {k} {n}" for k, n in cited]
    out += [""] + [l for l in md[leg[0]:]]
    while out[-1] == "":
        out.pop()
    os.makedirs(OUTDIR, exist_ok=True)
    open(SI_TEXT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", os.path.relpath(SI_TEXT, ROOT))
    print("cited:", ", ".join(f"{k} {n}" for k, n in cited))
    # the doc's legends against the plate folders' legend_draft.md
    si = read_si()
    differ = []
    for n in range(1, N_FIGS + 1):
        lines = open(os.path.join(folder(n), "legend_draft.md"), encoding="utf-8").read().split("\n")
        st = [i for i, l in enumerate(lines) if l.startswith(f"**Supplementary Figure {n} |")]
        draft = " ".join(p.strip() for p in "\n".join(lines[st[0]:]).split("\n\n") if p.strip()) if st else ""
        norm = lambda s: re.sub(r"\s+", " ", plain(s)).strip()
        if norm(draft) != norm(si["legends"][n]):
            differ.append(n)
    print("legends differing from legend_draft.md (doc text used):", differ or "none")


def read_si():
    lines = open(SI_TEXT, encoding="utf-8").read().split("\n")
    cited, legends, notes, sec = [], {}, {}, None
    for l in lines:
        if l.startswith("## "):
            h = l[3:].strip()
            m = re.match(r"Supplementary Note (\d+) \| (.+)", h)
            sec = ("note", int(m.group(1)), m.group(2)) if m else h.lower()
            if m:
                notes[int(m.group(1))] = (m.group(2), [])
            continue
        if not l.strip():
            continue
        if sec == "cited in the main text and methods":
            m = re.match(r"- Supplementary (\w+) (\d+)$", l)
            cited.append((m.group(1), int(m.group(2))))
        elif sec == "supplementary figure legends":
            m = re.match(r"\*\*Supplementary Figure (\d+) \|", l)
            assert m and int(m.group(1)) not in legends, l[:80]
            legends[int(m.group(1))] = l.strip()
        elif isinstance(sec, tuple):
            notes[sec[1]][1].append(l.strip())
    assert sorted(legends) == list(range(1, N_FIGS + 1)), sorted(legends)
    assert sorted(notes) == list(range(1, N_NOTES + 1)), sorted(notes)
    return {"cited": cited, "legends": legends, "notes": notes}


def legend_title(md_legend, n):
    t = plain(md_legend)
    m = re.match(rf"Supplementary Figure {n} \| (.+?)\.(?:\s|$)", t)
    return m.group(1).strip()


# -------------------------------------------------------------------------------------------------------------- inputs
def folder(n):
    hits = [d for d in glob.glob(os.path.join(FP, f"supp_fig{n}*")) if re.fullmatch(rf"supp_fig{n}(_.*)?", os.path.basename(d))]
    assert len(hits) == 1, (n, hits)
    return hits[0]


def plate(n, ext="pdf"):
    hits = [p for p in glob.glob(os.path.join(folder(n), f"Supplementary Figure {n}*.{ext}")) if " data" not in os.path.basename(p)]
    assert len(hits) == 1, (n, ext, hits)
    return hits[0]


def read_table(n):
    """A Supplementary Table's .md as blocks: ('h', level, text), ('p', text), ('t', header, rows). Title from its first
    '# Supplementary Table N | title' line, else from the workbook's first sheet."""
    md = os.path.join(FP, "supp_tables", f"Supplementary Table {n}.md")
    xl = os.path.join(FP, "supp_tables", f"Supplementary Table {n}.xlsx")
    assert os.path.exists(md) and os.path.exists(xl), n
    lines = open(md, encoding="utf-8").read().split("\n")
    title, blocks, i = None, [], 0
    m = re.match(rf"# Supplementary Table {n} \| (.+)", lines[0].strip())
    if m:
        title, i = m.group(1).strip(), 1
    else:
        import openpyxl
        title = openpyxl.load_workbook(xl, read_only=True).sheetnames[0]
    split = lambda l: [c.strip() for c in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
    while i < len(lines):
        l = lines[i]
        if l.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].startswith("|"):
                tbl.append(lines[i]); i += 1
            assert re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", tbl[1].replace(" ", "")), (n, tbl[1])
            blocks.append(("t", split(tbl[0]), [split(r) for r in tbl[2:]]))
            continue
        if l.startswith("#"):
            blocks.append(("h", len(l) - len(l.lstrip("#")), l.lstrip("#").strip()))
        elif l.strip():
            blocks.append(("p", l.strip()))
        i += 1
    return title, blocks


def data_items():
    """Supplementary Data 1 to 8, each with a caption in the agreed text's own words (Data availability; Note 1)."""
    assert os.path.exists(os.path.join(FP, "supp_data1_answer_key", "Supplementary Data 1.xlsx"))
    items = [("Supplementary Data 1", "The answer key",
              "Every question with its category, its source papers and their area; the expert-curated questions, "
              "ground-truth answers, validation results and per-question metadata.")]
    # D283 folders: Figure 4 is fig4_depth, Figure 5 fig4, Figure 6 fig5, Figure 7 fig6; Source Data of Figure n is Data n + 1
    for n, f in enumerate(["fig1", "fig2_human", "fig3_strategies", "fig4_depth", "fig4", "fig5", "fig6"], 1):
        wb = glob.glob(os.path.join(FP, f, f"Source Data Fig. {n}*.xlsx"))
        assert len(wb) == 1, (n, f, wb)
        items.append((f"Supplementary Data {n + 1}", f"Source Data for Figure {n}", "One sheet per panel."))
    return items


# ----------------------------------------------------------------------------------------------------------------- PDF
ARCH = fitz.Archive(FONT_DIR)


def story_pages(html_s, page_rect, size=9):
    story = fitz.Story(html=html_s, user_css=font_css(size), archive=ARCH)
    buf = io.BytesIO()
    w = fitz.DocumentWriter(buf)
    content = content_rect(page_rect)
    more = 1
    while more:
        dev = w.begin_page(page_rect)
        more, filled = story.place(content)
        assert filled[3] <= content.y1 + 0.5, f"content drawn past the foot of the page ({filled[3]:.1f} > {content.y1:.1f}): {html_s[:80]}"
        story.draw(dev)
        w.end_page()
    w.close()
    return fitz.open("pdf", buf.getvalue())


def content_rect(page_rect):
    return fitz.Rect(M, M, page_rect.width - M, page_rect.height - M - 14)


def units_html(units):
    """Units to HTML: ('x', html, keep_with_next) as is; consecutive ('r', table_id, header_html, row_html) rows of one table
    as one <table>, its header first."""
    h, i = "", 0
    while i < len(units):
        u = units[i]
        if u[0] == "x":
            h += u[1]; i += 1
            continue
        h += f"<table><tr>{u[2]}</tr>"
        while i < len(units) and units[i][0] == "r" and units[i][1] == u[1]:
            h += f"<tr>{units[i][3]}</tr>"; i += 1
        h += "</table>"
    return h


def fits(units, page_rect, size):
    content = content_rect(page_rect)
    more, filled = fitz.Story(html=units_html(units), user_css=font_css(size), archive=ARCH).place(content)
    return not more and filled[3] <= content.y1 + 0.5


def paginate(units, page_rect, size=9):
    """Greedy pagination of units (see units_html): a page takes units while they fit; a table split across pages repeats
    its header on each; a heading (keep_with_next) left last on a page moves to the next. A unit too tall for an empty page
    fails the build."""
    pages, cur = [], []
    for u in units:
        if fits(cur + [u], page_rect, size):
            cur.append(u)
            continue
        carry = []
        while cur and cur[-1][0] == "x" and cur[-1][2]:
            carry.insert(0, cur.pop())
        if cur:
            pages.append(cur)
        cur = carry + [u]
        assert fits(cur, page_rect, size), f"a unit does not fit an empty page: {units_html([u])[:120]}"
    if cur:
        pages.append(cur)
    buf = io.BytesIO()
    w = fitz.DocumentWriter(buf)
    for pu in pages:
        story = fitz.Story(html=units_html(pu), user_css=font_css(size), archive=ARCH)
        dev = w.begin_page(page_rect)
        story.place(content_rect(page_rect))
        story.draw(dev)
        w.end_page()
    w.close()
    return fitz.open("pdf", buf.getvalue())


def note_html(n, title, paras):
    return f"<h2>Supplementary Note {n} | {html.escape(title)}</h2>" + "".join(f"<p>{md_inline(p)}</p>" for p in paras)


def table_units(n, title, blocks):
    u = [("x", f"<h2>Supplementary Table {n} | {html.escape(title)}</h2>", True)]
    for k, b in enumerate(blocks):
        if b[0] == "h":
            u.append(("x", f"<h3>{md_inline(b[2])}</h3>", True))
        elif b[0] == "p":
            u.append(("x", f"<p>{md_inline(b[1])}</p>", False))
        else:
            head = "".join(f"<th>{md_inline(c)}</th>" for c in b[1])
            u += [("r", (n, k), head, "".join(f"<td>{md_inline(c)}</td>" for c in r)) for r in b[2]]
    return u


def contents_units(si, start, tables, data):
    row = lambda t, p: ("r", "contents", "<th>Item</th><th>Page</th>", f"<td>{html.escape(t)}</td><td>{p}</td>")
    u = [("x", "<h1>Supplementary Information</h1>"
               "<p><b>Systematic ablation of a multi-agent language model system for life sciences research</b></p>"
               "<p>Valerio Bianchi and Dirkjan Schokker</p>"
               "<p>This file holds Supplementary Notes 1 to 8, Supplementary Figures 1 to 18 and Supplementary Tables 1 to 3. "
               "Supplementary Data 1 to 8 are supplied as separate files, listed after the contents.</p>", False),
         ("x", "<h2>Contents</h2>", True)]
    u += [row(f"Supplementary Note {n} | {si['notes'][n][0]}", start[("Note", n)]) for n in range(1, N_NOTES + 1)]
    u += [row(f"Supplementary Figure {n} | {legend_title(si['legends'][n], n)}", start[("Figure", n)]) for n in range(1, N_FIGS + 1)]
    u += [row(f"Supplementary Table {n} | {tables[n][0]}", start[("Table", n)]) for n in range(1, N_TABLES + 1)]
    u.append(("x", "<h2>Supplementary Data (supplied as separate files)</h2>", True))
    u += [("x", f"<p><b>{html.escape(a)} | {html.escape(b)}.</b> {html.escape(c)}</p>", False) for a, b, c in data]
    return u


def build_pdf(si, tables, data):
    parts, start, figinfo = [], {}, []
    for n in range(1, N_NOTES + 1):
        parts.append((("Note", n), story_pages(note_html(n, *si["notes"][n]), A4)))
    for n in range(1, N_FIGS + 1):
        doc = fitz.open()
        src = fitz.open(plate(n))
        assert src.page_count == 1, (n, src.page_count)
        r = src[0].rect
        scale = min(1.0, CONTENT_W / r.width, (A4.height - 2 * M - 20) / r.height)
        w, h = r.width * scale, r.height * scale
        page = doc.new_page(width=A4.width, height=A4.height)
        page.show_pdf_page(fitz.Rect(M, M, M + w, M + h), src, 0)
        leg = f"<p>{md_inline(si['legends'][n])}</p>"
        box = fitz.Rect(M, M + h + 12, A4.width - M, A4.height - M - 14)
        spare = page.insert_htmlbox(box, leg, css=font_css(), archive=ARCH, scale_low=1)[0] if box.height > 40 else -1
        placed = "below"
        if spare < 0:
            p2 = doc.new_page(width=A4.width, height=A4.height)
            spare = p2.insert_htmlbox(fitz.Rect(M, M, A4.width - M, A4.height - M - 14), leg, css=font_css(), archive=ARCH, scale_low=1)[0]
            assert spare >= 0, f"legend of Supplementary Figure {n} does not fit one page"
            placed = "next page"
        figinfo.append((n, placed, scale, os.path.relpath(plate(n), ROOT)))
        src.close()
        parts.append((("Figure", n), doc))
    for n in range(1, N_TABLES + 1):
        parts.append((("Table", n), paginate(table_units(n, *tables[n]), A4L, size=8)))
    # contents: once with placeholder pages to learn its length, then with the real ones
    k = paginate(contents_units(si, {key: 999 for key, _ in parts}, tables, data), A4).page_count
    p = k + 1
    for key, d in parts:
        start[key] = p
        p += d.page_count
    toc = paginate(contents_units(si, start, tables, data), A4)
    assert toc.page_count == k
    out = fitz.open()
    out.insert_pdf(toc)
    for _, d in parts:
        out.insert_pdf(d)
    for i, pg in enumerate(out, 1):
        pg.insert_font(fontname="arial", fontfile=os.path.join(FONT_DIR, FONTS["regular"]))
        x = M if pg.rect.width < pg.rect.height else M
        pg.insert_text((x, pg.rect.height - M + 10), f"Supplementary Information, page {i} of {out.page_count}", fontname="arial", fontsize=8)
    out.set_metadata({"title": "Supplementary Information", "author": "Valerio Bianchi, Dirkjan Schokker",
                      "creator": "scripts/S602_si_draft.py (PyMuPDF)", "producer": "PyMuPDF"})
    out.subset_fonts()
    out.save(OUT_PDF, garbage=4, deflate=True)
    pages = out.page_count
    out.close()
    fix_soft_hyphens(OUT_PDF)
    return start, figinfo, pages


ALIAS = {0x00AD: 0x002D, 0x00A0: 0x0020, 0x037E: 0x003B}   # one Arial glyph, two code points: soft hyphen, no-break space,
                                                            # Greek question mark; the text uses the ASCII one


def read_cmap(cm):
    """A ToUnicode CMap's bfchar and bfrange entries as {code: unicode string}."""
    u16 = lambda h: bytes.fromhex(h).decode("utf-16-be")
    out = {}
    for block in re.findall(r"beginbfchar(.*?)endbfchar", cm, flags=re.S):
        for a, b in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            out[int(a, 16)] = u16(b)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", cm, flags=re.S):
        for a, b, rest in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])", block):
            lo, hi = int(a, 16), int(b, 16)
            if rest.startswith("["):
                for k, h in enumerate(re.findall(r"<([0-9A-Fa-f]+)>", rest)):
                    out[lo + k] = u16(h)
            else:
                start = bytes.fromhex(rest[1:-1])
                for k in range(hi - lo + 1):
                    v = bytearray(start)
                    v[-2:] = (int.from_bytes(start[-2:], "big") + k).to_bytes(2, "big")
                    out[lo + k] = v.decode("utf-16-be")
    return out


def write_cmap(m):
    h = ("/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
         "/CIDSystemInfo <</Registry(Adobe)/Ordering(UCS)/Supplement 0>> def\n/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n"
         "1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n")
    items = sorted(m.items())
    for k in range(0, len(items), 100):
        chunk = items[k:k + 100]
        h += f"{len(chunk)} beginbfchar\n" + "".join(f"<{c:04X}> <{u.encode('utf-16-be').hex().upper()}>\n" for c, u in chunk) + "endbfchar\n"
    return h + "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n"


def fix_soft_hyphens(path):
    """In every Arial font's ToUnicode, map the code points of ALIAS to the ASCII ones the text uses (MuPDF picks the
    soft hyphen, the no-break space and the Greek question mark for Arial's hyphen, space and semicolon glyphs)."""
    doc = fitz.open(path)
    n = 0
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "ToUnicode")[0] != "xref" or "Arial" not in doc.xref_get_key(xref, "BaseFont")[1]:
            continue
        tu = int(doc.xref_get_key(xref, "ToUnicode")[1].split()[0])
        m = read_cmap(doc.xref_stream(tu).decode("latin-1"))
        fixed = {c: "".join(chr(ALIAS.get(ord(ch), ord(ch))) for ch in u) for c, u in m.items()}
        n += sum(fixed[c] != m[c] for c in m)
        doc.update_stream(tu, write_cmap(fixed).encode("latin-1"))
    doc.save(path + ".tmp", garbage=4, deflate=True)
    doc.close()
    os.replace(path + ".tmp", path)
    print(f"ToUnicode: {n} Arial codes remapped to ASCII (soft hyphen, no-break space, Greek question mark)")


# ---------------------------------------------------------------------------------------------------------------- DOCX
def build_docx(si, tables, data):
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.text import WD_BREAK
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt

    d = Document()
    for st in ("Normal", "Heading 1", "Heading 2", "Heading 3", "Title"):
        s = d.styles[st]
        s.font.name = "Arial"
        s.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        s.font.color.rgb = None
    d.styles["Normal"].font.size = Pt(9)
    for st, sz in (("Title", 16), ("Heading 1", 14), ("Heading 2", 11), ("Heading 3", 10)):
        d.styles[st].font.size = Pt(sz)
    sec = d.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Mm(12))

    def para(md_s, size=None, style=None):
        p = d.add_paragraph(style=style)
        for t, b, it in runs(md_s):
            r = p.add_run(t)
            r.bold, r.italic = b or None, it or None
            if size:
                r.font.size = Pt(size)
        return p

    d.add_heading("Supplementary Information", level=0)
    para("**Systematic ablation of a multi-agent language model system for life sciences research**")
    para("Valerio Bianchi and Dirkjan Schokker")
    para("This file holds Supplementary Notes 1 to 8, Supplementary Figures 1 to 18 and Supplementary Tables 1 to 3. "
         "Supplementary Data 1 to 8 are supplied as separate files, listed below.")
    d.add_heading("Contents", level=1)
    for n in range(1, N_NOTES + 1):
        d.add_paragraph(f"Supplementary Note {n} | {si['notes'][n][0]}")
    for n in range(1, N_FIGS + 1):
        d.add_paragraph(f"Supplementary Figure {n} | {legend_title(si['legends'][n], n)}")
    for n in range(1, N_TABLES + 1):
        d.add_paragraph(f"Supplementary Table {n} | {tables[n][0]}")
    d.add_heading("Supplementary Data (supplied as separate files)", level=1)
    for a, b, c in data:
        para(f"**{a} | {b}.** {c}")

    def new_page():
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    for n in range(1, N_NOTES + 1):
        new_page()
        title, paras = si["notes"][n]
        d.add_heading(f"Supplementary Note {n} | {title}", level=1)
        for p in paras:
            para(p)
    for n in range(1, N_FIGS + 1):
        new_page()
        r = fitz.open(plate(n))[0].rect
        w_mm = r.width * 25.4 / 72
        d.add_paragraph().add_run().add_picture(plate(n, "png"), width=Mm(min(w_mm, 186)))
        para(si["legends"][n])
    sec = d.add_section()
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Mm(297), Mm(210)
    first = True
    for n in range(1, N_TABLES + 1):
        if not first:
            new_page()
        first = False
        title, blocks = tables[n]
        d.add_heading(f"Supplementary Table {n} | {title}", level=1)
        for b in blocks:
            if b[0] == "h":
                d.add_heading(plain(b[2]), level=2)
            elif b[0] == "p":
                para(b[1])
            else:
                t = d.add_table(rows=1 + len(b[2]), cols=len(b[1]))
                t.style = "Table Grid"
                for j, row in enumerate([b[1]] + b[2]):
                    for c, txt in enumerate(row):
                        cell = t.cell(j, c)
                        cell.paragraphs[0].text = ""
                        for tx, bo, it in runs(txt):
                            rr = cell.paragraphs[0].add_run(tx)
                            rr.font.size = Pt(7)
                            rr.bold = True if j == 0 else (bo or None)
                            rr.italic = it or None
    d.core_properties.title = "Supplementary Information"
    d.core_properties.author = "Valerio Bianchi, Dirkjan Schokker"
    d.save(OUT_DOCX)


# -------------------------------------------------------------------------------------------------------------- checks
def check(si, tables, start, pages):
    from docx import Document
    fails = []
    pdf = fitz.open(OUT_PDF)
    text = "\n".join(p.get_text() for p in pdf)
    flat = re.sub(r"\s+", " ", text)
    dx = Document(OUT_DOCX)
    dtext = "\n".join([p.text for p in dx.paragraphs] + [c.text for t in dx.tables for row in t.rows for c in row.cells])
    heads = {"Figure": "Supplementary Figure {} |", "Note": "Supplementary Note {} |", "Table": "Supplementary Table {} |", "Data": "Supplementary Data {} |"}
    have = {("Note", n) for n in range(1, N_NOTES + 1)} | {("Figure", n) for n in range(1, N_FIGS + 1)} | \
           {("Table", n) for n in range(1, N_TABLES + 1)} | {("Data", n) for n in range(1, 9)}
    for kind, n in si["cited"]:
        key = (kind, n)
        if key not in have:
            fails.append(f"cited Supplementary {kind} {n} has no item in the SI")
            continue
        h = heads[kind].format(n)
        if kind in start:
            pass
        page_ok = kind == "Data" or h in re.sub(r"\s+", " ", pdf[start[key] - 1].get_text() + (pdf[start[key]].get_text() if start[key] < pages else ""))
        if not page_ok or h not in flat or h not in dtext:
            fails.append(f"Supplementary {kind} {n}: heading not found on its page in the PDF or in the .docx")
    nfig_plates = sum(1 for p in pdf if p.get_images() or p.get_drawings())
    print(f"cited items: {len(si['cited'])}, each found in the PDF and the .docx" if not fails else "cited items: FAILURES")
    # every data row of every Supplementary Table .md in the PDF text, cell by cell, in order
    norm = lambda s: re.sub(r"\s+", "", s.replace("\u2212", "-"))
    ntext = norm(text)
    for n in range(1, N_TABLES + 1):
        rows = [r for b in tables[n][1] if b[0] == "t" for r in b[2]]
        missing = [r[0] for r in rows if not re.search(".*?".join(re.escape(norm(plain(c).replace("`", ""))) for c in r if c), ntext, flags=re.S)]
        if missing:
            fails.append(f"Supplementary Table {n}: {len(missing)} of {len(rows)} rows not in the PDF text, first {missing[0]!r}")
        print(f"Supplementary Table {n}: {len(rows) - len(missing)} of {len(rows)} data rows in the PDF text")
    # soft hyphens and fonts
    shy = text.count("\u00ad")
    if shy:
        fails.append(f"{shy} soft hyphens (U+00AD) in the PDF text")
    print("soft hyphens in the PDF text:", shy)
    src = open(SI_TEXT, encoding="utf-8").read() + "".join(
        open(os.path.join(FP, "supp_tables", f"Supplementary Table {n}.md"), encoding="utf-8").read() for n in range(1, N_TABLES + 1))
    src += "".join(SUPER.values()) + "0123456789 \n"
    stray = {}
    for p in pdf:
        for b in p.get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln["spans"]:
                    if "Arial" in sp["font"]:
                        for ch in sp["chars"]:
                            if ch["c"] not in src:
                                stray[f"U+{ord(ch['c']):04X}"] = stray.get(f"U+{ord(ch['c']):04X}", 0) + 1
    if stray:
        fails.append(f"Arial text layer holds characters absent from the sources: {stray}")
    print("Arial text layer characters absent from the sources:", stray or "none")
    # fonts
    bad, fams = set(), set()
    for p in pdf:
        for f in p.get_fonts(full=True):
            xref, ext, ftype, name = f[0], f[1], f[2], f[3]
            if ext == "n/a" or ftype == "Type3":
                bad.add((name, ftype, ext))
            fams.add(name.split("+")[-1])
    noto = sorted(f for f in fams if "noto" in f.lower() or "serif" in f.lower())
    if noto:
        fails.append(f"fallback fonts in the PDF: {noto}")
    print("font families:", sorted(fams))
    if bad:
        fails.append(f"fonts not embedded or Type 3: {sorted(bad)}")
    print("fonts:", "all embedded, no Type 3" if not bad else sorted(bad))
    # em dash
    for label, t in (("PDF", text), ("docx", dtext), ("SI text", open(SI_TEXT, encoding="utf-8").read())):
        if EM_DASH in t:
            fails.append(f"em dash in the {label}: {t.count(EM_DASH)}")
    print("em dashes:", "none in the PDF, the .docx or the SI text" if not any("em dash" in f for f in fails) else "FOUND")
    # legends
    words = {n: len(plain(si["legends"][n]).split()) for n in range(1, N_FIGS + 1)}
    over = {n: w for n, w in words.items() if w >= LEGEND_WORDS_UNDER}
    if over:
        fails.append(f"legends of {LEGEND_WORDS_UNDER} words or more: {over}")
    print(f"legend words: max {max(words.values())} (Supplementary Figure {max(words, key=words.get)}), all under {LEGEND_WORDS_UNDER}" if not over else over)
    # framing and banned words: reported, not failed (tables are S534's text)
    for pat in (r"submitted study", r"\bApril\b", r"\bre-run\b", r"\bcomprehensive\b", r"\bnovel\b", r"\bunique\b", r"\bnew\b", r"\bfor the first time\b"):
        hits = re.findall(pat, flat, flags=re.I)
        if hits:
            print(f"NOTE: {len(hits)} x '{pat}' in the PDF text")
    print("pages:", pages)
    return fails


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3])
        return 0
    assert len(sys.argv) == 1 or sys.argv[1] == "build", sys.argv
    si = read_si()
    tables = {n: read_table(n) for n in range(1, N_TABLES + 1)}
    data = data_items()
    start, figinfo, pages = build_pdf(si, tables, data)
    build_docx(si, tables, data)
    for n, placed, scale, path in figinfo:
        print(f"Supplementary Figure {n}: page {start[('Figure', n)]}, legend {placed}, plate scale {scale:.3f}, {path}")
    for n in range(1, N_NOTES + 1):
        print(f"Supplementary Note {n}: page {start[('Note', n)]}")
    for n in range(1, N_TABLES + 1):
        print(f"Supplementary Table {n} | {tables[n][0]}: page {start[('Table', n)]}")
    print("wrote", os.path.relpath(OUT_PDF, ROOT), "and", os.path.relpath(OUT_DOCX, ROOT))
    fails = check(si, tables, start, pages)
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
