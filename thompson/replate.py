"""Re-cut Thompson's plates from the page scans and turn them into black
ink on a transparent ground.

    python3 thompson/replate.py [--out DIR] [--only 12,75-76]

Two problems with the plates as first cut, both visible the moment you
read the assembled page:

1. **They are clipped.** The boxes come from ABBYY's Picture blocks,
   which fit the *engraving* and not the drawing: arrowheads, the outer
   labels ("Light No. 2"), the last ray of a pencil of rays all fall
   outside the block and were cut off. Re-cutting with a fixed margin
   would be a guess in both directions — too little and the arrowhead is
   still gone, too much and the body text below comes with it. So each
   side is GROWN OUTWARD UNTIL IT REACHES WHITESPACE: scan away from the
   box a line at a time, stop at the first run of blank lines, back off
   by a small pad. That recovers whatever the block clipped and stops in
   the gutter before the running text, and it is self-limiting on a
   plate that was never clipped at all.

2. **The paper is in the picture.** These are photographs of a
   hundred-year-old page, so every plate carries its own patch of cream
   with its own cast, and 127 slightly different creams down a white
   page read as dirt. Here the ink is separated from the paper and the
   paper is thrown away: the darkness of a pixel becomes its ALPHA over
   pure black, so what survives is the ink itself, anti-aliased as the
   scan had it, on a transparent ground.

Alpha rather than a hard threshold matters for this particular book: a
fifth of the plates are halftones — the Röntgen photographs, the ripple
tank, the dark-ground lantern shots — and a bilevel threshold destroys
them. Mapping darkness to alpha keeps a halftone looking like a
halftone while still throwing the paper away.

NOTE ON THE DARK PLATES. Some of Thompson's figures are printed white on
black (a lantern beam crossing a darkened room). The same mapping is
right for them with no special case: their black ground is ink and stays
opaque, their white lines are paper and become transparent, so over a
white page they look exactly as printed.

Needs the page scans: run `bash thompson/fetch.sh` from thompson/ first
(132 pages, ~100 MB, not kept in the repo).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BOOK = Path(__file__).parent
PAGES = BOOK / "pages"
SITE_IMG = BOOK.parent / "site/images/thompson"

# Growth: how far a side may travel looking for whitespace, how many
# blank lines end the search, and how much white to leave once it stops.
# MAX_GROW is deliberately generous — several of ABBYY's boxes clip a
# figure by 200 px and more (fig 3 loses the whole barrier and slit the
# wavefronts are diffracting through) — and CAPS holds the handful of
# plates where a generous search runs into the body text instead.
MAX_GROW = 400
BLANK_RUN = 16
PAD = 10

# Ink/paper separation. PAPER_PCT has to be near the top of the
# histogram, not near its mode: a fifth of these plates are printed white
# on black, where the mode IS the ink and a mid-percentile "paper" leaves
# the black ground at 0.9 alpha instead of 1.0 — enough for the text
# printed on the back of the leaf to show through it as a legible ghost.
PAPER_PCT = 99
INK_PCT = 2
LO, HI = 0.12, 0.82     # contrast curve: below LO is paper, above HI solid
MIN_SPAN = 40           # if paper and ink are this close, it is all one

# The scans are ~1956 px wide and the page these plates are read on is
# 70 characters; anything past this is weight with no detail in it.
MAX_DIM = 1500

# Alpha quantisation. The scan's noise gives every stroke a fringe of
# unique values, which PNG cannot compress; rounding the alpha to a few
# dozen levels halves the file and is invisible. Line art needs only
# enough levels to anti-alias an edge; a halftone needs enough not to
# band, so the two are told apart by how much of the plate is midtone.
LEVELS_LINE, LEVELS_TONE = 16, 48
TONAL_FRAC = 0.25

# Per-figure growth caps, set by eye where the search overshoots into
# body text or a neighbouring cut: {fig: {side: max_px}}, sides L T R B.
# Everything here was found by montaging all 127 and looking; the search
# has no way to tell a column of Thompson's prose from part of his
# diagram, and on a page where the two are a few pixels apart it walks
# straight into the text.
# A NEGATIVE cap moves that edge inward instead: ABBYY's box occasionally
# includes page furniture to begin with, and no amount of not-growing
# will take it back out.
CAPS = {
    "62": {"R": 30},          # the film-strip; body text runs alongside it
    "63": {"T": 1},           # the refractive-index chart, text above
    "70": {"T": -46},         # the box takes in the page number "116"
    "85": {"T": 1, "R": 30},  # the polarising prism, text above and beside
    "88-89-90": {"B": 105},   # keep the three captions, drop the prose
    "91": {"B": 55},          # keep "FIG. 91.", drop the prose
    "158": {"L": 30, "B": -96},  # Stokes's hypothesis, text all round it
}


def ink_mask(gray):
    """Boolean ink map used for finding edges, not for output."""
    paper = np.percentile(gray, PAPER_PCT)
    return gray < paper - 55


def grow(fig, box, page_gray):
    """Expand a box until each side reaches whitespace. Returns the new
    box, clamped to the page."""
    H, W = page_gray.shape
    x, y, w, h = box
    l, t, r, b = x, y, min(x + w, W), min(y + h, H)
    ink = ink_mask(page_gray)

    caps = CAPS.get(fig, {})

    def scan(fixed_lo, fixed_hi, start, step, limit, axis, side):
        """Walk outward from `start`; return the coordinate to stop at."""
        cap = caps.get(side, MAX_GROW)
        if cap < 0:                      # move the edge inward
            return start - step * abs(cap)
        blanks, last_ink = 0, start
        pos = start
        for _ in range(cap):
            pos += step
            if not (0 <= pos < limit):
                break
            line = (ink[pos, fixed_lo:fixed_hi] if axis == 0
                    else ink[fixed_lo:fixed_hi, pos])
            if line.any():
                blanks, last_ink = 0, pos
            else:
                blanks += 1
                if blanks >= BLANK_RUN:
                    break
        return last_ink + step * PAD

    t2 = max(0, scan(l, r, t, -1, H, 0, "T"))
    b2 = min(H, scan(l, r, b - 1, +1, H, 0, "B") + 1)
    l2 = max(0, scan(t2, b2, l, -1, W, 1, "L"))
    r2 = min(W, scan(t2, b2, r - 1, +1, W, 1, "R") + 1)
    return l2, t2, r2, b2


def to_ink(crop_gray):
    """Darkness -> alpha over pure black."""
    paper = float(np.percentile(crop_gray, PAPER_PCT))
    floor = float(np.percentile(crop_gray, INK_PCT))
    span = max(paper - floor, MIN_SPAN)
    a = (paper - crop_gray.astype(np.float32)) / span
    a = (a - LO) / (HI - LO)
    a = np.clip(a, 0.0, 1.0)
    out = np.zeros(crop_gray.shape + (2,), dtype=np.uint8)   # L=0, A
    out[..., 1] = np.round(a * 255).astype(np.uint8)
    tonal = ((out[..., 1] > 40) & (out[..., 1] < 215)).mean()
    levels = LEVELS_TONE if tonal > TONAL_FRAC else LEVELS_LINE
    q = out[..., 1].astype(np.float32) / 255.0
    out[..., 1] = np.round(np.round(q * (levels - 1)) / (levels - 1) * 255)
    img = Image.fromarray(out, mode="LA")
    if max(img.size) > MAX_DIM:
        s = MAX_DIM / max(img.size)
        img = img.resize((max(1, round(img.width * s)),
                          max(1, round(img.height * s))), Image.LANCZOS)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(SITE_IMG))
    ap.add_argument("--only", help="comma-separated figure ids")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    plates = json.loads((BOOK / "plates.json").read_text())
    if args.only:
        want = set(args.only.split(","))
        plates = [p for p in plates if p["fig"] in want]
    if not PAGES.exists():
        sys.exit("no thompson/pages — run `bash fetch.sh` from thompson/ first")

    cache, report = {}, []
    for p in plates:
        pf = PAGES / f"p{p['page']:03d}.jpg"
        if not pf.exists():
            sys.exit(f"missing page scan {pf}")
        if pf not in cache:
            cache.clear()                       # one page at a time
            cache[pf] = np.asarray(Image.open(pf).convert("L"))
        page = cache[pf]
        x, y, w, h = p["box"]
        l, t, r, b = grow(p["fig"], p["box"], page)
        img = to_ink(page[t:b, l:r])
        img.save(out / f"fig{p['fig']}.png", optimize=True)
        report.append((p["fig"], (w, h), (r - l, b - t),
                       (x - l, y - t, (r - l) - w - (x - l),
                        (b - t) - h - (y - t))))

    grew = [rr for rr in report if any(v > PAD for v in rr[3])]
    print(f"re-cut {len(report)} plates; {len(grew)} recovered clipped content")
    for fig, old, new, d in sorted(grew, key=lambda rr: -max(rr[3]))[:15]:
        print(f"  fig{fig:<10} {old[0]}x{old[1]} -> {new[0]}x{new[1]}"
              f"   grew L{d[0]} T{d[1]} R{d[2]} B{d[3]}")


if __name__ == "__main__":
    main()
