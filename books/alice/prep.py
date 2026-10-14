"""Lewis Carroll, Alice's Adventures in Wonderland (Macmillan, 1865), with
John Tenniel's forty-two illustrations: a RESTORED EDITION.

    python3 books/alice/prep.py

THE TEXT is Gutenberg #11 (the Millennium Fulcrum Edition 3.0), which
follows Macmillan's text of 1866 but leaves out the prefatory poem, "All in
the golden afternoon". The poem is restored here, typed from the scan below
and read line by line on its pages (leaves 11-13).

THE PLATES are cut from Archive.org `alicesadventu00carr`, the University
of Toronto (Thomas Fisher Rare Book Library) copy of Macmillan's 1867
printing, "Sixth Thousand", "With forty-two illustrations by John Tenniel",
scanned at 650 ppi. It is printed from the setting Richard Clay made for the
1866 issue, the first published (the 1865 Oxford printing was withdrawn
over the quality of its pictures). The leaves are kept in _src/scan/ (NNNN
= the leaf index in the scan's _jp2.zip, which is also the hOCR page index).

EACH PICTURE IS FOUND FROM THE PAGE, NOT TYPED IN: the hOCR's text lines
(lines whose words are mostly letters) mark what is type; every ink
component lying wholly inside a text line is a letter; what is left, joined
by a 30 px dilation, is the picture, and its largest piece is the plate,
padded 14 px. Twenty pictures share their page with text set beside them;
the text lines and paragraphs inside the box are painted out, sparing the
picture's own strokes. Paper levelled to white, greyscale, as looking-glass.
Every cut was checked on a contact sheet.

PLACEMENT: each plate goes before the first paragraph (or stanza) that
BEGINS after the picture's top on its page, read from the scan; where no
paragraph begins below it on that page, before the next one that does. The
four chapter-head pictures (I, II, III, V) therefore open their chapters.
Every anchor must match exactly one paragraph or stanza. The frontispiece
(the King and Queen of Hearts at the trial) faces the title page, which
comes before the prefatory poem, so it heads the poem's section.

THE MOUSE'S TALE is set as the 1867 page sets it: Gutenberg's <pre> has the
words but its own line breaks; the breaks and the indents here are read off
leaf 53 (each line's left edge from the hOCR, one indent level, two
spaces, per 50 px of the page), and the tale's words are asserted equal to Gutenberg's. Two
points are the page's against Gutenberg's: "to law;" and "old Fury;" (Gutenberg
has colons), both read on the 1867 page image. Its type
shrinks down the tail on the page; that cannot be carried.

WITNESSES: the raw HTML's word count, minus exactly what is removed, plus
exactly what is added (the poem), must equal the emitted words; every line
of every poem emitted once; 42 plates; the twelve chapter titles against
Gutenberg's Contents.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

SRC = HERE / "_src"
SCAN = SRC / "scan"
HOCR = SRC / "scan-alicesadventu00carr-hocr.html.gz"
CUT = HERE.parent.parent / "build" / "alice-plates"     # regenerated, not kept
SCAN_ID = "alicesadventu00carr"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}

# leaf -> the opening words of the paragraph or stanza it goes BEFORE
# (quotation marks, emphasis and spacing ignored). Leaf 8 is the frontispiece.
PLACE = {
    17: "Alice was beginning to get very tired",
    24: "Alice opened the door and found",
    26: "However, this bottle was not marked",
    31: "Curiouser and curiouser!",
    34: "Alice took up the fan and gloves",          # none begins below it on p. 18
    39: "I wish I hadn’t cried so much!",
    42: "We indeed!” cried the Mouse",               # none begins below it on p. 26
    45: "They were indeed a queer-looking party",
    51: "Then they all crowded round her once more",
    61: "Luckily for Alice, the little magic bottle",
    64: "Next came an angry voice",
    67: "She drew her foot as far down the chimney",
    71: "Hardly knowing what she did",
    75: "The Caterpillar and Alice looked at each other",
    79: "You are old, Father William,” the young man said",
    80: "You are old,” said the youth, “as I mentioned before",
    81: "You are old,” said the youth, “and your jaws",
    82: "You are old,” said the youth, “one would hardly",
    93: "The Fish-Footman began by producing",
    97: "There’s certainly too much pepper",
    104: "So she set the little creature down",
    107: "Well, then,” the Cat went on",
    109: "Did you say pig, or fig?",
    113: "The Hatter opened his eyes very wide",
    119: "‘Twinkle, twinkle, little bat!",
    126: "At any rate I’ll never go there again!",
    129: "That’s none of your business, Two!",
    133: "The Queen turned crimson with fury",
    137: "The chief difficulty Alice found at first",
    144: "The King’s argument was",
    148: "The game’s going on rather better now",
    154: "They very soon came upon a Gryphon",
    157: "When we were little,” the Mock Turtle went on at last",
    166: "Oh, you sing,” said the Gryphon",
    173: "‘Tis the voice of the Lobster",
    182: "The Queen of Hearts, she made some tarts",
    186: "Give your evidence,” the King repeated angrily",
    189: "Come, that finishes the guinea-pigs!",
    193: "The trial cannot proceed,” said the King",   # none begins below it on p. 177
    202: "Never!” said the Queen furiously",
    204: "At this the whole pack rose up into the air",
}
FRONT = 8
LEAVES = sorted([FRONT, *PLACE])

# "All in the golden afternoon", as the 1867 leaves 11-13 print it (the
# 1907 text this edition replaces read "dry." and "wither'd"; 1867 has
# "dry," and "withered"). Two spaces = the indented line.
POEM = """All in the golden afternoon
  Full leisurely we glide;
