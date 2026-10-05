"""Cut the Blake plates out of the scan -> site/images/perlman/fig{id}.jpg.

    python3 perlman/plates.py

Perlman opens each of the 24 chapters with a framed plate at the head of
the page (leaves listed in CHAPTER_LEAVES, found by the darkness of the
page's upper half and checked on a contact sheet); the title page carries
two narrow vignettes, and a pale one closes the book under the dateline.

A plate is found by its own ink: rows darker than the paper, from the
first inked row to the first long run of blank rows (the gap above the
chapter number); then the same across columns within those rows. Each box
is asserted against a size band, since a plate that ran into the text
below would come out far too tall.
"""
import glob
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent / "site/images/perlman"
CHAPTER_LEAVES = [7, 19, 34, 53, 67, 77, 82, 88, 99, 109, 119, 128, 134, 146,
                  163, 174, 188, 202, 213, 232, 246, 259, 272, 290]
LONG_SIDE = 1400


def ink_runs(profile, thresh, gap):
    """[(start, end)] of runs where profile > thresh, merging gaps < gap."""
    runs, start, last = [], None, None
    for i, v in enumerate(profile):
        if v > thresh:
            if start is None:
                start = i
            elif i - last > gap:
                runs.append((start, last + 1))
                start = i
            last = i
    if start is not None:
        runs.append((start, last + 1))
    return runs


def boxes(im, gap=40):
    """Inked regions top to bottom, each (l, t, r, b), on a greyscale page."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    step = 3
    rows = [sum(px[x, y] < 128 for x in range(0, w, step)) / (w / step) for y in range(h)]
    out = []
    for t, b in ink_runs(rows, 0.004, gap):
        cols = [sum(px[x, y] < 128 for y in range(t, b, step)) / ((b - t) / step) for x in range(w)]
        cr = ink_runs(cols, 0.01, 60)
        if cr:
            out.append((cr[0][0], t, cr[-1][1], b))
    return out


def plate_box(im):
    """The first tall inked region: the plate, not a line of text, trimmed
    to the bottom rule of its frame (the chapter number can sit close
    enough below to join the inked run)."""
    for l, t, r, b in boxes(im):
        if b - t > 300:
            g = im.convert("L").load()
            ruled = [y for y in range(t, b)
                     if sum(g[x, y] < 128 for x in range(l, r, 2)) > 0.6 * (r - l) / 2]
            return (l, t, r, ruled[-1] + 1 if ruled else b)
    raise SystemExit("no plate")


def main():
    files = sorted(glob.glob(str(HERE / "_src/jp2/*.jp2")))
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    L = "abcdefghijklmnopqrstuvwxyz"

    def save(pid, leaf, box, pale=False):
        im = Image.open(files[leaf]).convert("L")
        pad = 12
        l, t, r, b = box
        crop = im.crop((max(0, l - pad), max(0, t - pad), min(im.size[0], r + pad), min(im.size[1], b + pad)))
        w, h = crop.size
        assert 300 < w < 1400 and 150 < h < 2000, (pid, leaf, crop.size)
        if max(crop.size) > LONG_SIDE:
            crop.thumbnail((LONG_SIDE, LONG_SIDE))
        crop.save(OUT / f"fig{pid}.jpg", "JPEG", quality=88)
        rows.append({"id": pid, "leaf": leaf, "box": list(box), "size": list(crop.size)})

    # title page: the two narrow vignettes above and below the title
    tb = [bx for bx in boxes(Image.open(files[3])) if bx[2] - bx[0] > 1000]      # the title lines are narrower
    assert len(tb) == 2, tb
    save("aa", 3, tb[0])
    save("ab", 3, tb[1])
    for n, leaf in enumerate(CHAPTER_LEAVES, 1):
        # digit-free ids (RESTORED.md): chapter 1 is "ca", chapter 24 "cx"
        save("c" + L[n - 1], leaf, plate_box(Image.open(files[leaf])))
    # the closing vignette under "Detroit, March 1983": pale, so a lower threshold
    end = Image.open(files[308]).convert("L")
    w, h = end.size
    pale = end.point(lambda v: 0 if v < 200 else 255)
    eb = [bx for bx in boxes(pale) if bx[3] - bx[1] > 300]
    assert eb, "no closing vignette"
    save("zz", 308, eb[-1])
    (HERE / "plates.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(len(rows), "plates")


if __name__ == "__main__":
    main()
