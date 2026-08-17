#!/usr/bin/env python3
"""Per-book checks for augustine/ that verify.py structurally cannot make.

    python3 augustine/check.py

The Confessions measures at 35.9 archaisms per 1,000 words, the highest
in this collection — and nearly all of it is ONE grammatical feature,
the second person singular. That makes the central editorial decision
mechanically checkable in a way most books' decisions are not, which is
the reason this file exists.

  1 NO THOU-FAMILY WORD SURVIVES, anywhere, in any register — including
    inside quoted Scripture. The whole point of rendering Pusey's "Thou"
    as "you" is that the book has ONE voice; re-archaising the
    quotations would put a frame around them that Augustine did not put
    there. Exemptions are by EXACT PHRASE, never by loosening the sweep
    (the grimm rule): a blunted check is worse than none, because it
    still reads as coverage.

  2 HEADING AND PART MARKER against the manifest. Thirteen books, ten of
    them split, so the quixote trap — a part-2 file whose first line
    re-introduces the book, silently swallowed by assemble.strip_front —
    is live across most of the volume.

  3 INDENTED-BLOCK PARITY. The source's 23 indented lines are quoted
    verse and Psalms set as lined matter, and prep groups each run into
    one block so assemble renders one <pre> rather than strewing a
    quatrain down the page. A block dissolved into running prose is this
    book's silent summarisation; counted per file, both directions.

  4 NO MARKUP. Augustine has no emphasis at all, so the asterisk count
    must be ZERO — unlike hume/, where 202 markers are load-bearing.
    An ALL-CAPS line renders as a heading and an underscore as <em>.

  5 THE NUMERIC DIFF, COUNTED not set-differenced. A set cannot see a
    dropped DUPLICATE (found in hume/, where the same date is given
    twice in parallel suppositions).

Exit status is 1 if anything fires — the euclid-rivals lesson.
"""
import json
import pathlib
import re
import sys
from collections import Counter

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

NUM = re.compile(r"\d+(?:[,./]\d+)*")

# The whole thou-family, plus the verb forms that only exist to agree
# with it. Deliberately broad: this book's entire justification is that
# removing it is the work.
#
# "art" IS NOT IN THE LIST, and its absence costs nothing. As a verb it
# is the second person singular and CANNOT occur without "thou", which
# the sweep already catches; as a noun it is ordinary modern English,
# and Augustine writes about the art of verse. Including it fired on
# "the art itself, by which I wrote" -- correct prose. When a check
# fires on correct output, fix the check; but fix it by an argument
# about what the rule can actually miss, not by whatever silences it.
THOU = re.compile(
    r"\b(thou|thee|thy|thine|ye|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|mightest|wert|wilt|didst|knowest|madest|"
    r"gavest|sawest|hadst|wast|saith|cometh|goeth|liveth|maketh|giveth|"
    r"unto|whither|whence|thither|hither|betwixt|nay|verily|yea|aught|"
    r"naught|wont|ere|oft|methinks|hearken|behold|thereof|therein|"
    r"whereof|wherein|whereto|thenceforth)\b", re.I)

# EXACT PHRASES that keep an archaic form on purpose. Each needs a
# reason recorded here; the list is matched literally and case-
# sensitively, and never by relaxing THOU itself.
EXEMPT = [
    # (none yet — add with a justification, e.g. a liturgical formula a
    # modern reader knows only in its old wording)
]

IND = re.compile(r"^[ \t]")


def blocks(text):
    """Count runs of consecutive indented lines, as prep grouped them."""
    n, inblock = 0, False
    for line in text.split("\n"):
        if IND.match(line) and line.strip():
            if not inblock:
                n += 1
            inblock = True
        elif not line.strip():
            pass                      # a blank does not close a run here
        else:
            inblock = False
    return n


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out = []
    part1_head = None

    for m in manifest:
        fn = m["file"]
        if not (MOD / fn).exists():
            continue
        s, t = (SRC / fn).read_text(), (MOD / fn).read_text()
        lines = t.split("\n")
        nonblank = [l for l in lines if l.strip()]
        if not nonblank:
            out.append(f"{fn}: empty")
            continue

        # 1 -- the thou family
        scrubbed = t
        for phrase in EXEMPT:
            scrubbed = scrubbed.replace(phrase, "")
        hits = Counter(w.lower() for w in THOU.findall(scrubbed))
        if hits:
            out.append(f"{fn}: archaic forms survive: "
                       + ", ".join(f"{w}x{c}" for w, c in hits.most_common()))

        # 2 -- heading and part marker
        head = nonblank[0].strip()
        if m["part"] == 1:
            part1_head = head
        want_n = m["title"].split(":")[0].strip()
        if not head.startswith(want_n + ":"):
            out.append(f"{fn}: heading is {head!r}, expected it to open "
                       f"{want_n!r}")
        if m["of"] > 1:
            want = f"(Part {m['part']} of {m['of']})"
            if want not in nonblank[1:3]:
                out.append(f"{fn}: missing or misplaced {want}")
            if m["part"] > 1 and head != part1_head:
                out.append(f"{fn}: part {m['part']} heading {head!r} differs "
                           f"from part 1's {part1_head!r} -- strip_front "
                           f"will hide this")
        elif any(l.strip().startswith("(Part ") for l in nonblank[:3]):
            out.append(f"{fn}: part marker on a single-part file")

        # 3 -- indented blocks
        ws, wt = blocks(s), blocks(t)
        if ws != wt:
            out.append(f"{fn}: {ws} indented block(s) in source, {wt} in "
                       f"translation -- verse set as prose, or prose "
                       f"accidentally indented")

        # 4 -- markup
        if "*" in t:
            out.append(f"{fn}: asterisk present; this book has no emphasis")
        for i, l in enumerate(lines, 1):
            st = l.strip()
            if len(st) > 3 and st == st.upper() and any(c.isalpha() for c in st):
                out.append(f"{fn}:{i}: ALL-CAPS line renders as a heading: "
                           f"{st[:50]!r}")
            if "_" in st:
                out.append(f"{fn}:{i}: underscore renders as emphasis")

        # 5 -- numbers, counted
        lost = Counter(NUM.findall(s)) - Counter(NUM.findall(t))
        if lost:
            out.append(f"{fn}: numbers in source, missing or fewer in "
                       f"translation: {sorted(lost.elements())}")

    done = sum(1 for m in manifest if (MOD / m["file"]).exists())
    print(f"checked {done}/{len(manifest)} translated files")
    for line in out:
        print("  " + line)
    if out:
        print(f"\n{len(out)} finding(s)")
        sys.exit(1)
    print("clean")


if __name__ == "__main__":
    main()
