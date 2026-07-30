"""Build chapters/ + manifest.json for Faraday's On the Various Forces of
Nature from the Project Gutenberg plain text (#52293).

The six Christmas 1859-60 lectures to a juvenile audience at the Royal
Institution — the course Faraday gave the year BEFORE the Candle — with
the "Light-house Illumination: the Electric Light" address the edition
appends, and William Crookes's preface and notes, as in candle/.

FIGURES. Unlike the Candle, this Gutenberg package ships its plates: the
-h.zip carries 50 images covering 59 numbered figures, because Victorian
books routinely print several figures on one block. Plates are copied to
site/images/forces/ named for every figure they carry, joined by hyphens
(fig_015_016_017.jpg -> fig15-16-17.jpg), and the markers match:

    [Figure 15-16-17]   ->  rendered "Figures 15, 16 and 17"

The text's own grouping does NOT agree with the plates' grouping, so the
markers are driven by the FILES, not by the "[Illustration: ...]" lines:

  - fig15-16-17 is one plate, but the text marks it as two illustrations
    ("Fig. 15." and "Fig. 16. and Fig. 17."). The plate is emitted once,
    at the first of those, and the second marker is dropped — otherwise
    the same image appears twice.
  - figures 18 and 19 are two separate plates but a single text marker
    ("Fig. 18. and Fig. 19."); both are emitted there, in order.
  - fig29 has NO illustration marker at all. It is referenced only in
    prose, in lower case — "if I take a piece of platinum of that size
    (fig. 29)" — which is where it is inserted, confirmed against the
    Gutenberg HTML edition's own placement.

Dropped from the source: the title page, the contents, the trailing
publisher's advertisements (everything after "THE END."), and the
decorative colophon illustration.
Kept and MOVED: Crookes's 24 notes, all of which are anchored in the body
("[7]"). As in candle/, each is cut loose from its print-page heading and
inlined as its own "Editor's note: ..." paragraph after the paragraph
that cites it.

Ratio note for verify: English -> English modernization of spoken
Victorian lecture prose, as in candle/ (0.99) and soap-bubbles/ (1.02).
Run verify.py with --min-ratio 0.85 --max-ratio 1.3.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
SITE_IMAGES = BOOK.parent / "site" / "images" / "forces"
TARGET = 2800
MAX = 3500

GUT_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
ILLUS = re.compile(r"\[Illustration:\s*(Fig[^\]]*)\]", re.S)
ANCHOR = re.compile(r"\[(\d+)\]")
SUBHEAD_CAP = re.compile(r"^[A-Z][A-Z \-,.']{6,}$")

# heading in the body -> title for the manifest, from the book's contents
SECTIONS = [
    ("LECTURE I.", "Lecture One: The Force of Gravitation"),
    ("LECTURE II.", "Lecture Two: Gravitation and Cohesion"),
    ("LECTURE III.", "Lecture Three: Cohesion and Chemical Affinity"),
    ("LECTURE IV.", "Lecture Four: Chemical Affinity and Heat"),
    ("LECTURE V.", "Lecture Five: Magnetism and Electricity"),
    ("LECTURE VI.", "Lecture Six: The Correlation of the Physical Forces"),
    ("LIGHT-HOUSE ILLUMINATION--THE ELECTRIC LIGHT.",
     "Lighthouse Illumination: The Electric Light"),
]

# the one plate the text never marks; inserted after the paragraph that
# mentions it in prose (lower-case "fig. 29"), per the HTML edition
ORPHAN = ("29", re.compile(r"\(fig\.\s*29\)", re.I))


def strip_wrapper(text):
    return GUT_START.split(text, 1)[-1]


def clean(s):
    return re.sub(r"\s+", " ", s).strip().replace("_", "")


def find_line(lines, needle, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip() == needle:
            return i
    raise SystemExit(f"heading not found: {needle!r}")


def find_last_line(lines, needle, end):
    """Last occurrence before `end`. Every lecture heading appears three
    times — in the contents, in the body, and again as a section header
    inside the notes — so the body one is the last before NOTES."""
    for i in range(end - 1, -1, -1):
        if lines[i].strip() == needle:
            return i
    raise SystemExit(f"heading not found before line {end}: {needle!r}")


def plate_ids():
    """Every plate on disk, as its hyphen-joined figure id, ordered by first
    figure number: ['1', '2', '3-4', ..., '15-16-17', '18', '19', ...]."""
    ids = [p.stem[3:] for p in SITE_IMAGES.glob("fig*.jpg")]
    return sorted(ids, key=lambda i: [int(x) for x in i.split("-")])


def figure_markers(block, plates, placed):
    """Replace each [Illustration: Fig. ...] with markers for whichever
    plates carry those figure numbers and have not been emitted yet."""
    def sub(m):
        nums = {int(x) for x in re.findall(r"\d+", m.group(1))}
        out = []
        for pid in plates:
            if pid in placed:
                continue
            if {int(x) for x in pid.split("-")} & nums:
                placed.add(pid)
                out.append(f"[Figure {pid}]")
        return "\n\n" + "\n\n".join(out) + "\n\n" if out else "\n\n"
    return ILLUS.sub(sub, block)


def normalise(block, notes, plates, placed):
    block = figure_markers(block, plates, placed)

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
        cited = ANCHOR.findall(p)
        out.append(ANCHOR.sub("", p))
        for n in cited:
            if n in notes:
                out.append(f"Editor's note: {notes[n]}")
        # the unmarked plate goes with the paragraph that names it
        pid = ORPHAN[0]
        if pid not in placed and ORPHAN[1].search(p):
            placed.add(pid)
            out.append(f"[Figure {pid}]")
    return "\n\n".join(out)


def read_notes(lines, notes_at):
    body = "\n".join(lines[notes_at:])
    notes = {}
    # the notes are grouped under per-lecture headers ("LECTURE II."), which
    # must end a note as surely as the next note does
    for m in re.finditer(r"^\[(\d+)\] (.*?)(?=\n\[\d+\] |\n\s*LECTURE |\nTHE END|\Z)",
                         body, re.S | re.M):
        text = clean(m.group(2))
        text = re.sub(r"^Pages? [\d and]+\.\s*", "", text)
        notes[m.group(1)] = text
    return notes


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

    preface_at = find_line(lines, "PREFACE.")
    contents_at = find_line(lines, "CONTENTS.", preface_at)
    preface = "\n".join(lines[preface_at + 1:contents_at])

    notes_at = find_line(lines, "NOTES.", contents_at)
    bounds = [find_last_line(lines, needle, notes_at) for needle, _ in SECTIONS]
    if bounds != sorted(bounds):
        raise SystemExit(f"section headings out of order: {bounds}")
    bounds.append(notes_at)
    notes = read_notes(lines, notes_at)

    plates, placed = plate_ids(), set()

    front = "\n\n".join(["Front Matter", "Preface",
                         normalise(preface, notes, plates, placed)])
    (BOOK / "chapters").mkdir(exist_ok=True)
    (BOOK / "chapters" / "000.txt").write_text(front + "\n")
    manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
                 "words": body_words(front), "split_headings": ["Preface"]}]

    n = 1
    for i, (needle, title) in enumerate(SECTIONS):
        block = lines[bounds[i] + 1:bounds[i + 1]]
        # the next section's heading is set over several centred lines
        # ("LECTURE" / "ON" / "LIGHT-HOUSE ILLUMINATION..."); the boundary
        # only catches the last, so trim the orphaned words above it
        while block and (not block[-1].strip()
                         or re.fullmatch(r"[A-Z]{2,10}", block[-1].strip())):
            block.pop()
        # drop the ALL-CAPS argument line under the lecture heading
        j = 0
        while j < len(block) and not block[j].strip():
            j += 1
        if j < len(block) and SUBHEAD_CAP.match(block[j].strip()):
            j += 1
        parts = split_body(normalise("\n".join(block[j:]), notes, plates, placed))
        for k, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({"file": fname, "title": title,
                             "part": k, "of": len(parts),
                             "words": body_words(part)})
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    missing = [p for p in plates if p not in placed]
    print(f"{len(manifest)} files, {sum(e['words'] for e in manifest)} words, "
          f"{len(placed)}/{len(plates)} plates placed, {len(notes)} notes")
    if missing:
        print("UNPLACED PLATES:", missing)
    for e in manifest:
        print(f"  {e['file']}  {e['words']:>5}  {e['title'][:48]} "
              f"({e['part']}/{e['of']})")


if __name__ == "__main__":
    main()
