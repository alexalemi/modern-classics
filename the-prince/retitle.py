#!/usr/bin/env python3
"""Give every the-prince file one house heading, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so assemble took
each heading from the file's first line: a bare "CHAPTER XVIII." The
chapter's title sat on the next line in capitals and was set as an h4 in
the body, so the contents read "CHAPTER I." to "CHAPTER XXVI." with no
titles at all.

The fix merges the two lines into "Chapter N: Title" -- Arabic, which is
what assemble.CHAP_LINE sets as a chapter -- using the title as the
modern text renders it (not Marriott's 1908 wording), title-cased. The
dedication's heading "DEDICATION" becomes "Dedication"; its "To the
Magnificent Lorenzo de' Medici" line is the dedication's own address and
stays. Idempotent: a file already opening on "Chapter N:" is left alone.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"

CHAPTER = re.compile(r"CHAPTER ([IVXL]+)\.?$")
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
         "into", "of", "on", "or", "over", "the", "to", "upon", "with"}


def roman(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    n = 0
    for a, b in zip(s, s[1:] + " "):
        v = vals[a]
        n += -v if vals.get(b, 0) > v else v
    return n


def titlecase(s):
    """Rebuild an ALL-CAPS title in Title Case (democracy2/retitle.py)."""
    words = s.strip().rstrip(".").split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        first = i == 0 or i == len(words) - 1 or out[-1].endswith(":")
        if low in SMALL and not first:
            out.append(low)
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in low.split("-")))
    return " ".join(out)


def retitle(name):
    path = MOD / name
    lines = path.read_text().split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    first = lines[idx[0]].strip()
    if first.startswith("Chapter ") or first == "Dedication":
        return first
    if first == "DEDICATION":
        heading, cut = "Dedication", idx[:1]
    else:
        m = CHAPTER.match(first)
        second = lines[idx[1]].strip()
        assert m and second.isupper(), (name, first, second)
        heading = f"Chapter {roman(m.group(1))}: {titlecase(second)}"
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
