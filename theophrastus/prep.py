"""Build chapters/ + manifest.json for Theophrastus' Characters from
source.txt (Gutenberg #58242, the Bennett & Hammond translation, 1902).

Thirty character sketches headed "N _The So-and-So_" plus the Epistle
Dedicatory ("Theophrastus to Polycles" — probably spurious, but read
with the book for centuries; kept as the opening section). Bennett &
Hammond's introduction and their footnotes are apparatus and are
dropped; the (Greek) term under each heading is kept on its own line
after the title.

Output: 3 files of ten sketches each (whole book ~13k words); sketch
headings become "N. The So-and-So" standalone subheading lines. The
dedication opens file 000.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent

text = BOOK.joinpath("source.txt").read_text()
start = text.index("THEOPHRASTUS TO POLYCLES:")
end = text.index("*** END OF THE PROJECT GUTENBERG")
text = text[start:end]

heads = list(re.finditer(r"^([IVX]+) _(.+)_$", text, flags=re.M))
assert len(heads) == 30, len(heads)

ROMAN = {"I": 1, "V": 5, "X": 10}


def roman(s):
    total = 0
    for a, b in zip(s, s[1:] + "\0"):
        total += -ROMAN[a] if ROMAN[a] < ROMAN.get(b, 0) else ROMAN[a]
    return total


def clean(body):
    paras = []
    for p in re.split(r"\n\s*\n", body):
        if not p.strip():
            continue
        if re.match(r"^\[\d+\]", p.strip()):     # footnote block
            continue
        text = " ".join(p.split())
        text = re.sub(r"\[\d+\]", "", text)
        text = text.replace("_", "")
        paras.append(text)
    return paras


# dedication (before the first sketch)
ded = clean(text[len("THEOPHRASTUS TO POLYCLES:"): heads[0].start()])

sketches = []
for i, m in enumerate(heads):
    end_pos = heads[i + 1].start() if i + 1 < len(heads) else len(text)
    body = text[m.end(): end_pos]
    greek = ""
    gm = re.match(r"\s*\(([^)]+)\)", body)
    if gm:
        greek = gm.group(1)
        body = body[gm.end():]
    n = roman(m.group(1))
    assert n == i + 1
    sketches.append((n, m.group(2), greek, clean(body)))

manifest = []
for fi in range(3):
    group = sketches[fi * 10: fi * 10 + 10]
    lo, hi = group[0][0], group[-1][0]
    title = f"Characters {lo}–{hi}"
    out = [title]
    if fi == 0:
        out.append("\nTheophrastus to Polycles\n\n" + "\n\n".join(ded))
    for n, name, greek, paras in group:
        out.append(f"\n{n}. {name}\n\n" + "\n\n".join(paras))
    content = "\n".join(out) + "\n"
    fn = f"{fi:03d}.txt"
    BOOK.joinpath("chapters", fn).write_text(content)
    manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                     "words": len(content.split()),
                     "sketches": f"{lo}-{hi}"})

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
for m in manifest:
    print(m["file"], m["title"], m["words"])
