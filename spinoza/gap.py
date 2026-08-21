"""Parentheses that LOOK like references but that CITE never matched.

The grimm 151* lesson in its cheapest form: a reference the detector
cannot see is invisible to the resolver, to the validator and to every
count this pipeline reports. CITE keys on abbreviations with word
boundaries, so "Ax." matches and "Axiom" does not.
"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S
from shapes import CITE

# Anything that smells like a pointer into the book.
SMELL = re.compile(
    r"\b(Axiom|Postulate|Proposition|Definition|Corollary|Lemma|Note|"
    r"Explanation|Preface|Appendix|Prop|Def|Ax|Post|Coroll|Pt|Part)\b",
    re.I)

missed = collections.Counter()
where = {}
for n, text in S.split_parts(S.body()):
    flat = re.sub(r"\s+", " ", text)
    for m in re.finditer(r"\([^()]{0,120}\)", flat):
        s = m.group(0)
        if CITE.fullmatch(s):
            continue
        if SMELL.search(s):
            key = re.sub(r"\b[ivxlc]+\b", "<n>",
                         re.sub(r"\b[IVXLC]+\b", "<N>", s))
            missed[key] += 1
            where.setdefault(key, n)

print(f"{sum(missed.values())} parentheses look like references "
      f"but CITE does not match them\n")
for k, c in missed.most_common():
    print(f"  {c:>3}  Part {where[k]}  {k[:74]}")
