#!/usr/bin/env python3
"""Give every candide file one house heading, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so assemble took
each heading from the file's first line: "CHAPTER 1" for the first file
and "CHAPTER II" ... "CHAPTER XXX" for the rest, with the chapter's title
on a line of its own below, set as an h4. The contents had numbers and no
titles, and one of the numbers in a different system.

The fix merges the two lines into "Chapter N: Title" -- Arabic, which is
what assemble.CHAP_LINE sets as a chapter -- keeping Voltaire's chapter
title as the modern text renders it. 020-024 put a blank line between
number and title, so "the first two NON-BLANK lines" is the rule.
Idempotent: a file already opening on "Chapter N:" is left alone.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"

CHAPTER = re.compile(r"CHAPTER ([IVXL]+|\d+)\.?$")


def number(s):
    if s.isdigit():
        return int(s)
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    n = 0
    for a, b in zip(s, s[1:] + " "):
        v = vals[a]
        n += -v if vals.get(b, 0) > v else v
    return n


def retitle(name):
    path = MOD / name
    lines = path.read_text().split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    first = lines[idx[0]].strip()
    if first.startswith("Chapter "):
        return first
    m = CHAPTER.match(first)
    second = lines[idx[1]].strip()
    assert m and len(second) < 150, (name, first, second)
    heading = f"Chapter {number(m.group(1))}: {second.rstrip('.')}"
    cut = idx[:2]
    print(f"{name}: {[lines[i].strip() for i in cut]} -> {heading}")
    rest = "\n".join(l for i, l in enumerate(lines)
                     if i not in cut and i >= idx[0]).lstrip("\n")
    path.write_text(heading + "\n\n" + rest)
    return heading


def main():
    names = sorted(p.name for p in SRC.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    manifest = [{"file": n, "title": retitle(n), "part": 1, "of": 1,
                 "words": len((SRC / n).read_text().split())} for n in names]
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
