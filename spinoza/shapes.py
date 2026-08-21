"""Every distinct reference shape in the Ethics, with counts and an
example of each, so the resolver is designed against what the source
actually does rather than against a guess about it.

Whitespace is normalised FIRST: 233 of the 422 references break across
a line, and a resolver that reads the raw text sees fewer than half.
"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S

KINDS = r"Prop|Deff|Def|Ax|Post|Coroll|Corollary|Note|Lemma|Explanation|Pt|Part"
CITE = re.compile(rf"\((?:[^()]*?\b(?:{KINDS})\b[^()]*?)\)")


def shape(s):
    """Collapse numerals so structurally identical refs group together."""
    s = re.sub(r"\b[ivxlc]+\b", "<n>", s)
    s = re.sub(r"\b[IVXLC]+\b", "<N>", s)
    s = re.sub(r"\b\d+\b", "<d>", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    parts = S.split_parts(S.body())
    seen = collections.Counter()
    example = {}
    per_part = collections.Counter()
    for n, text in parts:
        flat = re.sub(r"\s+", " ", text)
        for m in CITE.finditer(flat):
            sh = shape(m.group(0))
            seen[sh] += 1
            per_part[n] += 1
            example.setdefault(sh, (n, m.group(0)))

    print(f"{sum(seen.values())} references, {len(seen)} distinct shapes")
    print("per Part:", dict(sorted(per_part.items())))
    print()
    for sh, n in seen.most_common():
        p, ex = example[sh]
        print(f"{n:>4}  {sh[:56]:<58} e.g. Part {p}: {ex[:40]}")


if __name__ == "__main__":
    main()
