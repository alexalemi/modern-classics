"""Split the 430 references into what a resolver may safely handle and
what it must refuse, BEFORE any resolution logic is written.

The point is to size the irregular tail honestly. A resolver that
quietly covers all 145 shapes is claiming a confidence it cannot have:
two of these references do not point into the Ethics at all, and a
dozen more point into Part II's interpolated physical digression, whose
Lemmas and Axioms carry their own numbering nested inside Prop. XIII.
"""
import collections, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S
from shapes import CITE

# Refuse outright. Each entry says what it is and why no rule can take it.
REFUSE = [
    (r"Principles of the Cartesian",
     "cites a DIFFERENT BOOK of Spinoza's, not the Ethics"),
    (r"\bafter\b.*\bLemma\b|\bLemma\b.*\bafter\b|before Lemma",
     "points into Part II's physical digression, numbered separately"),
    (r"\bpreface\b|\bPreface\b", "cites a Preface, which has no number"),
    (r"in Coroll\. [IVXLC]+\. stated",
     "a bare Corollary ordinal inside prose: 'Coroll. I.' here is the "
     "first Corollary of the proposition it sits in, not Part I, and "
     "the case rule cannot tell those apart"),
    (r"general Def", "the general Definition of the Emotions, unnumbered"),
]
# Relative: resolvable only from the citing position, never from the text.
RELATIVE = re.compile(
    r"\b(last|foregoing|preceding|first) (Prop|Def|Coroll|Post)|"
    r"\bthe same (Coroll|Post|Def|Prop|note)|\bthe note to the same\b",
    re.I)
# Prose wrapped round a citation: a clause, not a bare pointer.
PROSE = re.compile(r"\b(we proved|have already shown|am about to show|"
                   r"the proof (of which|whereof)|stated to be|which see|"
                   r"we pointed out|we showed|This is clear from|"
                   r"what is the same thing)\b", re.I)

def main():
    buckets = collections.Counter()
    detail = collections.defaultdict(list)
    for n, text in S.split_parts(S.body()):
        flat = re.sub(r"\s+", " ", text)
        for m in CITE.finditer(flat):
            s = m.group(0)
            for pat, why in REFUSE:
                if re.search(pat, s):
                    buckets["refuse"] += 1
                    detail[why].append((n, s))
                    break
            else:
                if PROSE.search(s):
                    buckets["prose"] += 1;  detail["prose"].append((n, s))
                elif RELATIVE.search(s):
                    buckets["relative"] += 1; detail["relative"].append((n, s))
                else:
                    buckets["regular"] += 1

    tot = sum(buckets.values())
    print(f"{tot} references")
    for k in ("regular", "relative", "prose", "refuse"):
        print(f"   {k:<10}{buckets[k]:>5}   {100*buckets[k]/tot:4.1f}%")
    for why, items in detail.items():
        print(f"\n--- {why}  ({len(items)})")
        for n, s in items[:6]:
            print(f"    Part {n}: {s[:72]}")
        if len(items) > 6:
            print(f"    ... and {len(items)-6} more")


if __name__ == "__main__":
    main()
