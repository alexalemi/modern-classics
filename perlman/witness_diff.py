"""Word diff of the Anarchist Library transcription against the scan's OCR.

    python3 perlman/witness_diff.py            # the list, for READING
    python3 perlman/witness_diff.py --json     # also writes _src/witness_diff.json

The two witnesses share no keystrokes: TAL's text came from a 2007 blog
transcription, the OCR from Archive.org's scan of Black & Red's 2010 third
printing (AgainstHistoryAgainstLeviathanByFredyPerlman). Where they differ,
the page image decides; this script only finds the places to look.
Each difference is reported with the scan leaf (from the djvu XML word
order) so the page can be opened directly.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from scan_diff import opcodes  # noqa: E402


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.lower()


def tal_words():
    t = (HERE / "_src/tal.muse").read_text()
    t = re.sub(r"^#.*$", " ", t, flags=re.M)
    t = re.sub(r"^\*\* \d+\s*$", " ", t, flags=re.M)      # chapter numbers
    t = re.sub(r"<[^>]+>", " ", t)
    return re.findall(r"[a-z]+", norm(t).replace("’", "").replace("'", ""))


def scan_words():
    """(word, leaf) from the djvu XML, which keeps each word's leaf."""
    x = (HERE / "_src/djvu.xml").read_text()
    out = []
    for leaf, page in enumerate(re.findall(r"<OBJECT.*?</OBJECT>", x, re.S)):
        lines = re.findall(r"<LINE>(.*?)</LINE>", page, re.S)
        text = []
        for ln in lines:
            ws = re.findall(r"<WORD[^>]*>(.*?)</WORD>", ln, re.S)
            text.append(" ".join(ws))
        # drop a bare page number or chapter number line
        text = [l for l in text if not re.fullmatch(r"\s*[\dIl]{1,3}\.?\s*", l)]
        body = "\n".join(text)
        body = re.sub(r"[¬\-]\s*\n\s*", "", body)        # line-end splits
        body = body.replace("&amp;", "&").replace("&apos;", "'").replace("&quot;", '"')
        for w in re.findall(r"[a-z]+", norm(body).replace("’", "").replace("'", "")):
            out.append((w, leaf))
    return out


def main():
    ew = tal_words()
    sl = scan_words()
    sw = [w for w, _ in sl]
    diffs = []
    for tag, i1, i2, j1, j2 in opcodes(ew, sw):
        if tag == "equal":
            continue
        a, b = " ".join(ew[i1:i2]), " ".join(sw[j1:j2])
        if a.replace(" ", "") == b.replace(" ", ""):
            continue                          # a split or joined word only
        leaf = sl[min(j1, len(sl) - 1)][1]
        ctx = " ".join(ew[max(0, i1 - 5):i1]) + " [" + a + "] " + " ".join(ew[i2:i2 + 5])
        diffs.append({"tag": tag, "tal": a, "scan": b, "leaf": leaf, "ctx": ctx})
    for d in diffs:
        print(f"{d['leaf']:3d} {d['tag'][:3]}  TAL={d['tal'][:60]!r:40}  SCAN={d['scan'][:60]!r:40}  ...{d['ctx'][:110]}")
    print(len(ew), "TAL words,", len(sw), "scan words,", len(diffs), "differences")
    if "--json" in sys.argv:
        (HERE / "_src/witness_diff.json").write_text(json.dumps(diffs, indent=1))


if __name__ == "__main__":
    main()


def plain_words(path, start="darkling plain is here"):
    t = (HERE / path).read_text()
    i = norm(t).find(start)
    t = t[max(0, i - 2000):]
    lines = [l for l in t.split("\n") if not re.fullmatch(r"\s*[\dIl|]{1,3}\.?\s*", l)]
    t = re.sub(r"[¬\-—]\s*\n\s*", "", "\n".join(lines))
    return re.findall(r"[a-z]+", norm(t).replace("’", "").replace("'", ""))


def agreed():
    """Corrections both OCRs make to TAL identically: {(i1, i2): words}."""
    ew = tal_words()
    a = [w for w, _ in scan_words()]
    b = plain_words("_src/ocrB.txt")
    oa = {(i1, i2): " ".join(a[j1:j2]) for t, i1, i2, j1, j2 in opcodes(ew, a) if t != "equal"}
    ob = {(i1, i2): " ".join(b[j1:j2]) for t, i1, i2, j1, j2 in opcodes(ew, b) if t != "equal"}
    return ew, {k: v for k, v in oa.items() if ob.get(k) == v and v.replace(" ", "") != " ".join(ew[k[0]:k[1]]).replace(" ", "")}
