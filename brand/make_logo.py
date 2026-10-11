#!/usr/bin/env python3
"""Emend Press logos as clean SVGs: every letter is an outline (no font
dependency), the caret is built geometrically.

  python3 make_logo.py SERIF_KEY  -> writes mark.svg, wordmark.svg (+ variants)
"""
import sys, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FONTS = pathlib.Path(__file__).resolve().parent / "fonts"   # see fetch_fonts.sh
OUT = pathlib.Path(__file__).resolve().parent

NAVY = "#24303F"
RED = "#A3291C"

SERIFS = {
    "cormorant": ("CormorantGaramond[wght].ttf", 600),
    "caslon": ("LibreCaslonText[wght].ttf", 500),
    "garamond": ("/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Regular.ttf", None),
}
SANS = ("Montserrat[wght].ttf", 500)


def load(path, wght):
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = FONTS / p
    f = TTFont(str(p))
    if wght is not None and "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": wght})
    return f


class Face:
    def __init__(self, font):
        self.f = font
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.upm = font["head"].unitsPerEm
        self.cap = getattr(font["OS/2"], "sCapHeight", 0) or self.bounds("H")[3]

    def gname(self, ch):
        return self.cmap[ord(ch)]

    def adv(self, ch):
        return self.gs[self.gname(ch)].width

    def bounds(self, ch):
        bp = BoundsPen(self.gs)
        self.gs[self.gname(ch)].draw(bp)
        return bp.bounds

    def path(self, ch, x, y, s):
        """SVG path for glyph ch, origin (baseline-left) at (x, y), scale s,
        y flipped for SVG."""
        pen = SVGPathPen(self.gs, ntos=lambda v: (f"{v:.2f}".rstrip("0").rstrip(".") or "0"))
        tp = TransformPen(pen, (s, 0, 0, -s, x, y))
        self.gs[self.gname(ch)].draw(tp)
        return pen.getCommands()


def run(face, text, x, y, size, track=0.0):
    """Lay out text; returns (list of path strings, end x, ink bounds)."""
    s = size / face.upm
    paths, ink = [], [1e9, 1e9, -1e9, -1e9]
    run.boxes = []                      # per-letter ink (left, right), for alignment
    for i, ch in enumerate(text):
        paths.append(face.path(ch, x, y, s))
        b = face.bounds(ch)
        run.boxes.append((x + b[0] * s, x + b[2] * s) if b else (x, x))
        if b:
            ink[0] = min(ink[0], x + b[0] * s); ink[2] = max(ink[2], x + b[2] * s)
            ink[1] = min(ink[1], y - b[3] * s); ink[3] = max(ink[3], y - b[1] * s)
        x += face.adv(ch) * s
        if i < len(text) - 1:
            x += track * size
    return paths, x, ink


def caret(cx, top, width, height, stroke):
    """A chevron '^' with horizontally cut feet: outer apex at (cx, top),
    feet on the line y = top + height, leg thickness `stroke` measured
    horizontally at the feet."""
    b = top + height
    l, r = cx - width / 2, cx + width / 2
    # inner apex: lower the apex so legs keep constant horizontal thickness
    slope = height / (width / 2)               # dy per dx along the outer leg
    inner_top = top + stroke * slope
    pts = [(cx, top), (r, b), (r - stroke, b), (cx, inner_top),
           (l + stroke, b), (l, b)]
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def svg(w, h, body, title):
    # whole-number canvas: `se lint` x-022 rejects fractions in viewBox
    import math
    w, h = math.ceil(w), math.ceil(h)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">\n'
            f'<title>{title}</title>\n{body}\n</svg>\n')


def build(key, navy=NAVY, red=RED, suffix=""):
    sf, sw = SERIFS[key]
    serif = Face(load(sf, sw))
    sans = Face(load(*SANS))

    # ---- MARK: E with caret beneath -------------------------------------
    size = 200.0
    s = size / serif.upm
    eb = serif.bounds("E")
    ew = (eb[2] - eb[0]) * s
    capH = (eb[3] - eb[1]) * s
    pad = 24
    x0 = pad - eb[0] * s
    base = pad + eb[3] * s
    e_path = serif.path("E", x0, base, s)
    e_cx = pad + ew / 2
    c_w, c_h, c_st = ew * 0.86, capH * 0.50, capH * 0.13
    c_top = base + capH * 0.22
    car = caret(e_cx, c_top, c_w, c_h, c_st)
    W = ew + 2 * pad
    H = c_top + c_h + pad
    body = (f'<path fill="{navy}" d="{e_path}"/>\n'
            f'<path fill="{red}" d="{car}"/>')
    (OUT / f"emend-mark{suffix}.svg").write_text(svg(W, H, body, "Emend Press"))

    # ---- WORDMARK: EMEND (serif) / PRESS (sans), caret under the E ------
    size = 200.0
    track = 0.07
    pad = 30
    # measure first
    paths, endx, ink = run(serif, "EMEND", 0, 0, size, track)
    dx = pad - ink[0]
    dy = pad - ink[1]
    paths, endx, ink = run(serif, "EMEND", dx, dy, size, track)
    end_l, end_r = run.boxes[2][0], run.boxes[4][1]      # ink span of "END"
    capH = ink[3] - ink[1]
    baseline = ink[3]
    # caret under the first E, as in the mockup
    s = size / serif.upm
    e = serif.bounds("E")
    e_left, e_right = dx + e[0] * s, dx + e[2] * s
    e_cx = (e_left + e_right) / 2
    c_w, c_h, c_st = (e_right - e_left) * 0.86, capH * 0.50, capH * 0.13
    c_top = baseline + capH * 0.22
    car = caret(e_cx, c_top, c_w, c_h, c_st)
    # PRESS: tracked sans, centred under "END", cap height ~ 0.36 of EMEND
    psize = size * 0.40
    ptrack = 0.16
    pp, pend, pink = run(sans, "PRESS", 0, 0, psize, ptrack)
    pw = pink[2] - pink[0]
    p_x = (end_l + end_r) / 2 - pw / 2 - pink[0]
    p_capH = pink[3] - pink[1]
    p_base = c_top + c_h - 0 # bottom of PRESS aligned with caret feet
    pp, pend, pink2 = run(sans, "PRESS", p_x, p_base, psize, ptrack)
    W = ink[2] + pad
    H = max(c_top + c_h, pink2[3]) + pad
    body = (f'<g fill="{navy}">\n' + "\n".join(f'<path d="{p}"/>' for p in paths + pp)
            + f'\n</g>\n<path fill="{red}" d="{car}"/>')
    (OUT / f"emend-wordmark{suffix}.svg").write_text(svg(W, H, body, "Emend Press"))


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "cormorant"
    if len(sys.argv) > 2:
        build(key, suffix=f"-{key}")
    else:
        build(key)                                   # navy + red on transparent
        build(key, navy="#FFFFFF", red="#E0553F", suffix="-reversed")  # for dark grounds
        build(key, navy="#000000", red="#000000", suffix="-black")     # one-colour
