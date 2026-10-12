"""Lewis Carroll, Through the Looking-Glass, and What Alice Found There
(Macmillan, dated 1872, published December 1871), with John Tenniel's
fifty illustrations: a RESTORED EDITION.

    python3 books/looking-glass/prep.py

THE TEXT is Gutenberg #12 (the Millennium Fulcrum Edition 1.7), which
follows the first edition: no 1896 Preface, no Wasp in a Wig. Gutenberg
carries none of Tenniel's pictures, only a modern cover and a small redrawn
chess diagram.

THE PLATES are cut from Archive.org `throughlooking00carr`, Gettysburg
College's copy of the first edition (title page "Macmillan and Co. 1872 ...
With fifty illustrations by John Tenniel"), scanned at 500 ppi. The leaves
are kept in _src/scan/ (NNNN = the leaf index in the scan's _jp2.zip, which
is also the hOCR page index). Each box below was found from the scan's own
picture zones (ABBYY's ocr_photo) united with the large connected ink
components of the leaf, padded 14 px, and checked by eye; the paper is
levelled to white and the cut saved in greyscale. Eight pictures share
their page with text that runs beside them; where a wrapped line falls
inside the box it is painted out (WHITE). Kept besides the fifty: Carroll's
chess diagram (leaf 11, with the printed RED and WHITE), the first verse
of "Jabberwocky" as the book prints it, in mirror type (leaf 41, where
Gutenberg has letter-reversed text, "sevot yhtils eht dna"), and the red
cloth covers with Tenniel's gilt Red Queen and White Queen (leaves 251, 256).

PLACEMENT: each plate goes before the first paragraph (or stanza) that
BEGINS after the picture's top on its page, read from the scan. A picture
set mid-paragraph therefore follows that paragraph, and a picture set
between stanzas of a poem falls between those stanzas, as the book has
it. Every anchor must match exactly one paragraph or stanza. Three
placements are the page's furniture rather than its text: the
frontispiece (the White Knight) closes the front matter, since it faces
the title page; the Red Queen being shaken heads Chapter X, which it faces;
the kitten closes Chapter XI, which it faces.

WITNESSES: the raw HTML's word count, minus exactly what is removed, must
equal the emitted words (a reading that shares no code with the walker);
every line of every poem emitted once; 54 plates; the twelve chapter
titles against Gutenberg's Contents and the first edition's.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

SRC = HERE / "_src"
SCAN = SRC / "scan"
CUT = HERE.parent.parent / "build" / "looking-glass-plates"   # regenerated, not kept
SCAN_ID = "throughlooking00carr"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}

# leaf: (crop box, [rectangles of wrapped text painted out])
BOXES = {
    11: ((585, 382, 1491, 1413), []),          # the chess diagram
    12: ((178, 272, 1960, 2906), []),          # frontispiece
    21: ((235, 562, 1735, 1522), []),
    25: ((162, 470, 1846, 2427), []),
    31: ((174, 409, 1810, 2469), []),
    32: ((286, 424, 1906, 2457), []),
    34: ((263, 1534, 1988, 2907), []),
    37: ((230, 466, 1630, 1772), []),
    40: ((266, 1020, 1206, 2104), []),
    41: ((370, 630, 1526, 1200), []),          # Jabberwocky in mirror type
    43: ((77, 356, 1839, 2976), []),
    49: ((79, 463, 1833, 2527), [(1060, 495, 1840, 850)]),
    55: ((353, 742, 1713, 2412), []),
    58: ((396, 679, 1908, 1702), []),
    61: ((131, 724, 1862, 1822), []),
    70: ((298, 408, 2018, 1784), []),
    76: ((418, 1133, 1922, 2137), []),
    77: ((210, 426, 1709, 1390), []),
    78: ((476, 1868, 1890, 2834), []),
    83: ((332, 772, 1539, 2249), []),
    87: ((48, 430, 1777, 1782), []),
    93: ((125, 434, 1863, 1530), []),
    96: ((295, 688, 2053, 1822), []),
    98: ((282, 1047, 2034, 2114), []),
    100: ((410, 1433, 1918, 2448), []),
    104: ((358, 1070, 1969, 2210), []),
    107: ((127, 682, 1856, 1928), []),
    113: ((761, 700, 1885, 2203), []),
    116: ((1042, 394, 2000, 1775), []),
    122: ((446, 447, 1850, 2190), []),
    130: ((250, 414, 1997, 2534), []),
    138: ((338, 481, 2052, 2508), [(1160, 1670, 2060, 2508)]),
    147: ((114, 403, 1841, 2493), []),
    153: ((484, 791, 1410, 2278), []),
    158: ((196, 400, 1944, 2512), []),
    162: ((306, 1007, 1930, 2362), []),
    168: ((260, 366, 2005, 1718), []),
    172: ((147, 762, 1926, 2086), []),
    176: ((108, 421, 1249, 2068), []),
    180: ((257, 384, 1915, 2070), []),
    186: ((366, 398, 1780, 1960), []),
    192: ((255, 1223, 1893, 2357), []),
    199: ((288, 1098, 1620, 2229), []),
    204: ((188, 382, 1187, 1899), []),
    210: ((278, 911, 1902, 2006), []),
    218: ((279, 1059, 1918, 2159), []),
    221: ((318, 612, 1722, 2374), []),
    225: ((124, 686, 1098, 2102), []),
    232: ((207, 423, 1993, 3074), [(1295, 423, 2000, 1470)]),
    234: ((618, 890, 1546, 2368), []),
    237: ((534, 917, 1490, 2300), []),
    240: ((466, 802, 1890, 2304), []),
    251: ((8, 8, 2119, 3253), []),             # front cover, in colour
    256: ((8, 8, 2119, 3253), []),             # back cover, in colour
}
COLOUR = {251, 256}
NOT_TENNIEL_FIFTY = {11, 41, 251, 256}

# leaf -> where it goes. A string is the opening words of the paragraph or
# stanza it goes BEFORE (quotation marks and emphasis ignored).
PLACE = {
    21: "One thing was certain",
    25: "That’s three faults, Kitty",
    31: "In another moment Alice was through the glass",
    32: "Then she began looking about",
    34: "Here something began squeaking on the table",
    37: "So Alice picked him up very gently",
    40: "There was a book lying near Alice",
    43: "And hast thou slain the Jabberwock",
    49: "I don’t care about the colour",
    55: "It succeeded beautifully",
    58: "For some minutes Alice stood without speaking",
    61: "Now! Now!” cried the Queen",
    70: "All this time the Guard was looking at her",
    76: "What does it live on?” Alice asked, with great curiosity",
    77: "And there’s the Dragon-fly",
    78: "Weak tea with cream in it",
    83: "Alice thought, but nothing came of it",
    87: "If you think we’re wax-works",
    93: "The Walrus and the Carpenter\n\tWere walking close at hand",
    96: "But wait a bit,’ the Oysters cried",
    98: "I weep for you,’ the Walrus said",
    100: "Isn’t he a lovely sight?",
    104: "I knew it was!” cried Tweedledum",
    107: "Do I look very pale?",
    113: "It can’t go straight",
    116: "Suppose he never commits the crime",
    122: "What is it you want to buy?” the Sheep said at last",
    130: "To buy!” Alice echoed",
    138: "Yes, all his horses and all his men",
    147: "I see it now,” Alice remarked",
    153: "I said to him, I said it plain",
    158: "Then came the horses",
    162: "You alarm me!” said the King",
    168: "There was a pause in the fight",
    172: "The Lion had joined them while this was going on",
    176: "If that doesn’t ‘drum them out of town",
    180: "Another Rule of Battle",
    186: "Whenever the horse stopped",
    192: "How can you go on talking so quietly",
    199: "He said “I hunt for haddocks’ eyes",
    204: "But how can it have got there",
    210: "Alice considered. “The bone wouldn’t remain",
    218: "What am I to do?” exclaimed Alice",
    221: "To answer the door?",
    225: "May I give you a slice?",
    232: "I can’t stand this any longer!",
    240: "Snowdrop, my pet!",
}
TITLES = ["Looking-Glass House", "The Garden of Live Flowers", "Looking-Glass Insects",
          "Tweedledum and Tweedledee", "Wool and Water", "Humpty Dumpty",
          "The Lion and the Unicorn", "“It’s My Own Invention”", "Queen Alice",
          "Shaking", "Waking", "Which Dreamed It?"]
ROMAN = "I II III IV V VI VII VIII IX X XI XII".split()
PRINTED = {"leaf0251.jpg": "The front cover of the first edition",
           "leaf0256.jpg": "The back cover of the first edition"}

# WHERE GUTENBERG'S TRANSCRIPTION DEPARTS FROM THE PRINT. Each was found by
# scan_diff's two-scan vote (the 1872 first edition, throughlooking00carr,
# and Macmillan's 1922 printing, throughlookinggl1922carr, agreeing against
# Gutenberg) and then read on the 1872 page image. Carroll's text stands as
# printed (Alex, 2026-10-12): these restore it; nothing else is changed.
PRINT = "the 1872 page reads so"
TEXT_FIXES = [
    ("to 4th (*Tweedledum", "to Q.’s 4th (*Tweedledum", PRINT),
    ("you wicked little thing", "you wicked wicked little thing", PRINT),
    ("came wiggling down", "came wriggling down", PRINT),
    ("a new invention of hers for getting", "a new invention for getting", PRINT),
    ("she could not speak", "she couldn’t speak", PRINT),
    ("footstep, thump, thump, thump, along", "footstep, thump, thump, along", PRINT),
    ("I won’t *just* yet", "I won’t go *just* yet", PRINT),
    ("how I like my walk", "how I liked my walk", PRINT),
    ("‘Oh, I like it well", "‘Oh, I liked it well", PRINT),
    ("sitting next to the Goat", "sitting next the Goat", PRINT),
    ("I never knew them to do it", "I never knew them do it", PRINT),
    ("people who name them", "people that name them", PRINT),
    ("Alice looked up at the Rocking", "Alice looked at the Rocking", PRINT),
    ("didn’t help much", "didn’t help her much", PRINT),
    ("if you’ll move a little further", "if you’ll come a little further", PRINT),
    ("together though the wood", "together through the wood", PRINT),
    ("how d’you do", "how d’ye do", PRINT),
    ("But the little men only", "But the fat little men only", PRINT),
    ("And that was scarcely odd", "And this was scarcely odd", PRINT),
    ("far worse off than you", "far worse than you", PRINT),
    ("voice rising to a squeak", "voice rising into a squeak", PRINT),
    ("Rub as she could, she", "Rub as she would, she", PRINT),
    ("worse then ever", "worse than ever", PRINT),
    ("to get the rushes", "to get hold of the rushes", PRINT),
    ("she wasn’t hurt", "she wasn’t a bit hurt", PRINT),
    ("so like to see a little crab", "so like a little crab", PRINT),
    ("a sort of a compliment", "a sort of compliment", PRINT),
    ("Don’t stand there chattering", "Don’t stand chattering", PRINT),
    ("he pursed his lips and looked", "he pursed up his lips, and looked", PRINT),
    ("I though you meant", "I thought you meant", PRINT),
    ("what’s the ‘*gyre*’", "what’s to ‘*gyre*’", PRINT),
    ("air with this thumb", "air with his thumb", PRINT),
    ("Didn’t I tell you?", "Don’t I tell you?", PRINT),
    ("carrying rough trays", "carrying round trays", PRINT),
    ("turned round rather instantly", "turned round instantly", PRINT),
    ("fastened across his shoulder,", "fastened across his shoulders,", PRINT),
    ("What’s the dish for?", "What’s that dish for?", PRINT),
    ("This took a very long time", "This took a long time", PRINT),
    ("got it in a last", "got it in at last", PRINT),
    ("“And you do Addition?”", "“Can you do Addition?”", PRINT),
    ("I can do Addition, if you", "I can do Addition,” she said, “if you", PRINT),
    ("poor Queen’s feeling.", "poor Queen’s feelings.", PRINT),
    ("make out the words, and", "make out words, and", PRINT),
    ("I talks English", "I speaks English", PRINT),
    ("“Vexes it, you know.”", "“Wexes it, you know.”", PRINT),
    ("one elbow in the rug", "one elbow on the rug", PRINT),
    ("Messenger said in a sulky tone", "Messenger said in a sullen tone", PRINT),
    # the Queens' word, twice, in both printings ("Can you do Subtraction?"
    # and "Try another Subtraction sum" are printed plain)
    ("She can’t do Subtraction,”", "She can’t do Substraction,”", PRINT),
    ("I can’t do Subtraction, under", "I can’t do Substraction, under", PRINT),
    # one witness only (the 1922 printing has Carroll's later revisions, or
    # its OCR failed): each read on the 1872 page image
    ("all but the bit behind", "all but the bit just behind", PRINT),
    ("a stupid enough name!", "a stupid name enough!", PRINT),
    ("poems that were ever invented", "poems that ever were invented", PRINT),
    ("animal—vegetable—or mineral?", "animal—or vegetable—or mineral?", PRINT),
    ("two great heads vanished", "two great heads suddenly vanished", PRINT),
    ("very heavy, and fitted tight", "very heavy, that fitted tight", PRINT),
    ("Alice laughed aloud:", "Alice laughed loud:", PRINT),
    ("get into the—into *what*?", "get into the—into the—into *what*?", PRINT),
    ("noticed, that last time you picked", "noticed, the last time you picked", PRINT),
    ("“If I only knew,”", "“If only I knew,”", PRINT),
    ("uncomfortable in the silence", "uncomfortable at the silence", PRINT),
    # a whole sentence Gutenberg lost, found by the plain diff (scan_diff
    # without --vote): the 1872 page 116-17 and the 1922 printing both have it
    ("“*The King has promised me—with his very own mouth*—to—to—”",
     "“*the King has promised me*—ah, you may turn pale, if you like! You didn’t think I was "
     "going to say that, did you? *The King has promised me—with his very own mouth*—to—to—”",
     "the 1872 pages 116–17 read so; Gutenberg drops a sentence"),
]


def leaf_path(n):
    SCAN.mkdir(parents=True, exist_ok=True)
    dest = SCAN / f"{n:04d}.jp2"
    if not dest.exists():
        url = (f"https://archive.org/download/{SCAN_ID}/{SCAN_ID}_jp2.zip/"
               f"{SCAN_ID}_jp2%2F{SCAN_ID}_{n:04d}.jp2")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
            data = r.read()
        if len(data) < 20_000:
            raise SystemExit(f"leaf {n} came back as {len(data)} bytes")
        dest.write_bytes(data)
    return dest


def cut_plates():
    """Cut every plate from its leaf; returns {synthetic source name: path}."""
    import numpy as np
    from PIL import Image
    CUT.mkdir(parents=True, exist_ok=True)
    out = {}
    for n, (box, white) in BOXES.items():
        name = f"leaf{n:04d}.jpg"
        dest = CUT / name
        out[name] = str(dest)
        if dest.exists() and dest.stat().st_mtime > Path(__file__).stat().st_mtime:
            continue
        im = Image.open(leaf_path(n))
        if n in COLOUR:
            im.convert("RGB").crop(box).save(dest, quality=88)
            continue
        a = np.asarray(im.convert("L")).astype(float)
        # level the yellowed paper to white: the 92nd percentile is paper
        paper, black = np.percentile(a, 92), np.percentile(a, 0.5)
        a = np.clip((a - black) / max(1.0, paper - 8 - black), 0, 1) ** 1.15 * 255
        a = a.astype("uint8")
        for x0, y0, x1, y1 in white:
            a[y0:y1, x0:x1] = 255
        Image.fromarray(a).crop(box).save(dest, quality=90)
    return out


def rebuild_poems(soup):
    """p.poem: lines split at <br>, a blank line between stanzas, the indent
    given as non-breaking spaces (four to a level)."""
    total = 0
    for p in soup.select("p.poem"):
        raw = p.decode_contents()
        box = soup.new_tag("div", attrs={"class": "poetry"})
        stanza = None
        for line in re.split(r"<br\s*/?>", raw):
            line = line.replace("\r", "").strip("\n")
            if not line.strip(" \xa0\n"):
                stanza = None
                continue
            lead = len(re.match(r"[ \xa0]*", line).group(0).replace(" ", ""))
            if stanza is None:
                stanza = soup.new_tag("div", attrs={"class": "stanza"})
                box.append(stanza)
            span = soup.new_tag("span", attrs={"class": f"verse indent{lead // 4}"})
            for c in list(BeautifulSoup(line.strip(" \xa0\n"), "html.parser").contents):
                span.append(c)
            stanza.append(span)
            total += 1
        p.replace_with(box)
    return total


def moves_table(soup, p):
    """The solution: two interleaved columns, White's moves flush and Red's
    indented. Set side by side, as the book prints them; White's eleventh
    move has no answer, and '""' is assemble's explicit empty cell (a
    trailing empty one is stripped and the row stops being a table row)."""
    lines = [l.replace("\r", "").strip("\n") for l in re.split(r"<br\s*/?>", p.decode_contents())]
    white, red = [], []
    for l in lines:
        if not l.strip(" \xa0\n"):
            continue
        (red if l.startswith("\xa0") else white).append(l.strip(" \xa0\n"))
    assert len(white) == 11 and len(red) == 10, (len(white), len(red))
    rows = "".join(f"<tr><td>{w}</td><td>{red[i] if i < len(red) else '""'}</td></tr>" for i, w in enumerate(white))
    p.replace_with(BeautifulSoup(f"<table>{rows}</table>", "html.parser"))


def place(sections):
    """Insert each plate before the item its anchor opens."""
    norm = lambda s: re.sub(r"[*“”‘’\"'\s]", "", s)
    for n, anchor in PLACE.items():
        a = norm(anchor)
        hits = []
        for s in sections:
            for k, it in enumerate(s["stream"]):
                if it[0] in ("P", "BLOCK") and norm(it[1]).startswith(a):
                    hits.append((s, k))
        assert len(hits) == 1, (n, anchor, len(hits))
        s, k = hits[0]
        s["stream"].insert(k, ("PLATE", f"leaf{n:04d}.jpg", ""))


def raw_count(html):
    """R.raw_words, with inline tags removed rather than spaced: Gutenberg
    italicises inside a word ("<i>me</i>—but"), which a tag-to-space
    reading would count as two."""
    return R.raw_words(re.sub(r"</?(?:i|em|b|strong|a)\b[^>]*>", "", html))


def main():
    replace = cut_plates()
    replace["fig01.jpg"] = replace.pop("leaf0011.jpg")   # the scan's diagram, in Gutenberg's place
    book = R.Book(HERE, "pg12-h.zip", drop={"cover.jpg": "Gutenberg's modern cover"}, replace=replace,
                  long_side=1300)   # line engravings: 1300 px keeps the hatching at twice page width
    h = book.html()
    body = book.body_html(h)
    raw = raw_count(body)
    soup = BeautifulSoup(body, "html.parser")
    removed = 0

    def drop(el):
        nonlocal removed
        removed += raw_count(str(el))
        el.decompose()

    # the e-text's own title block, down to the rule before the Dramatis Personae
    h1 = soup.find("h1")
    for el in [h1] + list(h1.find_next_siblings(limit=5)):
        if el.name == "hr":
            el.decompose()
            break
        drop(el)
    for img in soup.find_all("img"):
        if img["src"].endswith("cover.jpg"):
            img.find_parent("div").decompose()
    # Dramatis Personae: the heading becomes the section's title
    dp = soup.find("p", string=re.compile("DRAMATIS")) or soup.find(lambda t: t.name == "p" and "DRAMATIS" in t.get_text())
    removed += raw_count("DRAMATIS PERSONÆ.")
    dp.replace_with(BeautifulSoup('<h2>Dramatis Personæ</h2><p>(<i>As arranged before commencement of game.</i>)</p>', "html.parser"))
    # the table's spacer column; "WHITE" lacks the full stop the book and RED. have
    dt = soup.find("table")
    for tr in dt.find_all("tr"):
        tr.find_all("td")[2].decompose()
    first = dt.find("td")
    assert first.string == "WHITE"
    first.string = "WHITE."
    # the diagram: RED and WHITE are inside the scan's picture
    fig = soup.find("img", src=re.compile("fig01")).find_parent("div")
    for c in fig.find_all("p", class_="caption"):
        drop(c)
    letters = soup.select("p.letter")
    assert len(letters) == 2
    moves_table(soup, letters[0])
    # Humpty Dumpty's sum, set as the book sets it
    s365 = letters[1]
    assert "365" in s365.get_text()
    pre = soup.new_tag("pre")
    pre.string = "365\n  1\n____\n364\n___"
    s365.replace_with(pre)
    # the mirror verse: the book prints it in looking-glass type
    mirror = next(p for p in soup.select("p.poem") if "YKCOWREBBAJ" in p.get_text())
    removed += raw_count(str(mirror))
    mirror.replace_with(BeautifulSoup('<div class="figcenter"><img alt="" src="images/leaf0041.jpg"/></div>', "html.parser"))
    # the rows of stars between scenes
    for p in soup.select("p.asterism"):
        p.replace_with(soup.new_tag("hr"))
    # the prefatory poem: untitled in the book, titled here by its first line
    chap = soup.select("div.chapter")
    assert "Child of the pure" in chap[0].get_text()
    chap[0].insert(0, BeautifulSoup("<h2>Child of the Pure Unclouded Brow</h2>", "html.parser"))
    # Gutenberg's Contents: dropped, and kept as the witness for the titles
    assert chap[1].find("h2").get_text() == "Contents"
    toc = [R.clean(td.get_text()) for td in chap[1].find_all("td")]
    drop(chap[1])
    # the closing acrostic: its own section; THE END goes
    last = chap[-1]
    hr = last.find("hr", recursive=False)
    acro = hr.find_next_sibling("p", class_="poem")
    assert acro.get_text().strip().startswith("A boat beneath")
    hr.replace_with(BeautifulSoup("<h2>A Boat beneath a Sunny Sky</h2>", "html.parser"))
    drop(last.find("p", class_="center"))
    for h2 in soup.find_all("h2"):
        if h2.get_text().strip().startswith("CHAPTER"):
            removed += raw_count(str(h2))
    nl = rebuild_poems(soup)

    w = R.Walker(book, soup)
    items = w.stream(soup)
    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"CHAPTER ([IVX]+)\. (.+)", t)
            if m:
                k = ROMAN.index(m.group(1))
                cur = {"title": f"Chapter {m.group(1)}: {TITLES[k]}", "stream": []}
            else:
                cur = {"title": t, "stream": []}
            sections.append(cur)
            continue
        assert cur is not None, it
        cur["stream"].append(it)
    titles = [s["title"] for s in sections]
    assert titles[:2] == ["Dramatis Personæ", "Child of the Pure Unclouded Brow"] and titles[-1] == "A Boat beneath a Sunny Sky", titles
    assert len(sections) == 15
    # the chapter titles: Gutenberg's Contents, and the first edition's
    k_ = lambda t: re.sub(r"[^a-z]", "", t.lower())
    assert [k_(t.split(".", 1)[1]) for t in toc] == [k_(t) for t in TITLES], toc
    # every word the HTML holds, less exactly what was taken out
    got = sum(R.words(s["stream"]) for s in sections)
    assert got == raw - removed, (got, raw, removed)
    emitted = sum(len(it[1].split("\n")) for s in sections for it in s["stream"] if it[0] == "BLOCK")
    # poem lines + the eleven rows of moves + the Dramatis table's 10 + the sum's 5
    assert emitted == nl + 11 + 10 + 5, (emitted, nl)

    R.text_fixes(sections, TEXT_FIXES)
    place(sections)
    dp_, front = sections[0], sections[1]
    dp_["stream"].insert(0, ("PLATE", "leaf0251.jpg", ""))         # the front cover
    dp_["stream"].append(("PLATE", "leaf0012.jpg", ""))            # the frontispiece faces the title
    ten = next(s for s in sections if s["title"].startswith("Chapter X:"))
    ten["stream"].insert(0, ("PLATE", "leaf0234.jpg", ""))        # faces "Shaking"
    eleven = next(s for s in sections if s["title"].startswith("Chapter XI:"))
    eleven["stream"].append(("PLATE", "leaf0237.jpg", ""))         # faces "Waking"
    sections[-1]["stream"].append(("PLATE", "leaf0256.jpg", ""))   # the back cover

    plates = [{"src": it[1], "printed": PRINTED.get(it[1], "")}
              for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    tenniel = [p for p in plates if p["src"].startswith("leaf") and int(p["src"][4:8]) not in NOT_TENNIEL_FIFTY]
    assert len(tenniel) == 50 and len(plates) == 54, (len(tenniel), len(plates))
    # in the book's order: the leaves rise through the book
    order = [int(p["src"][4:8]) if p["src"].startswith("leaf") else 11 for p in plates]
    seq = [o for o in order if o not in (251, 256)]
    assert seq == sorted(seq), seq
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates ({len(tenniel)} Tenniel), {nl} lines of verse, "
          f"{got} words, {described} described")


if __name__ == "__main__":
    main()
