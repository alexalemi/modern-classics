"""Worthington's splash books: the collection's FIRST NATIVE RESTORED EDITION.

    python3 worthington/prep.py

TWO WORKS IN ONE VOLUME, from Project Gutenberg's HTML editions, which
carry the plates the plain text drops:

    #39831  A Study of Splashes (1908)     11 chapters, 218 plates
    #27125  The Splash of a Drop (1895)    one discourse, 29 plates

The 1908 book is the full account. The Splash of a Drop is the Friday
Evening Discourse Worthington gave at the ROYAL INSTITUTION on 18 May
1894, printed in 1895 in the SPCK's "Romance of Science" series -- the
ninth Royal Institution volume in the collection. They complement rather
than repeat: the 1908 Preface says the lecture "dealt largely with the
splash of a drop falling on a solid plate, with which the present volume
is not concerned". Dover's 1963 reprint put the book first and the
lecture after, and so does this edition.

A RESTORED EDITION, NOT A RETELLING (ROADMAP.md, "A second strand").
Worthington's prose screens at arch 0.00 / calq 25.4, cleaner than any
book this project has modernised, so nobody rewrites it. What the edition
adds is the apparatus: a caption and alt text for every plate. The source
has an EMPTY alt attribute on every one of its 247 plates.

MODERN_CHAPTERS/ IS COMPOSED, NEVER TYPED. chapters/ holds the prose with
bare markers; modern_chapters/ is the same files with each marker filled
from plates.json (the label the book printed) and captions.txt (the
description this edition writes). Nobody retypes 28,000 words of
Worthington to add captions to them, so the prose cannot drift -- and
verify.py's word ratio, the loosest check in the project, becomes an
EQUALITY TEST that holds by construction. Both directories open with the
same heading line for the same reason.

THE FILENAME DOES NOT TELL YOU WHAT THE PLATE IS. Found by opening them:
`fig-a` and `fig-b` are photographs; `plate-i` is a line diagram sitting
among the photographic plates while `plate-ii` is a photograph; fig-15a/b
are diagrams stored as JPEG, which is why the PNG figures skip 15.

TRAPS, each with a ruling earned elsewhere in this repo:
  1. Every photograph exists as `-f` (full) and `-t` (thumbnail). Only the
     full is extracted -- shipping both doubled thompson's epub to 51 MB.
  2. Figures 15a and 15b are printed in REVERSED order (15b first), the
     symbolic-logic floated-diagram trap. FLIPPED, asserted once.
  3. 197 mid-height decimal points (0·002 sec.) are MEASURED VALUES and
     pass through untouched (pillow-problems).
  4. A PAGE-105 COMPOSITE shows one plate twice. Order comes from a plate's
     FIRST appearance; its printed label from whichever appearance has one.
  5. Italics glued to a word ("15<i>a</i>") cannot become emphasis: EMPH
     refuses a delimiter after a word character and would ship literal
     asterisks. Such spans are emitted plain.

THE PLATE COUNT, recorded rather than smoothed over. The title page says
"WITH 197 ILLUSTRATIONS FROM INSTANTANEOUS PHOTOGRAPHS"; the source
carries 194 photographs. The book has NO list of illustrations. Two
witnesses were tried: Archive.org's ABBYY picture blocks (238, and they do
not align with printed pages -- ABBYY block types lie, the euclid-rivals
lesson) and the book's OWN SERIAL NUMBERING, which counts up without a
hole in every series. So no plate is missing from inside a numbered
series; the three-plate difference is unexplained, and it is not a gap a
reader would meet.

IDS. assemble.figure_label prints "Figure N" from an id's digits, and this
book has no single figure sequence. Numbered diagrams keep their numbers
("15a" -> "Figure 15a"); every photograph takes a DIGIT-FREE id ('aa',
'ab', ...) so its caption stands alone, beginning with the label the book
printed ("11 a  0·139 sec."). THE MAP IS PINNED in plates.json and
asserted on every run, or a re-run could renumber 247 plates out from
under 247 written captions without any marker failing to resolve.
"""
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
IMAGES = ROOT / "site" / "images" / "worthington"
PIN = HERE / "plates.json"
CAPTIONS = HERE / "captions.txt"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}

