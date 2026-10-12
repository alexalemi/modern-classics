#!/usr/bin/env python3
"""Give every malthus file one house heading, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so assemble took
each heading from the file's first line: "CHAPTER 1" ... "CHAPTER 19",
and for 000 the book's own title, so the contents opened on a second copy
of the title page that site/template.html already sets.

Malthus gave his chapters no titles, only a dash-separated summary of
contents, which the modern text keeps as the chapter's first paragraph.
A summary is far too long to be a contents entry, and a short title cut
from it would be ours, not his. So the chapters are headed "Chapter N",
sentence case, and set flat (no colon, so not assemble.CHAP_LINE; the
book has no Parts for them to nest under). 000's title-page lines (title,
subtitle, author, "London, 1798") are the edition's furniture, duplicated
by the page's own title block; the file now opens on "Preface", which is
what the rest of it is. Idempotent.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"
CHAPTER = re.compile(r"CHAPTER (\d+)$")


def retitle(name):
    path = MOD / name
    text = path.read_text()
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    first = lines[idx[0]].strip()
    if first == "Preface" or re.fullmatch(r"Chapter \d+", first):
        return first
    if name == "000.txt":
        # everything up to and including the "Preface" line
        stop = next(i for i in idx if lines[i].strip() == "Preface")
        cut = [i for i in idx if i <= stop]
        heading = "Preface"
    else:
        m = CHAPTER.match(first)
        assert m, (name, first)
        heading, cut = f"Chapter {int(m.group(1))}", idx[:1]
    print(f"{name}: {[lines[i].strip()[:40] for i in cut]} -> {heading}")
    rest = "\n".join(l for i, l in enumerate(lines)
                     if i not in cut and i > cut[-1]).lstrip("\n")
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
