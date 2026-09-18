"""Zitkala-Ša, Old Indian Legends (1901): a RESTORED EDITION.

    python3 old-indian-legends/prep.py

Gutenberg #338 for the text; Archive.org's scan of the Ginn & Company
printing (`oldindianlegends00zitkrich`, the 1902 impression of the 1901
edition) for everything Gutenberg left out. The collection's first book by
a woman, and its first by a Native American author: fourteen Dakota
legends told to her by the old story-tellers "in both Dakotas, North and
South".

GUTENBERG DROPPED THREE THINGS, and all three are restored here.
  1. THE PREFACE. Only its signature survives in the transcription, as a
     garbled heading "ITKALA-SA." (the Z was a drop initial). It is typed
     here from the page images, leaves v-vi, and CHECKED AGAINST THE SCAN'S
     OCR, which is a reading that shares no code or keystrokes with this
     file: letter for letter, after the page furniture is removed. The OCR
     misreads the initial I of "Iya" as l, and that is the only allowance.
  2. ANGEL DE CORA'S FOURTEEN PLATES. De Cora (Hinook-Mahiwi-Kilinaka) was
     Winnebago, trained under Howard Pyle, and made these for the book.
     They are cut from the scan's full-resolution page images by the plate
     rectangle itself -- the halftone is much darker than the paper, and
     its edges are sharp -- never with a fixed margin.
  3. THE PRINTED CAPTIONS. Each plate is captioned with a line from the
     story. Transcribed from under the plate (the List of Illustrations
     differs in small ways -- "savory odors" -- and the plate is what the
     reader sees), then placed after the ONE paragraph that contains the
     line, which is asserted. That is the second witness to every caption.
     The frontispiece says "(See page 89)" and is placed at page 89's
     paragraph instead, since a reflowable book has no page 89.

THE TEXT WAS COMPARED WITH THE SCAN WORD BY WORD, and with a second 1901
copy (`oldindianlegends01zitk`) where they disagreed. Gutenberg's
transcription is faithful except for two silent normalisations, reversed
in SOURCE_FIXES because both copies print the other reading: "Dumfounded"
and "hand's-breadth". The one large difference the diff reported (300
words of Iya, the Camp-Eater) is a page scanned twice in the Archive.org
copy, not a gap in Gutenberg.

A DROP CAPITAL PLUS SMALL CAPITALS opens every legend and the transcription
writes it as an all-caps word ("IKTOMI is a spider fairy"). Typography, not
text, and `se lint` t-048 rejects it: the first word only is recased.

MODERN_CHAPTERS/ IS COMPOSED from chapters/ plus captions/*.txt, as in the
other restored editions, so verify's ratio holds at 1.00 by construction
and sees nothing prep got wrong. The raw-HTML word count is the witness
that does.
"""
import io
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
SCAN = SRC / "scan"
IMAGES = ROOT / "site" / "images" / "old-indian-legends"
PIN = HERE / "plates.json"
BOOK = "338"
SCAN_ID = "oldindianlegends00zitkrich"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
LONG_SIDE = 1800
SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or", "as", "from", "into"}

# The printed Contents, page vii of the scan.
PRINTED_CONTENTS = [
    "Iktomi and the Ducks", "Iktomi's Blanket", "Iktomi and the Muskrat",
    "Iktomi and the Coyote", "Iktomi and the Fawn", "The Badger and the Bear",
    "The Tree-Bound", "Shooting of the Red Eagle", "Iktomi and the Turtle",
    "Dance in a Buffalo Skull", "The Toad and the Boy", "Iya, the Camp-Eater",
    "Manstin, the Rabbit", "The Warlike Seven",
]

# (scan leaf, the caption printed under the plate), in book order. The
# leaf is the index in the scan's _jp2.zip.
PLATES = [
    (8, "This was a sign of gratitude used when words failed to interpret "
        "strong emotion"),
    (29, "He sniffed impatiently the savory odor"),
    (39, "“Great-grandfather, give me meat to eat!”"),
    (49, "The muskrat began to feel awkward"),
    (65, "A shower of red coals upon Iktomi's bare arms and shoulders"),
    (79, "There among them stood Iktomi in brown buckskins"),
    (91, "Over a bed of coals she broiled the venison"),
    (127, "He placed the arrow on the bow"),
    (135, "“My friend, you are a skilled hunter”"),
    (147, "Tiny field mice were singing and dancing in a circle"),
    (159, "A little boy stopped his play among the grasses"),
    (171, "The proud chieftain rose with the little baby in his arms"),
    (187, "“I am going to the North Country on a long hunt”"),
    (205, "He blew the water all over the people"),
]

