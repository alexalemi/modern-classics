#!/usr/bin/env python3
"""Per-book checks for boethius/ that verify.py structurally cannot make.

    python3 boethius/check.py

verify.py sees word ratios, part markers and must_contain phrases. This
book's real failure modes are all outside that, and most of them live in
the verse:

  1 THE VERSE IS WHERE LOSS HIDES. Thirty-nine songs, 39,360 words in
    the whole book: a dropped LINE moves the word ratio by nothing at
    all, and a song quietly flattened into prose moves it by nothing
    either. So three things are checked per file and all three must
    match the source exactly:
      - the number of indented BLOCKS (a song dissolved into prose);
      - the number of indented LINES (a dropped line or stanza);
      - the INDENT PATTERN, i.e. which lines are the deeper-indented
        ones. The source marks the shorter line of each couplet that
        way, so the pattern IS the metrical shape. Matching it proves
        the couplets survived, which counting alone does not.
    grimm/ counts blocks and deliberately not lines, because there a
    re-lineation was a legitimate choice. HERE IT IS NOT: this edition
    commits to keeping Boethius' line structure, so any deviation is a
    decision that must be logged in running_notes, not absorbed
    silently by a loose tool.

  2 EVERY SONG KEEPS ITS HEADING AND ITS NUMBER. The songs are numbered
    independently of the prose chapters and offset from them (Book One
    chapter I carries Song II), so a heading quietly renumbered to match
    its chapter would look plausible and be wrong. Checked against the
    source's own labels, in order.

  3 NO THOU-FAMILY WORD SURVIVES. James's Victorian surface is most of
    the measured archaism, and removing it is most of the job. The
    augustine/ rule: exemptions by EXACT PHRASE, never by loosening the
    sweep.

  4 EMPHASIS PARITY against the source, per file (hume/), plus the
    counted numeric diff, plus a sweep for markup that does not belong.

Exit status is 1 if anything fires — the euclid-rivals lesson, where a
check printed its findings and returned success for 48 files.
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
MARKER = re.compile(r"\*([^*]*)\*")
SONG = re.compile(r"^Song ([IVXL]+)(?::|$)")

# "art" is deliberately absent: as a verb it is second person singular
# and cannot occur without "thou", which the sweep already catches; as a
# noun it is ordinary modern English. The augustine/ reasoning.
THOU = re.compile(
    r"\b(thou|thee|thy|thine|ye|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|mightest|wert|wilt|didst|knowest|seest|saith|"
    r"cometh|goeth|liveth|maketh|giveth|lieth|hadst|wast|"
    r"unto|whither|whence|thither|hither|betwixt|nay|verily|yea|aught|"
    r"naught|ere|oft|ofttimes|erstwhile|haply|wot|ween|behold|thereof|"
    r"therein|whereof|wherein|thenceforth|vouchsafe|peradventure)\b", re.I)

EXEMPT = []          # exact phrases only, each with a reason recorded here


def verse(text):
    """(blocks, [indent-depth per line]) for the indented runs."""
    blocks, depths, inblock = 0, [], False
    for line in text.split("\n"):
        if line.startswith("\t") and line.strip():
            if not inblock:
                blocks += 1
            inblock = True
            depths.append(len(line) - len(line.lstrip("\t")))
        elif not line.strip():
            pass                       # a blank does not close a run
        else:
            inblock = False
    return blocks, depths


def marker_report(text, where, out):
    n = text.count("*")
    if n % 2:
        out.append(f"{where}: ODD number of emphasis markers ({n})")
    for m in MARKER.finditer(text):
        inner = m.group(1)
        if not inner.strip():
            out.append(f"{where}: empty emphasis marker")
        elif inner != inner.strip():
            out.append(f"{where}: marker has a leading/trailing space -- "
                       f"{inner[:50]!r} will NOT render as <em>")
    return n


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out = []

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

        # 1 -- verse blocks, line count, and the couplet indent pattern
        sb, sd = verse(s)
        tb, td = verse(t)
        if sb != tb:
            out.append(f"{fn}: {sb} verse block(s) in source, {tb} in "
                       f"translation -- a song set as prose, or split")
        elif len(sd) != len(td):
            out.append(f"{fn}: {len(sd)} verse lines in source, {len(td)} in "
                       f"translation -- a line or stanza has moved")
        elif sd != td:
            first = next(i for i, (a, b) in enumerate(zip(sd, td)) if a != b)
            out.append(f"{fn}: couplet indent pattern differs at verse line "
                       f"{first + 1} (source depth {sd[first]}, "
                       f"translation {td[first]})")

        # 2 -- song headings, by number and in order
        want = [x for x in (SONG.match(l.strip()) for l in s.split("\n")) if x]
        got = [x for x in (SONG.match(l.strip()) for l in lines) if x]
        if [x.group(1) for x in want] != [x.group(1) for x in got]:
            out.append(f"{fn}: song numbers {[x.group(1) for x in want]} in "
                       f"source, {[x.group(1) for x in got]} in translation")

        # heading must open with the manifest's own chapter/song number
        head = nonblank[0].strip()
        want_n = m["title"].split(":")[0].strip()
        if not head.startswith(want_n):
            out.append(f"{fn}: heading is {head!r}, expected it to open "
                       f"{want_n!r}")

        # 3 -- the thou family
        scrubbed = t
        for phrase in EXEMPT:
            scrubbed = scrubbed.replace(phrase, "")
        hits = Counter(w.lower() for w in THOU.findall(scrubbed))
        if hits:
            out.append(f"{fn}: archaic forms survive: "
                       + ", ".join(f"{w}x{c}" for w, c in hits.most_common()))

        # 4 -- emphasis, markup, numbers
        we = marker_report(s, f"{fn} SOURCE", out)
        ge = marker_report(t, fn, out)
        if we != ge:
            out.append(f"{fn}: {we // 2} emphasis spans in source, "
                       f"{ge // 2} in translation")
        for i, l in enumerate(lines, 1):
            st = l.strip()
            if len(st) > 3 and st == st.upper() and any(c.isalpha() for c in st):
                out.append(f"{fn}:{i}: ALL-CAPS line renders as a heading: "
                           f"{st[:50]!r}")
            if "_" in st:
                out.append(f"{fn}:{i}: underscore renders as emphasis")
        lost = Counter(NUM.findall(s)) - Counter(NUM.findall(t))
        if lost:
            out.append(f"{fn}: numbers in source, missing or fewer in "
                       f"translation: {sorted(lost.elements())}")

    done = sum(1 for m in manifest if (MOD / m["file"]).exists())
    songs = sum(len([1 for l in (MOD / m["file"]).read_text().split("\n")
                     if SONG.match(l.strip())])
                for m in manifest if (MOD / m["file"]).exists())
    print(f"checked {done}/{len(manifest)} translated files; {songs} songs")
    if done == len(manifest) and songs != 39:
        out.append(f"whole book: {songs} songs, expected 39")
    for line in out:
        print("  " + line)
    if out:
        print(f"\n{len(out)} finding(s)")
        sys.exit(1)
    print("clean")


if __name__ == "__main__":
    main()
