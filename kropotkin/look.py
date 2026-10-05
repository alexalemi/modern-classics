"""Crop the lines of Duke's scan (the 1914 impression) holding a phrase.
The jp2 set has one more leaf than the djvu XML at the front: image = leaf + 1.

    python3 kropotkin/look.py OUT.png "phrase" ...
"""
import glob
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent


def lines():
    x = (HERE / "_src/mutualaidfactoro1902krop_djvu.xml").read_text()
    for leaf, page in enumerate(re.findall(r"<OBJECT.*?</OBJECT>", x, re.S)):
        for ln in re.findall(r"<LINE>(.*?)</LINE>", page, re.S):
            ws = re.findall(r'<WORD coords="([^"]*)"[^>]*>(.*?)</WORD>', ln, re.S)
            if ws:
                cs = [list(map(int, c.split(","))) for c, _ in ws]
                yield leaf, " ".join(w.strip() for _, w in ws), (min(c[0] for c in cs), min(c[3] for c in cs), max(c[2] for c in cs), max(c[1] for c in cs))


def main(out, phrases):
    files = sorted(glob.glob(str(HERE / "_src/jp2/*.jp2")))
    L = list(lines())
    ims = []
    for ph in phrases:
        hits = [(lf, b) for lf, t, b in L if ph.lower() in t.lower()]
        print(ph, "->", [h[0] for h in hits][:8])
        for lf, b in hits[:2]:
            ims.append(Image.open(files[lf + 1]).convert("L").crop((max(0, b[0] - 30), b[1] - 50, b[2] + 30, b[3] + 50)))
    if ims:
        W = max(i.size[0] for i in ims)
        s = Image.new("L", (W, sum(i.size[1] + 10 for i in ims)), 255)
        y = 0
        for i in ims:
            s.paste(i, (0, y)); y += i.size[1] + 10
        s.thumbnail((1300, 4000)); s.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
