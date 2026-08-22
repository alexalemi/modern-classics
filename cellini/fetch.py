"""Pull the Italian Vita from it.wikisource into _italian.json.

The seneca/galileo MediaWiki-API pattern. Run once, with network access;
prep.py then works entirely offline from the cached JSON, so the source
cannot move under a later re-run.

Wikisource holds one page per chapter: 128 in Libro primo, 113 in Libro
secondo, plus a Proemio. Symonds's English has 127 + 113, and that ONE
CHAPTER OF DIFFERENCE is a real alignment defect, not a rounding error;
prep.py locates it rather than assuming it away.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

BOOK = pathlib.Path(__file__).resolve().parent
BASE = ("La vita di Benvenuto di Maestro Giovanni Cellini fiorentino, "
        "scritta, per lui medesimo, in Firenze")
UA = {"User-Agent": "modern-classics/1.0 (contact: alexalemi@gmail.com)"}


def api(**kw):
    kw.setdefault("format", "json")
    url = "https://it.wikisource.org/w/api.php?" + urllib.parse.urlencode(kw)
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"wikisource api failed: {kw}")


ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman(s):
    n = 0
    for i, c in enumerate(s):
        v = ROMAN[c]
        n += -v if i + 1 < len(s) and v < ROMAN[s[i + 1]] else v
    return n


def all_titles():
    out, cont = [], {}
    while True:
        d = api(action="query", list="allpages", apprefix=BASE + "/",
                aplimit="500", **cont)
        out += [p["title"] for p in d["query"]["allpages"]]
        if "continue" in d:
            cont = d["continue"]
        else:
            return out


def fetch(titles):
    """Raw wikitext, fifty pages at a time."""
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = api(action="query", prop="revisions", rvprop="content",
                rvslots="main", titles="|".join(batch))
        for p in d["query"]["pages"].values():
            if "revisions" not in p:
                raise RuntimeError(f"no revision for {p.get('title')!r}")
            out[p["title"]] = p["revisions"][0]["slots"]["main"]["*"]
        print(f"  {min(i + 50, len(titles))}/{len(titles)}")
    return out


def main():
    titles = all_titles()
    want = []
    for book, label in ((1, "Libro primo"), (2, "Libro secondo")):
        got = sorted(
            ((roman(t.rsplit(" ", 1)[1]), t) for t in titles
             if f"/{label}/Capitolo " in t))
        nums = [n for n, _ in got]
        if nums != list(range(1, len(nums) + 1)):
            raise SystemExit(f"{label}: chapter numbers are not 1..n: {nums}")
        want += [(book, n, t) for n, t in got]
    print(f"{len(want)} chapters")
    raw = fetch([t for _, _, t in want])
    data = [{"book": b, "chapter": n, "title": t, "wikitext": raw[t]}
            for b, n, t in want]
    (BOOK / "_italian.json").write_text(json.dumps(data, ensure_ascii=False))
    print(f"wrote _italian.json ({sum(len(d['wikitext']) for d in data)} chars)")


if __name__ == "__main__":
    main()