# A printed caption that DEPARTS FROM THE SENTENCE IT QUOTES, placed by the
# sentence instead. The caption stands as printed.
PRINTED_DIFFERS = {
    147: ("Tiny little field mice were singing and dancing in a circle",
          "the plate drops 'little'; the story has 'Tiny little field mice'"),
    159: ("a little wild boy stopped his play among the tall grasses",
          "the plate drops 'wild' and 'tall'"),
}

# Gutenberg -> as printed. Both 1901 copies agree on the printed reading.
SOURCE_FIXES = [
    ("Dumbfounded", "Dumfounded"),
    ("handsbreadth", "hand's-breadth"),
]

# Typed from the page images, leaves 11-12 (printed pages v-vi).
PREFACE = [
    "These legends are relics of our country's once virgin soil. These and "
    "many others are the tales the little black-haired aborigine loved so "
    "much to hear beside the night fire.",
    "For him the personified elements and other spirits played in a vast "
    "world right around the center fire of the wigwam.",
    "Iktomi, the snare weaver, Iya, the Eater, and Old Double-Face are not "
    "wholly fanciful creatures.",
    "There were other worlds of legendary folk for the young aborigine, such "
    "as “The Star-Men of the Sky,” “The Thunder Birds Blinking Zigzag "
    "Lightning,” and “The Mysterious Spirits of Trees and Flowers.”",
    "Under an open sky, nestling close to the earth, the old Dakota "
    "story-tellers have told me these legends. In both Dakotas, North and "
    "South, I have often listened to the same story told over again by a new "
    "story-teller.",
    "While I recognized such a legend without the least difficulty, I found "
    "the renderings varying much in little incidents. Generally one helped "
    "the other in restoring some lost link in the original character of the "
    "tale. And now I have tried to transplant the native spirit of these "
    "tales—root and all—into the English language, since America in the last "
    "few centuries has acquired a second tongue.",
    "The old legends of America belong quite as much to the blue-eyed little "
    "patriot as to the black-haired aborigine. And when they are grown tall "
    "like the wise grown-ups may they not lack interest in a further study of "
    "Indian folklore, a study which so strongly suggests our near kinship "
    "with the rest of humanity and points a steady finger toward the great "
    "brotherhood of mankind, and by which one is so forcibly impressed with "
    "the possible earnestness of life as seen through the teepee door! If it "
    "be true that much lies “in the eye of the beholder,” then in the "
    "American aborigine as in any other race, sincerity of belief, though it "
    "were based upon mere optical illusion, demands a little respect.",
    "After all he seems at heart much like other peoples.",
    "Zitkala-Ša.",
]
# Page furniture inside the OCR'd preface: folios, the running head, and a
# library accession stamp.
PREFACE_FURNITURE = ["M182702", "Preface", "vi", "V"]


def fetch():
    SRC.mkdir(exist_ok=True)
    p = SRC / f"pg{BOOK}-h.zip"
    if not p.exists():
        url = f"https://www.gutenberg.org/cache/epub/{BOOK}/pg{BOOK}-h.zip"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=300) as r:
            p.write_bytes(r.read())
    djvu = SRC / "oil-djvu.txt"
    if not djvu.exists():
        url = f"https://archive.org/download/{SCAN_ID}/{SCAN_ID}_djvu.txt"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=300) as r:
            djvu.write_bytes(r.read())
    return zipfile.ZipFile(p), djvu.read_text(errors="replace")


def leaf(n):
    SCAN.mkdir(parents=True, exist_ok=True)
    dest = SCAN / f"{n:04d}.jp2"
    if not dest.exists():
        url = (f"https://archive.org/download/{SCAN_ID}/{SCAN_ID}_jp2.zip/"
               f"{SCAN_ID}_jp2%2F{SCAN_ID}_{n:04d}.jp2")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=300) as r:
            data = r.read()
        if len(data) < 20_000:
            raise SystemExit(f"leaf {n} came back as {len(data)} bytes")
        dest.write_bytes(data)
    from PIL import Image
    return Image.open(dest).convert("L")


