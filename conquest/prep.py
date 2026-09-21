"""Bertrand Russell, The Conquest of Happiness (1930): a RESTORED EDITION.

    python3 conquest/prep.py

Gutenberg #77894, from the London first edition (George Allen & Unwin,
October 1930; this copy is the third impression of December 1930). In the
US public domain since 1 January 2026. Russell wrote it for the general
reader in the plainest English he had, so it needs an edition, not a
retelling.

Kept: the Whitman epigraph, the Preface, the seventeen chapters in their
two Parts, and Russell's four footnotes. Dropped: the list of the author's
other books, the title page, the Contents (the renderers make it), the
Index (page numbers mean nothing in a reflowable book), and the
publisher's device and addresses at the back.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 17


def main():
    book = R.Book(HERE, "pg77894-h.zip", drop={"cover.jpg": "Gutenberg cover",
                                              "i_251.jpg": "the publisher's device"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum"):
        sp.decompose()
    # the rule between chapters is Gutenberg's page furniture, and the
    # walker would set it as a scene break at the foot of every chapter
    for hr in soup.select("hr.chap"):
        hr.decompose()
    assert not soup.find("hr")

    # the Contents is the witness for the chapter titles and for the two
    # Parts, which the body does not head
    toc = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "CONTENTS")
    toc_text = R.clean(toc.find_next("table").get_text(" "))

    # the epigraph: its lines are bare divs, which the walker would run
    # into one line; each becomes a verse line, the signature a line of
    # its own set off with a dash
    ep = soup.find("div", class_="poetry-container")
    assert "live with animals" in ep.get_text()
    lines = [R.clean(d.get_text(" ")) for d in ep.select("div.stanza > div")]
    assert len(lines) == 9 and lines[-1] == "Walt Whitman", lines
    epigraph = "\n".join("\t" + l for l in lines[:-1]) + "\n\t—Walt Whitman"

    pref = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "PREFACE")
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    toc.find_next("table").decompose()
    toc.decompose()
    idx = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "INDEX")
    notes = soup.find(lambda e: e.name == "h2" and "FOOTNOTES" in R.clean(e.get_text()))
    for el in list(idx.find_all_next()):
        if el is notes or notes in el.parents or el in notes.parents:
            break
        el.decompose()
    idx.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections = [{"title": "Epigraph", "stream": [("BLOCK", epigraph)]}]
    # the two Parts are headed in the body by two centred lines ("PART I" /
    # "CAUSES OF UNHAPPINESS"); they become dividers, in word form, since a
    # roman "Part I:" line is what assemble.strip_front deletes
    part, parts = None, []
    for it in items:
        if it[0] == "P" and re.fullmatch(r"PART (I|II)", it[1]):
            part = {"I": "One", "II": "Two"}[it[1][5:]]
            continue
        if part and it[0] == "P" and part not in parts:
            assert it[1] in ("CAUSES OF UNHAPPINESS", "CAUSES OF HAPPINESS"), it
            parts.append(part)
            part = f"Part {part}: {R.titlecase(it[1])}"
            continue
        if it[0] == "H" and it[1] == 2:
            t = it[2]
            if t == "PREFACE":
                sections.append({"title": "Preface", "stream": []})
                continue
            m = re.fullmatch(r"CHAPTER ([IVX]+) (.+)", t)
            assert m, it
            sec = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2))}", "stream": []}
            if part:
                sec["part_before"], part = part, None
            sections.append(sec)
            continue
        if it[0] == "H":
            raise SystemExit(f"unexpected heading {it}")
        sections[-1]["stream"].append(it)
    chapters = sections[2:]
    assert len(chapters) == CHAPTERS, [s["title"] for s in sections]
    assert [s.get("part_before") for s in chapters if s.get("part_before")] == \
        ["Part One: Causes of Unhappiness", "Part Two: Causes of Happiness"]
    # the chapter titles against the Contents' own
    for s in chapters:
        assert s["title"].split(": ", 1)[1].upper() in toc_text, s["title"]
    R.all_images_placed(book, [])
    rows, described = R.compose(book, sections, plates=[], captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
