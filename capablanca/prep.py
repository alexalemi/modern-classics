"""José Raúl Capablanca, Chess Fundamentals (1921): a RESTORED EDITION.

    python3 capablanca/prep.py

Gutenberg #33870, the Harcourt, Brace text of 1921 in a later printing that
carries Capablanca's preface of 1934 ("there is nothing to be added and
nothing to be changed"). Both Archive.org scans (cu31924014756724,
chessfundamental00capa) are that same state; the 1934 preface was not
renewed (NYPL cce-renewals, 1960-63 checked), so it is kept as his.
Screened clean -- arch 0.04, sentences of 14 words -- an edition, not a
retelling. The notation is the English descriptive notation of 1921 and it
stays as printed: it IS the text.

WHAT THE EDITION ADDS is what a reader who cannot see the board never had:
every one of the 150 diagrams gets a caption naming the position square by
square, in algebraic co-ordinates (captions/, written from the plates and
checked against the moves the text plays from them -- replayed with
python-chess from game score to diagram, and each diagram's next moves
tested for legality). No caption says whose move it is: the text does, and
the captioners' inferences disagreed about when to say it. One diagram
(ar, Example 17) prints White's queen on d1 dark; the caption gives the
position the moves require and says how the square is printed.

LAYOUT DECISIONS
  - Part I's thirty-three numbered sections are headings inside their
    chapters; Part II's fourteen games are sections of their own under the
    Part II divider.
  - A move table (empty cell | White | Black) becomes a set-off block, one
    move a line, the two sides separated by an em space. Centred move lines
    in the prose are set off the same way.
  - Capablanca's six page references are rewritten as section or game
    references (PAGE_REFS), because a reflowable book has no pages.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

DIAGRAMS = 150     # and the frontispiece portrait
GAMES = 14
SECTIONS = 33

# (text around the reference, replacement): a page is where a section began
# in the printed book, from the Contents
PAGE_REFS = [
    ("game at San Sebastian, page 197.)", "game at San Sebastian, Game 7.)"),
    ("(see pages 48-56, where", "(see section 14, where"),
    ("explained in section 20, p. 77.", "explained in section 20."),
    ("See page 37.", "See section 10."),
    ("See page 13.", "See section 3."),
    ("under Example 50 (p. 80.).", "under Example 50."),
]
SEP = "  "          # between White's move and Black's


def main():
    book = R.Book(HERE, "pg33870-h.zip", drop={"33870-cover.png": "Gutenberg cover"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum"):
        sp.decompose()

    # the Preface is kept; the title page and the List of Contents go
    pref = soup.find(lambda e: e.name in ("h2", "h3") and R.clean(e.get_text()) == "PREFACE")
    start = soup.find("h2", string="CHESS FUNDAMENTALS")
    kill, el = [], pref.find_previous()
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    toc_h = soup.find(lambda e: e.name in ("h2", "h3") and "LIST OF CONTENTS" in R.clean(e.get_text()))
    toc_rows = [R.clean(tr.get_text(" ")) for tr in soup.find_all("tr") if tr.find_parent("table") and tr.find_parent("table").find_previous(lambda e: e is toc_h) is not None]
    node = toc_h
    while node is not None and node is not start:
        nxt = node.find_next_sibling()
        node.decompose()
        node = nxt
    start.decompose()

    # notes: rename to the walker's pattern (fn / footnotes)
    for d in soup.select("div.note"):
        d["class"] = ["footnotes"]
        for a in d.find_all("a", id=re.compile(r"^Nt\d+$")):
            a["id"] = "fn" + a["id"][2:]
    for d in soup.find_all(lambda e: e.name == "h3" and R.clean(e.get_text()) == "Notes"):
        d.decompose()
    for a in soup.find_all("a", href=re.compile(r"^#Nt\d+$")):
        a["href"] = "#fn" + a["href"][3:]

    # move tables -> set-off blocks
    for t in soup.select("table.nobctr"):
        lines = []
        for tr in t.find_all("tr"):
            cells = [R.clean(td.get_text(" ")) for td in tr.find_all("td")]
            cells = [c for c in cells if c]
            lines.append(SEP.join(cells))
        div = soup.new_tag("div")
        div["class"] = ["poetry"]
        for ln in lines:
            ld = soup.new_tag("div")
            ld["class"] = ["line"]
            ld.string = ln
            div.append(ld)
        t.replace_with(div)

    # centred lines: chapter titles, section titles, game heads, move lines
    for p in soup.select("p.cenhead"):
        t = R.clean(p.get_text(" "))
        m = re.match(r"(\d+)\. ([A-Z][A-Z\"'.,: \-]+(?: v\. [A-Z ,]+)?[A-Z\"])$", t)
        if m or re.match(r"GAME \d+\.", t):
            p.name = "h4"
            # the number and the title are cased apart, or "9. A CARDINAL
            # PRINCIPLE" comes out "9. a Cardinal Principle"
            p.string = f"{m.group(1)}. {R.titlecase(m.group(2), keep=('v.',))}" if m else t
        elif p.find(class_="sc") is not None:
            p.name = "h5"                     # a chapter's own title
        elif re.match(r"\d+\.", t):
            div = soup.new_tag("div")
            div["class"] = ["poetry"]
            ld = soup.new_tag("div")
            ld["class"] = ["line"]
            ld.string = t
            div.append(ld)
            p.replace_with(div)

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, part = [], None, None
    for it in items:
        if it[0] == "H":
            t = it[2]
            if t == "PREFACE":
                # the frontispiece portrait stood before the title page,
                # which is dropped; it opens the Preface instead
                cur = {"title": "Preface", "stream": [("PLATE", "frontis.jpg", "José R. Capablanca")]}
                sections.append(cur)
                continue
            if re.fullmatch(r"PART (I+)", t):
                part = "Part " + {"I": "One", "II": "Two"}[t.split()[1]]
                continue
            if re.fullmatch(r"CHAPTER [IVX]+", t):
                cur = {"title": t.title().replace("Chapter ", "Chapter "), "stream": [], "chapter": True,
                       "roman": t.split()[1]}
                if part:
                    cur["part_before"], part = part, None
                sections.append(cur)
                continue
            if it[1] == 5 and cur.get("roman") and ":" not in cur["title"]:
                cur["title"] = f"Chapter {cur['roman']}: {t}"
                continue
            m = re.fullmatch(r"GAME (\d+)\. (.+)", t)
            if m:
                cur = {"title": f"Game {m.group(1)}: {R.titlecase(m.group(2))}", "stream": [], "chapter": True}
                if part:
                    cur["part_before"], part = part, None
                sections.append(cur)
                continue
            if it[1] == 4:
                cur["stream"].append(("P", t))
                continue
            raise SystemExit(f"unexpected heading {it}")
        cur["stream"].append(it)
    for s in sections:
        s.pop("roman", None)

    titles = [s["title"] for s in sections]
    assert titles[0] == "Preface" and len(titles) == 1 + 6 + GAMES, titles
    heads = [int(it[1].split(".")[0]) for s in sections for it in s["stream"]
             if it[0] == "P" and re.fullmatch(r"\d+\. [A-Z].*[^.]", it[1]) and it[1] == it[1].split(".")[0] + ". " + R.titlecase(it[1].split(". ", 1)[1], keep=("v.",))]
    assert heads == list(range(1, SECTIONS + 1)), heads
    R.text_fixes(sections, [(a, b, "page reference -> section") for a, b in PAGE_REFS])

    plates = [{"src": it[1], "printed": it[2]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert len(plates) == DIAGRAMS + 1, len(plates)
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} diagrams, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
