#!/usr/bin/env python3
"""Restore the curly apostrophe in modern title lines.

Fifteen of the 212 tale titles carry U+2019 ("The Hare's Bride", "The
Devil's Sooty Brother", ...), and check.py compares the title line against
the manifest byte for byte, so a straight apostrophe loses the section.
This is a TYPOGRAPHIC repair and nothing else: it only ever rewrites a
line that already matches a manifest title exactly apart from the quote
character, so it cannot mask a real title drift -- that is check.py's job
and this script deliberately cannot do it.
"""
import json
import pathlib
import sys

BOOK = pathlib.Path(__file__).parent
MOD = BOOK / "modern_chapters"


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    fixed = 0
    for m in manifest:
        path = MOD / m["file"]
        if not path.exists():
            continue
        titles = m.get("split_headings") or [m["title"]]
        wanted = {t.replace("’", "'"): t for t in titles
                  if "’" in t}
        if not wanted:
            continue
        lines = path.read_text().split("\n")
        out, hit = [], False
        for line in lines:
            if line in wanted:
                out.append(wanted[line])
                hit = True
                fixed += 1
            else:
                out.append(line)
        if hit:
            path.write_text("\n".join(out))
    print(f"{fixed} title line(s) re-punctuated")


if __name__ == "__main__":
    sys.exit(main())
