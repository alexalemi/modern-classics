"""Build chapters/ + manifest.json for Faraday's The Chemical History of a
Candle from the Project Gutenberg plain text (#14474).

The six Christmas 1860-61 lectures to a juvenile audience at the Royal
Institution — the most famous course in the tradition Boys' Soap Bubbles
belongs to — plus the separate Lecture on Platinum (Royal Institution,
22 February 1861) that Crookes appended to this edition.

FIGURES. Gutenberg's transcription keeps the illustration captions but
NOT the woodcuts: pg14474-h.zip contains one image, the cover. The 38
plates come instead from Wikisource/Commons, where they are filed as
"Chemical History of a Candle FigureNN" — with an inconsistent naming
scheme worth knowing about: figures 1-35 (the Candle proper) are
zero-padded with no space ("Figure01"), while 36-38 (the Platinum
lecture, a separate Wikisource page) have a space and no padding
("Figure 36"). They are PNG line art, not JPEG, which is why the figure
pipeline resolves plate extensions rather than assuming .jpg. Downloaded
to site/images/candle/figN.png; see DEVLOG for the fetch script.

Dropped from the source, deliberately:
  - the table of contents (a list of the arguments, which become the
    manifest titles instead)
  - each lecture's ALL-CAPS argument line under its heading — it is
    carried by the manifest title, and an all-caps line left in the body
    would be read as a section heading by assemble.py
Kept: Crookes's preface, which is a small essay in its own right, and his
19 explanatory notes — but MOVED. In the original they sit in a block at
the back, anchored by "[7]"-style markers and headed by print page
numbers ("Page 186"). A reflowable edition has no page 186 and no
footnote machinery, so each note is cut loose from its page reference and
inlined as its own "Editor's note: ..." paragraph directly after the
paragraph that cites it. The anchors are removed. Note 16 is unanchored
in the source and is dropped.

Ratio note for verify: English -> English modernization of spoken
Victorian lecture prose, same as soap-bubbles. Run verify.py with
--min-ratio 0.85 --max-ratio 1.3.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
SITE_IMAGES = BOOK.parent / "site" / "images" / "candle"
TARGET = 2800
MAX = 3500

GUT_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
GUT_END = re.compile(r"\*\*\* ?END OF THE PROJECT GUTENBERG")
ILLUS = re.compile(r"\[Illustration:\s*Fig\.\s*(\d+)\.?\s*(.*?)\]", re.S)

# Faraday's own arguments, retitled for a modern reader. The originals are
# in the source's table of contents; these keep his sequence exactly.
SECTIONS = [
    ("LECTURE I.", "Lecture One: A Candle — the Flame, Its Sources, Structure, Movement and Brightness"),
    ("LECTURE II.", "Lecture Two: Brightness of the Flame — the Air a Candle Needs, and the Water It Makes"),
    ("LECTURE III.", "Lecture Three: The Products — Water from the Burning, What Water Is Made Of, and Hydrogen"),
    ("LECTURE IV.", "Lecture Four: Hydrogen in the Candle Burns into Water — and Oxygen, the Other Half of Water"),
    ("LECTURE V.", "Lecture Five: Oxygen in the Air — What the Atmosphere Is, and Carbonic Acid"),
    ("LECTURE VI.", "Lecture Six: Carbon and Coal Gas — Breathing, and How Like a Candle It Is"),
    ("LECTURE ON PLATINUM.", "Lecture on Platinum"),
]


# Source defect. Lecture V anchors note 16 as "[14]", so note 14 (on the
# electricity needed to decompose water) was being inlined a second time in
# a passage about testing for oxygen, and note 16 — which names the test gas
# Faraday never identifies, binoxide of nitrogen — never appeared at all.
SOURCE_FIXES = [
    ("told by its association with this other substance[14]",
     "told by its association with this other substance[16]"),
]


def strip_wrapper(text):
    text = GUT_START.split(text, 1)[-1]
    for wrong, right in SOURCE_FIXES:
        if wrong not in text:
            raise SystemExit(f"source fix no longer applies: {wrong!r}")
        text = text.replace(wrong, right)
    return GUT_END.split(text, 1)[0]


def clean(s):
    return re.sub(r"\s+", " ", s).strip().replace("_", "")


def find_line(lines, needle, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip() == needle:
            return i
    raise SystemExit(f"heading not found: {needle!r}")


def drop_argument(lines):
    """Drop the ALL-CAPS argument line(s) that follow a lecture heading."""
    j = 0
    while j < len(lines) and not lines[j].strip():
        j += 1
    # the argument runs until the first blank line after it
    if j < len(lines) and lines[j].strip().isupper():
        while j < len(lines) and lines[j].strip():
            j += 1
    return lines[j:]


ANCHOR = re.compile(r"\[(\d+)\]")


def normalise(block, notes=None):
    block = ILLUS.sub(lambda m: f"\n\n[Figure {m.group(1)}]\n\n", block)
    paras, cur = [], []
    for raw in block.split("\n"):
        line = raw.strip()
        if line.startswith("[Figure"):
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(line)
        elif line:
            cur.append(line)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))

    out = []
    for p in paras:
        p = clean(p)
        if not p:
            continue
        cited = ANCHOR.findall(p) if notes else []
        out.append(ANCHOR.sub("", p))
        for n in cited:                 # Crookes's note follows what cites it
            if n in notes:
                out.append(f"Editor's note: {notes[n]}")
    return "\n\n".join(out)


def read_notes(lines, notes_at):
    """{number: text} from the NOTES block, with the leading print-page
    reference ("Page 186.") stripped — it means nothing in a reflowable
    edition."""
    body = "\n".join(lines[notes_at:])
    notes = {}
    for m in re.finditer(r"\[Footnote (\d+):(.*?)\]\s*\n", body, re.S):
        text = clean(m.group(2))
        text = re.sub(r"^Page \d+\.\s*", "", text)
        notes[m.group(1)] = text
    return notes


def split_body(body):
    """Near-equal parts, snapped to the nearest paragraph boundary, never
    leaving a figure marker stranded at the end of a part."""
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

    cuts, lo = [], 1
    for k in range(1, nparts):
        target = k * per
        best, best_d = None, None
        for i in range(lo, len(paras)):
            if paras[i - 1].startswith("[Figure"):
                continue
            d = abs(cum[i] - target)
            if best_d is None or d < best_d:
                best, best_d = i, d
        cuts.append(best)
        lo = best + 1
    edges = [0] + cuts + [len(paras)]
    return ["\n\n".join(paras[a:b]) for a, b in zip(edges, edges[1:])]


def body_words(text):
    return len(re.sub(r"^\[Figure[^\]]*\]$", "", text, flags=re.M).split())


def main():
    lines = strip_wrapper((BOOK / "source.txt").read_text()).split("\n")

    preface_at = find_line(lines, "PREFACE")
    contents_at = find_line(lines, "CONTENTS.", preface_at)
    preface = "\n".join(lines[preface_at + 1:contents_at])

    # The contents list every lecture heading verbatim, so the search for
    # body headings has to start after the half-title, not after CONTENTS.
    body_at = find_line(lines, "THE CHEMICAL HISTORY OF A CANDLE", contents_at)

    bounds = []
    at = body_at
    for needle, _ in SECTIONS:
        at = find_line(lines, needle, at + 1)
        bounds.append(at)
    # Crookes's notes close the book; they are lifted out and inlined
    notes_at = find_line(lines, "NOTES.", bounds[-1])
    bounds.append(notes_at)
    notes = read_notes(lines, notes_at)

    front = "\n\n".join(["Front Matter", "Preface", normalise(preface)])

    (BOOK / "chapters").mkdir(exist_ok=True)
    (BOOK / "chapters" / "000.txt").write_text(front + "\n")
    manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
                 "words": body_words(front), "split_headings": ["Preface"]}]

    n = 1
    for i, (needle, title) in enumerate(SECTIONS):
        block = drop_argument(lines[bounds[i] + 1:bounds[i + 1]])
        parts = split_body(normalise("\n".join(block), notes))
        for k, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({"file": fname, "title": title,
                             "part": k, "of": len(parts),
                             "words": body_words(part)})
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    figs = sorted({int(m.group(1)) for m in re.finditer(
        r"\[Figure (\d+)\]", "\n".join(
            (BOOK / "chapters" / e["file"]).read_text() for e in manifest))})
    missing = [f for f in figs if not (SITE_IMAGES / f"fig{f}.png").exists()]
    print(f"{len(manifest)} files, {sum(e['words'] for e in manifest)} words, "
          f"{len(figs)} figures (1-{max(figs)})")
    if missing:
        print("MISSING IMAGES:", missing)
    for e in manifest:
        print(f"  {e['file']}  {e['words']:>5}  {e['title'][:52]} "
              f"({e['part']}/{e['of']})")


if __name__ == "__main__":
    main()
