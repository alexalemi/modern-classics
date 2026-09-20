"""Lewis Carroll, The Game of Logic (1886/1887): a RESTORED EDITION.

    python3 game-of-logic/prep.py

The text is Gutenberg #4763 (pg4763-h.zip). The diagrams are REDRAWN from
its ASCII by diagram.py, because the 1887 printing SETS them in type (ruled
boxes with the digits 1 and 0 for the red and grey counters), so a drawing
from the transcription is the typeset diagram set again, not a picture of a
picture (the calculus-made-easy rule).

THE TRANSCRIPTION SETS ITALICS AS CAPITALS ("represents a DOUBLE
Proposition", 'what we call an 'EXHAUSTIVE' division'), the old plain-text
habit. Each run of capitals in running text is an italic span in the print,
and the print's CASE is not recoverable from the capitals ('the Premisses'
is set 'THE PREMISSES'), so each run takes its case from the aligned words
of an Archive.org OCR of the 1887 printing, which kept the case and lost the
italic. A run the OCR cannot place is lowercased and listed.

A diagram block becomes TABLE ROWS: the block is cut into its columns, each
ruled box is one plate, and the text on either side (the exercise number,
the reading of the diagram) becomes the cells beside it -- the symbolic-
logic convention both renderers already render as a table. Four blocks mix
prose and diagrams in a layout no rule can read, and are set by hand
(OVERRIDES), each asserted to match the source block it replaces.

WITNESSES, asserted: every ruled box placed exactly once; the Contents'
chapter and section names found as headings; no capital run left in prose.
"""
import html as HTML
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import restore_lib as R  # noqa: E402
import diagram           # noqa: E402
from bs4 import BeautifulSoup, NavigableString, Tag  # noqa: E402

DIAG = HERE / "_src" / "diagrams"
# SCAN VOTE: readings the two 1887 copies (gameoflogic00carruoft,
# gameoflogic00carrrich) agree on against the transcription. Each asserted
# once, on the walked text.
TEXT_FIXES = [
    ("and you friend will go", "and your friend will go", "both scans"),
    ("if we use letters, the must be", "if we use letters, they must be", "both scans"),
    ("the rather meager piece", "the rather meagre piece", "both scans: the print's spelling"),
    ("or our cupboard will be", "or our cupboards will be", "both scans"),
    ("at all, by \"some x are y\"", "at all, but \"some x are y\"", "both scans"),
    ("which said to make", "which is said to make", "both scans"),
    ("arguments, that scattered broadcast", "arguments, that are scattered broadcast", "both scans"),
    ("Suppose, of example,", "Suppose, for example,", "both scans"),
    ("the Attribute x, y are *compatible*", "the Attributes x, y are *compatible*", "both scans"),
    ("Any oyster may be crossed in love", "An oyster may be crossed in love", "both scans"),
    ("as the Subject of Proposition", "as the Subject of our Proposition", "both scans"),
    ("join one or the other of two", "join one or other of two", "both scans"),
]
KEEP_CAPS = {"I", "A", "O", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}


def is_box(t):
    return "|" in t and "---" in t


# ---------------------------------------------------------------- case from OCR
def ocr_words():
    txt = (HERE / "_src" / "scan-gameoflogic00carruoft-djvu.txt").read_text(errors="replace")
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", txt)


