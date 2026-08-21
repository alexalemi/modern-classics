"""Resolve the Ethics' cross-references to one canonical form.

ALEX'S RULING (2026-08-19): 137 shapes become one. Arabic numerals,
scope always explicit, relative references resolved to the number they
actually point at:

    (II. 7. Coroll.)              -> (by Part 2, Proposition 7, Corollary)
    (by Prop. iv.)                -> (by Proposition 4 of this Part)
    (by the last Prop.)           -> (by Proposition 22 of this Part)
    (Def. of the Emotions, xiii.) -> (by Definition 13 of the Emotions)

RESOLUTION IS INFERENCE, so it happens once here rather than 430 times
by hand, and nothing it produces is trusted that is not also validated
against structure.inventory(). Anything this module does not
understand is REFUSED and reported, never guessed -- the burke
ocr_sweep discipline, where being made to look at a case is the whole
mechanism.

The triage (spinoza/triage.py) over all 430 references:
    358  regular    a bare pointer; mechanical
     43  relative   "the last Prop." -- resolvable only from position
     10  prose      a citation inside a clause; the clause must survive
     19  refuse     19 that no rule may touch, each for a stated reason
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S

# How a kind is spelled out in the canonical form.
WORD = {
    "Prop": "Proposition", "Def": "Definition", "Ax": "Axiom",
    "Post": "Postulate", "Lemma": "Lemma", "Emotion": "Definition",
}
# Every abbreviation the source uses for each kind, including its typos:
# "Def of the Emotions" (no period) and "Ax.i." (no space) are both in
# the text, and a pattern that demands well-formed punctuation misses
# them silently.
ABBREV = {
    r"Prop": "Prop", r"Deff": "Def", r"Def": "Def", r"Ax(?:iom)?": "Ax",
    r"Post": "Post", r"Lemma": "Lemma",
}


class Ref:
    """One resolved pointer. `part` None means 'this Part'."""

    def __init__(self, part, kind, num, tail=()):
        self.part, self.kind, self.num = part, kind, num
        self.tail = list(tail)
        self.unnumbered = False

    def render(self, here):
        """Canonical English. `here` is the Part the citation sits in.

        The scope phrase belongs to the ITEM, not to the whole citation:
        "Proposition 6 of this Part, Corollary", never "Proposition 6,
        Corollary of this Part", which reads as though the Corollary
        rather than the Proposition were the thing being located.
        """
        if self.kind == "Part":
            return f"Part {self.num}"
        if self.kind == "Emotion":
            head = f"Definition {self.num} of the Emotions"
        else:
            name = WORD[self.kind]
            head = f"the {name}" if self.unnumbered else f"{name} {self.num}"
            if self.part is not None and self.part != here:
                head = f"Part {self.part}, {head}"
            else:
                head = f"{head} of this Part"
        return ", ".join([head] + self.tail)

    def valid(self, inv, here):
        """Does this pointer land on something that exists?"""
        if self.kind == "Part":
            # "(as we showed in Pt. II.)" -- a whole Part, no item.
            return self.num in (1, 2, 3, 4, 5)
        p = self.part if self.part is not None else here
        kind = "Emotion" if self.kind == "Emotion" else self.kind
        if kind == "Emotion":
            p = 3
        top = inv.get(p, {}).get(kind, 0)
        return self.num is not None and 1 <= self.num <= top

    def __repr__(self):
        return f"Ref(part={self.part}, {self.kind} {self.num}, {self.tail})"


# ---------------------------------------------------------------------
# THE ONE DECISION THAT IS NOT MECHANICAL
# ---------------------------------------------------------------------
def resolve_relative(phrase, here_part, here_prop, block):
    """Turn a relative reference into an absolute proposition number.

    Called for the 43 references that name no number at all:
        "by the last Prop."        "by the foregoing Prop."
        "by the preceding Prop."   "by the first Prop. of this Part"

    Arguments:
        phrase     the reference text, lower-cased, e.g. "by the last prop."
        here_part  the Part it occurs in                        (1..5)
        here_prop  the number of the Proposition it sits under  (int)
        block      the block it sits inside: "Proof", "Corollary",
                   "Note", "Explanation", or "" for none

    Return the proposition number it points at, or None to refuse it
    (refusing is safe -- the reference is then reported and left for a
    human, never guessed).

    THE TRADE-OFF, which is why this is not written for you:

    Inside a PROOF of Proposition N, "the last Prop." plainly means
    N - 1: the proof is part of N, so the last completed proposition is
    the one before it. That is most of the 43 and is not in doubt.

    Inside a COROLLARY of Proposition N it is genuinely ambiguous, and
    there are about ten of these (Part 1 Coroll. of VI; Part 4 Coroll.
    of XXXV, twice; Part 5 Coroll. of IV; Part 5 Coroll. of XXIII):
      - N - 1, reading "the last Prop." as the last complete
        proposition before the one we are inside; or
      - N, reading it as the proposition immediately above, which is
        the one the Corollary is drawn from and is what a reader
        looking up the page would find first.
    Spinoza's Corollaries usually follow directly from their own
    proposition, which argues for N -- but not always, and a wrong
    number here reads perfectly and sends the reader one proposition
    away from the argument.

    "the first Prop. of this Part" is 1 and needs no policy.

    ALEX RULED (2026-08-20): inside a Corollary, N.
    """
    p = phrase.lower()
    if not re.search(r"\bprop", p):
        # "the last Def.", "the same Coroll.", "the same Post." -- these
        # are relative to a different kind and get no policy here.
        return None
    if "first" in p:
        return 1
    if here_prop is None:
        return None
    if block in ("Corollary", "Coroll.", "Note", "Explanation"):
        # Alex's ruling. A Corollary is drawn FROM the proposition it
        # hangs on, and that proposition is what a reader looking up the
        # page finds first, so "the last Prop." there is N and not N-1.
        return here_prop
    return here_prop - 1 if here_prop > 1 else None


# ---------------------------------------------------------------------
# The mechanical 83%
# ---------------------------------------------------------------------
TOKEN = re.compile(
    r"(?P<partkw>\b(?:Pt|Part)\b\.?\s*(?P<pnum>[IVXLCivxlc]+|\d+)\b)"
    r"|(?P<emotion>\bDef(?:s)?\b\.?\s*(?:of\s+(?:the\s+)?Emotions?)\b)"
    r"|(?P<kind>\b(?:[Pp]rop(?:osition)?s?|[Dd]eff|[Dd]ef(?:inition)?s?|[Aa]xioms?|[Aa]x|[Pp]ost(?:ulate)?s?|[Ll]emmas?)\b\.?)"
    r"|(?P<coroll>\b[Cc]orolls?\b\.?|\b[Cc]orollary\b|\b[Cc]orollaries\b)"
    r"|(?P<note>\bnotes?\b\.?|\bNotes?\b\.?)"
    r"|(?P<expl>\bexplanations?\b|\bExplanations?\b)"
    r"|(?P<upper>\b[IVXLC]+\b)"
    r"|(?P<lower>\b[ivxlc]+\b)"
    r"|(?P<digit>\b\d+\b)",
    re.X)

# Words that merely introduce a citation and carry no structure.
LEAD = re.compile(r"^(?:by|see|cf\.?|in|from|solely from|as appears from|"
                  r"which see in|and)\s+", re.I)


def parse(inner, here_part):
    """Parse the inside of one parenthesis into Refs.

    Returns (refs, ok). ok is False when a token was met that the
    grammar does not account for -- the caller then REFUSES rather than
    shipping a half-understood citation.

    A QUALIFIER MAY COME BEFORE ITS TARGET. Elwes writes both
    "(II. vii. Coroll.)" and "(Corollary, Prop vi.)", and both
    "(Prop. x. note)" and "(in the note to Prop. x.)". A qualifier seen
    before any target is STICKY: it applies to every target in the
    parenthesis, which is what "(Def. of the Emotions, Explanation xii.
    and xiii.)" needs -- two Emotions, one Explanation each.
    """
    refs, cur_part, cur_kind, pending = [], None, None, None
    lead = []          # qualifiers seen before any target
    parts_seen = []    # every Part named anywhere in the parenthesis
    prev_end = 0       # end of the previous token, to read the gap

    def flush():
        nonlocal pending
        if pending is not None:
            refs.append(pending)
            pending = None

    def start(part, kind, n):
        return Ref(part, kind, n, list(lead))

    def open_tail(r):
        """True if r's last qualifier is still waiting for its number."""
        return (r is not None and r.tail
                and not any(c.isdigit() for c in r.tail[-1])
                and r.tail[-1] not in lead)

    for m in TOKEN.finditer(inner):
        g = m.lastgroup
        # "AND" BEFORE A NUMERAL STARTS A NEW TARGET. Elwes writes
        # "(II. vi. Coroll. and vii.)" for Proposition 6's Corollary AND
        # Proposition 7; without this the "vii" is read as qualifying
        # the open "Coroll." and the pair collapses into a single
        # "Corollary 7", which is a corollary Proposition 6 does not
        # have and a reference to Proposition 7 that has vanished.
        # A COMMA DETACHES TOO. "(II. xxxviii. Coroll., xxxix. and
        # Coroll. and xl.)" is Proposition 38's Corollary, then
        # Proposition 39 with its Corollary, then Proposition 40 --
        # and the comma is all that separates the open "Coroll."
        # from the next proposition number. Only whitespace means
        # the numeral belongs to the qualifier ("Coroll. ii.").
        joined = bool(re.search(r"\band\b|,",
                                inner[prev_end:m.start()]))
        prev_end = m.end()
        if g == "partkw":
            flush()
            cur_part = num(m.group("pnum"))
            parts_seen.append(cur_part)
        elif g == "emotion":
            flush()
            cur_kind = "Emotion"
        elif g == "kind":
            flush()
            raw = m.group("kind").strip(".").rstrip("s").capitalize()
            cur_kind = {"Deff": "Def", "Definition": "Def",
                        "Proposition": "Prop", "Axiom": "Ax",
                        "Postulate": "Post"}.get(raw, raw)
        elif g == "upper":
            v = num(m.group("upper"))
            if v is None:
                return refs, False
            if cur_kind == "Lemma" and pending is None:
                pending = start(cur_part, "Lemma", v)
            elif open_tail(pending) and not joined:
                # "Coroll. I." -- an uppercase ordinal qualifying a tail
                pending.tail[-1] = f"{pending.tail[-1]} {v}"
            elif 1 <= v <= 5:
                # An uppercase numeral in Part range is a PART, and it
                # CANCELS any kind word standing before it. Elwes writes
                # "(see the Def. of Appetite, III. ix. note)", where
                # "Def." is the English word "definition" and the actual
                # target is Part 3, Proposition 9, Note. Reading that
                # "Def." as a citation kind turns the Part number into a
                # definition number and invents two references that do
                # not exist. A real definition citation puts the Part
                # FIRST -- "(II. Def. ii.)" -- so nothing is lost.
                flush()
                cur_part, cur_kind = v, None
                parts_seen.append(v)
            else:
                prev_kind = pending.kind if pending is not None else None
                flush()
                pending = start(cur_part, cur_kind or prev_kind or "Prop", v)
        elif g in ("lower", "digit"):
            v = num(m.group(g))
            if v is None:
                return refs, False
            if open_tail(pending) and not joined:
                pending.tail[-1] = f"{pending.tail[-1]} {v}"
            else:
                prev_kind = pending.kind if pending is not None else None
                flush()
                pending = start(cur_part, cur_kind or prev_kind or "Prop", v)
        elif g in ("coroll", "note", "expl"):
            word = {"coroll": "Corollary", "note": "Note",
                    "expl": "Explanation"}[g]
            if pending is None and not refs:
                lead.append(word)          # sticky: applies to all targets
            elif pending is None:
                refs[-1].tail.append(word)
            else:
                pending.tail.append(word)
    flush()

    if not refs:
        # Part IV's single axiom carries no number: "(IV. Ax.)"
        if (cur_part, cur_kind) in S.UNNUMBERED:
            r = Ref(cur_part, cur_kind, 1)
            r.unnumbered = True
            return [r], True
        # A whole-Part citation with no item: "(as we showed in Pt. II.)"
        if cur_part is not None and cur_kind is None:
            return [Ref(cur_part, "Part", cur_part)], True
        return refs, False

    # A PART MARKER MAY FOLLOW ITS ITEM. Elwes writes both
    # "(Part i., Prop. xv.)" and "(by Prop. xvi., Part i.)", and only
    # propagating the Part forwards silently resolves the second to the
    # Part the citation SITS IN -- which usually exists, so it validates
    # and ships a plausible pointer to the wrong proposition. If exactly
    # one Part is named anywhere in the parenthesis, every part-less
    # reference in it belongs to that Part, whichever order they came in.
    if len(set(parts_seen)) == 1:
        for r in refs:
            if r.part is None and r.kind != "Emotion":
                r.part = parts_seen[0]

    ok = all(r.num is not None for r in refs)
    return refs, ok


