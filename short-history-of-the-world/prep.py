"""H. G. Wells, A Short History of the World (1922): a RESTORED EDITION.

    python3 short-history-of-the-world/prep.py

Gutenberg #35461, the Macmillan New York edition of 1922 with its 208
plates. Screened as clear (arch 0.43, calq 22.2, 22-word sentences):
Wells wrote it to be read in an evening by anybody, and it needs an
edition, not a retelling.

Structure is the book's own: sixty-seven chapters and the Chronological
Table, checked against the printed Contents. The plates are checked, in
order, against the printed List of Illustrations. Dropped: the title page,
the Contents, the List of Illustrations and the Index (its page numbers
point at nothing in a reflowable edition).

PRINTED CAPTIONS: each plate carries a title line in capitals, then
sometimes a note and a photograph credit in small type. The title line is
set in title case here (an all-caps line reads as a heading), the rest as
printed.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup, NavigableString  # noqa: E402

CHAPTERS = 67

# WELLS'S PREFACE, WHICH GUTENBERG LEAVES OUT. Both 1922 Macmillan scans
# print it on the leaf before the Contents; typed from the page image of
# shorthistoryofwo00welluoft (the italics are read off the page) and
# checked below against BOTH scans' OCR, which share no keystrokes with it.
PREFACE = [
    "This Short History of The World is meant to be read straightforwardly almost as a novel is read. It gives in the most general way an account of our present knowledge of history, shorn of elaborations and complications. It has been amply illustrated and everything has been done to make it vivid and clear. From it the reader should be able to get that general view of history which is so necessary a framework for the study of a particular period or the history of a particular country. It may be found useful as a preparatory excursion before the reading of the author’s much fuller and more explicit *Outline of History* is undertaken. But its especial end is to meet the needs of the busy general reader, too driven to study the maps and time charts of that *Outline* in detail, who wishes to refresh and repair his faded or fragmentary conceptions of the great adventure of mankind. It is not an abstract or condensation of that former work. Within its aim the *Outline* admits of no further condensation. This is a much more generalized History, planned and written afresh.",
    "H. G. Wells.",
]


def check_preface():
    import difflib
    letters = lambda t: re.sub(r"[^a-z]", "", t.lower())
    ours = letters(" ".join(PREFACE))
    for ident in ("shorthistoryofwo00welluoft", "shorthistoryofwo00well"):
        ocr = (HERE / "_src" / f"scan-{ident}-djvu.txt").read_text()
        a = ocr.index("PREFACE") + 7
        b = ocr.index("CONTENTS", a)
        theirs = letters(re.sub(r"-\s*\n", "", ocr[a:b]))
        r = difflib.SequenceMatcher(None, ours, theirs, autojunk=False).ratio()
        assert r > 0.995, (ident, r)
PLATES = 208
KEEP = {"B.C.", "A.D.", "U.S.A.", "S.S.", "H.M.S."}

# SCAN VOTE: Gutenberg against two copies of the 1922 Macmillan printing
# (shorthistoryofwo00welluoft, shorthistoryofwo00well), keeping only the
# readings where both scans agree against the edition (scan_diff.py
# --vote). Every entry was read in place. Gutenberg's transcription came
# from OCR and kept its word errors: "or" for "of", "it" for "a", "all"
# and "an" swapped, "arid" for "and", "polities" for "politics". Left as
# Gutenberg has them, because they are the printer's misprints and
# Gutenberg corrected them: "Muhummad", "natually", "distreesful".
TEXT_FIXES = [
    ("a number whose individuals whose individual differences", "a number whose individual differences", "Gutenberg doubled words; both scans"),
    ("a crabbed text arid then", "a crabbed text and then", "both scans"),
    ("complicated by the fad that", "complicated by the fact that", "both scans"),
    ("the polities of", "the politics of", "both scans", 2),
    ("old-world polities", "old-world politics", "both scans"),
    ("levels or beauty", "levels of beauty", "both scans"),
    ("the help or various", "the help of various", "both scans"),
    ("the fatigues or a court", "the fatigues of a court", "both scans"),
    ("own mode or proceeding", "own mode of proceeding", "both scans"),
    ("the greatest or the trading", "the greatest of the trading", "both scans"),
    ("it was all age of intolerance", "it was an age of intolerance", "both scans"),
    ("came to all end", "came to an end", "both scans"),
    ("Paris, and an France", "Paris, and all France", "both scans"),
    ("exacted it tribute", "exacted a tribute", "both scans"),
    ("then it very efficient", "then a very efficient", "both scans"),
    ("drawing to it close", "drawing to a close", "both scans"),
    ("the front. Then was a cessation", "the front. There was a cessation", "both scans"),
    ("Shi- Hwang-ti", "Shi-Hwang-ti", "transcription slip; spelled so everywhere else"),
    ("archæolologists", "archæologists", "Gutenberg typo; both scans"),
]
# PRINTED CAPTIONS, each read on the page image of the 1922 printing
# (shorthistoryofwo00welluoft, leaf = page + 23). Gutenberg ran several
# second lines into the capitals of the first, and pasted a stray
# "statue on left" into two. PAGE REFERENCES to plates are replaced by the
# chapter they are in, since a reflowable page has no page 54.
CAPTION_FIXES = [
    ("ag", "Humenocaris", "Hymenocaris"),
    ("ag", "see fossil on page 13", "see the fossil in the next plate"),
    ("cg", "architecht", "architect"),
    ("co", "the Altamira drawing on p. 54, and also with the Greek frieze, p. 140",
     "the Altamira drawing in Chapter XI, and also with the Greek frieze in Chapter XXV"),
    ("dd", "vesselswith sails and oars statue on left", "vessels with sails and oars"),
    ("dg", "the animals shown on p. 105", "the animals on the archaic amphora in Chapter XIX"),
    ("fb", "the pedestal her shown", "the pedestal here shown"),
    ("fb", "The complete obelisk is seen on page 239.", "The complete obelisk is seen in Chapter XLI."),
    ("fd", "The obelisk of Theodosius in in the foreground statue on left", "The obelisk of Theodosius is in the foreground"),
    ("gi", "Pained", "Painted"),
    ("hg", "From a print the British Museum", "(From a print in the British Museum)"),
    ("hp", "Soldier on the Eighteenth", "Soldier of the Eighteenth"),
    ("hu", "The crew came out", "The crew come out"),
    ("hy", "(Photo taken by another", "(Photo taken from another"),
]

# The Chronological Table was transcribed with ï for æ throughout.
AE = [("Chïronia", "Chæronia", 1), ("Cïsar", "Cæsar", 3), ("Mylï", "Mylæ", 1),
      ("Nicïa", "Nicæa", 1), ("Thermopylï", "Thermopylæ", 1)]


def footnotes(h):
    """Gutenberg's marks are "[<a>1</a>]" in the text and a bracketed
    backlink in the note; rename both to the fn_ shape the Walker reads,
    brackets and all, asserting all seven are found both ways."""
    h, a = re.subn(r'\[<a id="chap(\w+?)fn(\d+)text"></a><a href="#chap\w+?fn\d+" class="pginternal">\d+</a>\]',
                   r'<a href="#fn_\1_\2">\2</a>', h)
    h, b = re.subn(r'<a id="chap(\w+?)fn(\d+)"></a>\s*\[<a href="#chap\w+?fn\d+text" class="pginternal">\d+</a>\]',
                   r'<a id="fn_\1_\2"></a>', h)
    assert a == b == 7, (a, b)
    return h


def caption(p):
    """Title line (caps) -> title case; each later printed line as printed,
    and a line that ends without a stop takes one, so a title, its note and
    a photograph credit do not run together once the line breaks go."""
    for br in p.find_all("br"):
        br.replace_with("\x00")
    lines = [re.sub(r"\s+([,.;:)])", r"\1", R.clean(x)) for x in p.get_text(" ").split("\x00")]
    lines = [l.replace("B.C. 206 - A.D. 220", "B.C. 206–A.D. 220") for l in lines]
    lines = [l for l in lines if l]
    if not lines:
        return "", ""
    lines[0] = R.titlecase(lines[0], keep=KEEP)
    lines = [re.sub(r"(?<=\w)$", ".", l) if k < len(lines) - 1 else l for k, l in enumerate(lines)]
    return lines[0], " ".join(lines[1:])


def main():
    book = R.Book(HERE, "pg35461-h.zip", drop={"cover.jpg": "Gutenberg cover"}, source_fixes=[
        # the caption of the Alhambra plate pasted onto Milan Cathedral's;
        # both scans print MILAN CATHEDRAL alone over the 98 spires
        ("MILAN CATHEDRALA COURTYARD IN THE ALHAMBRA\r\n<br>", "MILAN CATHEDRAL\r\n<br>", "caption paste"),
    ])
    h = footnotes(book.html())
    # "B.C. A.D." three times: a stray A.D. after a B.C. date, absent from
    # both 1922 scans.
    h, n = re.subn(r"(<small>B\.C\.</small>)\s*<small>A\.D\.</small>", r"\1", h)
    assert n == 3, n
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    tables = soup.find_all("table")
    toc = [R.clean(tr.get_text(" ")) for tr in tables[0].find_all("tr")][1:]
    toc = [re.sub(r"\s+\d+$", "", t) for t in toc if t]
    lois = [re.sub(r"\s+\d+$", "", R.clean(tr.get_text(" "))) for tr in tables[1].find_all("tr")][1:]
    lois = [t for t in lois if t]
    tables[0].decompose(); tables[1].decompose()
    # the index: from its heading to the end
    idx = soup.find("a", id="INDEX").find_parent("h3")
    for n in list(idx.find_all_next()):
        n.extract() if n.parent is not None else None
    for n in list(idx.next_siblings):
        n.extract()
    idx.decompose()

    printed = {}
    for fig in soup.find_all(class_="fig"):
        cap = fig.find(class_="caption")
        if cap is None:                 # a map: its title is engraved on it
            printed[fig.find("img")["src"].split("/")[-1]] = ""
            continue
        t, rest = caption(cap)
        printed[fig.find("img")["src"].split("/")[-1]] = (t + (" " + rest if rest else "")).strip()
        cap.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)
    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"([IVXL]+) (.+)", t)
            if m:
                cur = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2), keep=KEEP)}", "stream": []}
            elif t == "CHRONOLOGICAL TABLE":
                cur = {"title": "Chronological Table", "stream": []}
            else:
                cur = None              # title page, byline, Contents, half-title
                continue
            sections.append(cur)
            continue
        if cur is not None:
            cur["stream"].append(it)
        else:
            assert it[0] in ("HR",) or (it[0] == "P" and not it[1].strip()), it
    assert sum(s["title"].startswith("Chapter") for s in sections) == CHAPTERS
    check_preface()
    key = lambda t: re.sub(r"[^a-z]+", " ", re.sub(r"^chapter [ivxl]+:", "", t.lower())).strip()
    ours = [key(s["title"]) for s in sections]
    theirs = [key(re.sub(r"^[IVXL]+\.\s*", "", t)) for t in toc if t != "A SHORT HISTORY OF THE WORLD" and t != "INDEX"]
    # The printed Contents and the chapter heading differ once in wording:
    # Contents "...Empires of the Steamship and Railway", heading "...of
    # Steamship and Railway". The heading stands.
    theirs = [t.replace("empires of the steamship", "empires of steamship") for t in theirs]
    ours, theirs = [o.replace(" ", "") for o in ours], [t.replace(" ", "") for t in theirs]
    assert ours == theirs, [(a, b) for a, b in zip(ours, theirs) if a != b][:3] or (len(ours), len(theirs))

    # chronology rows: date and event, empty third column dropped
    for s in sections:
        for k, it in enumerate(s["stream"]):
            if it[0] == "BLOCK" and " | " in it[1]:
                rows = [" ".join(c for c in l.lstrip("\t").split(" | ") if c.strip()) for l in it[1].split("\n")]
                s["stream"][k] = ("BLOCK", "\n".join("\t" + r for r in rows if r.strip()))

    plates = [{"src": it[1], "printed": printed[it[1]]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert len(plates) == PLATES, len(plates)
    ids = {p["src"]: R.L[i // 26] + R.L[i % 26] for i, p in enumerate(plates)}
    for pid, bad, good in CAPTION_FIXES:
        p = next(p for p in plates if ids[p["src"]] == pid)
        assert p["printed"].count(bad) == 1, (pid, bad, p["printed"])
        p["printed"] = p["printed"].replace(bad, good)
    R.all_images_placed(book, plates)
    # witness: the List of Illustrations, in order
    k2 = lambda t: re.sub(r"[^a-z]+", "", t.lower().replace("the", ""))
    bad = [(i, p["printed"][:50], l) for i, (p, l) in enumerate(zip(plates, lois))
           if not (k2(l)[:12] in k2(p["printed"]) or k2(p["printed"])[:12] in k2(l))]
    assert len(lois) == PLATES, len(lois)
    for b in bad:
        print("LOI?", b)

    # witness: raw words from chapter I to the index, less captions
    start = body.index('id="chapI"')
    raw = R.raw_words(body[start:body.index('id="INDEX"')])
    capw = sum(len(re.findall(r"\w+", p["printed"])) for p in plates)
    got = R.words([it for s in sections for it in s["stream"]]) + sum(len(s["title"].split()) - 1 for s in sections if s["title"].startswith("Chapter")) + 2
    print(f"raw {raw:,} (captions ~{capw:,}), got {got:,}")
    assert abs(raw - capw - got) <= 0.001 * raw, (raw, capw, got)
    for s in sections:
        s["stream"] = [it for it in s["stream"] if it[0] != "HR"]
    sections.insert(0, {"title": "Preface", "stream": [("P", p) for p in PREFACE]})
    R.text_fixes(sections, TEXT_FIXES + [(a, b, "ï for æ in the table", n) for a, b, n in AE])
    assert not any("ï" in it[1] for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK"))
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described")


if __name__ == "__main__":
    main()
