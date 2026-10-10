"""Second-witness sweep of the German: Gutenberg #7205 against zeno.org.

    python3 zarathustra/witness.py            # list every disagreement
    python3 zarathustra/witness.py --summary  # counts only

Gutenberg #7205 is an OCR transcription, and prep found three classes of
misreading in it by accident ("8." for every "9.", "verfuhren", "Weit" for
"Welt"). Accident is not a method. zeno.org prints Schlechta's text (Werke
in drei Bänden, 1954, Band 2), an independent transcription in MODERNISED
orthography, so it cannot be a source, but it can VOTE: a word where the
two disagree after the spelling reform is normalised away is a candidate,
read against the crib and fixed in prep.FIXES with a line pin.

The zeno pages are in _src/zeno/ (index.txt maps file -> URL); they are a
witness only and nothing from them is published.

Normalisation folds the 1901 spelling reform (Theil/Teil, gieng/ging,
diess/dies, Noth/Not, -niss/-nis, ß/ss) and case. What survives is either a
real variant between editions or a transcription error in one of them;
the frequent pairs are spelling, the one-offs are what to read.
"""

import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep  # noqa: E402

BOOK = Path(__file__).resolve().parent
ZENO = BOOK / "_src" / "zeno"


def zeno_sections():
    idx = [l.split(" ", 1) for l in (ZENO / "index.txt").read_text().splitlines()]
    out = {}
    for f, url in idx:
        x = (ZENO / f"{f}.html").read_bytes().decode("latin-1")
        m = re.search(r'<div class="zenoCOMain">(.*?)<div class="zenoCOFooter|<div class="zenoCOMain">(.*)', x, re.S)
        body = m.group(1) or m.group(2)
        body = re.sub(r'<a [^>]*class="zenoTXKonk"[^>]*>.*?</a>', " ", body)
        body = re.sub(r"<h\d[^>]*>.*?</h\d>", " ", body, flags=re.S)
        t = unescape(re.sub(r"<[^>]+>", " ", body))
        title = unescape(url.rsplit("/", 1)[1].replace("+", " "))
        from urllib.parse import unquote
        out[unquote(title)] = t
    return out


def norm_tokens(t):
    t = t.lower().replace("ß", "ss").replace("*", "")
    t = t.replace("ſ", "s").replace("’", "").replace("'", "")
    toks = re.findall(r"[a-zäöüé]+", t)
    res = []
    for w in toks:
        w = re.sub(r"th", "t", w)
        w = re.sub(r"ieng", "ing", w)
        w = re.sub(r"ie(?=[bng]t?$)", "i", w) if w in ("giebt", "gieb", "giebst") else w
        w = w.replace("giebt", "gibt").replace("gieb", "gib")
        w = re.sub(r"niss(e|en|es)?$", lambda m: "nis" + (m.group(1) or ""), w)
        w = re.sub(r"ss$", "s", w) if w in ("diess", "dass", "dess") else w
        w = {"diess": "dies", "das": "das", "daß": "dass"}.get(w, w)
        w = w.replace("ss", "s").replace("dt", "t").replace("ee", "e")
        w = w.replace("aa", "a").replace("oo", "o").replace("ä", "e")
        w = w.replace("ck", "k").replace("mm", "m")
        w = {"oh": "o"}.get(w, w)
        res.append(w)
    # fold compound spacing (mit einander / miteinander): join everything
    # and compare as one string per token boundary is overkill; instead drop
    # the space by re-splitting on a fixed list of separable first halves
    out = []
    for w in res:
        if out and out[-1] in JOIN_FIRST and w in JOIN_SECOND:
            out[-1] += w
        else:
            out.append(w)
    return out


JOIN_FIRST = {"mit", "zu", "bei", "ein", "irgend", "zehn", "bei", "an", "in",
              "durch", "hinter", "nach", "von", "aus", "auf", "um", "über",
              "unter", "vor", "für", "gegen", "so", "wie", "zwei", "drei",
              "hundert", "tausend", "aller", "jeder", "manch", "nicht"}
JOIN_SECOND = {"einander", "grunde", "mal", "seite", "ein", "einem", "einen",
               "einer", "eines", "jemand", "etwas", "wo", "wann", "wie", "viel",
               "sehr", "lange", "bald", "weit", "fern", "gleich"}


def gutenberg_sections():
    secs, mottos = prep.german()
    return {s["de"]: s["text"] for s in secs}


def match_title(de, ztitles):
    key = norm_tokens(de)
    for z in ztitles:
        if norm_tokens(z) == key:
            return z
    alias = {"Zarathustra’s Vorrede": "Zarathustras Vorrede",
             "Das Nachtwandler-Lied": "Das trunkne Lied",
             "Von tausend und Einem Ziele": "Von tausend und einem Ziele"}
    return alias.get(de)


def main():
    z = zeno_sections()
    g = gutenberg_sections()
    allpairs = Counter()
    report = []
    for de, gt in g.items():
        zt_title = match_title(de, z)
        assert zt_title in z, (de, zt_title)
        a, b = norm_tokens(gt), norm_tokens(z[zt_title])
        sm = SequenceMatcher(None, a, b, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            ga, zb = " ".join(a[i1:i2]), " ".join(b[j1:j2])
            if len(ga) > 120 or len(zb) > 120:
                ga, zb = ga[:120] + "…", zb[:120] + "…"
            allpairs[(ga, zb)] += 1
            report.append((de, op, ga, zb, " ".join(a[max(0, i1 - 4):i2 + 4])))
    if "--summary" in sys.argv:
        print(len(report), "disagreements;", len(allpairs), "distinct")
        for (ga, zb), n in allpairs.most_common(40):
            print(f"{n:4d}  {ga!r} | {zb!r}")
        return
    for de, op, ga, zb, ctx in report:
        if allpairs[(ga, zb)] <= 2:
            print(f"{de} :: {op} G[{ga}] Z[{zb}]  … {ctx}")


if __name__ == "__main__":
    main()
