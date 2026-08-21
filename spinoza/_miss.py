"""Show which number tokens the translation dropped, with context."""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as C

name = sys.argv[1].zfill(3) + ".txt"
B = pathlib.Path(__file__).resolve().parent


def toks(p):
    t = C.ENUM.sub(" ", re.sub(C.CITE, " ", p.read_text())).replace("\n", " ")
    return [(m.group(0), t[max(0, m.start() - 56):m.start() + 18])
            for m in C.NUM.finditer(t)]


a = toks(B / "chapters" / name)
b = toks(B / "modern_chapters" / name)
cb = collections.Counter(x for x, _ in b)
seen = collections.Counter()
for tok, ctx in a:
    seen[tok] += 1
    if seen[tok] > cb[tok]:
        print(f"MISSING {tok}: …{ctx}")
