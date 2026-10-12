"""Fourth round of proposals (for review)."""
import math
import numpy as np
from press import Press, W, H
from designs import title_block, GROT


def psychology_briefer_course(seed):
    """James's Fig. 53: lines of thought leaving A by very different paths,
    straight, wavy, looping, jagged, and all arriving at Z."""
    p = Press(seed, ["magenta", "black"])
    p.use("magenta").field(-20, -20, W + 20, H + 20)
    title_block(p, "magenta", ["PSYCHOLOGY"], "WILLIAM JAMES", ["Briefer Course",
                "“The only images intrinsically important are the halting-places…”"], size=200)
    k = p.use("black")
    A, Z = np.array([190.0, 1460]), np.array([1210.0, 1460])
    t = np.linspace(0, 1, 400)
    base = A + np.outer(t, Z - A)
    def env(peak):                       # a hump that peaks at `peak` (0..1), not mirror-symmetric
        return np.where(t < peak, np.sin(np.pi / 2 * t / peak), np.sin(np.pi / 2 * (1 - t) / (1 - peak))) ** 1.2
    tri = 2 * np.abs((t * 9) % 1 - 0.5)                  # a triangle wave
    paths = [np.zeros_like(t),                                       # straight
             -470 * env(0.30),                                       # a long smooth arc, early
             -250 * env(0.62) + 60 * env(0.62) * np.sin(np.pi * t * 12),   # wavy
             330 * env(0.40) + 70 * (tri - 0.5) * env(0.40)]         # jagged
    for off in paths:
        pts = base + np.column_stack([np.zeros_like(t), off])
        p.use("magenta").stroke(pts, width=16, clear=True)
        k.stroke(pts, width=5)
    lx = np.linspace(0, 1, 400)                                      # looping, late
    e = env(0.7)
    lp = A + np.column_stack([lx * (Z[0] - A[0]) + 60 * np.sin(lx * 12 * np.pi) * e,
                              -110 * e + 60 * np.cos(lx * 12 * np.pi) * e])
    p.use("magenta").stroke(lp, width=16, clear=True); k.stroke(lp, width=5)
    for q, lab in ((A, "A"), (Z, "Z")):
        p.use("magenta").disc(tuple(q), 62, clear=True); k.circle(tuple(q), 62, width=6)
        k.text(lab, q[0], q[1] + 32, 90, italic=True)
    return p


