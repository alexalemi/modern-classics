"""Demo covers NOT adopted (Alex, 2026-10-12: the diagrams from the book work,
pictures of objects like the candle do not; Bubbles keeps Millais). The
adopted four (origin, relativity, galileo, tyndall) live in designs.py."""
import math
import numpy as np
from press import Press, W, H
from designs import title_block, GROT


def origin_of_species(seed):
    """Darwin's one figure: species A to L at the foot, the generations as
    horizontal lines, two of them branching into new species, F unchanged."""
    p = Press(seed, ["olive", "mustard", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["ON THE ORIGIN", "OF SPECIES"], "CHARLES DARWIN",
                ["“Let A to L represent the species of a genus that is large in its own country.”"], size=150)
    x0, x1, yb, yt = 150, W - 150, 1980, 900
    k = p.use("black")
    gens = 10
    for g in range(gens + 1):
        y = yb - g * (yb - yt) / gens
        k.line((x0, y), (x1, y), width=1.8, jitter=0.6)
    xs = np.linspace(x0 + 40, x1 - 40, 11)
    rng = p.rng
    step = (yb - yt) / gens
    def lineage_tree(x, max_lines):
        lines = [x]
        for g in range(gens):
            y, y2 = yb - g * step, yb - (g + 1) * step
            nxt = []
            for lx in lines:
                r = rng.random()
                if r < 0.30 and len(lines) + len(nxt) < max_lines:      # a variety splits off
                    for c in (lx - rng.uniform(25, 55), lx + rng.uniform(25, 55)):
                        c = min(max(c, x0 + 20), x1 - 20)
                        k.line((lx, y), (c, y2), width=4); nxt.append(c)
                elif r < 0.42 and len(lines) > 2:                       # extinct
                    k.disc((lx, y), 5)
                else:
                    c = lx + rng.normal(0, 8); k.line((lx, y), (c, y2), width=4); nxt.append(c)
            lines = nxt
        for lx in lines:
            p.use("olive").disc((lx, yt), 12, clear=True)
            p.use("mustard").disc((lx, yt), 12); k.circle((lx, yt), 12, width=2.5)
    for i, x in enumerate(xs):
        k.text("ABCDEFGHIKL"[i], x, yb + 70, 54, italic=True)
        if i == 0:
            lineage_tree(x, 8)
        elif i == 8:
            lineage_tree(x, 6)
        elif i == 5:                                         # F: unchanged to the top
            k.line((x, yb), (x, yt), width=4)
            p.use("olive").disc((x, yt), 12, clear=True)
            p.use("mustard").disc((x, yt), 12); k.circle((x, yt), 12, width=2.5)
        else:
            top = yb - rng.integers(1, 4) * step
            k.line((x, yb), (x + rng.normal(0, 8), top), width=4)
            k.disc((x, top), 5)
    return p


def relativity(seed):
    """Einstein's train and embankment: two strokes of lightning at A and B."""
    p = Press(seed, ["cobalt", "mustard", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["RELATIVITY"], "ALBERT EINSTEIN",
                ["“Lightning has struck the rails on our railway embankment at two places", "A and B far distant from each other.”"], size=190)
    y = 1650
    k = p.use("black")
    k.line((60, y), (W - 60, y), width=10)
    k.line((60, y + 30), (W - 60, y + 30), width=4)
    # the train
    car = [(330, y - 230), (1070, y - 230), (1070, y - 40), (330, y - 40)]
    p.use("cobalt").fill(car, clear=True)
    k.polyline(car, width=7)
    for wx in (410, 540, 860, 990):
        p.use("cobalt").disc((wx, y - 20), 26, clear=True); k.circle((wx, y - 20), 26, width=6)
    for wx in np.linspace(380, 1020, 6):
        k.polyline([(wx, y - 200), (wx + 80, y - 200), (wx + 80, y - 130), (wx, y - 130)], width=3)
    # lightning at A and B
    for ax in (190, 1210):
        bolt = [(ax + 40, 900), (ax - 30, 1150), (ax + 25, 1150), (ax - 45, 1420), (ax + 10, 1420), (ax, y)]
        p.use("cobalt").stroke(bolt, width=34, taper=False, clear=True)
        p.use("mustard").stroke(bolt, width=30, taper=False)
        k.stroke(bolt, width=4, taper=False)
    for lab, x in (("A", 190), ("B", 1210), ("M", 700)):
        k.text(lab, x, y + 110, 64, italic=True)
    k.line((700, y + 40), (700, y + 50), width=6)
    k.text("M′", 700, y - 260, 56, italic=True)
    return p


def galileo(seed):
    """The Copernican system as Galileo draws it: the Sun at the centre,
    the planets' circles, the Moon about the Earth, four moons about Jupiter."""
    p = Press(seed, ["black", "mustard", "red"])
    k = p.use("black")
    k.field(-20, -20, W + 20, H + 20)
    title_block(p, "black", ["DIALOGUE", "CONCERNING", "THE TWO CHIEF", "WORLD SYSTEMS"], "GALILEO GALILEI",
                ["Ptolemaic and Copernican"], size=118)
    c = (W / 2, 1450)
    radii = [90, 150, 225, 310, 420, 520]
    for r in radii:
        k.circle(c, r, width=4, clear=True)
    k.disc(c, 50, clear=True)
    p.use("mustard").disc(c, 46)
    rng = p.rng
    for i, r in enumerate(radii):
        a = rng.uniform(0, 2 * math.pi)
        pos = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        rp = 22 if i in (4, 5) else 15
        k.disc(pos, rp + 10, clear=True)
        p.use("red" if i != 2 else "mustard").disc(pos, rp)
        if i == 2:                       # the Earth and its Moon
            k.circle(pos, 40, width=2.5, clear=True)
            m = (pos[0] + 40, pos[1]); k.disc(m, 6, clear=True)
        if i == 4:                       # Jupiter and its four moons
            for j, rr in enumerate((36, 48, 60, 72)):
                k.circle(pos, rr, width=1.6, clear=True)
                a2 = rng.uniform(0, 2 * math.pi)
                k.disc((pos[0] + rr * math.cos(a2), pos[1] + rr * math.sin(a2)), 5, clear=True)
    return p


def candle(seed):
    """Faraday's candle, with the glass tube that draws the vapour out of the
    middle of the flame and lights it at the other end."""
    p = Press(seed, ["brown", "mustard", "orange", "black"])
    p.use("brown").field(-20, -20, W + 20, H + 20)
    title_block(p, "brown", ["THE CHEMICAL", "HISTORY OF", "A CANDLE"], "MICHAEL FARADAY",
                ["“There is no better, there is no more open door by which you can enter", "into the study of natural philosophy, than by considering the physical", "phenomena of a candle.”"], size=140)
    k = p.use("black")
    cx0 = 520
    body = [(cx0 - 90, 1450), (cx0 + 90, 1450), (cx0 + 90, 2000), (cx0 - 90, 2000)]
    p.use("brown").fill(body, clear=True); k.polyline(body, width=7)
    k.line((cx0, 1450), (cx0, 1400), width=6)
    fl = []
    for t in np.linspace(0, 2 * math.pi, 120):
        r = 1 - 0.3 * math.cos(t)
        fl.append((cx0 + 70 * math.sin(t) * (1 - 0.2 * math.cos(t)), 1300 - 190 * math.cos(t) * 0.9 + 0 * r))
    fl = np.array(fl)
    p.use("brown").fill(fl, clear=True)
    p.use("mustard").fill(fl)
    inner = (fl - [cx0, 1300]) * 0.5 + [cx0, 1330]
    p.use("orange").fill(inner)
    k.polyline(fl, width=5)
    # the bent glass tube from the dark middle of the flame
    tube = [(cx0, 1320), (cx0 + 170, 1180), (cx0 + 480, 1180), (cx0 + 560, 1100)]
    k.rope(tube, 26); p.use("brown").rope(tube, 16, clear=True)
    tip = (cx0 + 580, 1060)
    sm = p.ring(tip, 40, n=40, wob=0.12)
    p.use("brown").fill(sm, clear=True); p.use("mustard").fill(sm); k.polyline(sm, width=4)
    return p


def soap_bubbles(seed):
    """A film drawn out between two rings into a catenoid, the surface
    that, as Boys explains, has no curvature and so no pressure."""
    p = Press(seed, ["teal", "sky", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["SOAP BUBBLES"], "C. V. BOYS", ["and the Forces Which Mould Them",
                "“Let us now take two rings, place a bubble between them…”"], size=170)
    k = p.use("black")
    cx0, ytop, ybot, R = W / 2, 1000, 1880, 330
    ys = np.linspace(ytop, ybot, 80)
    mid = (ytop + ybot) / 2
    a = 230
    rs = a * np.cosh((ys - mid) / (a * 1.55))
    rs *= R / rs[0]
    left = np.column_stack([cx0 - rs, ys]); right = np.column_stack([cx0 + rs, ys])
    film = np.vstack([left, right[::-1]])
    p.use("teal").fill(film, clear=True)
    p.use("sky").fill(film)
    k.stroke(left, width=4); k.stroke(right, width=4)
    for y in (ytop, ybot):
        e = np.array([(cx0 + R * math.cos(t), y + 0.22 * R * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 90)])
        k.polyline(e, width=9)
    for t in np.linspace(0.15, 0.85, 5):                 # light bands on the film
        yy = ytop + t * (ybot - ytop); r = np.interp(yy, ys, rs)
        e = np.array([(cx0 + r * math.cos(u), yy + 0.22 * r * math.sin(u)) for u in np.linspace(0, math.pi, 50)])
        k.stroke(e, width=1.6)
    return p


def tyndall(seed):
    """Chladni's figure: sand on a vibrating square plate gathers on the
    nodal lines."""
    p = Press(seed, ["magenta", "black"])
    p.use("magenta").field(-20, -20, W + 20, H + 20)
    title_block(p, "magenta", ["SOUND"], "JOHN TYNDALL", ["“Sand scattered over a vibrating surface is driven off the vibrating parts", "of the surface and gathers along the nodal lines.”"], size=220)
    k = p.use("black")
    S = 1000; x0, y0 = (W - S) / 2, 960
    plate = [(x0, y0), (x0 + S, y0), (x0 + S, y0 + S), (x0, y0 + S)]
    k.fill(plate)
    k.polyline(plate, width=8)
    n, m = 3, 5
    rng = p.rng
    pts = rng.uniform(0, 1, (60000, 2))
    f = np.cos(n * np.pi * pts[:, 0]) * np.cos(m * np.pi * pts[:, 1]) - np.cos(m * np.pi * pts[:, 0]) * np.cos(n * np.pi * pts[:, 1])
    keep = pts[np.abs(f) < 0.05]
    for (u, v) in keep[:9000]:
        q = (x0 + 20 + u * (S - 40), y0 + 20 + v * (S - 40)); r = rng.uniform(1.5, 3.5)
        k.disc(q, r, clear=True, wob=0.2); p.use("magenta").disc(q, r, clear=True, wob=0.2); k = p.use("black")
    k.disc((x0 + S / 2, y0 + S / 2), 16, clear=True)
    p.use("magenta").disc((x0 + S / 2, y0 + S / 2), 16)
    return p


DEMO = {"origin-of-species": origin_of_species, "relativity": relativity, "galileo": galileo,
        "candle": candle, "soap-bubbles": soap_bubbles, "tyndall": tyndall}
