"""Front covers for books that keep a PAINTING: the Dover series' title
band across the top, the artwork full bleed below.

The band is a flat ink sampled from the painting itself (a colour of the
picture, dark and saturated enough for cream lettering knocked out of
it), the type is the same as the generated covers', and the line where
band meets picture is hand-cut and misregistered like the rest of the
series. One series look for both kinds of cover.

    python3 gencover/artcover.py BOOK ...     -> build/covers/framed/BOOK.jpg
"""
import colorsys
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
from press import Press, W, H, PAPER   # noqa: E402
from designs import GROT              # noqa: E402

BAND = 760


# the band's colour is the SHELF's (Alex, 2026-10-12), the way Penguin coloured
# its covers by category; restored editions go by TOPIC
SHELF_INK = {
    "Science": "cobalt", "Physical sciences": "cobalt", "Life sciences": "teal",
    "Philosophy": "teal", "Politics, War & Law": "red", "Economics": "olive",
    "Tales & Novels": "orange", "Stories and verse": "orange",
    "Epic, Myth & Tragedy": "violet", "Histories & Lives": "brown",
    "The Art of Living": "olive", "Mathematics & Logic": "magenta", "Mathematics": "magenta",
}


def shelf_ink(book):
    from press import INKS
    env = env_of(book)
    key = env.get("SHELF") or env.get("TOPIC") or ""
    return INKS[SHELF_INK[key]] if key in SHELF_INK else None


def band_colour(art):
    """One of the series' own spot inks (press.INKS), chosen to answer the
    painting: the hue of its most saturated pixels picks the nearest ink.
    Old paintings are mostly brown varnish, so sampling the picture's own
    colours gave nearly every book the same mud; the series inks keep the
    list as varied as the Dover shelf."""
    from press import INKS
    a = np.asarray(art.convert("RGB").resize((120, 180))).reshape(-1, 3) / 255
    hls = np.array([colorsys.rgb_to_hls(*px) for px in a])
    vivid = hls[(hls[:, 2] > 0.30) & (hls[:, 1] > 0.15) & (hls[:, 1] < 0.85)]
    cands = {k: v for k, v in INKS.items() if k not in ("black", "sky", "yellow", "mustard", "lime")}
    if len(vivid) < 40:                     # a monochrome picture: a deep blue band
        return INKS["cobalt"]
    w = vivid[:, 2] ** 2
    ang = np.angle((w * np.exp(2j * np.pi * vivid[:, 0])).sum()) / (2 * np.pi) % 1
    ang = (ang + 0.5) % 1          # the complement: a band that sets the picture off
    def hdist(a, b):
        d = abs(a - b) % 1
        return min(d, 1 - d)
    cands = {k: v for k, v in cands.items() if k not in ("brown", "olive")}
    best = min(cands, key=lambda k: hdist(colorsys.rgb_to_hls(*cands[k])[0], ang))
    return INKS[best]


def env_of(book):
    d = ROOT / "books" / book / "env"
    return dict(re.findall(r"^(\w+)=(.*)$", d.read_text(), re.M))


def title_lines(title, maxchars=14):
    words, lines, cur = title.upper().split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxchars:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


# where the picture's subject is, top (0) to bottom (1), when the band would
# otherwise crop it: Millais's bubble floats at the very top of Bubbles
FOCUS = {"soap-bubbles": 0.0}


def compose(book, seed=1, art_path=None, focus=None, label=None):
    env = env_of(book)
    art = Image.open(art_path or ROOT / "site" / "covers" / f"{book}.jpg").convert("RGB")
    ink = shelf_ink(book) or band_colour(art)
    title = re.split(r":", env["ORIGINAL_WORK"])[0]
    sub = env["ORIGINAL_WORK"].split(":", 1)[1].strip() if ":" in env["ORIGINAL_WORK"] else ""
    lines = title_lines(title)
    size = {1: 190, 2: 160, 3: 128}.get(len(lines), 104)
    p = Press(seed, [ink, "black"])
    p.use(ink).field(-20, -20, W + 20, BAND)              # ragged lower edge = the cut
    y = 120 + size * 0.85
    for ln in lines:
        p.use(ink).text(ln, 100, y, size, font=GROT, align="left", clear=True, track=-0.01)
        y += size * 0.92
    y += 18 - size * 0.92 + size * 0.42
    p.use(ink).text(env["AUTHOR"].upper(), 106, y, 46, font=GROT, align="left", clear=True, track=0.05)
    if sub:
        p.use(ink).text(sub, 106, y + 64, 36, align="left", italic=True, clear=True)
        y += 50
    if label:      # the companion print of the source text says so on its face
        p.use(ink).text(label.upper(), 106, y + 70, 34, font=GROT, align="left", clear=True, track=0.12)
    k = p.use("black")
    k.line((-10, BAND + 4), (W + 10, BAND + 4), width=9, jitter=2.5)
    base = p.print(str(ROOT / "build" / "tmp_band.png")).convert("RGB")
    # the painting, cropped to the space below the band, printed under it
    aw, ah = art.size
    region_h = H - BAND
    scale = W / aw
    crop_h = int(region_h / scale)
    f = FOCUS.get(book, 0.5) if focus is None else focus
    top = int(max(0, ah - crop_h) * f)
    pic = art.crop((0, top, aw, top + crop_h)).resize((W, region_h), Image.LANCZOS)
    out = base.copy()
    out.paste(pic, (0, BAND))
    # keep the hand-cut band edge and the rule over the picture
    bnd = np.asarray(base).astype(float); o = np.asarray(out).astype(float)
    ys = slice(BAND - 30, BAND + 30)
    paper = np.array(PAPER) * 255
    is_paper = (np.abs(bnd[ys] - paper).sum(-1) < 40)[..., None]
    o[ys] = np.where(is_paper, o[ys], bnd[ys])
    (ROOT / "build" / "tmp_band.png").unlink()
    return Image.fromarray(o.clip(0, 255).astype("uint8"))


if __name__ == "__main__":
    outdir = ROOT / "build" / "covers" / "framed"
    outdir.mkdir(parents=True, exist_ok=True)
    for b in sys.argv[1:]:
        compose(b).save(outdir / f"{b}.jpg", quality=95)
        print("wrote", outdir / f"{b}.jpg")
