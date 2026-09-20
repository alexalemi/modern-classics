"""S. W. Erdnase, Artifice, Ruse and Subterfuge at the Card Table (1902):
page drafts and plate cuts for the proofreading pass.

    python3 erdnase/pages.py

The source is Archive.org's bwb_S0-DTR-948, a scan of the 2002 centennial
FACSIMILE of the 1902 first edition (its title page reproduces the 1902
imprint and adds one line, "Facsimile copyright, 2002"; a photographic
facsimile adds nothing of its own to the text or the drawings). No
transcription of the book exists on Gutenberg or Wikisource, and every
other Archive.org copy is lending-restricted, so there is no second scan to
vote with. Archive.org's hOCR is itself Tesseract output, so a second
Tesseract run would not be a second witness either. The second witness is
the PROOFREADING PASS: every page read against its image, which shares
nothing with the OCR.

Writes, per leaf that carries text or a plate:
  _src/draft/NNN.txt   the OCR text in reading order, running head, folio,
                       figure labels and the drawings' copyright lines
                       removed, each drawing marked [PLATE NNN-k]
  _src/plates/NNN-k.png  the drawing, cut from the page by its region
  _src/plates.json     [{leaf, k, page, bbox, label}] in reading order
"""
import json
import re
import zipfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "_src"
ID = "bwb_S0-DTR-948"
HEADS = re.compile(r"^(?:\d+\s+)?(?:CARD\s+TABLE\s+ARTIFICE|LEGERDEMAIN|CONTENTS)\.?(?:\s+\d+)?$", re.I)
FIGLABEL = re.compile(r"^(?:Fig|FIG|Fie|Pig)[.,]?\s*[\dIl!|]+\s*[.,!}\])]?$")   # "Fig. 79 }"
# the leaves that carry a drawing: every leaf ABBYY found a picture on,
# less the covers, endpapers and blank leaves that it also called pictures
NOT_PLATES = {0, 1, 3, 4, 5, 6, 10, 212, 213, 214, 215, 216, 217}
PLATE_LEAVES = None                     # filled in main() from the hOCR
# cuts that are not drawings: the word "up." on leaf 46, set apart as a
# paragraph's last line
DROP = {(46, 0)}
# boxes the text-gap rule gets wrong, set by hand from the page image
CROP = {(51, 0): (294, 964, 1236, 1419),      # Fig. 14: the OCR never read the paragraph under it
        (144, 0): (200, 810, 1388, 1617),     # Fig. 74: its cuff tip all but touches the copyright line
        (47, 0): (306, 1114, 1216, 1531),     # Fig. 12: copyright line 5px under the label
        (54, 0): (480, 1072, 1387, 1640)}     # Fig. 17: its copyright line reads as a few merged blobs
COPYLINE = re.compile(r"^Copyright,?\s+by\s+S\.?\s*W\.?\s+Erdnase,?\s+1902\.?$", re.I)


def boxes(page_html, cls):
    return [tuple(map(int, m.groups())) for m in re.finditer(
        r'class="%s"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)' % cls, page_html)]


def lines(page_html):
    """[(y0, y1, x0, text)] for every ocr_line."""
    out = []
    for m in re.finditer(r'<span class="ocr_line"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)[^"]*">(.*?)</span>\s*(?=<span class="ocr_line"|</p>)',
                         page_html, re.S):
        x0, y0, x1, y1 = map(int, m.groups()[:4])
        words = re.findall(r'<span class="ocrx_word"[^>]*>(.*?)</span>', m.group(5), re.S)
        t = " ".join(w.strip() for w in words).replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
        t = re.sub(r"&#(\d+);", lambda n: chr(int(n.group(1))), t)
        if t.strip():
            out.append((y0, y1, x0, t.strip()))
    return out


def paragraphs(page_html):
    """Lines grouped by ocr_par, as [(y0, [lines])]."""
    out = []
    for m in re.finditer(r'<p class="ocr_par"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)"[^>]*>(.*?)</p>', page_html, re.S):
        ls = lines(m.group(5) + "</p>")
        if ls:
            out.append((int(m.group(2)), [l[3] for l in ls]))
    return out


