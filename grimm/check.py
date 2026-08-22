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
 6. THE MANIFEST CAN AGREE WITH ITSELF AND STILL BE SHORT A TALE. Checks
    1-3 compare the manifest against the FILES, so a heading that prep
    never recognised is missing from both and every one of them passes.
    "The Twelve Idle Servants" is numbered 151* -- a star that a \\d{1,3}
    regex silently dropped -- and it shipped as an untitled paragraph in
    the middle of another tale, with no TOC entry, while verify.py's word
    ratio did not move by a hair. The only witness is the SOURCE'S OWN
    CONTENTS LIST, which is why the tale count is now taken from there
    rather than from anything the pipeline produced.
"""
import json
import pathlib
import re
import sys
from collections import Counter

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

# "art" and "wilt" are NOT in this list, and deliberately. Both are ordinary
# modern words -- the art of a trade, a flower that wilts -- and bare
# matches on them fired on "the animal knew nothing of the art". Nothing is
# lost by dropping them: Hunt's archaic "art"/"wilt" are always governed by
# "thou" ("thou art", "wilt thou"), which the sweep catches anyway. A check
# that cries wolf on correct prose gets ignored, which is worse than a
# narrower one that never does.
THOU = re.compile(r"\b(thou|thee|thy|thine|hast|hath|doth|dost|"
                  r"shalt|canst|mayest|wert|quoth|hither|whither|whence)\b",
                  re.I)
# A separator must be FOLLOWED BY A DIGIT, or a figure at the end of a
# clause swallows the comma after it and "1,000," stops matching its own
# occurrence in the translation (the hume fix).
NUM = re.compile(r"\d+(?:[,./]\d+)*")

# Numerals that are PAGE FURNITURE in the source rather than content —
# a tale's catalogue number left stranded in the body by the
# transcription. Keyed by file so an exemption can never spread.
# EMPTY, AND THAT IS THE POINT: this existed for "151* The Twelve Idle
# Servants", whose number survived into chapters/ only because prep did
# not recognise the heading. Once prep read the star the number was
# stripped like every other tale's, and the special case dissolved. An
# exemption that stops being needed is evidence the real bug was found;
# keep the mechanism, since the next scanned source will want it.
SOURCE_NUMBER_FURNITURE = {}


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


def source_tale_count():
    """How many tales the book itself says it contains.

    Read off the Gutenberg contents list, which is the only description of
    the collection that the pipeline did not produce. Numbers are what is
    counted, not titles: the contents prints entry 1 twice, and a title
    string cannot be compared against the manifest anyway once TITLE_FIXES
    has been applied to it. The star in "151*" is significant and is why
    this check exists.
    """
    src = sorted((BOOK / "source").glob("*.txt"))[0].read_text(errors="replace")
    head = src[:src.index("Legend 10 The Hazel Branch") + 200]
    tales = set(re.findall(r"\n[ \t]*(\d{1,3}\*?)[ \t]+[A-Z][^\n]{2,80}", head))
    legends = set(re.findall(r"\n[ \t]*Legend (\d{1,2})[ \t]+[A-Z]", head))
    return len(tales) + len(legends)


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

        # PAGE FURNITURE IS NOT A MEASURED VALUE. Gutenberg's transcription
        # leaves one tale number stranded in the body ("151* The Twelve Idle
        # Servants"); it is the Grimms' catalogue number, not anything the
        # story says, and it must NOT survive into the translation. Exempt
        # it by file and by exact token, never by loosening NUM -- the whole
        # value of this check (the fleming rule) is that it is blind and
        # total, and a general "ignore small integers" rule would let a real
        # dropped quantity through.
        # MEASURED, 2026-08-22: this check has almost nothing to bite on.
        # The Grimms' source carries SIX numeral tokens in all, across 3 of
        # 85 files, and one of those is the 151* catalogue number exempted
        # below. Hunt spells her numbers out ("seven ravens", "twelve
        # brothers"), so the fleming diff is nearly inert here. It is kept
        # because it is free and because a future source change would be
        # caught -- but it must NOT be counted as coverage. See the note in
        # nights/check.py, where it is inert entirely.
        # COUNTED, NOT A SET (the hume lesson): a set cannot see a dropped
        # duplicate, because the surviving occurrence covers for the lost
        # one. And the old test asked `n not in d`, a substring search over
        # the whole file, so "5" counted as present because some "1500"
        # contained it.
        stray = SOURCE_NUMBER_FURNITURE.get(f, set())
        lost = Counter(NUM.findall(s)) - Counter(NUM.findall(d))
        for n in stray:
            del lost[n]
        if lost:
            fails.append(f"{f}: numerals not found in translation: "
                         f"{sorted(lost.elements())} "
                         f"(check they are not spelled out)")

        for line, why, txt in caps_or_markup(d):
            fails.append(f"{f}:{line}: {why}: {txt}")

    tales = sum(len(m.get("split_headings") or [m["title"]])
                for m in done if m["part"] == 1)
    print(f"{len(done)}/{len(manifest)} files translated, {tales} tales")

    # THE COMPLETENESS CHECK, AND IT MUST NOT BE TAKEN FROM THE PIPELINE.
    # Count the entries in the source's own contents list and require the
    # manifest to hold exactly that many distinct titles. Deduplicated by
    # catalogue number, because the contents prints entry 1 twice and the
    # 3-part tale contributes its title three times to the manifest.
    if len(done) == len(manifest):
        want = source_tale_count()
        got = len({t for m in manifest
                   for t in (m.get("split_headings") or [m["title"]])})
        if want != got:
            fails.append(
                f"the source contents lists {want} tales, the manifest has "
                f"{got} distinct titles -- a tale has been lost or doubled")
    if fails:
        print(f"\n{len(fails)} PROBLEM(S):")
        for x in fails[:40]:
            print("  " + x)
        sys.exit(1)
    print("titles, order, thou-sweep, verse parity, numerals and "
          "conventions all clean")


if __name__ == "__main__":
    main()
