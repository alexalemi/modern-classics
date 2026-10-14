"""Proposals for the Law and Economics books (2026-10-13). None of the six
has a figure, so each draws the book's own central example or scheme; the
quotes and the few labels are verbatim from modern_chapters. Text stays
OUT of the drawings (Alex): a handful of labels at most.

    python3 gencover/law_econ_demo.py      # writes the review sheet
"""
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from press import Press, W, H  # noqa: E402
from designs import title_block, GROT  # noqa: E402


def _arrow(pen, a, b, width=6, head=26):
    a, b = np.array(a, float), np.array(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    n = np.array([-d[1], d[0]])
    pen.stroke([tuple(a), tuple(b - d * head * 0.8)], width=width, taper=False)
    pen.fill([tuple(b), tuple(b - d * head * 1.6 + n * head * 0.7), tuple(b - d * head * 1.6 - n * head * 0.7)])


def _clip(poly, ycut, above):
    """Sutherland-Hodgman against the line y = ycut (above = smaller y)"""
    inside = (lambda q: q[1] <= ycut) if above else (lambda q: q[1] >= ycut)
    out = []
    pts = [tuple(q) for q in poly]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        if inside(b):
            if not inside(a):
                t = (ycut - a[1]) / (b[1] - a[1]); out.append((a[0] + t * (b[0] - a[0]), ycut))
            out.append(b)
        elif inside(a):
            t = (ycut - a[1]) / (b[1] - a[1]); out.append((a[0] + t * (b[0] - a[0]), ycut))
    return out


def common_law(seed):
    """Holmes's account of how law grows: the custom, belief, or necessity
    disappears, but the rule remains; the old form receives a new content,
    and in time even the form changes to fit it. The same tablet, four
    times, its content changing and at last its outline."""
    p = Press(seed, ["brown", "red", "mustard", "black"])
    p.use("brown").field(-20, -20, W + 20, H + 20)
    title_block(p, "brown", ["THE COMMON", "LAW"], "OLIVER WENDELL HOLMES JR.",
                ["“The old form receives a new content, and in time even the form", "changes to fit the meaning it has received.”"], size=190)
    k = p.use("black")

    def tablet(cx, cy, w, h, round_=0.0):
        # an arched tablet; round_ swells the shoulders and the foot
        t = np.linspace(math.pi, 2 * math.pi, 40)
        arch = np.column_stack([cx + w / 2 * np.cos(t), cy - h / 2 + w / 2 + (w / 2) * np.sin(t)])
        foot_t = np.linspace(0, math.pi, 30)
        foot = np.column_stack([cx + w / 2 * np.cos(foot_t), cy + h / 2 - round_ * w / 2 + round_ * (w / 2) * np.sin(foot_t)])
        bulge = 1 + 0.12 * round_
        side_r = [(cx + w / 2 * bulge, cy), (cx + w / 2, cy + h / 2 - round_ * w / 2)]
        side_l = [(cx - w / 2, cy + h / 2 - round_ * w / 2), (cx - w / 2 * bulge, cy)]
        return np.vstack([arch, side_r, foot, side_l])

    contents = [("red", 1.0), ("red", 0.6), ("mustard", 0.65), ("mustard", 1.0)]
    xs = [250, 550, 850, 1150]
    w, h = 230, 520
    cy = 1420
    for i, (x, (ink, frac)) in enumerate(zip(xs, contents)):
        shape = tablet(x, cy, w, h, round_=[0, 0, 0.35, 0.8][i])
        p.use("brown").fill(shape, clear=True)
        top = cy - h / 2
        cut = {0: None, 1: cy + h / 2 - h * 0.4, 2: top + h * 0.12, 3: None}[i]
        if cut is None:
            p.use(ink).fill(shape)
        else:           # the old content above the line, the new below it
            p.use("red").fill(_clip(shape, cut, above=True))
            p.use("mustard").fill(_clip(shape, cut, above=False))
        k.polyline(shape, width=8)
        for j in range(4):      # the lines of the rule, the same on every tablet
            yy = top + w / 2 + 40 + j * 60
            k.line((x - w * 0.3, yy), (x + w * 0.3, yy), width=4)
        if i < 3:
            _arrow(k, (x + w / 2 + 18, cy), (xs[i + 1] - w / 2 - 18, cy), width=5, head=18)
    return p


def cardozo(seed):
    """The four lines along which the directive force of a principle may be
    exerted, converging on the decision."""
    p = Press(seed, ["cobalt", "orange", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["THE NATURE OF", "THE JUDICIAL", "PROCESS"], "BENJAMIN N. CARDOZO",
                ["“The directive force of a principle may be exerted along the line of", "logical progression…”"],
                size=140, y0=250)
    c = np.array([W / 2, 1480])
    ends = [((240, 1090), "PHILOSOPHY", "logical progression"),
            ((W - 240, 1090), "EVOLUTION", "historical development"),
            ((240, 1870), "TRADITION", "the customs of the community"),
            ((W - 240, 1870), "SOCIOLOGY", "justice, morals and social welfare")]
    k = p.use("black")
    for (e, name, sub) in ends:
        e = np.array(e, float)
        p.use("cobalt").stroke([tuple(e), tuple(c)], width=34, taper=False, jitter=1, clear=True)
        p.use("orange").stroke([tuple(e), tuple(c)], width=34, taper=False, jitter=1)
        k.stroke([tuple(e), tuple(c)], width=4, jitter=1.4)
        _arrow(k, e + (c - e) * 0.55, e + (c - e) * 0.78, width=5, head=22)
        up = e[1] < c[1]
        ty = e[1] - 110 if up else e[1] + 130
        al = "left" if e[0] < c[0] else "right"
        tx = 110 if al == "left" else W - 110
        p.use("cobalt").text(name, tx, ty, 56, font=GROT, align=al, clear=True, track=0.06)
    p.use("cobalt").disc(tuple(c), 96, clear=True)
    p.use("orange").disc(tuple(c), 96, clear=True)
    k.circle(tuple(c), 96, width=8)
    k.disc(tuple(c), 22)
    return p


def sabotage(seed):
    """The manual's advice for meetings: everything through channels, and
    every matter referred to a committee of never less than five."""
    p = Press(seed, ["orange", "black", "sky"])
    p.use("orange").field(-20, -20, W + 20, H + 20)
    title_block(p, "orange", ["SIMPLE", "SABOTAGE", "FIELD MANUAL"], "OFFICE OF STRATEGIC SERVICES",
                ["(1) Insist on doing everything through “channels.”"], size=150, y0=250)
    k = p.use("black")
    # the channels: a box handed on, box to box, down the page and round again
    boxes = [(260, 1060), (700, 1060), (1140, 1060), (1140, 1360), (700, 1360), (260, 1360)]
    bw, bh = 250, 130
    for i, (x, y) in enumerate(boxes):
        r = [(x - bw / 2, y - bh / 2), (x + bw / 2, y - bh / 2), (x + bw / 2, y + bh / 2), (x - bw / 2, y + bh / 2)]
        p.use("orange").fill(r, clear=True)
        k.polyline(r, width=6)
        if i + 1 < len(boxes):
            x2, y2 = boxes[i + 1]
            if y2 == y:
                s = 1 if x2 > x else -1
                _arrow(k, (x + s * bw / 2 + 8, y), (x2 - s * bw / 2 - 8, y2), width=6)
            else:
                _arrow(k, (x, y + bh / 2 + 8), (x2, y2 - bh / 2 - 8), width=6)
        for j in range(3):                     # the paper, form lines
            k.line((x - bw / 2 + 30, y - 30 + j * 30), (x + bw / 2 - 30 - 40 * (j == 2), y - 30 + j * 30), width=3)
    # the committee: never less than five, round a table, and back to the start
    c = np.array([W / 2, 1790])
    tab = p.ring(tuple(c), 150, n=60, wob=0.01)
    p.use("orange").fill(tab, clear=True)
    p.use("sky").fill(tab)
    k.polyline(tab, width=7)
    for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 7)[:-1]:
        q = c + 235 * np.array([math.cos(a), math.sin(a)])
        p.use("orange").disc(tuple(q), 52, clear=True)
        k.circle(tuple(q), 52, width=6)
    _arrow(k, (260, 1360 + bh / 2 + 8), (c[0] - 300, c[1] - 120), width=6)
    loop = np.array([(c[0] + 330, c[1] - 60), (W - 90, c[1] - 200), (W - 90, 1060), (1140 + bw / 2 + 12, 1060)])
    k.stroke(loop[:-1], width=6, taper=False)
    _arrow(k, tuple(loop[-2]), tuple(loop[-1]), width=6)
    return p


def wealth_of_nations(seed):
    """The labourer's woollen coat: the eight trades Smith names (in the
    epigraph), eight weft threads woven into the one humble garment."""
    p = Press(seed, ["red", "sky", "mustard", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["THE WEALTH", "OF NATIONS"], "ADAM SMITH",
                ["“The shepherd, the wool sorter, the wool comber, the dyer, the spinner, the weaver,",
                 "the cloth finisher, the dresser, and many others all have to contribute their",
                 "different skills just to produce this one humble garment.”"], size=170)
    N, x0, x1, y0 = 8, 480, 1300, 1000
    pitch = (x1 - x0) / N
    bw = pitch * 0.74
    xs = [x0 + (i + 0.5) * pitch for i in range(N)]
    ys = [y0 + 60 + (j + 0.5) * pitch for j in range(N)]
    top, bot = y0 - 40, H + 40               # the warp runs off the foot
    INKS = ("red", "sky", "mustard", "black")

    def piece(rect, ink, vertical):
        (a, b), (c, d) = rect                 # x0, y0, x1, y1
        poly = [(a, b), (c, b), (c, d), (a, d)]
        for pl in INKS:
            p.use(pl).fill(poly, clear=True, rough=0.4)
        p.use(ink).fill(poly, rough=0.4)
        k = p.use("black")
        if vertical:
            k.line((a, b), (a, d), width=4, taper=False); k.line((c, b), (c, d), width=4, taper=False)
        else:
            k.line((a, b), (c, b), width=4, taper=False); k.line((a, d), (c, d), width=4, taper=False)
        for t in np.arange(0.18, 1, 0.22):   # the twist of the yarn
            if vertical:
                yy = np.arange(b + 10, d - 10, 26)
                for y in yy:
                    k.line((a + bw * t - 6, y), (a + bw * t + 6, y + 14), width=1.6, taper=False)
            else:
                xx = np.arange(a + 10, c - 10, 26)
                for x in xx:
                    k.line((x, b + bw * t - 6), (x + 14, b + bw * t + 6), width=1.6, taper=False)

    for x in xs:                              # the warp, plain
        piece(((x - bw / 2, top), (x + bw / 2, bot)), "sky", True)
    for j, y in enumerate(ys):                # the weft, one trade to each thread
        piece(((-60, y - bw / 2), (x1 + 40, y + bw / 2)), "mustard", False)
    for j, y in enumerate(ys):                # the warp comes back over at every other crossing
        for i, x in enumerate(xs):
            if (i + j) % 2:
                piece(((x - bw / 2, y - bw / 2 - 4), (x + bw / 2, y + bw / 2 + 4)), "sky", True)
    return p


def progress_and_poverty(seed):
    """The law of rent: each piece of land yields what it can; what it yields
    above the least productive land in use goes to rent."""
    p = Press(seed, ["teal", "red", "mustard", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["PROGRESS", "AND POVERTY"], "HENRY GEORGE",
                ["“The rent of land is determined by how much more it produces than the same", "amount of labor and capital could produce on the least productive land still in use.”"], size=170)
    k = p.use("black")
    base, margin = 1960, 1640
    hs = [880, 990, 1110, 1230, 1340, 1440, 1540, 1640]
    bw = 116
    for i, top in enumerate(hs):
        x = 152 + i * 140
        r = [(x, top), (x + bw, top), (x + bw, base), (x, base)]
        p.use("teal").fill(r, clear=True)
        p.use("mustard").fill([(x, margin), (x + bw, margin), (x + bw, base), (x, base)])
        if top < margin:
            p.use("red").fill([(x, top), (x + bw, top), (x + bw, margin), (x, margin)])
        k.polyline(r, width=5)
    k.stroke([(110, margin), (W - 110, margin)], width=7, taper=False)
    k.line((110, base), (W - 110, base), width=9)
    for (ink, lab, lx) in (("red", "RENT", 152), ("mustard", "WAGES AND INTEREST", 500)):
        sw = [(lx, base + 40), (lx + 50, base + 40), (lx + 50, base + 90), (lx, base + 90)]
        p.use("teal").fill(sw, clear=True); p.use(ink).fill(sw); k.polyline(sw, width=4)
        p.use("teal").text(lab, lx + 70, base + 84, 44, font=GROT, align="left", clear=True, track=0.05)
    return p


def turgot(seed):
    """The three classes, and the money that passes round them: the
    cultivators', the landowners', the artisans'."""
    p = Press(seed, ["olive", "mustard", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["REFLECTIONS ON", "THE FORMATION AND", "DISTRIBUTION", "OF WEALTH"], "ANNE-ROBERT-JACQUES TURGOT",
                ["“People are quite right to compare it to the circulation of the blood", "in the animal body.”"], size=118, y0=240)
    c = np.array([W / 2, 1520]); R = 400
    names = [("CULTIVATORS", -math.pi / 2), ("LANDOWNERS", math.pi / 6), ("ARTISANS", 5 * math.pi / 6)]
    k = p.use("black")
    ring = p.ring(tuple(c), R, n=200, wob=0.004)
    p.use("mustard").stroke(ring, width=40, taper=False)
    k.stroke(ring, width=4)
    for a0 in [-math.pi / 2, math.pi / 6, 5 * math.pi / 6]:      # arrows round the ring, clockwise
        for f in (0.35, 0.65):
            a = a0 + f * 2 * math.pi / 3
            q = c + R * np.array([math.cos(a), math.sin(a)])
            t = np.array([-math.sin(a), math.cos(a)])
            _arrow(k, q - t * 30, q + t * 30, width=5, head=22)
    for name, a in names:
        q = c + R * np.array([math.cos(a), math.sin(a)])
        p.use("olive").disc(tuple(q), 120, clear=True)
        p.use("mustard").disc(tuple(q), 120, clear=True)
        p.use("black").disc(tuple(q), 120, clear=True)
        k.circle(tuple(q), 120, width=7)
        p.use("olive").text(name, q[0], q[1] + (-150 if a < 0 else 200), 50, font=GROT, clear=True, track=0.06)
    # in each circle, what it does: the furrows, the house, the hammer's anvil
    q = c + R * np.array([0, -1])
    for j in range(5):
        k.line((q[0] - 70, q[1] - 40 + j * 20), (q[0] + 70, q[1] - 40 + j * 20), width=4)
    q = c + R * np.array([math.cos(math.pi / 6), math.sin(math.pi / 6)])
    k.polyline([(q[0] - 55, q[1] + 50), (q[0] - 55, q[1] - 10), (q[0], q[1] - 60), (q[0] + 55, q[1] - 10), (q[0] + 55, q[1] + 50)], width=6)
    q = c + R * np.array([math.cos(5 * math.pi / 6), math.sin(5 * math.pi / 6)])
    k.fill([(q[0] - 60, q[1] - 30), (q[0] + 60, q[1] - 30), (q[0] + 30, q[1]), (q[0] + 20, q[1] + 50), (q[0] - 20, q[1] + 50), (q[0] - 30, q[1])])
    return p


DEMO = {"common-law": common_law, "nature-of-the-judicial-process": cardozo, "sabotage": sabotage,
        "wealth-of-nations": wealth_of_nations, "progress-and-poverty": progress_and_poverty, "turgot": turgot}


if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    ROOT = HERE.parent
    out = ROOT / "build" / "covers" / "demo6"
    out.mkdir(parents=True, exist_ok=True)
    tw, th, gap = 420, 630, 30
    sheet = Image.new("RGB", (len(DEMO) * (tw + gap) + gap, 2 * (th + gap) + gap + 60), "white")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("DejaVuSans.ttf", 24)
    only = sys.argv[1:]
    for i, (b, fn) in enumerate(DEMO.items()):
        x = gap + i * (tw + gap)
        if not only or b in only:
            fn(1).print(str(out / f"{b}.png"))
        im = Image.open(out / f"{b}.png").convert("RGB")
        cur = Image.open(ROOT / "site" / "covers" / f"{b}.jpg").convert("RGB")
        cur.thumbnail((tw, th)); sheet.paste(cur, (x + (tw - cur.width) // 2, gap + 50))
        sheet.paste(im.resize((tw, th)), (x, 2 * gap + th + 50))
        d.text((x, 12), b, fill="black", font=font)
    sheet.save(out / "sheet6.png")
    print(out / "sheet6.png")