STUDY, DROP = "39831", "27125"
CLAIMED_PHOTOGRAPHS = 197
PHOTOGRAPHS = 194           # derived once and pinned; see the docstring

PLATE_KIND = {
    "fig-a": "photo",       # a cavity beside a millimetre scale
    "fig-b": "photo",
    "plate-i": "diagram",   # the apparatus, laboratory and dark room
    "plate-ii": "photo",
}
NAMED_DIAGRAMS = {"plate-i": "plate-one", "fig-p033-water": "water-drop",
                  "fig-p033-turp": "turpentine-drop"}
FLIPPED = ("fig-15b", "fig-15a")

TITLES = {
    1: "Preliminary—Methods of Observation and Apparatus",
    2: "The Splash of a Drop—Low Fall",
    3: "Principles Involved",
    4: "The Splash Continued",
    5: "Higher Falls—Bubble-Building",
    6: "Below the Surface",
    7: "The Two Kinds of Splashes of Solid Spheres",
    8: "The Transition from the Smooth or “Sheath” Splash to the "
       "Rough or “Basket” Splash",
    9: "The Explanation of the Cause of Difference Between the Two Splashes",
    10: "Conclusion",
    11: "A New Phenomenon That Appears with an Increase in the Velocity of "
        "Entry of a Rough Sphere",
}
ROMAN = {r: i for i, r in enumerate(
    "I II III IV V VI VII VIII IX X XI".split(), 1)}


# ------------------------------------------------------------ source


def fetch(book_id):
    SRC.mkdir(exist_ok=True)
    path = SRC / f"pg{book_id}-h.zip"
    if not path.exists():
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-h.zip"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=300) as r:
            path.write_bytes(r.read())
    return zipfile.ZipFile(path)


def body_soup(z):
    h = z.read([n for n in z.namelist() if n.endswith(".html")][0]).decode(
        "utf-8", "replace")
    s = h.index("*** START")
    s = h.index(">", h.index("</div>", s)) + 1
    e = h.index("*** END")
    e = h.rindex("<div", 0, e)
    return BeautifulSoup(h[s:e], "html.parser")


def stem_of(src):
    base = re.sub(r"\.(jpg|jpeg|png|gif)$", "", src.split("/")[-1], flags=re.I)
    return re.sub(r"-[ft]$", "", base)


def kind_of(stem):
    if stem in PLATE_KIND:
        return PLATE_KIND[stem]
    return "photo" if stem.startswith("photo-") else "diagram"


# ------------------------------------------------------------ inline text


WORD = re.compile(r"\w")


def inline(el):
    """Text of an element with the house's only markup, *emphasis*."""
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            cls = c.get("class") or []
            if c.name == "br":
                out.append(" ")
            elif "pagenum" in cls:
                continue
            elif c.name in ("i", "em"):
                inner = inline(c)
                prev = "".join(out)[-1:]
                nxt = c.next_sibling
                nxt = (str(nxt)[:1] if isinstance(nxt, NavigableString)
                       else "")
                glued = WORD.match(prev or " ") or WORD.match(nxt or " ")
                if inner.strip() and inner == inner.strip() \
                        and "*" not in inner and not glued:
                    out.append(f"*{inner}*")
                else:
                    out.append(inner)
            else:
                out.append(inline(c))
    return "".join(out)


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


# ------------------------------------------------------------ plates


def plain(el):
    """A printed label as plain text: no emphasis markers, and no square
    brackets, which would close a [Figure id: ...] marker early."""
    t = clean(el.get_text(" ") if isinstance(el, Tag) else str(el))
    return t.replace("[", "(").replace("]", ")")


def cell_stems(cell):
    out = []
    for a in cell.find_all(["a", "img"]):
        s = a.get("href") or a.get("src")
        if s and re.search(r"images/.*\.(jpg|png)$", s):
            st = stem_of(s)
            if st != "cover" and st not in out:
                out.append(st)
    return out


