"""Fannie Merritt Farmer, The Boston Cooking-School Cook Book: a RESTORED
EDITION.

    python3 farmer/prep.py

Gutenberg #65061, the 1910 edition: Farmer's own revision of the 1896 book
("revised with one hundred and twenty-five new recipes ... and one hundred
half-tone illustrations"), published by Little, Brown five years before
her death. Screened clean -- arch 0.00, 18-word sentences -- an edition,
not a retelling.

Kept: the frontispiece, the Preface, the thirty-eight chapters, every
half-tone and drawing, and Farmer's Glossary. Dropped: the title page, the
Contents and List of Illustrations (the renderers make them), the pages
advertising Miss Farmer's School of Cookery and the publisher's books
(and their images), and the Index.

THE RECIPES ARE LISTS: every ingredient list, composition table and
cooking-time table is a Gutenberg "linegroup", which the walker would run
together into one paragraph ("1 cup flour 1/2 teaspoon salt 2 eggs");
they are turned into set-off blocks, one line a line. Each plate's printed
caption ends with the page of the text it illustrates ("--Page 14."), which
means nothing here and is removed; the plate sits by that text anyway.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 38


def main():
    book = R.Book(HERE, "pg65061-h.zip")
    ads = {n.split("/")[-1]: "an advertisement" for n in book.zip.namelist() if re.search(r"/ad_\w+\.jpg$", n)}
    book.drop.update(ads)
    book.drop["cover.jpg"] = "the transcriber's cover"
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pageno, span.pagenum"):
        sp.decompose()

    # plate captions: the printed caption, without its page reference
    labels = {}
    for fig in soup.select("div.figcenter"):
        img = fig.find("img")
        cap = fig.find("div", class_=re.compile(r"^ic\d"))
        text = ""
        if cap is not None:
            text = R.clean(cap.get_text(" "))
            text = re.sub(r"\s*[—-]+\s*Pages? [\d, and]+\s*\.?(?=\s|$)", "", text)
            text = re.sub(r"\s*\(\s*Pages? [\d, and]+\s*\)", "", text)          # "( Page 314 )"
            text = re.sub(r"\s*Pages? \d+(?: to \d+)?\s*\.?$", "", text)       # "Page 201 ."
            text = re.sub(r"\s+([.,])", r"\1", text).strip()
            assert not re.search(r"\bPages? \d", text), text
            cap.decompose()
        if img is not None:
            labels[img["src"].split("/")[-1]] = text

    # linegroups -> the walker's verse shape, a line a line
    for d in soup.select("div.lg-container-b, div.lg-container-l, div.lg-container-r"):
        d["class"] = ["poetry-container"]
    for g in soup.select("div.group"):
        g["class"] = ["stanza"]
    for ln in soup.select("div.line"):
        m = re.search(r"\bin(\d+)\b", " ".join(ln.get("class")))
        ln["class"] = ["line"] + ([f"indent{min(3, int(m.group(1)) // 4)}"] if m else [])
    # the two definition lists (uses of beverages, etc.): a line an item
    for dl in soup.find_all("dl"):
        div = soup.new_tag("div")
        div["class"] = ["poetry-container"]
        for dt in dl.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            ln = soup.new_tag("div")
            ln["class"] = ["line"]
            ln.string = R.clean(dt.get_text(" ")) + " " + R.clean(dd.get_text(" ") if dd else "")
            div.append(ln)
        dl.replace_with(div)

    # front: from the frontispiece through the Preface; back: the Glossary
    # stays, the School's pages and the Index go
    pref = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "PREFACE")
    front = soup.find("img", src=re.compile("i_frontispiece")).find_parent("div")
    front = front.extract()
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    for title in ("TABLE OF CONTENTS", "LIST OF ILLUSTRATIONS"):
        hh = soup.find(lambda e, t=title: e.name == "h2" and R.clean(e.get_text()) == t)
        node = hh
        while node is not None:
            nxt = node.find_next_sibling()
            if node is not hh and node.name == "h2":
                break
            node.decompose()
            node = nxt
    school = soup.find(lambda e: e.name == "h2" and "SCHOOL OF COOKERY" in R.clean(e.get_text()))
    for el in list(school.find_all_next()):
        el.decompose()
    school.decompose()
    pref.insert_after(front)

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H" and it[1] == 2:
            t = it[2]
            if t == "PREFACE":
                cur = {"title": "Preface", "stream": []}
            elif t == "GLOSSARY":
                cur = {"title": "Glossary", "stream": []}
            else:
                m = re.fullmatch(r"CHAPTER ([IVXL]+) (.+)", t)
                assert m, it
                cur = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2), keep=('ENTRÉES', 'CANAPÉS'))}", "stream": []}
                cur["title"] = cur["title"].replace("ENTRÉES", "Entrées").replace("CANAPÉS", "Canapés")
            sections.append(cur)
            continue
        if it[0] == "H":
            t = it[2]
            cur["stream"].append(("P", R.titlecase(t) if t == t.upper() else t))
            continue
        cur["stream"].append(it)
    assert len(sections) == 2 + CHAPTERS, [s["title"] for s in sections]

    plates = [{"src": it[1], "printed": labels.get(it[1], "")} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    n = R.mend_plate_splits(sections)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, {n} mended, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
