"""A second reading of the proof leaves that shares no code with prep.py's
stream builder (the epictetus rule): every word of the kept leaves, counted,
against every word of chapters/. Exits nonzero.

    python3 fowler/crosscheck.py

The kept leaves are the ones prep reads, listed here independently: Google
proof/ 009-078 (pp. iii-viii, 1-64) and 388-389 (pp. 374-375), KV proof_kv/
077 onward except the repeat scan 392-393. Words compare lower-cased,
accents and markup stripped. A word broken across two leaves ("ex-" | "+
pressed") is two fragments in the proofs and one word in the edition, so
each gained word is explained by two lost halves before anything is
reported; the letter headings and front-matter titles the prep writes are
the only words the edition adds.
"""
import collections
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent

LEAVES = [("proof", n) for n in range(9, 79)] + [("proof", 388), ("proof", 389)]
LEAVES += [("proof_kv", int(p.stem)) for p in sorted((HERE / "proof_kv").glob("*.txt"))
           if int(p.stem) not in (392, 393)]

# the section titles the prep writes (front matter and letters); the source
# has the front-matter headings in capitals, dropped by prep
ADDED = collections.Counter("dedication acknowledgements key to pronunciation list of general "
                            "articles".split())
DROPPED = collections.Counter("acknowledgements key to pronunciation list of general articles".split())


def words(t):
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    for a, b in (("Æ", "AE"), ("æ", "ae"), ("Œ", "OE"), ("œ", "oe")):
        t = t.replace(a, b)
    t = re.sub(r"⟦[#@][^|⟧]*\|?", " ", t).replace("⟧", " ")
    return collections.Counter(w.lower() for w in re.findall(r"[A-Za-z]+", t))


src = collections.Counter()
for d, n in LEAVES:
    t = (HERE / d / f"{n:03d}.txt").read_text()
    t = t.split("\n", 1)[1]                       # the page: line
    t = re.sub(r"^Footnote[:+] ?", "", t, flags=re.M)
    t = re.sub(r"^\+ ?", "", t, flags=re.M)
    src += words(t)
out = collections.Counter()
for p in sorted((HERE / "chapters").glob("*.txt")):
    out += words(p.read_text())
lost, gained = src - out - DROPPED, out - src - ADDED
# letter headings ("A" ... "Z") are titles in the edition, lines in the proofs
for c in "abcdefghijklmnopqrstuvwxyz":
    gained[c] = max(0, gained[c] - 1)
print(f"proof {sum(src.values()):,} words, chapters {sum(out.values()):,}")
for w, k in sorted(gained.items()):
    for _ in range(k):
        for i in range(1, len(w)):
            a, b = w[:i], w[i:]
            if lost[a] > 0 and lost[b] > 0 and (a != b or lost[a] > 1):
                lost[a] -= 1; lost[b] -= 1; gained[w] -= 1
                break
lost, gained = +lost, +gained
print("lost:", lost.most_common(30))
print("gained:", gained.most_common(30))
sys.exit(1 if lost or gained else 0)
