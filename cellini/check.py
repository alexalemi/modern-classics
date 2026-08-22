"""Per-book checks for cellini/ — the euclid-rivals pattern.

verify.py sees word ratios, part markers and must_contain phrases. It
cannot see any of the following.

  1 CHAPTER-LABEL PARITY, and it is the decisive check for this book.
    241 chapters are grouped five or six to a file, and each keeps its
    "Chapter N" label on its own line. A label that goes missing does
    not lose a word: it silently WELDS TWO CHAPTERS INTO ONE, so the
    prose reads perfectly, the ratio does not move, and every citation
    after it in that file points at the wrong chapter. The labels are
    compared as an exact ordered list against chapters/.

  2 VERSE INTEGRITY for the Proem and the Capitolo — stanza count, line
    count within each stanza, and the tab that makes a line verse at
    all. One lost tab turns the sonnet into a paragraph (boethius).

  3 HEADING PARITY against the manifest, and no all-caps line anywhere
    (assemble.py reads one as a section heading). Headings must also be
    UNIQUE across the book, because the anchor is the slugified
    heading and both Books have a chapter 97.

  4 THE MARKUP SWEEP, asked of assemble.EMPH itself rather than an
    approximation of it (the boethius lesson). The Italian carries no
    emphasis, so any asterisk or underscore is either a literal that
    will ship as itself or a marker that will not render.

  5 THE augustine THOU-SWEEP. Symonds sits open beside the translator
    all day and is thoroughly Victorian; anything the sweep finds is
    the translator drifting into the crib.

  6 THE hume COUNTED NUMERIC DIFF, measured before being trusted. The
    Italian carries 338 digit tokens, but 241 of those are the chapter
    labels prep.py writes, so the real figure is under a hundred —
    dates, sums in scudi, weights of bronze. Small, but not inert, and
    Cellini's quarrels are almost all about a number. The labels are
    stripped from both sides first, or every file would report the
    chapter numbers as lost.

Exits NONZERO on any finding.
"""
import json
import pathlib
import re
import sys
from collections import Counter

BOOK = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK.parent))
import assemble                                              # noqa: E402

SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

LABEL = re.compile(r"^Chapter (\d+)$", re.M)
NUM = re.compile(r"\d+(?:[,./]\d+)*")
THOU = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|wert|wilt|didst|knowest|seest|saith|ere|"
    r"whilst|amongst|betwixt|nay|methinks|perchance|oft|'tis|unto|"
    r"thereunto|whereupon|hereunto|whereof|thereof|'gainst)\b", re.I)

# BY EXACT PHRASE, NEVER BY LOOSENING THE SWEEP (the grimm rule).
ARCHAIC_OK = []

# A NUMBER SPELLED OUT IS NOT A NUMBER LOST, and in this book that is a
# rule rather than an excuse. The fleming check exists because a
# measured value written as a word hides itself from every other test;
# but Cellini is not measuring anything when he says he is fifty-eight,
# and ordinary English prose spells small numbers. So a lost digit token
# is forgiven if its English WORD is in the file -- and only then, which
# is why a dropped sum in scudi or a weight of bronze still fails.
ONES = ("zero one two three four five six seven eight nine ten eleven "
        "twelve thirteen fourteen fifteen sixteen seventeen eighteen "
        "nineteen").split()
TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty",
        7: "seventy", 8: "eighty", 9: "ninety"}


