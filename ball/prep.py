"""Build chapters/ + manifest.json for Sir Robert Ball's Star-land from the
Project Gutenberg plain text (#60318).

The Royal Institution Christmas courses of 1881 and 1887, worked up into a
book — the FIFTH RI Christmas Lecture volume in the collection, after
soap-bubbles/, candle/, forces/ and fleming/. Six lectures from the sun out
to the nebulae, plus a concluding chapter teaching the constellations.

The cleanest source of the five. No footnotes at all, headings sit at
column 0 in the body and are indented in the contents (so a column-anchored
regex separates them — none of the find_last_line contortions candle/ and
forces/ needed), and every plate carries its own descriptive caption in the
text. Those captions are Ball's own and are often the best jokes in the
book ("This is what we wanted the Cards for"), so unlike soap-bubbles/ they
are CARRIED THROUGH into chapters/ as [Figure N: caption] for the
translator to modernize rather than rewrite from scratch.

FIGURES. 94 plates ship in the -h.zip with page-number filenames
(i_p024.jpg) that carry no figure numbers, so the mapping is recovered from
the HTML edition's per-image captions into image_map.json, and prep copies
them to site/images/ball/figN.jpg. Three plates are special:

  i_f001.jpg  -> front  the frontispiece, a bare "[Illustration]" with no
                        caption at all. (fleming/ shipped a treble clef in
                        place of a line of Morse code because a regex
                        demanded the colon; the caption is optional here.)
  i_p077.jpg  -> 29-30  ONE plate carrying Figs 29 and 30 side by side,
                        "The Phases of the Moon". Hyphenated compound id,
                        as in forces/; assemble renders "Figures 29 and 30".
  figs 35, 64           captioned with their sub-labels FIRST ("Partial.
                        Annular. FIG. 35."), so the number is not at the
                        head of the caption. Search, never match.

Each lecture's body heading is followed by a subtitle line and an indented
synopsis of the lecture's topics. The synopsis is contents material — it
repeats the CONTENTS block verbatim — and is dropped; left in, it would
also render as a <pre> block.

Note the body subtitle for Lecture IV is "JUPITER, SATURN, URANUS,
NEPTUNE." where the contents calls it "THE GIANT PLANETS". The contents
titles are the better ones and are what TITLES uses.

Dropped: the Gutenberg wrapper, the contents, the index, the transcriber's
note. Kept: the preface, and the concluding chapter (which has no LECTURE
heading of its own — see fleming/ for what happens to back matter that
lacks one).

Ratio note for verify: English -> English modernization of spoken lecture
prose, as the other four. Run verify.py with --min-ratio 0.85
--max-ratio 1.3.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 2800
MAX = 3500

LECTURE = re.compile(r"^(LECTURE [IVX]+|CONCLUDING CHAPTER)\.\s*$")
# TWO spaces is enough to mark a preserved block. The concluding chapter's
# six astronomical tables are indented by two, not four, and at a
# four-space threshold every one of them was collapsed into running prose
# ("Mercury | 35.9 | 87.969 | 2,992 | Uncertain. Venus | 67.0 | ...").
INDENTED = re.compile(r"^[ \t]{2,}\S")
ILLUS = re.compile(r"\[Illustration(?::\s*(.*?))?\]", re.S)

TITLES = [
    "Lecture One: The Sun",
    "Lecture Two: The Moon",
    "Lecture Three: The Inner Planets",
    "Lecture Four: The Giant Planets",
    "Lecture Five: Comets and Shooting Stars",
    "Lecture Six: The Stars",
    "How to Name the Stars",
]


def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("_", "")


def strip_wrapper(text):
    text = text.replace("\r\n", "\n")
    text = re.split(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*\n",
                    text, 1)[-1]
    return re.split(r"\n\s*\*\*\* END OF THE PROJECT GUTENBERG EBOOK", text, 1)[0]


def figure_marker(body):
    """[Illustration: FIG. 12.--caption] -> [Figure 12: caption], keeping
    Ball's own caption. The frontispiece is a bare marker; figures 29 and 30
    share one plate; 35 and 64 hide their number behind sub-labels."""
    seen = []

    def sub(m):
        raw = clean(m.group(1) or "")
        if not raw:                       # bare [Illustration]: frontispiece
            seen.append("front")
            return "\n\n[Figure front]\n\n"
        n = re.search(r"FIG\.\s*(\d+)", raw, re.I)
        if not n:
            raise SystemExit(f"unnumbered plate with a caption: {raw[:60]!r}")
        fid = n.group(1)
        if fid == "29":                   # one block, two figure numbers
            fid = "29-30"
        # The caption is whatever is not a "FIG. n.--" label. Strip EVERY
        # label, not just the first: the compound plate carries two, and on
        # 35 and 64 the label sits in the middle with the plate's own
        # sub-labels ("Partial. Annular.") in front of it, which are part
        # of the caption and stay.
        cap = re.sub(r"FIG\.\s*\d+\.?(?:\s*[-—]{1,2})?\s*", "", raw, flags=re.I)
        cap = re.sub(r"\s+", " ", cap).strip().rstrip(".")
        seen.append(fid)
        return f"\n\n[Figure {fid}: {cap}]\n\n" if cap else f"\n\n[Figure {fid}]\n\n"

    return ILLUS.sub(sub, body), seen


def normalise(block):
    """Reflow to one paragraph per line, keeping runs of indented lines
    together as a single block (fleming/: one <pre> per line strews a table
    down the page) and figure markers on their own lines."""
    paras, cur = [], []
    for raw in block.split("\n"):
        line = raw.rstrip()
        if line.strip().startswith("[Figure"):
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(line.strip())
        elif INDENTED.match(line):
            if cur:
                paras.append(" ".join(cur)); cur = []
            if paras and INDENTED.match(paras[-1]):
                paras[-1] += "\n" + line
            else:
                paras.append(line)
        elif line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))

    out = []
    for p in paras:
        if INDENTED.match(p):
            out.append(p)
        elif p.startswith("[Figure"):
            out.append(p)
        else:
            p = clean(p)
            if p:
                out.append(p)
    return "\n\n".join(out)


def split_body(body):
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
                continue          # never orphan a plate at the end of a part
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
    text = strip_wrapper((BOOK / "source.txt").read_text())
    text = re.split(r"\n\s*INDEX\.\s*\n", text, 1)[0]

    marked, placed = figure_marker(text)
    lines = marked.split("\n")

    heads = [i for i, l in enumerate(lines) if LECTURE.match(l)]
    if len(heads) != 7:
        raise SystemExit(f"expected 7 body headings at column 0, got {len(heads)}")

    pre_at = next(i for i, l in enumerate(lines)
                  if l.strip() == "PREFACE TO FIRST EDITION.")
    con_at = next(i for i, l in enumerate(lines) if l.strip() == "CONTENTS.")
    preface = "\n".join(lines[pre_at + 1:con_at])

    # The dedication sits between the copyright notice and the preface. A
    # dedication belongs in the book (a contents does not), and it is the
    # line that says who these lectures were actually for.
    ded_at = next(i for i, l in enumerate(lines) if l.strip() == "To")
    dedication = " ".join(l.strip() for l in lines[ded_at:pre_at] if l.strip())
    if "DEDICATED" not in dedication:
        raise SystemExit("dedication no longer sits before the preface")

    (BOOK / "chapters").mkdir(exist_ok=True)
    front = "\n\n".join(["Front Matter", "Frontispiece", "[Figure front]",
                         "Dedication", dedication,
                         "Preface", normalise(preface)])
    (BOOK / "chapters" / "000.txt").write_text(front + "\n")
    manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
                 "words": body_words(front),
                 "split_headings": ["Frontispiece", "Dedication", "Preface"]}]

    bounds = heads + [len(lines)]
    n = 1
    for k in range(7):
        block = lines[bounds[k] + 1:bounds[k + 1]]
        # skip the ALL-CAPS subtitle and the indented synopsis of topics
        j = 0
        while j < len(block) and (not block[j].strip()
                                  or block[j].strip().isupper()
                                  or block[j].startswith("  ")):
            j += 1
        parts = split_body(normalise("\n".join(block[j:])))
        for i, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({"file": fname, "title": TITLES[k],
                             "part": i, "of": len(parts),
                             "words": body_words(part)})
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # every plate on disk must be placed exactly once, and vice versa
    have = {p.stem[3:] if p.stem.startswith("fig") else p.stem
            for p in (BOOK.parent / "site/images/ball").glob("*.jpg")}
    used = set(placed)
    if len(placed) != len(used):
        dup = [f for f in used if placed.count(f) > 1]
        raise SystemExit(f"plate placed twice: {dup}")
    if have != used:
        raise SystemExit(f"unplaced {sorted(have - used)}; missing {sorted(used - have)}")

    for m in manifest:
        print(f"  {m['file']}  {m['words']:>5}  {m['title']} "
              f"({m['part']}/{m['of']})")
    print(f"{len(manifest)} files, {sum(m['words'] for m in manifest)} words, "
          f"{len(used)} plates placed")


if __name__ == "__main__":
    main()
