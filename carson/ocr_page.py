"""Build a proof page from the PDF's own text layer, for pages no reader
could transcribe (Guarding 05-10: the readers' output was stopped by an
automated filter twice, so the words come from the scan's OCR instead,
corrected word by word against the image via FIXES below).

    python3 carson/ocr_page.py BOOK NN [--plate "x0 y0 x1 y1 | kind | caption"] ...
    python3 carson/ocr_page.py BOOK NN --suspects     # words to check on the image

Words are taken with their boxes (pdftotext -bbox), grouped into lines,
split into the left and right column at the page's middle, read left
column then right; a line indented past the column's left edge opens a
paragraph; line-end hyphens are joined; page numbers and the running
caption line are dropped by the FIXES / DROP lists.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = {"guarding": "arlis_1472474"}
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}


def words(book, nn):
    pdf = HERE / f"_src/{SRC[book]}.pdf"
    x = subprocess.run(["pdftotext", "-bbox", "-f", str(nn), "-l", str(nn), str(pdf), "-"],
                       capture_output=True, text=True).stdout
    pw = float(re.search(r'<page width="([\d.]+)"', x).group(1))
    ph = float(re.search(r'height="([\d.]+)"', x).group(1))
    import html
    ws = [(float(a), float(b), float(c), float(d), html.unescape(w))
          for a, b, c, d, w in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', x)]
    return ws, pw, ph


def lines_of(ws):
    ws = sorted(ws, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines = []
    for w in ws:
        mid = (w[1] + w[3]) / 2
        if lines and abs(lines[-1]["mid"] - mid) < 4:
            lines[-1]["w"].append(w)
        else:
            lines.append({"mid": mid, "w": [w]})
    for l in lines:
        l["w"].sort(key=lambda w: w[0])
        l["x0"] = l["w"][0][0]
        l["text"] = " ".join(w[4] for w in l["w"])
    # page numbers and specks: a line of only digits or punctuation
    return [l for l in lines if re.search(r"[A-Za-z]{2}", l["text"])]


def build(book, nn, ylo=0.0, yhi=1.0):
    ws, pw, ph = words(book, nn)
    ws = [w for w in ws if ylo * ph <= w[1] <= yhi * ph]
    # the gutter: the x between 40% and 62% of the page that the fewest
    # words cross (the left column can run past the middle)
    def crossing(x):
        return sum(1 for w in ws if w[0] < x < w[2])
    xs = [pw * f / 100 for f in range(40, 63)]
    best = min(crossing(x) for x in xs)
    cands = [x for x in xs if crossing(x) == best]
    half = cands[len(cands) // 2]
    cols = [[w for w in ws if (w[0] + w[2]) / 2 < half], [w for w in ws if (w[0] + w[2]) / 2 >= half]]
    paras = []
    for col in cols:
        ls = lines_of(col)
        if not ls:
            continue
        left = sorted(l["x0"] for l in ls)[len(ls) // 4]
        for l in ls:
            new = l["x0"] > left + 6
            if new or not paras:
                paras.append(l["text"])
            else:
                prev = paras[-1]
                if re.search(r"[A-Za-z]-$", prev):
                    paras[-1] = prev[:-1] + l["text"]
                else:
                    paras[-1] = prev + " " + l["text"]
    return paras


def suspects(paras):
    out = []
    for p in paras:
        for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", p):
            core = w.strip("'’-").lower()
            if core and core not in DICT and core.rstrip("s") not in DICT:
                out.append(w)
    return sorted(set(out))


if __name__ == "__main__":
    book, nn = sys.argv[1], int(sys.argv[2])
    paras = build(book, nn)
    if "--suspects" in sys.argv:
        print(len(paras), "paragraphs;", sum(len(p.split()) for p in paras), "words")
        print("SUSPECT:", " ".join(suspects(paras)))
        for p in paras:
            print("  starts:", " ".join(p.split()[:4]), "...", " ".join(p.split()[-3:]))
