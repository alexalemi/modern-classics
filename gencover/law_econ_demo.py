"""Proposals for the Law and Economics books (2026-10-13). None of the six
has a figure, so each draws the book's own central example or scheme; the
labels and quotes are verbatim from modern_chapters.

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


def common_law(seed):
    """Holmes's first page, set as the picture: logic, struck out by
    experience."""
    p = Press(seed, ["brown", "red", "black"])
    p.use("brown").field(-20, -20, W + 20, H + 20)
    title_block(p, "brown", ["THE COMMON", "LAW"], "OLIVER WENDELL HOLMES JR.", [], size=190)
    b = p.use("brown")
    x = 110
    b.text("THE LIFE OF THE LAW", x, 1050, 96, font=GROT, align="left", clear=True, track=0.01)
    b.text("HAS NOT BEEN", x, 1160, 96, font=GROT, align="left", clear=True, track=0.01)
    w = b.text("LOGIC:", x, 1330, 200, font=GROT, align="left", clear=True)
    p.use("black").stroke([(x - 20, 1262), (x + w + 30, 1250)], width=22, jitter=3)
    b.text("IT HAS BEEN", x, 1460, 96, font=GROT, align="left", clear=True, track=0.01)
    b.text("EXPERIENCE.", x, 1650, 196, font=GROT, align="left", clear=True)
    p.use("red").text("EXPERIENCE.", x, 1650, 196, font=GROT, align="left")
    for i, ln in enumerate(["The felt necessities of the time, the moral and political theories",
                            "that prevail, intuitions of public policy, whether openly stated or",
                            "unconscious, even the prejudices that judges share with their fellow",
                            "men, have had a good deal more to do than the syllogism…"]):
        b.text(ln, x + 6, 1790 + i * 50, 38, align="left", italic=True, clear=True)
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
        p.use("cobalt").text(sub, tx, ty + (46 if up else 48), 34, align=al, italic=True, clear=True)
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
    p.use("orange").text("never less than five", c[0], c[1] + 340, 40, italic=True, clear=True)
    return p


def wealth_of_nations(seed):
    """The pin, in its eighteen distinct operations, one worker to each."""
    p = Press(seed, ["red", "sky", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["THE WEALTH", "OF NATIONS"], "ADAM SMITH",
                ["“The simple business of making a pin is, in this way, divided into about", "eighteen distinct operations…”"], size=170)
    k = p.use("black")
    for row in range(2):
        y0 = 1060 + row * 520
        p.use("red").fill([(90, y0 - 40), (W - 90, y0 - 40), (W - 90, y0 + 400), (90, y0 + 400)], clear=True)
        k.polyline([(90, y0 - 40), (W - 90, y0 - 40), (W - 90, y0 + 400), (90, y0 + 400)], width=6)
        for i in range(9):
            n = row * 9 + i            # 0..17
            x = 160 + i * 135
            top = y0 + 20
            L = 340 if n < 2 else 260
            if n == 0:                 # the wire, drawn out from the coil
                t = np.linspace(0, 6 * math.pi, 200)
                k.stroke(np.column_stack([x + 30 * np.cos(t), top + 120 + 8 * t / math.pi + 30 * np.sin(t) * 0.35]), width=4)
            else:
                bot = top + L
                k.line((x, top + (0 if n < 3 else 40)), (x, bot - (24 if n >= 3 else 0)), width=9, taper=False)
                if n >= 3:             # pointed
                    k.fill([(x - 5, bot - 26), (x + 5, bot - 26), (x, bot + 14)])
                if n >= 7:             # the head
                    hy = top + 40
                    p.use("sky" if n >= 12 else "black").fill([(x - 26, hy - 16), (x + 26, hy - 16), (x + 18, hy + 8), (x - 18, hy + 8)])
                if n >= 12:            # whitened
                    p.use("sky").stroke([(x, top + 52), (x, bot - 30)], width=11, taper=False)
                if n == 17:            # put into the paper
                    p.use("sky").fill([(x - 60, bot - 120), (x + 50, bot - 120), (x + 50, bot - 60), (x - 60, bot - 60)])
            p.use("black").text(str(n + 1), x, y0 + 385, 34, font=GROT)
    p.use("red").text("ten workers  ·  more than forty-eight thousand pins in a day", W / 2, 2050, 40, italic=True, clear=True)
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
    bw = 128
    for i, top in enumerate(hs):
        x = 170 + i * 150
        r = [(x, top), (x + bw, top), (x + bw, base), (x, base)]
        p.use("teal").fill(r, clear=True)
        p.use("mustard").fill([(x, margin), (x + bw, margin), (x + bw, base), (x, base)])
        if top < margin:
            p.use("red").fill([(x, top), (x + bw, top), (x + bw, margin), (x, margin)])
        k.polyline(r, width=5)
    k.stroke([(110, margin), (W - 110, margin)], width=7, taper=False)
    k.line((110, base), (W - 110, base), width=9)
    for (ink, lab, lx) in (("red", "RENT", 170), ("mustard", "WAGES AND INTEREST", 520)):
        sw = [(lx, base + 40), (lx + 50, base + 40), (lx + 50, base + 90), (lx, base + 90)]
        p.use("teal").fill(sw, clear=True); p.use(ink).fill(sw); k.polyline(sw, width=4)
        p.use("teal").text(lab, lx + 70, base + 84, 44, font=GROT, align="left", clear=True, track=0.05)
    lx = 170 + 7 * 150 + bw / 2
    p.use("teal").text("the least productive", lx + 40, margin - 210, 34, align="right", italic=True, clear=True)
    p.use("teal").text("land still in use", lx + 40, margin - 168, 34, align="right", italic=True, clear=True)
    _arrow(k, (lx, margin - 140), (lx, margin - 12), width=4, head=18)
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
