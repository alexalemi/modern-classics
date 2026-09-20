"""Asa Gray, How Plants Grow: cut the woodcuts out of the page scans.

    python3 gray-plants/plates.py

Each proof/NNN.plates line is <ids> TAB <box[ - blank box ...]> TAB
<printed label> TAB <caption>, the box read off png/NNN.png by the
proofreading pass (see proof_instructions.txt). A woodcut that wraps round
text carries minus-boxes, whitened before anything else, so no transcribed
text ships inside an image.

The cut is then CLEANED on the thompson/replate.py pattern: darkness maps to
alpha over pure black, with "paper" read at the 99th percentile of the cut
(not the mode, which a heavily inked cut would get wrong), and the alpha
quantised to 32 levels so the PNG compresses. The ink survives anti-aliased
as the scan had it; the cream paper and its foxing go.

Writes _src/plates/NNN-k.png and returns [{leaf, k, ids, printed, caption}].
"""
import re
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "_src"


def boxes(field):
    parts = [p.strip() for p in field.split(" - ")]
    q = [tuple(int(v) for v in p.split(",")) for p in parts]
    for b in q:
        assert len(b) == 4 and b[0] < b[2] and b[1] < b[3], field
    return q[0], q[1:]


def read(leaf):
    f = HERE / "proof" / f"{leaf:03d}.plates"
    if not f.exists():
        return []
    out = []
    for k, line in enumerate(l for l in f.read_text().splitlines() if l.strip()):
        cells = line.split("\t")
        assert len(cells) == 4, f"{f.name}: {line[:60]!r} has {len(cells)} fields"
        ids, box, printed, caption = (c.strip() for c in cells)
        assert re.fullmatch(r"(?:\d+[a-z]?|x\d+)(?:-\d+[a-z]?)*", ids), (f.name, ids)
        main, minus = boxes(box)
        out.append({"leaf": leaf, "k": k, "ids": ids, "box": main, "minus": minus,
                    "printed": printed, "caption": caption})
    return out


def clean(im):
    a = np.asarray(im.convert("L"), dtype=np.float64)
    paper = np.percentile(a, 99)
    ink = min(np.percentile(a, 0.5), paper - 40)
    # paper texture and foxing sit within a few dozen levels of the paper;
    # a floor that far down clears the grey haze without thinning the
    # engraver's finest hatching, which prints near full black
    floor = 0.22 * (paper - ink)
    alpha = np.clip((paper - a - floor) / max(1.0, paper - ink - floor), 0, 1)
    alpha = np.round(alpha * 31) / 31
    rgba = np.zeros(a.shape + (4,), dtype=np.uint8)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def cut(p):
    page = Image.open(SRC / "png" / f"{p['leaf']:03d}.png").convert("L")
    W, H = page.size
    x0, y0, x1, y1 = p["box"]
    assert x1 <= W + 2 and y1 <= H + 2, (p["leaf"], p["ids"], p["box"], page.size)
    page = page.copy()
    for b in p["minus"]:
        page.paste(255, b)
    return clean(page.crop((x0, y0, min(x1, W), min(y1, H))))


def main(leaves):
    (SRC / "plates").mkdir(exist_ok=True)
    rows = []
    for leaf in leaves:
        for p in read(leaf):
            cut(p).save(SRC / "plates" / f"{leaf:03d}-{p['k']}.png", optimize=True)
            rows.append(p)
    return rows


if __name__ == "__main__":
    import sys
    rs = main(range(0, 256))
    print(len(rs), "plates")
