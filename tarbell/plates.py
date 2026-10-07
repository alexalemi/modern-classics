"""Cut Tarbell's drawings from the scan (Archive.org tarbellcourseinm0000unse,
360 ppi) into tarbell/plates/, from the page readers' boxes
(figs/NNNN.txt: "Fig. N | x0 y0 x1 y1 | description").

    python3 tarbell/plates.py

Each box is widened a little, then trimmed back to the drawing's ink
(blobs of a size, so a stray letter of the body text does not drag the
trim). Tarbell's hand-lettered "FIG. N" is part of the drawing and stays.
Files are named by leaf and order: p0060a.jpg, p0060b.jpg ...
"""
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).parent
SRC = HERE / "_src/jp2"
OUT = HERE / "plates"
PAD = 0.01
# Regions (page fractions) whitened in one drawing's cut because another
# drawing shares its columns: on leaf 79 Fig. 2's short wand stands inside
# the column of Fig. 3's labels; on 365 Fig. 10's rope runs over Fig. 11;
# on 186 a line-end of text sits in the drawing's top corner.
MASK = {(79, "Fig. 3"): [(0.12, 0.12, 0.236, 0.43)],
        (79, "Fig. 2"): [(0.237, 0.12, 0.31, 0.45)],
        (186, "Fig. 88"): [(0.365, 0.77, 0.45, 0.832)],
        (365, "Fig. 10"): [(0.826, 0.655, 0.92, 0.80)],
        (365, "Fig. 11"): [(0.80, 0.60, 0.826, 0.80)]}


def trim(g, inner, near, text=()):
    """Trim to the drawing's ink: blobs of a size, plus any small blob (a
    hand-lettered "FIG. 5", an arrow's label) lying wholly inside the
    reader's own box (`inner`, crop pixels) within `near` px of the
    drawing. A blob from the padding, or touching a printed text line
    (`text`, crop pixels), never qualifies."""
    from scipy import ndimage
    a = np.asarray(g)
    paper = np.percentile(a, 90)
    ink = a < paper - 60
    if not ink.any():
        return g
    D = 10
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=D))
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    objs = ndimage.find_objects(lab)
    big = [i for i, v in enumerate(sizes) if v >= 0.06 * sizes.max()]
    bx = [(o[1].start + D, o[0].start + D, o[1].stop - D, o[0].stop - D) for o in objs]
    l, t, r, b = inner
    keep = set(big)
    for i, (x0, y0, x1, y1) in enumerate(bx):
        if i in keep or not (x0 >= l and y0 >= t and x1 <= r and y1 <= b):
            continue
        if any(x0 < R and x1 > L and y0 < B and y1 > T for L, T, R, B in text):
            continue
        for j in big:
            X0, Y0, X1, Y1 = bx[j]
            if max(X0 - x1, x0 - X1, 0) <= near and max(Y0 - y1, y0 - Y1, 0) <= near:
                keep.add(i)
                break
    keep = [i + 1 for i in keep]
    ink = np.isin(lab, keep) & ink
    rows = np.where(ink.sum(1) > 2)[0]
    cols = np.where(ink.sum(0) > 2)[0]
    if not len(rows) or not len(cols):
        return g
    m = 12
    return g.crop((max(0, cols[0] - m), max(0, rows[0] - m),
                   min(g.width, cols[-1] + m), min(g.height, rows[-1] + m)))


DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}
_LINES = {}
_WORDS = {}
_ALL = {}


def text_lines(leaf):
    """hOCR line boxes on a leaf that are PRINTED TEXT: three or more
    lower-case dictionary words. Lettering on a drawing ("THREAD", "SLIT",
    "FIG. 4", "A") never qualifies."""
    if not _LINES:
        import html as H
        t = (HERE / "_src/tarbellcourseinm0000unse_hocr.html").read_text(errors="replace")
        for m in re.finditer(r'<div class="ocr_page" id="page_(\d+)"(.*?)(?=<div class="ocr_page"|\Z)', t, re.S):
            out, every = [], []
            for ln in re.finditer(r'<span class="ocr_line"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)[^"]*"[^>]*>(.*?)</span>\s*(?=<span class="ocr_line"|</p>)', m.group(2), re.S):
                words = [H.unescape(re.sub(r"<[^>]+>", "", w)) for w in re.findall(r'<span class="ocrx_word"[^>]*>(.*?)</span>', ln.group(5), re.S)]
                low = [w for w in (re.sub(r"[^A-Za-z]", "", x) for x in words) if len(w) >= 3 and w.islower() and w in DICT]
                every.append(tuple(int(v) for v in ln.groups()[:4]))
                if len(low) >= 3:
                    out.append(tuple(int(v) for v in ln.groups()[:4]))
            ws = []
            for w in re.finditer(r'<span class="ocrx_word"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)[^"]*"[^>]*>(.*?)</span>', m.group(2), re.S):
                k = re.sub(r"[^A-Za-z]", "", H.unescape(re.sub(r"<[^>]+>", "", w.group(5))))
                if len(k) >= 3 and k.islower() and k in DICT:
                    ws.append(tuple(int(v) for v in w.groups()[:4]))
            _LINES[int(m.group(1))] = out
            _WORDS[int(m.group(1))] = ws
            _ALL[int(m.group(1))] = every
    return _LINES.get(leaf, [])


