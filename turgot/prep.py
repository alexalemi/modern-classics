"""Turgot, Réflexions sur la formation et la distribution des richesses -> chapters/.

    python3 turgot/prep.py

Source: French Wikisource, Œuvres de Turgot, ed. Eugène Daire (Guillaumin,
1844), tome I, pp. 7-67. The 100 numbered sections run from § I to § C;
the editors' notes (Daire's, marked "Hte D.", and Dupont de Nemours's)
are gathered after § C by Wikisource and are dropped here. Split into four
files at section boundaries, as one essay in four parts.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "source/wikisource.txt").read_text()
start = src.index("§ I. —")
# Dupont de Nemours's "Observations" on Adam Smith follow § C: not Turgot's.
end = src.index("Observations sur les points dans lesquels Adam Smith")
body = src[start:end].replace(" ", " ")

secs = re.split(r"\n(?=§ [IVXLC]+\b)", body)
assert len(secs) == 100, len(secs)

paras = lambda t: "\n\n".join(re.sub(r"\s+", " ", p).strip()
                             for p in re.split(r"\n\s*\n", t) if p.strip())
secs = [paras(s) for s in secs]

K = 4
total = sum(len(s.split()) for s in secs)
chunks, cur, acc = [], [], 0
for s in secs:
    cur.append(s)
    acc += len(s.split())
    if len(chunks) < K - 1 and acc >= total * (len(chunks) + 1) / K:
        chunks.append(cur)
        cur = []
chunks.append(cur)

TITLE = "Reflections on the Formation and Distribution of Wealth"
(HERE / "chapters").mkdir(exist_ok=True)
manifest = []
n = 0
for i, ch in enumerate(chunks):
    name = f"{i:03d}.txt"
    text = "\n\n".join(ch) + "\n"
    (HERE / "chapters" / name).write_text(text)
    manifest.append({"file": name, "title": TITLE, "part": i + 1, "of": K,
                     "words": len(text.split()),
                     "sections": f"{n + 1}-{n + len(ch)}"})
    n += len(ch)
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print([(m["sections"], m["words"]) for m in manifest])
