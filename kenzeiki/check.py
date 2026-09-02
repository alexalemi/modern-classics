#!/usr/bin/env python3
"""Mechanical checks for the Kenzeiki working set.

The euclid-rivals per-book pattern. Nothing here checks the TRANSLATION;
it checks that the bookkeeping four files do about the same 238 half-leaves
agrees with itself. Each check exists because its defect was actually made:

 1. PLATE IDS. plates.txt was written with a caption keyed to n028r, which
    readorder classifies as text and layers classifies as apparatus. The
    caption was right and the plate existed; only the id was wrong, and
    nothing compared the two files. A wrong id here would put a woodcut on
    the wrong page at assembly, or drop it.
 2. TRANSLATION PARITY. every english/NNN.txt needs a transcript/NNN.txt
    and vice versa: a leaf transcribed and not rendered is silent loss.
 3. CLASSIFICATION COVERAGE. every translated leaf must be classified in
    layers.txt, so no leaf is rendered without a decision recorded about
    its apparatus.
 4. TAB DISCIPLINE. a quoted document is set tab-indented; assemble.py
    joins untabbed lines into running prose, so ONE LOST TAB turns a
    letter into a paragraph (the inferno lesson) and nothing else sees it.

Exits nonzero on any finding (the epictetus rule: a checker that cannot
fail a build will eventually be ignored).
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).parent
bad = []

def load_readorder():
    kind = {}
    for line in (HERE / "readorder.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0].startswith("n"):
            kind[parts[0]] = parts[2]
    return kind

kind = load_readorder()

# 1. plate ids
plate_ids = re.findall(r"^(n\d{3}[rl])\s+\S", (HERE / "plates.txt").read_text(), re.M)
for pid in plate_ids:
    if pid not in kind:
        bad.append(f"plates.txt: {pid} is not a leaf in readorder.txt")
    elif kind[pid] != "PICTURE":
        bad.append(f"plates.txt: {pid} is classified {kind[pid]}, not PICTURE")
if len(plate_ids) != len(set(plate_ids)):
    bad.append("plates.txt: a leaf is captioned twice")

# 2. translation parity
tr = {p.stem for p in (HERE / "transcript").glob("n*.txt")}
en = {p.stem for p in (HERE / "english").glob("n*.txt")}
for leaf in sorted(tr - en):
    bad.append(f"{leaf}: transcribed but not rendered")
for leaf in sorted(en - tr):
    bad.append(f"{leaf}: rendered but not transcribed")

# 3. classification coverage
classified = set(re.findall(r"^(n\d{3}[rl])\s+\S", (HERE / "layers.txt").read_text(), re.M))
for leaf in sorted(en - classified):
    bad.append(f"{leaf}: rendered but not classified in layers.txt")

# 4. tab discipline -- a quoted block must not lose its indent mid-block
for p in sorted((HERE / "english").glob("n*.txt")):
    lines = p.read_text().splitlines()
    for i in range(1, len(lines) - 1):
        if lines[i - 1].startswith("\t") and lines[i + 1].startswith("\t") \
           and lines[i] and not lines[i].startswith("\t"):
            bad.append(f"{p.stem}: line {i+1} lost its tab inside an indented block")

for b in bad:
    print(b)
print(f"\n{len(plate_ids)} plates, {len(en)} leaves rendered, {len(classified)} classified, "
      f"{len(bad)} finding(s)")
sys.exit(1 if bad else 0)
