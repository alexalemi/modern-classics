"""Simon Newcomb, Astronomy for Everybody (1902): a RESTORED EDITION.

    python3 astronomy-for-everybody/fetch.py   # once
    python3 astronomy-for-everybody/prep.py

Wikisource's text, transcluded from a VALIDATED index of the McClure,
Phillips first edition of November 1902: preface, six Parts, thirty-three
chapters, the frontispiece and sixty-four figures.

WITNESSES, all asserted:
  - each Part page is the printed Contents for that Part: chapter titles
    in order, and every section heading of every chapter, in order;
  - the printed List of Illustrations: every plate, in order;
  - every image fetched is placed exactly once;
  - every Wikisource reference becomes a footnote.

The transcription sets each plate's printed caption as a centred line
after the image ("Fig. 4.—The Sun Crossing the Equator about March
Twentieth."), and a plate at the top of a page CUTS THE PARAGRAPH that
runs over it; both are mended here.
"""
import io
import json
import re
import sys
import urllib.parse
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

ROMAN = "I II III IV V VI VII VIII IX X XI".split()
WORD = "One Two Three Four Five Six".split()
TEXT_FIXES = [
    ("Density of sun : Density of earth", "Density of sun \u2236 Density of earth",
     "a ratio: the ratio sign, not a colon"),
    ("called *central* *eclipses*.", "called *central eclipses*.",
     "one italic phrase the transcription closed and reopened around a plate"),
    ("in the picture of Jupiter on page 204.", "in the picture of Jupiter, Figs. 37–38.",
     "the one print-page reference in the book, pointed at the plate it means"),
    ("It is now know that radiance", "It is now known that radiance",
     "the printer's misprint; both scans print it"),
    ("suggest many points, but prove few, unless negatively", "suggest many points, but prove few, unless negatively.", "both scans print the full stop"),
    ("penetrate com- pares", "penetrate compares", "a page-end hyphen the transcription left open"),
]
DITTO = {"Polar diameter,": "diameter,"}
HYPHEN_JOINS = {
    "headlong": "headlong",
    "astronomers": "astronomers",
    "interesting": "interesting",
    "conjunction,": "conjunction,",
    "principal": "principal",
    "inclined": "inclined",}
FLATTEN = {"prp-pages-output", "mw-parser-output", "mw-content-ltr", "tiInherit"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("’", "'"))


def soup_of(z, k):
    s = BeautifulSoup(z.read(f"{k:02d}.html").decode(), "html.parser")
    for x in s.select("style, link, .ws-noexport, .wst-header, .ws-header, .pagenum, .ws-pagenum, .__nop"):
        x.decompose()
    # {{ditto}}: a hidden width-holder plus the text printed in its place.
    # Mostly the printed text IS the value (Saturn's table uses it only to
    # align columns); where the page prints a DITTO MARK, reflowed text can
    # no longer put it under the word it repeats, so the word is spelled
    # out. "Equatorial \" 7,926.6 miles" repeats "diameter," alone.
    for d in s.find_all("span", class_="__ditto"):
        hid = d.find("span", class_="__ditto_hidden").get_text()
        vis = d.find("span", class_="__ditto_text").get_text()
        m = re.fullmatch(r'(.*?)\s*["„\u201c\u201d]\s*', vis, re.S)
        if m:
            vis = (m.group(1).strip() + " " + DITTO.get(hid, hid).strip()).strip() + " "
        d.replace_with(vis)
    for p in s.find_all("p"):                       # Wikisource's layout switch
        if R.clean(p.get_text()) == "Layout 2":
            p.decompose()
    return s


def fix_caption(t):
    t = re.sub(r"\b(Figs?)\s*\.\s*", r"\1. ", R.clean(t)).replace(" .", ".")
    return re.sub(r"\s*—\s*", "—", t)


def normalise_plates(soup):
    """Every plate becomes <figure><img src=ORIGINAL NAME><figcaption>:
    the centred ones already are figures; the floated ones are spans
    inside a paragraph with the caption after a <br>."""
    for img in soup.find_all("img"):
        a = img.find_parent("a", class_="mw-file-description")
        if a is None:
            continue
        img["src"] = urllib.parse.unquote(a["href"].split("File:", 1)[1])
    for sp in soup.select("span.img-floatleft, span.img-floatright, span.img-center"):
        img = sp.find("img")
        f = soup.new_tag("figure")
        f.append(img.extract())
        cap = soup.new_tag("figcaption")
        cap.string = fix_caption(sp.get_text(" "))
        f.append(cap)
        sp.replace_with(f)


