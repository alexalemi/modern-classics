"""Markup balance per paragraph for the Fowler proofs.

    python3 fowler/markcheck.py

A paragraph must open and close every **bold**, *italic* and ^^small caps^^
it uses. A "+ " continuation is checked together with the paragraph it
continues, since ruling 14 closes a span at a column or leaf end and reopens
it after the "+ ". Prints every paragraph that does not balance.
"""
import re, glob
from pathlib import Path
HERE = Path(__file__).parent

def tokens(p):
    p = p.replace("***", "\x01\x02")          # bold-italic delimiter = both toggles
    b = p.count("**") + p.count("\x01")
    i = len(re.findall(r"(?<!\*)\*(?!\*)", p.replace("**", ""))) + p.count("\x02")
    s = p.count("^^")
    return b, i, s

bad = 0
for d in ("proof", "proof_kv"):
    units = []                                 # (where, text): "+ " joins the unit before it
    for f in sorted((HERE / d).glob("*.txt")):
        for k, p in enumerate(f.read_text().split("\n\n")[1:]):
            if p.startswith("+ ") and units:
                prev, cont = units[-1][1], p[2:]
                # a span left open at the break and reopened after "+ " is one span
                if tokens(prev)[1] % 2 and cont.startswith("*") and not cont.startswith("**"):
                    cont = cont[1:]
                units[-1] = (units[-1][0], prev + " " + cont)
            else:
                units.append((f"{d}/{f.name} para {k + 1}", p))
    for where, p in units:
        b, i, s = tokens(p)
        if b % 2 or i % 2 or s % 2:
            bad += 1
            print(f"{where}: bold {b} italic {i} smallcaps {s} | {p[:90]!r}")
print(bad, "unbalanced paragraphs")
