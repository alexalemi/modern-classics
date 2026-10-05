"""Cut the illustrations out of the scans -> site/images/carson/fig{id}.jpg.

    python3 carson/plates.py [BOOK-NN ...]     # all pages, or just these

Each page reader marks an illustration with a GENEROUS box in fractions of
the page ("[PLATE x0 y0 x1 y1 | kind | caption]"). Carson's drawings are set
INTO the text -- a refuge sign standing in the margin of a column, geese
flying across a paragraph -- so a rectangle around one takes in body text
too. The cutter therefore:
  1. renders the page at 300 dpi;
  2. blanks every body-text word inside the box, using the word boxes of
     the PDF's own text layer (pdftotext -bbox) -- except on maps, whose
     place names are part of the map;
  3. tightens the box to the remaining ink (pixels darker than the paper),
     with a margin.
A plate whose tightened box is still mostly text, or empty, stops the run.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = ROOT / "site/images/carson"
SRC = {"chincoteague": "nps_1-chincoteague", "parker": "nps_2-parker-river",
       "mattamuskeet": "arlis_36455789", "guarding": "arlis_1472474", "bear": "nps_8-bear-river"}
DPI = 300
PLATE = re.compile(r"^\[PLATE\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\|\s*(\w+)\s*\|\s*(.*?)\]\s*$")


def page_image(book, nn):
    cache = HERE / f"_src/hires/{book}-{nn:02d}.png"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        pdf = HERE / f"_src/{SRC[book]}.pdf"
        subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-f", str(nn), "-l", str(nn),
                        "-singlefile", str(pdf), str(cache)[:-4]], check=True)
    return Image.open(cache).convert("RGB")


def word_boxes(book, nn):
    pdf = HERE / f"_src/{SRC[book]}.pdf"
    x = subprocess.run(["pdftotext", "-bbox", "-f", str(nn), "-l", str(nn), str(pdf), "-"],
                       capture_output=True, text=True).stdout
    s = DPI / 72
    return [(float(a) * s, float(b) * s, float(c) * s, float(d) * s, w)
            for a, b, c, d, w in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', x)]


def plates_of(book, nn):
    p = HERE / f"proof/{book}-{nn:02d}.txt"
    out = []
    for line in p.read_text().splitlines():
        m = PLATE.match(line.strip())
        if m:
            out.append((tuple(float(v) for v in m.groups()[:4]), m.group(5), m.group(6)))
    return out


def dense_run(profile, thr, gap=25):
    """The longest run of indices whose value exceeds thr, bridging gaps
    shorter than `gap` (a pale sky inside a photograph)."""
    on = [v > thr for v in profile]
    best, cur, last = (0, 0), None, None
    for i, v in enumerate(on + [False] * (gap + 1)):
        if v:
            if cur is None:
                cur = i
            last = i
        elif cur is not None and i - last > gap:
            if last + 1 - cur > best[1] - best[0]:
                best = (cur, last + 1)
            cur = None
    return best


def cut_photo(book, nn, box):
    """A photograph is dense ink edge to edge; its caption and the page's
    text are sparse. Take the reader's box (a little widened), then the
    longest run of dense rows, then the dense columns within them."""
    im = page_image(book, nn)
    W, H = im.size
    x0, y0 = max(0, int((box[0] - 0.01) * W)), max(0, int((box[1] - 0.01) * H))
    x1, y1 = min(W, int((box[2] + 0.01) * W)), min(H, int((box[3] + 0.01) * H))
    crop = im.crop((x0, y0, x1, y1))
    g = crop.convert("L")
    w, h = g.size
    px = g.load()
    thr = paper_level(g) - 22
    rows = [sum(px[x, y] < thr for x in range(0, w, 4)) / (w / 4) for y in range(h)]
    r0, r1 = dense_run(rows, 0.10, gap=30)
    cols = [sum(px[x, y] < thr for y in range(r0, r1, 4)) / max(1, (r1 - r0) / 4) for x in range(w)]
    c0, c1 = dense_run(cols, 0.10, gap=30)
    if r1 - r0 < 80 or c1 - c0 < 80:
        raise SystemExit(f"{book}-{nn:02d} {box}: no photograph found")
    return crop.crop((c0, r0, c1, r1))


# OCR of pen strokes inside a drawing comes out as junk ("I)·,;", "\,..~"),
# and masking it painted over the drawing itself: printed text has two
# letters in a row or is a number. A word only partly inside the widened
# box is masked too (a text column's edge). INSIDE_KEPT: plates whose own
# lettering is part of the picture (the refuge sign on Mattamuskeet's title
# page): nothing inside the reader's box is masked.
INSIDE_KEPT = {"ma02a"}
# page fractions to clear: Chincoteague p. 7 sets a paragraph inside the map
BLANK = {"ch07a": [(0.03, 0.64, 0.42, 0.89)], "ch02a": [(0.335, 0.60, 1.0, 0.79)], "ma12a": [(0.298, 0.32, 1.0, 0.86), (0.276, 0.357, 0.30, 0.86)]}


def is_text(w):
    return bool(re.search(r"[A-Za-z]{2}|^\W*\d+\W*$", w))


def cut(book, nn, box, kind, pid=""):
    if kind == "photo":
        return cut_photo(book, nn, box)
    im = page_image(book, nn)
    W, H = im.size
    # widen the reader's box (readers clip wing tips); masking and the ink
    # trim below take back what does not belong
    mx, my = (int(0.03 * W), int(0.02 * H)) if kind != "map" else (int(0.005 * W), int(0.005 * H))
    x0, y0 = max(0, int(box[0] * W) - mx), max(0, int(box[1] * H) - my)
    x1, y1 = min(W, int(box[2] * W) + mx), min(H, int(box[3] * H) + my)
    im = im.copy()
    if kind != "map":
        src = im.copy()
        d = ImageDraw.Draw(im)
        for a, b, c, e, w in word_boxes(book, nn):
            inside = a >= box[0] * W and c <= box[2] * W and b >= box[1] * H and e <= box[3] * H
            if is_text(w) and not (pid in INSIDE_KEPT and inside) and c > x0 and a < x1 and e > y0 and b < y1:
                d.rectangle((a - 3, b - 3, c + 3, e + 3), fill=local_paper(src, a - 3, b - 3, c + 3, e + 3))
    if pid in BLANK:                # body text set inside a map's frame
        src = im.copy()
        d = ImageDraw.Draw(im)
        for fx0, fy0, fx1, fy1 in BLANK[pid]:
            r = (int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H))
            d.rectangle(r, fill=local_paper(src, *r))
    crop = im.crop((x0, y0, x1, y1))
    g = crop.convert("L")
    px = g.load()
    w, h = g.size
    thr = paper_level(g) - 60
    # trim to the drawing, not to every speck: strokes dilated into blobs,
    # and only blobs of some size kept (a stray letter the masking missed
    # was dragging the trim out across a text column)
    import numpy as np
    from scipy import ndimage
    ink = np.asarray(g) < thr
    if not ink.any():
        raise SystemExit(f"{book}-{nn:02d} {box}: no ink in the box")
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=10))
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = [i + 1 for i, a in enumerate(sizes) if a >= 0.04 * sizes.max()]
    ys, xs = np.nonzero(np.isin(lab, keep) & ink)
    m = 18
    return crop.crop((max(0, xs.min() - m), max(0, ys.min() - m), min(w, xs.max() + m), min(h, ys.max() + m)))


def local_paper(im, a, b, c, e):
    """The paper just around a word: the brightest-third median of a ring of
    pixels outside its box, so a blanked word matches its own patch of a
    yellowed page."""
    W, H = im.size
    px = im.load()
    ring = []
    for x in range(int(max(0, a - 6)), int(min(W, c + 6)), 3):
        for y in (int(max(0, b - 6)), int(min(H - 1, e + 6))):
            ring.append(px[x, y])
    if not ring:
        return paper(im)
    ring.sort(key=sum)
    top = ring[len(ring) * 2 // 3:]
    return tuple(sorted(p[i] for p in top)[len(top) // 2] for i in range(3))


_paper = {}


def paper(im):
    k = id(im)
    if k not in _paper:
        g = im.convert("L").resize((60, 80))
        vals = sorted(g.getdata())
        level = vals[int(len(vals) * 0.9)]
        rgb = im.resize((60, 80)).getdata()
        _paper[k] = max(rgb, key=lambda p: -abs(sum(p) / 3 - level))
    return _paper[k]


def paper_level(g):
    vals = sorted(g.resize((50, 50)).getdata())
    return vals[int(len(vals) * 0.9)]


def main(only=()):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    pages = sorted(HERE.glob("proof/*.txt"))
    for p in pages:
        book, nn = p.stem.rsplit("-", 1)
        nn = int(nn)
        if only and p.stem not in only:
            continue
        if book == "mattamuskeet" and nn >= 13:
            continue        # Bear River bound in after Mattamuskeet: a second witness only
        for k, (box, kind, caption) in enumerate(plates_of(book, nn)):
            if kind == "ornament":
                continue    # seals, spine bands, rules: printers' furniture
            pid = f"{book[:2]}{nn:02d}{'abcdefghij'[k]}"
            img = cut(book, nn, box, kind, pid)
            if max(img.size) > 1600:
                img.thumbnail((1600, 1600))
            img.save(OUT / f"fig{pid}.jpg", "JPEG", quality=88)
            rows.append({"id": pid, "book": book, "page": nn, "box": box, "kind": kind,
                         "caption": caption, "size": list(img.size)})
    if not only:
        (HERE / "plates.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    print(len(rows), "plates")
    return rows


if __name__ == "__main__":
    main(set(sys.argv[1:]))
