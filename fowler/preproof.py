"""Fowler, A Dictionary of Modern English Usage: a first draft of each page,
made mechanically from Archive.org's OCR, for the proofreading pass to
correct against the page image (the helmholtz/ method: fixes, not retyping).

    python3 fowler/preproof.py              # writes fowler/preproof/NNN.txt

The scan is Archive.org's a-dictionary-of-modern-english-usage, a Google
copy of the 1926 first edition (the title page is dated 1926). The OCR's own
paragraphs are unreliable here -- one holds forty lines of several entries,
another half an entry -- so paragraphs are rebuilt from the LINES:

  - the page is two columns; a line belongs to the column its left edge is
    in, and the left column is read before the right;
  - a line indented from its column's margin opens a paragraph (an entry,
    or a numbered section of one); every other line continues the last;
  - the top band is the running head (two guide words and the folio): it
    goes, and the folio becomes the "page:" line;
  - a column that opens mid-paragraph opens "+ ".

Everything else -- italic, small capitals, bold headwords, the OCR's
misreadings -- is left for the proofreader.
"""
import gzip
import html
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_src"


def pages():
    t = gzip.open(SRC / "chocr.html.gz").read().decode()
    return re.split(r'<div class="ocr_page"', t)[1:]


def gutter(pg, W, H):
    """the page's own gutter: the centre of the widest band between 30% and
    70% of the width that (almost) no word covers. The scan's margins differ
    from leaf to leaf (the left column of leaf 400 runs to 49% of the
    width), so no fixed fraction separates the columns everywhere. The
    running head is left out -- its folio sits IN the gutter (leaf 131) --
    and a band crossed by one or two stray marks still counts as empty."""
    lo, hi = int(0.30 * W), int(0.70 * W)
    cover = [0] * (hi - lo)
    for a, y, b in re.findall(r'class="ocrx_word"[^>]*title="bbox (\d+) (\d+) (\d+) \d+', pg):
        if int(y) < 0.07 * H:
            continue
        a, b = max(int(a), lo), min(int(b), hi)
        for x in range(a, b):
            cover[x - lo] += 1
    best, run, start = (0, W // 2), 0, 0
    for i, c in enumerate(cover + [99]):
        if c <= 2:
            if run == 0:
                start = i
            run += 1
        else:
            if run > best[0]:
                best = (run, lo + start + run // 2)
            run = 0
    return best[1]


def lines_of(ln, g):
    """[(x0, y0, x1, text)] for an OCR line, spaces restored between words.
    A line the OCR read straight across the gutter is TWO lines, one in
    each column: its words are split at the page's middle."""
    m = re.search(r'bbox (\d+) (\d+) (\d+) (\d+)', ln)
    if not m:
        return []
    y0 = int(m.group(2))
    words = []
    for w in re.split(r'class="ocrx_word"', ln)[1:]:
        b = re.search(r'bbox (\d+) \d+ (\d+) \d+', w)
        cs = re.findall(r'class="ocrx_cinfo"[^>]*>([^<]*)<', w)
        if cs and b:
            words.append((int(b.group(1)), int(b.group(2)), html.unescape("".join(cs))))
    out = []
    for side in (lambda x: x < g, lambda x: x >= g):
        ws = [w for w in words if side((w[0] + w[1]) / 2)]
        if ws:
            out.append((ws[0][0], y0, ws[-1][1], " ".join(w[2] for w in ws)))
    return out


CHAR_FIXES = [
    (r"(?<=[A-Za-z)]) ([;:?!])", r"\1"),          # the printer's space before : ; ? !
    (r"\bSce\b", "See"), (r"\bsce\b", "see"), (r"\bSec\b(?= [A-Z-])", "See"),
]


def fix_chars(t):
    for a, b in CHAR_FIXES:
        t = re.sub(a, b, t)
    return t


def join(lines):
    s = ""
    for t in lines:
        if s.endswith("-") and not s.endswith("--") and re.match(r"[a-z]", t):
            s = s[:-1] + t
        else:
            s = (s + " " + t) if s else t
    return re.sub(r"\s+", " ", s).strip()


def main():
    import json
    # the printed folio, from Archive.org's page map (the OCR reads the
    # running head's number badly: 118 of 247 folios it found agree); the
    # proofreader confirms it from the image
    pn = {p["leafNum"]: p["pageNumber"] for p in json.loads((SRC / "page_numbers.json").read_text())["pages"]}
    out = HERE / "preproof"
    out.mkdir(exist_ok=True)
    for i, pg in enumerate(pages()):
        m = re.search(r'bbox 0 0 (\d+) (\d+)', pg)
        W, H = int(m.group(1)), int(m.group(2))
        g = gutter(pg, W, H)
        lines = [x for l in re.split(r'class="ocr_line"', pg)[1:] for x in lines_of(l, g)]
        if not lines:
            (out / f"{i:03d}.txt").write_text("page: none\n")
            continue
        body_top = min(y for _, y, _, _ in lines)
        # the running head is the top ROW only: the first entry line sits
        # about 130px below it and is short too
        # ... and it sits in the top 7% of the page: p. 1, which has none,
        # otherwise loses its first entry line to this test
        head = [l for l in lines if l[1] < body_top + 50 and l[1] < 0.07 * H and len(l[3]) < 40]
        page = pn.get(i) or "none"
        body = [l for l in lines if l not in head]
        cols = [[l for l in body if l[0] < g], [l for l in body if l[0] >= g]]
        paras = []
        for c, col in enumerate(cols):
            if not col:
                continue
            col.sort(key=lambda l: l[1])
            margin = statistics.median(sorted(l[0] for l in col)[: max(1, len(col) // 2)])
            cur, first = [], True
            for x0, y0, x1, t in col:
                indent = x0 - margin > 18
                if indent and cur:
                    paras.append(join(cur)); cur = []
                if first and not indent:
                    t = "+ " + t
                first = False
                cur.append(t)
            if cur:
                paras.append(join(cur))
        paras = [fix_chars(p) for p in paras]
        (out / f"{i:03d}.txt").write_text(f"page: {page}\n\n" + "\n\n".join(paras) + "\n")
    print(i + 1, "pages")


if __name__ == "__main__":
    main()
