"""James Stephens, Irish Fairy Tales (1920): a RESTORED EDITION.

    python3 irish-fairy-tales/prep.py

Gutenberg #2892, with Arthur Rackham's illustrations. Struck from the
retelling roadmap because "modernising it would be like modernising
Yeats"; restored instead (ROADMAP.md, "A second strand").

GUTENBERG DROPPED RACKHAM'S CAPTIONS. Its plates carry alt text like
"001m" and nothing else. The 1920 Macmillan printing lists sixteen colour
plates, each captioned with a sentence from the story, and those survive
in Archive.org's scan (`irishfairytales00steprich`). They are OCR, so each
is checked against Stephens' OWN PROSE near the plate -- the caption
quotes the story, which makes the book a second witness to its own
captions. That witness caught "Guillen" for Cuillen and a welded
"con-tinuous" in the prose itself. It is not infallible: one plate caption
genuinely departs from the sentence it quotes, and that one was settled
against the page image instead (PRINTED_DIFFERS). The frontispiece ("page 250") is exempt from the nearness test
only, since it sits at the front of the book.

38 IMAGES, 37 PLATES. `001` is the book's green cloth CASE, not a plate;
the ebook has its own cover. It is dropped by name and asserted, so a
future source change cannot quietly drop anything else. `013` is Rackham's
drawn title page and is kept. The other 22 are headpieces and drawings
with no printed caption.

STRUCTURE: ten stories, each with its own run of chapters; stories are
part dividers and chapters are sections. The source's `pre` blocks are the
first lines of quoted songs and set as verse. The "Original Size" link
under every plate is Gutenberg furniture and must not reach the text.
Plates are downscaled to 2000px on the long side: the sources are page
scans at up to 2182x2964, and nothing a reader sees needs more.

MODERN_CHAPTERS/ IS COMPOSED from chapters/ plus captions.txt, as in
worthington/ and aesop/. Plate ids are digit-free and pinned.
"""
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
IMAGES = ROOT / "site" / "images" / "irish-fairy-tales"
PIN = HERE / "plates.json"
CAPTIONS = HERE / "captions.txt"
BOOK = "2892"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
STORIES = 10
# A printed caption that DEPARTS FROM THE PROSE it quotes. The prose
# witness cannot settle these, so they were settled against the page image:
# Archive.org irishfairytales00steprich, leaf n19, printed page x.
PRINTED_DIFFERS = {
    "323": "the plate reads 'all the worlds ... one huge green cataract'; "
           "the story reads 'all the world ... one huge, green cataract'",
}
DROPPED = {"001": "the book's cloth case, photographed; not a plate"}
LONG_SIDE = 2000

# Rackham's printed captions, from the 1920 List of Illustrations, in book
# order -- mapped in order onto the portrait plates. None = not yet settled
# against the prose (see the docstring); such plates carry no printed text
# until it is.
COLOUR = [
    ("010", "In a forked glen into which he slipped at night-fall he was "
            "surrounded by giant toads"),
    ("035", "“Wild and shy and monstrous creatures ranged in her plains and "
            "forests”"),
    ("053", "“My life became a ceaseless scurry and wound and escape, a burden "
            "and anguish of watchfulness”"),
    ("069", "He might think, as he stared on a staring horse, “a boy cannot "
            "wag his tail to keep the flies off”"),
    ("079", "How he strained and panted to catch on that pursuing person and "
            "pursue her and get his own switch into action"),
    ("131", "A man who did not like dogs. In fact, he hated them. When he saw "
            "one he used to go black in the face, and he threw rocks at it "
            "until it got out of sight"),
    ("137", "Then they went hand in hand in the country that smells of "
            "apple-blossom and honey"),
    ("161", "The door of Fionn’s chamber opened gently and a young woman came "
            "into the room"),
    ("193", "She looked with angry woe at the straining and snarling horde "
            "below"),
    ("219", "The banqueting hall was in tumult"),
    ("247", "The thumping of his big boots grew as continuous as the pattering "
            "of hailstones on a roof, and the wind of his passage blew trees "
            "down"),                       # OCR "hail- stones", source "con-tinuous"
    ("271", "“This one is fat,” said Cuillen, and she rolled a bulky Fenian "
            "along like a wheel"),         # OCR "Guillen"; the prose says Cuillen
    ("279", "They stood outside, filled with savagery and terror"),
    ("323", "The waves of all the worlds seemed to whirl past them in one huge "
            "green cataract"),
    ("343", "They offered a cow for each leg of her cow, but she would not "
            "accept that offer unless Fiachna went bail for the payment"),
    ("385", "The Hag of the Mill was a bony, thin pole of a hag with odd feet"),
]
SOURCE_FIXES = [
    ("con-tinuous", "continuous"),
]
ROMAN = {r: i for i, r in enumerate(
    "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX"
    .split(), 1)}
SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or"}


def fetch():
    SRC.mkdir(exist_ok=True)
    p = SRC / f"pg{BOOK}-h.zip"
    if not p.exists():
        url = f"https://www.gutenberg.org/cache/epub/{BOOK}/pg{BOOK}-h.zip"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=600) as r:
            p.write_bytes(r.read())
    return zipfile.ZipFile(p)


def emph_safe(text):
    """Remove every asterisk assemble.EMPH would not render.

    An italic letter glued to a number ("Figs. 20<i>a</i>") cannot be
    emphasis -- EMPH refuses a delimiter after a word character -- and a
    test made inside a nested tag cannot see the digit before it. So ask
    the renderer instead of approximating it: keep the spans EMPH matches,
    drop any asterisk left over. 16 of them shipped on the first
    Worthington page before this existed.
    """
    import sys as _s
    _s.path.insert(0, str(ROOT))
    import assemble
    keep = []

    def hold(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"
    held = assemble.EMPH.sub(hold, text).replace("*", "")
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], held)


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def titlecase(s):
    words = clean(s).lower().split()
    return " ".join(w if i and w in SMALL else
                    "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
                    for i, w in enumerate(words))


def norm(s):
    return re.sub(r"[^a-z]+", " ", s.lower()).strip()


def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name == "br":
                out.append(" ")
            elif c.name == "a" and not c.get_text(strip=True):
                continue
            else:
                out.append(inline(c))     # dropcap spans join their word
    return "".join(out)


