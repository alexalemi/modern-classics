"""The three figures of Gödel's Proof, DRAWN AFRESH for this edition.

    python3 godel/figures.py      -> site/images/godel/fig{aa,ab,ac}.png

The book's acknowledgments say several of its diagrams were reproduced from
the June 1956 Scientific American, whose copyright was renewed in 1984, so
none of the printed art is copied. Each figure is constructed from the
mathematics it shows: the triangle model of Fig. 1, great circles on a
sphere for Fig. 2, and the Pappus configuration and its dual for Fig. 3,
with every point computed. Drawn at 3x and reduced, for clean lines.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT = HERE.parent / "site/images/godel"
S = 3                                   # supersampling
INK = (25, 25, 25)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"


def canvas(w, h):
    im = Image.new("RGB", (w * S, h * S), "white")
    return im, ImageDraw.Draw(im)


def font(size, italic=False):
    return ImageFont.truetype(FONT_I if italic else FONT, size * S)


def line(d, p, q, w=2):
    d.line([(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)], fill=INK, width=w * S)


def dot(d, p, r=3.5):
    d.ellipse([(p[0] - r) * S, (p[1] - r) * S, (p[0] + r) * S, (p[1] + r) * S], fill=INK)


def label(d, p, text, size=17, italic=False, dx=0, dy=0):
    f = font(size, italic)
    box = d.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((p[0] + dx) * S - w / 2, (p[1] + dy) * S - h / 2 - box[1]), text, fill=INK, font=f)


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = im.size
    im.resize((w // S, h // S), Image.LANCZOS).save(OUT / name, optimize=True)


# ---------------------------------------------------------------- Fig. 1
def fig1():
    im, d = canvas(520, 380)
    A, B, C = (90, 320), (300, 50), (430, 320)
    for p, q in ((A, B), (B, C), (C, A)):
        line(d, p, q, 3)
    for p, (dx, dy) in ((A, (-22, 4)), (B, (0, -24)), (C, (22, 4))):
        dot(d, p)
        label(d, p, "K", dx=dx, dy=dy)
    for p, q, (dx, dy) in ((A, B, (-22, -12)), (B, C, (24, -8)), (A, C, (0, 24))):
        label(d, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), "L", dx=dx, dy=dy)
    save(im, "figaa.png")


# ---------------------------------------------------------------- Fig. 2
def rot_y(v, a):
    x, y, z = v
    return (x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a))


def rot_x(v, a):
    x, y, z = v
    return (x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def slerp(p, q, t):
    om = math.acos(max(-1, min(1, sum(a * b for a, b in zip(p, q)))))
    if om < 1e-9:
        return p
    s1, s2 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
    return tuple(s1 * a + s2 * b for a, b in zip(p, q))


def arc(d, c, R, p, q, w=3, dash=False, n=80):
    pts = [slerp(p, q, k / n) for k in range(n + 1)]
    xy = [((c[0] + R * v[0]) * S, (c[1] - R * v[1]) * S) for v in pts]
    if dash:
        for k in range(0, n, 4):
            d.line(xy[k:k + 3], fill=INK, width=w * S // 2 or 1)
    else:
        d.line(xy, fill=INK, width=w * S, joint="curve")


def sphere(d, c, R):
    # an outline and a light rim of shading towards the right, for roundness
    for k in range(40):
        f = k / 40
        g = int(255 - 40 * f ** 3)
        r = R * (1 - 0.0 * f)
        off = 0.25 * R * (1 - f)
        d.ellipse([(c[0] - r + off * 0) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], outline=None)
    d.ellipse([(c[0] - R) * S, (c[1] - R) * S, (c[0] + R) * S, (c[1] + R) * S], outline=INK, width=2 * S)


def gc_point(lon, lat):
    """A point on the unit sphere facing the viewer (z toward us)."""
    return (math.cos(lat) * math.sin(lon), math.sin(lat), math.cos(lat) * math.cos(lon))


def fig2():
    W, H = 560, 760
    im, d = canvas(W, H)
    R = 105
    rows = (130, 380, 630)
    xl, xs = 140, 400
    # row 1: a segment, and an arc of a great circle (a meridian)
    y = rows[0]
    line(d, (xl, y - 70), (xl, y + 70), 3)
    sphere(d, (xs, y), R)
    arc(d, (xs, y), R, gc_point(-0.35, -0.7), gc_point(-0.35, 0.7))
    # row 2: a square, and a region bounded by four great-circle arcs
    y = rows[1]
    d.rectangle([(xl - 60) * S, (y - 60) * S, (xl + 60) * S, (y + 60) * S], outline=INK, width=3 * S)
    sphere(d, (xs, y), R)
    a = 0.55
    n_left, n_right = norm(rot_y((1, 0, 0), a)), norm(rot_y((1, 0, 0), -a))
    n_top, n_bot = norm(rot_x((0, 1, 0), -a)), norm(rot_x((0, 1, 0), a))

    def corner(n1, n2):
        v = norm(cross(n1, n2))
        return v if v[2] > 0 else tuple(-c for c in v)
    tl, tr = corner(n_left, n_top), corner(n_right, n_top)
    bl, br = corner(n_left, n_bot), corner(n_right, n_bot)
    for p, q in ((tl, tr), (tr, br), (br, bl), (bl, tl)):
        arc(d, (xs, y), R, p, q)
    # row 3: two parallel segments, and two great-circle arcs that, extended
    # (dotted), meet at the poles
    y = rows[2]
    line(d, (xl - 20, y - 70), (xl - 20, y + 70), 3)
    line(d, (xl + 20, y - 70), (xl + 20, y + 70), 3)
    sphere(d, (xs, y), R)
    for lon in (-0.45, 0.45):
        arc(d, (xs, y), R, gc_point(lon, -0.6), gc_point(lon, 0.6))
        arc(d, (xs, y), R, gc_point(lon, 0.6), (0, 1, 0), dash=True)
        arc(d, (xs, y), R, gc_point(lon, -0.6), (0, -1, 0), dash=True)
    label(d, (xl, 30), "the plane", size=15, italic=True)
    label(d, (xs, 15), "the sphere", size=15, italic=True)
    save(im, "figab.png")


# ---------------------------------------------------------------- Fig. 3
def meet(p1, p2, q1, q2):
    """Intersection of line p1p2 with line q1q2."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, q1, q2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    a, b = x1 * y2 - y1 * x2, x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / den, (a * (y3 - y4) - (y1 - y2) * b) / den)


