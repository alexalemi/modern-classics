"""Professor Hoffmann (Angelo Lewis), Modern Magic: a RESTORED EDITION.

    python3 hoffmann/prep.py

Gutenberg #58057, from Routledge's American edition of Modern Magic
(first published in London, 1876), with its appendix "Ancient and Modern
Magic" by Arprey Vere, explaining the specialties of Maskelyne and Cooke at
the Egyptian Hall. Screened clean -- arch 0.01 -- an edition, not a
retelling.

Kept: the frontispiece, the eighteen chapters, the appendix's eight
chapters (under a divider of their own), and every illustration, the
decorative head- and tailpieces included (CAPTIONS.md: they get a
description that stands alone). Dropped: the title page and the
publisher's list, the Contents (the renderers make it), the advertisements
at the back and the transcriber's notes.

TWO OF GUTENBERG'S CHANGES ARE REVERSED:
  - It renumbered the appendix's Figs. 1-4 as 321-324 "to avoid ambiguity";
    the print numbers them 1-4 and so does this edition, labels and text.
  - It "made spelling and punctuation consistent where a predominant
    preference was found". Where two scans of the printing agree against
    it, the print is followed. The vote (two printings, 1877 and 1885)
    found one wording only, "thus much"; the rest was OCR noise.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 18
APPENDIX_CHAPTERS = 8


def main():
    book = R.Book(HERE, "pg58057-h.zip", drop={"cover.jpg": "Gutenberg cover",
                                                "i_000b.jpg": "the title page's ornament",
                                                "i_001.jpg": "the half-title's headpiece"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum, span.pageno"):
        sp.decompose()

    # the drop-cap image is an ornamental initial whose letter is also in
    # the text; it goes, as the renderers set no initials
    for img in soup.find_all("img", class_="drop-cap"):
        book.drop[img["src"].split("/")[-1]] = "an ornamental initial"
        img.decompose()

    # FOUR ROWS OF CARDS use "*" for an indifferent card ("... 1, 0, *, *,
    # *, *,--"); the walker's emphasis cleaning deletes a stray asterisk, so
    # those rows came out as bare commas. They are set as the book's other
    # asterisks are in this project, a low asterisk.
    rows = soup.find_all(string=re.compile(r"(?:^|, )\*(?:,|\.)"))
    assert len(rows) == 4, len(rows)
    for t in rows:
        t.replace_with(re.sub(r"(?<![\w*])\*(?![\w*])", "\u204e", str(t)))

    # printed labels: the caption div ("Fig. 24. Fig. 25.")
    labels = {}
    for d in soup.select("div.figcenter, div.figleft, div.figright"):
        img = d.find("img")
        cap = d.find(class_="caption")
        if img is None:
            continue
        text = R.clean(cap.get_text(" ")) if cap is not None else ""
        # undo the renumbering of the appendix's four figures
        text = re.sub(r"\b32([1-4])\b", r"\1", text) if re.search(r"\b32[1-4]\b", text) else text
        # three figures are drawn inside the image above them and carry
        # their number there, not in a caption: the label names both
        for a, b in (("Fig. 99.", "Fig. 100."), ("Fig. 103.", "Fig. 104."), ("Fig. 112.", "Fig. 113.")):
            if text == a:
                text = f"{a} {b}"
        labels[img["src"].split("/")[-1]] = text
        if cap is not None:
            cap.decompose()
    for a in soup.find_all(string=re.compile(r"\b32[1-4]\b")):
        a.replace_with(re.sub(r"\b32([1-4])\b", r"\1", str(a)))

    # front: keep the frontispiece; drop from it to the first chapter
    front = soup.find("img", src=re.compile(r"i_000\.jpg")).find_parent("div").extract()
    first = soup.find("h2", id="CHAPTER_I")
    for el in list(first.find_all_previous()):
        if el.parent is not None and el not in first.parents:
            el.decompose()
    first.insert_after(front)
    ads = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "ADVERTISEMENTS")
    for img in ads.find_all_next("img"):
        book.drop[img["src"].split("/")[-1]] = "the publisher's advertisements"
    for el in list(ads.find_all_next()):
        el.decompose()
    ads.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, part, in_app = [], None, None, False
    for it in items:
        if it[0] == "H" and it[1] == 2:
            t = it[2]
            if t.startswith("APPENDIX"):
                in_app = True
                continue
            if t.startswith("ANCIENT AND MODERN MAGIC"):
                part = "Appendix: Ancient and Modern Magic, by Arprey Vere"
                continue
            if t.startswith("MODERN MAGIC"):
                continue
            m = re.fullmatch(r"CHAPTER ([IVX]+)\. (.+?)\.?", t)
            assert m, it
            cur = {"title": f"{'Appendix ' if in_app else ''}Chapter {m.group(1)}: {m.group(2)}", "stream": []}
            if part:
                cur["part_before"], part = part, None
            if in_app:
                cur["chapter"] = True
            sections.append(cur)
            continue
        if it[0] == "H":
            t = it[2]
            cur["stream"].append(("P", R.titlecase(t) if t == t.upper() else t))
            continue
        cur["stream"].append(it)
    nmain = sum(1 for s in sections if not s["title"].startswith("Appendix"))
    assert nmain == CHAPTERS and len(sections) == CHAPTERS + APPENDIX_CHAPTERS, [s["title"] for s in sections]

    plates = [{"src": it[1], "printed": labels.get(it[1], "")} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    n = R.mend_plate_splits(sections)
    # scan vote (scan_diff.py --vote) against modernmagicpract00hoff_0 (1885)
    # and modernmagic00hoffgoog (1877): one wording both print
    R.text_fixes(sections, [("Having achieved this much", "Having achieved thus much", "both printings")])
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, {n} mended, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