def plate_box(im):
    """The halftone rectangle, found from its own edges.

    Average the brightness across a central band, then take the LONGEST run
    darker than the paper. The paper reads ~249 and the plate's lightest
    passages (smoke, sky) stay under ~232, while the page's gutter shading
    and the library's perforated stamp make only short runs. The same test
    across, restricted to the plate's rows, gives the sides.
    """
    W, H = im.size
    px = im.load()

    def longest(profile):
        paper = sorted(profile)[int(len(profile) * 0.95)]
        runs, s = [], None
        for i, v in enumerate(profile + [255]):
            if v < paper - 12:
                s = i if s is None else s
            elif s is not None:
                runs.append((s, i))
                s = None
        return max(runs, key=lambda r: r[1] - r[0])

    band = range(W // 2 - 300, W // 2 + 300, 6)
    top, bot = longest([sum(px[x, y] for x in band) / len(band)
                        for y in range(H)])
    rows = range(top + 100, bot - 100, 6)
    left, right = longest([sum(px[x, y] for y in rows) / len(rows)
                           for x in range(W)])
    inset = 6
    return left + inset, top + inset, right - inset, bot - inset


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def titlecase(s):
    words = clean(s).lower().split()
    return " ".join(w if i and w in SMALL else
                    "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
                    for i, w in enumerate(words))


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]+", " ", s.lower()).strip()


def letters(s):
    return norm(s).replace(" ", "")


def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, Comment):
            continue                       # "<!--  H2 anchor -->"
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name == "br":
                out.append(" ")
            elif c.name in ("i", "em"):
                out.append(f"*{inline(c)}*")
            else:
                out.append(inline(c))
    return "".join(out)


def emph_safe(text):
    """Keep only the asterisks assemble.EMPH renders (see aesop/prep.py)."""
    sys.path.insert(0, str(ROOT))
    import assemble
    keep = []

    def hold(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"
    held = assemble.EMPH.sub(hold, text).replace("*", "")
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], held)


def check_preface(djvu):
    """The typed preface against the scan's OCR, letter for letter."""
    s = djvu.index("PREFACE")
    e = djvu.index("CONTENTS", s)
    lines = [ln.strip() for ln in djvu[s + len("PREFACE"):e].splitlines()]
    ocr = " ".join(ln for ln in lines if ln and ln not in PREFACE_FURNITURE)
    ocr = re.sub(r"\blya\b", "Iya", ocr)          # the OCR's one misreading
    typed = letters(" ".join(PREFACE))
    got = letters(ocr)
    if typed != got:
        i = next(k for k in range(min(len(typed), len(got)))
                 if typed[k] != got[k])
        raise SystemExit(f"preface disagrees with the scan at letter {i}: "
                         f"typed {typed[i-20:i+20]!r} / scan {got[i-20:i+20]!r}")


