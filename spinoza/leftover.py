"""Roman-numeral references that survived into chapters/.

THE DETECTOR ONLY EVER LOOKED INSIDE PARENTHESES. Spinoza also cites
without them -- "This is clear from Deff. iii. and v.", "the
demonstration of Prop. vii." -- and those went through prep untouched,
so the reader gets the Victorian shorthand the ruling exists to remove,
in the middle of a sentence where it is most disruptive.

Run after prep. Anything this prints is unresolved.
"""
import collections
import pathlib
import re

CH = pathlib.Path(__file__).resolve().parent / "chapters"

# A kind word followed by a lower-case roman numeral, anywhere.
LEFT = re.compile(
    # PLURALS TOO. "Lemmas v. and vii." went unreported because
    # "Lemma\\b" does not match inside "Lemmas", so the one check
    # meant to catch surviving roman numerals was blind to exactly
    # the form that survived.
    r"\b(?:Props?|Deff|Defs?|Axs?|Axioms?|Posts?|Corolls?|"
    r"Corollary|Corollaries|Lemmas?|Notes?)\b\.?\s*"
    r"\b[ivxlc]+\b\.?")
# A bare Part.Proposition pair outside parentheses: "II. xiii."
BARE = re.compile(r"(?<![(\w])\b[IVXLC]+\.\s*[ivxlc]+\.")

# SIGNED ALLOWANCES. Each says why the roman numerals are correct where
# they stand; an allowance without a reason is just a loosened check.
ALLOW = [
    ('Ovid, "Amores," II. xix.',
     "a citation to Ovid, not to the Ethics"),
    ("evident from Ax. i. (which see after Lemma 3",
     "the digression's Axiom 1, which has no number of its own; the "
     "parenthetical right after it is resolved and says where it is"),
]

found = collections.Counter()
where = {}
for f in sorted(CH.glob("*.txt")):
    t = re.sub(r"\s+", " ", f.read_text())
    for m in list(LEFT.finditer(t)) + list(BARE.finditer(t)):
        s = m.group(0)
        # SKIP what is inside a parenthesis rather than blanking it out.
        # Blanking destroys the context the allowances are written
        # against: the digression's "Ax. i." is correct precisely
        # BECAUSE of the parenthetical that follows it, and blanking
        # removed the evidence before the allowance could see it.
        before = t[:m.start()]
        if before.count("(") > before.count(")"):
            continue
        ctx = t[max(0, m.start() - 60):m.end() + 70]
        if any(a in ctx for a, _ in ALLOW):
            continue
        found[s] += 1
        where.setdefault(s, (f.name, t[max(0, m.start() - 46):m.end() + 26]))

print(f"{sum(found.values())} unparenthesised references left in chapters/")
for s, n in found.most_common(30):
    name, ctx = where[s]
    print(f"  {n:>3}  {s:<18} {name}  …{ctx.strip()}…")
