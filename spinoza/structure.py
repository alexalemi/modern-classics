"""Parse the Ethics into its numbered machine, and resolve every
cross-reference against it. Run and read BEFORE prep.py emits anything.

WHY THIS EXISTS. The Ethics is not prose with headings. It is five Parts
of numbered Definitions, Axioms, Postulates and Propositions, each
Proposition trailing a Proof and often Corollaries and Notes, and every
proof is a chain of citations to other numbered items. Alex's ruling of
2026-08-19: resolve the references and normalise them to one form. That
turns 137 shapes into one and makes every citation checkable -- but
resolution is INFERENCE, so nothing here may be trusted that is not
also verified. This module's job is to produce the index and then prove
that every one of the 422 references lands on an item that exists.

THREE TRAPS THE SOURCE SETS, all found by surveying before writing:
  1. PART II HAS NO "PART" LINE. The five Parts are headed five
     different ways -- "PART I. CONCERNING GOD.", then nothing at all
     for Part II (only its subtitle, "ON THE NATURE AND ORIGIN OF THE
     MIND"), then "PART III.", "PART IV:", "PART V:". A regex anchored
     on the word PART silently loses a fifth of the book, which is the
     grimm 151* defect exactly: a section prep never recognises is
     invisible to every check that compares prep's own output.
  2. 233 OF THE 422 REFERENCES BREAK ACROSS A LINE ("(see\nAx. iv.)").
     Normalise whitespace before matching anything, or more than half
     of them are invisible.
  3. FOOTNOTE NUMBERING RESTARTS PER PART. 51 marks, 17 distinct
     numbers. "[1]" is five different notes, so the marks must be
     scoped to their Part before they are inlined, or a note lands on
     the wrong sentence -- which reads perfectly (the candle lesson).
"""
import collections
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source" / "ethics.txt"

PART_TITLES = {
    1: "Concerning God",
    2: "On the Nature and Origin of the Mind",
    3: "On the Origin and Nature of the Emotions",
    4: "Of Human Bondage, or the Strength of the Emotions",
    5: "Of the Power of the Understanding, or of Human Freedom",
}
# Where each Part begins. Part II is anchored on its SUBTITLE because
# the source gives it no number line at all; the others on their own
# heading, which is spelled a different way in each case.
PART_ANCHORS = {
    1: "PART I. CONCERNING GOD.",
    2: "ON THE NATURE AND ORIGIN OF THE MIND",
    3: "PART III.",
    4: "PART IV:",
    5: "PART V:",
}

ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def unroman(s):
    s = s.lower().strip(". ")
    if not s or not all(c in ROMAN for c in s):
        return None
    total, prev = 0, 0
    for c in reversed(s):
        v = ROMAN[c]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def body():
    t = SRC.read_text()
    m = re.search(r"\*\*\* ?START OF TH[EI]S? PROJECT GUTENBERG[^\n]*\n", t)
    if m:
        t = t[m.end():]
    m = re.search(r"\*\*\* ?END OF TH[EI]S? PROJECT GUTENBERG", t)
    if m:
        t = t[:m.start()]
    return t


def split_parts(t):
    """[(n, text)] for the five Parts, by explicit anchor."""
    marks = []
    for n, anchor in PART_ANCHORS.items():
        i = t.find(anchor)
        assert i >= 0, f"Part {n} anchor not found: {anchor!r}"
        # the Part II anchor also occurs in Part I's table of contents
        if n == 2:
            i = t.find(anchor, t.find(PART_ANCHORS[1]) + 1)
        marks.append((i, n))
    marks.sort()
    assert [n for _, n in marks] == [1, 2, 3, 4, 5], \
        f"Parts out of order: {[n for _, n in marks]}"
    out = []
    for k, (i, n) in enumerate(marks):
        j = marks[k + 1][0] if k + 1 < len(marks) else len(t)
        out.append((n, t[i:j]))
    return out