def main():
    z, djvu = fetch()
    check_preface(djvu)
    html = z.read([n for n in z.namelist() if n.endswith(".html")][0]).decode(
        "utf-8", "replace")
    for bad, good in SOURCE_FIXES:
        assert html.count(bad) == 1, (bad, html.count(bad))
        html = html.replace(bad, good)
    s = html.index("</header>", html.index("*** START")) + len("</header>")
    e = html.index('<footer class="pg-boilerplate')
    soup = BeautifulSoup(html[s:e], "html.parser")

    # ---- witness 1: the book's own Contents
    toc = [clean(a.get_text()) for p in soup.select("p.toc")
           for a in p.find_all("a")]
    assert toc[0] == "OLD INDIAN LEGENDS", toc[0]
    assert [titlecase(t) for t in toc[1:]] == PRINTED_CONTENTS, toc

    legends, h1s = [], 0
    for el in soup.children:
        if not isinstance(el, Tag):
            if clean(str(el)):
                raise SystemExit(f"loose text: {clean(str(el))[:60]!r}")
            continue
        if el.name == "h1":
            h1s += 1
            continue
        if h1s < 2:
            continue                       # title page, garbled signature, contents
        if el.name == "h2":
            legends.append({"title": titlecase(el.get_text()), "paras": []})
            continue
        if el.name == "hr":
            continue
        if el.name == "div" and not clean(el.get_text()):
            continue                       # "height: 4em" spacers of <br>
        if el.name == "pre":
            assert not clean(el.get_text()), "text in a <pre>"
            continue
        if el.name == "p":
            t = emph_safe(clean(inline(el)))
            if not t:
                continue                   # spacer and anchor paragraphs
            if not legends:
                raise SystemExit(f"text before the first legend: {t[:60]!r}")
            if not legends[-1]["paras"]:
                # the drop capital and small capitals, as an all-caps word
                t = re.sub(r"^([“‘\"']?[A-Z])([A-Z]+(?:'[A-Z]+)?)\b",
                           lambda m: m.group(1) + m.group(2).lower(), t)
            legends[-1]["paras"].append(t)
            continue
        raise SystemExit(f"unhandled <{el.name}>")
    assert [x["title"] for x in legends] == PRINTED_CONTENTS, \
        [x["title"] for x in legends]

    # ---- witness 2: the raw HTML's word count, tags stripped
    raw = html[html.index('id="link2H_4_0003"'):e]
    raw = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    raw_words = len(re.sub(r"<[^>]+>", " ", raw).split()) - 1   # the id attr's tail
    got = sum(len(x["title"].split()) + sum(len(p.split()) for p in x["paras"])
              for x in legends)
    assert abs(raw_words - got) <= 0.005 * raw_words, (raw_words, got)

    # ---- plates: each after the one paragraph that holds its caption
    L = "abcdefghijklmnopqrstuvwxyz"
    rows = [{"id": L[i // 26] + L[i % 26], "leaf": n, "printed": cap}
            for i, (n, cap) in enumerate(PLATES)]
    if PIN.exists():
        old = json.loads(PIN.read_text())
        assert [(r["id"], r["leaf"]) for r in old] == \
               [(r["id"], r["leaf"]) for r in rows], "plate ids moved"
    PIN.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    placed = {}
    for r in rows:
        key = norm(PRINTED_DIFFERS.get(r["leaf"], (r["printed"],))[0])
        hits = [(li, pi) for li, x in enumerate(legends)
                for pi, p in enumerate(x["paras"]) if key in norm(p)]
        assert len(hits) == 1, (r["id"], r["printed"], hits)
        placed.setdefault(hits[0], []).append(r)
    # Book order, except the frontispiece: it faces the title page in print
    # and is placed at the passage its "(See page 89)" points to.
    order = sorted(placed)
    assert [r["id"] for k in order for r in placed[k] if r["leaf"] != 8] == \
           [r["id"] for r in rows if r["leaf"] != 8], "plates out of book order"

    IMAGES.mkdir(parents=True, exist_ok=True)
    for old in IMAGES.iterdir():
        old.unlink()
    for r in rows:
        im = leaf(r["leaf"])
        box = plate_box(im)
        w, h = box[2] - box[0], box[3] - box[1]
        assert 1400 < w < 2200 and 1700 < h < 2700, (r["id"], box)
        plate = im.crop(box)
        plate.thumbnail((LONG_SIDE, LONG_SIDE))
        plate.save(IMAGES / f"fig{r['id']}.jpg", "JPEG", quality=85)
        r["box"] = box

    # ---- compose
    captions = {}
    for f in sorted((HERE / "captions").glob("*.txt")) if (HERE / "captions").is_dir() else []:
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                k, _, v = line.partition("\t")
                if k.strip() in captions:
                    raise SystemExit(f"{f.name}: {k.strip()} captioned twice")
                captions[k.strip()] = v.strip()
    unknown = set(captions) - {r["id"] for r in rows}
    assert not unknown, unknown
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    sections = [("Preface", [(None, p) for p in PREFACE])]
    for li, x in enumerate(legends):
        stream = []
        for pi, p in enumerate(x["paras"]):
            stream.append((None, p))
            for r in placed.get((li, pi), []):
                stream.append((r, None))
        sections.append((x["title"], stream))
    manifest, described = [], 0
    for idx, (title, stream) in enumerate(sections):
        src, mod = [title, ""], [title, ""]
        for r, p in stream:
            if r is None:
                src.append(p)
                mod.append(p)
            else:
                desc = captions.get(r["id"], "")
                described += bool(desc)
                cap = " — ".join(y for y in (r["printed"], desc) if y)
                src.append(f"[Figure {r['id']}]")
                mod.append(f"[Figure {r['id']}: {cap}]")
            src.append("")
            mod.append("")
        (HERE / "chapters" / f"{idx:03d}.txt").write_text(
            "\n".join(src).rstrip() + "\n")
        (HERE / "modern_chapters" / f"{idx:03d}.txt").write_text(
            "\n".join(mod).rstrip() + "\n")
        manifest.append({"file": f"{idx:03d}.txt", "title": title,
                         "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"preface + {len(legends)} legends, {got:,} words "
          f"(raw HTML {raw_words:,}); {len(rows)} plates placed, "
          f"{described}/{len(rows)} described")


if __name__ == "__main__":
    main()