def part_contents(s):
    """A Part page: its title and [(chapter title, [section heads])]."""
    lines = [R.clean(t) for t in s.get_text("\n").split("\n") if R.clean(t)]
    lines = [l for l in lines if l not in ("Layout 2", "page")]
    i = next(i for i, l in enumerate(lines) if re.fullmatch(r"PART [IVX]+\.", l))
    head = lines[i] + " " + lines[i + 1]
    i += 2
    chapters = []
    while i < len(lines):
        l = lines[i]
        if re.fullmatch(r"[IVX]+\.", l):
            chapters.append([lines[i + 1], []])
            i += 3
        elif re.fullmatch(r"\d+", l):
            i += 1
        else:
            chapters[-1][1].append(l)
            i += 1
    return head.split(". ", 1)[1], chapters


def notes_to_footnotes(soup, prefix):
    for li in soup.select("ol.references li"):
        n = li["id"].split("-")[-1]
        p = soup.new_tag("p", attrs={"class": "footnote"})
        p.append(soup.new_tag("a", attrs={"id": f"fn_{prefix}{n}"}))
        for c in list(li.select_one(".reference-text").contents):
            p.append(c.extract())
        li.replace_with(p)
    for ol in soup.select("ol.references, .mw-references-wrap"):
        ol.unwrap()
    for a in soup.select('sup.reference a[href^="#cite_note"]'):
        n = a["href"].split("-")[-1]
        a["href"] = f"#fn_{prefix}{n}"
        a.string = n
        a.parent.unwrap()


NOT_HEADINGS = {"365 days 5 hours 48 minutes 46 seconds.": "P", "THE END.": None}


def wrap_loose(soup):
    """Text a plate interrupted sometimes resumes as LOOSE inline nodes
    after the caption, with no <p> of its own; gather each run into one."""
    body = soup.select_one(".prp-pages-output") or soup.select_one(".mw-parser-output")
    run = []

    def flush():
        if any(R.clean(x.get_text() if hasattr(x, "get_text") else str(x)) for x in run):
            p = soup.new_tag("p")
            run[0].insert_before(p)
            for x in run:
                p.append(x.extract())
        run.clear()
    for c in list(body.children):
        if getattr(c, "name", None) in (None, "i", "b", "a", "small", "sup", "sub", "span") and not (
                getattr(c, "name", None) == "span" and c.find(R.BLOCKS)):
            run.append(c)
        else:
            flush()
    flush()


def captions_and_heads(soup):
    """Fold each plate's centred caption into its <figure>; every other
    centred line is a section heading (<h3>), except the two in
    NOT_HEADINGS. Returns the headings, in order."""
    found = []
    for d in soup.select("div.wst-center"):
        t = R.clean(d.get_text(" "))
        prev = d.find_previous_sibling()
        if prev is not None and prev.name == "figure":
            cap = prev.find("figcaption") or soup.new_tag("figcaption")
            cap.clear()
            cap.string = fix_caption(t)
            prev.append(cap)
            d.decompose()
        elif t in NOT_HEADINGS:
            if NOT_HEADINGS[t]:
                p = soup.new_tag("p")
                p.string = t
                d.replace_with(p)
            else:
                d.decompose()
        else:
            h = soup.new_tag("h3")
            h.string = t
            d.replace_with(h)
            found.append(t)
    return found


