#!/usr/bin/env python3
"""Flatland repair (2026-10-10, from the ROADMAP audit of the MODEL=unknown
books). Repeatable: every step checks before it changes anything.

    python3 flatland/retitle.py

1. THE PLATES. Abbott's ten diagrams sat in flatland/images/ and reached
   neither the page nor the epub: the page printed eleven bare
   "[Illustration]" paragraphs. They now go through the collection's figure
   mechanism (assemble.render_figure, build_ebook.copy_figures):
     - images/illustration-N.svg -> site/images/flatland/fig{id}.svg, with
       width/height written from the viewBox so the page does not reflow;
     - FIGURE_DIR=images/flatland in env;
     - chapters/NNN.txt gets the bare marker "[Figure id]" and
       modern_chapters/NNN.txt "[Figure id: caption]", so verify.py's
       figure-parity check (6) guards them from now on.
   The ids are LETTERS, not numbers: Abbott never numbered his plates, and
   Section 1's own prose says "Figure 1 represents the Tradesman ... figures
   2 and 3" of the sub-drawings INSIDE the first plate, so a page label
   "Figure 1" would collide with the author's. A digitless id gets no
   label (assemble.figure_label) and its caption stands alone.
   Two [Illustration] markers have no drawing in images/: the Gutenberg
   cover (chapters/000) and the tailpiece after the last paragraph of
   Section 22. The source keeps them as they are (invisible to the parity
   check); the modern 022 drops its bare marker, which printed as text.
2. The hand-written Contents block in modern 000 disagreed with the real
   headings (it was never the book's; the page has its own Contents), and
   the "FLATLAND / PART I / THIS WORLD" and "PART II / OTHER WORLDS" lines
   duplicated the manifest's Part dividers. Their epigraphs move to the top
   of the Part's first section (001, 013). chapters/ takes the same cuts
   and moves, plus the Gutenberg header, so 000 still compares like with
   like in verify.py.
3. The dedication is set as lined matter (tab-indented) so its line breaks
   survive instead of running together in one paragraph.
4. Six headings used "Section N." where the rest use "Section N:".
5. manifest.json is written from the files' own headings, excluding
   chapters/024.txt (the Gutenberg licence).
"""

import json
import re
import shutil
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
SITE_FIGS = ROOT / "site" / "images" / "flatland"

# (file, svg number, id, caption). Order within a file is document order.
PLATES = [
    ("001", 1, "a", "The Tradesman, an equilateral Triangle, seen three ways: "
     "from above, then with the eye close to the level of the table, then all "
     "but on that level, where he narrows almost to a straight line."),
    ("002", 2, "b", "Plan of a pentagonal house, the two northern sides RO and "
     "OF forming the roof, with the large Men's door on the west and the "
     "small Women's door on the east."),
    ("006", 3, "c", "Recognition by sight: an eye bisects the angle A of a "
     "Triangle on the left and of a Pentagon on the right, and the sides on "
     "either hand are seen shading away into dimness."),
    ("006", 4, "d", "A Hexagon seen side-on: the near side AB appears whole "
     "and bright, while the neighbouring sides, seen as CA and BD, grow dim "
     "toward C and D."),
    ("009", 5, "e", "A Priest, a Circle with his mouth at M, seen by an eye in "
     "line with his diameter AB: he appears as a single straight line CD, half "
     "red and half green."),
    ("013", 6, "f", "The Square's view of Lineland: Men, Women and boys strung "
     "along one line, the King at the centre and the Square above looking "
     "down on them; the King's eyes are drawn much larger than reality, to "
     "show that he could see nothing but a point."),
    ("014", 7, "g", "The Square half out of Lineland, labelled “My body just "
     "before I disappeared,” drawn as a stack of lines rising from the "
     "line of the kingdom, with the King beside it."),
    ("016", 8, "h", "The Sphere rising out of Flatland in three "
     "stages: his section at full size, the Sphere rising, and the Sphere on "
     "the point of vanishing, as seen by the Square's eye on the plane."),
    ("018", 9, "i", "Plan of the Square's pentagonal house: the Hall where his "
     "Wife paces, his study with the Page, his bedroom, his Wife's and "
     "Daughter's apartment, the rooms of his Sons and Grandsons, the Cellar "
     "and the servants, with Policemen at the doors."),
    ("019", 10, "j", "Two drawings of a Cube: one built up of many square "
     "cards stacked one on another, and one as it appears to the Square, an "
     "irregular figure that seems laid open to view."),
]

