"""Lewis Carroll, Alice's Adventures in Wonderland, in Heinemann's 1907
edition illustrated by Arthur Rackham: a RESTORED EDITION.

    python3 alice/prep.py

Gutenberg #28885. Carroll's text of 1865 as Heinemann printed it, with
Rackham's thirteen colour plates, his frontispiece, fourteen drawings in
the text, the decorated title page, the endpapers and the cover, and
Austin Dobson's proem for this edition. Checked against the printed
Contents and List of the Plates.

THREE THINGS THE TRANSCRIPTION DOES THAT THE PAGE DOES NOT NEED:
  - each chapter opens on a decorated initial set as a PICTURE, so the
    first letter of the chapter is missing from the text ("LICE was
    beginning"); the letter goes back, and the small capitals after it
    come down to ordinary case;
  - every poem is one div of <br>-separated lines with the indents as
    inline margins, which the walker would run into a paragraph; each is
    rebuilt into stanzas, the margin kept as indent (the Mouse's tale at
    twice the resolution, since its shape is the joke);
  - the chapter heading and its title are two separate boxes.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup, NavigableString, Tag  # noqa: E402

# RACKHAM'S COLOUR PLATES AT FULL SIZE. Gutenberg's are about 500 pixels
# tall; Wikimedia Commons holds scans of all thirteen at two to seven times
# that ("Alice in Wonderland by Arthur Rackham - NN - ..."), each compared
# with Gutenberg's by eye. The file names and Commons titles are in
# _src/commons/sources.json.
import json as _json
_SRC = HERE / "_src" / "commons"
REPLACE = {k: str(_SRC / k) for k in _json.loads((_SRC / "sources.json").read_text())}
assert len(REPLACE) == 13
INITIALS = {"a.png", "c-quote.png", "f.png", "h-quote.png", "i.png", "t.png", "y-quote.png"}
ROMAN = "I II III IV V VI VII VIII IX X XI XII".split()


def fix_initials(soup):
    n = 0
    for img in soup.find_all("img"):
        if img["src"].split("/")[-1] not in INITIALS:
            continue
        box = img.find_parent("div")
        letter = img.get("alt", "")
        nxt = box.find_next_sibling()
        box.decompose()
        # the first text node of the next block: prepend the letter and
        # bring the small-capital run down ("A" + "LICE" -> "Alice",
        # "A" + " LARGE" -> "A large", '"C' + "URIOUSER" -> '"Curiouser')
        first = next(t for t in nxt.descendants if isinstance(t, NavigableString) and t.strip())
        s = letter + str(first).lstrip("\n")
        m = re.match(r"^(\W*)([A-Z])([A-Z]*)((?:\s+[A-Z]{2,}\b)*)", s)
        s = m.group(1) + m.group(2) + m.group(3).lower() + m.group(4).lower() + s[m.end():]
        first.replace_with(s)
        n += 1
    return n


def rebuild_poems(soup):
    lines_total = 0
    for div in soup.select("div.poem"):
        tale = bool(div.find(class_=re.compile(r"^tale")))
        # split the div's children into lines at each <br>
        lines, cur = [], []
        for c in list(div.children):
            if isinstance(c, Tag) and c.name == "br":
                lines.append(cur)
                cur = []
            else:
                cur.append(c)
        lines.append(cur)
        box = soup.new_tag("div", attrs={"class": "poetry"})
        stanza = None
        for parts in lines:
            text = "".join(p.get_text() if isinstance(p, Tag) else str(p) for p in parts).strip()
            if not text:
                stanza = None                    # a blank line: the next stanza
                continue
            em = 0.0
            for p in parts:
                if isinstance(p, Tag):
                    m = re.search(r"margin-left:\s*([\d.]+)em", p.get("style", ""))
                    if m:
                        em = float(m.group(1))
            level = int(em * (2 if tale else 1) + 0.5)
            if stanza is None:
                stanza = soup.new_tag("div", attrs={"class": "stanza"})
                box.append(stanza)
            line = soup.new_tag("span", attrs={"class": f"verse indent{level}"})
            for p in parts:
                line.append(p.extract() if isinstance(p, Tag) else NavigableString(str(p)))
            stanza.append(line)
            lines_total += 1
        div.replace_with(box)
    return lines_total


def headings(soup):
    n = 0
    for ch in soup.select("div.chapter"):
        side = ch.find_next_sibling("div", class_="sidenote")
        h = soup.new_tag("h2")
        h.string = R.clean(ch.get_text()) + "|" + R.clean(side.get_text())
        ch.replace_with(h)
        side.decompose()
        n += 1
    return n


def main():
    book = R.Book(HERE, "pg28885-h.zip", drop={**{f: "decorated initial, restored as a letter" for f in INITIALS},
                                               "spine.jpg": "the book's spine"}, flatten={"center"},
                  replace=REPLACE)
    body = book.body_html(book.html())
    soup = BeautifulSoup(body, "html.parser")
    # Gutenberg's own note on other editions, and its table
    note = soup.find(lambda t: t.name == "h4" and "several editions" in t.get_text())
    note.find_next("table").decompose()
    note.decompose()
    # the Contents (a table nested in a table) and the List of the Plates:
    # dropped, and kept as witnesses
    toc_t = [t for t in soup.find_all("table") if "Rabbit-hole" in t.get_text() and not t.find("table")][0]
    toc = [R.clean(tr.find_all("td")[1].get_text(" ")) for tr in toc_t.find_all("tr") if len(tr.find_all("td")) == 3]
    toc = [t for t in toc if t]
    lop_t = soup.find("table", attrs={"data-summary": "List of Illustrations"})
    lop = [R.clean(tr.find("td").get_text(" ")) for tr in lop_t.find_all("tr")][1:]
    outer = toc_t
    while outer.find_parent("table") is not None:
        outer = outer.find_parent("table")
    outer.decompose()
    lop_t.decompose()
    # the rabbit-hole drawing is a CSS background behind the text of one
    # page: the text becomes ordinary paragraphs, the drawing a plate
    rh = soup.find("table", class_="rabbithole")
    fig = BeautifulSoup('<div class="figcenter"><img alt="" src="images/p0003-rabbithole.png"/></div>', "html.parser")
    paras = rh.find_all("p")
    holder = rh.find_parent("div", class_="center") or rh
    holder.insert_before(fig)
    for para in paras:
        holder.insert_before(para.extract())
    holder.decompose()
    for img in soup.find_all("img"):
        if img["src"].endswith("spine.jpg"):
            img.find_parent("div").decompose()
    # each colour plate is a two-cell table, caption beside picture: the
    # picture becomes a figure (its caption is the alt text, and the List)
    nt = 0
    for t in soup.find_all("table"):
        img = t.find("img")
        if img is not None and "insert" in img["src"]:
            t.replace_with(BeautifulSoup(f'<div class="figcenter">{img}</div>', "html.parser"))
            nt += 1
    assert nt == 12, nt
    ni = fix_initials(soup)
    nl = rebuild_poems(soup)
    nh = headings(soup)
    assert nh == 12 and ni == 12, (nh, ni)
    # printed captions: the colour plates carry theirs as alt text (they
    # are the List of the Plates); one drawing has a caption box
    printed = {}
    for img in soup.find_all("img"):
        src = img["src"].split("/")[-1]
        if "insert" in src or src == "f0002-image.jpg":
            printed[src] = R.clean(img.get("alt", "")).strip('"')
        box = img.find_parent("div")
        cap = box.find(class_="caption") if box else None
        if cap:
            printed[src] = R.clean(cap.get_text(" "))
            cap.decompose()
    w = R.Walker(book, soup)
    items = w.stream(soup)
    front = [it for it in items[:6] if it[0] == "PLATE"]
    sections = [{"title": "Proem", "stream": list(front)}]
    cur, blocks = sections[0], 0
    for it in items:
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"CHAPTER ([IVX]+)\|(.+)", t)
            if m:
                cur = {"title": f"Chapter {m.group(1)}: {m.group(2).replace('*', '')}", "stream": []}
                sections.append(cur)
            elif it[1] > 1:
                cur = None                                 # Contents, List of the Plates
            continue
        if it in front or it[0] == "HR" or (it[0] == "P" and it[1] == "Printed in England"):
            continue
        if cur is None:
            continue
        if cur is sections[0] and it[0] == "P" and "AUSTIN DOBSON" in it[1]:
            cur["stream"].append(("P", "Austin Dobson."))
            # Carroll's own prefatory poem follows, untitled in the book
            cur = {"title": "All in the Golden Afternoon", "stream": []}
            sections.append(cur)
            continue
        cur["stream"].append(it)
    key = lambda t: re.sub(r"[^a-z]", "", t.lower())
    # the chapter titles as the Contents prints them: the running sidenotes
    # at the chapter heads shorten some ("Pool of Tears")
    assert len(sections) == 14 and len(toc) == 12
    for s_, t in zip(sections[2:], toc):
        num = s_["title"].split(":")[0]
        assert key(t).endswith(key(s_["title"].split(": ", 1)[1])), (t, s_["title"])
        s_["title"] = f"{num}: {t}"
    assert [key(s_["title"].split(": ", 1)[1]) for s_ in sections[2:]] == [key(t) for t in toc], ([s_["title"] for s_ in sections], toc)
    assert len(sections) == 14
    plates = [{"src": it[1], "printed": printed.get(it[1], "")} for s_ in sections for it in s_["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    listed = [p_ for p_ in plates if p_["printed"] and p_["src"] != "p0015-image.png"]
    assert [key(p_["printed"]) for p_ in listed] == [key(l) for l in lop], ([p_["printed"] for p_ in listed], lop)
    for p_, l in zip(listed, lop):                     # the printed List's wording
        p_["printed"] = l
    emitted = sum(len(it[1].split("\n")) for s_ in sections for it in s_["stream"] if it[0] == "BLOCK")
    assert emitted == nl, (emitted, nl)                    # every line of every poem, once
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {nl} lines of verse, {described} described")


if __name__ == "__main__":
    main()
