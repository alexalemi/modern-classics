#!/usr/bin/env python3
"""Write common-sense/manifest.json.

WHY THIS EXISTS. The book shipped with a legacy `splits` file and no
manifest.json (see CLAUDE.md, "EVERY BOOK NEEDS A REAL manifest.json").
Its headings were already clean -- each file opens on Paine's own section
title in Title Case -- so no file changes; this records the file ->
section mapping explicitly, with each heading asserted rather than
assumed. 000 is Paine's 1776 title page (subjects, epigraph from Thomson,
imprint), which is the pamphlet's own text and stays as its first section.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"
HEADINGS = [
    "Common Sense",
    "Introduction",
    "Of the Origin and Design of Government in General, with Concise "
    "Remarks on the English Constitution",
    "Of Monarchy and Hereditary Succession",
    "Thoughts on the Present State of American Affairs",
    "Of the Present Ability of America, with Some Additional Reflections",
    "Appendix",
]


def main():
    names = sorted(p.name for p in SRC.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    manifest = []
    for n, want in zip(names, HEADINGS, strict=True):
        first = (MOD / n).read_text().lstrip().split("\n", 1)[0].strip()
        assert first == want, (n, first)
        manifest.append({"file": n, "title": first, "part": 1, "of": 1,
                         "words": len((SRC / n).read_text().split())})
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