def all_lines(page_html):
    """[(x0, y0, x1, y1, text)] for every ocr_line on the page."""
    out = []
    for m in re.finditer(r'<span class="ocr_line"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)[^"]*">(.*?)</span>\s*(?=<span class="ocr_line"|</p>)',
                         page_html, re.S):
        words = re.findall(r'<span class="ocrx_word"[^>]*>(.*?)</span>', m.group(5), re.S)
        tx = " ".join(w.strip() for w in words).strip()
        if tx:
            out.append(tuple(map(int, m.groups()[:4])) + (tx,))
    return out


def is_furniture(tx):
    return bool(FIGLABEL.match(tx) or COPYLINE.match(tx) or re.search(r"(?i)copyright|erdnase,? 1902", tx)
                or re.fullmatch(r"(?i)fig[.,]?\s*\d+[.,]?", tx))


def cut_plates(img, page_lines):
    """THE DRAWINGS ARE WHAT THE TEXT LEAVES. ABBYY/Tesseract picture
    regions here are unreliable (blank leaves read as pictures, Fig. 8 in
    three pieces, crops that took in a line of text), so a plate is the ink
    in a vertical gap between BODY lines, with its own label and copyright
    lines blanked first, split into side-by-side drawings on a wide empty
    column. Returns [(box, [label lines inside it])] top to bottom."""
    g = img.convert("L")
    W, H = g.size
    px = g.load()
    # a "line" the OCR read INSIDE a drawing (shading, cuff lines) is debris
    # and must not split the drawing in two (Fig. 60 was, by an "s"): a
    # body line has at least one real word in it
    def real(tx):
        return bool(re.search(r"[A-Za-z]{3,}", tx))
    # ...and is the height of a line of type (about 50px here; "eet" read
    # off the shading of Fig. 33 was 96px tall and clipped its top)
    body = sorted((l for l in page_lines if not is_furniture(l[4]) and real(l[4]) and l[3] - l[1] <= 72),
                  key=lambda l: l[1])
    furn = [l for l in page_lines if is_furniture(l[4])]
    # only a COPYRIGHT line is blanked out of a drawing; its label "Fig. N"
    # is engraved with it and stays whole (blanking it clipped Figs. 60, 86)
    copy = [l for l in furn if re.search(r"(?i)copyright|erdnase", l[4])]
    heads = [l for l in body if HEADS.match(l[4]) or re.fullmatch(r"\d{1,3}", l[4])]
    text = [l for l in body if l not in heads]
    top = max([l[3] for l in heads if l[1] < H * 0.12] or [int(H * 0.05)])
    bounds = [top] + [y for l in text for y in (l[1], l[3])] + [int(H * 0.95)]
    gaps = [(bounds[i], bounds[i + 1]) for i in range(0, len(bounds) - 1, 2)]
    ink = 150
    out = []
    for a, b in gaps:
        if b - a < 70:
            continue
        a, b = a + 4, b - 4

        def blank(x, y):
            return any(l[0] - 12 <= x <= l[2] + 12 and l[1] - 12 <= y <= l[3] + 12 for l in copy)
        rows = [y for y in range(a, b, 2) if any(px[x, y] < ink and not blank(x, y) for x in range(40, W - 40, 3))]
        if len(rows) < 12:
            continue
        y0, y1 = rows[0], rows[-1]
        cols = [x for x in range(40, W - 40, 2) if any(px[x, y] < ink and not blank(x, y) for y in range(y0, y1, 3))]
        runs, s = [], cols[0]
        for u, v in zip(cols, cols[1:]):
            if v - u > 80:
                runs.append((s, u)); s = v
        runs.append((s, cols[-1]))
        # a narrow run is a stray cuff or finger of the drawing beside it
        # (Fig. 83 lost its right cuff this way): join it to its neighbour
        merged_runs = []
        for r in runs:
            if merged_runs and (r[1] - r[0] < 60 or merged_runs[-1][1] - merged_runs[-1][0] < 60 or r[0] - merged_runs[-1][1] < 140):
                merged_runs[-1] = (merged_runs[-1][0], r[1])
            else:
                merged_runs.append(r)
        runs = merged_runs
        for x0, x1 in runs:
            if x1 - x0 < 60:
                continue
            ys = [y for y in range(y0, y1 + 1, 2) if any(px[x, y] < ink and not blank(x, y) for x in range(x0, x1, 3))]
            # THE COPYRIGHT LINE under 26 of the drawings is set in the plate
            # area and the OCR never read it as a line: drop the lowest band
            # of ink when it is short, wide and cut off by a clear gap (a
            # label "Fig. 12" is narrow, and usually inside the drawing)
            runs_y, s0 = [], ys[0]
            for u, v in zip(ys, ys[1:]):
                if v - u > 6:
                    runs_y.append((s0, u)); s0 = v
            runs_y.append((s0, ys[-1]))
            # dust: a band a few pixels high is not ink that belongs to anything
            specks = [r for r in runs_y if r[1] - r[0] <= 4]
            if specks and len(runs_y) > len(specks):
                runs_y = [r for r in runs_y if r not in specks]
                ys = [y for y in ys if any(r[0] <= y <= r[1] for r in runs_y)]
            if len(runs_y) > 1:
                ly0, ly1 = runs_y[-1]
                lx = [x for x in range(x0, x1, 2) if any(px[x, y] < ink for y in range(ly0, ly1 + 1, 2))]
                if ly1 - ly0 <= 36 and lx and lx[-1] - lx[0] >= 280:
                    ys = [y for y in ys if y < ly0]
            # faint pencil-weight tails (cuff strokes) fall under the ink
            # threshold: grow each side while it still touches lighter ink
            yb0, yb1, xb0, xb1 = ys[0], ys[-1], x0, x1
            faint = 185
            # vertically only, and only a little: sideways it walks into paper
            # dust, and downward into an unread copyright line (Fig. 74)
            for _ in range(8):
                grew = False
                if yb1 + 2 < b and any(px[x, yb1 + 2] < faint and not blank(x, yb1 + 2) for x in range(xb0, xb1, 2)):
                    yb1 += 2; grew = True
                if yb0 - 2 > a and any(px[x, yb0 - 2] < faint and not blank(x, yb0 - 2) for x in range(xb0, xb1, 2)):
                    yb0 -= 2; grew = True
                if not grew:
                    break
            # DUST: a speck beside a drawing joins it through the run merge;
            # trim each side back to where a 10px strip holds real ink
            def dense(x_from, x_to):
                return sum(1 for x in range(x_from, x_to) for y in range(yb0, yb1, 2)
                           if px[x, y] < ink and not blank(x, y)) >= 12
            while xb1 - xb0 > 80 and not dense(xb0, xb0 + 10):
                xb0 += 10
            while xb1 - xb0 > 80 and not dense(xb1 - 10, xb1):
                xb1 -= 10
            box = (max(xb0 - 8, 0), max(yb0 - 8, 0), min(xb1 + 8, W), min(yb1 + 8, H))
            labs = [l[4] for l in furn if FIGLABEL.match(l[4]) and box[1] - 20 <= l[1] <= box[3] + 90
                    and box[0] - 60 <= (l[0] + l[2]) / 2 <= box[2] + 60]
            out.append((box, labs))
    # a LABEL CUT OFF ON ITS OWN ("Fig. 31", "Fig. 63" set well below their
    # drawings) goes back into the drawing directly above it
    merged = []
    for box, labs in out:
        small = box[2] - box[0] < 260 and box[3] - box[1] < 90
        if small and merged and 0 <= box[1] - merged[-1][0][3] <= 120:
            (a0, b0, a1, b1), l0 = merged[-1]
            merged[-1] = ((min(a0, box[0]), b0, max(a1, box[2]), box[3]), l0 + labs)
        else:
            merged.append((box, labs))
    return merged


