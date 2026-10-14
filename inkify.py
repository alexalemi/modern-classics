"""Take the scanned paper out of a book's finished plates: black ink on a
transparent ground, the method of books/thompson/replate.py applied to
images already in site/images/{book}/ (no re-cutting).

    python3 inkify.py BOOK [--only af,ag] [--skip aa] [--dry] [--sheet PATH] [--lo 0.12]

Found by Alex (2026-10-14): most books' scans had their cream or grey
paper removed, five did not (irish-fairy-tales, capablanca, euler,
beecher, part of tarbell), and a page of cream rectangles on a white
page reads as dirt.

WHICH FILES. A plate is converted when its border is paper (bright, and
neutral or warm) and its ink is not coloured. COLOUR PLATES ARE SKIPPED:
darkness-to-alpha over black would turn a watercolour into a grey one.
A plate whose border is already near-white is left alone too, so the
tool is safe to rerun. A PHOTOGRAPH on a paper margin must be named with
--skip: dense engraving (Beecher's interiors) is as mid-toned as a
photograph by every cheap measure, and converts well, while the photo is
crushed into a poster (Capablanca's frontispiece portrait, figaa). Each converted fig*.jpg is replaced by fig*.png
(assemble.figure_name tries .jpg first, so the JPEG MUST go), and
build_ebook then gives the book `figure img{background:#fff}` for dark
reading themes, as book.css already does on the site.

--lo raises the floor below which a pixel counts as paper: the default
suits clean line art; a leaf whose back shows through (tarbell) needs
more, or the print on the other side survives as a ghost.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent

PAPER_PCT, INK_PCT = 99, 2
LO, HI = 0.12, 0.82
MIN_SPAN = 40
LEVELS_LINE, LEVELS_TONE, TONAL_FRAC = 16, 48, 0.25
MAX_DIM = 1500


def to_ink(gray, lo=LO):
    """Darkness -> alpha over pure black (thompson/replate.to_ink)."""
    paper = float(np.percentile(gray, PAPER_PCT))
    floor = float(np.percentile(gray, INK_PCT))
    span = max(paper - floor, MIN_SPAN)
    a = (paper - gray.astype(np.float32)) / span
    a = np.clip((a - lo) / (HI - lo), 0.0, 1.0)
    alpha = np.round(a * 255).astype(np.uint8)
    tonal = ((alpha > 40) & (alpha < 215)).mean()
    levels = LEVELS_TONE if tonal > TONAL_FRAC else LEVELS_LINE
    q = alpha.astype(np.float32) / 255.0
    alpha = np.round(np.round(q * (levels - 1)) / (levels - 1) * 255).astype(np.uint8)
    img = Image.fromarray(np.stack([np.zeros_like(alpha), alpha], -1), mode="LA")
    if max(img.size) > MAX_DIM:
        s = MAX_DIM / max(img.size)
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    return img


def verdict(rgb):
    """'convert', or the reason not to."""
    a = np.asarray(rgb).astype(np.float32)
    k = max(2, min(a.shape[:2]) // 60)
    border = np.concatenate([a[:k].reshape(-1, 3), a[-k:].reshape(-1, 3),
                             a[:, :k].reshape(-1, 3), a[:, -k:].reshape(-1, 3)])
    r, g, b = np.median(border, axis=0)
    if min(r, g, b) >= 246:
        return "clean already"
    if (r + g + b) / 3 < 170:
        return "dark border (a photograph or a full-bleed plate)"
    # Colour is measured AGAINST THE PAPER: cream paper is itself coloured,
    # so raw chroma puts Rackham's muted watercolours and his pen drawings
    # in the same range. The share of pixels more saturated than the paper
    # by 25 separates them cleanly on irish-fairy-tales (every colour plate
    # >= 0.03, every line drawing 0.000).
    lum = a.mean(-1)
    paper = np.percentile(lum, PAPER_PCT)
    chroma = a.max(-1) - a.min(-1)
    paper_chroma = np.median(chroma[lum > paper - 15])
    if (chroma > paper_chroma + 25).mean() > 0.01:
        return "colour plate"
    return "convert"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--sheet", default="")
    ap.add_argument("--lo", type=float, default=LO)
    args = ap.parse_args()
    d = ROOT / "site" / "images" / args.book
    only = {f"fig{x}" for x in args.only.split(",") if x}
    skip = {f"fig{x}" for x in args.skip.split(",") if x}
    files = sorted(p for p in d.glob("*.jp*g")
                   if (not only or p.stem in only) and p.stem not in skip)
    done, skipped, pairs = [], {}, []
    for p in files:
        rgb = Image.open(p).convert("RGB")
        v = verdict(rgb)
        if v != "convert":
            skipped.setdefault(v, []).append(p.name)
            continue
        ink = to_ink(np.asarray(rgb.convert("L")), args.lo)
        done.append(p.name)
        if args.sheet and len(pairs) < 12:
            pairs.append((rgb, ink))
        if not args.dry:
            ink.save(p.with_suffix(".png"), optimize=True)
            p.unlink()
    print(f"{args.book}: {len(done)} converted{' (dry run)' if args.dry else ''}")
    for v, names in skipped.items():
        print(f"  skipped, {v}: {len(names)}  e.g. {', '.join(names[:5])}")
    if args.sheet and pairs:
        cw, ch = 300, 300
        sheet = Image.new("RGB", (cw * 2, ch * len(pairs)), (255, 255, 255))
        for i, (a, b) in enumerate(pairs):
            a = a.copy(); a.thumbnail((cw - 8, ch - 8))
            b = b.convert("RGBA"); b.thumbnail((cw - 8, ch - 8))
            sheet.paste(a, (0, i * ch))
            sheet.paste(Image.new("RGB", b.size, (255, 255, 255)), (cw, i * ch), None)
            sheet.paste(b, (cw, i * ch), b)
        sheet.save(args.sheet)


if __name__ == "__main__":
    sys.exit(main())