RETITLE = {  # "Section N." -> "Section N:"
    r"^Section (\d+)\. ": r"Section \1: ",
}

EPIGRAPH_1 = '"Be patient, for the world is broad and wide."'
EPIGRAPH_2 = '"O brave new worlds,\nThat have such people in them!"'


def read(p):
    return p.read_text()


def write(p, text, changed):
    if p.read_text() != text:
        p.write_text(text)
        changed.append(str(p.relative_to(ROOT)))


def copy_plates(changed):
    SITE_FIGS.mkdir(parents=True, exist_ok=True)
    for _, n, pid, _ in PLATES:
        svg = (BOOK / "images" / f"illustration-{n}.svg").read_text()
        if "width=" not in svg.split(">", 1)[0] + ">":
            vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
            w, h = float(vb.group(1)), float(vb.group(2))
            # the drawings were traced at roughly 1.6x their printed size
            k = 0.6
            svg = svg.replace("<svg ", f'<svg width="{round(w * k)}" '
                              f'height="{round(h * k)}" ', 1)
        dest = SITE_FIGS / f"fig{pid}.svg"
        if not dest.exists() or dest.read_text() != svg:
            dest.write_text(svg)
            changed.append(str(dest.relative_to(ROOT)))


def place_markers(changed):
    by_file = {}
    for f, _, pid, cap in PLATES:
        by_file.setdefault(f, []).append((pid, cap))
    for f, plates in by_file.items():
        for kind in ("chapters", "modern_chapters"):
            p = BOOK / kind / f"{f}.txt"
            text = read(p)
            for pid, cap in plates:
                marker = (f"[Figure {pid}]" if kind == "chapters"
                          else f"[Figure {pid}: {cap}]")
                if f"[Figure {pid}" in text:
                    # already placed: refresh a modern caption if it changed
                    if kind == "modern_chapters":
                        text = re.sub(rf"\[Figure {pid}:[^\]]*\]",
                                      lambda m: marker, text)
                    continue
                if "[Illustration]" not in text:
                    raise SystemExit(f"{p}: no [Illustration] left for {pid}")
                text = text.replace("[Illustration]", marker, 1)
            write(p, text, changed)


def fix_022(changed):
    p = BOOK / "modern_chapters" / "022.txt"
    text = read(p)
    text = re.sub(r"\n+\[Illustration\]\s*$", "\n", text)
    write(p, text, changed)


def fix_000(changed):
    p = BOOK / "modern_chapters" / "000.txt"
    text = read(p)
    # the Contents block, through the end of the file (FLATLAND, PART I,
    # THIS WORLD and the Part I epigraph, which moves to 001)
    text = re.sub(r"\n\s*\nContents\n.*\Z", "\n", text, flags=re.S)
    # dedication: lined matter, so its line breaks survive
    lines = text.split("\n")
    try:
        i = lines.index("To")
    except ValueError:
        i = lines.index("\tTo") if "\tTo" in lines else None
    if i is not None:
        j = i
        while j < len(lines) and lines[j].strip():
            if not lines[j].startswith("\t"):
                lines[j] = "\t" + lines[j]
            j += 1
    text = "\n".join(lines).rstrip("\n") + "\n"
    write(p, text, changed)


def add_epigraph(fn, epigraph, changed):
    p = BOOK / "modern_chapters" / fn
    text = read(p)
    if epigraph in text:
        return
    head, rest = text.split("\n", 1)
    text = f"{head}\n\n\n{epigraph}\n\n{rest.lstrip(chr(10))}"
    write(p, text, changed)


