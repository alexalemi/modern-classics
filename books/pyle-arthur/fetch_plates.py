"""Replace Gutenberg's 550px plates with crops from a full-resolution scan.

    python3 books/pyle-arthur/fetch_plates.py      # after prep.py

Gutenberg #60184 ships Pyle's drawings as thumbnails (550px on the long
side). Archive.org `storyofkingarthu00pylerich` (UC Libraries; a 1909
Scribner reprint from the 1903 plates, so the drawings are identical) has
every page at 2800px. For each plate in plates.json this script downloads
the page it is printed on, finds the drawing on the page, crops it, and
writes site/images/pyle-arthur/fig<id>.jpg (grayscale, 1600px on the long
side, paper levelled to white).

FINDING THE DRAWING. The Gutenberg thumbnail is a crop of the same printed
page, so it is used as a template: normalised cross-correlation (by FFT)
over every position and every scale, coarse at 1/8 size and then refined at
1/2 size. The box it lands on is the crop, so the scan crop takes in exactly
what Gutenberg's did (the lettered title of a plate, the "Chapter First."
lettering of a headpiece). A plate whose best score is under MIN_SCORE keeps
the Gutenberg image and is reported. That witness is the guard: a wrong
leaf cannot correlate with the thumbnail. (A first version cut the page
into ink bands and picked the best band run; it clipped plates that ran to
the scan's edge and headpieces whose top row was faint.)

LEAVES. Body pages map through the scan's own page_numbers.json (page n is
leaf n+26 in this copy). Front matter and the last tailpiece were identified
by eye from a contact sheet and are pinned in FRONT_LEAVES. The drawn title
page (aa) is NOT replaced: the scan's title page reads "1909", and the
Gutenberg file is already a full-size scan of the 1903 page.
"""
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
IMAGES = ROOT / "site" / "images" / "pyle-arthur"
GUT = HERE / "_src" / "h" / "images"
CACHE = HERE / "_src" / "scan"
IA = "storyofkingarthu00pylerich"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
MIN_SCORE = 0.5
LONG_SIDE = 1600

FRONT_LEAVES = {"ill_pg_iv_sml.jpg": 10, "ill_pg_vii_sml.jpg": 13,
                "ill_pg_viii.jpg": 14, "ill_pg_xiii_sml.jpg": 25,
                "ill_pg_xiv_sml.jpg": 26, "ill_pg_001_sml.jpg": 27,
                "ill_pg_312.jpg": 338}
SKIP = {"title.jpg"}


def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:  # archive.org 500s now and then
            err = e
            time.sleep(3 * (attempt + 1))
    raise err


def leaf_map():
    pn = CACHE / "page_numbers.json"
    if not pn.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        pn.write_bytes(fetch(f"https://archive.org/download/{IA}/{IA}_page_numbers.json"))
    pages = json.loads(pn.read_text())["pages"]
    return {p["pageNumber"]: p["leafNum"] for p in pages if p["pageNumber"]}


def page_image(leaf):
    f = CACHE / f"n{leaf}.jpg"
    if not f.exists():
        f.write_bytes(fetch(f"https://archive.org/download/{IA}/page/n{leaf - 1}.jpg"))
    return Image.open(f).convert("L")


def ncc_map(img, tpl):
    """Normalised cross-correlation of tpl at every valid offset in img."""
    th, tw = tpl.shape
    H, W = img.shape
    t = tpl - tpl.mean()
    tn = np.sqrt((t * t).sum())
    if tn == 0 or th > H or tw > W:
        return None
    fh, fw = H + th, W + tw
    F = np.fft.rfft2(img, (fh, fw)) * np.conj(np.fft.rfft2(t, (fh, fw)))
    num = np.fft.irfft2(F, (fh, fw))[:H - th + 1, :W - tw + 1]
    c1 = np.pad(img.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    c2 = np.pad((img * img).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    def win(c):
        return c[th:, tw:] - c[:-th, tw:] - c[th:, :-tw] + c[:-th, :-tw]
    n = th * tw
    s1, s2 = win(c1), win(c2)
    var = np.maximum(s2 - s1 * s1 / n, 1e-9)
    return num / (np.sqrt(var) * tn)


def search(img, thumb, widths):
    best = (-1.0, None)
    for tw in widths:
        th = max(4, round(tw * thumb.height / thumb.width))
        tpl = np.asarray(thumb.resize((tw, th), Image.BOX), dtype=float)
        m = ncc_map(img, tpl)
        if m is None:
            continue
        i = np.unravel_index(np.argmax(m), m.shape)
        if m[i] > best[0]:
            best = (float(m[i]), (i[1], i[0], tw, th))
    return best


def locate(page, thumb):
    """(box, score): where the thumbnail's drawing sits on the page. A
    coarse search over scale and position at 1/8 size, then a fine one at
    1/2 size around the coarse answer."""
    thumb = thumb.convert("L")
    k = 8
    small = np.asarray(page.resize((page.width // k, page.height // k), Image.BOX), dtype=float)
    score, (x, y, tw, th) = search(small, thumb, range(20, small.shape[1] + 1, 2))
    k2 = 2
    x0, y0 = max(0, (x - 3) * k // k2), max(0, (y - 3) * k // k2)
    x1 = min(page.width // k2, (x + tw + 3) * k // k2)
    y1 = min(page.height // k2, (y + th + 3) * k // k2)
    region = page.resize((page.width // k2, page.height // k2), Image.BOX).crop((x0, y0, x1, y1))
    reg = np.asarray(region, dtype=float)
    base = tw * k // k2
    score2, (fx, fy, ftw, fth) = search(reg, thumb, range(base - 8, base + 9))
    if score2 >= score:
        return ((x0 + fx) * k2, (y0 + fy) * k2, (x0 + fx + ftw) * k2, (y0 + fy + fth) * k2), score2
    return (x * k, y * k, (x + tw) * k, (y + th) * k), score


def finish(page, box):
    pad = 12
    x0, y0, x1, y1 = box
    crop = page.crop((max(0, x0 - pad), max(0, y0 - pad),
                      min(page.width, x1 + pad), min(page.height, y1 + pad)))
    # level the paper to white and the ink to black
    lo, hi = np.percentile(np.asarray(crop), [1, 90])
    lut = [0 if v <= lo else 255 if v >= hi else int(255 * (v - lo) / (hi - lo))
           for v in range(256)]
    crop = crop.point(lut)
    crop.thumbnail((LONG_SIDE, LONG_SIDE), Image.LANCZOS)
    return crop


def main():
    plates = json.loads((HERE / "plates.json").read_text())
    pages = leaf_map()
    report = []
    for p in plates:
        src = p["src"]
        if src in SKIP:
            continue
        if src in FRONT_LEAVES:
            leaf = FRONT_LEAVES[src]
        else:
            num = src.split("_")[2].split(".")[0].lstrip("0")
            leaf = pages.get(num)
        if leaf is None:
            report.append((p["id"], src, None, "no leaf"))
            continue
        page = page_image(leaf)
        thumb = Image.open(GUT / src)
        box, score = locate(page, thumb)
        stem = "front" if p["id"] == "front" else f"fig{p['id']}"
        if box is None or score < MIN_SCORE:
            report.append((p["id"], src, leaf, f"KEPT GUTENBERG (score {score:.2f})"))
            continue
        finish(page, box).save(IMAGES / f"{stem}.jpg", quality=88)
        report.append((p["id"], src, leaf, f"{score:.2f}"))
        print(p["id"], src, leaf, f"{score:.2f}", flush=True)
    for r in report:
        if not r[3][0].isdigit():
            print("!!", *r)


if __name__ == "__main__":
    main()
