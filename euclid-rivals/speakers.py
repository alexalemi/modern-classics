"""Resolve the OCR-damaged speaker tags of Euclid and His Modern Rivals.

The book is a play, and the dangerous defect in an OCR play is a
misattributed speech: give Carroll's argument to the wrong ghost and it
reads perfectly well and says the opposite of what he wrote. This is the
bunyan/ trap ("Christ." is Christiana, not Christ) but noisy instead of
systematic -- the same tag comes out a dozen different ways.

TWO THINGS MAKE IT TRACTABLE.

First, the tags can be found STRUCTURALLY rather than by pattern. In the
printed book a speech opens with its tag in italic, and the ABBYY XML
records italic="true" per run, so the leading italic run of a paragraph is
the tag whatever its characters came out as. That is how "Jihad." and
"Bhad." were found at all -- both are "Rhad.".

Second, THE VOCABULARY IS CLOSED. Five speakers, and no more:

    Min.   Minos, a college examiner marking papers at midnight
    Euc.   the ghost of Euclid
    Nie.   Herr Niemand, the phantom of a German professor, who speaks
           for each modern textbook in turn
    Nos.   Nostradamus
    Rhad.  Rhadamanthus

So resolution is nearest-match against a list of five, which is safe in a
way that guessing at free text never is. Anything that does not resolve
CLEANLY IS RAISED, not guessed: a wrong tag is worse than a stopped build.

"Mill." (45 occurrences) is "Min.", not a character. Confirmed against the
1879 scan, which gives "Min." for the same speeches -- "Exactly so.", "We
could easily deduce that from I. 34.", "You had indeed."
"""

import re
import unicodedata

SPEAKERS = {
    "min": "Minos",
    "euc": "Euclid",
    "nie": "Niemand",
    "nos": "Nostradamus",
    "rhad": "Rhadamanthus",
}

# The confusions this scan actually makes, gathered from the census rather
# than imagined. Applied before matching, so "3Iin." and "M'ln." and "Mm."
# all land on "min".
FOLD = [
    ("3i", "m"), ("3l", "m"), ("31", "m"), ("2h", "m"), ("iii", "m"),
    ("i7i", "in"), ("iyi", "in"), ("bi", "in"), ("hi", "in"),
    ("ii", "n"), ("ll", "n"), ("l^", "n"), ("^", "n"), ("7", "n"),
    ("'", ""), ("`", ""), ("rn", "m"), ("vv", "w"), ("j", "i"),
    ("1", "l"), ("0", "o"), ("cl", "d"),
]

# WORDS THAT OPEN A SPEECH IN ITALIC AND ARE NOT SPEAKERS. "Reads." is the
# stage direction for reading a paper aloud, and it comes out as "Beads.",
# "^eads." and "Reads,"; resolved as a name it would invent a character and
# hand him somebody else's argument.
NOT_SPEAKER = {"reads", "read", "enter", "exit", "exeunt", "preface",
               "aside", "sings", "writes", "argument", "contents", "act",
               "scene", "appendix", "note", "table", "wilson", "symmetry",
               "todhunter", "niemand", "minos", "euclid"}