ITEM = re.compile(
    r"^[ \t]*(?:(PROP\.)\s*([IVXLC]+)\.|"
    r"(DEFINITIONS?|AXIOMS?|POSTULATES?|APPENDIX|PREFACE|PROPOSITIONS)\b)",
    re.M)
# TWO LAYOUTS FOR THE SAME THING, in one book. Part I numbers its
# definitions with a bare "I."; Part II writes "DEFINITION I." with the
# word in front. A regex written against either one alone silently
# reports that the other Part has no definitions at all -- which is how
# Part II came back with zero on the first run.
NUMBERED = re.compile(
    r"^[ \t]*(?:DEFINITION|AXIOM|POSTULATE|PROPOSITION)?[ \t]*"
    r"([IVXLC]+)\.[ \t]+", re.M)
# Part IV has exactly ONE axiom and it carries no number at all, so a
# reference to it is "(IV. Ax.)" with nothing after the abbreviation.
# max()==0 is the truth there, not a parsing failure; the validator has
# to allow a numberless citation for those.
UNNUMBERED = {(4, "Ax"): 1}


def inventory(parts):
    """{part: {kind: highest number}} for everything a reference can cite."""
    inv = collections.defaultdict(dict)
    for n, text in parts:
        props = [unroman(m.group(1)) for m in
                 re.finditer(r"^[ \t]*PROP\.\s*([IVXLC]+)\.", text, re.M)]
        props = [p for p in props if p]
        inv[n]["Prop"] = max(props) if props else 0
        inv[n]["nprops"] = len(set(props))
        for kind, head in (("Def", r"DEFINITIONS?"), ("Ax", r"AXIOMS?"),
                           ("Post", r"POSTULATES?")):
            nums = []
            for h in re.finditer(rf"^[ \t]*{head}\.?\s*$", text, re.M):
                seg = text[h.end():h.end() + 9000]
                stop = re.search(r"^[ \t]*(PROP\.|AXIOMS?|POSTULATES?|"
                                 r"PROPOSITIONS)", seg, re.M)
                if stop:
                    seg = seg[:stop.start()]
                nums += [unroman(m.group(1)) for m in NUMBERED.finditer(seg)]
            nums = [x for x in nums if x]
            inv[n][kind] = max(nums) if nums else UNNUMBERED.get((n, kind), 0)
            if (n, kind) in UNNUMBERED:
                inv[n][kind + "_unnumbered"] = True
        # Part III's Definitions of the Emotions are cited from Parts
        # III, IV and V and are numbered in their own series.
        m = re.search(r"DEFINITIONS? OF THE EMOTIONS", text)
        if m:
            seg = text[m.end():]
            nums = [unroman(x.group(1)) for x in NUMBERED.finditer(seg)]
            inv[n]["Emotion"] = max(x for x in nums if x)
    return inv


def main():
    t = body()
    parts = split_parts(t)
    print(f"body {len(t.split()):,} words in {len(parts)} Parts")
    for n, text in parts:
        print(f"   Part {n}: {len(text.split()):>7,} words  "
              f"{PART_TITLES[n]}")

    inv = inventory(parts)
    print("\n=== inventory (highest number found for each citable kind)")
    print(f"   {'Part':<6}{'Props':>7}{'Def':>6}{'Ax':>5}{'Post':>6}"
          f"{'Emotion':>9}")
    for n in sorted(inv):
        d = inv[n]
        print(f"   {n:<6}{d.get('Prop', 0):>7}{d.get('Def', 0):>6}"
              f"{d.get('Ax', 0):>5}{d.get('Post', 0):>6}"
              f"{d.get('Emotion', 0):>9}")
    total = sum(inv[n]["nprops"] for n in inv)
    print(f"   distinct propositions in all: {total}   "
          f"(the survey counted 259 PROP. headings)")


if __name__ == "__main__":
    main()
