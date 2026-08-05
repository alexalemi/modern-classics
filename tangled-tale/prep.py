"""Turn Gutenberg #29042 (A Tangled Tale) into chapters/ + manifest.json.

    bash tangled-tale/fetch.sh && python3 tangled-tale/prep.py

Carroll serialised these ten "Knots" in The Monthly Packet between 1880
and 1885: a comic story with a mathematical puzzle buried in it, and then,
a month later, his own review of the answers his readers had sent in. The
Appendix that carries those reviews is nearly half the book and is the
best thing in it — he sorts his correspondents into classes by pseudonym
and takes the wrong ones apart with enormous relish. It is translated
whole. (Same rule as soap-bubbles/, whose "Practical Hints" appendix is a
third of that book and is the reason it was written.)

THE PLATES. The -h.zip carries eleven images and only nine are the book's:

  i005  frontispiece, "at a pace of six miles in the hour"   Knot 1
  i018  Balbus and the dragon                                Knot 2
  i037  the deck of the ship (untitled in the original)      Knot 4
  i048  "why do they say 'Bamboo!' so often?"                Knot 6
  i059  "the cab-door isn't half wide enough!"               Knot 7
  i078  "he remains steadfast and unmoved."                  Knot 9
  i081  the Chelsea-bun street cry, set as music             Knot 10
  i097  the family tree of the dinner party                  Answers 2
  i099  the four houses round the square                     Answers 2

The two that are dropped are Gutenberg's own cover and the Macmillan
publisher's device — a monogram in a roundel of butterflies and fruit,
which is a printer's ornament and not an illustration. LOOK AT A PLATE
BEFORE DECIDING WHAT IT IS; three of these have no caption in the source
and one of them turned out to be a colophon.

CAPTIONS. Carroll captioned seven of them himself, and his captions are
quotations from the story, so they ride through into chapters/ as
[Figure N: caption] to be MODERNISED rather than replaced — the ball/
rule. The three with no caption (the ship's deck and the two diagrams in
the Answers) need one written, and the diagrams need one that says what
the diagram is *for*, because the prose refers to them by their letters.

MONEY. Keep the shillings and pence. Several answers work out the way
they do BECAUSE of twelve pence to the shilling, so decimalising would
silently break the puzzles; it is Carroll's arithmetic in Carroll's
units, which is the Verne rule. The currency gets one gloss, in the
preface, and none after that.
"""

import html
from html.parser import HTMLParser
import json
import re
import shutil
import sys
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
SITE_IMG = BOOK.parent / "site/images/tangled-tale"

# Plates, in the order they appear, with the section each belongs to.
# Anything in the -h.zip and not in this table is deliberately not a plate.
PLATES = ["i005", "i018", "i037", "i048", "i059", "i078", "i081",
          "i097", "i099"]
DROP_IMAGES = {"icover", "i003"}          # Gutenberg's cover; Macmillan's device