# Letters that this typeface loses to each other. Used only to score a
# near-miss, never to rewrite.
# THE RESIDUE, EACH ONE READ AND RESOLVED BY EYE. Distance scoring gets
# ninety-odd per cent of the tags; these are the spellings it cannot reach
# without a threshold so loose it would start guessing. Listed rather than
# inferred, in the manner of thompson/appendix_fixes.py -- and prep checks
# that every entry is still present in the scan, so the table cannot rot
# silently if the source is ever re-OCRed.
OVERRIDE = {
    # Euclid
    "hue": "Euclid", "etic": "Euclid", "knc": "Euclid", "iiuc": "Euclid",
    "tnnc": "Euclid", "uluc": "Euclid", "eiw": "Euclid", "eicc": "Euclid",
    "tnue": "Euclid", "mic": "Euclid", "una": "Euclid", "enc": "Euclid",
    "ekc": "Euclid", "emc": "Euclid", "iluc": "Euclid", "uuc": "Euclid",
    "euq": "Euclid", "eug": "Euclid",
    # Niemand
    "islie": "Niemand", "isiie": "Niemand", "isie": "Niemand",
    "jsie": "Niemand", "kie": "Niemand", "nle": "Niemand",
    "wie": "Niemand", "lie": "Niemand",
    # Minos
    "iliti": "Minos", "nnn": "Minos", "mm": "Minos", "mn": "Minos",
    "min": "Minos", "mln": "Minos", "ilin": "Minos", "mhn": "Minos",
    # Rhadamanthus
    "rhad": "Rhadamanthus", "bltad": "Rhadamanthus",
    "reach": "Rhadamanthus", "bhad": "Rhadamanthus",
    # The residue, each read in context. The play alternates strictly
    # between Minos and whichever ghost he is interviewing, so the speech
    # before each of these settles it.
    "^7": "Minos", "21171": "Minos", "3rui": "Minos", "3rm": "Minos",
    "Miti": "Minos", "M'ui": "Minos", "Mia": "Minos", "ITm": "Minos",
    "Iliti": "Minos", "Mhi": "Minos", "Ilin": "Minos", "3Ibi": "Minos",
    "Mbi": "Minos", "2Hn": "Minos", "Mi7i": "Minos", "3Ii7i": "Minos",
    "Miyi": "Minos",
    "ISiie": "Niemand", "JSIie": "Niemand", "Isle": "Niemand",
    "ISlle": "Niemand", "ISlie": "Niemand", "ISie": "Niemand",
    "JSie": "Niemand",
    # "Me." x4, all in Act II and all following a speech of Minos's, which
    # in that Act means Niemand and can mean nobody else.
    "Me": "Niemand",
    "Nas": "Nostradamus",
    "Em": "Euclid", "Iiuc": "Euclid", "T^nc": "Euclid", "T^ue": "Euclid",
    "Etic": "Euclid", "Knc": "Euclid", "Uluc": "Euclid", "Eiw": "Euclid",
    "Eicc": "Euclid", "Mic": "Euclid", "Una": "Euclid", "Hue": "Euclid",
}

NEAR = {("i", "l"), ("i", "e"), ("e", "c"), ("c", "e"), ("u", "n"),
        ("n", "u"), ("m", "n"), ("i", "t"), ("s", "e"), ("h", "b"),
        ("b", "r"), ("k", "n"), ("w", "n"), ("g", "c"), ("r", "n"),
        ("d", "cl"), ("h", "li")}


def _fold(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9'^`]", "", s)
    for a, b in FOLD:
        s = s.replace(a, b)
    return s


def _distance(a, b):
    """Levenshtein, with a near-miss letter pair costing a half."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cost = 0.0
            elif (ca, cb) in NEAR or (cb, ca) in NEAR:
                cost = 0.5
            else:
                cost = 1.0
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def resolve(tag):
    """'Bhad.' -> ('Rhadamanthus', 0.5). Returns (None, score) if unsure."""
    key = _fold(tag)
    if not key:
        return None, 99.0
    if key in _OVERRIDE:
        return _OVERRIDE[key], 0.0
    # "Rhad." AND "Reads." ARE ONE LETTER APART, so a non-speaker list
    # tested on its own steals Rhadamanthus and turns him into a stage
    # direction. Score both sets and let the closer one win; a tie raises.
    scored = sorted(((_distance(key, k), k) for k in SPEAKERS))
    not_best = min((_distance(key, w) for w in NOT_SPEAKER), default=99.0)
    best, second = scored[0], scored[1]
    if not_best < best[0]:
        return None, -1.0              # a known non-speaker, not a failure
    if not_best == best[0]:
        return None, best[0]           # ambiguous: stop, do not pick
    # A tag must be clearly closer to one speaker than to any other. Two
    # of the five are "Min" and "Nie", which a bad scan can confuse, so an
    # ambiguous result has to stop the build rather than pick a side.
    if best[0] <= 2.5 and (second[0] - best[0]) >= 1.0:
        return SPEAKERS[best[1]], best[0]
    if best[0] == 0:
        return SPEAKERS[best[1]], 0.0
    return None, best[0]


# The table is written in the spellings as they appear on the page, but
# matching happens on the folded form -- so fold the keys too. Written the
# other way round the table silently never matches, and every entry in it
# looks like a tag the scorer failed on.
_OVERRIDE = {_fold(k): v for k, v in OVERRIDE.items()}


TAG = re.compile(r"^([A-Za-z0-9'^`À-ɏ]{2,8})\s*[.,;:]\s*$")


def looks_like_tag(s):
    return bool(TAG.match(s.strip()))
