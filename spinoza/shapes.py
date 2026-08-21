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

# THE DETECTOR MUST SEE LOWER CASE. This pattern was originally
# compiled without re.I over a list with "Note" capitalised, so
# "(II. xl. note)" -- Part 2's single commonest reference form, 77 of
# them -- matched nothing at all, and 171 references in the book were
# invisible to the resolver, to the validator and to every count this
# pipeline printed. All of those counts agreed with each other because
# they came from this one blind regex; self-consistency was never
# evidence. (The grimm 151* defect, in its cheapest form.)
#
# But widening it cannot simply lower-case the list, because Elwes also
# writes ordinary English inside parentheses: "(by the definition of
# pain)", "(whose character is too well known to need definition
# here)", "(supposing the proposition to be denied)". Those are prose,
# not pointers. What separates a citation from a sentence is that a
# citation carries either A NUMERAL or A RELATIVE MARKER beside its
# kind word.
KINDS = (r"[Pp]rop(?:osition)?s?|[Dd]eff|[Dd]ef(?:inition)?s?|"
         r"[Aa]xioms?|[Aa]x|[Pp]ost(?:ulate)?s?|[Cc]orolls?|"
         r"[Cc]orollary|[Cc]orollaries|[Nn]otes?|[Ll]emmas?|"
         r"[Ee]xplanations?|Pt|Part|[Pp]reface|[Aa]ppendix")
NUMERAL = r"\b(?:[IVXLC]+|[ivxlc]+|\d+)\b"
# "general" and "preface" earn their place here: "(by the general
# Def. of the Emotions)" and "(see preface to this Part)" carry no
# numeral and no relative marker, so the numeral-or-relative rule
# dropped them out of the count altogether -- refused references are
# still references and must be seen in order to be refused.
RELMARK = r"\b(?:last|foregoing|preceding|first|same|general|preface)\b"

_KIND_RE = re.compile(rf"\b(?:{KINDS})\b")
_NUM_RE = re.compile(NUMERAL)
_REL_RE = re.compile(RELMARK, re.I)
_PAREN = re.compile(r"\([^()]{0,200}\)")


class _Cite:
    """CITE.fullmatch(s) / CITE.finditer(text), as before, but with the
    numeral-or-relative rule instead of a bare keyword list."""

    @staticmethod
    def _is_cite(s):
        if not _KIND_RE.search(s):
            return False
        return bool(_NUM_RE.search(s) or _REL_RE.search(s))

    def fullmatch(self, s):
        return self._is_cite(s) if _PAREN.fullmatch(s) else None

    def finditer(self, text):
        for m in _PAREN.finditer(text):
            if self._is_cite(m.group(0)):
                yield m


CITE = _Cite()


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