For both our oars, with little skill,
  By little arms are plied,
While little hands make vain pretence
  Our wanderings to guide.

Ah, cruel Three! In such an hour,
  Beneath such dreamy weather,
To beg a tale of breath too weak
  To stir the tiniest feather!
Yet what can one poor voice avail
  Against three tongues together?

Imperious Prima flashes forth
  Her edict “to begin it”—
In gentler tone Secunda hopes
  “There will be nonsense in it!”—
While Tertia interrupts the tale
  Not <i>more</i> than once a minute.

Anon, to sudden silence won,
  In fancy they pursue
The dream-child moving through a land
  Of wonders wild and new,
In friendly chat with bird or beast—
  And half believe it true.

And ever, as the story drained
  The wells of fancy dry,
And faintly strove that weary one
  To put the subject by,
“The rest next time—” “It <i>is</i> next time!”
  The happy voices cry.

Thus grew the tale of Wonderland:
  Thus slowly, one by one,
Its quaint events were hammered out—
  And now the tale is done,
And home we steer, a merry crew,
  Beneath the setting sun.

Alice! a childish story take,
  And with a gentle hand
Lay it where Childhood’s dreams are twined
  In Memory’s mystic band,
Like pilgrim’s withered wreath of flowers
  Pluck’d in a far-off land."""

# The Mouse's tale on leaf 53: (left edge on the page in px, line). The
# last two lines' edges are read off the page image (the hOCR drops them).
TALE = [
    (585, "“Fury said to"), (785, "a mouse, That"), (1116, "he met"), (1193, "in the"),
    (1238, "house,"), (1157, "‘Let us"), (1112, "both go"), (1070, "to law;"),
    (982, "<i>I</i> will"), (784, "prosecute"), (732, "<i>you</i>.—"), (767, "Come, I’ll"),
    (858, "take no"), (932, "denial;"), (1050, "We must"), (1274, "have a"),
    (1421, "trial:"), (1515, "For"), (1414, "really"), (1356, "this"),
    (1389, "morning"), (1565, "I’ve"), (1424, "nothing"), (1355, "to do.’"),
    (1253, "Said the"), (1179, "mouse to"), (1156, "the cur,"), (1208, "‘Such a"),
    (1337, "trial,"), (1229, "dear sir,"), (1105, "With no"), (1017, "jury or"),
    (983, "judge,"), (1014, "would be"), (1079, "wasting"), (1115, "our breath.’"),
    (1201, "‘I’ll be"), (1163, "judge,"), (1105, "I’ll be"), (1057, "jury,’"),
    (1020, "Said"), (1059, "cunning"), (1146, "old Fury;"), (1225, "‘I’ll try"),
    (1262, "the whole"), (1325, "cause,"), (1372, "and"), (1293, "condemn"),
    (1269, "you"), (1241, "to"), (1260, "death.’”"),
]

# WHERE GUTENBERG'S TRANSCRIPTION DEPARTS FROM THE PRINT, found by
# scan_diff's two-scan vote (the 1867 printing, alicesadventu00carr, and
# Macmillan's 1872 printing, alicesadventures00carruoft, agreeing against
# Gutenberg) and each read on the 1867 page image; then the plain diff
# against the 1867 OCR alone, every real difference read on the page.
# Nearly all are not Gutenberg's slips but CARROLL'S OWN LATER REVISIONS:
# #11 follows the text he revised in 1886 and 1897 ("had no idea" for "had
# not the slightest idea", the owl and the panther for the owl and the
# oyster). This edition is the 1866 book, so its words are the 1866 words,
# as the 1867 printing has them (the looking-glass ruling: a later printing
# can confirm the page but not overrule it). After these the vote's residue
# is OCR noise only. Punctuation and capitalisation were not compared.
PRINT = "the 1867 page reads so"
TEXT_FIXES = [
    ("I shall be late!”", "I shall be too late!”", PRINT),
    ("and fortunately was just in time", "and was just in time", PRINT),
    ("Alice had no idea what Latitude", "Alice had not the slightest idea what Latitude", PRINT),
    ("either, but thought they were nice grand words", "either, but she thought they were nice grand words", PRINT),
    ("heads downward!", "heads downwards!", PRINT),
    ("with Dinah, and saying to her very earnestly", "with Dinah, and was saying to her very earnestly", PRINT),
    ("nothing on it except a tiny golden key", "nothing on it but a tiny golden key", PRINT),
    ("first thought was that it might belong", "first idea was that this might belong", PRINT),
    ("and round the neck of the bottle", "and tied round the neck of the bottle", PRINT),
    ("nice little histories about", "nice little stories about", PRINT),
    ("flame of a candle is like", "flame of a candle looks like", PRINT),
    ("Just then her head struck", "Just at this moment her head struck", PRINT),
    ("she was now more than nine feet", "she was now rather more than nine feet", PRINT),
    ("Table doesn’t signify", "Table don’t signify", PRINT),
    ("How neatly spread his claws", "How neatly spreads his claws", PRINT),
    ("And welcome little fishes in", "And welcomes little fishes in", PRINT),
    ("time to avoid shrinking away", "time to save herself from shrinking away", PRINT),
    ("there were a Duck and a Dodo", "there was a Duck and a Dodo", PRINT),
    ("a person of authority among them", "a person of some authority among them", PRINT),
    ("not that she wanted much to know", "not that she much wanted to know", PRINT),
    ("explain the mistake it had made", "explain the mistake that it had made", PRINT),
    ("Bill’s to go down", "Bill’s got to go down", PRINT),
    ("the master says you’re to go down", "the master says you’ve got to go down", PRINT),
    ("Shy, they seem to put", "Why, they seem to put", PRINT),
    ("the Rabbit’s voice along", "the Rabbit’s voice alone", PRINT),
    ("but she did not see anything", "but she could not see anything", PRINT),
    ("she thought of herself", "she thought to herself", PRINT),
    ("crawled away in the grass", "crawled away into the grass", PRINT),
    ("opportunity for repeating his remark", "opportunity of repeating his remark", PRINT),
    ("The only things in the kitchen", "The only two creatures in the kitchen", PRINT),
    ("own business,” the Duchess said in a hoarse growl", "own business,” said the Duchess in a hoarse growl", PRINT),
    ("Just think of what work", "Just think what work", PRINT),
    ("after her as she went out, but it just missed her", "after her as she went, but it just missed her", PRINT),
    ("and looked into its eyes again", "and looked in its eyes again", PRINT),
    ("to carry it further", "to carry it any further", PRINT),
    ("getting so used to queer things", "getting so well used to queer things", PRINT),
    ("While she was looking at the place", "While she was still looking at the place", PRINT),
    ("Alice quietly said, just as if it had come back", "Alice answered very quietly, just as if the Cat had come back", PRINT),
    ("said the Hatter. “You might just as well say", "said the Hatter. “Why, you might just as well say", PRINT),
    ("remark seemed to have no sort of meaning", "remark seemed to her to have no sort of meaning", PRINT),
    ("Alice considered a little, and then said", "Alice considered a little, and said", PRINT),
    ("a little hot tea upon its nose", "a little hot tea on its nose", PRINT),
    ("than waste it in asking riddles", "than wasting it in asking riddles", PRINT),
    ("when the Queen jumped up and bawled out", "when the Queen bawled out", PRINT),
    ("But what happens when you come to the beginning", "But when you come to the beginning", PRINT),
    ("I won’t interrupt again", "I won’t interrupt you again", PRINT),
    ("Then she went to work nibbling", "Then she set to work nibbling", PRINT),
    ("procession,” thought she,", "procession,” she thought,", PRINT),
    ("lie down upon their faces", "lie down on their faces", PRINT),
    ("she stood still where she was", "she stood where she was", PRINT),
    ("wild beast, screamed", "wild beast, began screaming,", PRINT),
    ("double themselves up and to stand", "double themselves up and stand", PRINT),
    ("said the King, going up to Alice", "said the King, coming up to Alice", PRINT),
    ("and he called the Queen", "and he called to the Queen", PRINT),
    ("So she went in search", "So she went off in search", PRINT),
    ("went back for a little more conversation", "went back to have a little more conversation", PRINT),
    ("very hard indeed to make out", "very hard to make out", PRINT),
    ("did not much like keeping so close", "did not much like her keeping so close", PRINT),
    ("chin upon Alice’s shoulder", "chin on Alice’s shoulder", PRINT),
    ("your waist,” the Duchess said after a pause", "your waist,” said the Duchess after a pause", PRINT),
    ("so ordered about in all my life", "so ordered about before in all my life", PRINT),
    ("What! Never heard of uglifying!", "Never heard of uglifying!", PRINT),
    ("the Classics master", "the Classical master", PRINT),
    ("We can do without lobsters", "We can do it without lobsters", PRINT),
    ("are done with a whiting", "are done with whiting", PRINT),
    ("I might as well be at school", "I might just as well be at school", PRINT),
    ("she had sat down with her face in her hands", "she had sat down again with her face in her hands", PRINT),
    ("Alice said; but was dreadfully puzzled", "Alice said; but she was dreadfully puzzled", PRINT),
    ("How the Owl and the Panther were sharing a pie", "How the owl and the oyster were sharing a pie", PRINT),
    ("but she stopped hastily", "but she stopped herself hastily", PRINT),
    ("began staring at the Hatter", "began staring hard at the Hatter", PRINT),
    ("twinkling of the *what?*", "twinkling of *what?*", PRINT),
    ("that finished the guinea-pigs!", "that finishes the guinea-pigs!", PRINT),
    ("note-book, cackled out", "note-book, called out", PRINT),
    ("added in an offended tone", "added in an angry tone", PRINT),
    ("of little Alice herself, and once again", "of little Alice herself:—once again", PRINT),
    ("the distant sobs of the miserable", "the distant sob of the miserable", PRINT),
    ("on the Duchess’s knee", "on the Duchess’ knee", PRINT),
    # punctuation is not compared by the vote; these two were seen on the
    # page while reading it, where Gutenberg's quotation marks went wrong
    ("everybody laughed, “Let the jury consider their verdict.” the King said",
     "everybody laughed. “Let the jury consider their verdict,” the King said", PRINT),
    ("after all. “—*said I could not swim*—” you can’t swim",
     "after all. ‘—*said I could not swim*—’ you can’t swim", PRINT),
]


def leaf_path(n):
    SCAN.mkdir(parents=True, exist_ok=True)
    dest = SCAN / f"{n:04d}.jp2"
    if not dest.exists():
        import urllib.request
        url = (f"https://archive.org/download/{SCAN_ID}/{SCAN_ID}_jp2.zip/"
               f"{SCAN_ID}_jp2%2F{SCAN_ID}_{n:04d}.jp2")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
            data = r.read()
        if len(data) < 20_000:
            raise SystemExit(f"leaf {n} came back as {len(data)} bytes")
        dest.write_bytes(data)
    return dest


def hocr_text_boxes():
    """{leaf: ([text line boxes], [text paragraph boxes])}: only lines and
    paragraphs whose characters are mostly letters (the hOCR also reads
    hatching as 'words')."""
    import gzip

    def bb(t):
        return tuple(map(int, re.search(r"bbox (\d+) (\d+) (\d+) (\d+)", t.get("title", "")).groups()))
    soup = BeautifulSoup(gzip.open(HOCR, "rt").read(), "html.parser")
    pages = soup.find_all(class_="ocr_page")
    out = {}
    for n in LEAVES:
        lines, pars = [], []
        for p in pages[n].find_all(class_="ocr_par"):
            ls = p.find_all(class_="ocr_line")
            t = " ".join(w.get_text() for w in p.find_all(class_="ocrx_word")).replace(" ", "")
            letters = sum(c.isalpha() for c in t)
            if letters >= 3 and letters / max(1, len(t)) > 0.75:
                lines += [bb(l) for l in ls]
                pars.append(bb(p))
        out[n] = (lines, pars)
    return out


def cut_plates():
    """Cut every plate from its leaf; returns {synthetic source name: path}."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    CUT.mkdir(parents=True, exist_ok=True)
    out, boxes = {}, None
    for n in LEAVES:
        name = f"leaf{n:04d}.jpg"
        dest = CUT / name
        out[name] = str(dest)
        if dest.exists() and dest.stat().st_mtime > Path(__file__).stat().st_mtime:
            continue
        boxes = boxes or hocr_text_boxes()
        lines, pars = boxes[n]
        a = np.asarray(Image.open(leaf_path(n)).convert("L")).astype(float)
        paper, black = np.percentile(a, 92), np.percentile(a, 0.5)
        ink = a < paper - 45
        lab, k = ndi.label(ink)
        letter = np.zeros(k + 1, bool)
        for i, s in enumerate(ndi.find_objects(lab), 1):
            y0, y1, x0, x1 = s[0].start, s[0].stop, s[1].start, s[1].stop
            letter[i] = any(x0 >= bx0 - 8 and x1 <= bx1 + 8 and y0 >= by0 - 8 and y1 <= by1 + 8
                            for bx0, by0, bx1, by1 in lines)
        sizes = ndi.sum(np.ones_like(lab), lab, range(k + 1))
        keep = ~letter[lab] & ink & (sizes[lab] > 30)
        keep[:420, :] = False                  # running head and folio
        keep[3830:, :] = False                 # signature mark
        lab2, k2 = ndi.label(ndi.binary_dilation(keep, iterations=30))
        big = int(np.argmax(ndi.sum(keep, lab2, range(k2 + 1))))
        ys, xs = np.where((lab2 == big) & keep)
        H, W = a.shape
        box = (max(0, xs.min() - 14), max(0, ys.min() - 14), min(W, xs.max() + 15), min(H, ys.max() + 15))
        b = np.clip((a - black) / max(1.0, paper - 8 - black), 0, 1) ** 1.15 * 255
        pic = ndi.binary_dilation(keep, iterations=2)
        for bx0, by0, bx1, by1 in lines + pars:
            r = (slice(max(0, by0 - 6), by1 + 6), slice(max(0, bx0 - 6), bx1 + 6))
            sub = b[r]
            sub[~pic[r]] = 255
        b[ndi.binary_dilation(letter[lab], iterations=4) & ~pic] = 255
        b[b > 228] = 255                       # the paper's grain between painted-out lines
        Image.fromarray(b.astype("uint8")).crop(box).save(dest, quality=90)
    return out