def plate_cells(block):
    """[(stem, printed label, block title)] in first-seen order.

    THREE LAYOUTS, all in this book, and a label must be paired with ITS
    plate in each:
      a. label then plate in the same row      ("11 0·139 sec." | img)
      b. a row of plates, then a row of labels beneath, paired by column
      c. a plate in a div with its caption as the div's own text
    A row holding one text cell and no plate is the block's TITLE
    ("SERIES I  Milk into water (40 cm.). Scale 3/4.") and belongs to every
    plate in the block, never to the first one. The page-105 composite
    shows one plate twice: order comes from its FIRST appearance, the
    label from whichever appearance has one.
    """
    order, label, title = [], {}, []
    if block.name != "table":
        titles = [i.get("title", "").strip() for i in block.find_all("img")]
        own = BeautifulSoup(str(block), "html.parser")
        for x in own.find_all(["a", "img"]):
            x.decompose()
        text = plain(own)
        for k, st in enumerate(cell_stems(block)):
            order.append(st)
            # the lecture's plates have no caption text, only an img title
            # ("First Series 1 through 6")
            alt = titles[k] if k < len(titles) else ""
            label.setdefault(st, text or alt)
        return [(st, label.get(st, ""), "") for st in order]
    rows = [tr for tr in block.find_all("tr") if tr.find_parent("table") is block]
    grid = [tr.find_all("td", recursive=False) for tr in rows]
    for r, cells in enumerate(grid):
        has_img = [bool(cell_stems(c)) for c in cells]
        if not any(has_img):
            texts = [plain(c) for c in cells if plain(c)]
            if len(texts) == 1 and (r + 1 < len(grid) and any(
                    cell_stems(c) for c in grid[r + 1])) and \
                    not re.fullmatch(r"\d+\s?[a-z]?\b.*", texts[0]):
                title.append(texts[0])
            continue
        text_in_row = not all(has_img)
        below = grid[r + 1] if r + 1 < len(grid) else []
        below_is_labels = below and not any(cell_stems(c) for c in below)
        for c, cell in enumerate(cells):
            nested = [t for t in cell.find_all("table")
                      if t.find_parent("table") is block]
            if nested:
                # A cell holding a NESTED TABLE of several plates. Taking the
                # cell's text as each plate's label gave every one of Series
                # I's nine photographs the whole row "1 2 T = 0 3 0·002 sec.
                # ..." -- present, and wrong, which is worse than absent.
                # EVERY top-level nested table in the cell, and any plate
                # outside them: following only the first dropped 16 plates,
                # which the exactly-once assertion caught.
                for inner in nested:
                    for st, lab, _ in plate_cells(inner):
                        if st not in order:
                            order.append(st)
                        if lab and not label.get(st):
                            label[st] = lab
                loose = BeautifulSoup(str(cell), "html.parser")
                for t in loose.find_all("table"):
                    t.decompose()
                for st in cell_stems(loose):
                    if st not in order:
                        order.append(st)
                continue
            for st in cell_stems(cell):
                if st not in order:
                    order.append(st)
                lab = ""
                if text_in_row and c > 0 and not has_img[c - 1]:
                    lab = plain(cells[c - 1])
                elif not text_in_row and below_is_labels and c < len(below):
                    lab = plain(below[c])
                if not lab:
                    # d. the label inside the SAME cell as its plate
                    #    (<td><img><p>Fig. 1</p></td>, and Series I's
                    #    "2  T = 0" under each photograph)
                    own = BeautifulSoup(str(cell), "html.parser")
                    for x in own.find_all(["a", "img"]):
                        x.decompose()
                    lab = plain(own)
                if lab and not label.get(st):
                    label[st] = lab
    t = " ".join(title)
    if len(order) == 1 and not label.get(order[0]) and t:
        label[order[0]] = t        # Plate II: its title is its only label
    return [(st, label.get(st, ""), t) for st in order]


