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


for n in sys.argv[1:]:
    w = words((HERE / "proof_kv" / f"{int(n):03d}.txt").read_text())
    head = " ".join(w[:6])
    i = SJ.find(head)
    nxt = HERE / "proof_kv" / f"{int(n) + 1:03d}.txt"
    j = -1
    if nxt.exists():
        nw = words(nxt.read_text())
        for k in range(0, 8):                          # skip a split first word
            j = SJ.find(" ".join(nw[k:k + 6]), i + 1)
            if j > i:
                break
    if i < 0 or j < 0:
        tail = " ".join(w[-6:])
        j = SJ.find(tail, i)
        j = j + len(tail) if j >= 0 else -1
    if i < 0 or j < 0:
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
