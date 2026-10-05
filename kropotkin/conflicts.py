"""Crop the Duke page line for each unsettled conflict, numbered, into
contact sheets _src/thumbs/conf{N}.png, and list them.

    python3 kropotkin/conflicts.py
"""
import glob
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import merge as M  # noqa: E402

A, B, C, mB, mC, out, ins, log, conflicts = M.run()
files = sorted(glob.glob(str(HERE / "_src/jp2/*.jp2")))
crops = []
for n, c in enumerate(conflicts):
    lo = c["lo"]
    j = lo
    while j >= 0 and j not in mB:
        j -= 1
    b = B[mB[j]] if j >= 0 else None
    print(f"{n:3d} leaf {c['leaf']}: A={c['A'][:50]!r} T={c['T'][:50]!r} B={(c['B'] or '')[:40]!r} C={(c['C'] or '')[:40]!r}")
    if b is None:
        continue
    x0, y0, x1, y1 = b["box"]
    im = Image.open(files[b["leaf"] + 1]).convert("L").crop((max(0, x0 - 20), y0 - 70, x1 + 20, y1 + 70))
    im.thumbnail((1100, 400))
    crops.append((n, im))
for s in range(0, len(crops), 12):
    part = crops[s:s + 12]
    H = sum(im.size[1] + 22 for _, im in part)
    sheet = Image.new("L", (1120, H), 255)
    d = ImageDraw.Draw(sheet)
    y = 0
    for n, im in part:
        d.text((4, y + 2), f"#{n}", fill=0)
        sheet.paste(im, (10, y + 18))
        y += im.size[1] + 22
    sheet.save(HERE / f"_src/thumbs/conf{s // 12}.png")
print(len(crops), "crops")
