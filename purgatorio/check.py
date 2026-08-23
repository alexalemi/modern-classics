"""Per-book checks for purgatorio/ — the euclid-rivals pattern.

verify.py sees word ratios, part markers and must_contain phrases. It
cannot see any of the following.

  1 VERSE INTEGRITY, and it is the decisive check for this book, exactly
    as in boethius/. The Purgatorio is 4,755 lines in 33 cantos, and its
    shape is not decoration: a citation is a canto and a line number
    (Purg. XXX.55), the tercet is the unit Dante thought in, and the line
    counts (136, 133, 145, 139, ...) are facts about the poem rather
    than about any translation of it. So the tercet COUNT, the line
    count WITHIN each tercet, and the total per canto are all compared
    exactly against chapters/. Dissolving a tercet into prose, or
    quietly merging two lines into one, is this book's silent
    summarisation, and the word ratio barely moves when it happens.

  2 EVERY LINE IS TAB-INDENTED. A line that loses its tab stops being
    verse: assemble.py renders the block as a paragraph and joins the
    lines into running prose, so ONE missing tab silently converts a
    tercet into a sentence. Nothing else in the toolchain can see it.

  3 HEADING PARITY against the manifest, and no all-caps line anywhere
    (assemble.py reads an all-caps line as a section heading).

  4 THE MARKUP SWEEP. This pipeline is markup-free apart from emphasis,
    and the Italian carries no emphasis at all, so any asterisk or
    underscore in a modern file is either a literal that will ship as
    itself or a marker that will not render. Asked of assemble.EMPH
    itself, not an approximation of it (the boethius lesson).

  5 THE AUGUSTINE THOU-SWEEP. Longfellow's crib is 28.7 archaisms per
    1,000 words and sits open beside the translator all day; the whole
    point of this edition is not to sound like him. Anything the sweep
    finds is the translator drifting into the crib.

MEASURED AND NOT INCLUDED, so it is not re-tried blind: the fleming
numeric diff. The Italian text contains ZERO digit tokens -- Dante
spells every number as a word -- so a token diff would be entirely
inert, and an inert check that looks like coverage is worse than no
check (the nights/ lesson, where the same measurement was made only
after the check had been shipped). What guards a lost number here is
line parity plus the line-aligned crib.

Exits NONZERO on any finding.
"""
import json
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK.parent))
import assemble                                              # noqa: E402

SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

THOU = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|wert|wilt|didst|knowest|seest|saith|ere|"
    r"whilst|amongst|betwixt|nay|methinks|perchance|oft|'tis|"
    r"thereunto|whereupon|hereunto|whereof|thereof|unto|'gainst)\b", re.I)

# BY EXACT PHRASE, NEVER BY LOOSENING THE SWEEP (the grimm rule).
ARCHAIC_OK = []


def tercets(text):
    body = text.split("\n", 1)[1]
    return [[l for l in b.split("\n") if l.strip()]
            for b in re.split(r"\n\s*\n", body) if b.strip()]


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out = []
    done = 0

    for m in manifest:
        fn = where = m["file"]
        if not (MOD / fn).exists():
            continue
        done += 1
        text = (MOD / fn).read_text()
        src = (SRC / fn).read_text()
        lines = text.split("\n")

        # 3 -- heading
        if lines[0].strip() != m["title"]:
            out.append(f"{where}: heading {lines[0].strip()!r} != manifest "
                       f"{m['title']!r}")
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if len(s) > 3 and s == s.upper() and any(c.isalpha() for c in s):
                out.append(f"{where}:{i}: all-caps line renders as a "
                           f"heading -- {s[:50]!r}")

        # 1 -- verse integrity, exact
        st, dt = tercets(src), tercets(text)
        if len(st) != len(dt):
            out.append(f"{where}: {len(dt)} tercets, source has {len(st)}")
        else:
            bad = [(i + 1, len(d), len(s)) for i, (s, d) in
                   enumerate(zip(st, dt)) if len(s) != len(d)]
            if bad:
                out.append(f"{where}: tercet line counts differ -- "
                           + ", ".join(f"#{i} has {d}, source {s}"
                                       for i, d, s in bad[:6]))
        ns, nd = sum(len(t) for t in st), sum(len(t) for t in dt)
        if ns != nd:
            out.append(f"{where}: {nd} lines, source has {ns}")

        # 2 -- every verse line keeps its tab
        for i, line in enumerate(lines[1:], 2):
            if line.strip() and not line.startswith("\t"):
                out.append(f"{where}:{i}: line is not indented, so it will "
                           f"render as prose -- {line.strip()[:50]!r}")

        # 4 -- markup sweep, via the renderer itself
        for i, line in enumerate(assemble.EMPH.sub("", text).split("\n"), 1):
            if "*" in line or "_" in line:
                out.append(f"{where}:{i}: stray markup that does NOT "
                           f"render -- {line.strip()[:60]!r}")

        # 5 -- archaism
        found = sorted({w.lower() for w in THOU.findall(text)})
        keep = [w for w in found
                if not any(p in text and w in p.lower() for p in ARCHAIC_OK)]
        if keep:
            out.append(f"{where}: archaic forms survive: {', '.join(keep)}")

    print(f"checked {done}/{len(manifest)} translated files")
    for line in out:
        print("  " + line)
    if out:
        print(f"\n{len(out)} finding(s)")
        sys.exit(1)
    print("clean")


if __name__ == "__main__":
    main()
