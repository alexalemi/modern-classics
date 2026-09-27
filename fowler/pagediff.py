"""Word diff of proof leaves against another copy's OCR of the same page.

    python3 fowler/pagediff.py 671 672 673      (KV leaves)

For a page rebuilt from a scrambled draft: are all its words there, and no
more? The other copy (i0s2, the 1926 printing) is located by the leaf's first
and last eight words; line-end splits ("neighbour hood") and one-word noise
are ignored, so what is printed is a run of two or more words one side has
and the other lacks.
"""
import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCAN = (HERE / "_src" / "scan-dictionaryofmode0000hwfo_i0s2-djvu.txt").read_text(errors="replace")
SW = re.findall(r"[a-z]+", SCAN.lower())
SJ = " ".join(SW)


def words(t):
    t = re.sub(r"(?m)^page: .*$", "", t)
    return re.findall(r"[a-z]+", re.sub(r"[*^]", "", t).lower())


def find_last(keys, end):
    """Latest match of any key before `end` (a page's start is the last
    occurrence of its opening words before the next page begins)."""
    best = -1
    for k in keys:
        i = SJ.rfind(k, 0, end)
        best = max(best, i)
    return best


for n in sys.argv[1:]:
    w = words((HERE / "proof_kv" / f"{int(n):03d}.txt").read_text())
    nxt = HERE / "proof_kv" / f"{int(n) + 1:03d}.txt"
    j = -1
    tails = [" ".join(w[-k - 5:len(w) - k]) for k in range(0, 40, 3)]
    if nxt.exists():
        nw = words(nxt.read_text())
        # the next page's opening, located after this page's own ending
        for tail in tails:
            e = SJ.find(tail)
            if e >= 0:
                for k in range(0, 60, 3):
                    j = SJ.find(" ".join(nw[k:k + 5]), e)
                    if j >= 0:
                        break
                break
    if j < 0:
        for tail in tails:
            e = SJ.find(tail)
            if e >= 0:
                j = e + len(tail)
                break
    heads = [" ".join(w[k:k + 5]) for k in range(0, 60, 3)]
    i = find_last(heads, j) if j >= 0 else -1
    if i >= 0:
        k = next(k for k in range(0, 60, 3) if SJ.rfind(" ".join(w[k:k + 5]), 0, j) == i)
        for _ in range(k):
            i = SJ.rfind(" ", 0, max(0, i - 1))
        i = max(i, 0)
    if i < 0 or j < 0 or j - i > 20000:
        print(n, "could not locate the page in the other scan", i, j)
        continue
    sw = SJ[i:j].split()
    print(f"== {n}: proof {len(w)} words, other copy {len(sw)}")
    for op, a, b, c, d in difflib.SequenceMatcher(None, w, sw, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        ed, pr = w[a:b], sw[c:d]
        if "".join(ed) == "".join(pr):
            continue                                   # a split word
        if max(len(ed), len(pr)) >= 2:
            print(f"   {op:7s} proof={' '.join(ed)[:70]!r}  other={' '.join(pr)[:70]!r}")