def fix_012(changed):
    p = BOOK / "modern_chapters" / "012.txt"
    text = read(p)
    text = re.sub(r"\n\s*\nPART II\nOTHER WORLDS\n.*\Z", "\n", text, flags=re.S)
    write(p, text, changed)


def retitle(changed):
    for p in sorted((BOOK / "modern_chapters").glob("[0-9][0-9][0-9].txt")):
        text = read(p)
        head, rest = text.split("\n", 1)
        for pat, rep in RETITLE.items():
            head = re.sub(pat, rep, head)
        write(p, head + "\n" + rest, changed)


def manifest(changed):
    entries = []
    for p in sorted((BOOK / "modern_chapters").glob("[0-9][0-9][0-9].txt")):
        title = read(p).split("\n", 1)[0].strip()
        n = int(p.stem)
        e = {"file": p.name, "title": title, "part": 1, "of": 1}
        if n == 1:
            e["part_before"] = "Part One: This World"
        if n == 13:
            e["part_before"] = "Part Two: Other Worlds"
        if 1 <= n <= 22:
            e["chapter"] = True
        entries.append(e)
    assert not any(e["file"] == "024.txt" for e in entries)
    out = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    mp = BOOK / "manifest.json"
    if not mp.exists() or mp.read_text() != out:
        mp.write_text(out)
        changed.append(str(mp.relative_to(ROOT)))


def env(changed):
    p = BOOK / "env"
    text = read(p)
    if "FIGURE_DIR=" not in text:
        text = text.rstrip("\n") + "\nFIGURE_DIR=images/flatland\n"
        write(p, text, changed)


SRC_EPI_1 = "“Be patient, for the world is broad and wide.”"
SRC_EPI_2 = "“O brave new worlds,\nThat have such people in them!”"


def fix_source(changed):
    """The same cuts in chapters/, so 000 still compares like with like:
    chapters/000 also carried the Gutenberg header and the Contents, which
    left modern 000 at a ratio of 0.23 once its own Contents went."""
    s0 = BOOK / "chapters" / "000.txt"
    s1 = BOOK / "chapters" / "001.txt"
    s12 = BOOK / "chapters" / "012.txt"
    s13 = BOOK / "chapters" / "013.txt"
    t0 = read(s0)
    if SRC_EPI_1 in t0 and SRC_EPI_1 not in read(s1):
        h, r = read(s1).split("\n", 1)
        write(s1, f"{h}\n\n\n{SRC_EPI_1}\n\n{r.lstrip(chr(10))}", changed)
    t0 = re.sub(r"\A.*?\*\*\* START OF THE PROJECT GUTENBERG EBOOK[^\n]*\n",
                "", t0, flags=re.S)
    t0 = re.sub(r"\n\s*\nContents\n.*\Z", "\n", t0, flags=re.S)
    write(s0, t0.lstrip("\n"), changed)
    t12 = read(s12)
    if SRC_EPI_2 in t12 and SRC_EPI_2 not in read(s13):
        h, r = read(s13).split("\n", 1)
        write(s13, f"{h}\n\n\n{SRC_EPI_2}\n\n{r.lstrip(chr(10))}", changed)
    t12 = re.sub(r"\n\s*\nPART II\nOTHER WORLDS\n.*\Z", "\n", t12, flags=re.S)
    write(s12, t12, changed)


def main():
    changed = []
    copy_plates(changed)
    place_markers(changed)
    fix_source(changed)
    fix_022(changed)
    # the Part I epigraph must be taken from 000 before 000 loses it
    if EPIGRAPH_1 in read(BOOK / "modern_chapters" / "000.txt"):
        add_epigraph("001.txt", EPIGRAPH_1, changed)
    fix_000(changed)
    if EPIGRAPH_2 in read(BOOK / "modern_chapters" / "012.txt"):
        add_epigraph("013.txt", EPIGRAPH_2, changed)
    fix_012(changed)
    retitle(changed)
    manifest(changed)
    env(changed)
    print("\n".join(changed) if changed else "nothing to change")


if __name__ == "__main__":
    main()
