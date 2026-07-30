"""Build chapters/ + manifest.json for C. V. Boys' Soap-Bubbles and the
Forces Which Mould Them from the Project Gutenberg plain text (#33370).

THE PROJECT'S FIRST ILLUSTRATED VOLUME. Boys' three lectures are a
demonstration course: the text makes ~150 references to 69 numbered
figures ("the apparatus in Fig. 22"), and the argument is unreadable
without them. Gutenberg's HTML edition ships every plate as
images/figNN.jpg; those are copied to site/images/soap-bubbles/ and the
figures are carried through the pipeline as plain-text markers so that
chapters/ and modern_chapters/ stay pure text files:

    [Figure 22]                 <- what prep.py emits (source side)
    [Figure 22: caption text]   <- what the translation writes

assemble.py turns the latter into <figure><img><figcaption>, and
verify.py checks that the set of figure numbers in a modern file matches
its source file exactly (a figure silently dropped is the illustrated
analogue of silent summarization).

Structure: front matter (dedication + preface), three lectures, and the
"Practical Hints" appendix. Lectures are untitled in the original
("LECTURE II."); the manifest gives them descriptive modern titles.

Source quirks handled:
  - the frontispiece plate (front.jpg) has a real caption and no number;
    it becomes [Figure front: ...] in the front-matter file
  - Fig. 35 (the thaumatrope: 43 photos of a falling drop) was a fold-out
    at the END of the 1890 book, reached via a [Sidenote: See Diagram at
    the end of the Book]. A web reader wants it where it is discussed, so
    the marker is moved inline to the sidenote's position and the trailing
    plate is dropped.
  - fig39b.jpg is not a figure but the scale bar ("thousandths of an
    inch") belonging to Fig. 39's photomicrograph; it is emitted as
    [Figure 39b] immediately after [Figure 39] so it stays bound to it.
  - two [Footnote N: ...] blocks become inline "(Note: ...)" paragraphs
    (assemble.py has no footnote machinery, and both are asides).
  - Practical Hints is divided by _Italic Subheadings._; the underscores
    are stripped so assemble.py's title-case-line rule renders them as
    subheadings, and part splits are forced onto those boundaries so no
    apparatus recipe is cut in half.

Ratio note for verify: this is English -> English modernization of
Victorian lecture prose. Long periodic sentences break into shorter
modern ones at close to 1:1; run verify.py with --min-ratio 0.85
--max-ratio 1.3. Figure markers are excluded from word counts.
"""

import json
import re
import shutil
from pathlib import Path

BOOK = Path(__file__).parent
SITE_IMAGES = BOOK.parent / "site" / "images" / "soap-bubbles"
TARGET = 2600
MAX = 3300

GUT_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
GUT_END = re.compile(r"\*\*\* ?END OF THE PROJECT GUTENBERG")

# Section heads, in body order. Lecture I's head is the running title.
SECTIONS = [
    ("PREFACE.", None),
    ("SOAP-BUBBLES, AND THE FORCES WHICH MOULD THEM.", "Lecture One"),
    ("LECTURE II.", "Lecture Two"),
    ("LECTURE III.", "Lecture Three"),
    ("PRACTICAL HINTS.", "Practical Hints"),
    ("THE END.", None),
]

TITLES = {
    "Lecture One": "Lecture One: The Elastic Skin of Water",
    "Lecture Two": "Lecture Two: The Shapes a Bubble Can Take",
    "Lecture Three": "Lecture Three: Singing Fountains and Bubbles Inside Bubbles",
    "Practical Hints": "Practical Hints: How to Do These Experiments Yourself",
}

FRONTISPIECE = re.compile(
    r"\[Illustration: (Experiment for showing.*?)\]", re.S)
ILLUS = re.compile(r"\[Illustration:\s*Fig\.\s*(\d+)\.?\s*(.*?)\]", re.S)
SIDENOTE_35 = re.compile(r"\[Sidenote:.*?Fig\.\s*35\.\]", re.S)
FOOTNOTE = re.compile(r"\[Footnote\s*\d+:\s*(.*?)\]", re.S)
SUBHEAD = re.compile(r"^_([A-Z][^_]*?)\._$")


def strip_wrapper(text):
    text = GUT_START.split(text, 1)[-1]
    return GUT_END.split(text, 1)[0]