def in_words(n):
    """English forms of n that might stand in a sentence, or None."""
    if n < 20:
        return [ONES[n]]
    if n < 100:
        t = TENS[n // 10]
        return [t] if n % 10 == 0 else [f"{t}-{ONES[n % 10]}", f"{t} {ONES[n % 10]}"]
    if n % 100 == 0 and n < 1000:
        return [f"{ONES[n // 100]} hundred"]
    if n == 1000:
        return ["a thousand", "one thousand"]
    return None


# SIGNED ALLOWANCES (the burke rule): a reason beside every entry.
# "in su le 22 ore" is the twenty-second hour of the Italian clock,
# which counted from sunset -- about two hours before dark on a Sunday
# in autumn. The FIGURE cannot survive into English without becoming
# nonsense, so the time of day survives instead.
# The Wikisource text of Book Two chapter 77 prints the weight of the
# half loaf of tin as "6o libbre" -- a letter o for the zero, which is a
# transcription slip and not a figure Cellini wrote. The token the check
# sees is therefore "6"; the translation reads 60 pounds, which is what
# the sentence says.
NUM_DROPPED = {"001.txt": ["22"], "036.txt": ["6"]}


def body_of(text):
    return text.split("\n", 1)[1]


def stanzas(text):
    """Runs of consecutive tab-indented lines, as line counts."""
    out, cur = [], []
    for line in text.split("\n"):
        if line.startswith("\t"):
            cur.append(line)
        else:
            if cur:
                out.append(len(cur))
            cur = []
    if cur:
        out.append(len(cur))
    return out


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out, done = [], 0
    seen = {}

    for m in manifest:
        fn = where = m["file"]
        if m["title"] in seen:
            out.append(f"{fn}: heading {m['title']!r} repeats {seen[m['title']]}"
                       f" -- a repeated heading is a repeated anchor")
        seen[m["title"]] = fn
        if not (MOD / fn).exists():
            continue
        done += 1
        text = (MOD / fn).read_text()
        src = (SRC / fn).read_text()
        lines = text.split("\n")

        # 3 -- heading, and no all-caps line
        if lines[0].strip() != m["title"]:
            out.append(f"{where}: heading {lines[0].strip()!r} != manifest "
                       f"{m['title']!r}")
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if len(s) > 3 and s == s.upper() and any(c.isalpha() for c in s):
                out.append(f"{where}:{i}: all-caps line renders as a heading "
                           f"-- {s[:50]!r}")

        sb, db = body_of(src), body_of(text)

        # 1 -- chapter labels, exact and in order
        ls, ld = LABEL.findall(sb), LABEL.findall(db)
        if ls != ld:
            miss = [x for x in ls if x not in ld]
            extra = [x for x in ld if x not in ls]
            out.append(f"{where}: chapter labels differ -- source {ls}, "
                       f"translation {ld}"
                       + (f"; MISSING {miss}" if miss else "")
                       + (f"; UNEXPECTED {extra}" if extra else ""))

        # 2 -- verse
        ss, ds = stanzas(sb), stanzas(db)
        if ss != ds:
            out.append(f"{where}: verse shape differs -- source stanzas "
                       f"{ss}, translation {ds}")

        # 4 -- markup sweep, via the renderer itself
        for i, line in enumerate(assemble.EMPH.sub("", text).split("\n"), 1):
            if "*" in line or "_" in line:
                out.append(f"{where}:{i}: stray markup that does NOT render "
                           f"-- {line.strip()[:60]!r}")

        # 5 -- archaism
        found = sorted({w.lower() for w in THOU.findall(text)})
        keep = [w for w in found
                if not any(p in text and w in p.lower() for p in ARCHAIC_OK)]
        if keep:
            out.append(f"{where}: archaic forms survive: {', '.join(keep)}")

        # 6 -- numerals, COUNTED, with the chapter labels stripped
        strip = lambda t: LABEL.sub("", t)
        bare = lambda t: [x.replace(",", "") for x in NUM.findall(strip(t))]
        lost = (Counter(bare(sb)) - Counter(bare(db))
                - Counter(NUM_DROPPED.get(fn, [])))
        for tok in list(lost):
            words = in_words(int(tok)) if tok.isdigit() else None
            if words and any(w in db.lower() for w in words):
                del lost[tok]
        if lost:
            out.append(f"{where}: numerals lost: "
                       + ", ".join(sorted(lost.elements())))

    print(f"checked {done}/{len(manifest)} translated files")
    for line in out:
        print("  " + line)
    if out:
        print(f"\n{len(out)} finding(s)")
        sys.exit(1)
    print("clean")


if __name__ == "__main__":
    main()
