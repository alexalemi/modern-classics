"""Paul de Kruif, Microbe Hunters (1926): a RESTORED EDITION.

    python3 de-kruif/prep.py

Gutenberg #77842, from the Harcourt, Brace first edition of 1926 (in the
US public domain since 1 January 2022). Screened clean -- arch 0.04, calq
7.8 -- so it needs an edition, not a retelling: de Kruif wrote it for the
general reader and it reads like a newspaper, which is what he meant.

Kept: the epigraph (Blakeney) and dedication ("To Rhea"), the twelve
chapters with de Kruif's roman section numbers inside each, the one
footnote, the eight portrait plates and the line drawings. Dropped: the
title page, the Contents and the List of Illustrations (the renderers make
both), the Index (page numbers mean nothing in a reflowable book) and the
publisher's colophon device.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 12


def main():
    book = R.Book(HERE, "pg77842-h.zip", drop={"colophon.jpg": "the publisher's device",
                                              "cover.jpg": "Gutenberg cover"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")

    # the Contents table, with its chapter names, is the witness for the
    # chapter headings; then everything before Chapter I goes except the
    # epigraph and the dedication, which are kept as the front section
    toc = [R.clean(tr.get_text(" ")) for tr in soup.find_all("tr")]
    toc = [re.sub(r"\s+\d+$", "", t) for t in toc if re.match(r"[IVX]+ ", t)]
    assert len(toc) == CHAPTERS, toc
    text = R.clean(soup.get_text(" "))
    epigraph = re.search(r"(“The gods are frankly human.*?Romance\.”) (E\. H\. BLAKENEY\.)", text)
    assert epigraph and "TO RHEA" in text
    first = soup.find("h2", id="CHAPTER_I")
    for el in list(first.find_all_previous()):
        if el.parent is not None and el not in first.parents:
            el.decompose()
    idx = soup.find(lambda e: e.name in ("h2", "h3") and R.clean(e.get_text()) == "INDEX")
    if idx is not None:
        for el in list(idx.find_all_next()):
            el.decompose()
        idx.decompose()
    for sp in soup.select("span.pagenum"):
        sp.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections = [{"title": "Epigraph and Dedication", "stream": [
        ("BLOCK", "\t" + epigraph.group(1) + "\n\t—E. H. Blakeney"),
        ("P", "To Rhea")]}]
    for it in items:
        if it[0] == "H" and it[1] == 2:
            # the heading is three runs (CHAPTER VI / ROUX AND BEHRING /
            # MASSACRE THE GUINEA-PIGS) that flatten into one line with no
            # way to tell where the name ends, so the title comes from the
            # book's own Contents, which prints "ROUX AND BEHRING: Massacre
            # the Guinea-Pigs"
            m = re.fullmatch(r"CHAPTER ([IVX]+) .+", it[2])
            assert m, it[2]
            row = toc[len(sections) - 1]
            num, rest = row.split(" ", 1)
            assert num == m.group(1), (num, it[2])
            name, sub = rest.split(": ", 1)
            name = R.titlecase(name, keep=("VS.",)).replace(" VS. ", " vs. ")
            sections.append({"title": f"{num}. {name}: {sub}", "stream": []})
            continue
        if it[0] == "H":
            raise SystemExit(f"unexpected heading {it}")
        sections[-1]["stream"].append(it)
    ours = [re.sub(r"[^a-z]+", " ", s["title"].lower()).strip() for s in sections[1:]]
    theirs = [re.sub(r"[^a-z]+", " ", t.lower()).strip() for t in toc]
    assert ours == theirs, [(a, b) for a, b in zip(ours, theirs) if a != b]

    # printed labels are the List of Illustrations' ("DR. ROUX"); the Roux
    # plate's figcaption is instead his inscription on the photograph, which
    # goes into its caption as description
    LABEL = {"i_204fp.jpg": "Dr. Roux"}
    plates = [{"src": it[1], "printed": LABEL.get(it[1]) or (R.titlecase(it[2]) if it[2] else "")}
              for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
