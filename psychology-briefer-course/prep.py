"""William James, Psychology: Briefer Course (1892): a RESTORED EDITION.

    python3 psychology-briefer-course/prep.py

Gutenberg #55262, Holt's American Science Series text of 1892. Screened as
clear (arch 0.79, calq 32.3, 26-word sentences): James is the plainest
writer psychology has had, and the book needs an edition, not a retelling.

Structure is the book's own and is checked against its printed Contents:
the Preface, twenty-six chapters and the Epilogue. Dropped: the title
page, the Contents (whose per-chapter topic summaries point at page
numbers) and the Index. The plates are the LARGE images Gutenberg links
from each thumbnail.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 26

# SCAN VOTE: Gutenberg against two Holt printings from the same plates
# (psychology0000jame, 1893; cu31924014062180, 1910), keeping only the
# readings where both agree against the edition. Each was read in
# place. Kept as printed, though they look wrong: "incessently" (both
# scans print it).
TEXT_FIXES = [
    ("measured. Gallon, using", "measured. Galton, using", "both scans"),
    ("No reader of this hook", "No reader of this book", "both scans"),
    ("sense-impression proponderate", "sense-impression preponderate", "both scans"),
    ("The place at which each clears is held", "The place at which each appears is held", "both scans"),
    ("lets its thoughts follow", "lets its thought follow", "both scans"),
    ("raise it bodily up! How it is obvious", "raise it bodily up! Now it is obvious", "both scans"),
    ("by the processes get up.", "by the processes set up.", "both scans"),
    # page references Gutenberg did not link, resolved by hand
    ("(see Fig. 48, p. 117)", "(see Fig. 48, below)", "p. 117 is two paragraphs on, in this chapter"),
    ("A pure sensation we saw above, p. 12, to be", "A pure sensation we saw in Chapter II to be", "p. 12 is Chapter II"),
    ("We have learned in an earlier chapter (p. 72) that", "We have learned in an earlier chapter (Chapter VI) that", "p. 72 is Chapter VI"),
]

# JAMES'S OWN PAGE REFERENCES, 62 of them, are links to page anchors in
# the Gutenberg HTML, so each resolves mechanically: to the chapter the
# page falls in ("on p. 168" -> "in Chapter XI"), or to "above"/"below"
# when it points into the chapter it is written in. A reflowable page has
# no page 168. Galton's "pp. 83-114" is a reference to HIS book that
# Gutenberg linked by mistake, and is kept.
EXTERNAL = {"083"}
ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI".split()


def page_refs(h):
    heads = [(m.start(), m.group(1)) for m in re.finditer(r'<a id="(CHAPTER_[IVXL]+|EPILOGUE|INDEX)"></a>', h)]
    chap_at = lambda pos: max((p, c) for p, c in heads if p <= pos)[1] if pos >= heads[0][0] else None
    anchor = {m.group(1): m.start() for m in re.finditer(r'<a id="page_(\w+)"></a>', h)}
    link = re.compile(r'(pp?\. |p)?<a href="#page_(\w+)" class="pginternal">([^<]*)</a>( ff\.)?')
    n = 0

    def sub(m):
        nonlocal n
        pre, pg = m.group(1) or "", m.group(2)
        here = chap_at(m.start())
        if here in (None, "INDEX") or pg in EXTERNAL:
            return m.group(0)
        n += 1
        # a page that opens on a chapter heading belongs to that chapter
        nxt = min((p for p, c in heads if p > anchor[pg]), default=None)
        there = chap_at(nxt) if nxt is not None and nxt - anchor[pg] < 400 else chap_at(anchor[pg])
        if there == here:
            rel = "above" if anchor[pg] < m.start() else "below"
        else:
            rel = "Epilogue" if there == "EPILOGUE" else "Chapter " + there.split("_")[1]
        return f"\u27e6{rel}\u27e7"
    h = link.sub(sub, h)
    return h, n


REF_RULES = [
    # two pages in one breath
    (r"on pp\. ⟦(Chapter \w+)⟧, ⟦(Chapter \w+)⟧", r"in \1 and \2"),
    (r"\bOn\s*⟦(above|below)⟧", lambda m: m.group(1).capitalize()),
    (r"\bon\s*⟦(above|below)⟧", r"\1"),
    (r"\bOn\s*⟦([^⟧]+)⟧", r"In \1"),
    (r"\bon\s*⟦([^⟧]+)⟧", r"in \1"),
    (r"⟦([^⟧]+)⟧", r"\1"),
    (r"in Chapter (\w+), Chapter (\w+), and elsewhere", r"in Chapters \1 and \2, and elsewhere"),
]


def resolve_refs(sections):
    shown = []
    for s in sections:
        for k, it in enumerate(s["stream"]):
            if it[0] in ("P", "BLOCK") and "⟦" in it[1]:
                t = it[1]
                for pat, rep in REF_RULES:
                    t = re.sub(pat, rep, t)
                s["stream"][k] = (it[0], t) + tuple(it[2:])
                shown += [x.strip() for x in re.split(r"(?<=[.;!?])\s+", t)
                          if re.search(r"\b(Chapter [IVXL]+|Epilogue|above|below)\b", x)]
    # "(pp. 2-13)" runs across the first two chapters
    R.text_fixes(sections, [("can *know* (Chapter I).", "can *know* (Chapters I and II).", "pp. 2-13")])
    assert not any("⟦" in it[1] for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK"))
    return shown


def main():
    zipped = R.Book(HERE, "pg55262-h.zip").zip
    small = [n.split("/")[-1] for n in zipped.namelist() if n.endswith("_sml.png")]
    book = R.Book(HERE, "pg55262-h.zip",
                  drop={"cover.jpg": "Gutenberg cover", **{s: "thumbnail of the _lg plate" for s in small}})
    h = book.html()
    # the thumbnail on the page, the full plate behind its link
    h, n = re.subn(r'src="images/(i_\w+?)_sml\.png"', r'src="images/\1_lg.png"', h)
    assert n == len(small), (n, len(small))
    h, nrefs = page_refs(h)
    assert nrefs == 61, nrefs
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    # the Contents: headings only (each is followed by a topic summary)
    toc_table = next(t for t in soup.find_all("table") if "Introductory" in t.get_text())
    toc = [R.clean(tr.find("td").get_text(" ")) for tr in toc_table.find_all("tr")
           if tr.find("td") and tr.find("td").find(class_="smcap") and tr.find("td", class_="rt")]
    toc_table.decompose()
    first = soup.find("table")
    if "Project Gutenberg" in first.get_text():
        first.decompose()
    # the Index runs to the end of the book, EXCEPT the footnotes, which
    # Gutenberg gathers after it: cut up to them, never past
    idx = soup.find("a", id="INDEX").find_parent("h2")
    notes = soup.find("div", class_="footnotes")
    for n in list(idx.find_all_next()):
        if n is notes or notes in n.parents or n in notes.parents:
            continue
        if n.parent is not None:
            n.extract()
    idx.decompose()
    assert len(notes.select(".footnote")) == 55

    printed = {}
    for fig in soup.select(".figcenter, .figleft, .figright"):
        img = fig.find("img")
        if img is None or "cover" in img["src"]:
            continue
        cap = fig.find(class_="caption")
        printed[img["src"].split("/")[-1]] = R.clean(cap.get_text(" ")) if cap else ""
        if cap:
            cap.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)
    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = re.sub(r"\s*\[\d+\]$", "", it[2])
            m = re.fullmatch(r"CHAPTER ([IVXL]+)\. (.+?)\.", t)
            if m:
                cur = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2))}", "stream": []}
            elif t in ("PREFACE.",):
                cur = {"title": "Preface", "stream": []}
            elif t.startswith("EPILOGUE."):
                cur = {"title": "Epilogue: " + R.titlecase(t.split(". ", 1)[1].rstrip(".")), "stream": []}
            elif it[1] >= 3 and cur is not None:
                cur["stream"].append(("P", t.rstrip(".")))
                continue
            else:
                cur = None
                continue
            sections.append(cur)
            continue
        if cur is not None:
            cur["stream"].append(it)
    assert sum(s["title"].startswith("Chapter") for s in sections) == CHAPTERS
    print(len(toc), toc[:4], toc[-2:])

    plates = [{"src": it[1], "printed": printed.get(it[1], "")} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    # the raw reading: Preface to Index, less the Contents table and the
    # printed "Fig. n." labels, which the walker hands to plates.json
    a, b = body.index('id="PREFACE"'), body.index('id="INDEX"')
    t0 = body.index("<table", body.index('id="CONTENTS"') if 'id="CONTENTS"' in body else a)
    t1 = body.index("</table>", t0)
    raw = R.raw_words(body[a:t0]) + R.raw_words(body[t1:b])
    raw -= sum(len(p["printed"].split()) for p in plates)
    f0 = body.index('<div class="footnotes">')
    raw += R.raw_words(body[f0:]) - 1 - 55        # "FOOTNOTES:" and each "[n]" label
    got = R.words([it for s in sections for it in s["stream"]])
    print(f"raw {raw:,} got {got:,}")
    assert abs(raw - got) <= 0.003 * raw, (raw, got)
    nf = sum(1 for s_ in sections for it in s_["stream"] if it[0] == "P" and it[1].startswith("Footnote: "))
    assert nf == 55, nf
    for s in sections:
        s["stream"] = [it for it in s["stream"] if it[0] != "HR"]
    assert R.mend_plate_splits(sections) == 4
    R.text_fixes(sections, TEXT_FIXES)
    if "--refs" in sys.argv:
        for x in resolve_refs(sections):
            print("REF", x[:200])
    else:
        resolve_refs(sections)
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described")


if __name__ == "__main__":
    main()
