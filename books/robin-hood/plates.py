"""Fetch Pyle's 44 illustrations from the 1883 first edition and crop them.

    python3 books/robin-hood/plates.py [cache_dir]

Source: archive.org merryadventureso00pylerich (New York: Scribner, 1883;
University of California Libraries copy, NOT_IN_COPYRIGHT). Each leaf is
fetched at full scan resolution (2384x3392) as page/n{leaf}.jpg into
cache_dir (default $TMPDIR/robin-hood-leaves), cropped, and written to
site/images/robin-hood/fig{id}.jpg at most 1000px wide, in grayscale, the paper
levelled to white (levels 40..210).

Full-page plates (box None) are trimmed to their ink automatically. A
head-piece or tail-piece shares its page with text, so it gets a rough
box in 1/8-scale coordinates (x0, y0, x1, y1 on a 298x424 thumbnail),
inside which the crop is trimmed to the ink. The boxes were read off
gridded thumbnails and every crop was then looked at.

The Gutenberg HTML (#10148) carries only twelve of these, all from the
first chapters, which is why the scan is used.
"""

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site" / "images" / "robin-hood"
IA = "https://archive.org/download/merryadventureso00pylerich/page/n{}.jpg"
S = 8

# id -> (leaf, box or None). Order is the 1883 list of illustrations.
PLATES = {
    "front": (11, None),
    "headpreface": (14, (25, 40, 275, 112)),
    "tailpreface": (15, (100, 250, 200, 335)),
    "bridge": (29, None),
    "headprologue": (30, (20, 30, 265, 165)),
    "tailprologue": (39, (75, 298, 250, 370)),
    "tinker": (41, None),
    "headone": (42, (10, 35, 250, 125)),
    "kinglondon": (53, None),
    "palmer": (68, None),
    "tailone": (73, (85, 186, 215, 270)),
    "butcher": (75, None),
    "headtwo": (76, (5, 35, 270, 125)),
    "eric": (91, None),
    "cook": (101, None),
    "bland": (107, None),
    "headthree": (108, (15, 40, 265, 130)),
    "scarlet": (120, None),
    "miller": (137, None),
    "tailthree": (141, (80, 215, 230, 315)),
    "fountain": (143, None),
    "headfour": (144, (25, 35, 260, 110)),
    "friarsong": (166, None),
    "bride": (178, None),
    "tailfour": (183, (60, 280, 215, 390)),
    "knight": (185, None),
    "headfive": (186, (25, 30, 275, 180)),
    "prior": (204, None),
    "tailfive": (213, (70, 290, 240, 395)),
    "lasses": (215, None),
    "headsix": (216, (30, 35, 270, 140)),
    "engrosser": (240, None),
    "tailsix": (245, (95, 290, 215, 385)),
    "queen": (247, None),
    "headseven": (248, (25, 30, 275, 135)),
    "escape": (271, None),
    "tailseven": (281, (95, 160, 215, 270)),
    "gisbourne": (283, None),
    "headeight": (284, (25, 35, 255, 163)),
    "bargain": (309, None),
    "taileight": (314, (90, 240, 215, 345)),
    "lastshaft": (317, None),
    "headepilogue": (318, (20, 40, 260, 155)),
    "finis": (325, (40, 238, 265, 380)),
}


def crop(src, box):
    im = Image.open(src).convert("L")
    a = np.asarray(im)
    x0, y0, x1, y1 = [v * S for v in (box or (10, 10, 288, 414))]
    sub = a[y0:y1, x0:x1]
    ink = ndimage.binary_opening(sub < 110, iterations=1)
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=6))
    sizes = ndimage.sum(ink, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 400]) & ink
    ys, xs = np.nonzero(keep)
    pad = 20
    bx0, by0 = max(xs.min() - pad, 0) + x0, max(ys.min() - pad, 0) + y0
    bx1 = min(xs.max() + pad, sub.shape[1]) + x0
    by1 = min(ys.max() + pad, sub.shape[0]) + y0
    c = im.crop((bx0, by0, bx1, by1))
    if c.width > 1000:
        c = c.resize((1000, round(c.height * 1000 / c.width)), Image.LANCZOS)
    # whiten the yellowed paper and deepen the ink: levels 40..210
    return c.point(lambda v: 0 if v < 40 else 255 if v > 210 else
                   round((v - 40) * 255 / 170))


def main():
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else
                 os.path.join(os.environ.get("TMPDIR", "/tmp"), "robin-hood-leaves"))
    cache.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for pid, (leaf, box) in PLATES.items():
        src = cache / f"n{leaf}.jpg"
        if not src.exists() or src.stat().st_size < 10000:
            subprocess.run(["curl", "-sL", "--max-time", "120", "-o", str(src),
                            IA.format(leaf)], check=True)
        c = crop(src, box)
        # assemble.figure_name: the frontispiece is front.jpg, not figfront
        name = "front.jpg" if pid == "front" else f"fig{pid}.jpg"
        c.save(OUT / name, quality=80, optimize=True)
        print(pid, leaf, c.size)


if __name__ == "__main__":
    main()
