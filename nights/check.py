#!/usr/bin/env python3
"""Per-book checks for the Nights that verify.py structurally cannot make.

    python3 nights/check.py

verify.py knows about completeness, word ratio, part markers and figure
parity. It cannot see a defect where the content is PRESENT, IN ORDER, AND
WRONG, which is the class every book since tyndall/ has actually shipped.
This is the euclid-rivals/check.py pattern applied to what THIS book has
that the shared tools do not know about.

  1. THE NIGHT-BREAK PARITY. The 147 night-breaks are the frame's whole
     mechanism, not filler, and a translation can drop one without moving
     the word ratio by a measurable amount. Every source break must have a
     modern break, and the spelled-out night NUMBERS must match as a
     sequence -- a wrong number is worse than a missing one, because the
     reader is being told which of the thousand nights this is.

     BURTON CAPITALISES THE HEADER AT RANDOM ("When It Was The Fifth
     Night", "When it Was the Ninth Night", "When It was the Eleventh
     Night"), so the match MUST be case-insensitive. A case-sensitive
     pattern reports three false mismatches and hides any real one in the
     noise.

  2. THE LOCKED PHRASES. Formulae that recur across the whole book and
     whose power is that they are identical every time. Burton words each
     of them several ways; we do not. Any near-miss variant is a drift
     that a ledger entry alone will not catch -- file 001 and 002 carried
     one for twenty files before a grep found it.

  3. THE NUMERIC DIFF (the fleming rule). Numbers spelled as words pass
     the ratio, the parity and must_contain alike. Every numeral in a
     source file should appear in its modern counterpart, allowing for
     digits legitimately written out as words.

  4. THE CONVENTION SWEEP. The pipeline is markup-free: an all-caps line
     renders as a section heading and a stray asterisk ships as an
     asterisk. The source is full of both -- the opening doxology, the
     inscription over the ladies' door, and 545 hemistich caesuras.
"""
import json
import pathlib
import re
import sys
from collections import Counter

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

# THREE SOURCE FORMS, one locked translation form. The main volume has
# Shahrazad "perceive" the dawn; Aladdin's supplemental text has her
# "surprised by" it; ALI BABA'S has "the morn began to dawn" and puts the
# night header AFTER the break instead of before it, counting the night
# that just ENDED rather than the one beginning. All three are normalised
# to the volume's single form -- so the check has to know all three, or
# Ali Baba's four breaks read as four inventions.
NIGHT_SRC = re.compile(r"(perceived|surprised by) the dawn of day"
                       r"|morn began to dawn")
NIGHT_MOD = re.compile(r"saw the dawn breaking, and fell silent")
# case-insensitive on purpose; see the module docstring
NIGHT_NO = re.compile(r"when it was the ([A-Za-z][A-Za-z- ]*?) night", re.I)
# Ali Baba's header form. Its number is the night that has just CLOSED, so
# the modern header -- which names the night about to open -- is one higher.
NIGHT_END = re.compile(r"the end of the ([A-Za-z][A-Za-z- ]*?) night", re.I)

ONES = ["", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
        "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
        "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
        "nineteenth"]