def despeck(img, box, pad=8):
    """Shrink a box to the ink blobs that belong to the drawing. Paper dust
    beside a plate is a blob of a few pixels; the drawing and its label are
    blobs of hundreds. Keep every blob of at least 40 pixels (a label's
    period is ~60, a dust speck under 30) and take their bounding box."""
    import numpy as np
    from scipy import ndimage
    a = np.asarray(img.convert("L").crop(box)) < 170
    lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=2))
    if n == 0:
        return box
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    floor = max(40, 0.004 * max(sizes))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= floor]
    # THE COPYRIGHT LINE, where the OCR never read it: a row of ten or more
    # small blobs, at least 350px wide, along the bottom edge. A label
    # ("Fig. 12") is five blobs and 90px.
    objs = ndimage.find_objects(lab)
    bottom = max(objs[i - 1][0].stop for i in keep)
    row = [i for i in keep if objs[i - 1][0].start >= bottom - 40 and sizes[i - 1] < 1500]
    if len(row) >= 10:
        span = max(objs[i - 1][1].stop for i in row) - min(objs[i - 1][1].start for i in row)
        if span >= 350:
            keep = [i for i in keep if i not in row]
    ys, xs = np.nonzero(np.isin(lab, keep) & a)
    x0, y0 = box[0] + int(xs.min()), box[1] + int(ys.min())
    x1, y1 = box[0] + int(xs.max()), box[1] + int(ys.max())
    # never past the box it was given: a hand crop's edge is deliberate
    return (max(x0 - pad, box[0]), max(y0 - pad, box[1]), min(x1 + pad, box[2]), min(y1 + pad, box[3]))