def find_line(lines, needle, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip() == needle:
            return i
    raise SystemExit(f"heading not found: {needle!r}")


def normalise(block):
    """Reflow hard-wrapped paragraphs, strip underscore-italics, and turn
    the source's bracket markers into pipeline markers. Bracket blocks and
    subheadings are kept as their own paragraphs so splits can see them."""
    block = FRONTISPIECE.sub(lambda m: f"\n\n[Figure front: {clean(m.group(1))}]\n\n",
                             block)
    block = SIDENOTE_35.sub("\n\n[Figure 35]\n\n", block)
    # "Note: ..." must end in a period, not a bracket: assemble.py reads a
    # short unpunctuated line with majority-capitalised words as a heading.
    block = FOOTNOTE.sub(lambda m: f"\n\nNote: {clean(m.group(1))}\n\n", block)

    def figure(m):
        num, cap = m.group(1), clean(m.group(2))
        marker = f"[Figure {num}: {cap}]" if cap else f"[Figure {num}]"
        if num == "39":
            marker += "\n\n[Figure 39b]"
        return f"\n\n{marker}\n\n"

    block = ILLUS.sub(figure, block)

    paras, cur = [], []
    for raw in block.split("\n"):
        line = raw.strip()
        sub = SUBHEAD.match(line)
        if sub:                       # Practical Hints subheading
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(sub.group(1))
        elif line.startswith("[Figure") or line.startswith("(Note:"):
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(line)
        elif line:
            cur.append(line)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(clean(p) for p in paras if p.strip())


def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("_", "")


def split_body(body):
    """Cut into near-equal parts, snapping each cut to the best nearby
    paragraph boundary rather than the first one past quota (which badly
    unbalances the tail). A cut may not leave a figure marker stranded at
    the end of a part, and a Practical Hints subheading is a strongly
    preferred cut point so no apparatus recipe is split in half."""
    paras = body.split("\n\n")
    words = [len(p.split()) for p in paras]
    total = sum(words)
    if total <= MAX:
        return [body]
    nparts = max(2, round(total / TARGET))
    per = total / nparts

    cum = [0]
    for w in words:
        cum.append(cum[-1] + w)

    def cost(i, target):
        if paras[i - 1].startswith("[Figure"):
            return None                      # would orphan a figure
        d = abs(cum[i] - target)
        return d * 0.25 if SUBHEAD.match(paras[i]) else d

    cuts, lo = [], 1
    for k in range(1, nparts):
        target = k * per
        best, best_c = None, None
        for i in range(lo, len(paras)):
            c = cost(i, target)
            if c is not None and (best_c is None or c < best_c):
                best, best_c = i, c
        cuts.append(best)
        lo = best + 1

    edges = [0] + cuts + [len(paras)]
    return ["\n\n".join(paras[a:b]) for a, b in zip(edges, edges[1:])]


def body_words(text):
    """Word count ignoring figure markers (they are not prose)."""
    stripped = re.sub(r"^\[Figure[^\]]*\]$", "", text, flags=re.M)
    return len(stripped.split())


def main():
    lines = strip_wrapper((BOOK / "source.txt").read_text()).split("\n")

    bounds = []
    at = 0
    for needle, _ in SECTIONS:
        at = find_line(lines, needle, at)
        bounds.append(at)

    # Everything before the dedication is the 1896 title page plus the
    # Gutenberg transcriber note: dropped (site/template.html renders the
    # title, author and date). Only the frontispiece plate is kept.
    dedication_at = find_line(lines, "TO")
    head = "\n".join(lines[:dedication_at])
    frontispiece = FRONTISPIECE.search(head)
    dedication = "\n".join(lines[dedication_at:bounds[0]])
    preface = "\n".join(lines[bounds[0] + 1:bounds[1]])

    # "Frontispiece" is a split_heading of its own: assemble.py discards
    # whatever precedes the first split heading in a front-matter file, so
    # the plate needs a heading above it to survive.
    front = "\n\n".join(x for x in [
        "Front Matter",
        "Frontispiece",
        f"[Figure front: {clean(frontispiece.group(1))}]" if frontispiece else "",
        "Dedication",
        normalise(dedication),
        "Preface",
        normalise(preface),
    ] if x)

    sections = [("front", front)]
    for i, (needle, name) in enumerate(SECTIONS):
        if name is None:
            continue
        block = "\n".join(lines[bounds[i] + 1:bounds[i + 1]])
        sections.append((name, normalise(block)))

    (BOOK / "chapters").mkdir(exist_ok=True)
    manifest, n = [], 0
    for name, text in sections:
        if name == "front":
            (BOOK / "chapters" / "000.txt").write_text(text + "\n")
            manifest.append({
                "file": "000.txt", "title": "Front Matter",
                "part": 1, "of": 1, "words": body_words(text),
                "split_headings": ["Frontispiece", "Dedication", "Preface"],
            })
            n = 1
            continue
        parts = split_body(text)
        for k, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({
                "file": fname, "title": TITLES[name],
                "part": k, "of": len(parts), "words": body_words(part),
            })
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    figs = sorted({m.group(1) for m in re.finditer(
        r"\[Figure (\S+?)[:\]]", "\n".join(
            (BOOK / "chapters" / e["file"]).read_text() for e in manifest))})
    missing = [f for f in figs
               if not (SITE_IMAGES / f"fig{f}.jpg").exists()
               and not (f == "front" and (SITE_IMAGES / "front.jpg").exists())]
    print(f"{len(manifest)} files, {sum(e['words'] for e in manifest)} words, "
          f"{len(figs)} figures")
    if missing:
        print("MISSING IMAGES:", missing)
    for e in manifest:
        print(f"  {e['file']}  {e['words']:>5}  {e['title']} "
              f"({e['part']}/{e['of']})")


if __name__ == "__main__":
    main()
