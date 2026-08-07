"""Repair the 1885 OCR against the 1879 OCR, where and only where it helps.

The two Archive.org scans of this book make DIFFERENT mistakes, which is
the biggest lever available on a source this damaged. The 1885 renders
italic text as debris —

    "[Scene, a College dudy. Time, midvigJtf. Mixos discovered seated
     between tivo gigantic j)iles of manuscripts ... with a ivearij sigh"

— where the 1879 gives "a College study. Time, midnight ... two gigantic
piles ... with a weary sigh". And yet in those same two sentences the 1885
has "Euc. I. 32" and "I. 20" right where the 1879 has 33 and 30 wrong.
Neither is authoritative. So this module never simply prefers one: it
aligns them, and at each disagreement it asks which reading is more likely
to be English.

TWO RULES KEEP IT HONEST, and both matter:

1. THE 1885 IS COPY TEXT, because it is the edition Carroll revised. A
   1879 reading is adopted only to fix an OCR error, never to undo a
   revision. The two are told apart by SHAPE: an OCR error looks like the
   right words misspelt, a revision looks like different words. So a
   replacement is considered only when the two spans are already similar.

2. THE REPLACEMENT MUST BE CLEARLY BETTER, measured against a dictionary,
   not merely different. "dudy" -> "study" is a gain of one real word out
   of one; "I. 32" -> "I. 33" is no gain at all and is refused, which is
   what saves the digits.

Every substitution is logged. Nothing here is silent.
"""

import difflib
import re
from pathlib import Path

WORDS = Path("/usr/share/dict/british-english")


def load_dictionary():
    words = set()
    for path in (WORDS, Path("/usr/share/dict/american-english")):
        if path.exists():
            words |= {w.strip().lower() for w in path.read_text(
                errors="replace").splitlines() if w.strip()}
    # The book's own vocabulary, which no dictionary has.
    words |= {"euclid", "minos", "niemand", "nostradamus", "rhadamanthus",
              "legendre", "cuthbertson", "henrici", "wilson", "todhunter",
              "chauvenet", "loomis", "morell", "reynolds", "willock",
              "pierce", "playfair", "euc", "syllabus", "coextensional",
              "superposition", "postulate", "postulates", "corollary",
              "corollaries", "theorem", "theorems", "isosceles", "tetragon",
              "rectilineal", "vertically", "proposition", "propositions"}
    return words


DICT = load_dictionary()
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


def english_share(text):
    """Fraction of alphabetic tokens that are real words. The measure the
    whole module turns on, so it counts TOKENS and not characters: one
    mangled word in a short span should weigh heavily."""
    toks = WORD.findall(text)
    if not toks:
        return 1.0, 0
    good = sum(1 for t in toks if t.lower().strip("'-") in DICT)
    return good / len(toks), len(toks)


def _key(tok):
    """What counts as 'the same word' for alignment purposes."""
    return re.sub(r"[^a-z0-9]", "", tok.lower())


def align(a_text, b_text):
    """Word-level opcodes between copy text and corrector."""
    a, b = a_text.split(), b_text.split()
    sm = difflib.SequenceMatcher(
        None, [_key(t) for t in a], [_key(t) for t in b], autojunk=False)
    return a, b, sm.get_opcodes()


def similar(x, y):
    """Is this an OCR difference rather than a revision?"""
    if not x or not y:
        return False
    if abs(len(x) - len(y)) > max(6, 0.4 * max(len(x), len(y))):
        return False
    # 0.45, not 0.55: "Tieap^"/"heap>" scores 0.545 and "ivearij"/"weary"
    # 0.50, and both are plainly the same word badly read. The guard that
    # actually prevents a revision being imported is the length test above
    # and the dictionary gain required by the caller, not this ratio.
    return difflib.SequenceMatcher(None, x.lower(), y.lower()).ratio() >= 0.45


DIGITS = re.compile(r"\d+")
# Two or more capitals in a row: AB, GHD, EF. In this book that is almost
# always a geometrical label -- the letters naming points on a diagram --
# and the diagram is printed with those letters on it.
LABEL = re.compile(r"[A-Z]{2,}")


def refuses(span_a, span_b):
    """Guards that override any dictionary gain. Each of these was a real
    substitution this module made before the guard existed."""
    # A NUMERAL MUST NEVER CHANGE. "32. Cuth- bertson" -> "33. Cuthbertson"
    # scored a clean gain, because the gain came from the WORD while the
    # digit rode along beside it. Proposition numbers are the whole
    # argument of this book, and no later check can see one go wrong.
    if DIGITS.findall(span_a) != DIGITS.findall(span_b):
        return "digits differ"
    # GEOMETRICAL LABELS ARE NOT WORDS, and a dictionary will always prefer
    # a word: "EF" -> "IF", "EGB" -> "12GB", "GAF," -> "GAP,", and worst,
    # "AGH, GHD," -> "AGE, GET),". The letters name points on a printed
    # diagram; changing them makes the text disagree with the picture.
    if LABEL.search(span_a) or LABEL.search(span_b):
        return "geometrical label"
    # A SPEAKER TAG IS RESOLVED STRUCTURALLY, NOT SPELT. "Bhad." became
    # "It had." here -- two dictionary words, and a speech handed to
    # nobody.
    if re.match(r"^[A-Z][A-Za-z'^]{1,7}[.,]\s*$", span_a):
        return "speaker tag"
    return None


def repair(copy_text, corrector_text, log=None, min_gain=0.34):
    """Return copy_text with clearly-better corrector readings adopted."""
    a, b, ops = align(copy_text, corrector_text)
    out = []
    for tag, i1, i2, j1, j2 in ops:
        span_a = " ".join(a[i1:i2])
        span_b = " ".join(b[j1:j2])
        if tag == "equal":
            out.append(span_a)
            continue
        if tag == "delete":
            out.append(span_a)
            continue
        if tag == "insert":
            # The corrector has words the copy text lacks. That is usually
            # a revision (or a scan reading through a blot), never
            # something to import blind.
            continue
        sa, na = english_share(span_a)
        sb, nb = english_share(span_b)
        veto = refuses(span_a, span_b)
        if veto is None and similar(span_a, span_b) and nb and sb - sa >= min_gain:
            out.append(span_b)
            if log is not None:
                log.append((span_a, span_b, round(sa, 2), round(sb, 2)))
        else:
            out.append(span_a)
    return " ".join(x for x in out if x)
