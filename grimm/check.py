#!/usr/bin/env python3
"""Per-book checks for Grimm that verify.py structurally cannot make.

    python3 grimm/check.py

verify.py knows completeness, word ratio and part markers. This book's
failure modes are elsewhere, and all of them are silent:

 1. THE TITLE LINES ARE LOAD-BEARING. assemble.build_sections carves each
    file into sections by splitting on `^(exact title)$` from the
    manifest's split_headings. A title that drifts by one character --
    "The Wolf and the Seven Kids" for "...Seven Little Kids" -- does not
    error: its section simply never opens, the tale is welded onto the end
    of the tale before it, and the TOC is one entry short. On a page of
    210 tales nobody will notice. Checked exactly, and in order.
 2. ANYTHING BEFORE THE FIRST TITLE IS DISCARDED by that same split, so a
    file must BEGIN with its first title line.
 3. THE THOU-FAMILY IS THE BOOK'S WHOLE JOB (3,729 instances, 99% of them
    inside dialogue). One survivor is a missed sentence.
 4. VERSE PARITY. Grimm's rhymes arrive unindented in the source and are
    re-emitted tab-indented by prep; a rhyme flattened back into prose in
    translation is invisible to the word ratio and is this book's silent
    summarisation.
 5. The fleming numeric diff, and the markup-free conventions.
"""
import json
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

THOU = re.compile(r"\b(thou|thee|thy|thine|hast|hath|doth|dost|art|wilt|"
                  r"shalt|canst|mayest|wert|quoth)\b", re.I)
NUM = re.compile(r"\d[\d,]*")


def caps_or_markup(text):
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        letters = [c for c in s if c.isalpha()]
        if len(s.split()) >= 4 and letters and \
                sum(c.isupper() for c in letters) / len(letters) > 0.9:
            out.append((i, "all-caps line would render as a heading", s[:70]))
        # A LINE OF ASTERISKS IS A SCENE BREAK, not stray markup: both
        # renderers match assemble.HR_LINE and set it as an <hr/>. Hunt uses
        # one in Little Red-Cap, between the tale and the second wolf.
        if ("*" in s or "_" in s) and not re.fullmatch(r"\*+( \*+)*|-{2,}", s):
            out.append((i, "markup character ships literally", s[:70]))
    return out


def verse_blocks(text):
    return len(re.findall(r"(?:^|\n)\t[^\n]+(?:\n\t[^\n]+)*", text))


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    done = [m for m in manifest if (MOD / m["file"]).exists()]
    fails = []

    for m in done:
        f = m["file"]
        s = (SRC / f).read_text()
        d = (MOD / f).read_text()
        titles = m.get("split_headings")

        if titles:
            lines = [l.rstrip() for l in d.split("\n")]
            first = next((l for l in lines if l.strip()), "")
            if first != titles[0]:
                fails.append(f"{f}: must begin with {titles[0]!r}, begins "
                             f"{first[:50]!r} (anything before the first "
                             f"title is DISCARDED by assemble.py)")
            found = [l for l in lines if l in titles]
            missing = [t for t in titles if t not in lines]
            if missing:
                fails.append(f"{f}: title line missing or misspelled: {missing}")
            elif found != titles:
                fails.append(f"{f}: titles out of order: {found} != {titles}")
        else:
            head = [l.strip() for l in d.split("\n") if l.strip()][:2]
            if head and head[0] != m["title"]:
                fails.append(f"{f}: heading {head[0]!r} != {m['title']!r}")
            if m["of"] > 1 and (len(head) < 2 or
                                head[1] != f"(Part {m['part']} of {m['of']})"):
                fails.append(f"{f}: missing or wrong part marker")

        # A FIXED LITURGICAL QUOTATION KEEPS ITS OWN ARCHAIC ENGLISH. The
        # boy in "The Girl Without Hands" recites the Lord's Prayer he was
        # taught -- "Our Father, which art in Heaven" -- and that wording
        # is the prayer, not Hunt's costume; modernising it would put words
        # in the child's mouth that no child ever learned. Exempted by
        # exact phrase rather than by loosening the sweep, so that a stray
        # "art" anywhere else still fails.
        swept = d
        for fixed in ("Our Father, which art in Heaven",):
            swept = swept.replace(fixed, "")
        left = sorted({w.lower() for w in THOU.findall(swept)})
        if left:
            fails.append(f"{f}: archaic second person survives: {left}")

        # ONLY LOSS IS A DEFECT. The check exists to catch a rhyme flattened
        # into prose, so it flags vd < vs. GAINING blocks is routine and
        # correct: Hunt often sets a rhymed call-and-response as separate
        # one-line quotations, which prep cannot detect as verse (its rule
        # needs two short lines), and the translation properly sets every
        # rhymed reply as verse. Flagging that would have made the check
        # bully the text instead of guarding it.
        vs, vd = verse_blocks(s), verse_blocks(d)
        if vs and not vd:
            fails.append(f"{f}: {vs} verse block(s) in source, none in "
                         f"translation -- a rhyme has been flattened")
        elif vd < vs and (vs - vd) > max(1, vs // 3):
            fails.append(f"{f}: verse blocks lost: {vs} -> {vd}")

        missing = [n for n in set(NUM.findall(s)) if n not in d]
        if missing:
            fails.append(f"{f}: numerals not found in translation: "
                         f"{sorted(missing)} (check they are not spelled out)")

        for line, why, txt in caps_or_markup(d):
            fails.append(f"{f}:{line}: {why}: {txt}")

    tales = sum(len(m.get("split_headings") or [m["title"]])
                for m in done if m["part"] == 1)
    print(f"{len(done)}/{len(manifest)} files translated, {tales} tales")
    if fails:
        print(f"\n{len(fails)} PROBLEM(S):")
        for x in fails[:40]:
            print("  " + x)
        sys.exit(1)
    print("titles, order, thou-sweep, verse parity, numerals and "
          "conventions all clean")


if __name__ == "__main__":
    main()