def main():
    z = fetch()
    html = z.read([n for n in z.namelist() if n.endswith(".html")][0]).decode(
        "utf-8", "replace")
    s = html.index("*** START")
    s = html.index(">", html.index("</div>", s)) + 1
    e = html.rindex("<div", 0, html.index("*** END"))
    # SOURCE_FIXES: transcription defects, each asserted to apply once.
    # A line-break hyphen welded into a word reads as a real hyphen, and it
    # is also why Rackham's caption for page 190 failed the prose test.
    for bad, good in SOURCE_FIXES:
        assert html.count(bad) == 1, (bad, html.count(bad))
        html = html.replace(bad, good)
    soup = BeautifulSoup(html[s:e], "html.parser")

    plates, sections, story, current = [], [], None, None
    front = []

    def plate(div):
        img = div.find("img")
        n = re.search(r"(\d+)m\.jpg", img["src"]).group(1)
        plates.append(n)
        return ("PLATE", n)

    for el in soup.children:
        if not isinstance(el, Tag):
            continue
        cls = el.get("class") or []
        if el.name in ("header", "footer", "section") or \
                any(c.startswith("pg") for c in cls):
            continue                       # Project Gutenberg's own furniture
        if el.name == "h2":
            t = clean(el.get_text())
            m = re.fullmatch(r"CHAPTER ([IVXL]+)", t)
            if m:
                current = {"story": story, "n": ROMAN[m.group(1)],
                           "stream": pending, "first": not any(
                               x["story"] == story for x in sections)}
                sections.append(current)
                pending = []
            else:
                story, current, pending = titlecase(t), None, []
            continue
        if el.name == "div" and "fig" in cls:
            p = plate(el)
            if story is None:
                front.append(p)
            elif current is None:
                pending.append(p)          # a story's headpiece
            else:
                current["stream"].append(p)
            continue
        if current is None:
            continue
        if "h4" in cls or el.name in ("hr", "h1") or "toc" in cls:
            continue                       # "Original Size", furniture
        if el.name == "pre":
            lines = [clean(x) for x in el.get_text().split("\n") if clean(x)]
            current["stream"].append(("VERSE", "\n".join("\t" + x for x in lines)))
            continue
        if el.name == "p":
            t = emph_safe(clean(inline(el)))
            if t and el.get("class") and "pfirst" in el.get("class"):
                # A DROP CAP PLUS SMALL CAPITALS, written by the transcription
                # as an all-caps word ("BY his arts"). That is typography,
                # not text, and `se lint` t-048 rightly rejects a chapter
                # opening in capitals. Normal casing for the word only.
                # Keyed on the FIRST WORD ONLY, whatever follows it: "THERE I
                # dreamed" slipped past a version that wanted a lowercase
                # word next.
                t = re.sub(r"^([“‘\"']?[A-Z])([A-Z]+)\b",
                           lambda m: m.group(1) + m.group(2).lower(), t)
            if t:
                current["stream"].append(("P", t))
            continue
        if el.name in ("div", "blockquote"):
            t = emph_safe(clean(inline(el)))
            if t:
                raise SystemExit(f"text in an unexpected <div>: {t[:80]!r}")
            continue
        raise SystemExit(f"unhandled <{el.name} {cls}>")
    stories = []
    for x in sections:
        if x["story"] not in stories:
            stories.append(x["story"])
    assert len(stories) == STORIES, stories
    if pending:
        sections[-1]["stream"] += pending   # Becuma's tailpiece, after ch. X

    # ---- plates: 37 placed, the case dropped, ids pinned
    on_disk = {re.search(r"(\d+)\.jpg$", n).group(1) for n in z.namelist()
               if re.search(r"images/\d+\.jpg$", n)}
    kept = [p for p in plates if p not in DROPPED]
    assert len(plates) == len(set(plates)), "a plate placed twice"
    assert on_disk == set(plates), (sorted(on_disk - set(plates)),
                                    sorted(set(plates) - on_disk))
    front = [f for f in front if f[1] not in DROPPED]
    colour = dict(COLOUR)
    assert all(c in kept for c in colour), "a colour plate is not placed"
    L = "abcdefghijklmnopqrstuvwxyz"
    rows = [{"id": L[i // 26] + L[i % 26], "source": p,
             "colour": p in colour, "printed": colour.get(p) or ""}
            for i, p in enumerate(kept)]
    if PIN.exists():
        old = json.loads(PIN.read_text())
        assert [(r["id"], r["source"]) for r in old] == \
               [(r["id"], r["source"]) for r in rows], "plate ids moved"
    PIN.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    by = {r["source"]: r for r in rows}

    # ---- second witness: every settled caption is in the prose near it
    prose = [(x, " ".join(v for k, v in x["stream"] if k == "P"))
             for x in sections]
    for p, cap in COLOUR:
        if not cap or p in PRINTED_DIFFERS:
            continue
        home = next(i for i, (x, _) in enumerate(prose)
                    if ("PLATE", p) in x["stream"]) if p not in \
            [f[1] for f in front] else None
        near = prose if home is None else prose[max(0, home - 1):home + 2]
        hay = norm(" ".join(t for _, t in near))
        assert norm(cap) in hay, f"caption for {p} not in the prose near it"

    IMAGES.mkdir(parents=True, exist_ok=True)
    for old in IMAGES.iterdir():
        old.unlink()
    from PIL import Image
    for p in kept:
        im = Image.open(io.BytesIO(z.read(f"images/{p}.jpg"))).convert("RGB")
        im.thumbnail((LONG_SIDE, LONG_SIDE))
        im.save(IMAGES / f"fig{by[p]['id']}.jpg", "JPEG", quality=88)

    # ---- compose
    captions = {}
    if CAPTIONS.exists():
        for line in CAPTIONS.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                k, _, v = line.partition("\t")
                captions[k.strip()] = v.strip()
    if (HERE / "captions").is_dir():
        for f in sorted((HERE / "captions").glob("*.txt")):
            for line in f.read_text().splitlines():
                if line.strip() and not line.startswith("#"):
                    k, _, v = line.partition("\t")
                    if k.strip() in captions:
                        raise SystemExit(f"{f.name}: {k.strip()} captioned twice")
                    captions[k.strip()] = v.strip()
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest, total, described = [], 0, 0
    for idx, x in enumerate(sections):
        heading = f"Chapter {x['n']}"
        stream = (front if idx == 0 else []) + x["stream"]
        src, mod = [heading, ""], [heading, ""]
        for k, v in stream:
            if k == "PLATE":
                r = by[v]
                desc = captions.get(r["id"], "")
                described += bool(desc)
                cap = " — ".join(y for y in (r["printed"], desc) if y)
                src.append(f"[Figure {r['id']}]")
                mod.append(f"[Figure {r['id']}: {cap}]" if cap else f"[Figure {r['id']}]")
            else:
                src.append(v)
                mod.append(v)
            src.append("")
            mod.append("")
        body = "\n".join(src).rstrip() + "\n"
        total += len(body.split())
        (HERE / "chapters" / f"{idx:03d}.txt").write_text(body)
        (HERE / "modern_chapters" / f"{idx:03d}.txt").write_text(
            "\n".join(mod).rstrip() + "\n")
        entry = {"file": f"{idx:03d}.txt", "title": heading, "part": 1,
                 "of": 1, "chapter": True}
        if x["first"]:
            entry["part_before"] = x["story"]
        manifest.append(entry)
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    settled = sum(1 for _, c in COLOUR if c)
    print(f"{len(sections)} chapters in {STORIES} stories, {total:,} words, "
          f"{len(rows)} plates ({len(COLOUR)} colour, {settled} captions "
          f"settled against the prose); {described}/{len(rows)} described")


if __name__ == "__main__":
    main()