def has_plate(el):
    return any(re.search(r"images/.*\.(jpg|png)$", a.get("href") or
                         a.get("src") or "")
               and stem_of(a.get("href") or a.get("src")) != "cover"
               for a in el.find_all(["a", "img"]))


# ------------------------------------------------------------ walking


def walk(nodes, book, stream):
    """Append ('P', text) | ('PLATE', stem, label, book) | ('BLOCK', text)."""
    for el in nodes:
        if isinstance(el, NavigableString) or not isinstance(el, Tag):
            continue
        cls = el.get("class") or []
        if el.name in ("header", "footer", "section") or \
                any(c.startswith("pg-") or c.startswith("pg") and "boilerplate"
                    in " ".join(cls) for c in cls):
            continue                 # Project Gutenberg's own furniture
        if el.name == "table" or (el.name == "div" and has_plate(el)
                                  and not el.find("table")
                                  and ("figcenter" in cls or "center" in cls)):
            if has_plate(el):
                for st, lab, ttl in plate_cells(el):
                    stream.append(("PLATE", st, lab, book, ttl))
            else:
                rows = [" | ".join(clean(inline(td)) for td in tr.find_all(
                    ["td", "th"])) for tr in el.find_all("tr")]
                stream.append(("BLOCK", "\n".join("\t" + r for r in rows)))
            continue
        if "footnotes" in cls:
            for fn in el.find_all("div", class_="footnote"):
                stream.append(("P", "Footnote " + clean(inline(fn))))
            continue
        if el.name == "p":
            t = clean(inline(el))
            if t:
                stream.append(("P", t))
            continue
        if el.name in ("div", "blockquote"):
            walk(el.children, book, stream)
            continue
        if el.name in ("br", "img"):
            continue
        if el.name in ("small", "i", "b", "em", "strong", "sup", "sub"):
            t = clean(inline(el))
            if t:
                stream.append(("P", t))
            continue
        if el.name in ("a", "span"):
            # A bare anchor between blocks is a page or footnote target and
            # carries nothing; a bare PLATE LINK must still be placed, or the
            # exactly-once assertion below would be the first to notice.
            if has_plate(el) or (el.name == "a" and re.search(
                    r"images/.*\.(jpg|png)$", el.get("href") or "")):
                for st, lab, ttl in plate_cells(el):
                    stream.append(("PLATE", st, lab, book, ttl))
            elif clean(el.get_text(" ")) and "pagenum" not in cls:
                stream.append(("P", clean(inline(el))))
            continue
        if el.name in ("h2", "h3", "hr", "ul", "pre"):
            continue
        raise SystemExit(f"unhandled element <{el.name} class={cls}>: "
                         f"{clean(el.get_text(' '))[:80]!r}")


def split_study(soup):
    """{section key: [nodes]} for the 1908 book."""
    heads = soup.find_all("h2")
    sections, current, dedication = {}, None, []
    for el in soup.children:
        if not isinstance(el, Tag):
            continue
        if el.name == "h2":
            t = clean(el.get_text(" "))
            m = re.fullmatch(r"CHAPTER ([IVX]+)", t)
            if t == "PREFACE":
                current = "preface"
            elif m:
                current = ROMAN[m.group(1)]
            else:
                current = None          # CONTENTS, the half title
            if current is not None:
                sections[current] = []
            continue
        if current is None and el.name == "p" and "DEDICATED" in el.get_text():
            dedication.append(el)
        if current is None and el.name == "div" and has_plate(el):
            sections.setdefault("frontispiece", []).append(el)
        if current is not None:
            if el.name == "h3" and "Transcriber" in el.get_text():
                current = None
                continue
            sections[current].append(el)
    return sections, dedication


