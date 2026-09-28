"""Ibn Tufayl, Hayy ibn Yaqzan -> chapters/.

    python3 hayy/prep.py

Story: Arabic Wikisource, حي بن يقظان (raw wikitext). That text begins at the
story ("ذكر سلفنا الصالح") and lacks Ibn Tufayl's prologue. No other Arabic
text was reachable (Shamela has the same gap; Hindawi and Archive.org were
blocked or down on 2026-09-28), so file 000 is the prologue in Ockley's 1708
English (source/prologue.txt, footnote markers removed), retold from that and
declared in the introduction. Replace it with the Arabic when one is found.
The story and the
closing address are split into four files at paragraph boundaries.

English crib: Simon Ockley's 1708 translation, Project Gutenberg #16831
(source/ockley.txt), Ibn Tufayl's introduction at its line 258, the story
from line 842.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
raw = (HERE / "source/wikisource.wiki").read_text()
raw = re.sub(r"\{\{[^{}]*\}\}", "", raw)
raw = re.sub(r"\[\[تصنيف:[^\]]*\]\]", "", raw)
raw = re.sub(r"'''?", "", raw)
paras = [re.sub(r"\s+", " ", p).strip() for p in raw.split("\n") if p.strip()]

K = 4
total = sum(len(p.split()) for p in paras)
chunks, cur, acc = [], [], 0
for p in paras:
    cur.append(p)
    acc += len(p.split())
    if len(chunks) < K - 1 and acc >= total * (len(chunks) + 1) / K:
        chunks.append(cur)
        cur = []
chunks.append(cur)

TITLE = "The Story of Hayy ibn Yaqzan"
out = HERE / "chapters"
out.mkdir(exist_ok=True)
manifest = []
prologue = HERE / "source/prologue.txt"
if prologue.exists():
    text = prologue.read_text().strip() + "\n"
    (out / "000.txt").write_text(text)
    manifest.append({"file": "000.txt", "title": "Ibn Tufayl's Introduction",
                     "part": 1, "of": 1, "words": len(text.split())})
for i, ch in enumerate(chunks, 1):
    name = f"{i:03d}.txt"
    text = "\n\n".join(ch) + "\n"
    (out / name).write_text(text)
    manifest.append({"file": name, "title": TITLE, "part": i, "of": K,
                     "words": len(text.split())})
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print([(m["file"], m["words"]) for m in manifest])
