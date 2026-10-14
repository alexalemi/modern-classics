"""Choosing how each painting fills the space under the title band.

The band takes the top 27% of the cover (it was 36%, and the near-square
left under it cost a third of every painting's height, which is where the
heads were: Alex, 2026-10-13, "a lot of the crops are bad"). Under it the
picture is W : H - BAND, about 0.9, and each book chooses one of:

  wide   the cover crop's full height, widened sideways into the rest of the
         painting, inside its content box (scan margins and plain borders
         trimmed automatically, so no page edges or frame strips)
  f<n>   inside the cover crop, the window placed at n (0 = top, 1 = bottom)
  box    "box": [x0, y0, x1, y1] in source pixels, chosen by hand; it may
         reach past the picture's edge (Kamo no Chomei's head sits at the
         top of the sheet), and what lies outside is filled from "fill", a
         patch of plain paper [x0, y0, x1, y1] tiled with alternate tiles
         mirrored so it shows no seam

ebook_meta cover "band": "wide" | 0.3 ... ; the default is "wide" where the
painting has room, else 0.3.

    python3 gencover/bandcrop.py [book ...]   # review sheets of the options
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from press import W, H  # noqa: E402

BAND = 570
ASPECT = W / (H - BAND)


def cover_crop(src, art):
    sw, sh = src.size
    if art.get("crop"):
        m = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", art["crop"])
        cw, ch, x0, y0 = map(int, m.groups())
    else:
        fx, fy = art.get("focus_x", 0.5), art.get("focus_y", 0.5)
        if sw / sh > 2 / 3:
            cw, ch = int(sh * 2 / 3), sh
            x0, y0 = int((sw - cw) * fx), 0
        else:
            cw, ch = sw, int(sw * 3 / 2)
            x0, y0 = 0, int((sh - ch) * fy)
    return cw, ch, x0, y0


def content_box(src):
    """The painting without its scan margin or a plain border: walk in from
    each edge while the row or column is near-uniform (low spread)."""
    g = np.asarray(src.convert("L").resize((400, int(400 * src.height / src.width)))).astype(float)
    hh, ww = g.shape

    def walk(lines, limit):
        n = 0
        for ln in lines[:limit]:
            if ln.std() < 14:
                n += 1
            else:
                break
        return n
    top = walk([g[i] for i in range(hh)], hh // 6)
    bot = walk([g[hh - 1 - i] for i in range(hh)], hh // 6)
    lef = walk([g[:, i] for i in range(ww)], ww // 6)
    rig = walk([g[:, ww - 1 - i] for i in range(ww)], ww // 6)
    pad = 2                                   # and a little more, past the edge's shadow
    s = src.width / ww
    return (int((lef + pad * (lef > 0)) * s), int((top + pad * (top > 0)) * s),
            int(src.width - (rig + pad * (rig > 0)) * s), int(src.height - (bot + pad * (bot > 0)) * s))


def region_box(src, art, mode):
    if mode == "box":
        return tuple(art["box"])
    cw, ch, x0, y0 = cover_crop(src, art)
    if mode == "wide":
        L, T, R, B = content_box(src)
        y0c, y1c = max(y0, T), min(y0 + ch, B)
        h = y1c - y0c
        w = h * ASPECT
        if w > R - L:                         # not that much room: as wide as it goes
            w = R - L
            h = w / ASPECT
            y0c = y0c + ((y1c - y0c) - h) * 0.3
        cx = x0 + cw / 2
        left = min(max(cx - w / 2, L), R - w)
        return (left, y0c, left + w, y0c + h)
    f = float(mode)
    w, h = cw, cw / ASPECT
    top = y0 + (ch - h) * f
    return (x0, top, x0 + w, top + h)


def has_room(src, art):
    cw, ch, x0, y0 = cover_crop(src, art)
    L, T, R, B = content_box(src)
    return (R - L) >= 0.92 * (min(y0 + ch, B) - max(y0, T)) * ASPECT


def default_mode(src, art):
    return "wide" if has_room(src, art) else 0.3


def region(src, art, book=None):
    mode = art.get("band", default_mode(src, art))
    box = tuple(int(v) for v in region_box(src, art, mode))
    if box[0] < 0 or box[1] < 0 or box[2] > src.width or box[3] > src.height:
        src = padded(src, box, art)
        box = (0, 0, box[2] - box[0], box[3] - box[1])
    return src.crop(box).resize((W, H - BAND), Image.LANCZOS)


def padded(src, box, art):
    """The picture placed in a canvas the size of box, the rest paper."""
    x0, y0, x1, y1 = box
    cw, ch = x1 - x0, y1 - y0
    if art.get("fill"):
        patch = src.crop(tuple(art["fill"]))
        pw, ph = patch.size
        flips = [patch, patch.transpose(Image.FLIP_LEFT_RIGHT)]
        flipv = [f.transpose(Image.FLIP_TOP_BOTTOM) for f in flips]
        canvas = Image.new("RGB", (cw, ch))
        for j in range(0, ch, ph):
            for i in range(0, cw, pw):
                row = flips if (j // ph) % 2 == 0 else flipv
                canvas.paste(row[(i // pw) % 2], (i, j))
    else:
        g = np.asarray(src)
        edge = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])
        canvas = Image.new("RGB", (cw, ch), tuple(int(v) for v in np.median(edge, axis=0)))
    canvas.paste(src, (-x0, -y0))
    return canvas


if __name__ == "__main__":
    from PIL import ImageDraw, ImageFont
    meta = json.load(open(ROOT / "ebook_meta.json"))
    books = sys.argv[1:] or sorted(b for b, v in meta.items() if not v.get("cover", {}).get("generated"))
    out = ROOT / "build" / "covers" / "bandcrop"
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("DejaVuSans.ttf", 16)
    modes = ["wide", 0.0, 0.25, 0.5, 0.75]
    tw, th = 200, int(200 / ASPECT)
    per = 8
    for k in range(0, len(books), per):
        chunk = books[k:k + per]
        sheet = Image.new("RGB", (len(modes) * (tw + 8) * 2 + 40, len(chunk) // 2 * (th + 26) + (th + 26) * (len(chunk) % 2) + 10), "white")
        d = ImageDraw.Draw(sheet)
        for i, b in enumerate(chunk):
            src = Image.open(ROOT / "build" / "covers" / f"{b}.jpg").convert("RGB")
            art = meta[b]["cover"]
            dflt = art.get("band", default_mode(src, art))
            ox = (i % 2) * (len(modes) * (tw + 8) + 40)
            oy = (i // 2) * (th + 26)
            for j, mo in enumerate(modes):
                if mo == "box":
                    continue
                if mo == "wide" and not has_room(src, art):
                    continue
                im = src.crop(tuple(int(v) for v in region_box(src, art, mo))).resize((tw, th))
                x = ox + j * (tw + 8)
                sheet.paste(im, (x, oy + 22))
                tag = f"{b[:18]} {mo}" if (j == 0 or (j == 1 and not has_room(src, art))) else str(mo)
                d.text((x, oy + 4), tag + (" *" if mo == dflt else ""), fill="red" if mo == dflt else "black", font=font)
        sheet.save(out / f"crops{k // per + 1:02d}.png")
    print(out)
