"""Cut the figures of The American Woman's Home from the University of
California's 500-ppi scan of the 1869 edition (Archive.org
americanwomansho00beecrich), into beecher/plates/.

    python3 beecher/plates.py

The boxes are the page readers' (figs/batch-*.txt: page | label | x0 y0
x1 y1 | caption, fractions of the page; figure_prompt.txt), read off the
page images. Each box is widened a little, then trimmed back to the ink, so
a reader's tight box never clips a line and a generous one carries no
paper. Pages are the jp2 numbering (one more than the ABBYY leaf).
"""
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).parent
SRC = HERE / "_src/jp2"
OUT = HERE / "plates"
PAD = 0.012


def name(label, page):
    m = re.match(r"Fig\. (\d+)", label)
    if m:
        return f"fig{int(m.group(1)):02d}.jpg"
    return {"frontispiece": "frontispiece.jpg", "title": "title.jpg"}.get(label) or \
        {31: "vignette.jpg", 37: "vignette2.jpg"}[page]


def trim(g):
    """Trim a crop to the drawing's ink: strokes dilated into blobs, and only
    blobs of some size kept, so a stray word or the edge of a text line
    left in the box does not drag the trim out with it."""
    from scipy import ndimage
    a = np.asarray(g)
    paper = np.percentile(a, 90)
    ink = a < paper - 70
    if not ink.any():
        return g
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=12))
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = [i + 1 for i, v in enumerate(sizes) if v >= 0.08 * sizes.max()]
    ink = np.isin(lab, keep) & ink
    rows = np.where(ink.sum(1) > 3)[0]
    cols = np.where(ink.sum(0) > 3)[0]
    if not len(rows) or not len(cols):
        return g
    # a printed label above the drawing or a text line below it is a thin
    # band set off by white space: drop such edge bands while a band at
    # least twice as tall remains
    has = ink.sum(1) > 3
    bands, start, gap = [], None, 0
    for y, v in enumerate(has):
        if v:
            if start is None:
                start = y
            gap, end = 0, y
        elif start is not None:
            gap += 1
            if gap >= 18:
                bands.append((start, end))
                start = None
    if start is not None:
        bands.append((start, end))
    while len(bands) > 1:
        tall = max(b - a for a, b in bands)
        if bands[0][1] - bands[0][0] <= 80 and tall >= 2 * (bands[0][1] - bands[0][0]):
            bands.pop(0)
        elif bands[-1][1] - bands[-1][0] <= 80 and tall >= 2 * (bands[-1][1] - bands[-1][0]):
            bands.pop()
        else:
            break
    y0, y1 = bands[0][0], bands[-1][1]
    cols = np.where(ink[y0:y1 + 1].sum(0) > 3)[0]
    m = 14
    return g.crop((max(0, cols[0] - m), max(0, y0 - m),
                   min(g.width, cols[-1] + m), min(g.height, y1 + m)))


DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}


def text_lines(page):
    """ABBYY's text lines on a page (ABBYY leaf = page - 1), with their
    pixel boxes, and whether each is PRINTED TEXT that has no place in a
    figure: a "Fig. N" label, a caption, or a line of the body. Lettering
    inside a drawing ("KITCHEN", "OVEN", "a", "b") is kept: a line counts
    as text only if it is the label, or carries three dictionary words of
    three letters or more in lower case."""
    import gzip
    import xml.etree.ElementTree as ET
    tag = lambda e: e.tag.split("}")[-1]
    if not hasattr(text_lines, "cache"):
        text_lines.cache = {}
        with gzip.open(HERE / "_src/americanwomansho00beecrich_abbyy.gz") as f:
            leaf = -1
            for ev, el in ET.iterparse(f, events=("end",)):
                if tag(el) != "page":
                    continue
                leaf += 1
                out = []
                for b in el.iter():
                    if tag(b) != "block" or b.get("blockType") != "Text":
                        continue
                    for ln in b.iter():
                        if tag(ln) == "line":
                            s = "".join(c.text or "" for c in ln.iter() if tag(c) == "charParams")
                            out.append(((int(ln.get("l")), int(ln.get("t")), int(ln.get("r")), int(ln.get("b"))), s))
                text_lines.cache[leaf + 1] = out
                el.clear()
    res = []
    for box, s in text_lines.cache.get(page, []):
        words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", s)]
        prose = sum(1 for w in words if w in DICT and w == w.lower()) >= 3 and re.search(r"[a-z]{3}", s)
        label = re.match(r"^\s*F[il1][gq]\.?\s*\d+", s)
        res.append((box, s, bool(prose or label)))
    return res


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for f in sorted((HERE / "figs").glob("batch-*.txt")):
        for line in f.read_text().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3 or parts[1] == "none":
                continue
            page, label, box = int(parts[0]), parts[1], [float(v) for v in parts[2].split()]
            caption = parts[3] if len(parts) > 3 else ""
            # an optional fifth field: this figure's own padding, for a cut
            # whose printed label sits a few pixels from the drawing
            pad = float(parts[4]) if len(parts) > 4 and parts[4] else PAD
            rows.append({"page": page, "label": label, "box": box, "caption": caption,
                         "pad": pad, "file": name(label, page)})
    files = [r["file"] for r in rows]
    assert len(files) == len(set(files)), "a figure marked twice"
    for r in rows:
        im = Image.open(SRC / f"{r['page']:04d}.jp2").convert("L")
        W, H = im.size
        x0, y0, x1, y1 = r["box"]
        P = r["pad"]
        crop = im.crop((int(max(0, x0 - P) * W), int(max(0, y0 - P) * H),
                        int(min(1, x1 + P) * W), int(min(1, y1 + P) * H)))
        if r["label"] not in ("frontispiece", "title"):
            # whiten printed text inside the box: the label, a caption, a
            # body line the box caught (paper tone, so the trim ignores it)
            cx0, cy0 = int(max(0, x0 - P) * W), int(max(0, y0 - P) * H)
            paper = int(np.percentile(np.asarray(crop), 90))
            from PIL import ImageDraw
            d = ImageDraw.Draw(crop)
            cw, ch = crop.size
            for (l, t, rr, b), s, is_text in text_lines(r["page"]):
                if not is_text:
                    continue
                # only a line that lies mostly inside the box: ABBYY's line
                # boxes can run through a drawing beside them (Fig. 35's
                # FIRE BOX lost its FIRE to "front sides of the fire-box")
                ix = max(0, min(rr - cx0, cw) - max(l - cx0, 0))
                iy = max(0, min(b - cy0, ch) - max(t - cy0, 0))
                if ix * iy < 0.6 * (rr - l) * (b - t):
                    continue
                d.rectangle((l - cx0 - 6, t - cy0 - 6, rr - cx0 + 6, b - cy0 + 6), fill=paper)
            crop = trim(crop)
        crop = ImageOps.autocontrast(crop, cutoff=0.5)
        crop.thumbnail((1600, 1600), Image.LANCZOS)
        crop.save(OUT / r["file"], "JPEG", quality=85, optimize=True)
        r["size"] = list(crop.size)
    (HERE / "figures.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    print(len(rows), "figures cut")


if __name__ == "__main__":
    main()
