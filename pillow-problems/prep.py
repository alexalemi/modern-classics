"""Turn Gutenberg #79080 (Pillow Problems) into chapters/ + manifest.

    bash pillow-problems/fetch.sh && python3 pillow-problems/prep.py

Carroll's Curiosa Mathematica, Part II (1893): seventy-two problems he
worked in his head, in bed, in the dark, "as a remedy for the harassing
thoughts that are apt to invade a wholly unoccupied mind". Questions,
Answers and Solutions, in three chapters that share one numbering.

WHAT MAKES THIS SOURCE DIFFERENT FROM EVERY OTHER IN THE PROJECT

There is no plain-text edition, because the mathematics is not text: it
is 2,436 separate SVG files pulled in by <img>, one per symbol or
fragment, so "sin OP · PN" arrives as four images in a row. The
figure-marker pipeline does not fit that at all -- a marker mid-sentence
is not a plate.

But every one of those images carries a `data-tex` attribute holding the
LaTeX it was rendered from. So the mathematics is encoded, not lost, and
tex.py converts it: see that module for the four traps (the mid-height
decimal point, the multiplication dot, the vinculum-as-bracket, and the
row break welded to an ampersand). Formulas come back as Unicode text and
go inline; the seventy-two multi-line derivations come back flagged as
displays and are set as indented blocks, which both renderers now
handle.

THE PLATES ARE SEPARATE AND ARE ORDINARY. Sixty-three geometrical
diagrams arrive as real raster images (i_pNNN.jpg) and take the normal
[Figure N] pipeline. The FRONTISPIECE is one of them twice over: i_f004
is the diagram of Solution 67 with its labels taken off, printed opposite
the title page under the line "See p. 100". It falls outside every kept
section, so it would simply have been dropped -- and prep's own assertion
that every plate is placed exactly once is what caught it. It is moved to
the head of the first section and given the id "front", which
assemble.figure_name special-cases to front.jpg; writing it as
figfront.jpg produces a broken image on the page and a missing resource
in the epub (the tyndall/ trap).

THE PAGE-NUMBER CROSS-REFERENCES ARE DROPPED, and Carroll's own footnote
says why they can be: "The numerals, placed in parentheses, indicate the
pages where the corresponding matter may be found." They are page numbers
and nothing else, in an edition that has no pages -- and the three
chapters already share one numbering, so Answer 5 and Solution 5 belong
to Question 5 by construction. Each entry is titled instead ("Problem 5",
"Answer 5", "Solution 5"), which says the same thing and can be followed.

TWO THINGS THE TRANSCRIBER DID, both recorded in text_analysis:
  - Carroll used PRIVATE SYMBOLS for sine and cosine; the transcription
    replaced them with sin and cos. His footnote explaining them is kept.
  - 'a' and Greek alpha are indistinguishable in the printed book, and
    the transcriber corrected some expressions to avoid mathematical
    errors. Some symbol assignments are therefore his judgement, not
    Carroll's page.
"""

import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tex import convert                                   # noqa: E402

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
SITE_IMG = BOOK.parent / "site/images/pillow-problems"

MAX_WORDS = 7000

# A SOURCE DEFECT: one piece of LaTeX never got rendered and sits in the
# body as literal markup -- "1/kα, \\text{&c.}; which answers (1)". Every
# other formula in the book is an <img> with a data-tex attribute, so this
# one is invisible to the converter and would have shipped as typed. Fixed
# here, with a check that stops the build if the transcription is ever
# corrected upstream (the candle/ SOURCE_FIXES pattern).
SOURCE_FIXES = [("\\text{&amp;c.}", "etc.")]

# Printed opposite the title page, outside every section this prep keeps.
FRONTIS = "i_f004"

# The sections to keep, in order, with the title each gets in the manifest.
# CONTENTS is a list of page numbers, and "WORKS BY C. L. DODGSON" is the
# publisher's advertisements bound in at the back (the forces/ lesson).
KEEP = {
    "PREFACE TO FOURTH EDITION.": "Preface to the Fourth Edition",
    "PREFACE TO SECOND EDITION.": "Preface to the Second Edition",
    "INTRODUCTION.": "Introduction",
    "SUBJECTS CLASSIFIED.": "Subjects Classified",
    "CHAPTER I.": "Chapter I: Questions",
    "CHAPTER II.": "Chapter II: Answers",
    "CHAPTER III.": "Chapter III: Solutions",
}
ENTRY = {"CHAPTER I.": "Problem", "CHAPTER II.": "Answer",
         "CHAPTER III.": "Solution"}

