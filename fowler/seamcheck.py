"""Page-seam check for the Fowler proofs: a leaf whose last paragraph ends
without a stop should be followed by a leaf opening "+ " (a continuation),
and a leaf that ends on a stop is usually followed by a fresh paragraph.

    python3 fowler/seamcheck.py [kv]

Prints every seam where the two disagree. Both kinds of hit are worth
reading, and neither is always wrong: a sentence can end at the foot of a
column while its paragraph continues, and the French Words list has no
stops at all. What it has caught: a speck kept as a stop (245, 301) and a
word broken across the page with no "+ " on the next leaf (247-248).
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
d = HERE / ("proof_kv" if len(sys.argv) > 1 and sys.argv[1] == "kv" else "proof")
leaves = sorted(int(p.stem) for p in d.glob("*.txt"))
for n in leaves:
    b = d / f"{n + 1:03d}.txt"
    if not b.exists():
        continue
    last = (d / f"{n:03d}.txt").read_text().strip().split("\n\n")[-1].rstrip("*^ ")
    parts = b.read_text().split("\n\n")
    first = parts[1] if len(parts) > 1 else ""
    ends = bool(re.search(r"[.!?:;)\]—'\"]$", last))
    cont = first.startswith("+ ")
    if ends == cont:
        print(n, "ends" if ends else "OPEN", "| next", "continues" if cont else "FRESH", "|", last[-50:])