def num(tok):
    """Roman or arabic numeral to int; None if it is neither."""
    tok = tok.strip(". ")
    if tok.isdigit():
        return int(tok)
    return S.unroman(tok)


def inventory():
    """The verified index every reference is validated against."""
    return S.inventory(S.split_parts(S.body()))


# ---------------------------------------------------------------------
# THE HAND TABLE
# ---------------------------------------------------------------------
# The 36 references the resolver refuses, each resolved by READING the
# passage and keyed by (Part, Proposition, exact text). Five of them
# needed the surrounding proof to settle:
#   II.11  "by the same Axiom"     -> the "(by II. Ax. iii.)" two clauses back
#   III.1  "by the same Coroll."   -> the "(II. xl. Coroll.)" just cited
#   III.16 "by the foregoing Coroll." -> III.15's Corollary
#   III.51 "by the same Post."     -> the "(II. Post. iii.)" that opens the proof
#   V.33   "by the same Axiom"     -> the "(V. xxxi. I. Ax. iii.)" before it
# Most of the rest need good English rather than a number: the physical
# digression's items are located by position and HAVE no absolute
# number, the general Definition of the Emotions is unnumbered, and the
# Prefaces are not numbered at all. Two are not pointers into the
# Ethics and stand unchanged.
HAND = {
    # --- not the Ethics ------------------------------------------------
    (1, 19, '(in Prop. xix. of my "Principles of the Cartesian Philosophy")'):
        "(in Proposition 19 of my Principles of the Cartesian Philosophy)",
    (4, 66, "(Pollock, p. 268, note.)"): "(Pollock, p. 268, note.)",

    # --- resolved by reading the proof ---------------------------------
    (2, 11, "(by the same Axiom)"): "(by Part 2, Axiom 3)",
    (3, 1, "(by the same Coroll.)"):
        "(by Part 2, Proposition 40, Corollary)",
    (3, 16, "(by the foregoing Corollary)"):
        "(by Proposition 15 of this Part, Corollary)",
    (3, 51, "(by the same Post.)"): "(by Part 2, Postulate 3)",
    (5, 33, "(by the same Axiom)"): "(by Part 1, Axiom 3)",
    (2, 41, "(in the foregoing note)"):
        "(in Proposition 40 of this Part, Note 2)",
    (3, None, "(by the foregoing definition)"):
        "(by Definition 1 of this Part)",
    (4, 35, "(by the foregoing Coroll.)"): "(by Corollary 1 above)",
    (4, 45, "(which I have in Coroll. I. stated to be bad)"):
        "(which I have in Corollary 1 stated to be bad)",

    # --- Part II's physical digression, located by position ------------
    (2, 13, "(by the last Def.)"):
        "(by the Definition before Lemma 4)",
    (2, 16, "(by Ax. i., after the Coroll. of Lemma iii.)"):
        "(by Axiom 1, after the Corollary to Lemma 3)",
    (2, 17, "(Ax. ii., after the Coroll. of Lemma iii.)"):
        "(Axiom 2, after the Corollary to Lemma 3)",
    (2, 24, "(Def. after Lemma iii.)"): "(the Definition after Lemma 3)",
    (2, 24, "(Ax. i., after Lemma iii.)"): "(Axiom 1, after Lemma 3)",
    (3, 17, "(Ax.i. after Lemma iii. after II. xiii.)"):
        "(Axiom 1, after Lemma 3, which follows Part 2, Proposition 13)",
    (3, 51, "(by Ax. i. after Lemma iii. after II. xiii.)"):
        "(by Axiom 1, after Lemma 3, which follows Part 2, Proposition 13)",
    (3, 51, "(by the same Axiom)"): "(by that same Axiom 1)",
    (3, 57, "(which see after Lemma iii. Prop. xiii., Part II.)"):
        "(which see after Lemma 3, following Part 2, Proposition 13)",
    (4, 39, "(Def. before Lemma iv. after II. xiii.)"):
        "(the Definition before Lemma 4, which follows Part 2, "
        "Proposition 13)",
    (5, 4, "(II. xii. and Lemma ii. after II. xiii.)"):
        "(Part 2, Proposition 12, and Lemma 2, which follows Part 2, "
        "Proposition 13)",

    # --- the general Definition of the Emotions, which has no number ---
    (4, 7, "(cf. the general Definition of the Emotions at the end of "
           "Part III.)"):
        "(compare the general Definition of the Emotions at the end of "
        "Part 3)",
    (4, 7, "(by the general definition of the emotions)"):
        "(by the general Definition of the Emotions)",
    (4, 7, "(by the general Definition of the Emotions)"):
        "(by the general Definition of the Emotions)",
    (4, 14, "(by the general Definition of the Emotions)"):
        "(by the general Definition of the Emotions)",
    (5, 3, "(by the general Def. of the Emotions)"):
        "(by the general Definition of the Emotions)",
    (5, 4, "(by the general Def. of the Emotions)"):
        "(by the general Definition of the Emotions)",
    (5, 17, "(by the general Def. of the Emotions)"):
        "(by the general Definition of the Emotions)",
    (5, 34, "(see general Def. of Emotions)"):
        "(see the general Definition of the Emotions)",
    (5, 40, "(III. iii. and general Def. of the Emotions)"):
        "(Part 3, Proposition 3, and the general Definition of the "
        "Emotions)",

    # --- the Prefaces, which carry no number ---------------------------
    (4, None, "(Concerning these terms see the foregoing preface towards "
              "the end.)"):
        "(Concerning these terms see the Preface to this Part, towards "
        "the end.)",
    (4, 39, "(see Preface to this Part towards the end, though the point "
            "is indeed self--evident)"):
        "(see the Preface to this Part, towards the end, though the point "
        "is indeed self-evident)",
    (4, 59, "(as we pointed out in the preface to Pt. IV.)"):
        "(as we pointed out in the Preface to Part 4)",
    (4, 65, "(see preface to this Part)"): "(see the Preface to this Part)",

    # --- a citation INSIDE a clause -----------------------------------
    # The clause is Spinoza's prose and has to survive, so only the
    # pointer inside it moves. These cannot go through the resolver at
    # all: "as I have already shown in Prop. vii." opens with a capital
    # I, which the case rule reads as Part I.
    (1, 19, "(as I have already shown in Prop. vii.)"):
        "(as I have already shown in Proposition 7 of this Part)",
    (2, None, "(for we proved in Part i., Prop. xvi., that an infinite "
              "number must follow in an infinite number of ways)"):
        "(for we proved in Part 1, Proposition 16, that an infinite "
        "number must follow in an infinite number of ways)",
    (2, 3, "(what is the same thing, by Prop. xvi., Part i.)"):
        "(what is the same thing, by Part 1, Proposition 16)",
    (3, 23, "(as I am about to show in Prop. xxvii.)"):
        "(as I am about to show in Proposition 27 of this Part)",
    (3, 28, "(This is clear from II. vii. Coroll. and II. xi. Coroll.)"):
        "(This is clear from Part 2, Proposition 7, Corollary, and "
        "Part 2, Proposition 11, Corollary)",
    (4, 4, "(by the last Prop., the proof of which is universal, and can "
           "be applied to all individual things)"):
        "(by Proposition 3 of this Part, the proof of which is universal, "
        "and can be applied to all individual things)",
    (4, 16, "(by the last Prop., the proof whereof is of universal "
            "application)"):
        "(by Proposition 16 of this Part, the proof whereof is of "
        "universal application)",
    (4, 30, "(by the Def., which see in III. xi. note)"):
        "(by the Definition, which see in Part 3, Proposition 11, Note)",
    (4, 59, "(as we showed in Pt. II.)"): "(as we showed in Part 2)",
    (4, 73, "(as we showed in IV. xxxvii. note. ii.)"):
        "(as we showed in Proposition 37 of this Part, Note 2)",
}
