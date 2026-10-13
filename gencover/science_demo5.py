"""Round 5 (2026-10-13). Adopted designs (Howard, Capablanca, Malthus,
Verrill, Lucretius) moved to designs.py; not adopted (Alex): Beecher's
ground plan, kept here."""
import numpy as np
from press import Press, W, H
from designs import title_block, GROT


def beecher(seed):
    """Fig. 1, the ground plan of the first floor: two large rooms either
    side of the stove-room, a conservatory at each end."""
    p = Press(seed, ["teal", "orange", "black"])
    p.use("teal").field(-20, -20, W + 20, H + 20)
    title_block(p, "teal", ["THE AMERICAN", "WOMAN’S HOME"], "CATHARINE E. BEECHER  &  HARRIET BEECHER STOWE",
                ["Principles of Domestic Science"], size=150)
    s = 21                                   # pixels per foot
    ox, oy = W / 2 - 12.5 * s, 900
    def P(x, y):
        return (ox + x * s, oy + y * s)
    # the outline: main block 25 x 43, conservatories 10 x 4 at each end, kitchen bay
    out = [P(0, 4), P(7.5, 4), P(9, 0), P(16, 0), P(17.5, 4), P(25, 4), P(25, 47), P(17.5, 47),
           P(16, 51), P(9, 51), P(7.5, 47), P(0, 47), P(0, 29), P(-4, 29), P(-4, 20), P(0, 20)]
    p.use("teal").fill(out, clear=True)
    core = [P(7, 20), P(16, 20), P(16, 29), P(7, 29)]
    p.use("orange").fill(core)
    k = p.use("black")
    k.polyline(out, width=12)
    k.stroke([P(0, 20), P(25, 20)], width=8, taper=False)
    k.stroke([P(0, 29), P(25, 29)], width=8, taper=False)
    k.polyline(core, width=6)
    stove = [P(10, 22.5), P(13, 22.5), P(13, 25.5), P(10, 25.5)]
    p.use("orange").fill(stove, clear=True)
    k.fill(stove)
    p.use("orange").disc(P(11.5, 24), 18, clear=True)
    p.use("black").disc(P(11.5, 24), 18, clear=True)
    for y in np.arange(21, 29, 1.2):         # the stair
        k.line(P(16.6, y), P(22.5, y), width=2.5)
    # the fresh-air duct, from the front door to the stove-room
    p.use("orange").stroke([P(25, 24.5), P(16, 24.5)], width=18, taper=False)
    k.line(P(24, 24.5), P(17.5, 24.5), width=3)
    k.fill([P(17.5, 23.6), P(17.5, 25.4), P(16.4, 24.5)])
    for y0 in (8, 34):                       # piazza, dashed
        for y in np.arange(y0, y0 + 11, 2):
            k.line(P(27, y), P(27, y + 1.1), width=4)
    lab = p.use("black")
    lab.text("DRAWING ROOM", *P(12.5, 12.5), 40, font=GROT, track=0.05)
    lab.text("25 × 16", *P(12.5, 15), 34, font=GROT)
    lab.text("25 × 16", *P(12.5, 39), 34, font=GROT)
    lab.text("KITCHEN", *P(1.6, 24.4), 26, font=GROT)
    lab.text("CONSERVATORY", *P(12.5, 3), 26, font=GROT)
    lab.text("CONSERVATORY", *P(12.5, 49.3), 26, font=GROT)
    return p


