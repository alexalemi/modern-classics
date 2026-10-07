"""Draft proofs from the scan's hOCR (_src/tarbellcourseinm0000unse_hocr.html):
one file per leaf, tarbell/draft/NNNN.txt, in the markup the page readers
correct (see page_prompt.txt).

    python3 tarbell/draft.py

Paragraphs are hOCR's ocr_par blocks, read in its order; running heads
(a "Lesson NN -- TITLE  page" line, or a page number alone) are dropped; a
line-end hyphen is closed up when the halves make a word. Text the OCR
found inside a drawing (labels, "Fig. 12") stays in the draft: the reader
removes it while marking the figure.
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_src/tarbellcourseinm0000unse_hocr.html"
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}


def is_word(k):
    k = k.lower()
    return k in DICT or k.rstrip("s") in DICT or k[:-2] in DICT or k[:-3] in DICT or k[:-1] in DICT


def join(a, b):
    m = re.search(r"([A-Za-z]+)-$", a)
    if m:
        w = re.match(r"[A-Za-z]+", b)
        if w and (is_word(m.group(1) + w.group(0)) or not (is_word(m.group(1)) and is_word(w.group(0)))):
            return a[:-1] + b
        return a + b
    return (a + " " + b).strip()


def pages():
    t = SRC.read_text(errors="replace")
    for m in re.finditer(r'<div class="ocr_page" id="page_(\d+)"(.*?)(?=<div class="ocr_page"|\Z)', t, re.S):
        leaf = int(m.group(1))
        paras = []
        for p in re.finditer(r'<p class="ocr_par"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)"[^>]*>(.*?)</p>', m.group(2), re.S):
            lines = []
            for ln in re.finditer(r'<span class="ocr_line"[^>]*>(.*?)</span>\s*(?=<span class="ocr_line"|$)', p.group(5), re.S):
                words = [html.unescape(re.sub(r"<[^>]+>", "", w)).strip()
                         for w in re.findall(r'<span class="ocrx_word"[^>]*>(.*?)</span>', ln.group(1), re.S)]
                s = " ".join(w for w in words if w)
                if s:
                    lines.append(s)
            if not lines:
                continue
            text = ""
            for s in lines:
                text = join(text, s)
            paras.append((tuple(int(v) for v in p.groups()[:4]), text))
        yield leaf, paras


RUNHEAD = re.compile(r"^\S{0,4}\s*THE TARBELL COURSE IN MAGIC\s*\S{0,4}$|^(\d+\s+)?Lesson\s*\d+\s*[—–-]+.*?(\s+\S{1,4})?$|^Lesson \d+\s*\|?$", re.I)


def main():
    out = HERE / "draft"
    out.mkdir(exist_ok=True)
    n = 0
    for leaf, paras in pages():
        body = []
        for i, (box, t) in enumerate(paras):
            if i < 2 and RUNHEAD.match(t) and len(t) < 70:
                continue
            if re.fullmatch(r"[\W\dIVXLivxl]{1,5}", t):
                continue
            body.append(t)
        (out / f"{leaf:04d}.txt").write_text(f"# leaf {leaf:04d}\n\n" + "\n\n".join(body) + "\n")
        n += 1
    print("drafted", n, "leaves")


if __name__ == "__main__":
    main()