CARD = ["", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
TENS_ORD = {"twentieth": 20, "thirtieth": 30, "fortieth": 40, "fiftieth": 50,
            "sixtieth": 60, "seventieth": 70, "eightieth": 80, "ninetieth": 90}


def spelled(phrase):
    """"Six Hundred and Thirty-fourth" -> 634. None if it will not parse."""
    total = 0
    for word in re.split(r"[\s-]+", phrase.lower().replace(",", "")):
        if not word or word == "and":
            continue
        if word == "hundred":
            total *= 100
            continue
        if word in TENS:
            total += TENS[word]
        elif word in TENS_ORD:
            total += TENS_ORD[word]
        elif word in CARD:
            total += CARD.index(word)
        elif word in ONES:
            total += ONES.index(word)
        else:
            return None
    return total or None
# A separator must be FOLLOWED BY A DIGIT, or a figure at the end of a
# clause swallows the comma after it and "1,000," stops matching its own
# occurrence in the translation (the hume fix).
NUM = re.compile(r"\d+(?:[,./]\d+)*")

# Phrases locked in running_notes.txt, with the near-miss variants that
# have actually been written by mistake. A variant present anywhere is a
# drift, even though it reads perfectly.
LOCKED = {
    "the meddling proverb": (
        "own meddling brought",
        ["meddling made me uncomfortable", "officiousness brought"],
    ),
    "the night-break": ("saw the dawn breaking, and fell silent",
                        ["perceived the dawn", "ceased to say her permitted say"]),
    # The variants are anchored to "reached me," on purpose. Aladdin's
    # source addresses the Sultan as "O King of the Age" IN DIALOGUE as
    # well as in the resumption formula, and that address is good flavour
    # and stays; it is only the FORMULA that is locked. An unanchored
    # variant flagged the Queen greeting her husband.
    "the resumption": ("It has reached me, O fortunate King",
                       ["reached me, O auspicious King",
                        "reached me, O King of the Age"]),
    "the pardon formula": ("rub your head and be on your way", []),
    "the warning formula": ("engraved with needles on the inner corners of the eye",
                            ["graven with gravers", "eye corners"]),
    "the caliph's title": ("Commander of the Faithful",
                           ["Prince of the Faithful", "Prince of True Believers",
                            "Prince of the True Believers"]),
    # Burton writes "Sunderer of Societies" here and "Sunderer of Companies"
    # elsewhere; normalised to the famous English form. Recurs in 071.
    "the death formula": ("the Destroyer of Delights and the Sunderer of Companies",
                          ["Sunderer of Societies", "Destroyer of delights",
                           "Caterer for Cemeteries"]),
}


def caps_or_markup(text):
    """An all-caps line becomes an <h2>; a stray asterisk ships as one."""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        letters = [c for c in s if c.isalpha()]
        if len(s.split()) >= 4 and letters and \
                sum(c.isupper() for c in letters) / len(letters) > 0.9:
            out.append((i, "all-caps line would render as a heading", s[:70]))
        if "*" in s or "_" in s:
            out.append((i, "markup character ships literally", s[:70]))
    return out


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    done = [m for m in manifest if (MOD / m["file"]).exists()]
    fails = []

    whole = ""
    for m in done:
        s = (SRC / m["file"]).read_text()
        d = (MOD / m["file"]).read_text()
        whole += d
        f = m["file"]

        a, b = len(NIGHT_SRC.findall(s)), len(NIGHT_MOD.findall(d))
        if a != b:
            fails.append(f"{f}: {a} night-breaks in source, {b} in translation")

        # Compare as INTEGERS, not strings, so the two source header forms
        # can be checked against the one translation form. Ali Baba's
        # "end of the Nth" maps to the modern "when it was the (N+1)th".
        ns = [spelled(x) for x in NIGHT_NO.findall(s)] + \
             [(spelled(x) or 0) + 1 for x in NIGHT_END.findall(s)]
        nd = [spelled(x) for x in NIGHT_NO.findall(d)]
        if None in ns or None in nd:
            fails.append(f"{f}: a night number would not parse: {ns} -> {nd}")
        elif sorted(ns) != sorted(nd):
            fails.append(f"{f}: night numbers {ns} -> {nd}")

        # THIS CHECK CANNOT FIRE, AND SAYING SO IS THE POINT.
        # MEASURED, 2026-08-22: there is not a single digit anywhere in the
        # 72 source files. Burton spells every number out in words -- "three
        # hundred and sixty days", "the Forty Thieves" -- so NUM.findall
        # returns nothing on either side and the diff is always empty. The
        # line below has reported "numerals clean" since the day it was
        # written while testing precisely nothing.
        # It is kept, tightened, because this file is a template other books
        # copy and the old set-plus-substring form was wrong in three ways
        # (see the module docstring). But the fleming numeric diff only has
        # purchase where the SOURCE USES DIGITS: measure that before
        # claiming it as protection. What actually guards numbers in this
        # book is the night-number sequence check above, which parses the
        # spelled-out ordinals -- and that one has caught real defects.
        # COUNTED, NOT A SET (the hume lesson): a set cannot see a dropped
        # duplicate. And the old test asked `n not in d`, a substring
        # search over the whole file, so "5" counted as present because
        # some "1500" contained it. Sindbad's voyages are full of repeated
        # small figures, which is exactly the material this protects.
        lost = Counter(NUM.findall(s)) - Counter(NUM.findall(d))
        if lost:
            fails.append(f"{f}: numerals not found in translation: "
                         f"{sorted(lost.elements())} "
                         f"(check they are not spelled out)")

        for line, why, txt in caps_or_markup(d):
            fails.append(f"{f}:{line}: {why}\n    {txt}")

    for name, (good, bad) in LOCKED.items():
        if good not in whole and any(m["file"] for m in done):
            fails.append(f"locked phrase never appears: {name} ({good!r})")
        for variant in bad:
            if variant in whole:
                fails.append(f"DRIFT from {name}: found {variant!r} in the "
                             f"translation; the locked form is {good!r}")

    print(f"{len(done)}/{len(manifest)} files translated")
    if fails:
        print(f"\n{len(fails)} PROBLEM(S):")
        for x in fails:
            print("  " + x)
        sys.exit(1)
    print("night-breaks, night numbers, numerals, locked phrases "
          "and conventions all clean")


if __name__ == "__main__":
    main()
