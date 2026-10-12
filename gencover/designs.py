"""Generated covers, in the manner of the 1950s-60s Dover science and
mathematics paperbacks (Alex, 2026-10-12): a saturated spot-colour field,
the title knocked out of it in the top third, and one large diagram TAKEN
FROM THE BOOK ITSELF -- its own worked example, figure or construction --
drawn by hand-wobbling pen strokes and printed as misregistered plates
(press.py). Every quotation on a cover is verbatim from our text; check it
against books/{book}/modern_chapters before adding one.

Each function takes a seed and returns a Press; COVERS maps a book to its
design. ebook_meta.json marks such a cover {"generated": true, "seed": N,
"titled": true, ...}; build_ebook.prepare_cover calls render() when the
cached art is missing.
"""
import math
import numpy as np
from press import Press, W, H

GROT = "Fira Sans Black"
SIGNS = ["(", "∃", "x", ")", "(", "x", "=", "s", "y", ")"]
EXPS = [8, 4, 11, 9, 8, 11, 5, 7, 13, 9]
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def godel(seed):
    p = Press(seed, ["magenta", "lime", "black"])
    # the field, with a ragged hand-cut edge, bleeding off the page
    p.use("magenta").field(-20, -20, W + 20, H + 20)
    # title knocked out of the field, top third, flush left
    p.text("GÖDEL’S", 110, 300, 210, font=GROT, align="left", clear=True, track=-0.01)
    p.text("PROOF", 110, 490, 210, font=GROT, align="left", clear=True, track=-0.01)
    p.text("ERNEST NAGEL  &  JAMES R. NEWMAN", 116, 580, 44, font=GROT, align="left", clear=True, track=0.04)
    p.text("How a formula came to say of itself that it cannot be proved:", 116, 650, 34,
           align="left", italic=True, clear=True)
    p.text("Gödel’s 1931 argument for readers with school mathematics.", 116, 694, 34,
           align="left", italic=True, clear=True)
    # the abacus: the Gödel number of (∃x)(x = sy), from the book
    x0, x1 = 170, W - 170
    xs = np.linspace(x0, x1, 10)
    ybase = H - 230
    step = 63
    for x, s in zip(xs, SIGNS):
        p.use("magenta").text(s, x, 860, 76, bold=True, clear=True)
    for x, e, pr in zip(xs, EXPS, PRIMES):
        p.use("black").line((x, 900), (x, ybase + 10), width=4.5, jitter=1.6)
        for k in range(e):
            y = ybase - 22 - k * step
            bx = x + p.rng.normal(0, 1.5)
            if k == e - 1:
                p.use("magenta").disc((bx, y), 27, clear=True)     # paper bead on top
            else:
                p.use("lime").disc((bx, y), 24)
            p.use("black").circle((bx, y), 25 if k == e - 1 else 22, width=4.2, jitter=0.8)
        p.use("magenta").text(str(pr), x, ybase + 105, 46, font=GROT, clear=True)
    p.use("black").line((x0 - 70, ybase + 30), (x1 + 70, ybase + 30), width=11)
    return p





def title_block(p, field, lines, author, blurb=None, size=170, y0=270, x=110, lead=None):
    p.use(field)
    lead = lead or size * 0.92
    y = y0
    for ln in lines:
        p.text(ln, x, y, size, font=GROT, align="left", clear=True, track=-0.01)
        y += lead
    y += 10 - lead + size * 0.45
    p.text(author, x + 6, y, 44, font=GROT, align="left", clear=True, track=0.05)
    y += 68
    for b in (blurb or []):
        p.text(b, x + 6, y, 34, align="left", italic=True, clear=True)
        y += 44
    return y


def game_of_logic(seed):
    p = Press(seed, ["mustard", "red", "black"])
    p.use("mustard").field(-20, -20, W + 20, H + 20)
    title_block(p, "mustard", ["THE GAME", "OF LOGIC"], "LEWIS CARROLL",
                ["“It also requires one Player, at least.”"])
    # Carroll's board: a square cut in four by a cross, with a smaller
    # square in the middle: eight compartments (the triliteral diagram)
    cx0, cy0, S = W / 2, 1320, 1000
    sq = [(cx0 - S / 2, cy0 - S / 2), (cx0 + S / 2, cy0 - S / 2), (cx0 + S / 2, cy0 + S / 2), (cx0 - S / 2, cy0 + S / 2)]
    p.use("mustard").fill(sq, clear=True)
    s = S / 2
    inner = [(cx0 - s / 2, cy0 - s / 2), (cx0 + s / 2, cy0 - s / 2), (cx0 + s / 2, cy0 + s / 2), (cx0 - s / 2, cy0 + s / 2)]
    k = p.use("black")
    k.polyline(sq, width=10, jitter=2)
    k.polyline(inner, width=7, jitter=1.5)
    k.line((cx0, cy0 - S / 2 - 6), (cx0, cy0 + S / 2 + 6), width=7)
    k.line((cx0 - S / 2 - 6, cy0), (cx0 + S / 2 + 6, cy0), width=7)
    # counters: red = occupied, grey = empty (a half-tone of the black plate)
    reds = [(cx0 - S * 0.37, cy0 - S * 0.37), (cx0 + s * 0.25, cy0 + s * 0.25), (cx0 + S * 0.37, cy0 - S * 0.12)]
    greys = [(cx0 - s * 0.25, cy0 - s * 0.25), (cx0 + S * 0.12, cy0 + S * 0.37), (cx0 - S * 0.37, cy0 + S * 0.12)]
    for c in reds:
        p.use("red").disc(c, 58)
        p.use("black").circle(c, 58, width=5)
    for c in greys:
        p.use("black")._poly(p.ring(c, 58, n=40, wob=0.03), alpha=0.42)
        p.use("black").circle(c, 58, width=5)
    for lab, pos in (("x", (cx0 - S / 2 - 50, cy0 - S / 4)), ("x′", (cx0 - S / 2 - 50, cy0 + S / 4 + 20)),
                     ("y", (cx0 - S / 4, cy0 + S / 2 + 80)), ("y′", (cx0 + S / 4, cy0 + S / 2 + 80))):
        p.use("black").text(lab, *pos, 64, italic=True)
    p.use("black").text("m", cx0 + s / 2 - 40, cy0 - s / 2 + 70, 56, italic=True)
    return p


