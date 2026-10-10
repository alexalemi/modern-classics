#!/usr/bin/env python3
"""Give every federalist file one house heading, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so verify.py
paired every file in chapters/ -- including 000 (the Project Gutenberg
header) and 086 (the Gutenberg licence), which have no translation and
never should -- and reported both MISSING. The headings were all-caps
"FEDERALIST No. N".

The fix: a manifest of the 85 papers (001-085) only, with 000 and 086
left on disk and out of it; and each paper's first line becomes
"Federalist No. N". The paper's title, dateline and author lines below it
are left exactly as the text has them (they set as h4). Idempotent.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"
DROP = {"000.txt", "086.txt"}   # Gutenberg header and licence


def retitle(name):
    path = MOD / name
    lines = path.read_text().split("\n")
    i = next(k for k, l in enumerate(lines) if l.strip())
    n = int(name[:3])
    want = f"Federalist No. {n}"
    if lines[i].strip() != want:
        assert lines[i].strip() == f"FEDERALIST No. {n}", (name, lines[i])
        lines[i] = want
        path.write_text("\n".join(lines))
    return want


def main():
    names = sorted(p.name for p in SRC.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name) and p.name not in DROP)
    manifest = [{"file": n, "title": retitle(n), "part": 1, "of": 1,
                 "words": len((SRC / n).read_text().split())} for n in names]
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(manifest)} papers")


if __name__ == "__main__":
    main()
