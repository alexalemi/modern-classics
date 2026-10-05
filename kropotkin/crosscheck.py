"""Second reading (the epictetus rule): the finished chapters/ against the
two Duke OCRs (the 1914 impression), sharing no code with merge.py or
prep.py. Reports runs where BOTH Duke scans agree with each other against
the edition. Notes are compared as a separate stream (the edition sets
them after their paragraph, the print at the foot of the page), so the
edition is split into body and "Footnote:" text first.

    python3 kropotkin/crosscheck.py
"""
import difflib
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent


def toks(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("æ", "ae").replace("Æ", "Ae")
    return re.findall(r"[a-z]+", s.lower())


def edition():
    body, notes = [], []
    for f in sorted((HERE / "chapters").glob("*.txt")):
        for para in f.read_text().split("\n\n")[1:]:
            (notes if para.startswith("Footnote:") else body).append(para.replace("Footnote:", ""))
    return toks(" ".join(body)), toks(" ".join(notes))


def scan(name):
    t = (HERE / "_src" / name).read_text()
    # running heads and page numbers: short lines of the book's or a
    # chapter's title, or of numerals
    keep = []
    for ln in t.split("\n"):
        s = ln.strip()
        if len(s.split()) <= 7 and (re.search(r"MUTUAL\s*AID|INTRODUCTION|CONCLUSION|APPENDIX|AMONG|AMONGST|SAVAGES|BARBARIANS|ANIMALS|CITY|OURSELVES", s)
                                    or re.fullmatch(r"[\divxlcIl. ]{1,8}", s)):
            continue
        keep.append(ln)
    t = "\n".join(keep)
    t = re.sub(r"[-¬]\s*\n\s*", "", t)
    i = re.search(r"Two\s+aspects\s+of\s+animal", t).start()
    j = [m.end() for m in re.finditer(r"148\s+and\s+149", t)][-1]
    w = toks(t[i:j])
    assert len(w) > 90000, len(w)
    return w


def main():
    eb, en = edition()
    b, c = scan("mutualaidfactoro1902krop_djvu.txt"), scan("mutualaid01krop_djvu.txt")
    ed = eb + en

    def diffs(other):
        out = {}
        sm = difflib.SequenceMatcher(None, ed, other, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal" and "".join(ed[i1:i2]) != "".join(other[j1:j2]):
                out[(i1, i2)] = " ".join(other[j1:j2])
        return out
    db, dc = diffs(b), diffs(c)
    both = sorted(k for k in db if dc.get(k) == db[k])
    for i1, i2 in both:
        print(f"ED={' '.join(ed[i1:i2])[:40]!r:42} SCANS={db[(i1, i2)][:40]!r:42} ..{' '.join(ed[max(0, i1 - 6):i1])}")
    print(len(ed), "edition words;", len(both), "places both Duke scans read otherwise")


if __name__ == "__main__":
    main()
