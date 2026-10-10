#!/usr/bin/env python3
"""Write meditations/manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json (see CLAUDE.md,
"EVERY BOOK NEEDS A REAL manifest.json"). Its headings were already
consistent -- each file opens on "Book I" ... "Book XII", which is not a
PART_LINE and so is not deleted by strip_front -- so no file changes; this
only records the file -> section mapping explicitly, with each heading
asserted rather than assumed.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"
ROMAN = "I II III IV V VI VII VIII IX X XI XII".split()


def main():
    names = sorted(p.name for p in SRC.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    manifest = []
    for k, n in enumerate(names):
        first = (MOD / n).read_text().lstrip().split("\n", 1)[0].strip()
        assert first == f"Book {ROMAN[k]}", (n, first)
        manifest.append({"file": n, "title": first, "part": 1, "of": 1,
                         "words": len((SRC / n).read_text().split())})
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