# "1." or "1. (28)" or "1. (19, 31)" alone in a paragraph: the entry number,
# with the printed page references that follow it.
NUMBER = re.compile(r"^(\d+)\.\s*(?:\([\d,\s]*\))?\s*$")


# The chapter's own label repeats the title the manifest already gives it.
LABEL = re.compile(r"^(Questions|Answers|Solutions)\.$")


def clean(s):
    s = html.unescape(re.sub(r"<[^>]*>", "", s))
    # spelled as escapes: a literal no-break space inside a character class
    # is invisible in a diff and easy to lose in an edit (the bunyan/ trap)
    s = re.sub("[\u00a0\u2007\u202f\u2009\u2002\u2003]", " ", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    # Carroll dates each problem in the margin with an opening bracket and
    # no closing one -- "[24/3/84" -- which reads as a typo off the page.
    s = re.sub(r"^\[(\d+/\d+/\d+)$", r"[\1]", s)
    return s.replace("i. e.", "i.e.").replace("Q. E. F.", "Q.E.F.")


class Extract(HTMLParser):
    """Section HTML -> paragraphs, formulas, figure markers, tables.

    A parser and not a pattern, for the reason tyndall/ paid for: the
    source nests <p><span class="nowrap"><img>, and a non-greedy close tag
    lands in the wrong place every time.
    """

    def __init__(self, figmap, notes):
        super().__init__(convert_charrefs=True)
        self.figmap, self.notes = figmap, notes
        self.out, self.buf = [], []
        self.p = self.skip = 0
        self.table = self.row = self.cell = None

    def flush(self):
        s = clean("".join(self.buf))
        self.buf = []
        if not s:
            return
        if LABEL.match(s):
            return
        m = NUMBER.match(s)
        if m:
            self.out.append(("num", m.group(1)))
        else:
            self.out.append(("p", s))

    def emit(self, s):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(s)
        elif self.p or self.table is None:
            self.buf.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "").split()
        if tag == "img":
            if "data-tex" in a:
                text, display = convert(html.unescape(a["data-tex"]))
                if display:
                    self.flush()
                    self.out.append(("display", text))
                else:
                    self.emit(text)
                return
            name = Path(a.get("src", "")).stem
            if name in self.figmap:
                self.flush()
                self.out.append(("fig", self.figmap[name]))
            return
        if tag == "a" and "fnanchor" in cls:
            # KILL THE NOTE ANCHOR AS AN ELEMENT. Strip the tags naively and
            # its bare "[2]" welds onto the preceding word, which reads as
            # part of the text and passes every mechanical check (bunyan/).
            self.skip += 1
            self.emit(self.notes.get(a.get("href", "").lstrip("#"), ""))
            return
        if tag == "span" and "pagenum" in cls:
            self.skip += 1
            return
        if tag == "p":
            self.flush()
            self.p += 1
        elif tag == "table":
            self.flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "br":
            self.emit(" ")

    def handle_endtag(self, tag):
        if tag in ("a", "span") and self.skip:
            self.skip -= 1
            return
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(clean("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row):
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            rows = ["\t" + " | ".join(c for c in r) for r in self.table]
            if rows:
                self.out.append(("block", "\n".join(rows)))
            self.table = None
        elif tag == "p" and self.p:
            self.p -= 1
            self.flush()

    def handle_data(self, d):
        self.emit(d)

    def close(self):
        super().close()
        self.flush()
        return self.out


def render(blocks, label):
    """Extracted blocks -> the text of one chapter file."""
    out = []
    for kind, val in blocks:
        if kind == "num":
            out.append(f"{label} {val}")
        elif kind == "fig":
            out.append(f"[Figure {val}]")
        elif kind == "display":
            # indented, so both renderers set it as a block and not as prose
            out.append("\n".join("\t" + l for l in val.split("\n")))
        elif kind == "block":
            out.append(val)
        else:
            out.append(val)
    return out


def split_oversize(paras, label):
    """Chapter III is 11,600 words; cut it at entry boundaries only."""
    total = sum(len(p.split()) for p in paras)
    if total <= MAX_WORDS:
        return [paras]
    n = (total // MAX_WORDS) + 1
    target = total / n
    parts, cur, count = [], [], 0
    for p in paras:
        if (cur and count >= target
                and re.fullmatch(rf"{label} \d+", p.strip())):
            parts.append(cur)
            cur, count = [], 0
        cur.append(p)
        count += len(p.split())
    if cur:
        parts.append(cur)
    return parts


def main():
    page = SRC / "pg79080-images.html"
    if not page.exists():
        sys.exit("run fetch.sh first")
    body = page.read_text(errors="replace")
    for wrong, right in SOURCE_FIXES:
        if wrong not in body:
            sys.exit(f"the source no longer contains {wrong!r} -- the "
                     f"transcription has been corrected; drop this fix")
        body = body.replace(wrong, right)

    # ---- footnotes, inlined where they are anchored --------------------
    notes = {}
    for m in re.finditer(r'<div class="footnote"[^>]*>(.*?)</div>', body, re.S):
        seg = m.group(1)
        fid = re.search(r'id="(Footnote_\d+)"', seg)
        txt = re.sub(r"<img[^>]*data-tex=\"([^\"]*)\"[^>]*>",
                     lambda x: convert(html.unescape(x.group(1)))[0], seg)
        txt = clean(txt)
        txt = re.sub(r"^\[\d+\]\s*", "", txt)
        if fid:
            notes[fid.group(1)] = f" [Note: {txt}]"

    # ---- figures --------------------------------------------------------
    SITE_IMG.mkdir(parents=True, exist_ok=True)
    # OWN THE SET. An earlier run numbered the frontispiece among the
    # plates and left a fig64 behind; a step that writes a set of files
    # without clearing it first will eventually ship something stale (the
    # copy_figures lesson, and rebrand's consumed placeholder).
    for old in SITE_IMG.iterdir():
        old.unlink()
    figmap = {}
    for m in re.finditer(r'<figure[^>]*>(.*?)</figure>', body, re.S):
        src = re.search(r'src="images/([^"]+)"', m.group(1))
        if not src or not src.group(1).startswith("i_"):
            continue          # the cover is not a plate
        stem = Path(src.group(1)).stem
        if stem in figmap:
            sys.exit(f"plate {stem} is claimed twice")
        figmap[stem] = ("front" if stem == FRONTIS
                        else sum(1 for v in figmap.values() if v != "front") + 1)
        img = SRC / "unz" / "images" / src.group(1)
        if img.exists():
            name = ("front" if figmap[stem] == "front"
                    else f"fig{figmap[stem]}")
            shutil.copy(img, SITE_IMG / f"{name}{img.suffix}")
    if FRONTIS not in figmap:
        sys.exit(f"the frontispiece {FRONTIS} has gone from the source")
    placed = set()

    # ---- sections -------------------------------------------------------
    # The contents lists every heading too, so anchor on the LAST occurrence
    # (the candle/ and forces/ rule).
    cuts = {}
    for m in re.finditer(r"<h[12][^>]*>(.*?)</h[12]>", body, re.S):
        cuts[clean(m.group(1))] = (m.start(), m.end())
    order = sorted(((v[0], v[1], k) for k, v in cuts.items()))

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()

    manifest, idx = [], 0
    for i, (a, b, name) in enumerate(order):
        if name not in KEEP:
            continue
        stop = order[i + 1][0] if i + 1 < len(order) else len(body)
        e = Extract(figmap, notes)
        e.feed(body[b:stop])
        blocks = e.close()
        placed |= {v for k, v in blocks if k == "fig"}
        paras = render(blocks, ENTRY.get(name, ""))
        paras = [p for p in paras if p.strip()]
        if not manifest and not any(p.startswith("[Figure front") for p in paras):
            paras.insert(0, "[Figure front]")
            placed.add("front")
        if not paras:
            continue
        label = ENTRY.get(name, "")
        chunks = split_oversize(paras, label) if label else [paras]
        for k, chunk in enumerate(chunks):
            (CHAPTERS / f"{idx:03d}.txt").write_text("\n\n".join(chunk) + "\n")
            manifest.append({"file": f"{idx:03d}.txt", "title": KEEP[name],
                             "part": k + 1, "of": len(chunks),
                             "words": sum(len(p.split()) for p in chunk)})
            idx += 1

    missing = set(figmap.values()) - placed
    if missing:
        sys.exit(f"{len(missing)} plates on disk were never placed: "
                 f"{sorted(missing)[:8]}")

    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words, {len(figmap)} plates")
    for m in manifest:
        print(f"  {m['file']}  {m['words']:6,}w  {m['title']}"
              + (f"  (part {m['part']} of {m['of']})" if m["of"] > 1 else ""))


if __name__ == "__main__":
    main()