WORDNUM = ["One", "Two", "Three", "Four", "Five",
           "Six", "Seven", "Eight", "Nine", "Ten"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def clean(s):
    s = re.sub(r"<[^>]*>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace(" ", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


SMALL = {"a","an","and","as","at","but","by","for","in","of","on","or",
         "the","to","with"}


def titlecase(s):
    out = []
    for i, w in enumerate(s.split()):
        out.append(w.capitalize() if (i == 0 or w.lower() not in SMALL)
                   else w.lower())
    return " ".join(out)


def img_parts(tag):
    """<img> tag -> (basename, caption). ATTRIBUTE ORDER IS NOT GUARANTEED:
    this source writes alt before src, so a pattern that expects src first
    matches the tag and quietly returns no caption at all — which loses
    every caption in the book while looking like it worked."""
    src = re.search(r'src="images/(\w+)\.\w+"', tag)
    alt = re.search(r"alt=(['\"])(.*?)\1", tag, re.S)
    return (src.group(1) if src else ""), clean(alt.group(2) if alt else "")


class Extract(HTMLParser):
    """Section HTML -> paragraphs, figure markers and indented verse.

    A PARSER RATHER THAN A PATTERN, because the verse here is
    div.poem > div.stanza > span, and a non-greedy regex for the closing
    </div> stops at the inner one — which is how Tyndall's Spenser stanza
    came out four times. Nesting is exactly what a parser is for.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf, self.lines = [], [], []
        self.depth_p = 0
        self.poem = 0

    def flush_par(self):
        s = clean("".join(self.buf))
        s = re.sub(r"\[\d+\]", "", s).strip()     # Gutenberg page anchors
        if s:
            self.out.append(s)
        self.buf = []

    def flush_verse(self):
        ls = [x for x in (clean(l) for l in self.lines) if x]
        if ls:
            self.out.append("\n".join("\t" + x for x in ls))
        self.lines = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            name, cap = img_parts(self.get_starttag_text())
            if name in DROP_IMAGES:
                return
            if name not in PLATES:
                sys.exit(f"unplaced image {name} — classify it in PLATES "
                         f"or DROP_IMAGES before running")
            n = PLATES.index(name) + 1
            self.out.append(f"[Figure {n}: {cap}]" if cap else f"[Figure {n}]")
        elif tag == "div" and "poem" in a.get("class", ""):
            self.poem += 1
        elif tag == "div" and self.poem and "stanza" in a.get("class", ""):
            self.flush_verse()
        elif tag == "br":
            if self.poem:
                self.lines.append("\n")
            else:
                self.buf.append(" ")
        elif tag == "p":
            self.depth_p += 1

    def handle_endtag(self, tag):
        if tag == "div" and self.poem:
            self.flush_verse()
            if "poem" in (self.get_starttag_text() or ""):
                pass
        elif tag == "p" and self.depth_p:
            self.depth_p -= 1
            self.flush_par()

    def handle_data(self, d):
        if self.poem:
            self.lines.append(d)
        elif self.depth_p:
            self.buf.append(d)

    def close(self):
        super().close()
        self.flush_verse()
        self.flush_par()
        return self.out


def blocks(chunk):
    """Kept as the entry point so main() reads the same."""
    # The poem divs close one level at a time; count them down explicitly
    # so verse never leaks into the following prose.
    e = Extract()
    for piece in re.split(r"(</div>)", chunk):
        if piece == "</div>" and e.poem:
            e.poem -= 1
            e.flush_verse()
            continue
        e.feed(piece)
    return e.close()


def main():
    page = SRC / "pg29042-images.html"
    if not page.exists():
        sys.exit("no tangled-tale/source — run `bash tangled-tale/fetch.sh`")
    t = page.read_text(encoding="utf-8", errors="replace")

    # The body runs from the dedication to the publisher's advertisements.
    start = t.rfind("<h2", 0, t.find("To My Pupil"))
    end = t.find("WORKS BY LEWIS CARROLL")
    if start < 0 or end < 0:
        sys.exit("could not find the body bounds in the source")
    body = t[start:end]

    # Cut on the headings. Every h2/h3 that names a real section is kept;
    # the contents list and the transcriber's notes are not sections.
    SKIP = {"CONTENTS.", "TRANSCRIBER'S NOTE", "MUSIC TRANSCRIBER'S NOTE",
            "APPENDIX.", "FOOTNOTE:"}
    cuts = []
    for m in re.finditer(r"<h([23])[^>]*>(.*?)</h\1>", body, re.S):
        name = clean(m.group(2))
        if name.upper().rstrip(".") in {s.upper().rstrip(".") for s in SKIP}:
            continue
        if re.fullmatch(r"KNOT [IVX]+\.?", name.upper()):
            continue          # the knot number; its title follows as an h3
        cuts.append((m.start(), m.end(), name))

    sections = []
    for i, (a, b, name) in enumerate(cuts):
        stop = cuts[i + 1][0] if i + 1 < len(cuts) else len(body)
        sections.append((name, blocks(body[b:stop])))

    # THE FRONTISPIECE IS PRINTED FACING THE TITLE PAGE, so it falls outside
    # the body entirely and would be lost. Its caption — "at a pace of six
    # miles in the hour" — is a line from the first Knot, which is where it
    # illustrates, so it is placed at the head of that section. (Same move
    # soap-bubbles/ makes with Boys' fold-out thaumatrope, which the 1890
    # book prints at the back.)
    fm = re.search(r"<img\b[^>]*i005[^>]*>", t, re.S)
    if not fm:
        sys.exit("frontispiece i005 not found in the source")
    cap = img_parts(fm.group(0))[1].replace("Frontispiece.", "").strip()
    for name, paras in sections:
        if name.upper().rstrip(".") == "EXCELSIOR":
            paras.insert(0, f"[Figure 1: {cap}]")
            break
    else:
        sys.exit("could not find Knot One to place the frontispiece in")

    # Title the knots and their answers the way the reader will meet them.
    titled = []
    knot = 0
    for name, paras in sections:
        n = name.rstrip(".").strip()
        up = n.upper()
        if up.startswith("ANSWERS TO KNOT "):
            r = up[len("ANSWERS TO KNOT "):].strip()
            n = f"Answers to Knot {WORDNUM[ROMAN.index(r)]}"
        elif up == "ANSWERS TO CORRESPONDENTS":
            n = "Answers to Correspondents"
        elif up in ("TO MY PUPIL", "PREFACE"):
            n = "To My Pupil" if up == "TO MY PUPIL" else "Preface"
        else:
            knot += 1
            n = f"Knot {WORDNUM[knot - 1]}: {titlecase(n)}"
        titled.append((n, paras))

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()
    manifest = []
    divider = None
    for i, (name, paras) in enumerate(titled):
        (CHAPTERS / f"{i:03d}.txt").write_text("\n\n".join(paras) + "\n")
        e = {"file": f"{i:03d}.txt", "title": name, "part": 1, "of": 1,
             "words": sum(len(p.split()) for p in paras)}
        if name.startswith("Knot One") and divider is None:
            e["part_before"] = "The Knots"
            divider = 1
        if name.startswith("Answers to Knot One"):
            e["part_before"] = "The Answers"
        manifest.append(e)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    SITE_IMG.mkdir(parents=True, exist_ok=True)
    for f in SITE_IMG.glob("fig*"):
        f.unlink()
    for n, name in enumerate(PLATES, 1):
        shutil.copy(SRC / "images" / f"{name}.png", SITE_IMG / f"fig{n}.png")

    seen = sorted(int(m) for f in CHAPTERS.glob("*.txt")
                  for m in re.findall(r"\[Figure (\d+)", f.read_text()))
    if seen != list(range(1, len(PLATES) + 1)):
        sys.exit(f"figure markers {seen} do not match the {len(PLATES)} plates")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words, {len(PLATES)} plates")
    for m in manifest:
        if m.get("part_before"):
            print(f"  -- {m['part_before']} --")
        print(f"  {m['file']}  {m['words']:6,}w  {m['title']}")


if __name__ == "__main__":
    main()
