"""Not adopted (Alex, 2026-10-12): Worthington keeps his own photograph.
The other round-4 designs moved to designs.py."""
import math
import numpy as np
from press import Press, W, H
from designs import title_block, GROT


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