def extend(p, q, k0=-0.15, k1=1.15):
    return ((p[0] + k0 * (q[0] - p[0]), p[1] + k0 * (q[1] - p[1])),
            (p[0] + k1 * (q[0] - p[0]), p[1] + k1 * (q[1] - p[1])))


def fig3():
    W, H = 640, 860
    im, d = canvas(W, H)
    # (a) Pappus: A, B, C on line I; A', B', C' on line II
    def on(p, q, t):                       # a point of line pq, exactly
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
    A, C = (120, 330), (430, 354)
    B = on(A, C, 0.42)
    A2, C2 = (210, 195), (520, 105)
    B2 = on(A2, C2, 0.39)
    R = meet(A, B2, A2, B)
    Sx = meet(A, C2, A2, C)
    T = meet(B, C2, B2, C)
    for p, q in (extend(A, C, -0.2, 1.35), extend(A2, C2, -0.6, 1.12)):
        line(d, p, q, 2)
    for p, q in ((A, B2), (A2, B), (A, C2), (A2, C), (B, C2), (B2, C)):
        line(d, p, q, 2)
    p, q = extend(R, T, -0.6, 2.6)
    line(d, p, q, 2)
    for pt, name, off in ((A, "A", (-4, 20)), (B, "B", (0, 20)), (C, "C", (4, 20)),
                          (A2, "A′", (-10, -18)), (B2, "B′", (-6, -18)), (C2, "C′", (-14, -14)),
                          (R, "R", (-12, -16)), (Sx, "S", (2, 20)), (T, "T", (12, -16))):
        dot(d, pt)
        label(d, pt, name, size=15, dx=off[0], dy=off[1])
    label(d, (600, 380), "I", size=15)
    label(d, (585, 85), "II", size=15)
    label(d, (q[0] + 16, q[1]), "III", size=15)
    label(d, (40, 60), "(a)", size=16)
    # (b) the dual: lines A, B, C through point I; A', B', C' through point II
    # placed (by a search over layouts) so that the point III, where the
    # three lines R, S, T meet, falls inside the drawing
    I, II = (572, 704), (377, 497)
    ends_I = {"A": (43, 684), "B": (120, 561), "C": (44, 772)}
    ends_II = {"A′": (247, 805), "B′": (153, 831), "C′": (432, 818)}
    for k, e in ends_I.items():
        line(d, I, e, 2)
    for k, e in ends_II.items():
        line(d, II, e, 2)
    pts = {}
    for a in "ABC":
        for b in ("A′", "B′", "C′"):
            pts[a + b] = meet(I, ends_I[a], II, ends_II[b])
    # lines R, S, T through the pairs (AB', A'B), (AC', A'C), (BC', B'C)
    rst = {"R": ("AB′", "BA′"), "S": ("AC′", "CA′"), "T": ("BC′", "CB′")}
    III = meet(pts["AB′"], pts["BA′"], pts["AC′"], pts["CA′"])
    for name, (p1, p2) in rst.items():
        far = pts[p1] if math.dist(pts[p1], III) > math.dist(pts[p2], III) else pts[p2]
        a, b = extend(III, far, 0, 1.25)
        line(d, a, b, 2)
        label(d, b, name, size=15, dx=(-12 if b[0] < III[0] else 12), dy=4)
    for v in pts.values():
        dot(d, v, 3)
    dot(d, I)
    dot(d, II)
    dot(d, III)
    label(d, I, "I", size=15, dx=16, dy=0)
    label(d, II, "II", size=15, dx=0, dy=-18)
    label(d, III, "III", size=15, dx=-22, dy=12)
    for k, e in ends_I.items():
        label(d, e, k, size=15, dx=-14, dy=0)
    for k, e in ends_II.items():
        label(d, e, k, size=15, dx=0, dy=14)
    label(d, (40, 470), "(b)", size=16)
    save(im, "figac.png")
    # the drawing is only right if the theorem holds in it
    assert abs((T[1] - R[1]) * (Sx[0] - R[0]) - (Sx[1] - R[1]) * (T[0] - R[0])) < 1e-3 * abs((T[0] - R[0]) * (Sx[0] - R[0]) + 1)
    t_line = meet(pts["BC′"], pts["CB′"], III, (III[0] + 1, III[1]))   # noqa: F841


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("drew", sorted(p.name for p in OUT.glob("fig*.png")))