def story_book_of_science(seed):
    """The garden spider's orb web, from 'The Spider's Web'."""
    p = Press(seed, ["olive", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["THE STORY-BOOK", "OF SCIENCE"], "JEAN-HENRI FABRE",
                ["“Since it must serve as a support to the silken network, the first thread", "stretched from one bank to the other must be of exceptional firmness.”"], size=150)
    c = np.array([W / 2, 1470.0])
    rng = p.rng
    n = 28
    angs = np.sort(rng.uniform(0, 2 * math.pi, n)) if False else np.linspace(0, 2 * math.pi, n, endpoint=False) + rng.normal(0, 0.03, n)
    lens = 560 + rng.normal(0, 40, n)
    tips = c + np.column_stack([lens * np.cos(angs), lens * np.sin(angs)])
    o = p.use("olive")
    o.stroke([(80, 900), (W - 80, 930)], width=7, clear=True, taper=False)         # the bridge thread
    for tip in tips:
        o.stroke([tuple(c), tuple(tip)], width=4, clear=True, taper=False)
    for r in np.arange(70, 520, 22):                                               # the spiral, radius to radius
        pts = []
        for a, L in zip(list(angs) + [angs[0] + 2 * math.pi], list(lens) + [lens[0]]):
            rr = min(r + 22 * (a - angs[0]) / (2 * math.pi), L - 20)
            pts.append(c + rr * np.array([math.cos(a), math.sin(a)]))
        o.stroke(np.array(pts), width=2.6, clear=True, taper=False)
    p.use("black").disc(tuple(c + [0, 0]), 22)
    p.use("black").disc(tuple(c + [0, 34]), 30)
    for s in (-1, 1):
        for j in range(4):
            a = math.pi / 2 + s * (0.5 + j * 0.35)
            p.use("black").stroke([tuple(c + [0, 20]), tuple(c + [0, 20] + 70 * np.array([math.cos(a) * s * -1, -math.sin(a) * 0.9]))], width=4)
    return p


def gray_plants(seed):
    """Gray's young Red Maple seedling: two long seed-leaves spread on the
    stemlet, the bud of the next pair between them, the root below."""
    p = Press(seed, ["lime", "olive", "black"])
    p.use("lime").field(-20, -20, W + 20, H + 20)
    title_block(p, "lime", ["HOW PLANTS", "GROW"], "ASA GRAY", ["A Simple Introduction to Structural Botany"], size=190)
    k = p.use("black")
    x0, ysoil = W / 2, 1600
    k.line((120, ysoil), (W - 120, ysoil), width=6)
    for x in np.arange(140, W - 140, 60):
        k.line((x, ysoil + 10), (x - 25, ysoil + 40), width=2.5)
    stem = [(x0, ysoil), (x0 - 8, ysoil - 200), (x0, ysoil - 400)]
    k.stroke(stem, width=12)
    root = [(x0, ysoil), (x0 + 10, ysoil + 160), (x0 - 15, ysoil + 300), (x0 + 5, ysoil + 420)]
    k.stroke(root, width=9)
    for (a, b) in (((x0 - 20, ysoil + 150), (x0 - 120, ysoil + 230)), ((x0 + 5, ysoil + 260), (x0 + 110, ysoil + 320)),
                   ((x0 - 10, ysoil + 340), (x0 - 90, ysoil + 400))):
        k.stroke([a, b], width=4)
    top = np.array([x0, ysoil - 400])
    for s in (-1, 1):                                       # the long, narrow seed-leaves
        t = np.linspace(0, 1, 60)
        mid = top + np.column_stack([s * 430 * t, -60 * np.sin(np.pi * t) - 40 * t])
        w = 48 * np.sin(np.pi * t) ** 0.8
        leaf = np.vstack([mid + np.column_stack([np.zeros_like(t), -w]), (mid + np.column_stack([np.zeros_like(t), w]))[::-1]])
        p.use("lime").fill(leaf, clear=True); p.use("olive").fill(leaf)
        k.polyline(leaf, width=5)
        k.stroke(mid, width=2.5)
    bud = [(x0 - 22, ysoil - 400), (x0, ysoil - 470), (x0 + 22, ysoil - 400)]
    p.use("olive").fill(bud); k.polyline(bud, width=4)
    for lab, (x, y) in (("a", (x0 + 40, ysoil - 200)), ("b", (x0 - 300, ysoil - 520)), ("b", (x0 + 300, ysoil - 520)),
                        ("c", (x0 + 60, ysoil + 250)), ("d", (x0 + 40, ysoil - 490))):
        k.text(lab, x, y, 54, italic=True)
    return p


def worthington(seed):
    """A drop's splash in stages, as Worthington describes it: the crater
    grows wider and higher, and jets shoot from its rim."""
    p = Press(seed, ["cobalt", "sky", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["A STUDY OF", "SPLASHES"], "A. M. WORTHINGTON",
                ["“…this crater grows wider and higher and thicker in the wall, and jets", "are shot out from its edge or rim.”"], size=180)
    k = p.use("black")
    cols = [(260, 0.25), (700, 0.6), (1140, 1.0)]
    for cx0, s in cols:
        y = 1750
        p.use("cobalt").field(cx0 - 200, y, cx0 + 200, y + 18)
        k.line((cx0 - 200, y), (cx0 + 200, y), width=4)
        hgt, wid = 80 + 420 * s, 80 + 110 * s
        wall = [(cx0 - wid, y), (cx0 - wid * 0.8, y - hgt * 0.6), (cx0 - wid * 0.95, y - hgt)]
        wall2 = [(x + 2 * (cx0 - x), yy) for x, yy in wall]
        shape = np.array(wall + wall2[::-1])
        p.use("cobalt").fill(shape, clear=True); p.use("sky").fill(shape)
        k.stroke(np.array(wall), width=5); k.stroke(np.array(wall2), width=5)
        n = int(4 + 8 * s)
        for j in range(n):
            a = math.pi * (0.15 + 0.7 * j / max(n - 1, 1))
            base = np.array([cx0 - wid * 0.95 * math.cos(a), y - hgt])
            tip = base + (40 + 90 * s) * np.array([-math.cos(a), -math.sin(a) * 0.9])
            k.stroke([tuple(base), tuple(tip)], width=3)
            p.use("cobalt").disc(tuple(tip), 9, clear=True); k.circle(tuple(tip), 9, width=3)
        if s < 0.4:
            p.use("cobalt").disc((cx0, y - hgt - 120), 26, clear=True); k.circle((cx0, y - hgt - 120), 26, width=4)
    return p


def speed(seed):
    """Speed's Diagram III: a frame crossed by threads in equal squares, held
    up so that the student sees appearances as a flat subject."""
    p = Press(seed, ["orange", "black"])
    p.use("orange").field(-20, -20, W + 20, H + 20)
    title_block(p, "orange", ["THE PRACTICE", "AND SCIENCE", "OF DRAWING"], "HAROLD SPEED",
                ["“A Device for Enabling Students to Observe Appearances as a Flat Subject”"], size=150)
    k = p.use("black")
    x0, y0, w, h = 230, 1050, 940, 940 * 5 / 7
    frame = [(x0 - 50, y0 - 50), (x0 + w + 50, y0 - 50), (x0 + w + 50, y0 + h + 50), (x0 - 50, y0 + h + 50)]
    p.use("orange").fill(frame, clear=True)
    k.fill(frame)
    p.use("black").fill([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], clear=True)
    # a cone and a sphere seen through it
    c = (x0 + 330, y0 + 420)
    cone = [(c[0] - 150, c[1] + 120), (c[0], c[1] - 260), (c[0] + 150, c[1] + 120)]
    k.polyline(cone, width=4)
    k.stroke([(c[0] - 150 + 300 * t, c[1] + 120 + 30 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 40)], width=4)
    k.circle((x0 + 680, y0 + 420), 130, width=4)
    k.hatch = None
    for t in np.linspace(0, 1, 9):                          # shade on the cone's dark side
        k.line((c[0] + 20 + 120 * t, c[1] + 110 - 10 * t), (c[0] + 5 + 10 * t, c[1] - 220 + 260 * t), width=2)
    for i in range(1, 7):
        k.line((x0 + i * w / 7, y0), (x0 + i * w / 7, y0 + h), width=1.8)
    for j in range(1, 5):
        k.line((x0, y0 + j * h / 5), (x0 + w, y0 + j * h / 5), width=1.8)
    return p


DEMO = {"psychology-briefer-course": psychology_briefer_course, "story-book-of-science": story_book_of_science,
        "gray-plants": gray_plants, "worthington": worthington, "speed": speed}
