"""Silvanus P. Thompson, Calculus Made Easy (1914): a RESTORED EDITION.

    python3 calculus-made-easy/prep.py

Gutenberg #33283, the second edition, enlarged, of 1914 (first edition
1910). Alex asked for it on 2026-09-20, together with Rogers' Physics for
the Inquiring Mind, which could not be done: Rogers renewed its copyright
himself in 1988 (RE414029), so it is protected in the US until 2055.

THE MATHEMATICS IS THE BOOK, AND IT IS ENCODED, NOT LOST. Gutenberg sets
every formula as an SVG image, 3,687 of them, and every one carries a
`data-tex` attribute with its LaTeX -- the pillow-problems situation. A
restored edition prints the notation as Thompson printed it, so the LaTeX
rides through chapters/ untouched, \\(...\\) inline and \\[...\\] displayed,
and both renderers typeset it as MathML at render time (mathml.py). A
display formula inside a paragraph stays inside it, as it does on the
printed page. Pillow Problems flattened its formulas to Unicode instead;
that was a retelling, and a different ruling.

TABLES carrying formulas are tab-indented rows with cells split on " | ",
which both renderers set as a real table. The Contents table is dropped;
the edition makes its own.

THE TRANSCRIBERS CORRECTED THE BOOK, AND SAY SO. Their note: "minor
typographical and numerical corrections, have been made without comment";
the Chapter XIV tables of (1 + 1/n)^n, e^x and the money sums were
recomputed; Figures 38/39 and 44/45 were interchanged to match the text,
and the dashed lines of Fig. 39 moved to match its table. The LaTeX source
(_src/cme.tex) records each correction as \\DPtypo{printed}{corrected}, so
the list is not lost. This edition follows the corrected text -- they are
misprints and arithmetic slips against Thompson's own working -- and the
introduction says so.

WHAT IS LEFT OUT: the cover image and a title-page ornament (not plates),
the transcriber's note, the Contents, and "A Selection of Mathematical
Works", the publisher's advertisement at the back.

Thompson's page references ("see p. 76") are kept as printed; they refer
to the 1914 printing, and the introduction says that too.

MODERN_CHAPTERS/ IS COMPOSED from chapters/ plus captions/*.txt, as in the
other restored editions. The raw-HTML word count is the second witness.
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
IMAGES = ROOT / "site" / "images" / "calculus-made-easy"
PIN = HERE / "plates.json"
SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or", "as", "from", "into"}
ROMAN = re.compile(r"^[IVXLC]+$")
HOLD = "\x00F{}\x00"
DROPPED = {"cover.jpg": "the Gutenberg cover, not a plate",
           "i_001.jpg": "the title-page ornament"}
# Two printed captions carry a formula. A figcaption is plain text on the
# page and is the epub's alt text, so these two are set in Unicode.
CAPTION_FIX = {"Fig. 6.—Graph of .": "Fig. 6.—Graph of y = 7x².",
               "Fig. 6a.—Graph of .": "Fig. 6a.—Graph of dy/dx = 14x."}
FRONT_EPIGRAPH = ["What one fool can do, another can.",
                  "(Ancient Simian Proverb.)"]
# Gutenberg's HTML -> as printed. Witnessed by Archive.org
# `CalculusMadeEasy`, a photographic scan of a later US printing (1943) whose
# first 21 chapters are this text, and by Gutenberg's own typeset PDF.
# NOTE: `calculusmadeeasy_202001`, catalogued as a 1914 scan, IS that PDF
# (blue hyperlinks, Computer Modern type) and is not an independent witness.
SOURCE_FIXES = [
    ("(or one trillionth)", "(or one billionth)",
     "1/1,000,000,000,000 is a billionth in the British long scale Thompson "
     "wrote in; Gutenberg's HTML and TeX both modernised it"),
    ("bang went sixpence", "bang went saxpence",
     "Sandy's Scots, the Punch joke; Gutenberg's own TeX has saxpence too, "
     "so only the HTML normalised it"),
    ('">4.50</td>\r\n<td class="tdc bb br">7.69<', '">4.50</td>\r\n<td class="tdc bb br">7.39<',
     "the For Fig. 38 table: e squared is 7.389, the plate draws 7.39, and "
     "Gutenberg's TeX corrects it (\\DPtypo{7.69}{7.39}); the HTML did not"),
]
# (image file drawing the SMALLER-numbered figure, image file drawing the other)
LABEL_SWAPS = [("i_077c.jpg", "i_077d.jpg"),    # Figs. 12 and 13
               ("i_141a.jpg", "i_141b.jpg"),    # Figs. 38 and 39
               ("i_162a.jpg", "i_162b.jpg")]    # Figs. 44 and 45
EXPECT = {"plates": 66, "footnotes": 9, "tables": 14}
# The printed Contents does not list the Note to Chapter III; everything
# else must match it, title for title (the grimm rule: count against the
# book's own contents, never against a number written from memory).
UNLISTED = {"Note to Chapter III: How to Read Differentials",
            "Epilogue and Apologue"}
# The Contents line and the heading over the section differ; the heading is
# what stands over the text, so the heading is used (the Zitkala-Ša rule).
HEADING_DIFFERS = {"Answers to Exercises": "Answers"}


def clean(s):
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ").replace("\u202f", " ")).strip()


def titlecase(s):
    words = clean(s).rstrip(".").split()
    out = []
    for i, w in enumerate(words):
        if ROMAN.match(w.rstrip(".:")):
            out.append(w)
        elif i and w.lower() in SMALL:
            out.append(w.lower())
        else:
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(out)


def emph_safe(text):
    """Keep only the asterisks assemble.EMPH renders -- with every formula
    held aside first, because LaTeX's own underscores and asterisks would
    otherwise be read as emphasis delimiters here as well."""
    sys.path.insert(0, str(ROOT))
    import assemble
    import mathml
    maths, keep = [], []
    text = mathml.MATH.sub(lambda m: (maths.append(m.group(0)),
                                      HOLD.format(len(maths) - 1))[1], text)

    def hold(m):
        keep.append(m.group(0))
        return f"\x01{len(keep) - 1}\x01"
    held = assemble.EMPH.sub(hold, text).replace("*", "")
    held = re.sub(r"\x01(\d+)\x01", lambda m: keep[int(m.group(1))], held)
    return re.sub(r"\x00F(\d+)\x00", lambda m: maths[int(m.group(1))], held)


class Walker:
    def __init__(self, soup):
        self.notes = {}
        for d in soup.select("div.footnotes p"):
            a = d.find("a", id=re.compile(r"Footnote_\d+"))
            if a:
                n = a["id"].split("_")[1]
                a.decompose()
                self.notes[n] = self.para(d)     # same spacing rules as the body
        self.pending = []

    def text(self, el):
        out = []
        for c in el.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                out.append(str(c))
                continue
            if not isinstance(c, Tag):
                continue
            cls = c.get("class") or []
            if c.name == "img":
                tex = c.get("data-tex")
                if not tex:
                    raise SystemExit(f"image inside text: {c.get('src')}")
                out.append(" " + tex.strip() + " ")
            elif c.name == "span" and "pagenum" in cls:
                continue
            elif c.name == "a" and "fnanchor" in cls:
                self.pending.append(c["href"].split("_")[1])
            elif c.name == "br":
                out.append(" ")
            elif c.name in ("i", "em", "b"):
                inner = clean(self.text(c))
                out.append(f"*{inner}*" if inner else "")
            else:
                out.append(self.text(c))
        return "".join(out)

    def para(self, el):
        t = clean(self.text(el))
        # a formula's own spacing, not the text's: no space before
        # punctuation that follows a formula
        t = re.sub(r"(\\\)|\\\]) ([.,;:!?)])", r"\1\2", t)
        t = re.sub(r"\( (\\\()", r"(\1", t)
        return emph_safe(t)


def main():
    z = zipfile.ZipFile(SRC / "pg33283-h.zip")
    html = z.read("pg33283-images.html").decode("utf-8", "replace")
    for bad, good, why in SOURCE_FIXES:
        assert html.count(bad) == 1, (bad, html.count(bad))
        html = html.replace(bad, good)
    s = html.index("</header>") + len("</header>")
    e = html.index('<footer class="pg-boilerplate')
    soup = BeautifulSoup(html[s:e], "html.parser")
    for d in soup.select("div.transnote"):
        d.decompose()
    w = Walker(soup)

    # ---- front matter, located by its own text and asserted
    bq = soup.select_one("div.blockquot")
    got = re.sub(r"\( | \)", lambda m: m.group(0).strip(), clean(bq.get_text(" ")))
    assert got == " ".join(FRONT_EPIGRAPH), got
    pre = soup.find(string=re.compile(r"PREFACE TO THE SECOND EDITION"))
    pre_p = pre.find_parent("p")
    preface = []
    for x in pre_p.find_next_siblings():
        if x.name == "h2" or x.find("h2") or x.name == "table":
            break
        if x.name == "p" and clean(x.get_text()):
            preface.append(w.para(x))
    assert preface[0].startswith("The surprising success") or \
        preface[0].startswith("THE surprising success"), preface[0]
    preface[0] = re.sub(r"^THE ", "The ", preface[0])
    assert preface[-1] == "*October*, 1914.", preface[-1]   # italic in print

    # ---- the body: every h2 from PROLOGUE to the advertisement
    sections, cur, plates, tables = [], None, [], 0
    started = False

    def flat(nodes):
        """Top-level elements, with UNCLASSED <div>s opened. Gutenberg wraps
        several displayed formulas in a bare <div>; get_text() on it is
        empty because a formula is an image, and an earlier version of
        this file skipped every such div -- six displayed formulas never
        reached the text (the aesop wrapper trap, in a new costume)."""
        for n in nodes:
            if isinstance(n, Tag) and n.name == "div" and not n.find("h2") and (
                    not n.get("class") or "pg_body_wrapper" in n["class"]):
                yield from flat(n.children)
            else:
                yield n
    for el in flat(list(soup.children)):
        if not isinstance(el, Tag):
            continue
        h2 = el if el.name == "h2" else (el.find("h2") if el.name == "div" and
                                         "chapter" in (el.get("class") or []) else None)
        if h2 is not None:
            t = clean(h2.get_text(" "))
            if t.startswith("PROLOGUE"):
                started = True
            if t.startswith("A SELECTION OF MATHEMATICAL WORKS"):
                break
            if not started:
                continue
            m = re.match(r"(CHAPTER|NOTE TO CHAPTER) ([IVXLC]+)\.\s*(.*)", t)
            if m:
                label = "Chapter" if m.group(1) == "CHAPTER" else "Note to Chapter"
                title = f"{label} {m.group(2)}: {titlecase(m.group(3))}"
            else:
                title = titlecase(t)
            cur = {"title": title, "stream": []}
            sections.append(cur)
            continue
        if not started:
            continue
        cls = el.get("class") or []
        if el.name == "hr":
            if "tb" in cls:
                cur["stream"].append("* * *")
            continue
        if el.name == "div" and "footnotes" in cls:
            continue
        if el.name == "figure":
            img = el.find("img")
            src = img["src"].split("/")[-1]
            if src in DROPPED:
                continue
            cap = el.find("figcaption")
            printed = clean(cap.get_text(" ")) if cap else ""
            printed = CAPTION_FIX.get(printed, printed)
            plates.append({"src": src, "printed": printed})
            cur["stream"].append(("PLATE", len(plates) - 1))
            continue
        if el.name == "table":
            tables += 1
            rows = []
            for tr in el.find_all("tr"):
                cells = [w.para(td) for td in tr.find_all("td")]
                assert not any(" | " in c for c in cells), cells
                rows.append("\t" + " | ".join(cells))
            cur["stream"].append("\n".join(rows))
            continue
        if el.name == "div" and el.select_one(".poetry"):
            lines = [clean(v.get_text()) for v in el.select("div.verse")]
            cur["stream"].append("\n".join("\t" + x for x in lines))
            continue
        if el.name == "span" and "pagenum" in cls:
            continue                               # a page number, out of a wrapper
        if el.name == "span" and "align-center" in cls:
            cur["stream"].append(w.para(el))       # a bare display, from a wrapper
            continue
        if el.name == "p":
            only = [c for c in el.contents
                    if not (isinstance(c, NavigableString) and not c.strip())
                    and not (isinstance(c, Tag) and "pagenum" in (c.get("class") or []))]
            if not only:
                continue
            if len(only) == 1 and isinstance(only[0], Tag):
                k = only[0]
                kc = k.get("class") or []
                txt = clean(k.get_text(" "))
                if k.name == "span" and "float" in kc:        # "{For Fig. 38"
                    cur["stream"].append(txt.lstrip("{").strip())
                    continue
                if k.name in ("b", "i") and not k.find("img") and (
                        k.name == "b" or "space-above2" in (el.get("class") or [])
                        or re.match(r"(Case|Examples?|Numerical|Exercises)\b", txt)):
                    cur["stream"].append(txt.rstrip("."))
                    continue
            t = w.para(el)
            if t:
                cur["stream"].append(t)
                for n in w.pending:
                    cur["stream"].append(f"Footnote: {w.notes.pop(n)}")
                w.pending = []
            continue
        if el.name == "div" and not el.find("img") and \
                not clean(re.sub(r"\[Pg \d+\]", "", el.get_text())):
            continue
        raise SystemExit(f"unhandled <{el.name} {cls}>: {clean(el.get_text())[:80]!r}")

    toc = []
    for tr in soup.find_all("table")[0].find_all("tr")[1:]:
        tds = [clean(td.get_text(" ")) for td in tr.find_all("td")]
        t = re.sub(r"^([IVXLC]+)\. ", r"Chapter \1: ", tds[0])
        toc.append(HEADING_DIFFERS.get(t, t))
    def key(t):
        return re.sub(r"[^a-z]+", " ", t.lower()).strip()
    ours = [x["title"] for x in sections if x["title"] not in UNLISTED]
    assert [key(t) for t in toc] == [key(t) for t in ours], \
        [(a, b) for a, b in zip(toc, ours) if key(a) != key(b)][:3] or (len(toc), len(ours))
    assert len(plates) == EXPECT["plates"], len(plates)
    assert tables == EXPECT["tables"], tables
    assert not w.notes, f"footnotes never placed: {sorted(w.notes)}"
    nfoot = sum(1 for x in sections for v in x["stream"]
                if isinstance(v, str) and v.startswith("Footnote: "))
    assert nfoot == EXPECT["footnotes"], nfoot

    # ---- three pairs of plates carry each other's numbers in the HTML.
    # Thompson's text defines each figure (Fig. 12 "a straight line", Fig. 13
    # "turns more upwards", Fig. 38 y = ε^x, Fig. 44 y = sin θ), Gutenberg's
    # own typeset PDF agrees, and the transcriber's note says two of the
    # pairs were interchanged -- it appears the pictures moved and their
    # numbers went with them. Relabelled by what each plate draws; where the
    # swap left the pair out of order in the text, the two change places.
    for src_a, src_b in LABEL_SWAPS:
        ia = next(i for i, p in enumerate(plates) if p["src"] == src_a)
        ib = next(i for i, p in enumerate(plates) if p["src"] == src_b)
        plates[ia]["printed"], plates[ib]["printed"] = \
            plates[ib]["printed"], plates[ia]["printed"]
    for x in sections:
        st = x["stream"]
        for k in range(len(st) - 1):
            if isinstance(st[k], tuple) and isinstance(st[k + 1], tuple):
                na = re.search(r"\d+", plates[st[k][1]]["printed"] or "0")
                nb = re.search(r"\d+", plates[st[k + 1][1]]["printed"] or "0")
                if na and nb and int(na.group()) > int(nb.group()) and \
                        plates[st[k][1]]["src"] in {s for p in LABEL_SWAPS for s in p}:
                    st[k], st[k + 1] = st[k + 1], st[k]

    # ---- plates: digit-free ids, pinned
    L = "abcdefghijklmnopqrstuvwxyz"
    rows = [{"id": L[i // 26] + L[i % 26], "source": p["src"], "printed": p["printed"]}
            for i, p in enumerate(plates)]
    if PIN.exists():
        old = json.loads(PIN.read_text())
        assert [(r["id"], r["source"]) for r in old] == \
               [(r["id"], r["source"]) for r in rows], "plate ids moved"
    PIN.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    IMAGES.mkdir(parents=True, exist_ok=True)
    for f in IMAGES.iterdir():
        f.unlink()
    for r in rows:
        (IMAGES / f"fig{r['id']}.jpg").write_bytes(z.read(f"images/{r['source']}"))

    # ---- spoken readings for alttext (see mathml.py): Gutenberg's own alt
    # on each formula image, keyed by its LaTeX
    import mathml
    alts = {}
    for img in soup.find_all("img"):
        tex, alt = img.get("data-tex"), clean(img.get("alt") or "")
        if tex and alt:
            k = mathml._norm(mathml.formulas(tex.strip())[0][0])
            alts.setdefault(k, alt)
    (HERE / "mathalt.json").write_text(json.dumps(alts, indent=0, ensure_ascii=False))

    # ---- witness: the raw HTML's prose words against what was emitted
    body = html[html.index('id="PROLOGUE"'):html.index("A SELECTION OF MATHEMATICAL")]
    body = re.sub(r'<div class="footnotes">.*?</div>\s*</div>', " ", body, flags=re.S)
    body = re.sub(r'<span class="pagenum"[^>]*>.*?</span>', " ", body, flags=re.S)
    body = re.sub(r'<a class="fnanchor[^>]*>.*?</a>', " ", body, flags=re.S)
    body = re.sub(r"<figcaption>.*?</figcaption>", " ", body, flags=re.S)
    body = re.sub(r"<h2.*?</h2>", " ", body, flags=re.S)
    raw = re.sub(r"<[^>]+>", " ", body).replace("&nbsp;", " ")
    raw_words = len([x for x in raw.split() if re.search(r"\w", x)])
    got = 0
    for x in sections:
        for v in x["stream"]:
            if isinstance(v, str) and not v.startswith("Footnote: "):
                t = mathml.MATH.sub(" ", v).replace("*", "").replace(" | ", " ")
                got += len([y for y in t.split() if re.search(r"\w", y)])
    assert abs(raw_words - got) <= 0.005 * raw_words, (raw_words, got)

    # ---- compose
    captions = {}
    for f in sorted((HERE / "captions").glob("*.txt")) if (HERE / "captions").is_dir() else []:
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                k, _, v = line.partition("\t")
                if k.strip() in captions:
                    raise SystemExit(f"{f.name}: {k.strip()} captioned twice")
                captions[k.strip()] = v.strip()
    assert not set(captions) - {r["id"] for r in rows}
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    front = [("Epigraph", ["\t" + FRONT_EPIGRAPH[0] + "\n\t" + FRONT_EPIGRAPH[1]]),
             ("Preface to the Second Edition", preface)]
    allsec = front + [(x["title"], x["stream"]) for x in sections]
    manifest, described = [], 0
    for idx, (title, stream) in enumerate(allsec):
        src, mod = [title, ""], [title, ""]
        for v in stream:
            if isinstance(v, tuple):
                r = rows[v[1]]
                desc = captions.get(r["id"], "")
                described += bool(desc)
                cap = " — ".join(y for y in (r["printed"], desc) if y)
                src.append(f"[Figure {r['id']}]")
                mod.append(f"[Figure {r['id']}: {cap}]" if cap else f"[Figure {r['id']}]")
            else:
                src.append(v)
                mod.append(v)
            src.append("")
            mod.append("")
        (HERE / "chapters" / f"{idx:03d}.txt").write_text("\n".join(src).rstrip() + "\n")
        (HERE / "modern_chapters" / f"{idx:03d}.txt").write_text("\n".join(mod).rstrip() + "\n")
        manifest.append({"file": f"{idx:03d}.txt", "title": title, "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    nmath = sum(len(mathml.MATH.findall(v)) for _, st in allsec for v in st if isinstance(v, str))
    mathml.convert_all([f for _, st in allsec for v in st if isinstance(v, str)
                        for f in mathml.formulas(v)])
    print(f"{len(allsec)} sections, {raw_words:,} prose words (emitted {got:,}), "
          f"{nmath:,} formulas, {tables} tables, {nfoot} footnotes, "
          f"{len(rows)} plates, {described}/{len(rows)} described")


if __name__ == "__main__":
    main()
