#!/usr/bin/env python3
"""Give every peloponnesian-war file a "Chapter N: Title" line; write manifest.json.

WHY THIS EXISTS (audit of 2026-10-09, ROADMAP.md). The book shipped with
no manifest.json, so assemble took each file's first line as its heading
and the contents read "I / BOOK ONE, PART II / CHAPTER III / CHAPTER 5 /
VI ...": six conventions across 26 chapters, the number alone in the
TOC with Crawley's descriptive title demoted to an h4 underneath, and no
Book dividers at all. The eight Books lived only in the BOOKS table of
the old book-specific assemble.py (kept in this directory, unused).

Every file opens on a number line and then a title line (sometimes with
a blank between). Both are replaced by one "Chapter N: Title" line, which
is what assemble.CHAP_LINE nests as an h3 under its Book divider. The
titles are the translation's own renderings of Crawley's chapter
summaries; 024 had dropped Crawley's "Nineteenth and twentieth years of
the war", restored here so it matches its neighbours.

The Book boundaries were checked against the source: each divider falls
where Thucydides' Book opens (II.1 "The war ... now really begins", V.1
"the truce for a year ended", VIII.1 "Such were the events in Sicily").

The NNN_notes.txt files in modern_chapters/ are translation notes; the
manifest lists only NNN.txt, so neither assemble nor verify reads them.

Idempotent: a file already headed "Chapter N:" is left alone.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"

# (divider, first chapter) — from the old assemble.py BOOKS table.
BOOKS = [
    ("Book One: Origins and Causes", 1),
    ("Book Two: The First Years", 6),
    ("Book Three: Escalation", 9),
    ("Book Four: Turning Points", 12),
    ("Book Five: Uneasy Peace", 15),
    ("Book Six: The Sicilian Expedition", 18),
    ("Book Seven: Catastrophe at Syracuse", 21),
    ("Book Eight: The War in Ionia", 24),
]

TITLE_FIX = {
    24: "Nineteenth and Twentieth Years of the War — Revolt of Ionia — "
        "Intervention of Persia — The War in Ionia",
}

NUMBER = re.compile(r"^(?:BOOK ONE, PART II|(?:CHAPTER )?(?:[IVXLC]+|\d+))$")


def retitle(n):
    path = MOD / f"{n:03d}.txt"
    lines = path.read_text().split("\n")
    if lines[0].startswith(f"Chapter {n}: "):
        return lines[0]
    idx = [i for i, l in enumerate(lines) if l.strip()][:2]
    num, title = (lines[i].strip() for i in idx)
    if not NUMBER.match(num):
        raise SystemExit(f"{path.name}: unexpected number line {num!r}")
    if title.isupper() or len(title) > 200:
        raise SystemExit(f"{path.name}: unexpected title line {title!r}")
    title = TITLE_FIX.get(n, title)
    heading = f"Chapter {n}: {title}"
    rest = lines[idx[1] + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    path.write_text(heading + "\n\n" + "\n".join(rest))
    return heading


# INVENTED SUBHEADINGS (orchestrator ruling, 2026-10-10, as for
# progress-and-poverty). The translating agents wrote ALL-CAPS section
# heads ("THE SPEECH OF CLEON") that the source translation never prints
# -- chapters/ has no such line anywhere -- and applied them unevenly
# across files. They are removed: any paragraph that is one short line in
# capitals. Re-running finds none and changes nothing.
def strip_caps_heads(path):
    text = path.read_text()
    paras = re.split(r"\n\s*\n", text)
    keep = [p for p in paras
            if not (p.strip() and "\n" not in p.strip()
                    and p.strip().isupper() and len(p.strip()) < 90)]
    if len(keep) != len(paras):
        path.write_text("\n\n".join(keep))
    return len(paras) - len(keep)


def main():
    starts = {first: div for div, first in BOOKS}
    manifest = []
    for n in range(1, 27):
        heading = retitle(n)
        entry = {"file": f"{n:03d}.txt", "title": heading, "part": 1, "of": 1}
        if n in starts:
            entry["part_before"] = starts[n]
        manifest.append(entry)
    for n in range(1, 27):
        strip_caps_heads(MOD / f"{n:03d}.txt")
    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
