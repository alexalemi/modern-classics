"""Ebenezer Howard, Garden Cities of To-morrow (1902): a RESTORED EDITION.

    python3 howard/prep.py

Gutenberg #46134, from Swan Sonnenschein's 1902 second edition of
"To-morrow: a Peaceful Path to Real Reform" (1898), renamed. Screened
clean -- arch 0.49 -- an edition, not a retelling.

Kept: the frontispiece portrait, the Lowell epigraph, the Introduction,
the thirteen chapters with their tables of estimated revenue and
expenditure, Howard's footnotes, the five numbered diagrams (taken from
Gutenberg's high-resolution copies) and the Postscript. Dropped: the
title page and publisher's device, the Contents and List of
Illustrations (the renderers make both), the Index, and the Garden City
Association's list of officers and membership terms bound in after it.

THE DIAGRAMS ARE THE ARGUMENT -- the Three Magnets above all -- and they
are full of words: every magnet, ward and railway is lettered. Their
captions (captions/) therefore transcribe the lettering, so that a
reader who cannot see the diagram can read it.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 13
PLATES = ["ill_002b.jpg", "ill_016a.png", "ill_022a.png", "ill_022c.png", "ill_128a4.png", "ill_128a5.png"]


def main():
    zp = HERE / "_src" / "pg"
    book = R.Book(HERE, "pg46134-h.zip",
                  drop={"cover.jpg": "Gutenberg cover", "covers.jpg": "Gutenberg cover",
                        "ill_003.png": "the publisher's device on the title page",
                        **{p.replace(".", "h."): "the high-resolution copy, used in place of the plate"
                           for p in PLATES}},
                  replace={p: str(zp / "images" / p.replace(".", "h.")) for p in PLATES})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum"):
        sp.decompose()

    # labels ("No. 1 The Three Magnets") live in the alt text
    labels = {}
    for img in soup.find_all("img"):
        src = img["src"].split("/")[-1]
        labels[src] = R.clean(img.get("alt") or "")
    labels["ill_002b.jpg"] = "Ebenezer Howard"          # alt is his signature

    # front: keep the portrait and the epigraph, then from INTRODUCTION on
    portrait = soup.find("img", src=re.compile("ill_002b")).find_parent("div")
    epigraph = soup.find("div", class_="poem")
    intro = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()).startswith("INTRODUCTION"))
    keep = [portrait.extract(), epigraph.find_parent("div", class_="center") or epigraph]
    keep = [k.extract() if k.parent else k for k in keep]
    for el in list(intro.find_all_previous()):
        if el.parent is not None and el not in intro.parents:
            el.decompose()
    for k in keep:
        intro.insert_before(k)
    front_h = soup.new_tag("h2")
    front_h.string = "FRONTISPIECE"
    keep[0].insert_before(front_h)

    # back: drop the Index and the Association's pages, keep the Postscript
    idx = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "INDEX")
    post = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()).startswith("POSTSCRIPT"))
    assoc = soup.find(lambda e: e.name in ("h2", "h3") and "GARDEN CITY ASSOCIATION" in R.clean(e.get_text()))
    notes = soup.find(lambda e: e.name in ("h2", "h3") and R.clean(e.get_text()) == "FOOTNOTES")
    node = idx
    while node is not None and node is not post:
        nxt = node.find_next_sibling()
        node.decompose()
        node = nxt
    node = assoc
    # the notes heading sits inside a div, not beside the Association's
    # pages: stop at whatever element holds it
    while node is not None and node is not notes and notes not in node.descendants:
        nxt = node.find_next_sibling()
        node.decompose()
        node = nxt
    for el in list(soup.find_all(lambda e: e.name == "h2" and "Transcriber" in e.get_text())):
        for x in list(el.find_all_next()):
            x.decompose()
        el.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H" and it[1] == 2:
            t = it[2]
            if t == "FRONTISPIECE":
                cur = {"title": "Frontispiece and Epigraph", "stream": []}
            elif t.startswith("INTRODUCTION"):
                cur = {"title": "Introduction", "stream": []}
            elif t.startswith("POSTSCRIPT"):
                cur = {"title": "Postscript", "stream": []}
            elif t == "FOOTNOTES":
                continue
            else:
                m = re.fullmatch(r"CHAPTER ([IVX]+)\. (.+?)\.?", t)
                assert m, it
                # each dash-separated piece is a title of its own
                t2 = "—".join(R.titlecase(x) for x in m.group(2).split("—"))
                cur = {"title": f"Chapter {m.group(1)}: {t2}", "stream": []}
            sections.append(cur)
            continue
        if it[0] == "H":
            t = it[2].rstrip(".")
            cur["stream"].append(("P", R.titlecase(t) if t.isupper() else t))
            continue
        cur["stream"].append(it)
    assert len(sections) == 3 + CHAPTERS, [s["title"] for s in sections]
    for s in sections:                   # rules closing a section are furniture
        while s["stream"] and s["stream"][-1][0] == "HR":
            s["stream"].pop()

    plates = [{"src": it[1], "printed": labels[it[1]]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert [p["src"] for p in plates] == PLATES, [p["src"] for p in plates]
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")
    print([s["title"] for s in sections])


if __name__ == "__main__":
    main()
