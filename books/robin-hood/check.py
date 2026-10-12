"""Per-book checks for robin-hood that verify.py cannot make.

    python3 books/robin-hood/check.py

1. THE COSTUME IS OFF. Pyle's mock-Elizabethan ("thou", "quoth", "marry",
   "-eth" verbs...) is swept for in every modern file. Exempt BY EXACT
   PHRASE only, never by loosening the sweep: the Kirklees epitaph, the
   beggars' cant, and the titles Pyle lettered into his plates (inside
   [Figure ...] markers, which are stripped before the sweep).
2. Headings: line 1 of every file is the manifest title; "(Part n of k)"
   on line 3 for split chapters and nowhere else.
3. Plates: every [Figure id] in chapters/ appears in the same file of
   modern_chapters/ in the same ORDER (verify.py compares the set).
4. Italics: underscores balance per paragraph; no "Footnote:" paragraph
   survives; no "--" double hyphen; no ALL-CAPS opening words.
Exits nonzero on any failure.
"""

import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).parent
MOD = BOOK / "modern_chapters"
SRC = BOOK / "chapters"

COSTUME = re.compile(
    r"\bmarry[,!]|\b(thou|thee|thy|thine|ye|quoth|wot|ween|trow|eke|anon|fain|"
    r"prythee|prithee|methinks|mayhap|perchance|forsooth|whilst|betwixt|"
    r"'tis|'twas|hath|doth|dost|hast|art thou|nay|yea|ay|aye|ere|"
    r"wouldst|shouldst|couldst|canst|wilt|shalt|thyself)\b"
    r"|\b\w+(?<!s)eth\b(?<!\bteeth)(?<!\bbeneath)(?<!\bdeath)(?<!\bbreath)"
    r"(?<!\bSeth)(?<!\bheath)(?<!\bwreath)(?<!\bsheath)(?<!\bElizabeth)"
    r"(?<!\bnineteenth)(?<!\btwentieth)(?<!\bthirtieth)(?<!\bfortieth)"
    r"(?<!\bfiftieth)(?<!\bsixtieth)(?<!\bseventieth)(?<!\beightieth)"
    r"(?<!\bninetieth)(?<!\bMacbeth)(?<!\bunderneath)",
    re.I)

# exact phrases where the old form is the point (see text_analysis.txt)
EXEMPT = [
    "HEAR UNDERNEAD DIS LAITL STEAN LAIS ROBERT EARL OF HUNTINGTUN NEA ARCIR "
    "VER AS HIE SAE GEUD AN PIPL KAULD IM ROBIN HEUD SICK UTLAWS AS HI AN IS "
    "MEN VIL ENGLAND NIDIR SI AGEN OBIIT 24 KAL. DEKEMBRIS 1247",
]

FIG = re.compile(r"\[Figure ([A-Za-z0-9_]+)(?::[^\]]*)?\]")


def main():
    fails = []
    manifest = json.loads((BOOK / "manifest.json").read_text())
    hits = {}
    for e in manifest:
        f = MOD / e["file"]
        if not f.exists():
            continue
        text = f.read_text()
        lines = text.split("\n")
        if lines[0].strip() != e["title"]:
            fails.append(f"{e['file']}: heading {lines[0]!r} != {e['title']!r}")
        mark = f"(Part {e['part']} of {e['of']})"
        if e["of"] > 1 and (len(lines) < 3 or lines[2].strip() != mark):
            fails.append(f"{e['file']}: line 3 should be {mark}")
        if e["of"] == 1 and re.search(r"^\(Part \d+ of \d+\)$", text, re.M):
            fails.append(f"{e['file']}: stray part marker")
        src_figs = FIG.findall((SRC / e["file"]).read_text())
        mod_figs = FIG.findall(text)
        if src_figs != mod_figs:
            fails.append(f"{e['file']}: plates {mod_figs} != source {src_figs}")
        body = FIG.sub("", text)
        for ex in EXEMPT:
            body = body.replace(ex, "")
        for i, par in enumerate(re.split(r"\n\s*\n", body)):
            if par.count("_") % 2:
                fails.append(f"{e['file']}: unbalanced _ in paragraph {i}")
            if par.startswith("Footnote:"):
                fails.append(f"{e['file']}: Footnote paragraph survives")
            if re.match(r"\s*[A-Z]{3,} [A-Z]{2,}", par) and i > 0:
                fails.append(f"{e['file']}: ALL CAPS opening: {par[:30]!r}")
        if "--" in body:
            fails.append(f"{e['file']}: double hyphen")
        for m in COSTUME.finditer(body):
            hits.setdefault(e["file"], []).append(
                body[max(0, m.start() - 30):m.end() + 30].replace("\n", " "))
    for f, hs in hits.items():
        for h in hs:
            fails.append(f"{f}: costume? ...{h}...")
    for x in fails:
        print(x)
    print(f"{len(fails)} problem(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
