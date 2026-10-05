"""Crop the scan lines holding a phrase, to read the print.

    python3 perlman/look.py OUT.png "phrase one" "phrase two" ...

Matches against the ABBYY OCR (djvu.xml) with whitespace normalised and
case ignored; each hit is cropped from the page image with a line of
context above and below and stacked into OUT.png.
"""
import glob
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent


def lines():
    x = (HERE / "_src/djvu.xml").read_text()
    for leaf, page in enumerate(re.findall(r"<OBJECT.*?</OBJECT>", x, re.S)):
        for ln in re.findall(r"<LINE>(.*?)</LINE>", page, re.S):
            ws = re.findall(r'<WORD coords="([^"]*)"[^>]*>(.*?)</WORD>', ln, re.S)
            if not ws:
                continue
            cs = [list(map(int, c.split(","))) for c, _ in ws]
            yield (leaf, " ".join(w.strip() for _, w in ws),
                   (min(c[0] for c in cs), min(c[3] for c in cs), max(c[2] for c in cs), max(c[1] for c in cs)))


def main(out, phrases):
    files = sorted(glob.glob(str(HERE / "_src/jp2/*.jp2")))
    L = list(lines())
    ims = []
    for ph in phrases:
        hits = [(leaf, box) for leaf, t, box in L if ph.lower() in t.lower()]
        print(ph, "->", [h[0] for h in hits])
        for leaf, box in hits[:4]:
            ims.append(Image.open(files[leaf]).convert("L").crop(
                (max(0, box[0] - 30), box[1] - 60, box[2] + 30, box[3] + 60)))
    if not ims:
        return
    W = max(i.size[0] for i in ims)
    sheet = Image.new("L", (W, sum(i.size[1] + 12 for i in ims)), 255)
    y = 0
    for i in ims:
        sheet.paste(i, (0, y))
        y += i.size[1] + 12
    sheet.thumbnail((1300, 4000))
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
