"""Round 7 proposals (2026-10-13): Politics and Philosophy, each drawing the
book's own example or construction. No words inside the drawings (Alex):
the title block and one verbatim epigraph only.

    python3 gencover/demo7.py [book ...]     # writes the review sheet
"""
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from press import Press, W, H  # noqa: E402
from designs import title_block, GROT  # noqa: E402


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def federalist(seed):
    """No. 51's compound republic: the people's power divided between two
    distinct governments, and each share divided again among separate
    departments."""
    p = Press(seed, ["red", "sky", "mustard", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["THE FEDERALIST", "PAPERS"], "ALEXANDER HAMILTON, JAMES MADISON, AND JOHN JAY",
                ["“…the power given up by the people is first divided between two distinct", "governments…”"], size=150)
    k = p.use("black")
    x0, x1, y0, y1 = 200, W - 200, 1000, 1960
    ym = (y0 + y1) / 2
    gap = 34
    for (ya, yb, ink) in ((y0, ym - gap / 2, "sky"), (ym + gap / 2, y1, "mustard")):
        cw = (x1 - x0 - 2 * gap) / 3
        for i in range(3):
            xa = x0 + i * (cw + gap)
            r = _rect(xa, ya, xa + cw, yb)
            p.use("red").fill(r, clear=True)
            p.use(ink).fill(r)
            k.polyline(r, width=7)
            if i == 0:                     # the legislature, itself divided in two
                k.line((xa + cw / 2, ya + 30), (xa + cw / 2, yb - 30), width=5)
    return p


def social_contract(seed):
    """Book III: the government as the mean proportional between the sovereign
    and the people -- the geometers' construction of the mean: a semicircle on
    the two lengths laid end to end, and the perpendicular where they meet."""
    p = Press(seed, ["red", "mustard", "sky", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["THE SOCIAL", "CONTRACT"], "JEAN-JACQUES ROUSSEAU",
                ["“The government is the middle term — what geometers call the mean proportional.”"], size=170)
    k = p.use("black")
    xa, xb, y = 150, W - 150, 1800
    a, b = 280, (xb - xa) - 280            # the sovereign, the people
    xm = xa + a
    R = (xb - xa) / 2; cx = (xa + xb) / 2
    t = np.linspace(math.pi, 2 * math.pi, 160)
    semi = np.column_stack([cx + R * np.cos(t), y + R * np.sin(t)])
    p.use("red").fill(np.vstack([semi, [(xb, y), (xa, y)]]), clear=True)
    p.use("sky").fill(np.vstack([semi, [(xb, y), (xa, y)]]))
    k.stroke(semi, width=7)
    hgt = math.sqrt(a * b)
    p.use("mustard").stroke([(xa, y), (xm, y)], width=26, taper=False)
    p.use("red").stroke([(xm, y), (xb, y)], width=26, taper=False, clear=True)
    p.use("black").stroke([(xm, y), (xb, y)], width=26, taper=False)
    p.use("mustard").stroke([(xm, y), (xm, y - hgt)], width=26, taper=False)
    p.use("black").stroke([(xm, y), (xm, y - hgt)], width=4)
    for q in ((xa, y), (xm, y), (xb, y), (xm, y - hgt)):
        p.use("red").disc(q, 16, clear=True); p.use("sky").disc(q, 16, clear=True); k.circle(q, 16, width=5)
    k.stroke([(xa, y), (xm, y - hgt), (xb, y)], width=3, taper=False)
    return p


def utopia(seed):
    """The island: shaped like a crescent moon, the sea coming in between its
    horns through a strait eleven miles wide to a sheltered bay; fifty-four
    cities, the capital in the middle."""
    p = Press(seed, ["red", "sky", "mustard", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["UTOPIA"], "THOMAS MORE", ["“Its shape is something like a crescent moon.”"], size=220)
    k = p.use("black")
    c = np.array([W / 2, 1460]); R = 560
    sea = p.ring(tuple(c), R + 40, n=200, wob=0.02)
    p.use("red").fill(sea, clear=True); p.use("sky").fill(sea)
    # crescent: the outer disc less an inner disc pushed toward the strait
    ci = c + np.array([0, 150]); Ri = 410
    # walk the outer edge outside the inner disc, then back along the inner edge
    angs = np.linspace(math.pi * 0.5 + 0.22, math.pi * 2.5 - 0.22, 300)     # from one horn round the top to the other
    out_edge = np.column_stack([c[0] + R * np.cos(angs), c[1] + R * np.sin(angs)])
    inner_angs = np.linspace(math.pi * 2.5 - 0.62, math.pi * 0.5 + 0.62, 200)
    in_edge = np.column_stack([ci[0] + Ri * np.cos(inner_angs), ci[1] + Ri * np.sin(inner_angs)])
    land = np.vstack([out_edge, in_edge])
    p.use("sky").fill(land, clear=True)
    p.use("mustard").fill(land)
    k.polyline(land, width=7)
    rng = p.rng
    cities = []
    for _ in range(40000):                  # fifty-four cities, spread over the land
        if len(cities) == 54:
            break
        q = c + rng.uniform(-R, R, 2)
        if np.linalg.norm(q - c) < R - 30 and np.linalg.norm(q - ci) > Ri + 30 and all(np.linalg.norm(q - o) > 48 for o in cities):
            cities.append(q)
    for q in cities:
        k.disc(tuple(q), 11)
    cap = c + np.array([0, -R + (R - (Ri - 150)) / 2 + 20])
    p.use("mustard").disc(tuple(cap), 30, clear=True); k.circle(tuple(cap), 30, width=6); k.disc(tuple(cap), 12)
    return p


def hume(seed):
    """Section IV: one billiard ball strikes another, and the second moves:
    all we ever see is the one event followed by the other."""
    p = Press(seed, ["teal", "sky", "mustard", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["AN ENQUIRY", "CONCERNING HUMAN", "UNDERSTANDING"], "DAVID HUME",
                ["“The impact of one billiard ball is followed by motion in the second.”"], size=130)
    k = p.use("black")
    r = 150
    A0, A1 = np.array([120.0, 2020]), np.array([430.0, 1660])
    d = np.array([1.0, -0.42]); d /= np.linalg.norm(d)
    B0 = A1 + d * 2 * r
    B1 = B0 + d * 400
    u = (A1 - A0) / np.linalg.norm(A1 - A0)
    for f in np.linspace(0, 1, 7)[:-1]:              # the first ball's path, as dashes
        q = A0 + (A1 - A0 - u * r) * f
        k.line(tuple(q), tuple(q + u * 40), width=6, taper=False)
    for f in np.linspace(0, 1, 6)[1:]:               # the second's, to where it will be
        q = B0 + d * r + (B1 - B0 - 2 * d * r) * f
        k.line(tuple(q - d * 40), tuple(q), width=6, taper=False)
    k.circle(tuple(B1), r, width=4)                  # where it will be
    for q, ink in ((A1, "mustard"), (B0, "sky")):
        p.use("teal").disc(tuple(q), r, clear=True); p.use(ink).disc(tuple(q), r)
        k.circle(tuple(q), r, width=8)
        p.use(ink).disc(tuple(q + np.array([-48, -50])), 28, clear=True)     # the shine
    return p


def problems_of_philosophy(seed):
    """Chapter I: the table. It is 'really' rectangular, and from almost every
    point of view it looks to have two acute angles and two obtuse ones: the
    same table from two places, and the shape itself."""
    p = Press(seed, ["violet", "mustard", "black"])
    p.use("violet").field(-20, -20, W + 20, H + 20)
    title_block(p, "violet", ["THE PROBLEMS", "OF PHILOSOPHY"], "BERTRAND RUSSELL",
                ["“If our table is ‘really’ rectangular, it will look, from almost all points of view,",
                 "as if it had two acute angles and two obtuse angles.”"], size=160)
    k = p.use("black")
    w, h = 640, 380
    views = [
        [(-w / 2 + 120, -h / 2), (w / 2 - 120, -h / 2), (w / 2 + 40, h / 2), (-w / 2 - 40, h / 2)],   # from the end
        [(-w / 2, -h / 2 + 40), (w / 2 - 160, -h / 2), (w / 2, h / 2 - 50), (-w / 2 + 150, h / 2)],   # from a corner
        [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)],                          # really
    ]
    for i, (v, (cx_, cy_)) in enumerate(zip(views, ((W / 2 - 160, 1100), (W / 2 + 160, 1500), (W / 2, 1880)))):
        pts = [(cx_ + x, cy_ + y * (0.6 if i < 2 else 0.75)) for x, y in v]
        p.use("violet").fill(pts, clear=True)
        if i == 2:
            p.use("mustard").fill(pts)
        k.polyline(pts, width=8 if i == 2 else 6)
    return p


def spinoza(seed):
    """Part II, the scholium to Proposition 8: in a circle, the rectangles made
    by the segments of crossing lines are all equal, infinitely many of them;
    two drawn."""
    p = Press(seed, ["teal", "mustard", "sky", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["ETHICS"], "BARUCH SPINOZA",
                ["“…so an infinite number of equal rectangles are contained in a circle.”"], size=220)
    k = p.use("black")
    c = np.array([W / 2, 1460]); R = 520
    disc = p.ring(tuple(c), R, n=200, wob=0.006)
    p.use("teal").fill(disc, clear=True)
    P = c + np.array([-150, 110])
    for th in np.linspace(0, math.pi, 13)[:-1]:         # the infinite family of chords through P
        d = np.array([math.cos(th), math.sin(th)])
        b = d @ (P - c); cc = (P - c) @ (P - c) - R ** 2
        s1 = -b + math.sqrt(b * b - cc); s2 = -b - math.sqrt(b * b - cc)
        k.line(tuple(P + d * s2), tuple(P + d * s1), width=2.2)
    for th, ink in ((0.35, "mustard"), (1.95, "sky")):
        d = np.array([math.cos(th), math.sin(th)]); n = np.array([-d[1], d[0]])
        b = d @ (P - c); cc = (P - c) @ (P - c) - R ** 2
        s1 = -b + math.sqrt(b * b - cc); s2 = -(-b - math.sqrt(b * b - cc))
        # the rectangle on the two segments, set on the chord at P
        rect = [tuple(P), tuple(P + d * s1), tuple(P + d * s1 + n * s2), tuple(P + n * s2)]
        poly = np.array(rect)
        p.use("teal").fill(poly, clear=True)
        p.use(ink).fill(poly)
        k.polyline(poly, width=5)
        k.line(tuple(P - d * s2), tuple(P + d * s1), width=7)
    k.stroke(disc, width=9)
    k.disc(tuple(P), 12)
    return p


def dialogues(seed):
    """Meno: Socrates and the boy double the square. Doubling the side
    quadruples it; the square on the diagonal is the double."""
    p = Press(seed, ["teal", "mustard", "sky", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["DIALOGUES"], "PLATO",
                ["“Tell me, boy — you say that doubling the side gives you double the area?”"], size=220)
    k = p.use("black")
    s = 420; c = np.array([W / 2, 1460])
    big = np.array(_rect(c[0] - s, c[1] - s, c[0] + s, c[1] + s))
    p.use("teal").fill(big, clear=True)
    p.use("mustard").fill(_rect(c[0] - s, c[1] - s, c[0], c[1]))      # the first square
    diam = np.array([(c[0], c[1] - s), (c[0] + s, c[1]), (c[0], c[1] + s), (c[0] - s, c[1])])
    p.use("sky").fill(diam)                                          # the double, on the diagonal
    k.polyline(big, width=8)
    k.line((c[0], c[1] - s), (c[0], c[1] + s), width=4)
    k.line((c[0] - s, c[1]), (c[0] + s, c[1]), width=4)
    k.polyline(diam, width=7)
    return p


def ethics(seed):
    """Book II: the mean. Ten pounds of food too much, two too little; six
    the mean of the thing itself, but the trainer's mean is relative to the
    man -- less for the beginner, more for Milo."""
    p = Press(seed, ["olive", "red", "mustard", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["NICOMACHEAN", "ETHICS"], "ARISTOTLE",
                ["“…destroyed by excess and by deficiency, and preserved by the mean.”"], size=170)
    k = p.use("black")
    x2, x10 = 200, W - 200
    def X(v): return x2 + (v - 2) / 8 * (x10 - x2)
    y = 1500
    # the beam, its two extremes, and the fulcrum at the mean
    p.use("olive").stroke([(X(2), y), (X(10), y)], width=30, taper=False, clear=True)
    p.use("mustard").stroke([(X(2), y), (X(10), y)], width=30, taper=False)
    k.stroke([(X(2), y - 15), (X(10), y - 15)], width=4, taper=False)
    k.stroke([(X(2), y + 15), (X(10), y + 15)], width=4, taper=False)
    for v in (2, 10):
        p.use("olive").disc((X(v), y), 70, clear=True); p.use("red").disc((X(v), y), 70); k.circle((X(v), y), 70, width=6)
    tri = [(X(6), y + 18), (X(6) + 110, y + 260), (X(6) - 110, y + 260)]
    p.use("olive").fill(tri, clear=True); k.fill(tri)
    for v, dy in ((4.6, -150), (7.6, -150)):              # the mean relative to us
        k.line((X(v), y - 30), (X(v), y + dy + 40), width=4, taper=False)
        p.use("olive").disc((X(v), y + dy), 26, clear=True); p.use("mustard").disc((X(v), y + dy), 26); k.circle((X(v), y + dy), 26, width=5)
    for v in (2, 6, 10):
        p.use("olive").text(str(v), X(v), y + 360 if v == 6 else y + 170, 60, font=GROT, clear=True)
    return p


def boethius(seed):
    """Book II: Fortune's wheel. 'I turn the wheel that spins.'"""
    p = Press(seed, ["olive", "mustard", "red", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["THE CONSOLATION", "OF PHILOSOPHY"], "BOETHIUS",
                ["“I turn the wheel that spins.”"], size=150)
    k = p.use("black")
    c = np.array([W / 2, 1480]); R = 520
    rim = p.ring(tuple(c), R, n=220, wob=0.005); rim2 = p.ring(tuple(c), R - 70, n=220, wob=0.005)
    p.use("olive").fill(rim, clear=True)
    p.use("mustard").fill(rim)
    p.use("mustard").fill(rim2, clear=True)
    k.polyline(rim, width=8); k.polyline(rim2, width=6)
    for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
        d = np.array([math.cos(a + 0.2), math.sin(a + 0.2)])
        k.stroke([tuple(c + d * 70), tuple(c + d * (R - 70))], width=14, taper=False)
    hub = p.ring(tuple(c), 80, n=60); p.use("red").fill(hub); k.polyline(hub, width=7)
    # one rising on the rim, one falling: two figures as discs, and the turn
    for a, ink in ((-math.pi / 2 - 0.5, "red"), (math.pi / 2 - 0.5, "red")):
        q = c + (R + 50) * np.array([math.cos(a), math.sin(a)])
        p.use("olive").disc(tuple(q), 44, clear=True); p.use(ink).disc(tuple(q), 44); k.circle(tuple(q), 44, width=6)
    arc = [tuple(c + (R + 150) * np.array([math.cos(t), math.sin(t)])) for t in np.linspace(-0.9, 0.5, 40)]
    k.stroke(arc, width=8, taper=False)
    e = np.array(arc[-1]); dd = e - np.array(arc[-3]); dd /= np.linalg.norm(dd); nn = np.array([-dd[1], dd[0]])
    k.fill([tuple(e + dd * 40), tuple(e + nn * 26), tuple(e - nn * 26)])
    return p


DEMO = {"federalist": federalist, "social-contract": social_contract, "utopia": utopia, "hume": hume,
        "problems-of-philosophy": problems_of_philosophy, "spinoza": spinoza, "dialogues": dialogues,
        "ethics": ethics, "boethius": boethius}


if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    import edition
    ROOT = HERE.parent
    out = ROOT / "build" / "covers" / "demo7"
    out.mkdir(parents=True, exist_ok=True)
    tw, th, gap = 380, 570, 24
    n = len(DEMO)
    sheet = Image.new("RGB", (n * (tw + gap) + gap, 2 * (th + gap) + gap + 50), "white")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("DejaVuSans.ttf", 22)
    only = sys.argv[1:]
    for i, (b, fn) in enumerate(DEMO.items()):
        if not only or b in only:
            pr = fn(1); pr.mark(edition.label(b)); pr.print(str(out / f"{b}.png"))
        x = gap + i * (tw + gap)
        cur = Image.open(ROOT / "build" / "covers" / "framed" / f"{b}.jpg").convert("RGB").resize((tw, th))
        sheet.paste(cur, (x, gap + 40))
        sheet.paste(Image.open(out / f"{b}.png").convert("RGB").resize((tw, th)), (x, 2 * gap + th + 40))
        d.text((x, 10), b, fill="black", font=font)
    sheet.save(out / "sheet7.png")
    print(out / "sheet7.png")
