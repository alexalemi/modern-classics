"""Second reading (the epictetus rule): the finished chapters/ against both
OCRs, sharing no code with prep.py's merge. Reports every place where the
two OCRs AGREE with each other against the edition. What may remain is
deliberate: the printer's misprints corrected (prep.MISPRINTS), the page
readings where both OCRs fail on a diacritic, and OCR's treatment of
spaced ellipses. Anything else is a defect.

    python3 perlman/crosscheck.py
"""
import difflib
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent


def toks(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", s.lower().replace("’", "").replace("'", ""))


def ocr_a():
    x = (HERE / "_src/djvu.xml").read_text()
    lines = []
    for ln in re.findall(r"<LINE>(.*?)</LINE>", x, re.S):
        t = " ".join(w.strip() for w in re.findall(r"<WORD[^>]*>(.*?)</WORD>", ln, re.S))
        if not re.fullmatch(r"[\dIl]{1,3}\.?", t.strip()):
            lines.append(t)
    return re.sub(r"[¬\-]\s*\n\s*", "", "\n".join(lines))


def ocr_b():
    lines = [l for l in (HERE / "_src/ocrB.txt").read_text().split("\n")
             if not re.fullmatch(r"\s*[\dIl|]{1,3}\.?\s*", l)]
    return re.sub(r"[¬\-]\s*\n\s*", "", "\n".join(lines))


def main():
    ed = []
    for f in sorted((HERE / "chapters").glob("*.txt"))[1:]:         # the chapters, not the front
        body = re.sub(r"^Chapter \d+$|\[Figure \w+\]", " ", f.read_text(), flags=re.M)
        ed += toks(body)
    a, b = toks(ocr_a()), toks(ocr_b())
    s = a.index("darkling") - 6
    a = a[s:]
    b = b[b.index("darkling") - 6:]

    def readings(other):
        out = {}
        sm = difflib.SequenceMatcher(None, ed, other, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal" and "".join(ed[i1:i2]) != "".join(other[j1:j2]):
                out[(i1, i2)] = " ".join(other[j1:j2])
        return out
    ra, rb = readings(a), readings(b)
    both = sorted(k for k in ra if rb.get(k) == ra[k])
    for i1, i2 in both:
        print(f"ED={' '.join(ed[i1:i2])!r:30} PRINT={ra[(i1, i2)]!r:30} ..{' '.join(ed[max(0, i1 - 6):i1])}")
    print(len(ed), "edition words;", len(both), "places both OCRs read otherwise")


if __name__ == "__main__":
    main()
