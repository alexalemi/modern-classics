"""Henry Dunant, Un souvenir de Solférino (Geneva: Jules-Guillaume Fick,
1862), the first edition, from French Wikisource (proofread 100% against the
scan, "Dunant - Un souvenir de Solférino, 1862.djvu", pp. 4-118).

    python3 books/solferino/prep.py            # from source/wikisource.html
    python3 books/solferino/prep.py --fetch    # refetch it first

source/wikisource.html is the rendered page (action=render). This script
turns it into source/solferino.txt -- paragraphs, the author's 31 footnotes
numbered [n] in the text and set as "NOTE n: ..." paragraphs directly after
the paragraph that cites them -- and then cuts that into chapters/.

The book has no divisions of its own. It is cut at the natural joints of
the narrative and the argument (see BREAKS) into seven files, each opening
on the paragraph named there; the headings are ours, also in BREAKS. The
division ruling is in text_analysis.txt.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "source"
URL = ("https://fr.wikisource.org/w/index.php?title="
       "Un_souvenir_de_Solf%C3%A9rino&action=render")

# (opening words of the first paragraph of each file, manifest title)
BREAKS = [
    ("La sanglante victoire de Magenta", "The Battle"),
    ("Les troupes de l’empereur François-Joseph se sont repliées",
     "The Night and the Morning After"),
    ("Depuis Castiglione les blessés devaient être conduits", "Castiglione"),
    ("Les rues de Castiglione sont plus calmes", "The Road to Brescia"),
    ("Dans les vastes salles des hôpitaux", "The Hospitals of Brescia"),
    ("Le transport des blessés, de Brescia à Milan", "Milan"),
    ("Mais pourquoi avoir raconté", "A Proposal"),
]


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "modern-classics prep"})
    (SRC / "wikisource.html").write_bytes(urllib.request.urlopen(req).read())


def clean(t):
    t = " ".join(t.split())
    t = re.sub(r"\s+\[(\d+)\]", r"[\1]", t)
    t = t.replace("M me ", "Mme ").replace("S t . ", "St. ")
    t = re.sub(r"\b(\d+) (e|er|re|me)\b", r"\1\2", t)   # superscript ordinals
    return re.sub(r"(\[\d+\]) ([,.;:])", r"\1\2", t)


def to_text():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup((SRC / "wikisource.html").read_text(), "html.parser")
    for x in soup.select(".ws-noexport, .pagenum, .ws-pagenum, style, script"):
        x.decompose()
    notes = {}
    refs = soup.select_one("ol.references")
    for i, li in enumerate(refs.find_all("li", recursive=False), 1):
        for b in li.select(".mw-cite-backlink"):
            b.decompose()
        notes[i] = clean(li.get_text(" "))
    refs.decompose()
    for sup in soup.select("sup.reference"):
        n = re.sub(r"\D", "", sup.get_text())
        sup.replace_with(f"[{n}]")
    out = []
    for el in soup.find_all(["p", "div", "li", "h1", "h2", "h3"]):
        if el.find(["p", "div"]):
            continue
        t = clean(el.get_text(" "))
        if not t or t in ("UN SOUVENIR", "DE", "SOLFERINO"):
            continue
        out.append(t)
        for n in re.findall(r"\[(\d+)\]", t):
            out.append(f"NOTE {n}: {notes.pop(int(n))}")
    assert not notes, f"uncited notes {sorted(notes)}"
    return out


def main():
    if "--fetch" in sys.argv:
        fetch()
    pars = to_text()
    (SRC / "solferino.txt").write_text("\n\n".join(pars) + "\n")
    starts = []
    for opening, _ in BREAKS:
        hits = [i for i, p in enumerate(pars) if p.startswith(opening)]
        assert len(hits) == 1, (opening, hits)
        starts.append(hits[0])
    assert starts == sorted(starts) and starts[0] == 0
    starts.append(len(pars))
    (HERE / "chapters").mkdir(exist_ok=True)
    manifest = []
    for j, (_, title) in enumerate(BREAKS):
        body = "\n\n".join(pars[starts[j]:starts[j + 1]])
        fn = f"{j:03d}.txt"
        (HERE / "chapters" / fn).write_text(f"{title}\n\n{body}\n")
        manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                         "words": len(body.split())})
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print([(m["title"], m["words"]) for m in manifest])


if __name__ == "__main__":
    main()
