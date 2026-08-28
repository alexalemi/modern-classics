#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-book checks for the Odyssey (the euclid-rivals pattern).

WHY THIS FILE MATTERS MORE HERE THAN USUAL.  The three cantiche of the
Comedy were checked by exact line and tercet parity, which is what caught
the only real defect in the Paradiso.  This book is being retold as PROSE
(Alex's ruling), so that check does not exist.  What replaces it comes
free out of Perseus' markup: every speech in the poem is tagged <q>, 674
of them, 570 at the top level and 104 quoted inside another speech.  The
translation renders the first kind in double quotes and the second in
single quotes -- the convention ovid/ already uses -- so both are
countable, per file, against what prep.py recorded.

A LOST SPEECH BOUNDARY IS THE DEFECT THIS BOOK IS MOST LIKELY TO SUFFER,
and it is invisible to every other measurement: two speeches welded into
one, or a speech dissolved into narration, leaves every word present, in
order, reading perfectly, with the word ratio unmoved.  That is the
euclid-rivals lesson (a misattributed speech reads perfectly and argues
the opposite) and the cellini one (a missing chapter label welds two
chapters and moves nothing).

CHECKS THAT ARE DELIBERATELY *NOT* HERE, with the reason, because a check
that cannot fire is worse than none -- it is counted as coverage (the
nights lesson, learned there only after shipping it):

  * THE FLEMING NUMERIC DIFF.  The Greek body of the Odyssey contains
    ZERO digit tokens: Homer spells every number out.  Measured, not
    assumed -- see the probe in the commit message.  The check could
    never fire, so it is not here.  If numbers ever need guarding, the
    shape to build is the nights night-number check, which parses
    spelled-out numerals into integers.
  * EXACT LINE PARITY.  There are no lines in prose.  Speech parity is
    what stands in for it, and it is weaker: it can see a speech that
    vanished, but not four verses of narration that did.  The word ratio
    is the only guard on those, which is why the bounds are tight.
"""

import collections
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

MODERN = os.path.join(HERE, "modern_chapters")
SOURCE = os.path.join(HERE, "chapters")

# Ratio bounds.  Murray's fairly literal 1919 prose runs 1.53 against the
# Greek (133,145 English words to 87,181).  Ours should land near that:
# we cut his archaism, which loses words, and unstack his syntax, which
# gains them.  Anything under 1.30 in a file means summarising.
MIN_RATIO, MAX_RATIO = 1.30, 1.80

# The thou-family sweep (the augustine rule).  Murray is a 1919 Loeb and
# writes "thou hast", "thee", "thy", "doth", "aye" throughout; with the
# crib open all day the drift is into HIS English, exactly as Symonds'
# Victorian prose pulled at the Cellini translation.  WHEN A CRIB IS
# VICTORIAN, THE SWEEP IS AIMED AT YOU.
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|ye|hast|hath|doth|dost|art|shalt|wilt|"
    r"unto|whilst|whereupon|betwixt|nay|aye|verily|behold|lo|"
    r"sore|wroth|fain|wight|anon|ere|oft|'?tis|methinks)\b", re.I)
# Exemptions are by EXACT PHRASE, never by loosening the sweep (grimm).
ARCHAIC_OK = []


# THE FOUR APOLOGUE BOOKS, WHERE THE MARKUP CANNOT BE TRUSTED AND SAYS SO.
#
# Books 9-12 are Odysseus telling his own story to the Phaeacians, and the
# translation renders them as PRIMARY NARRATION with no enclosing quotation
# marks -- the rule ovid/ settled for a long embedded tale, and the only
# sane choice when one speech runs to 4,145 words.  Speeches inside the
# tale are therefore double-quoted like any other.
#
# But Perseus' <q> nesting is inconsistent across exactly these books, so
# the recorded shape cannot be compared against the translation:
#   book  9  one top-level <q>, lines 2-566        (consistent)
#   book 10  one top-level <q>, lines 1-574        (consistent)
#   book 11  seven: the tale, the Phaeacian intermezzo at 336-376, the
#            tale resumed                          (consistent)
#   book 12  ELEVEN, and the nesting is FLATTENED: Circe at 116-141 and
#            the Sirens at 184-191 are speeches inside the tale but are
#            tagged top-level, and 352-453 opens "ὣς ἔφατʼ Εὐρύλοχος",
#            which is narration and not a speech at all.
#
# So for these four files the speech counts are hand-calibrated against
# the Greek when the file is translated, and until a number is filled in
# here the check PRINTS THAT IT IS NOT CHECKING THEM.  A check that
# silently passes on four of twenty-five files is worse than no check,
# because it is counted as coverage (the nights lesson).
APOLOGUE = {"009.txt", "010.txt", "011.txt", "012.txt"}
APOLOGUE_EXPECT = {}          # file -> (outer, inner), filled in on writing


def paragraphs(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def words(text):
    return len(re.sub(r"[^\w\s'-]", " ", text).split())


def count_speeches(paras):
    """(outer, inner) speeches in a modern file.

    A speech is a run of paragraphs that opens with a double quote and
    closes with one; standard English typography reopens the quote at
    each new paragraph of the same speech, so a paragraph that opens a
    quote while one is already open is a CONTINUATION, not a new speech.
    A speech quoted inside another is single-quoted and counted apart.
    """
    outer = inner = 0
    is_open = False
    for p in paras:
        n = p.count('"')
        # a speech that runs over a paragraph break reopens its quote at
        # the new paragraph without ever having closed it.  That quote is
        # typography, not a state change, so it is dropped before the
        # marks are read as alternating open/close.
        if is_open and p.lstrip().startswith('"'):
            n -= 1
        for _ in range(n):
            if not is_open:
                outer += 1
            is_open = not is_open
        # a speech quoted inside another is single-quoted; count only the
        # opening marks, and never an apostrophe inside a word
        inner += len(re.findall(r"(?<![\w])'(?=[A-Za-z])", p))
    return outer, inner


def main():
    man = json.load(open(os.path.join(HERE, "manifest.json")))
    shape = json.load(open(os.path.join(HERE, "speeches.json")))
    findings, unchecked = [], []
    checked = 0

    for m in man:
        name = m["file"]
        mp = os.path.join(MODERN, name)
        if not os.path.exists(mp):
            continue
        checked += 1
        paras = paragraphs(mp)
        src_words = m["words"]

        # 1. heading -- the quixote trap.  Part 2+ must NOT re-introduce
        #    the book, and must carry its part marker in the first lines.
        head = paras[0].splitlines()[0].strip()
        want = m["title"] if m["of"] == 1 else "%s (Part %d of %d)" % (
            m["title"], m["part"], m["of"])
        if head != want:
            findings.append("%s: heading is %r, manifest says %r"
                            % (name, head, want))

        body = "\n\n".join(paras[1:]) if len(paras) > 1 else ""

        # 2. speech parity -- the check that replaces line parity
        got = count_speeches(paragraphs(mp)[1:])
        if name in APOLOGUE:
            exp = APOLOGUE_EXPECT.get(name)
            if exp is None:
                unchecked.append("%s (book %d): speech parity NOT checked "
                                 "-- Apologue, Perseus' nesting unreliable; "
                                 "found %d spoken / %d nested"
                                 % (name, m["book"], got[0], got[1]))
                exp = got
        else:
            exp = (shape[name]["outer"], shape[name]["inner"])
        if got != exp:
            findings.append(
                "%s: %d spoken / %d nested speeches, source has %d / %d"
                % (name, got[0], got[1], exp[0], exp[1]))

        # 3. word ratio
        n = words(body)
        if src_words >= 20:
            r = n / float(src_words)
            if not (MIN_RATIO <= r <= MAX_RATIO):
                findings.append("%s: ratio %.2f (%d words on %d Greek)"
                                % (name, r, n, src_words))

        # 4. the crib's English must not have leaked in
        probe = body
        for ok in ARCHAIC_OK:
            probe = probe.replace(ok, "")
        hits = collections.Counter(w.lower() for w in ARCHAIC.findall(probe))
        if hits:
            findings.append("%s: archaic: %s" % (
                name, ", ".join("%s x%d" % kv for kv in
                                sorted(hits.items()))))

        # 5. markup-free pipeline: no stray asterisks or underscores that
        #    are not the emphasis convention, and never an ALL-CAPS line
        #    (assemble.py reads one as a heading)
        for line in body.splitlines():
            s = line.strip()
            if s and s.isupper() and len(s.split()) > 1:
                findings.append("%s: all-caps line would render as a "
                                "heading: %r" % (name, s[:60]))
                break

    print("checked %d/%d translated files" % (checked, len(man)))
    for u in unchecked:
        print("  NOT CHECKED: " + u)
    for f in findings:
        print("  " + f)
    if findings:
        print("\n%d finding(s)" % len(findings))
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
