"""python3 books/laws-of-thought/patch_modern.py, after prep.py.

Carry formula corrections from chapters/ into modern_chapters/ by position
(the identity check guarantees the same formulas in the same order)."""
import re, sys
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mathml
TEXT = [(r"\(18\).", "18."), (r"\(19\).", "19."), (r"\(20\).", "20."), (r"(I. \(12\))", "(I. 12)"),
        (r"\(1\)st", "1st"), (r"\(2\)ndly", "2ndly"), (r"&\(c\).", "&c.")]
for n in range(0, 31):
    f = f"{n:03d}.txt"
    src = open("chapters/" + f).read()
    mod = open("modern_chapters/" + f).read()
    m0 = mod
    for a, b in TEXT:
        if a in mod and a not in src:
            mod = mod.replace(a, b)
    S = [m.group(0) for m in mathml.MATH.finditer(src)]
    M = list(mathml.MATH.finditer(mod))
    if len(S) != len(M):
        print(f, "COUNT MISMATCH", len(S), len(M)); continue
    out, last, ch = [], 0, 0
    for s, m in zip(S, M):
        out.append(mod[last:m.start()]); out.append(s); last = m.end()
        if s != m.group(0): ch += 1
    out.append(mod[last:])
    mod = "".join(out)
    if mod != m0:
        open("modern_chapters/" + f, "w").write(mod)
        print(f, "patched", ch, "formulas")
