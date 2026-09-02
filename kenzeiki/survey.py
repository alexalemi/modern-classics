"""Map which half-leaves are text and which are picture, without eyes.

238 images is too many to classify by looking, and the classification
decides the whole shape of the work: the Teiho Kenzeiki zue alternates
Menzan's annotated text with Daiken's woodcuts, and only the text has
to be transcribed.

THE SIGNAL IS COLUMN REGULARITY. Woodblock text sits in evenly spaced
vertical columns, so the column-wise ink profile of a text page is a
near-periodic comb; a picture's profile is not. Score each page by how
much of its ink-density spectrum sits in the column band, and print a
map. This is a HEURISTIC and is checked against a sample by eye before
being trusted -- see check_survey().
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "pages")


def profile(path, width=900):
    im = Image.open(path).convert("L")
    w, h = im.size
    im = im.resize((width, int(h * width / w)))
    # crop away the mount and the page edge, keep the printed block
    im = im.crop((int(width * .08), int(im.size[1] * .10),
                  int(width * .95), int(im.size[1] * .92)))
    px = im.load()
    W, H = im.size
    col = []
    for x in range(W):
        dark = sum(1 for y in range(0, H, 3) if px[x, y] < 150)
        col.append(dark)
    return col


def combdepth(col):
    """How deep the white gutters between ink columns are.

    SPECTRAL REGULARITY ALONE MISCLASSIFIES, and it was checked rather
    than trusted: v1_010r is a woodcut of Dogen's birth whose lattice
    screens and railings are periodic enough to score as text. What a
    picture does NOT have is the alternation of dense ink columns with
    near-empty gutters. Compare the darkest third of columns with the
    lightest third; on text the ratio is large, on a picture the ink is
    spread and the ratio is near one.
    """
    s = sorted(col)
    n = len(s)
    lo = sum(s[:n // 3]) / max(1, n // 3)
    hi = sum(s[-n // 3:]) / max(1, n // 3)
    return hi / lo if lo > 0.5 else 99.0


def main():
    files = sorted(f for f in os.listdir(PAGES) if f.endswith(".jpg"))
    if len(sys.argv) > 1:
        files = [f for f in files if f.startswith(tuple(sys.argv[1:]))]
    for f in files:
        col = profile(os.path.join(PAGES, f))
        ink = sum(col) / len(col)
        d = combdepth(col)
        # THE DISTRIBUTION IS SHARPLY BIMODAL and the threshold sits in
        # its gap: the 30th percentile is 5.26 and the 40th is 19.30,
        # with nothing between. Calibrated by eye at both ends and in
        # the middle -- v1_003r and v1_004r are text (21-25), v1_010r
        # and v1_011l are woodcuts (3.0), and v2_028r at 5.32, the
        # highest-scoring page I checked below the gap, is Dogen
        # conferring the precepts at Kamakura. A picture misfiled as
        # text costs one wasted look; a text page misfiled as a picture
        # would silently drop a leaf of the book, so the threshold sits
        # well above the picture cluster.
        if ink < 15:
            kind = "blank"
        elif d > 10.0:
            kind = "text"
        else:
            kind = "PICTURE"
        print(f"{f}  ink {ink:6.1f}  comb {d:6.2f}  {kind}")


if __name__ == "__main__":
    main()
