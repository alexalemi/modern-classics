#!/usr/bin/env python3
"""Per-book checks for hume/ that verify.py structurally cannot make.

    python3 hume/check.py

verify.py sees word ratios, part markers and must_contain phrases. The
defects this book can actually have are all outside that:

  1 HEADING AND PART MARKER against the manifest. The quixote trap: a
    part-2 file whose first line re-introduces the section ships
    silently, because assemble.strip_front drops the first line of
    EVERY file in a group and takes the heading from part 1 only. Six
    of this book's twelve sections are split, so the trap is live in
    more than half of it.

  2 EMPHASIS PARITY. This is the first book that depends on the *marker*
    rendering, and Hume's italics are argument -- the terms he defines,
    the propositions under examination, both definitions of cause. A
    dropped marker is this book's version of a dropped plate. Counted
    per file, and the count must MATCH THE SOURCE exactly: too few means
    an italicised run was lost in a rewrite, too many means emphasis was
    invented, which devalues the rest.

  3 MARKERS MUST BE BALANCED AND WELL-FORMED. An odd count, or a marker
    with a space inside it, produces a run of literal asterisks on the
    page rather than an <em> -- assemble.EMPH refuses to match across a
    leading or trailing space, deliberately, so a malformed marker fails
    OPEN and is visible only here.

  4 NO OTHER MARKUP. The pipeline is markup-free apart from emphasis:
    an ALL-CAPS line is read as a heading and a leading tab as verse or
    a table, and neither belongs anywhere in this book.

  5 THE FLEMING NUMERIC DIFF. Every number in the source must survive in
    the modern file. Hume's numbers are few but they are all load-
    bearing (the fork, the four considerations against miracles, the
    dates of the events he weighs). A number spelled out as a word
    passes the ratio, the markers and must_contain alike.

Exit status is 1 if anything fires -- the euclid-rivals lesson, where
check.py printed its findings and exited 0, and 48 files went through a
`check && commit` chain with a finding in them.
"""
import json
from collections import Counter
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

# A number, with internal separators only. The class form r"\d[\d,./]*"
# lets a figure swallow the SENTENCE comma after it, so "1600," and
# "1600" count as different tokens and every number ending a clause
# fires a false positive. Separators must be followed by a digit.
NUM = re.compile(r"\d+(?:[,./]\d+)*")
MARKER = re.compile(r"\*([^*]*)\*")
PART_DIV = re.compile(r"Part (One|Two|Three|Four)$")

# Numbers in a source file that are deliberately absent from the modern
# one, keyed by file. FILE-SCOPED, as in grimm/ -- never loosen NUM
# itself, which would blind the check everywhere at once.
NUM_EXEMPT = {}


def marker_report(text, where, out):
    n = text.count("*")
    if n % 2:
        out.append(f"{where}: ODD number of emphasis markers ({n}) -- "
                   f"one is unclosed and will render as a literal asterisk")
    for m in MARKER.finditer(text):
        inner = m.group(1)
        if not inner.strip():
            out.append(f"{where}: empty emphasis marker")
        elif inner != inner.strip():
            out.append(f"{where}: emphasis marker has a leading or trailing "
                       f"space -- {inner[:60]!r} will NOT render as <em>")
    return n


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out = []
    part1_head = None

    for m in manifest:
        fn = m["file"]
        src, mod = SRC / fn, MOD / fn
        if not mod.exists():
            continue
        s, t = src.read_text(), mod.read_text()
        lines = [l for l in t.split("\n")]
        nonblank = [l for l in lines if l.strip()]

        # 1 -- heading and part marker
        if not nonblank:
            out.append(f"{fn}: empty")
            continue
        head = nonblank[0].strip()
        if m["part"] == 1:
            part1_head = head
        # The modern heading may retitle the section, but it must be a
        # "Section N: ..." line so assemble.CHAP_LINE sets it as a
        # chapter, and its NUMBER must be the manifest's.
        want_n = m["title"].split(":")[0].strip()
        if not head.startswith(want_n + ":"):
            out.append(f"{fn}: heading is {head!r}, expected it to open "
                       f"{want_n!r}")
        if m["of"] > 1:
            want = f"(Part {m['part']} of {m['of']})"
            if want not in nonblank[1:3]:
                out.append(f"{fn}: missing or misplaced {want}")
            if m["part"] > 1 and head != part1_head:
                # Parts 2+ repeat part 1's heading VERBATIM -- and the
                # comparison is against part 1's MODERN heading, not the
                # manifest's, because assemble.build_sections takes the
                # heading from the file for the modern build (titles=
                # args.original) and only reads manifest titles for the
                # -original companion. So a section may be retitled here,
                # and its later parts must follow the retitling.
                #
                # A part-2 file that renames the section is the quixote
                # bug: strip_front drops the first line of EVERY file in
                # a group, so the wrong line vanishes without trace and
                # the section ships under whatever part 1 happened to say.
                out.append(f"{fn}: part {m['part']} heading {head!r} differs "
                           f"from part 1's {part1_head!r} -- strip_front "
                           f"will hide this")
        elif any(l.strip().startswith("(Part ") for l in nonblank[:3]):
            out.append(f"{fn}: part marker on a single-part file")

        # 2 and 3 -- emphasis
        want_em = marker_report(s, f"{fn} SOURCE", out)
        got_em = marker_report(t, fn, out)
        if want_em != got_em:
            out.append(f"{fn}: {want_em // 2} emphasis spans in source, "
                       f"{got_em // 2} in translation")

        # 4 -- stray markup
        for i, l in enumerate(lines, 1):
            st = l.strip()
            if st.startswith("\t") or l.startswith("\t"):
                out.append(f"{fn}:{i}: leading tab -- renders as verse/table")
            if len(st) > 3 and st == st.upper() and any(c.isalpha() for c in st):
                out.append(f"{fn}:{i}: ALL-CAPS line renders as a heading: "
                           f"{st[:50]!r}")
            if "_" in st:
                out.append(f"{fn}:{i}: underscore renders as emphasis: "
                           f"{st[:50]!r}")

        # 5 -- HUME'S OWN "Part One"/"Part Two" DIVIDERS, per file.
        # The descartes trap: assemble.strip_front deletes a line matching
        # PART_LINE (^Part [IVXLC0-9]+: \S) anywhere in a file's front
        # matter, which is how the Principles of Philosophy lost all four
        # of its Parts off the published page. WORD form dodges the
        # pattern, but only counting them proves it -- and proves equally
        # that a divider was not dropped in translation.
        want_p = [l.strip() for l in s.split("\n") if PART_DIV.match(l.strip())]
        got_p = [l.strip() for l in lines if PART_DIV.match(l.strip())]
        if want_p != got_p:
            out.append(f"{fn}: part dividers {want_p} in source, "
                       f"{got_p} in translation")

        # 6 -- numeric diff
        # COUNTED, not set-differenced. fleming/ compares the SETS, which
        # cannot see a dropped DUPLICATE: Hume states the same date twice
        # in two parallel suppositions in Section Ten, and spelling one of
        # them out passes a set difference untouched because the other
        # survives. Counter subtraction catches it.
        exempt = Counter(NUM_EXEMPT.get(fn, []))
        lost = Counter(NUM.findall(s)) - Counter(NUM.findall(t)) - exempt
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