def to_alpha(im):
    """Darkness to alpha over black, paper read at the 99th percentile (the
    thompson/replate rule), quantised to 16 levels for line art."""
    g = im.convert("L")
    hist = g.histogram()
    n, acc, paper = sum(hist), 0, 255
    for v in range(255, -1, -1):
        acc += hist[v]
        if acc >= n * 0.01:
            paper = v
            break
    a = g.point(lambda v: 0 if v >= paper else min(255, int((paper - v) * 255 / max(paper - 40, 1))))
    a = a.point(lambda v: (v // 16) * 17)
    out = Image.new("LA", g.size, 0)
    out.putalpha(a)
    return out


def main():
    h = (SRC / f"{ID}_hocr.html").read_text()
    pages = re.split(r'(?=<div class="ocr_page")', h)[1:]
    nums = {p["leafNum"]: p["pageNumber"] for p in json.loads((SRC / f"{ID}_page_numbers.json").read_text())["pages"]}
    z = zipfile.ZipFile(SRC / f"{ID}_jp2.zip")
    global PLATE_LEAVES
    PLATE_LEAVES = {i for i, ph in enumerate(pages) if boxes(ph, "ocr_photo")} - NOT_PLATES
    (SRC / "draft").mkdir(exist_ok=True)
    (SRC / "plates").mkdir(exist_ok=True)
    plates = []
    for f in (SRC / "plates").glob("*.png"):
        f.unlink()
    for leaf, ph in enumerate(pages):
        pars = paragraphs(ph)
        items = []
        for y, ls in pars:
            ls = [l for l in ls if not HEADS.match(l) and not re.fullmatch(r"\d{1,3}", l)
                  and not is_furniture(l)]
            if ls:
                items.append((y, "\n".join(ls)))
        pl = all_lines(ph)
        if leaf in PLATE_LEAVES:
            img = Image.open(z.open(f"{ID}_jp2/{ID}_{leaf:04d}.jp2"))
            cuts = [c for i, c in enumerate(cut_plates(img, pl)) if (leaf, i) not in DROP]
            for k, (box, labs) in enumerate(cuts):
                box = despeck(img, CROP.get((leaf, k), box))
                to_alpha(img.crop(box)).save(SRC / "plates" / f"{leaf:03d}-{k}.png", optimize=True)
                plates.append({"leaf": leaf, "k": k, "page": nums.get(leaf, ""), "bbox": list(box), "label": " ".join(labs)})
                items.append((box[1], f"[PLATE {leaf:03d}-{k}]"))
        if not items:
            continue
        items.sort()
        (SRC / "draft" / f"{leaf:03d}.txt").write_text(
            f"# leaf {leaf}, printed page {nums.get(leaf) or '-'}\n\n" + "\n\n".join(t for _, t in items) + "\n")
    (SRC / "plates.json").write_text(json.dumps(plates, indent=1) + "\n")
    print(len(plates), "plates;", sum(1 for p in plates if p["label"]), "with a label read")


if __name__ == "__main__":
    main()
