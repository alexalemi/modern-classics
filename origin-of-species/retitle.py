#!/usr/bin/env python3
"""Give every origin-of-species file one house heading, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so assemble took
each heading from the file's first line, and the February translators had
used six conventions between them: "I", "II: Variation Under Nature",
"IV. Natural Selection...", "CHAPTER V", "Chapter VIII: Instinct", "XV".
Several files also repeated the title on the lines below the heading
(003 and 004 carry title, numeral, title), which set as h4 duplicates,
and 015's heading had lost Darwin's "—Classification".

The fix: every chapter opens on "Chapter N: <Darwin's title>" -- Arabic,
so assemble.CHAP_LINE sets it as a chapter -- with the title taken from
the source file's own first line, and the duplicate number/title lines
beneath it removed. Front matter (Historical Sketch, Introduction,
Glossary) keeps its own heading. Idempotent: a file that already opens on
its target heading is left alone.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"

# How many leading non-blank lines are heading furniture (number and/or
# title, in whichever of the six conventions the file used).
EAT = {"002.txt": 2, "003.txt": 3, "004.txt": 3, "005.txt": 1,
       "006.txt": 2, "007.txt": 2, "008.txt": 2, "009.txt": 1,
       "010.txt": 2, "011.txt": 1, "012.txt": 2, "013.txt": 1,
       "014.txt": 1, "015.txt": 2, "016.txt": 2}


def roman(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    n = 0
    for a, b in zip(s, s[1:] + " "):
        v = vals[a]
        n += -v if vals.get(b, 0) > v else v
    return n


def source_title(name):
    """Darwin's title, from the source file's first line ("XIV: ...")."""
    first = SRC.joinpath(name).read_text().split("\n", 1)[0].strip()
    m = re.match(r"([IVXL]+): (.*)$", first)
    num, title = roman(m.group(1)), m.group(2)
    # house style: a spaced em dash
    title = re.sub(r"\s*—\s*", " — ", title)
    return f"Chapter {num}: {title}"


def retitle(name, heading, eat):
    path = MOD / name
    lines = path.read_text().split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    if lines[idx[0]].strip() == heading:
        return False
    cut = set(idx[:eat])
    print(f"{name}: {[lines[i].strip()[:50] for i in sorted(cut)]} -> {heading}")
    rest = "\n".join(l for i, l in enumerate(lines)
                     if i not in cut and i > idx[0] - 1).lstrip("\n")
    path.write_text(heading + "\n\n\n" + rest)
    return True


def main():
    names = sorted(p.name for p in SRC.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    manifest = []
    for n in names:
        if n in EAT:
            heading = source_title(n)
            retitle(n, heading, EAT[n])
        else:
            heading = (MOD / n).read_text().split("\n", 1)[0].strip()
        manifest.append({"file": n, "title": heading, "part": 1, "of": 1,
                         "words": len((SRC / n).read_text().split())})
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for m in manifest:
        print(f"  {m['file']}  {m['title']}")


if __name__ == "__main__":
    main()