def rebuild_poems(soup):
    """p.poem: lines split at <br>, a blank line between stanzas, the indent
    given as leading spaces (four to a level)."""
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
            lead = len(re.match(r"[ \xa0]*", line).group(0))
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
    italicises inside a word, which a tag-to-space reading counts as two."""
    return R.raw_words(re.sub(r"</?(?:i|em|b|strong|a)\b[^>]*>", "", html))


def main():
    replace = cut_plates()
    book = R.Book(HERE, "pg11-h.zip", drop={"cover.jpg": "Gutenberg's modern cover"}, replace=replace,
                  long_side=1300)   # line engravings: 1300 px keeps the hatching at twice page width
    body = book.body_html(book.html())
    raw = raw_count(body)
    soup = BeautifulSoup(body, "html.parser")
    removed = added = 0

    def drop(el):
        nonlocal removed
        removed += raw_count(str(el))
        el.decompose()

    soup.find("img", src=re.compile("cover.jpg")).find_parent("div").decompose()
    # the e-text's title block and its Contents (kept as the titles' witness)
    h1 = soup.find("h1")
    for el in [h1] + list(h1.find_next_siblings(limit=8)):
        if el.name == "table":
            toc = [R.clean(tr.find_all("td")[1].get_text()) for tr in el.find_all("tr")]
            drop(el)
            break
        if el.name == "hr":
            el.decompose()
        else:
            drop(el)
    assert len(toc) == 12, toc
    # the prefatory poem, which Gutenberg #11 leaves out
    first = soup.find("div", class_="chapter")
    poem_html = "<br>\n".join(l.replace("  ", "    ", 1) if l.startswith("  ") else l for l in POEM.split("\n"))
    first.insert_before(BeautifulSoup(f"<h2>All in the Golden Afternoon</h2><p class=\"poem\">{poem_html}</p>",
                                      "html.parser"))
    added += raw_count("All in the Golden Afternoon " + POEM)
    # the Mouse's tale: the 1867 page's lines and indents
    tale = next(p for p in soup.find_all("pre") if "Fury said" in p.get_text())
    letters = lambda s: re.sub(r"[^a-z]", "", re.sub(r"<[^>]+>", "", s).lower())
    assert letters(tale.get_text()) == letters(" ".join(t for _, t in TALE))
    x0 = min(x for x, _ in TALE)
    removed += raw_count(str(tale))
    added += raw_count(" ".join(t for _, t in TALE))
    tale.replace_with(BeautifulSoup(f'<div class="poetry"><div class="stanza">'
                                    + "".join(f'<span class="verse indent{round((x - x0) / 50)}">{t}</span>'
                                              for x, t in TALE) + "</div></div>", "html.parser"))
    # the Rabbit's address on the foot letter: a <pre>, set as indented lines
    foot = next(p for p in soup.find_all("pre") if "Right Foot" in p.get_text())
    foot.replace_with(BeautifulSoup(
        '<div class="poetry"><div class="stanza">'
        '<span class="verse indent0"><i>Alice’s Right Foot, Esq.,</i></span>'
        '<span class="verse indent1"><i>Hearthrug,</i></span>'
        '<span class="verse indent2"><i>near the Fender,</i></span>'
        '<span class="verse indent3">(<i>with Alice’s love</i>).</span></div></div>', "html.parser"))
    # CHORUS. in small capitals: an all-capital line would be set as a heading
    for p in soup.select("p.center"):
        parts = [R.clean(t) for t in re.split(r"<br\s*/?>", p.decode_contents())]
        assert parts[0] == "CHORUS.", parts
        p.replace_with(BeautifulSoup("".join(f"<p>{t}</p>" for t in ["Chorus."] + parts[1:]), "html.parser"))
    for p in soup.select("p.asterism"):
        p.replace_with(soup.new_tag("hr"))
    drop(soup.find("h5", string=re.compile("THE END")))
    # Gutenberg's own note, inside two poems: the stanzas Carroll added in
    # 1886, which the 1866 book does not print
    for p in soup.select("p.poem"):
        raw_p = p.decode_contents()
        if "[later editions" in raw_p:
            cut = re.search(r"(?:<br\s*/?>\s*){2}\[later editions", raw_p).start()
            removed += raw_count(raw_p[cut:])
            p.clear()
            p.append(BeautifulSoup(raw_p[:cut], "html.parser"))
    assert "[later editions" not in str(soup)
    nl = rebuild_poems(soup)

    w = R.Walker(book, soup)
    items = w.stream(soup)
    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            m = re.fullmatch(r"CHAPTER ([IVX]+)\. (.+)", it[2])
            if m:
                cur = {"title": f"Chapter {m.group(1)}: {m.group(2)}", "stream": []}
                removed += len(it[2].split())          # counted by R.words as a heading
            else:
                cur = {"title": it[2], "stream": []}
                added -= len(it[2].split())
            sections.append(cur)
            continue
        assert cur is not None, it
        cur["stream"].append(it)
    titles = [s["title"] for s in sections]
    assert titles[0] == "All in the Golden Afternoon" and len(sections) == 13, titles
    k_ = lambda t: re.sub(r"[^a-z]", "", t.lower())
    assert [k_(t.split(": ", 1)[1]) for t in titles[1:]] == [k_(t) for t in toc], (titles, toc)
    got = sum(R.words(s["stream"]) for s in sections)
    assert got == raw - removed + added, (got, raw, removed, added)
    emitted = sum(len(it[1].split("\n")) for s in sections for it in s["stream"] if it[0] == "BLOCK")
    assert emitted == nl + len(TALE) + 4, (emitted, nl)

    R.text_fixes(sections, TEXT_FIXES)
    place(sections)
    sections[0]["stream"].insert(0, ("PLATE", f"leaf{FRONT:04d}.jpg", ""))   # faces the title page

    plates = [{"src": it[1], "printed": ""} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    assert len(plates) == 42, len(plates)
    order = [int(p["src"][4:8]) for p in plates]
    assert order == sorted(order), order
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {nl} lines of verse + the tale's {len(TALE)}, "
          f"{got} words, {described} described")


if __name__ == "__main__":
    main()