class Caser:
    """Find a capital run's words in the OCR, in order, near where the
    run falls in the book, and take the OCR's case."""

    def __init__(self):
        self.w = ocr_words()
        self.low = [x.lower().strip("'’") for x in self.w]
        self.missed = []

    # runs the OCR garbled, set from the page image of gameoflogic00carruoft
    FIXED = {"THIS SQUARE IS OCCUPIED": "this Square is occupied",
             "I ADVISE YOU NOT TO TRY THE EXPERIMENT": "I advise you not to try the experiment"}

    def case(self, run, frac):
        if run in self.FIXED:
            return self.FIXED[run]
        want = [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z'’-]*", run)]
        n = len(self.low)
        centre = int(frac * n)
        best = None
        for i in range(max(0, centre - 3000), min(n, centre + 3000)):
            if self.low[i] == want[0].strip("'’") and all(
                    i + k < n and self.low[i + k] == want[k].strip("'’") for k in range(len(want))):
                d = abs(i - centre)
                if best is None or d < best[0]:
                    best = (d, i)
        if best is None:
            self.missed.append(run)
            return run.lower()
        i = best[1]
        out, k = [], 0
        for tok in re.split(r"([A-Za-z][A-Za-z'’-]*)", run):
            if re.fullmatch(r"[A-Za-z][A-Za-z'’-]*", tok):
                o = self.w[i + k]
                out.append(o if o.lower().strip("'’") == tok.lower().strip("'’") else tok.lower())
                k += 1
            else:
                out.append(tok)
        return "".join(out)


CAPRUN = re.compile(r"(?<![A-Za-z])((?:[A-Z][A-Z'’-]*[A-Z]|[A-Z])(?:[ ,-]+(?:[A-Z][A-Z'’-]*[A-Z]|[A-Z]))*)(?![A-Za-z])")


def italicise(text, caser, frac):
    def sub(m):
        run = m.group(1)
        words = re.findall(r"[A-Z][A-Z'’-]*", run)
        if all(w in KEEP_CAPS for w in words):
            return run
        if len(words) == 1 and len(words[0]) == 1:
            return run
        return "*" + caser.case(run, frac) + "*"
    return CAPRUN.sub(sub, text)


# ---------------------------------------------------------------- diagram blocks
def grid_of(text):
    rows = [r.rstrip() for r in text.replace("\t", "    ").split("\n")]
    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    W = max(len(r) for r in rows)
    return [r.ljust(W) for r in rows], W


def column_spans(g, W):
    """Box columns: runs of columns that carry a rule character, joined
    across one-column gaps (a box's corners are blank)."""
    # a HYPHEN in the text beside a box ("not-nice") is not a rule: a column
    # belongs to a box only if it holds a '|' or lies inside a run of three
    # or more '-'
    def ruled(r, c):
        if r[c] == "|":
            return True
        if r[c] != "-":
            return False
        a = c
        while a > 0 and r[a - 1] == "-":
            a -= 1
        b = c
        while b + 1 < len(r) and r[b + 1] == "-":
            b += 1
        return b - a + 1 >= 3
    has = [any(ruled(r, c) for r in g) for c in range(W)]
    spans, c = [], 0
    while c < W:
        if has[c]:
            s = c
            while c < W and (has[c] or (c + 1 < W and has[c + 1])):
                c += 1
            spans.append((s, c))
        else:
            c += 1
    return spans


def block_rows(text, place):
    """A diagram <pre> -> one table row: the text left of each box, the box
    (rendered), and the text after it; cells in order."""
    g, W = grid_of(text)
    spans = column_spans(g, W)
    cells, prev = [], 0
    for s, e in spans:
        left = " ".join(" ".join(r[prev:s].split()) for r in g if r[prev:s].strip()).strip()
        if left:
            cells.append(left)
        sub = "\n".join(r[s:e] for r in g)
        cells.append(place(sub))
        prev = e
    tail = " ".join(" ".join(r[prev:].split()) for r in g if r[prev:].strip()).strip()
    if tail:
        cells.append(tail)
    return cells


# ---------------------------------------------------------------- hand-set blocks
# Diagram corrections, each read off the page image of gameoflogic00carr
# and asserted to apply once: (pre index, transcribed row, printed row).
ASCII_FIXES = [
    # p. 60, answer 7 is "Some x are y'": ONE counter, in the right-hand cell
    (81, "  7.  | 1 | 1 |  It might be thought that the proper",
         "  7.  |   | 1 |  It might be thought that the proper"),
    # p. 52, § 7 no. 4: grey counters in 10, 13, 14 and 16 (14 was lost)
    (75, "|  |1 | 0|  |            |  |0 |  |  |",
         "|  |1 | 0|  |            |  |0 | 0|  |"),
    # p. 68, § 6 no. 9, "No x are m": grey in 11 and 12 only (a stray 0 in 13)
    (114, "                         |   | 0 |   |   |",
          "                         |   |   |   |   |"),
    # p. 43, § 3 no. 16: a grey counter above AND below (answer: No y' exist)
    (61, "| 1 |        |   |        | 1 |        |   |",
         "| 1 |        |   |        | 1 |        | 0 |"),
    # Gutenberg's exercise numbers against the print: p. 61 prints 19., p. 64
    # prints 23. (each follows 18. and 22.)
    (92, " 15. Some y exist.", " 19. Some y exist."),
    (109, " 17.  Some x are y, and some x' are y'.", " 23.  Some x are y, and some x' are y'."),
]


def cut(pre, r0, r1, c0, c1):
    rows = pre.split("\n")
    return "\n".join(r[c0:c1] for r in rows[r0:r1])


def override(i, pre, place):
    """The four blocks that mix prose and diagrams, set by hand. Each text
    piece is asserted to be in the source block, word for word."""
    words = lambda s: " ".join(s.split())
    src = words(re.sub(r"[|_-]+", " ", pre))

    def say(s):
        assert all(w in src for w in re.findall(r"[A-Za-z']+", s)), (i, s)
        return s
    rows = pre.split("\n")
    if i == 16:
        box = "\n".join(r[43:] for r in rows)
        return [("P", say("Suppose we find it marked like this:—")), ("CELLS", [place(box)]),
                ("P", say("What would that tell us?"))]
    if i == 28:
        box = [r[38:] for r in rows]
        # the column also catches the end of the prose line above the box
        while "-" not in box[0]:
            box.pop(0)
        box = "\n".join(box)
        return [("P", say("These principles may be applied to all the other oblongs. For instance, to represent "
                          "\"all y' are m'\" we should mark the ") + "*right-hand upright oblong*" +
                 say(" (the one that has the attribute y') thus:—")),
                ("CELLS", [place(box)])]
    if i == 81:
        seven = "\n".join(r[6:15] for r in rows[0:5])
        wrong = "\n".join(r[18:27] for r in rows[4:9])
        eight = "\n".join(r[25:34] for r in rows[13:18])
        return [("CELLS", ["7.", place(seven), say("It might be thought that the proper Diagram would be") + " " +
                           place(wrong) + say(", in order to express \"some x exist\": but this is really "
                           "contained in \"some x are y'.\" To put a red counter on the division-line would only "
                           "tell us ") + "\"*one of the two* compartments is occupied\"" +
                           say(", which we know already, in knowing that ") + "*one*" + say(" is occupied.")]),
                ("CELLS", ["8.", say("No x are y. i.e."), place(eight)])]
    if i == 52:
        # a lone board whose label x' sits on the rule: column-splitting took
        # the prime for a column of its own
        return [("CELLS", [place(pre)])]
    if i == 17:
        out = [("CELLS", ["*Symbols*", "*Meanings*"])]
        # the table's closing rule is not part of the last board
        body = [r for r in rows[4:] if "_" not in r]
        groups, cur = [], []
        for r in body:
            if r[:17].strip() in ("", "|") and r[18:].strip() == "" and cur and r.rstrip().endswith("|") and r.strip() == "|":
                groups.append(cur); cur = []
            else:
                cur.append(r)
        if cur:
            groups.append(cur)
        for gr in groups:
            box = "\n".join(r[:16] for r in gr)
            meaning = " ".join(" ".join(r[18:].split()) for r in gr if r[18:].strip("_ "))
            out.append(("CELLS", [place(box), say(meaning)]))
        # ONE table: the rows go into one block, or each renders as a table
        # of its own and the header as preformatted text
        return [("TABLE", [c for _, c in out])]
    raise KeyError(i)


OVERRIDDEN = {16, 17, 28, 52, 81}
# the section heads are short paragraphs naming a section of the Contents
SECHEAD = re.compile(r"(\d)\.\s+(Syllogisms|Fallacies|Elementary|Half of Smaller Diagram|Smaller Diagram|"
                     r"Larger Diagram|Both Diagrams (?:to be )?employed)\.?")
SUBTITLE = re.compile(r"(?:Propositions (?:to be )?represented|Symbols (?:to be )?interpreted)\.")


# ---------------------------------------------------------------- main
def main():
    z = zipfile.ZipFile(HERE / "_src" / "pg4763-h.zip")
    h = z.read("pg4763-images.html").decode()
    # the transcriber's stand-in for the therefore sign, and his note
    # apologising for it (which is his, not Carroll's)
    n = h.count("&amp;there4")
    assert n >= 5, n
    h = h.replace("&amp;there4", "∴")
    note = re.search(r"<p>\s*\[\*\]\[NOTE from Brett:.*?</p>", h, re.S)
    assert note, "transcriber's note not found"
    h = h[:note.start()] + h[note.end():]
    assert h.count("[*]") == 1, h.count("[*]")
    h = h.replace("[*]", "")
    soup = BeautifulSoup(h, "html.parser")
    body = soup.body
    DIAG.mkdir(parents=True, exist_ok=True)
    for f in list(DIAG.glob("*.png")) + list(DIAG.glob("*.txt")):
        f.unlink()
    caser = Caser()
    placed = []

    def place(sub):
        k = len(placed)
        name = f"d{k:03d}.png"
        diagram.render(sub).save(DIAG / name, optimize=True)
        (DIAG / name).with_suffix(".txt").write_text(sub)   # for proofing
        placed.append(name)
        return f"[PLATE {name}]"

    pres_all = body.find_all("pre")
    pre_index = {id(e): k for k, e in enumerate(pres_all)}
    fixed = {}
    for k, old, new in ASCII_FIXES:
        t0 = HTML.unescape(pres_all[k].get_text())
        assert t0.count(old) == 1, (k, old)
        fixed[k] = fixed.get(k, t0).replace(old, new)
    els = [e for e in body.find_all(["h1", "h2", "h3", "p", "pre"])]
    start = next(i for i, e in enumerate(els) if e.name == "p" and "To my Child-friend" in e.get_text())
    end = next(i for i, e in enumerate(els) if e.name == "h2" and "LICENSE" in e.get_text().upper())
    # the two boards before the dedication are the book's frontispiece: kept
    fronts = [e for e in els[:start] if e.name == "pre" and is_box(HTML.unescape(e.get_text()))]
    els = els[start:end]
    total = sum(len(e.get_text()) for e in els) or 1
    seen = 0
    # THE FRONTISPIECE, set by hand from the page image (gameoflogic00carr
    # leaf 6): the larger board, then the verse beside the smaller board.
    # Gutenberg drops the comma in "See, the Sun"; the print sets "full" and
    # "empty" in small capitals and RED and GREY letter-spaced, given here
    # as emphasis.
    assert len(fronts) == 2
    b1 = HTML.unescape(fronts[0].get_text())
    b2 = HTML.unescape(fronts[1].get_text())
    small = "\n".join(r[29:] for r in b2.split("\n"))
    assert "See the Sun is overhead" in b2 and "EMPTY" in b2
    sections = [{"title": "Frontispiece", "stream": [
        ("CELLS", [place(b1)]),
        ("P", "Colours for Counters"),
        ("BLOCK", "\tSee, the Sun is overhead,\n\tShining on us, *full* and *red*!\n"
                  "\tNow the Sun is gone away,\n\tAnd the *empty* sky is *grey*!"),
        ("CELLS", [place(small)])]}]
    pending_title = None
    for e in els:
        t = HTML.unescape(e.get_text())
        frac = seen / total
        seen += len(t)
        if e.name in ("h1", "h2", "h3"):
            s = " ".join(t.split()).rstrip(".")
            if re.fullmatch(r"CHAPTER [IVX]+", s):
                pending_title = s
                continue
            if pending_title:
                sections.append({"title": f"Chapter {pending_title.split()[1]}: {R.titlecase(s.lower())}",
                                 "stream": [], "chapter": True})
                pending_title = None
            elif s in ("NOTA BENE", "PREFACE", "CONTENTS"):
                sections.append({"title": R.titlecase(s.lower()), "stream": []})
            else:
                sections[-1]["stream"].append(("P", R.titlecase(s.lower())))
            continue
        st = sections[-1]["stream"]
        one = " ".join(t.split())
        if e.name == "p" and SUBTITLE.fullmatch(one) and st and st[-1][0] == "P" and st[-1][1].startswith("§ ") and "—" not in st[-1][1]:
            st[-1] = ("P", st[-1][1] + " — " + one.rstrip("."))      # "Propositions to be represented"
            continue
        m = SECHEAD.fullmatch(one) if e.name == "p" else None
        if m:
            st.append(("P", f"§ {m.group(1)}. {m.group(2)}"))
            continue
        if e.name == "p":
            if "poem" in (e.get("class") or []):
                lines = [" ".join(x.split()) for x in re.split(r"\n", e.get_text("\n")) if x.strip()]
                if lines and "To my Child-friend" in lines[0]:
                    if sections[-1]["title"] != "Dedication":
                        sections.append({"title": "Dedication", "stream": []})
                    st = sections[-1]["stream"]
                st.append(("BLOCK", "\n".join("\t" + x for x in lines)))
            else:
                st.append(("P", italicise(" ".join(t.split()), caser, frac)))
            continue
        # <pre>
        k = pre_index[id(e)]
        t = fixed.get(k, t)
        if k in OVERRIDDEN:
            st.extend(override(k, t, place))
            continue
        if is_box(t):
            st.append(("CELLS", block_rows(t, place)))
            continue
        for chunk in re.split(r"\n\s*\n", t):
            lines = [l.rstrip() for l in chunk.split("\n") if l.strip()]
            if not lines:
                continue
            if all(re.fullmatch(r"\s*_+\s*", l) for l in lines):
                continue                                # the printer's rule
            one = " ".join(lines[0].split())
            m = re.fullmatch(r"(\d+)\.\s+([A-Z][^.]*)\.", one)
            if len(lines) == 1 and m:
                st.append(("P", f"§ {m.group(1)}. {m.group(2)}"))   # a section head
                continue
            lines = [l for l in lines if not re.fullmatch(r"\s*_+\s*", l)]
            ind = min(len(l) - len(l.lstrip()) for l in lines)
            st.append(("BLOCK", "\n".join("\t" + l[ind:] for l in lines)))
    # PRINT-PAGE REFERENCES -> SECTIONS. Every "[See pp. 56, 7]" in the
    # Cross Questions points at the Crooked Answers by page; the printed
    # Contents gives each section's first page, so a page names its section.
    ANSWERS = [(55, 1), (59, 2), (61, 3), (62, 4), (65, 5), (67, 6), (72, 7), (85, None)]
    QUESTIONS = [(37, 1), (40, 2), (42, 3), (44, 4), (46, 5), (48, 6), (51, 7), (55, None)]

    def sec_of(page, table):
        return max(s for p0, s in table[:-1] if p0 <= page)

    def pages(spec):
        nums = [int(x) for x in re.findall(r"\d+", spec)]
        first = nums[0]
        out = [first]
        for n in nums[1:]:
            if n < first:                   # "pp. 55, 6" is 55 and 56
                n = int(str(first)[:-len(str(n))] + str(n))
            out.append(n)
        if "-" in spec:
            out = list(range(out[0], out[-1] + 1))
        return out

    nref = 0

    def ref(m):
        nonlocal nref
        nref += 1
        ps = pages(m.group(2))
        if ps[0] >= 55:
            secs = sorted({sec_of(p, ANSWERS) for p in ps})
            where = "Chapter III"
        else:
            secs = sorted({sec_of(p, QUESTIONS) for p in ps})
            where = "Chapter II"
        s = f"§ {secs[0]}" if len(secs) == 1 else "§§ " + ", ".join(map(str, secs[:-1])) + f" and {secs[-1]}"
        return f"[{m.group(1)} {where}, {s}]"
    REF = re.compile(r"\[([Ss]ee) (pp?\. [\d, -]+)\]")
    for s in sections:
        s["stream"] = [(it[0], REF.sub(ref, it[1])) + tuple(it[2:]) if it[0] in ("P", "BLOCK") else it
                       for it in s["stream"]]
    assert nref == 20, nref
    # the printed Contents is the WITNESS, not text: every section it names is
    # a heading in the body, and then it goes (the edition makes its own)
    contents = next(s for s in sections if s["title"] == "Contents")
    names = re.findall(r"\d\.\s+([A-Z][A-Za-z. ]+?)(?:\s*\.)*\s+\d+\s*$",
                       "\n".join(it[1] for it in contents["stream"]), re.M)
    heads = [it[1] for s in sections for it in s["stream"] if it[0] == "P" and it[1].startswith("§ ")]
    print(len(names), "sections in the Contents,", len(heads), "section heads in the body")
    assert len(heads) == 17, heads
    sections = [s for s in sections if s["title"] != "Contents"]
    # the transcription's "--" is the print's em dash (and assemble.py does
    # not convert it, so it would ship literally on the page)
    for s in sections:
        s["stream"] = [(it[0], re.sub(r"\s*--\s*", "—", it[1])) + tuple(it[2:]) if it[0] == "P" else it
                       for it in s["stream"]]
    R.text_fixes(sections, TEXT_FIXES)
    # the CELLS rows -> BLOCK tables with plate markers
    for s in sections:
        s["stream"] = [("BLOCK", "\t" + " | ".join(it[1])) if it[0] == "CELLS" else
                       ("BLOCK", "\n".join("\t" + " | ".join(r) for r in it[1])) if it[0] == "TABLE" else it
                       for it in s["stream"]]
    print(len(placed), "diagrams drawn;", len(caser.missed), "capital runs the OCR could not place:", caser.missed[:20])
    for s in sections:
        print(f'  {s["title"][:60]:60} {sum(len(it[1].split()) for it in s["stream"]):6}')
    json.dump({"sections": [{"title": s["title"], "stream": s["stream"], "chapter": s.get("chapter", False)}
                            for s in sections]}, open(HERE / "_src" / "stream.json", "w"), indent=1)
    compose(sections, placed)


def compose(sections, placed):
    """chapters/ with bare [Figure id] markers, modern_chapters/ with each
    filled from captions/*.txt; plates.json pins the ids (digit-free, in
    order of appearance); the drawings go to site/images/game-of-logic/."""
    L = "abcdefghijklmnopqrstuvwxyz"
    ids = {name: L[i // 26] + L[i % 26] for i, name in enumerate(placed)}
    pin = HERE / "plates.json"
    rows = [{"id": ids[n], "source": n, "printed": ""} for n in placed]
    if pin.exists():
        old = json.loads(pin.read_text())
        assert [(r["id"], r["source"]) for r in old] == [(r["id"], r["source"]) for r in rows], "plate ids moved"
    pin.write_text(json.dumps(rows, indent=1) + "\n")
    caps = {}
    for f in sorted((HERE / "captions").glob("*.txt")) if (HERE / "captions").is_dir() else []:
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                k, _, v = line.partition("\t")
                assert k.strip() not in caps, k
                caps[k.strip()] = v.strip()
    assert not set(caps) - set(ids.values()), "caption for an unknown plate"
    out = Path(__file__).parent.parent / "site" / "images" / "game-of-logic"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.iterdir():
        f.unlink()
    for n, i in ids.items():
        (out / f"fig{i}.png").write_bytes((DIAG / n).read_bytes())
    MARK = re.compile(r"\[PLATE (d\d{3}\.png)\]")
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for k, s in enumerate(sections):
        src, mod = [s["title"], ""], [s["title"], ""]
        for it in s["stream"]:
            text = it[1]
            # the print's short rule between exercise sets: a scene break,
            # not a paragraph of underscores
            if isinstance(text, str) and text.strip() and set(text.strip()) == {"_"}:
                text = "* * *"
            # a row that is ONE plate and nothing else is a figure, not a table
            if it[0] == "BLOCK" and MARK.fullmatch(text.strip()):
                text = text.strip()
            src.append(MARK.sub(lambda m: f"[Figure {ids[m.group(1)]}]", text))
            mod.append(MARK.sub(lambda m: f"[Figure {ids[m.group(1)]}: {caps[ids[m.group(1)]]}]"
                                if ids[m.group(1)] in caps else f"[Figure {ids[m.group(1)]}]", text))
            src.append(""); mod.append("")
        (HERE / "chapters" / f"{k:03d}.txt").write_text("\n".join(src).rstrip() + "\n")
        (HERE / "modern_chapters" / f"{k:03d}.txt").write_text("\n".join(mod).rstrip() + "\n")
        e = {"file": f"{k:03d}.txt", "title": s["title"], "part": 1, "of": 1}
        if s.get("chapter"):
            e["chapter"] = True
        manifest.append(e)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(len(ids), "plates;", len(caps), "captioned")


if __name__ == "__main__":
    main()