def split_drop(soup):
    """The discourse: its plate gallery, the lecture, and its footnotes.

    From the first in-body h2 (the half title) to THE END, then the
    footnotes that follow; the printer's line and the SPCK advertisements
    after them are dropped.
    """
    # The first in-body h2 is the half title, and the gallery of the first
    # plates ("INSTANTANEOUS PHOTOGRAPHS OF THE SPLASH OF A WATER-DROP...")
    # sits BETWEEN it and the lecture's own h2. Starting at the second h2
    # dropped image1-3, and the exactly-once assertion is what caught it.
    h2s = soup.find_all("h2")
    start = h2s[0]
    nodes, ended = [], False
    for el in start.next_siblings:
        if not isinstance(el, Tag):
            continue
        t = clean(el.get_text(" "))
        if el.name == "p" and t == "THE END.":
            ended = True
            continue
        if ended:
            if "footnotes" in (el.get("class") or []):
                nodes.append(el)
                break
            continue
        nodes.append(el)
    assert ended, "The Splash of a Drop: no THE END."
    return nodes


# ------------------------------------------------------------ main


def main():
    zs, zd = fetch(STUDY), fetch(DROP)
    study, dedication = split_study(body_soup(zs))
    drop = split_drop(body_soup(zd))
    assert sorted(k for k in study if isinstance(k, int)) == list(range(1, 12))

    files = []                  # (key, heading, part_before, stream)
    ded = [clean(inline(p)) for p in dedication]
    assert len(ded) == 1, ded
    files.append(("dedication", "Dedication", "A Study of Splashes",
                  [("BLOCK", "\t" + ded[0])]))
    pre = []
    walk(study.get("frontispiece", []), STUDY, pre)
    walk(study["preface"], STUDY, pre)
    files.append(("preface", "Preface", None, pre))
    for n in range(1, 12):
        st = []
        walk(study[n], STUDY, st)
        files.append((n, f"Chapter {n}: {TITLES[n]}", None, st))
    dr = []
    walk(drop, DROP, dr)
    files.append(("drop", "The Splash of a Drop", None, dr))

    # ---- plate order, the flip, and the exactly-once assertion
    plates = [(s[1], s[2], s[3], s[4]) for _, _, _, stream in files
              for s in stream if s[0] == "PLATE"]
    stems = [p[0] for p in plates]
    i, j = stems.index(FLIPPED[0]), stems.index(FLIPPED[1])
    assert j == i + 1, "15b/15a no longer adjacent -- re-check the flip"
    for _, _, _, stream in files:
        for k in range(len(stream) - 1):
            if stream[k][0] == "PLATE" and stream[k][1] == FLIPPED[0] \
                    and stream[k + 1][1] == FLIPPED[1]:
                stream[k], stream[k + 1] = stream[k + 1], stream[k]
    plates = [(s[1], s[2], s[3], s[4]) for _, _, _, stream in files
              for s in stream if s[0] == "PLATE"]

    on_disk = {STUDY: set(), DROP: set()}
    for book, z in ((STUDY, zs), (DROP, zd)):
        for n in z.namelist():
            if re.search(r"images/.*(-f\.jpg|\.png|image\d+\.jpg)$", n):
                on_disk[book].add(stem_of(n))
    placed = {STUDY: [p[0] for p in plates if p[2] == STUDY],
              DROP: [p[0] for p in plates if p[2] == DROP]}
    for book in (STUDY, DROP):
        dup = {s for s in placed[book] if placed[book].count(s) > 1}
        assert not dup, f"{book}: placed twice {sorted(dup)}"
        missing = on_disk[book] - set(placed[book])
        extra = set(placed[book]) - on_disk[book]
        assert not missing and not extra, (book, sorted(missing), sorted(extra))
    photos = sum(1 for p in plates if p[2] == STUDY and kind_of(p[0]) == "photo")
    assert photos == PHOTOGRAPHS, f"{photos} photographs, pinned {PHOTOGRAPHS}"

    # ---- ids, pinned
    rows, n_photo = [], 0
    for stem, label, book, ttl in plates:
        key = stem if book == STUDY else f"drop-{stem}"
        if book == STUDY and kind_of(stem) == "diagram":
            m = re.fullmatch(r"fig-0*(\d+[a-z]?)", stem)
            pid = m.group(1) if m else NAMED_DIAGRAMS[stem]
        else:
            pid = ""
            k = n_photo
            while True:
                pid = "abcdefghijklmnopqrstuvwxyz"[k // 26] + \
                      "abcdefghijklmnopqrstuvwxyz"[k % 26]
                break
            n_photo += 1
        rows.append({"id": pid, "source": key, "book": book,
                     "kind": "photo" if book == DROP else kind_of(stem),
                     "printed": label, "block": ttl})
    if PIN.exists():
        old = json.loads(PIN.read_text())
        assert [(r["id"], r["source"]) for r in old] == \
               [(r["id"], r["source"]) for r in rows], \
            "plate ids moved -- captions.txt would describe the wrong plates"
    else:
        PIN.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    by_source = {r["source"]: r for r in rows}
    assert all(not any(c.isdigit() for c in r["id"]) for r in rows
               if r["kind"] == "photo"), "a photograph id carries a digit"

    # ---- images
    IMAGES.mkdir(parents=True, exist_ok=True)
    for old in IMAGES.iterdir():
        old.unlink()
    for book, z in ((STUDY, zs), (DROP, zd)):
        for n in z.namelist():
            if not re.search(r"images/.*(-f\.jpg|\.png|image\d+\.jpg)$", n):
                continue
            st = stem_of(n)
            key = st if book == STUDY else f"drop-{st}"
            if key not in by_source:
                continue
            data, ext = z.read(n), n.rsplit(".", 1)[1].lower()
            if ext == "png":
                # All 22 are grayscale with NO transparency, which `se lint`
                # rejects (f-019); candle's fix is JPEG. Quality is high
                # because these are line drawings, where JPEG ringing shows.
                import io
                from PIL import Image
                im = Image.open(io.BytesIO(data))
                assert im.mode == "L" and "transparency" not in im.info, n
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=95)
                data, ext = buf.getvalue(), "jpg"
            (IMAGES / f"fig{by_source[key]['id']}.{ext}").write_bytes(data)

    # ---- write both directories
    captions = {}
    if CAPTIONS.exists():
        for line in CAPTIONS.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                pid, _, desc = line.partition("\t")
                captions[pid.strip()] = desc.strip()
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest, words, described = [], 0, 0
    for idx, (key, heading, part_before, stream) in enumerate(files):
        src, mod = [heading, ""], [heading, ""]
        for item in stream:
            if item[0] == "PLATE":
                stem, book = item[1], item[3]
                r = by_source[stem if book == STUDY else f"drop-{stem}"]
                src.append(f"[Figure {r['id']}]")
                printed = r["printed"]
                if re.fullmatch(r"\d+[a-z]?", r["id"]):
                    printed = re.sub(rf"^Fig\. ?{r['id']}\b\.?\s*", "",
                                     printed).strip()
                desc = captions.get(r["id"], "")
                described += bool(desc)
                cap = " — ".join(x for x in (printed, desc) if x)
                mod.append(f"[Figure {r['id']}: {cap}]" if cap
                           else f"[Figure {r['id']}]")
            else:
                src.append(item[1])
                mod.append(item[1])
            src.append("")
            mod.append("")
        body = "\n".join(src).rstrip() + "\n"
        words += len(body.split())
        (HERE / "chapters" / f"{idx:03d}.txt").write_text(body)
        (HERE / "modern_chapters" / f"{idx:03d}.txt").write_text(
            "\n".join(mod).rstrip() + "\n")
        entry = {"file": f"{idx:03d}.txt", "title": heading, "part": 1, "of": 1}
        if part_before:
            entry["part_before"] = part_before
        if isinstance(key, int):
            entry["chapter"] = True
        manifest.append(entry)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1,
                                                   ensure_ascii=False) + "\n")
    print(f"{len(files)} files, {words:,} words, {len(rows)} plates "
          f"({photos} photographs in the 1908 book, title page claims "
          f"{CLAIMED_PHOTOGRAPHS}); {described}/{len(rows)} described")


if __name__ == "__main__":
    main()
