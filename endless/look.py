"""Crop the 1945 page image around a phrase, for settling a reading.

    python3 endless/look.py "phrase" [more phrases] -> $TMPDIR/look-N.png
"""
import io
import os
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import abbyy  # noqa: E402

want = sys.argv[1:]
found = {}
for leaf, ps in abbyy.pages():
    for p in ps:
        flat = re.sub(r"[\s­*]", "", p["text"])
        for w in want:
            if w not in found and re.sub(r"\s", "", w) in flat:
                # rough line position: the phrase's share of the paragraph
                frac = flat.find(re.sub(r"\s", "", w)) / max(1, len(flat))
                found[w] = (leaf, p, frac)
    if len(found) == len(want) or leaf > 60:
        break
z = zipfile.ZipFile(HERE / "_src/scan_jp2.zip")
for k, w in enumerate(want):
    if w not in found:
        print("NOT FOUND", w)
        continue
    leaf, p, frac = found[w]
    im = Image.open(io.BytesIO(z.read(f"scienceendlessfr00unit_0_jp2/scienceendlessfr00unit_0_{leaf:04d}.jp2"))).convert("L")
    sy = im.height / p["ph"]
    y = (p["t"] + frac * (p["b"] - p["t"])) * sy
    c = im.crop((0, max(0, int(y - 260)), im.width, min(im.height, int(y + 260))))
    c = c.resize((c.width // 2, c.height // 2))
    out = Path(os.environ.get("TMPDIR", "/tmp")) / f"look-{k}.png"
    c.save(out)
    print(k, "leaf", leaf, w, "->", out)
