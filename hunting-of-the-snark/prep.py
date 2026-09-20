"""Lewis Carroll, The Hunting of the Snark (1876): a RESTORED EDITION.

    python3 hunting-of-the-snark/prep.py

Gutenberg #29888, Macmillan's first edition with Henry Holiday's nine
illustrations and the two cover designs. Kept: the dedication to Gertrude
Chataway (an acrostic on her name, and the first letters of its lines are
the reason it is set as printed), the Preface and the eight Fits. The
blackletter title and heading images carry only words the headings
already give, and are dropped; the publisher's list at the end goes too.

THE VERSE: Gutenberg sets each line as a <p> inside div.verse, with
p.stanza opening a stanza and p.indent/indent2/indent4 for the indents.
It is rebuilt here into stanza blocks, indent kept, with the plates left
where they fall between stanzas.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

LETTERING = {f"fit{r}.png" for r in "I II III IV V VI VII VIII".split()} | {
    "alice.png", "halftitle.png", "agony.png", "london.png", "contents.png"}
PLATES = ["cover.jpg", "page5.png", "page10.png", "page17.png", "page31.png", "page41.png",
          "page52.png", "page62.png", "page74.png", "page82.png", "coverback.jpg"]
FITS = ["The Landing", "The Bellman’s Speech", "The Baker’s Tale", "The Hunting",
        "The Beaver’s Lesson", "The Barrister’s Dream", "The Banker’s Fate", "The Vanishing"]
ORD = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
PRINTED = {"cover.jpg": "The front cover of the first edition",
           "coverback.jpg": "The back cover of the first edition",
           "page17.png": "Ocean-Chart."}


def rebuild_verse(soup):
    n = 0
    # the last two stanzas sit in a div.verse inside an unclosed one: unwrap
    # the outer shell, so each div rebuilt holds only lines and plates
    for div in soup.select("div.verse"):
        if div.find("div", class_="verse"):
            div.unwrap()
    for div in soup.select("div.verse"):
        out = BeautifulSoup("", "html.parser")
        stanza = None
        for p in div.find_all(["p", "div"], recursive=False):
            cls = set(p.get("class") or [])
            if "illustration" in cls:
                out.append(p.extract() if False else BeautifulSoup(str(p), "html.parser"))
                stanza = None
                continue
            if stanza is None or "stanza" in cls:
                box = soup.new_tag("div", attrs={"class": "poetry"})
                stanza = soup.new_tag("div", attrs={"class": "stanza"})
                box.append(stanza)
                out.append(box)
            m = re.search(r"indent(\d*)", " ".join(cls))
            depth = (int(m.group(1) or 2) // 2) if m else 0
            line = soup.new_tag("span", attrs={"class": f"verse indent{depth}"})
            for c in list(p.contents):
                line.append(c.extract() if hasattr(c, "extract") else c)
            stanza.append(line)
            n += 1
        div.replace_with(out)
    return n


def main():
    book = R.Book(HERE, "pg29888-h.zip", drop={f: "blackletter lettering" for f in LETTERING},
                  flatten={"intro", "maintext", "page"}, skip_classes={"mynote", "pub_ads"})
    h = book.html()
    # the Preface's one footnote (the helmsman): its anchor id is "note1",
    # which the walker's footnote pattern does not know
    h, n = re.subn(r'(href="#|id=")note1"', r'\1fn_1"', h)
    assert n == 2, n
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for img in soup.find_all("img"):
        if img["src"].split("/")[-1] in LETTERING:
            img.find_parent("p").decompose() if img.find_parent("p") else img.decompose()
    # the Contents table: dropped, and kept as the witness for the Fits
    toc_t = next(t for t in soup.find_all("table") if "Fit the First" in t.get_text())
    toc = [R.clean(tr.find("td").get_text(" ")) for tr in toc_t.find_all("tr") if "Fit" in tr.get_text()]
    toc_t.decompose()
    lines = rebuild_verse(soup)
    w = R.Walker(book, soup)
    items = w.stream(soup)
    sections, cur, cover = [], None, None
    for it in items:
        if it[0] == "PLATE" and it[1] == "cover.jpg":
            cover = it
            continue
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"FIT ([IVX]+)\.—(.+?)\.", t)
            if "Inscribed to a dear Child" in t:
                cur = {"title": "Dedication", "stream": [("P", "*" + t.replace("*", "") + "*")]}
            elif t == "PREFACE.":
                cur = {"title": "Preface", "stream": []}
            elif m:
                k = "I II III IV V VI VII VIII".split().index(m.group(1))
                cur = {"title": f"Fit the {ORD[k]}: {FITS[k]}", "stream": []}
            elif t.startswith("WORKS BY"):
                cur = None
                continue
            else:
                continue              # the repeated sub-heading, the title page
            sections.append(cur)
            continue
        if cur is not None:
            cur["stream"].append(it)
    assert [s["title"] for s in sections][2:] == [f"Fit the {o}: {f}" for o, f in zip(ORD, FITS)], [s["title"] for s in sections]
    assert [re.sub(r"\W", "", t.lower()) for t in toc] == [re.sub(r"\W", "", t.lower().replace(":", ".")) for t in
            [s_["title"] for s_ in sections][2:]], toc
    sections[0]["stream"].insert(0, cover)
    plates = [{"src": it[1], "printed": PRINTED.get(it[1], "")} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert [p["src"] for p in plates] == PLATES, [p["src"] for p in plates]
    R.all_images_placed(book, plates)
    R.text_fixes(sections, [("on the line (in p. 18)", "on the line (in Fit the Second)", "p. 18 is Fit the Second")])
    for s in sections:
        # "[TURN OVER." sends the reader to the publisher's list, which is gone
        s["stream"] = [it for it in s["stream"] if it[0] != "HR" and not (it[0] == "P" and it[1] == "[TURN OVER.")]
    rows, described = R.compose(book, sections, plates=plates)
    stanzas = sum(1 for s in sections for it in s["stream"] if it[0] == "BLOCK")
    emitted = sum(len(it[1].split("\n")) for s in sections for it in s["stream"] if it[0] == "BLOCK")
    if emitted != lines:
        for s_ in sections:
            print(s_["title"], sum(len(it[1].split("\n")) for it in s_["stream"] if it[0] == "BLOCK"))
    assert emitted == lines, (emitted, lines)            # every line of verse, once
    print(f"{len(sections)} sections, {lines} lines, {stanzas} stanzas, {len(rows)} plates, {described} described")


if __name__ == "__main__":
    main()