def text_words(leaf):
    """hOCR boxes of single lower-case dictionary words: the end of a body
    line ("real knot", "and made") too short to count as a text line.
    Tarbell letters his drawings in capitals."""
    text_lines(leaf)
    return _WORDS.get(leaf, [])


def rows():
    out = []
    for f in sorted((HERE / "figs").glob("*.txt")):
        leaf = int(f.stem)
        k = 0
        for line in f.read_text().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3 or parts[0].lower() == "none":
                continue
            box = [float(v) for v in parts[1].split()]
            assert len(box) == 4, (f, line)
            out.append({"leaf": leaf, "label": parts[0], "box": box,
                        "desc": "|".join(parts[2:]).strip(),
                        "file": f"p{leaf:04d}{'abcdefghijklmnop'[k]}.jpg"})
            k += 1
    return out


def main():
    OUT.mkdir(exist_ok=True)
    R = rows()
    for r in R:
        dst = OUT / r["file"]
        im = Image.open(SRC / f"{r['leaf']:04d}.jp2").convert("L")
        W, H = im.size
        x0, y0, x1, y1 = r["box"]
        crop = im.crop((int(max(0, x0 - PAD) * W), int(max(0, y0 - PAD) * H),
                        int(min(1, x1 + PAD) * W), int(min(1, y1 + PAD) * H)))
        for mx0, my0, mx1, my1 in MASK.get((r["leaf"], r["label"]), []):
            ImageDraw.Draw(crop).rectangle((int(mx0 * W) - int(max(0, x0 - PAD) * W), int(my0 * H) - int(max(0, y0 - PAD) * H),
                                            int(mx1 * W) - int(max(0, x0 - PAD) * W), int(my1 * H) - int(max(0, y0 - PAD) * H)),
                                           fill=int(np.percentile(np.asarray(crop), 90)))
        # whiten body-text lines that lie mostly inside the box
        cx0, cy0 = int(max(0, x0 - PAD) * W), int(max(0, y0 - PAD) * H)
        cw, ch = crop.size
        paper = int(np.percentile(np.asarray(crop), 90))
        from PIL import ImageDraw
        d = ImageDraw.Draw(crop)
        for l, t, rr, b in text_lines(r["leaf"]):
            ix = max(0, min(rr - cx0, cw) - max(l - cx0, 0))
            iy = max(0, min(b - cy0, ch) - max(t - cy0, 0))
            if ix * iy >= 0.5 * (rr - l) * (b - t):
                d.rectangle((l - cx0 - 4, t - cy0 - 4, rr - cx0 + 4, b - cy0 + 4), fill=paper)
            else:
                # and any part of a line that falls in the padding: the
                # padding is there for a drawing's own overhang, not text
                L, T, Rt, B = l - cx0 - 4, t - cy0 - 4, rr - cx0 + 4, b - cy0 + 4
                il, it = int(x0 * W) - cx0, int(y0 * H) - cy0
                ir, ib = int(x1 * W) - cx0, int(y1 * H) - cy0
                for bl, bt, br, bb in ((0, 0, cw, it), (0, ib, cw, ch), (0, 0, il, ch), (ir, 0, cw, ch)):
                    if min(Rt, br) > max(L, bl) and min(B, bb) > max(T, bt):
                        d.rectangle((max(L, bl), max(T, bt), min(Rt, br), min(B, bb)), fill=paper)
        # a lower-case body word reaching into the padding is the end of a
        # text line beside the drawing
        il, it = int(x0 * W) - cx0, int(y0 * H) - cy0
        ir, ib = int(x1 * W) - cx0, int(y1 * H) - cy0
        for l, t, rr, b in text_words(r["leaf"]):
            L, T, Rt, B = l - cx0, t - cy0, rr - cx0, b - cy0
            if Rt > 0 and B > 0 and L < cw and T < ch and (L < il + 6 or T < it + 6 or Rt > ir - 6 or B > ib - 6):
                d.rectangle((L - 3, T - 3, Rt + 3, B + 3), fill=paper)
        # and any OCR line lying wholly in the padding (a heading above the
        # drawing): nothing outside the reader's box is the drawing's lettering
        text_lines(r["leaf"])
        for l, t, rr, b in _ALL.get(r["leaf"], []):
            L, T, Rt, B = l - cx0, t - cy0, rr - cx0, b - cy0
            if Rt > 0 and B > 0 and L < cw and T < ch and (Rt <= il or B <= it or L >= ir or T >= ib):
                d.rectangle((L - 3, T - 3, Rt + 3, B + 3), fill=paper)
        inner = (int(x0 * W) - cx0, int(y0 * H) - cy0, int(x1 * W) - cx0, int(y1 * H) - cy0)
        text = [(l - cx0, t - cy0, rr - cx0, b - cy0) for l, t, rr, b in text_lines(r["leaf"]) + text_words(r["leaf"])]
        crop = trim(crop, inner, int(0.03 * W), text)
        crop = ImageOps.autocontrast(crop, cutoff=0.5)
        crop.thumbnail((1200, 1200), Image.LANCZOS)
        crop.save(dst, "JPEG", quality=82, optimize=True)
        r["size"] = list(crop.size)
    (HERE / "figures.json").write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n")
    print(len(R), "drawings cut")


if __name__ == "__main__":
    main()
