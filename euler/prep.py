"""Euler, Lettres a une princesse d'Allemagne: Cournot's 1842 OCR -> chapters/.

    python3 euler/prep.py

Source: Archive.org lettresdeleuleru01eule / 02eule (Hachette, 1842), which
reprints the 1768-72 Petersburg text unretouched but renumbers the 234
letters as three thematic series (I: 68, II: 64, III: 102). We number them
1-234 as Euler did, and keep Cournot's series as the Part dividers.

A letter boundary is a LETTRE heading, or a date line with no heading just
above it (a heading the OCR lost). The false positives are verso running
heads the OCR split over two lines ("28 / I^re PARTIE. / LETTRE VII."),
dropped by ordinal below after checking each by eye; the series counts are
the checksum.

Cournot's footnotes are left in: they are easy to see ("(1) Le pied de
Berlin vaut...") and the translators drop them. Figures are cited by the
number on the plate, which restarts in the second volume (letter 115).
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
V1 = (HERE / "source/scan-lettresdeleuleru01eule-djvu.txt").read_text().split("\n")
V2 = (HERE / "source/scan-lettresdeleuleru02eule-djvu.txt").read_text().split("\n")

a = next(i for i, l in enumerate(V1) if l.strip().startswith("PREMIERE  PARTIE"))
b = next(i for i, l in enumerate(V1) if l.strip() == "TABLE")
c = next(i for i, l in enumerate(V2) if "SUITE  DE  LA" in l)
d = next(i for i, l in enumerate(V2) if l.strip().startswith("FIN ") and "TOM" in l)
lines = V1[a:b] + V2[c:d]
VOL2_START = len(V1[a:b])

MON = r"janv|f[ée]v|mars|avr|mai|m\.ii|juin|jum|juil|jail|ao[uû]t|sept|oct|ocl|nov|d[ée]c|aéc"
DATE = re.compile(r"^\W{0,6}\S{0,3}\s*\d{0,2}\S?\s+(" + MON + r")\S*\s+\S{3,6}\s*\S?\)?\s*\S?\s*$", re.I)
HEAD = re.compile(r"^\s*LETTRE\s+\S+\s*$")

heads = [i for i, l in enumerate(lines) if HEAD.match(l)]
dates = [i for i, l in enumerate(lines) if DATE.match(l)]
cands = sorted(set(heads) | {i for i in dates if not any(0 < i - h <= 6 for h in heads)})
bounds = []
for x in cands:
    if bounds and x - bounds[-1] <= 6:
        continue
    bounds.append(x)
# Split running heads, 1-based ordinals among the candidates (checked by eye).
RUNNING = {8, 14, 36, 38, 62, 112, 142, 148, 233}
drop = {bounds[k - 1] for k in RUNNING}
bounds = [x for k, x in enumerate(bounds, 1) if k not in RUNNING]
assert len(bounds) == 234, len(bounds)
series = [i for i, l in enumerate(lines) if re.match(r"^\s*(DEUXI|TROISI)\S*\s+PARTIE", l)]
import bisect
assert [bisect.bisect(bounds, p) for p in series] == [68, 132], series

RUNHEAD = re.compile(r"PARTI[ER]|PA\.?I+RT|^\s*\S{0,6}\s*PA\S{0,4}TIE")
RECTO = re.compile(r"^[A-ZÉÈÀÊÇ'’\s\.,;\-]{4,}\s+\S{1,4}\s*$")
JUNK = re.compile(r"^\s*(\S{1,3}|\d{1,3}\S?\.?)\s*$")


def clean(block):
    out = []
    for l in block:
        s = l.strip()
        if len(s) < 60 and RUNHEAD.search(s):
            continue
        if RECTO.match(s) and not HEAD.match(s) and s.upper() == s:
            continue
        if s and JUNK.match(s):
            continue
        out.append(s)
    text = "\n".join(out)
    text = re.sub(r"(?<=\w)[-­]\n(?=[a-zàâçéèêëîïôûùüÿœ])", "", text)
    paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(re.sub(r"\s{2,}", " ", p) for p in paras if p)


letters = []
for k, start in enumerate(bounds):
    end = bounds[k + 1] if k + 1 < len(bounds) else len(lines)
    block = [l for i, l in enumerate(lines[start:end], start) if i not in drop]
    if HEAD.match(block[0]):
        block = block[1:]
    letters.append((k + 1, start >= VOL2_START, clean(block)))

# Cournot's own description of his three series (preface, p. x).
PARTS = {1: "Part One: Physics and the Universe",
         69: "Part Two: Mind, Logic and Morals",
         133: "Part Three: Physics in Particular"}
# The six folding plates, each set at the letter that first cites one of its
# figures (same markers as modern_chapters/, so verify.py can match them).
PLATES = {
    3: '[Figure platea: Plate I of the first volume, Figures 1 to 38: the letters on sound, air, light, the eye, mirrors, gravity and the solar system.]',
    102: '[Figure plateb: Plate II of the first volume, Figures 39 to 89: the circles with which Euler draws propositions and syllogisms.]',
    123: '[Figure platec: Plate I of the second volume, Figures 1 to 27: infinite divisibility, electricity, the globe and its circles, longitude, and the compass.]',
    178: '[Figure plated: Plate II of the second volume, Figures 28 to 65: magnets and their armatures, and the kinds of lenses.]',
    194: '[Figure platee: Plate III of the second volume, Figures 66 to 95: the dark room, magnifying glasses, microscopes and spyglasses.]',
    213: '[Figure platef: Plate IV of the second volume, Figures 96 to 127: telescopes, the horizon moon, twilight and the refraction of the air.]',
}

TARGET = 5500

chunks, cur = [], []
for n, v2, text in letters:
    wc = len(text.split())
    if cur and (n in PARTS or sum(len(t.split()) for _, _, t in cur) + wc > TARGET):
        chunks.append(cur)
        cur = []
    cur.append((n, v2, text))
if len(cur) == 1 and not cur[0][0] in PARTS:
    chunks[-1] += cur
else:
    chunks.append(cur)

(HERE / "chapters").mkdir(exist_ok=True)
manifest = []
for f, ch in enumerate(chunks):
    lo, hi = ch[0][0], ch[-1][0]
    body = []
    for n, v2, text in ch:
        plate = f"{PLATES[n]}\n\n" if n in PLATES else ""
        body.append(f"=== LETTER {n} (figures: {'second' if v2 else 'first'} volume) ===\n\n{plate}{text}")
    name = f"{f:03d}.txt"
    (HERE / "chapters" / name).write_text("\n\n".join(body) + "\n")
    e = {"file": name, "title": f"Letters {lo}–{hi}" if hi > lo else f"Letter {lo}",
         "part": 1, "of": 1, "words": sum(len(t.split()) for _, _, t in ch),
         "letters": f"{lo}-{hi}"}
    if lo in PARTS:
        e["part_before"] = PARTS[lo]
    manifest.append(e)
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(len(chunks), "files;", sum(e["words"] for e in manifest), "words;",
      "max", max(e["words"] for e in manifest))
