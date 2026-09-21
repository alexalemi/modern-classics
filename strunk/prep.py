"""William Strunk Jr., The Elements of Style (1920): a RESTORED EDITION.

    python3 strunk/prep.py

Gutenberg #37134, transcribed by Distributed Proofreaders from the Harcourt,
Brace and Howe edition of 1920 (Archive.org cu31924014450716, Cornell's
copy, which is the scan it was made from). That is the book's first trade
publication; Strunk had printed it privately for his Cornell classes in 1918
and 1919, and both copyrights are on its verso. It is Strunk's text alone,
before E. B. White's revisions of 1959 and after, which are in copyright.

WHAT THE EDITION DOES WITH STRUNK'S LAYOUT, and why each is needed:
  - THE PAIRED EXAMPLES. Strunk sets a faulty sentence and its correction
    side by side, the fault on the left. A reflowable page has no columns,
    so each pair becomes a two-line block, the fault first and the
    correction under it: reading order is kept, and it is the order White's
    later editions use.
  - THE INDENTED EXAMPLES (div.example) are set as indented blocks, one
    sentence a line, as printed -- except the numbered Exercises of
    Chapter VII, which are paragraphs, one exercise each.
  - THE RULES are the book's real sections ("The numbers of the sections
    may be used as references in correcting manuscript"), so each of the
    eighteen is a section nested under its chapter, which becomes a part
    divider. Chapters without rules stay single sections.
  - BOLD run-in heads (the entries of Chapters IV and V) become italic: the
    renderers have emphasis and nothing heavier.
  - The spelling list is one block, a word a line.
Gutenberg's nine transcriber's corrections are all plain misprints and are
kept (the restored-editions rule), including "embarrass" in, of all places,
the list of words often misspelled.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

RULES = 18
EXAMPLE_PAIRS = 111     # counted in the source: td.first cells


def main():
    book = R.Book(HERE, "pg37134-h.zip", drop={"logo.png": "Harcourt's device on the title page",
                                              "title-page.jpg": "Gutenberg cover"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")

    # front matter: the transcriber's notes, the title page and the Contents
    # all go; the book begins at "I. INTRODUCTORY"
    toc = soup.find(lambda e: e.name == "h2" and "CONTENTS" in e.get_text())
    table = toc.find_next("table")
    toc_rows = [R.clean(tr.get_text(" ")) for tr in table.find_all("tr")]
    start = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "I. INTRODUCTORY")
    for el in list(start.find_all_previous()):
        if el.parent is not None and el not in start.parents:
            el.decompose()
    tn = soup.find("a", id="tn-bottom")
    if tn:
        tp = tn.find_parent("p")
        for el in list(tp.find_next_siblings()):
            el.decompose()
        tp.decompose()

    for b in soup.find_all(["b", "strong"]):
        b.name = "i"
    for ins in soup.find_all("ins"):
        ins.unwrap()

    # paired examples: fault above, correction below
    pairs = 0
    # (one block per PAIR: a table of several rows stacked into one block
    # would read fault, correction, fault, correction with nothing to say
    # which is which; the columns said it in print)
    for t in soup.select("table.example"):
        divs = []
        for tr in t.find_all("tr"):
            a, b = tr.find("td", class_="first"), tr.find("td", class_="second")
            assert a is not None and b is not None, tr
            div = soup.new_tag("div")
            div["class"] = ["poetry"]
            for td in (a, b):
                td.name = "div"
                td["class"] = ["line"]
                div.append(td.extract())
            divs.append(div)
            pairs += 1
        for div in divs:
            t.insert_before(div)
        t.decompose()
    assert pairs == EXAMPLE_PAIRS, pairs

    # indented examples: a sentence a line, unless they are whole passages
    for d in soup.select("div.example"):
        ps = d.find_all("p", recursive=False)
        if all(re.match(r"\d+\. ", R.clean(p.get_text(" "))) for p in ps):
            d.unwrap()                  # the numbered Exercises of Chapter VII
            continue
        d["class"] = ["poetry"]
        for p in ps:
            p.name = "div"
            p["class"] = ["line"]
    for ul in soup.select("ul.word-list"):
        ul.name = "div"
        ul["class"] = ["poetry"]
        for li in ul.find_all("li"):
            li.name = "div"
            li["class"] = ["line"]

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, part = [], None, None
    for it in items:
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"([IVX]+)\. (.+)", t)
            r = re.fullmatch(r"(\d+)\. (.+)", t)
            if it[1] == 2 and m:
                title = f"{m.group(1)}. {R.titlecase(m.group(2))}"
                cur = {"title": title, "stream": []}
                part = title
                sections.append(cur)
                continue
            if it[1] == 3 and r:
                cur = {"title": t, "stream": [], "chapter": True}
                if part:
                    cur["part_before"], part = part, None
                    sections.pop()          # the chapter heading is the divider
                sections.append(cur)
                continue
        cur["stream"].append(it)
    # Chapters II and III open straight on Rule 1 and Rule 8: nothing of the
    # chapter's own was dropped when it became a divider
    assert sum(bool(s.get("chapter")) for s in sections) == RULES
    assert [s.get("part_before") for s in sections if s.get("part_before")] == [
        "II. Elementary Rules of Usage", "III. Elementary Principles of Composition"]

    # witness 1: the printed Contents, chapter and rule titles in order
    key = lambda t: re.sub(r"[^a-z]+", " ", t.lower()).strip()
    ours = []
    for s in sections:
        if s.get("part_before"):
            ours.append(s["part_before"])
        ours.append(s["title"])
    theirs = [re.sub(r"\s*\d+$", "", r) for r in toc_rows if r and not r.startswith("Page")]
    strip_num = lambda t: re.sub(r"^([IVX]+|\d+)\.\s*", "", t)
    assert [key(strip_num(a)) for a in ours] == [key(strip_num(b)) for b in theirs], \
        [(a, b) for a, b in zip(ours, theirs) if key(strip_num(a)) != key(strip_num(b))][:3]

    # witness 2: the raw HTML's words from the first chapter to the end note
    raw_body = body[body.index("I. INTRODUCTORY</h2>") - 60:body.index('id="tn-bottom"')]
    raw = R.raw_words(raw_body)
    got = R.words([it for s in sections for it in s["stream"]]) + \
        sum(len(s["title"].split()) + len((s.get("part_before") or "").split()) for s in sections)
    assert abs(raw - got) <= 0.005 * raw, (raw, got)

    # A WORD-INITIAL APOSTROPHE must be typed as one: `se typogrify` reads a
    # straight quote before a letter as an OPENING quote, and Rule 1 came out
    # "adding ‘s" in the epub (the page renders the straight mark fine)
    R.text_fixes(sections, [("Sir, 'twas", "Sir, ’twas", "Browning; elided it")])
    fixed = [s for s in sections if " 's" in s["title"]]
    assert len(fixed) == 1, fixed
    fixed[0]["title"] = fixed[0]["title"].replace(" 's", " ’s")
    R.compose(book, sections, plates=[])
    print(f"{len(sections)} sections, {pairs} example pairs, {got:,} words (raw {raw:,})")


if __name__ == "__main__":
    main()