def pillow_problems(seed):
    p = Press(seed, ["cobalt", "orange", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["PILLOW", "PROBLEMS"], "LEWIS CARROLL",
                ["Thought out during wakeful hours"])
    rng = p.rng
    for _ in range(70):                       # a night of stars, knocked out
        x, y = rng.uniform(60, W - 60), rng.uniform(820, H - 80)
        p.use("cobalt").disc((x, y), rng.uniform(2.5, 6), clear=True)
    # Problem 58: AB the longest side; the vertex must fall in ABDCE, the
    # region bounded by arcs about A and B through B and A; if it falls in
    # the semicircle on AB the triangle is obtuse
    A, B = np.array([330.0, 1700]), np.array([1070.0, 1700])
    L = B[0] - A[0]
    mid = (A + B) / 2
    # the lens ABDCE: arcs of radius AB about A and about B, above AB
    t1 = np.linspace(0, math.pi / 3, 80)
    arcA = np.column_stack([A[0] + L * np.cos(t1), A[1] - L * np.sin(t1)])           # from B up to the apex
    t2 = np.linspace(2 * math.pi / 3, math.pi, 80)
    arcB = np.column_stack([B[0] + L * np.cos(t2), B[1] - L * np.sin(t2)])           # from apex down to A
    lens = np.vstack([arcA, arcB])
    p.use("cobalt").fill(lens, clear=True)
    semi_t = np.linspace(0, math.pi, 90)
    semi = np.column_stack([mid[0] + L / 2 * np.cos(semi_t), mid[1] - L / 2 * np.sin(semi_t)])
    p.use("orange").fill(semi)
    k = p.use("black")
    k.stroke(arcA, width=6); k.stroke(arcB, width=6)
    k.stroke(semi, width=4.5)
    k.line(tuple(A), tuple(B), width=8)
    V = np.array([mid[0] + 120, mid[1] - 210])          # a vertex inside the semicircle: obtuse
    k.line(tuple(A), tuple(V), width=5); k.line(tuple(B), tuple(V), width=5)
    for lab, pt, d in (("A", A, (-40, 50)), ("B", B, (40, 50))):
        k.text(lab, pt[0] + d[0], pt[1] + d[1], 60, italic=True)
    k.text("Problem 58", W / 2, H - 150, 46, italic=True)
    return p


def euclid_rivals(seed):
    p = Press(seed, ["orange", "cobalt", "black"])
    p.use("orange").field(-20, -20, W + 20, H + 20)
    title_block(p, "orange", ["EUCLID", "AND HIS", "MODERN RIVALS"], "LEWIS CARROLL",
                ["“Let EF meet the two parallel Lines AB, CD, in the points GH.", "The alternate angles AGH, GHD, shall be equal.”"],
                size=150)
    k = p.use("black")
    y1, y2 = 1160, 1620
    k.line((170, y1), (W - 170, y1), width=10)
    k.line((170, y2), (W - 170, y2), width=10)
    E, F = np.array([420.0, 930]), np.array([980.0, 1850])
    k.line(tuple(E), tuple(F), width=8)
    def at(y):
        t = (y - E[1]) / (F[1] - E[1]); return E + t * (F - E)
    G, Hh = at(y1), at(y2)
    ang = math.atan2(F[1] - E[1], F[0] - E[0])
    # the alternate angles, filled
    r = 120
    tA = np.linspace(ang, math.pi, 40)               # angle AGH: between GA (left) and GH (down the line)
    wedge1 = np.vstack([[G], np.column_stack([G[0] + r * np.cos(tA), G[1] + r * np.sin(tA)])])
    tD = np.linspace(ang + math.pi, 2 * math.pi, 40)  # angle GHD: between HG (up the line) and HD (right)
    wedge2 = np.vstack([[Hh], np.column_stack([Hh[0] + r * np.cos(tD), Hh[1] + r * np.sin(tD)])])
    p.use("cobalt").fill(wedge1); p.use("cobalt").fill(wedge2)
    k.stroke(wedge1[1:], width=4); k.stroke(wedge2[1:], width=4)
    for lab, (x, y) in (("A", (130, y1 + 20)), ("B", (W - 130, y1 + 20)), ("C", (130, y2 + 20)), ("D", (W - 130, y2 + 20)),
                        ("E", (E[0] - 30, E[1] - 10)), ("F", (F[0] + 30, F[1] + 50)),
                        ("G", (G[0] + 55, G[1] - 25)), ("H", (Hh[0] - 55, Hh[1] + 70))):
        k.text(lab, x, y, 64, italic=True)
    return p


def calculus_made_easy(seed):
    p = Press(seed, ["lime", "magenta", "black"])
    p.use("lime").field(-20, -20, W + 20, H + 20)
    title_block(p, "lime", ["CALCULUS", "MADE EASY"], "SILVANUS P. THOMPSON",
                ["“What one fool can do, another can.”"])
    k = p.use("black")
    ox, oy = 200, 1900
    k.line((ox, oy), (W - 140, oy), width=7)
    k.line((ox, oy), (ox, 820), width=7)
    xs = np.linspace(0, 1, 120)
    curve = np.column_stack([ox + 60 + xs * 1000, oy - 60 - 960 * xs ** 2])
    k.stroke(curve, width=9)
    # at P: the little triangle dx, dy, and the tangent
    x0, dx = 0.55, 0.22
    P = (ox + 60 + x0 * 1000, oy - 60 - 960 * x0 ** 2)
    Q = (ox + 60 + (x0 + dx) * 1000, oy - 60 - 960 * (x0 + dx) ** 2)
    R = (Q[0], P[1])
    p.use("magenta").fill([P, R, Q])
    k.line(P, R, width=5); k.line(R, Q, width=5)
    slope = 2 * 960 * x0 / 1000
    k.line((P[0] - 420, P[1] + 420 * slope), (P[0] + 360, P[1] - 360 * slope), width=3.5)
    k.text("dx", (P[0] + R[0]) / 2, P[1] + 75, 64, italic=True)
    k.text("dy", R[0] + 70, (R[1] + Q[1]) / 2 + 20, 64, italic=True)
    k.text("y", ox - 50, 860, 64, italic=True)
    k.text("x", W - 150, oy + 75, 64, italic=True)
    return p


def russell_imp(seed):
    p = Press(seed, ["red", "sky", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["INTRODUCTION", "TO MATHEMATICAL", "PHILOSOPHY"], "BERTRAND RUSSELL",
                ["“We can suppose all couples in one bundle, all trios in another.”"], size=118)
    k = p.use("black")
    cx0, cy0 = W / 2, 1440
    # the bundle: one loop round many couples
    loop = p.ring((cx0, cy0), 540, n=120, wob=0.04)
    loop[:, 1] = cy0 + (loop[:, 1] - cy0) * 0.92
    p.use("red").fill(loop, clear=True)
    k.polyline(loop, width=9, jitter=2)
    shapes = ["disc", "square", "tri", "star", "disc", "square", "tri"]
    centers = [(cx0 - 300, cy0 - 300), (cx0 + 120, cy0 - 360), (cx0 + 330, cy0 - 90), (cx0 - 380, cy0 + 40),
               (cx0 - 60, cy0 - 20), (cx0 + 200, cy0 + 280), (cx0 - 170, cy0 + 230)]
    rng = p.rng
    for shp, (x, y) in zip(shapes, centers):
        ang = rng.uniform(0, math.pi)
        d = 95
        pts = [(x - d * math.cos(ang), y - d * math.sin(ang)), (x + d * math.cos(ang), y + d * math.sin(ang))]
        k.line(pts[0], pts[1], width=3)                     # the pair's tie
        for (a, b) in pts:
            r = 46
            if shp == "disc":
                poly = p.ring((a, b), r, n=30, wob=0.04)
            elif shp == "square":
                poly = np.array([(a - r, b - r), (a + r, b - r), (a + r, b + r), (a - r, b + r)])
            elif shp == "tri":
                poly = np.array([(a, b - r * 1.2), (a + r * 1.1, b + r * 0.8), (a - r * 1.1, b + r * 0.8)])
            else:
                poly = np.array([(a + r * (1 if i % 2 == 0 else 0.45) * math.cos(i * math.pi / 5 - math.pi / 2),
                                  b + r * (1 if i % 2 == 0 else 0.45) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)])
            p.use("sky").fill(poly)
            k.polyline(poly, width=4.5, jitter=0.8)
    p.use("red").text("2", W - 230, H - 110, 300, font=GROT, clear=True)
    return p




def byrne(seed):
    """Byrne's own figure for I.47 (the squares on the sides of a right
    triangle), redrawn by hand in his red, yellow and blue on cream."""
    p = Press(seed, ["yellow", "red", "cobalt", "black"])
    k = p.use("black")
    k.text("THE FIRST SIX BOOKS OF", 110, 230, 66, font=GROT, align="left")
    k.text("THE ELEMENTS", 110, 380, 150, font=GROT, align="left")
    k.text("OF EUCLID", 110, 530, 150, font=GROT, align="left")
    k.text("OLIVER BYRNE", 116, 615, 46, font=GROT, align="left", track=0.05)
    k.text("“In Which Coloured Diagrams and Symbols Are Used Instead of Letters", 116, 680, 34, align="left", italic=True)
    k.text("for the Greater Ease of Learners”", 116, 724, 34, align="left", italic=True)
    # right triangle on a horizontal hypotenuse AB, right angle at C
    A, B = np.array([450.0, 1330]), np.array([1010.0, 1330])
    c = B[0] - A[0]
    a_len = c * 0.6                                  # leg AC (short), angle at A from the legs
    th = math.acos(a_len / c)
    C = A + a_len * np.array([math.cos(th), -math.sin(th)])
    def square_out(P, Q, outward):
        d = Q - P; nrm = np.array([d[1], -d[0]]) * outward
        return [tuple(P), tuple(Q), tuple(Q + nrm), tuple(P + nrm)]
    sq_AC = square_out(A, C, 1)
    sq_CB = square_out(C, B, 1)
    D = A + np.array([0, c]); E = B + np.array([0, c])
    foot = np.array([C[0], A[1]])                    # foot of the altitude on AB
    p.use("black").fill(sq_AC)
    p.use("red").fill(sq_CB)
    p.use("yellow").fill([tuple(A), tuple(foot), (foot[0], D[1]), tuple(D)])
    p.use("cobalt").fill([tuple(foot), tuple(B), tuple(E), (foot[0], E[1])])
    k = p.use("black")
    k.polyline([tuple(A), tuple(B), tuple(C)], width=7)
    k.line(tuple(A), (sq_CB[2][0], sq_CB[2][1]), width=6)
    k.line(tuple(C), tuple(E), width=6)
    k.line(tuple(C), (C[0], D[1]), width=5)
    return p


def introduction_to_mathematics(seed):
    """Periodicity (chapters XII-XIII): a radius turning in a circle traces,
    when its height is carried along, the sine wave."""
    p = Press(seed, ["olive", "orange", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["AN INTRODUCTION", "TO MATHEMATICS"], "ALFRED NORTH WHITEHEAD",
                ["“Civilization advances by extending the number of important operations", "which we can perform without thinking about them.”"], size=128)
    cx0, cy0, r = 330, 1420, 210
    p.use("olive").disc((cx0, cy0), r, clear=True)
    k = p.use("black")
    k.circle((cx0, cy0), r, width=7)
    k.line((cx0 - r - 40, cy0), (W - 120, cy0), width=4)
    ang = 0.9
    P = (cx0 + r * math.cos(ang), cy0 - r * math.sin(ang))
    k.line((cx0, cy0), P, width=6)
    p.use("orange").disc(P, 16)
    k.circle(P, 16, width=3.5)
    x0 = cx0 + r + 90
    xs = np.linspace(0, 2.2 * 2 * math.pi, 300)
    wave = np.column_stack([x0 + xs / (2.2 * 2 * math.pi) * (W - 140 - x0), cy0 - r * np.sin(xs + ang)])
    p.use("olive").rope(wave, 30, clear=True)
    p.use("orange").rope(wave, 26)
    k.stroke(wave, width=5)
    k.line(P, (x0, P[1]), width=2.5)
    return p


def tangled_tale(seed):
    """A knot drawn in rope, for a book whose ten chapters are Knots."""
    p = Press(seed, ["teal", "mustard", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["A TANGLED", "TALE"], "LEWIS CARROLL",
                ["“The writer’s intention was to embody in each Knot … one or more", "mathematical questions.”"])
    t = np.linspace(0, 2 * math.pi, 900)
    cx0, cy0, s = W / 2, 1420, 175
    xk = cx0 + s * (np.sin(t) + 2 * np.sin(2 * t))
    yk = cy0 + s * (np.cos(t) - 2 * np.cos(2 * t))
    pts = np.column_stack([xk, yk])
    z = -np.sin(3 * t)                                   # over or under
    rope = 74
    n = len(t)
    segs = [np.arange(i, min(i + 12, n)) for i in range(0, n - 1, 10)]
    segs.sort(key=lambda idx: z[idx].mean())
    for idx in segs:                    # lowest first, so each pass covers what it crosses
        q = pts[idx[0]: idx[-1] + 2]
        p.use("teal").rope(q, rope + 14, clear=True)
        p.use("black").rope(q, rope + 14)
        p.use("black").rope(q, rope, clear=True)     # the crossing strand's rim must not show through
        p.use("mustard").rope(q, rope - 2)
    return p


def symbolic_logic(seed):
    """The biliteral diagram, with a red counter 'sitting on the fence'."""
    p = Press(seed, ["brown", "red", "black"])
    p.use("brown").field(-20, -20, W + 20, H + 20)
    title_block(p, "brown", ["SYMBOLIC", "LOGIC"], "LEWIS CARROLL",
                ["“(1) No ducks waltz; (2) No officers ever decline to waltz;", "(3) All my poultry are ducks.”"])
    cx0, cy0, S = W / 2, 1380, 900
    sq = [(cx0 - S / 2, cy0 - S / 2), (cx0 + S / 2, cy0 - S / 2), (cx0 + S / 2, cy0 + S / 2), (cx0 - S / 2, cy0 + S / 2)]
    p.use("brown").fill(sq, clear=True)
    k = p.use("black")
    k.polyline(sq, width=10, jitter=2)
    k.line((cx0, cy0 - S / 2 - 6), (cx0, cy0 + S / 2 + 6), width=7)
    k.line((cx0 - S / 2 - 6, cy0), (cx0 + S / 2 + 6, cy0), width=7)
    fence = (cx0 - S / 4, cy0)                         # on the division line
    p.use("red").disc(fence, 62); p.use("black").circle(fence, 62, width=5)
    occ = (cx0 + S / 4, cy0 - S / 4)
    p.use("red").disc(occ, 62); p.use("black").circle(occ, 62, width=5)
    emp = (cx0 + S / 4, cy0 + S / 4)
    p.use("black")._poly(p.ring(emp, 62, n=40, wob=0.03), alpha=0.42); p.use("black").circle(emp, 62, width=5)
    for lab, pos in (("x", (cx0 - S / 2 - 55, cy0 - S / 4 + 20)), ("x′", (cx0 - S / 2 - 60, cy0 + S / 4 + 20)),
                     ("y", (cx0 - S / 4, cy0 + S / 2 + 85)), ("y′", (cx0 + S / 4, cy0 + S / 2 + 85))):
        p.use("black").text(lab, *pos, 64, italic=True)
    return p


def flatland(seed):
    """The Sphere passing through Flatland, as the Square sees it: a point,
    then circles growing and shrinking in the plane, and the Square beside them."""
    p = Press(seed, ["violet", "lime", "black"])
    p.use("violet").field(-20, -20, W + 20, H + 20)
    title_block(p, "violet", ["FLATLAND"], "EDWIN A. ABBOTT", ["A Romance of Many Dimensions", "“Upward, not Northward”"], size=200)
    y = 1500
    p.use("violet").field(80, y - 40, W - 80, y + 40, rough=1.0)      # the plane, edge on
    p.use("violet").fill([(80, y - 40), (W - 80, y - 40), (W - 80, y + 40), (80, y + 40)], clear=True)
    k = p.use("black")
    k.line((80, y - 40), (W - 80, y - 40), width=4); k.line((80, y + 40), (W - 80, y + 40), width=4)
    # the sphere's successive sections, seen from above, rising out of the plane
    xs = np.linspace(200, 1200, 7)
    rs = [6, 40, 62, 72, 62, 40, 6]
    for x, r in zip(xs, rs):
        c = (x, y - 230 - r)
        p.use("violet").disc(c, r, clear=True)
        p.use("lime").disc(c, r)
        k.circle(c, r, width=5)
        k.line((x, y - 230), (x, y - 40), width=2.5)
    # the Square, in the plane's own view below
    sq = [(560, 1700), (840, 1700), (840, 1980), (560, 1980)]
    p.use("violet").fill(sq, clear=True)
    p.use("lime").fill(sq)
    k.polyline(sq, width=7)
    return p


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





def forces(seed):
    """Faraday's iron filings over a bar magnet, along the lines of force."""
    p = Press(seed, ["red", "black"])
    p.use("red").field(-20, -20, W + 20, H + 20)
    title_block(p, "red", ["THE VARIOUS", "FORCES OF", "NATURE"], "MICHAEL FARADAY",
                ["“Here I have an arch of iron filings, built up as regularly as an iron bridge…”"], size=150)
    cx0, cy0 = W / 2, 1480
    L = 300
    N, S = np.array([cx0 + L, cy0]), np.array([cx0 - L, cy0])
    rng = p.rng
    k = p.use("black")
    def field(pt):
        f = np.zeros(2)
        for q, s in ((N, 1), (S, -1)):
            d = pt - q; r = np.hypot(*d) + 1e-6
            f += s * d / r ** 3
        return f
    for _ in range(2600):
        pt = np.array([rng.uniform(80, W - 80), rng.uniform(900, H - 80)])
        if abs(pt[1] - cy0) < 60 and abs(pt[0] - cx0) < L + 40:
            continue
        f = field(pt); n = np.hypot(*f)
        if n == 0:
            continue
        u = f / n
        ln = rng.uniform(10, 22)
        p.use("red").stroke([pt - u * ln, pt + u * ln], width=7, clear=True, taper=False, jitter=0.3)
        k.stroke([pt - u * ln, pt + u * ln], width=2.6, jitter=0.3)
    bar = [(cx0 - L - 40, cy0 - 55), (cx0 + L + 40, cy0 - 55), (cx0 + L + 40, cy0 + 55), (cx0 - L - 40, cy0 + 55)]
    p.use("red").fill(bar, clear=True)
    k.fill([(cx0, cy0 - 55), (cx0 + L + 40, cy0 - 55), (cx0 + L + 40, cy0 + 55), (cx0, cy0 + 55)])
    k.polyline(bar, width=6)
    k.text("N", cx0 + L - 20, cy0 + 22, 64, font=GROT, clear=True)
    k.text("S", cx0 - L + 20, cy0 + 22, 64, font=GROT)
    return p


def thompson(seed):
    """A prism spreading white light into its colours, with the invisible
    rays beyond either end: the infra-red and the ultra-violet."""
    p = Press(seed, ["black", "red", "orange", "yellow", "lime", "sky", "violet"])
    k = p.use("black")
    k.field(-20, -20, W + 20, H + 20)
    title_block(p, "black", ["LIGHT", "VISIBLE AND", "INVISIBLE"], "SILVANUS P. THOMPSON", None, size=170)
    # the beam
    k.stroke([(60, 1480), (520, 1340)], width=26, clear=True, taper=False)
    tri = [(520, 1120), (720, 1500), (360, 1500)]
    k.fill(tri, clear=True)
    p.use("sky").fill(tri)
    k.polyline(tri, width=5, clear=True)
    # the fan of colours
    src = np.array([640.0, 1360])
    angs = np.linspace(-0.05, 0.42, 9)
    inks = [None, "red", "orange", "yellow", "lime", "sky", "violet", None]
    for i in range(8):
        a0, a1 = angs[i], angs[i + 1]
        far = 900
        poly = [tuple(src), tuple(src + far * np.array([math.cos(a0), math.sin(a0)])),
                tuple(src + far * np.array([math.cos(a1), math.sin(a1)]))]
        if inks[i]:
            k.fill(poly, clear=True); p.use(inks[i]).fill(poly)
        else:
            for t in np.linspace(0.25, 1, 7):            # the invisible bands: hatched in outline
                q0 = src + far * t * np.array([math.cos(a0), math.sin(a0)])
                q1 = src + far * t * np.array([math.cos(a1), math.sin(a1)])
                k.line(tuple(q0), tuple(q1), width=3, clear=True)
    k.text("infra-red", 1150, 1290, 40, italic=True, clear=True)
    k.text("ultra-violet", 1090, 1860, 40, italic=True, clear=True)
    return p


def science_and_hypothesis(seed):
    """Lobatschewsky's plane in Poincaré's disc: straight lines are arcs that
    meet the rim at right angles, and a triangle's angles add to less than
    two right angles."""
    p = Press(seed, ["violet", "lime", "black"])
    p.use("violet").field(-20, -20, W + 20, H + 20)
    title_block(p, "violet", ["SCIENCE AND", "HYPOTHESIS"], "HENRI POINCARÉ",
                ["“If Lobatschewsky’s geometry is true, the parallax of a very distant", "star will be finite.”"], size=160)
    c = np.array([W / 2, 1420.0]); R = 520
    p.use("violet").disc(tuple(c), R, clear=True)
    k = p.use("black")
    k.circle(tuple(c), R, width=8)
    def geodesic(t1, t2):
        a, b = np.array([math.cos(t1), math.sin(t1)]), np.array([math.cos(t2), math.sin(t2)])
        if abs(math.sin(t2 - t1)) < 1e-3:
            return np.array([c + R * a, c + R * b])
        m = (a + b) / 2; cen = m / np.dot(m, m)            # centre of the orthogonal circle
        r = np.hypot(*(a - cen))
        s1, s2 = math.atan2(*(a - cen)[::-1]), math.atan2(*(b - cen)[::-1])
        d = (s2 - s1 + math.pi) % (2 * math.pi) - math.pi
        ts = np.linspace(s1, s1 + d, 80)
        return np.array([c + R * (cen + r * np.array([math.cos(t), math.sin(t)])) for t in ts])
    tri_pts = [(0.3, 1.9), (1.9, 3.8), (3.8, 0.3)]
    arcs = [geodesic(a, b) for a, b in tri_pts]
    # the triangle between the three arcs
    inner = np.vstack([a[int(len(a) * 0.0):] for a in arcs])
    rng = p.rng
    for i in range(14):
        t1 = rng.uniform(0, 2 * math.pi); t2 = t1 + rng.uniform(0.6, 2.6)
        k.stroke(geodesic(t1, t2), width=2.5)
    p.use("lime").fill(np.vstack(arcs))
    for a in arcs:
        k.stroke(a, width=6)
    # a parallel bundle: lines through one point that never meet a given line
    return p


def helmholtz(seed):
    """A string and its harmonics: the fundamental and the upper partial
    tones, each a standing wave with its nodes."""
    p = Press(seed, ["olive", "mustard", "black"])
    p.use("olive").field(-20, -20, W + 20, H + 20)
    title_block(p, "olive", ["ON THE", "SENSATIONS", "OF TONE"], "HERMANN VON HELMHOLTZ",
                ["as a Physiological Basis for the Theory of Music"], size=160)
    k = p.use("black")
    x0, x1 = 160, W - 160
    xs = np.linspace(0, 1, 300)
    for n in range(1, 7):
        y = 860 + n * 175
        amp = 70 / n ** 0.4
        up = np.column_stack([x0 + xs * (x1 - x0), y - amp * np.sin(n * np.pi * xs)])
        dn = np.column_stack([x0 + xs * (x1 - x0), y + amp * np.sin(n * np.pi * xs)])
        p.use("olive").fill(np.vstack([up, dn[::-1]]), clear=True)
        p.use("mustard").fill(np.vstack([up, dn[::-1]]))
        k.stroke(up, width=4); k.stroke(dn, width=4)
        for j in range(n + 1):
            k.disc((x0 + j / n * (x1 - x0), y), 9)
        k.text(str(n), x0 - 60, y + 18, 50, font=GROT)
    return p


def chalk(seed):
    """Globigerina, the shell of which Huxley shows much of the chalk is made."""
    p = Press(seed, ["sky", "black"])
    p.use("sky").field(-20, -20, W + 20, H + 20)
    title_block(p, "sky", ["ON A PIECE", "OF CHALK"], "T. H. HUXLEY", ["“Let us fix our attention upon the Globigerina.”"], size=170)
    k = p.use("black")
    rng = p.rng
    chambers = []
    for i in range(9):
        t = i * 1.05
        r = 50 * 1.27 ** i
        d = 0.75 * r + 10 * i
        chambers.append((np.array([d * math.cos(t), d * math.sin(t)]), r))
    show = chambers[-5:]
    xs = [c[0] - r for c, r in show] + [c[0] + r for c, r in show]
    ys = [c[1] - r for c, r in show] + [c[1] + r for c, r in show]
    off = np.array([W / 2 - (min(xs) + max(xs)) / 2, 1450 - (min(ys) + max(ys)) / 2])
    for ctr, r in show:
        p.use("sky").disc(tuple(ctr + off), r, clear=True)
    for ctr, r in show[::-1]:
        ctr = ctr + off
        k.circle(tuple(ctr), r, width=6)
        for _ in range(int(r * 0.7)):                         # the pores
            a = rng.uniform(0, 2 * math.pi); q = math.sqrt(rng.uniform(0, 0.8)) * r
            k.disc((ctr[0] + q * math.cos(a), ctr[1] + q * math.sin(a)), rng.uniform(2.5, 4.5))
    return p


def bridgman(seed):
    """The simple pendulum, the problem 'used in nearly every introduction to
    this subject'."""
    p = Press(seed, ["teal", "orange", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["DIMENSIONAL", "ANALYSIS"], "P. W. BRIDGMAN",
                ["“…the illustrative problem used in nearly every introduction to this", "subject, that of the simple pendulum.”"], size=170)
    k = p.use("black")
    piv = np.array([W / 2, 900.0]); Lp = 880; th = 0.42
    k.line((W / 2 - 260, 900), (W / 2 + 260, 900), width=10)
    for x in np.linspace(W / 2 - 250, W / 2 + 230, 13):
        k.line((x, 900), (x + 30, 860), width=3)
    bob = piv + Lp * np.array([math.sin(th), math.cos(th)])
    k.line(tuple(piv), tuple(bob), width=5)
    k.line(tuple(piv), tuple(piv + np.array([0, Lp + 60])), width=2.5)
    arc = np.array([piv + (Lp) * np.array([math.sin(t), math.cos(t)]) for t in np.linspace(-th, th, 60)])
    p.use("teal").rope(arc, 6, clear=True)
    k.stroke(arc, width=2.5)
    p.use("teal").disc(tuple(bob), 62, clear=True); p.use("orange").disc(tuple(bob), 60); k.circle(tuple(bob), 60, width=6)
    th_arc = np.array([piv + 200 * np.array([math.sin(t), math.cos(t)]) for t in np.linspace(0, th, 30)])
    k.stroke(th_arc, width=3)
    k.text("θ", piv[0] + 45, piv[1] + 260, 60, italic=True)
    k.text("l", (piv[0] + bob[0]) / 2 + 50, (piv[1] + bob[1]) / 2, 64, italic=True)
    k.text("m", bob[0] + 90, bob[1] + 20, 60, italic=True)
    k.line((bob[0], bob[1] + 70), (bob[0], bob[1] + 220), width=4)
    k.stroke([(bob[0] - 18, bob[1] + 190), (bob[0], bob[1] + 225), (bob[0] + 18, bob[1] + 190)], width=4, taper=False)
    k.text("g", bob[0] + 45, bob[1] + 200, 60, italic=True)
    return p


def fleming(seed):
    """Two sets of ripples spreading from two points and crossing:
    interference, where crest meets crest and crest meets trough."""
    p = Press(seed, ["cobalt", "sky", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["WAVES AND", "RIPPLES"], "J. A. FLEMING", ["in Water, Air, and Aether"], size=180)
    k = p.use("black")
    srcs = [np.array([520.0, 1500]), np.array([880.0, 1500])]
    for s in srcs:
        for r in np.arange(40, 900, 55):
            p.use("cobalt").circle(tuple(s), r, width=7, clear=True, overshoot=0.0)
    for s in srcs:
        p.use("cobalt").disc(tuple(s), 22, clear=True)
        k.disc(tuple(s), 14)
    return p


def ball(seed):
    """The Great Bear and the two Pointers leading the eye to the Pole Star."""
    p = Press(seed, ["cobalt", "mustard", "black"])
    p.use("cobalt").field(-20, -20, W + 20, H + 20)
    title_block(p, "cobalt", ["STAR-LAND"], "ROBERT S. BALL",
                ["“Follow the line of the two Pointers, alpha and beta, along the dotted", "line and it leads your eye straight to the Pole.”"], size=200)
    rng = p.rng
    for _ in range(140):
        q = (rng.uniform(40, W - 40), rng.uniform(820, H - 60))
        p.use("cobalt").disc(q, rng.uniform(1.5, 4), clear=True)
    # the Plough: bowl (alpha, beta, gamma, delta) and handle (epsilon, zeta, eta)
    st = {"α": (980, 1260), "β": (1010, 1500), "γ": (760, 1560), "δ": (720, 1360),
          "ε": (520, 1330), "ζ": (330, 1360), "η": (170, 1500)}
    k = p.use("black")
    order = ["η", "ζ", "ε", "δ", "α", "β", "γ", "δ"]
    for a, b in zip(order, order[1:]):
        p.use("cobalt").stroke([st[a], st[b]], width=6, clear=True, taper=False)
    A, B = np.array(st["α"]), np.array(st["β"])
    d = (A - B) / np.hypot(*(A - B))
    pole = A + d * 520
    for t in np.arange(30, 500, 32):
        q = A + d * t
        p.use("cobalt").disc(tuple(q), 5, clear=True)
    def star(c, r):
        pts = [(c[0] + (r if i % 2 == 0 else r * 0.42) * math.cos(i * math.pi / 5 - math.pi / 2),
                c[1] + (r if i % 2 == 0 else r * 0.42) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)]
        p.use("cobalt").fill(pts, clear=True)
        p.use("mustard").fill(pts)
        k.polyline(pts, width=3)
    for name, c in st.items():
        star(c, 30)
    star(tuple(pole), 46)
    k.text("α", st["α"][0] + 55, st["α"][1] + 10, 50, italic=True, clear=False)
    k.text("β", st["β"][0] + 55, st["β"][1] + 25, 50, italic=True)
    p.use("cobalt").text("POLE STAR", pole[0], pole[1] - 70, 34, font=GROT, clear=True, track=0.1)
    return p


def fontenelle(seed):
    """Descartes' vortices, as the philosopher explains them to the
    Marquise: each a whirl of matter turning about its own star."""
    p = Press(seed, ["violet", "mustard", "black"])
    p.use("violet").field(-20, -20, W + 20, H + 20)
    title_block(p, "violet", ["CONVERSATIONS", "ON THE PLURALITY", "OF WORLDS"], "BERNARD LE BOVIER DE FONTENELLE",
                ["“What we call a vortex is a mass of matter whose parts are detached", "from one another and all move in the same direction.”"], size=120)
    k = p.use("black")
    centres = [((480, 1250), 300), ((980, 1180), 230), ((1020, 1700), 260), ((420, 1790), 240)]
    rng = p.rng
    for (cx0, cy0), R in centres:
        p.use("violet").disc((cx0, cy0), R, clear=True, wob=0.06)
        for j in range(5):                                  # spiral streams of matter
            a0 = j * 2 * math.pi / 5 + rng.uniform(0, 0.4)
            ts = np.linspace(0, 2.6 * math.pi, 160)
            rr = 26 + (R - 30) * ts / ts[-1]
            pts = np.column_stack([cx0 + rr * np.cos(a0 + ts), cy0 + rr * np.sin(a0 + ts)])
            k.stroke(pts, width=3.2)
        p.use("mustard").disc((cx0, cy0), 26)
        k.circle((cx0, cy0), 26, width=3)
        k.circle((cx0, cy0), R, width=5)
    return p


def haldane(seed):
    """The square-cube law of the essay: make a man ten times as tall and his
    bones' cross-section grows a hundredfold, his weight a thousandfold."""
    p = Press(seed, ["orange", "black"])
    p.use("orange").field(-20, -20, W + 20, H + 20)
    title_block(p, "orange", ["ON BEING THE", "RIGHT SIZE"], "J. B. S. HALDANE",
                ["“Let us take the most obvious of possible cases, and consider a giant", "man sixty feet high…”"], size=160)
    k = p.use("black")
    def cube(x, y, s):
        d = s * 0.35
        front = [(x, y), (x + s, y), (x + s, y - s), (x, y - s)]
        top = [(x, y - s), (x + d, y - s - d), (x + s + d, y - s - d), (x + s, y - s)]
        side = [(x + s, y), (x + s + d, y - d), (x + s + d, y - s - d), (x + s, y - s)]
        for f in (front, top, side):
            p.use("orange").fill(f, clear=True)
        k.fill(side) if False else None
        for f in (front, top, side):
            k.polyline(f, width=max(2.5, s / 90))
        return front
    cube(150, 1900, 60)
    big = cube(380, 1900, 650)
    # the big cube's front face ruled into 10 x 10: a hundred times the area
    for i in range(1, 10):
        k.line((380 + 65 * i, 1900), (380 + 65 * i, 1250), width=1.6)
        k.line((380, 1900 - 65 * i), (1030, 1900 - 65 * i), width=1.6)
    k.text("1", 180, 1820, 48, font=GROT)
    k.text("× 10 high", 820, 1180, 44, font=GROT)
    p.use("orange").text("× 100 bone   × 1000 weight", W / 2, H - 50, 44, font=GROT, clear=True)
    return p


def de_kruif(seed):
    """Leeuwenhoek's 'little animals' in a drop of rain water, through his lens."""
    p = Press(seed, ["teal", "mustard", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["MICROBE", "HUNTERS"], "PAUL DE KRUIF",
                ["“Come here! Hurry! There are little animals in this rain water.”"], size=200)
    k = p.use("black")
    c = np.array([W / 2, 1430.0]); R = 500
    p.use("teal").disc(tuple(c), R, clear=True)
    p.use("mustard").disc(tuple(c), R)
    k.circle(tuple(c), R, width=12)
    rng = p.rng
    def inside(q, m=40):
        return np.hypot(*(q - c)) < R - m
    for _ in range(60):                                     # rods, spheres, spirals
        q = c + rng.uniform(-R, R, 2)
        if not inside(q):
            continue
        kind = rng.choice(["rod", "ball", "spiral", "chain"])
        a = rng.uniform(0, math.pi)
        u = np.array([math.cos(a), math.sin(a)])
        if kind == "rod":
            k.rope([q - u * 26, q + u * 26], 14)
        elif kind == "ball":
            k.disc(tuple(q), rng.uniform(6, 11))
        elif kind == "chain":
            for j in range(4):
                k.disc(tuple(q + u * j * 18), 7)
        else:
            ts = np.linspace(0, 1, 60)
            pts = q + np.outer(ts * 90 - 45, u) + np.outer(10 * np.sin(ts * 6 * math.pi), [-u[1], u[0]])
            k.stroke(pts, width=4)
    return p


def astronomy_for_everybody(seed):
    """The phases of the moon: sunlight from one side, the moon in eight
    places round the earth, each half lit."""
    p = Press(seed, ["black", "mustard", "orange"])
    k = p.use("black")
    k.field(-20, -20, W + 20, H + 20)
    title_block(p, "black", ["ASTRONOMY", "FOR EVERYBODY"], "SIMON NEWCOMB",
                ["“The varying phases of the moon depend upon its position", "with respect to the sun.”"], size=150)
    c = np.array([W / 2 + 60, 1450.0]); R = 430
    for y in np.linspace(1050, 1850, 9):                   # sunlight from the left
        k.stroke([(60, y), (230, y)], width=4, clear=True)
        k.stroke([(205, y - 14), (232, y), (205, y + 14)], width=4, clear=True, taper=False)
    k.circle(tuple(c), R, width=2.5, clear=True)
    k.disc(tuple(c), 70, clear=True); p.use("orange").disc(tuple(c), 70)
    for i in range(8):
        a = i * math.pi / 4
        q = c + R * np.array([math.cos(a), math.sin(a)])
        r = 52
        k.disc(tuple(q), r + 6, clear=True)
        p.use("mustard").disc(tuple(q), r)                  # lit (toward the sun, on the left)
        half = [(q[0] + r * math.cos(t), q[1] + r * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 30)]
        k.fill(half)                                        # the dark half, away from the sun
        k.circle(tuple(q), r, width=3, clear=True)
    return p


COVERS = {
    "godel": godel,
    "game-of-logic": game_of_logic,
    "pillow-problems": pillow_problems,
    "euclid-rivals": euclid_rivals,
    "calculus-made-easy": calculus_made_easy,
    "russell-imp": russell_imp,
    "byrne": byrne,
    "introduction-to-mathematics": introduction_to_mathematics,
    "tangled-tale": tangled_tale,
    "symbolic-logic": symbolic_logic,
    "flatland": flatland,
    "origin-of-species": origin_of_species,
    "relativity": relativity,
    "galileo": galileo,
    "tyndall": tyndall,
    "forces": forces,
    "thompson": thompson,
    "science-and-hypothesis": science_and_hypothesis,
    "helmholtz": helmholtz,
    "chalk": chalk,
    "bridgman": bridgman,
    "fleming": fleming,
    "ball": ball,
    "fontenelle": fontenelle,
    "haldane": haldane,
    "de-kruif": de_kruif,
    "astronomy-for-everybody": astronomy_for_everybody,
}