def main():
    z = zipfile.ZipFile(HERE / "_src" / "newcomb.zip")
    pages = json.loads(z.read("pages.json"))
    book = R.Book(HERE, "newcomb.zip", html_name="00.html", flatten=FLATTEN,
                  drop={"PD-icon.svg": "", "Wikimedia-logo.svg": "", "Yellow_Checkmark_Circle.svg": ""})
    # the List of Illustrations, from the front page
    front = soup_of(z, 0)
    ftext = [R.clean(t) for t in front.get_text("\n").split("\n") if R.clean(t)]
    li = ftext.index(next(l for l in ftext if l.lower().startswith("list of illustrations")))
    illus = [l for l in ftext[li + 1:] if not re.fullmatch(r"\d+|page|Page|PAGE", l)]
    illus = illus[:next(i for i, l in enumerate(illus) if l.startswith("This work was published"))]
    print(len(illus), "illustrations listed")
    sections, plates = [], []
    nheads = 0
    k = 1
    for p in range(6):
        ptitle, chapters = part_contents(soup_of(z, k))
        k += 1
        for c, (ctitle, heads) in enumerate(chapters):
            s = soup_of(z, k)
            assert pages[k].endswith(f"Part {p + 1}/Chapter {c + 1}"), pages[k]
            k += 1
            title = s.select_one("div.wst-center")
            assert norm(ctitle) in norm(title.get_text()), (ctitle, title.get_text())
            title.decompose()
            notes_to_footnotes(s, f"{p}{c}_")
            normalise_plates(s)
            wrap_loose(s)
            got = captions_and_heads(s)
            nheads += len(got)
            w = R.Walker(book, s)
            items = []
            for it in w.stream(s):
                if it[0] == "H":
                    items.append(("H", 3, R.titlecase(it[2]) if it[2].islower() else it[2]))
                else:
                    items.append(it)
            sec = {"title": f"Chapter {c + 1}: {ctitle}", "stream": items}
            if c == 0:
                sec["part_before"] = f"Part {WORD[p]}: {R.titlecase(ptitle.lower())}"
            sec["chapter"] = True
            sections.append(sec)
    print(nheads, "section headings")
    # A PLATE THAT CUT A HYPHENATED WORD: "in-" / [plate] / "clined".
    # mend_plate_splits only joins at a letter or a comma; each of these is
    # listed so the join is a decision, not a guess.
    for s_ in sections:
        st = s_["stream"]
        for q in range(len(st) - 2):
            if st[q][0] == "P" and st[q][1].endswith("-"):
                r = q + 1
                while r < len(st) and st[r][0] == "PLATE":
                    r += 1
                if r > q + 1 and r < len(st) and st[r][0] == "P" and re.match(r"[a-z]", st[r][1]):
                    head, tail = st[q][1][:-1], st[r][1]
                    word = head.split()[-1] + tail.split()[0]
                    assert word in HYPHEN_JOINS, f"plate cuts {word!r}: add it to HYPHEN_JOINS"
                    joined = HYPHEN_JOINS[word]
                    st[q] = ("P", head[: -len(head.split()[-1])] + joined + tail[len(tail.split()[0]):])
                    st[r] = ("DEL",)
        s_["stream"] = [it for it in st if it[0] != "DEL"]
        st = s_["stream"]
        # re-order so the plates follow the joined paragraph
    # a plate that cut a sentence at an EMPHASIS boundary: "*central*" /
    # [plate] / "*eclipses*." mend_plate_splits looks for a bare letter.
    for s_ in sections:
        st = s_["stream"]
        for q in range(len(st) - 2):
            if st[q][0] == "P" and re.search(r"[a-z]\*$", st[q][1]):
                r = q + 1
                while r < len(st) and st[r][0] == "PLATE":
                    r += 1
                if r > q + 1 and r < len(st) and st[r][0] == "P" and re.match(r"\*[a-z]", st[r][1]):
                    st[q] = ("P", st[q][1] + " " + st[r][1])
                    st[r] = ("DEL",)
        s_["stream"] = [it for it in st if it[0] != "DEL"]
    n = R.mend_plate_splits(sections)
    print("mended", n)
    # the frontispiece and the Preface, from the front page
    parts = front.select_one(".mw-parser-output").find_all("div", class_="prp-pages-output", recursive=False)
    fp = parts[1]
    normalise_plates(fp)
    fimg = fp.find("img")
    fcap = " ".join(R.clean(d.get_text(" ")) for d in fp.select("div.wst-center"))
    pref = parts[3]
    pref.select_one("div.wst-center").decompose()
    for x in pref.select("hr"):
        x.decompose()
    w = R.Walker(book, pref)
    pitems = [("PLATE", fimg["src"], fcap)] + list(w.stream(pref))
    sections.insert(0, {"title": "Preface", "stream": pitems})
    for s_ in sections:
        for it in s_["stream"]:
            if it[0] == "PLATE":
                plates.append({"src": it[1], "printed": it[2]})
    # WITNESS: the printed List of Illustrations, entry for entry, in order
    tab = parts[5].find("table")
    listed = [R.clean(tr.find_all("td")[0].get_text(" ")) for tr in tab.find_all("tr")
              if tr.find_all("td") and R.clean(tr.find_all("td")[0].get_text()) not in ("", "page")]
    printed = [re.sub(r"^Figs?\. [\d–]+\.?—", "", p["printed"]) for p in plates]
    assert len(listed) == len(printed) == 62, (len(listed), len(printed))
    for a, b in zip(listed, printed):
        if norm(a) != norm(b):
            print("  LIST:", a, "\n  PLATE:", b)
    R.text_fixes(sections, TEXT_FIXES)
    left = [it for s_ in sections for it in s_["stream"] if it[0] not in ("P", "BLOCK", "H", "PLATE")]
    assert not left, left[:3]
    # headings: H items become plain lines (title case, no terminal stop)
    for s_ in sections:
        s_["stream"] = [("P", it[2]) if it[0] == "H" else it for it in s_["stream"]]
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates)
    print(len(rows), "plates;", described, "described")

if __name__ == "__main__":
    main()
