"""The scan witnesses for Kropotkin's Mutual Aid (1904 revised edition).

A  ABBYY FineReader XML of UCLA's copy of the Revised and Cheaper Edition
   (Heinemann, 1904; Archive.org mutualaidfactor00kropiala): words with
   ITALIC and SUPERSCRIPT flags, font size and line boxes.
B  djvu XML of Duke's copy of the 1914 impression of the same edition
   (mutualaidfactoro1902krop -- catalogued as 1902, but its verso lists
   the impressions to 1914).
C  djvu XML of a second Duke scan of the 1914 impression (mutualaid01krop),
   noisier; a tie-breaker.

Each scan is split by type size into BODY (12 pt; block quotations 11 pt),
NOTES (9-10 pt, at the foot of the page) and FURNITURE (running heads, page
numbers). The splitting is what makes the vote possible: the print sets
notes at the foot of each page, so a raw OCR stream interleaves note text
with body text at every page break.
"""
import gzip
import html
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_src"

HEAD = re.compile(r"^\S{0,5}\s*(MUTUAL\s+AID[A-Z \-—,.']*|INTRODUCTION|CONCLUSION|APPENDIX|INDEX)\s*\S{0,5}$")


def _tokens_from_line(ln):
    """[(text, italic, sup)] for an ABBYY <line>, split on spaces, a
    token's flags taken from its characters."""
    chars = []
    for attrs, run in re.findall(r"<formatting([^>]*)>(.*?)</formatting>", ln, re.S):
        it = 'italic="true"' in attrs
        sup = 'superscript="true"' in attrs
        for c in re.findall(r"<charParams[^>]*>([^<]*)</charParams>", run):
            c = html.unescape(c)
            chars.append((c if c else " ", it, sup))
    out, cur = [], []
    for c, it, sup in chars + [(" ", False, False)]:
        if c.isspace():
            if cur:
                out.append(cur)
                cur = []
        else:
            cur.append((c, it, sup))
    toks = []
    for w in out:
        # a superscript tail is a note reference: split it off as a MARK
        i = len(w)
        while i > 0 and w[i - 1][2]:
            i -= 1
        body, mark = w[:i], w[i:]
        if body:
            letters = [x for x in body if x[0].isalpha()]
            italic = bool(letters) and sum(x[1] for x in letters) * 2 > len(letters)
            toks.append(("".join(x[0] for x in body), italic, False))
        if mark:
            toks.append(("".join(x[0] for x in mark), False, True))
    return toks


def abbyy():
    """Pages of lines: dict(leaf, box, fs, toks, par)."""
    x = gzip.open(SRC / "ucla_abbyy.gz").read().decode("utf8")
    pages = []
    for leaf, p in enumerate(re.findall(r"<page .*?</page>", x, re.S)):
        lines = []
        for pi, par in enumerate(re.findall(r"<par[^>]*>.*?</par>", p, re.S)):
            for ln in re.findall(r"<line [^>]*>.*?</line>", par, re.S):
                m = re.search(r'l="(\d+)" t="(\d+)" r="(\d+)" b="(\d+)"', ln)
                fs = [float(f) for f in re.findall(r'fs="([\d.]+)"', ln)]
                toks = _tokens_from_line(ln)
                if not toks or not m:
                    continue
                lines.append({"leaf": leaf, "box": tuple(map(int, m.groups())),
                              "fs": max(set(fs), key=fs.count) if fs else 12.0,
                              "toks": toks, "par": pi})
        pages.append(lines)
    return pages


def djvu(name):
    """Pages of lines from a djvu XML: dict(leaf, box, h, toks)."""
    x = (SRC / name).read_text()
    pages = []
    for leaf, page in enumerate(re.findall(r"<OBJECT.*?</OBJECT>", x, re.S)):
        lines = []
        for ln in re.findall(r"<LINE>(.*?)</LINE>", page, re.S):
            ws = re.findall(r'<WORD coords="([^"]*)"[^>]*>(.*?)</WORD>', ln, re.S)
            ws = [(tuple(map(int, c.split(","))), html.unescape(w.strip())) for c, w in ws if w.strip()]
            if not ws:
                continue
            hs = sorted(c[1] - c[3] for c, _ in ws)
            lines.append({"leaf": leaf,
                          "box": (min(c[0] for c, _ in ws), min(c[3] for c, _ in ws),
                                  max(c[2] for c, _ in ws), max(c[1] for c, _ in ws)),
                          "h": hs[len(hs) // 2],
                          "toks": [(w, False, False) for _, w in ws]})
        pages.append(lines)
    return pages


def is_head(line, i):
    """A running head: the page's first line, carrying the book's or the
    section's title and a page number OCR may garble ("TOO MUTUAL AID")."""
    t = " ".join(w for w, *_ in line["toks"])
    if i != 0 or line["box"][1] > 400:
        return False                    # a section heading sits lower on the page
    if HEAD.match(t) or re.fullmatch(r"[\divxlcIl]{1,6}", t.strip()):
        return True
    m = re.search(r"MUTUAL\s*AID|INTRODUCTION|CONCLUSION|APPENDIX", t)
    return bool(m) and len(t) - len(m.group()) <= 10 and t.upper() == t


def split_zones(pages, kind):
    """For each page: (body_lines, note_lines). Furniture dropped. ABBYY
    zones by font size; djvu zones by line height relative to the page's
    body height."""
    out = []
    for lines in pages:
        lines = [l for i, l in enumerate(lines) if not is_head(l, i)]
        # a lone page number at the foot (chapter openings)
        lines = [l for l in lines if not re.fullmatch(r"[\divxlcIl]{1,4}", " ".join(w for w, *_ in l["toks"]).strip())]
        if not lines:
            out.append(([], []))
            continue
        if kind == "abbyy":
            small = [l["fs"] <= 10.5 for l in lines]
        else:
            hs = sorted(l["h"] for l in lines)
            body_h = hs[len(hs) * 2 // 3]
            small = [l["h"] < body_h * 0.86 for l in lines]
        # the notes are the trailing run of small lines at the foot
        k = len(lines)
        while k > 0 and small[k - 1]:
            k -= 1
        # only a run that starts on a note number is a note zone
        if k < len(lines) and not re.match(r"^[\d*†Il]{1,3}$|^[\d*†Il]{1,3}\b", lines[k]["toks"][0][0]) \
                and not (out and out[-1][1]):
            k = len(lines)
        out.append((lines[:k], lines[k:]))
    return out


if __name__ == "__main__":
    A = split_zones(abbyy(), "abbyy")
    B = split_zones(djvu("mutualaidfactoro1902krop_djvu.xml"), "djvu")
    C = split_zones(djvu("mutualaid01krop_djvu.xml"), "djvu")
    for name, Z in (("A", A), ("B", B), ("C", C)):
        nb = sum(len(t) for b, n in Z for l in b for t in l["toks"])
        nn = sum(len(t) for b, n in Z for l in n for t in l["toks"])
        print(name, len(Z), "pages,", nb, "body tokens,", nn, "note tokens")
