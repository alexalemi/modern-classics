"""Cut the diagrams out of the page scans and separate the ink from the paper.

    python3 euclid-rivals/replate.py

thompson/replate.py established the method and every lesson in it applies
here:

  - ABBYY'S PICTURE BOX FITS THE ENGRAVING, NOT THE DRAWING, so plates
    arrive clipped -- a label, an arrowhead or a whole construction line
    outside the box. Do not re-cut with a fixed margin, which is either
    too small somewhere or takes in body text elsewhere. GROW EACH SIDE
    UNTIL IT REACHES WHITESPACE: scan outward, stop at the first run of
    blank rows or columns, back off by a pad. Self-limiting on a plate
    that was never clipped.
  - SCANNED PAPER IS DIRT ON A WHITE PAGE. Map DARKNESS TO ALPHA over
    pure black: the ink survives with the anti-aliasing the scan gave it,
    and the paper goes. A bilevel threshold would destroy the fine
    hatching in these geometrical figures.
  - READ "PAPER" AT THE 99TH PERCENTILE, NOT THE MODE. On a plate that is
    mostly ink the mode IS the ink, and reading paper there leaves the
    page showing through as a grey ghost.
  - QUANTISE THE ALPHA. The scan's noise gives every stroke a fringe of
    unique values that PNG cannot compress; rounding halves the file and
    is invisible.

Pages come one at a time out of the Archive.org JP2 zip rather than by
downloading all 106 MB: the whole book is 324 leaves and only 22 of them
carry a diagram.
"""

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from abbyy import pages                                   # noqa: E402

BOOK = Path(__file__).parent
XML = BOOK / "source" / "euclidhismodernr00carr_abbyy.gz"
CACHE = BOOK / "source" / "pagecache"
OUT = BOOK.parent / "site/images/euclid-rivals"
ID = "euclidhismodernr00carr"

PAD = 12                # blank margin kept around the found edge
BLANK_RUN = 14          # consecutive blank lines that mean "outside"
INK = 176               # a pixel darker than this counts as ink
GROW_LIMIT = 260        # never grow a side further than this

# NOT EVERY PICTURE BLOCK IS A PLATE. Three of the twenty-two are the
# library's, not the book's: the Wellesley College bookplate pasted inside
# the front cover (p3), the decorative device on the flyleaf (p7) and the
# date-due slip at the back (p318). ABBYY cannot tell them from a figure
# and neither can any rule about size or position -- they had to be
# looked at. Listed rather than inferred, and prep asserts the count.
NOT_A_PLATE = {3, 7, 318}


def fetch_page(n):
    """Scan page n (1-based, as abbyy.py numbers them)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{n:04d}.jp2"
    if not dest.exists():
        url = (f"https://archive.org/download/{ID}/{ID}_jp2.zip/"
               f"{ID}_jp2%2F{ID}_{n - 1:04d}.jp2")
        req = urllib.request.Request(
            url, headers={"User-Agent": "modern-classics/1.0"})
        data = urllib.request.urlopen(req, timeout=180).read()
        if len(data) < 20_000:
            sys.exit(f"page {n} came back as {len(data)} bytes")
        dest.write_bytes(data)
    return Image.open(io.BytesIO(dest.read_bytes())).convert("L")


def _row_has_ink(px, w, y, x0, x1, ink):
    return any(px[x, y] < ink for x in range(x0, x1, 2))


def _col_has_ink(px, h, x, y0, y1, ink):
    return any(px[x, y] < ink for y in range(y0, y1, 2))


def grow(img, box, ink=INK):
    """Push each edge outward until it has been clear for BLANK_RUN lines."""
    l, t, r, b = box
    W, H = img.size
    px = img.load()

    run = 0
    while t > 0 and (t > box[1] - GROW_LIMIT) and run < BLANK_RUN:
        t -= 1
        run = 0 if _row_has_ink(px, W, t, max(0, l), min(W, r), ink) else run + 1
    run = 0
    while b < H - 1 and (b < box[3] + GROW_LIMIT) and run < BLANK_RUN:
        b += 1
        run = 0 if _row_has_ink(px, W, b, max(0, l), min(W, r), ink) else run + 1
    run = 0
    while l > 0 and (l > box[0] - GROW_LIMIT) and run < BLANK_RUN:
        l -= 1
        run = 0 if _col_has_ink(px, H, l, max(0, t), min(H, b), ink) else run + 1
    run = 0
    while r < W - 1 and (r < box[2] + GROW_LIMIT) and run < BLANK_RUN:
        r += 1
        run = 0 if _col_has_ink(px, H, r, max(0, t), min(H, b), ink) else run + 1

    return (max(0, l - PAD), max(0, t - PAD),
            min(W, r + PAD), min(H, b + PAD))


def ink_to_alpha(crop, levels=16, white_frac=0.80):
    """Black ink on nothing.

    TWO POINTS, NOT ONE. Reading the paper at the 99th percentile finds
    the paper's brightest pixels -- but most of the sheet is DARKER than
    that, so mapping everything below it to some alpha leaves the whole
    page faintly visible, which is what the first version did. The white
    point has to sit below the paper's own noise (0.80 of it here), and
    the black point at the ink's 2nd percentile. Then paper clips to
    nothing and the strokes keep the anti-aliasing the scan gave them.

    Still read at a PERCENTILE and not at the mode: on a plate that is
    mostly ink the mode is the ink.
    """
    hist = crop.histogram()
    total = sum(hist)
    acc, paper = 0, 255
    for value, count in enumerate(hist):
        acc += count
        if acc >= total * 0.99:
            paper = max(value, 1)
            break
    acc, ink = 0, 0
    for value, count in enumerate(hist):
        acc += count
        if acc >= total * 0.02:
            ink = value
            break
    white = max(2, int(paper * white_frac))
    black = max(0, min(ink, white - 2))
    span = max(1, white - black)
    out = Image.new("LA", crop.size)
    src, dst = crop.load(), out.load()
    step = 255 // levels
    for y in range(crop.size[1]):
        for x in range(crop.size[0]):
            v = src[x, y]
            a = 0 if v >= white else int(255 * min(1.0, (white - v) / span))
            dst[x, y] = (0, min(255, round(a / 255 * levels) * step))
    return out


def plates():
    found = []
    for pg in pages(XML):
        for b in pg.blocks:
            if (b.kind == "Picture" and pg.number not in NOT_A_PLATE
                    and (b.right - b.left) < pg.width * 0.95):
                found.append((pg.number, (b.left, b.top, b.right, b.bottom)))
    if len(found) != 19:
        sys.exit(f"expected 19 plates, found {len(found)} -- the scan or "
                 f"NOT_A_PLATE has changed")
    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()                       # own the set (the copy_figures rule)
    for i, (page, box) in enumerate(plates(), 1):
        img = fetch_page(page)
        grown = grow(img, box)
        plate = ink_to_alpha(img.crop(grown))
        name = OUT / f"fig{i}.png"
        plate.save(name, optimize=True)
        print(f"  fig{i:<3} p{page:<4} {box} -> {grown}  "
              f"{plate.size[0]}x{plate.size[1]}  {name.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
