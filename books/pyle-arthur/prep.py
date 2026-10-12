"""Howard Pyle, The Story of King Arthur and His Knights (1903): source prep.

    python3 books/pyle-arthur/prep.py            # chapters/, manifest.json, plates
    python3 books/pyle-arthur/prep.py --captions # fill [Figure id] captions
                                                 # in modern_chapters/ from captions.txt

SOURCE: Project Gutenberg #60184, the illustrated HTML (pg60184-h.zip),
transcribed from the 1903 Scribner first edition. Pyle drew every picture
himself: full-page plates, a drawn headpiece over every chapter, and small
tailpieces. Gutenberg ships them at 550px on the long side (the drawn title
page alone at full scan size), which is what this edition uses.

STRUCTURE. Two Books in one volume: The Book of King Arthur (Prologue +
three Parts) and The Book of Three Worthies (Foreword, Prologue, three
Parts: Merlin, Pelleas, Gawain). Each Part opens on an italic address to
the reader, which becomes its own short section headed "Foreword" (Pyle's
own word for these openers; the Three Worthies one is printed under a
"Foreword." headpiece). Pyle restarts "Chapter First" in every Part, and so
does this edition ("Chapter 1:"); assemble.unique_ids keeps the anchors
distinct. Part dividers are two-level, on the democracy2 precedent:
"The Book of King Arthur, Part One: The Winning of Kinghood" -- a bare
"Part One: ..." would give both Books' Part One the same anchor.

FILES. One file per chapter, except the four longest, which are split in two
at a paragraph boundary near the middle (keeps every file under ~6k words).
The "CONCLUSION" sections Pyle prints after the last chapter of a Part stay in
that chapter's file as a "Conclusion" subheading.

SIDENOTES. Pyle printed 306 marginal summaries ("Sir Kay breaketh his
sword.") beside the paragraphs they summarise. They are his text and are
kept, as italic one-line paragraphs just before the paragraph they sat
beside, written "*Sir Kay breaketh his sword*." -- THE STOP OUTSIDE THE
ASTERISK, or assemble.is_subheading (which sees par[-1] == "*") counts the
capitals and sets "*Sir Pellias overthroweth Sir Gawaine.*" as a heading.
Inscriptions on swords and shields are set the same way, on one line.
Pyle's wholly italic paragraphs (the Part forewords and Conclusions) are
set roman: assemble's emphasis spans stop at 400 characters, and most of
these run longer, so the asterisks would print.

PLATES. Every drawing is kept except: the publisher's case (cover.jpg); the
head- and tailpieces of the Contents and List of Illustrations, which go
with those two lists (the List of Illustrations headpiece is also an
allegorical figure with bare breasts -- see BOOKS.md COVERS); and four
repeated printer's-ornament bands and the leaf ornament (ill_bow, ill_circ,
ill_curl, leaf-end), which carry no picture. A full-page plate that the
book faces against a chapter opening (i.e. the plate stands just before the
chapter's headpiece) is moved inside that chapter, after its heading.
Plate ids are digit-free (no "Figure N" label: Pyle never numbered them)
and pinned in plates.json. The printed title of each full-page plate comes
from Pyle's List of Illustrations and is lettered into the plate itself.
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SRC = HERE / "_src"
HTML = SRC / "h" / "pg60184-images.html"
IMAGES = ROOT / "site" / "images" / "pyle-arthur"
PIN = HERE / "plates.json"
CAPTIONS = HERE / "captions.txt"

DROP_IMAGES = {"cover.jpg", "ill_bow.jpg", "ill_circ.jpg", "ill_curl.jpg",
               "leaf-end.jpg", "ill_pg_ix_sml.jpg", "ill_pg_x.jpg",
               "ill_pg_xi_sml.jpg", "ill_pg_xii.jpg"}

# Pyle's List of Illustrations, by image file (printed titles, as printed).
PRINTED = {
    "ill_pg_iv_sml.jpg": "King Arthur of Britain",
    "ill_pg_xiv_sml.jpg": "Uther-Pendragon",
    "ill_pg_008_sml.jpg": "Sir Kay breaketh his sword at ye Tournament",
    "ill_pg_020_sml.jpg": "Sir Kay showeth the mystic Sword unto Sir Ector",
    "ill_pg_028_sml.jpg": "How Arthur drew forth ye Sword",
    "ill_pg_040_sml.jpg": "In the Valley of Delight",
    "ill_pg_052_sml.jpg": "The Battle with the Sable Knight",
    "ill_pg_064_sml.jpg": "Excalibur the Sword",
    "ill_pg_078_sml.jpg": "The Lady Guinevere",
    "ill_pg_090_sml.jpg": "Two Knights do battle before Cameliard",
    "ill_pg_100_sml.jpg": "The White Champion meets two Knights at the Mill",
    "ill_pg_112_sml.jpg": "Four Knights serve the Gardener Lad",
    "ill_pg_124_sml.jpg": "The Gardener Lad takes off his Cap",
    "ill_pg_138_sml.jpg": "King Arthur meets the Lady Guinevere",
    "ill_pg_149_sml.jpg": "Ornamented Title—The Book of Three Worthies",
    "ill_pg_150_sml.jpg": "The Lady of ye Lake",
    "ill_pg_154_sml.jpg": "The Enchanter Merlin",
    "ill_pg_162_sml.jpg": "The Enchantress Vivien",
    "ill_pg_172_sml.jpg": "Vivien bewitches Merlin",
    "ill_pg_180_sml.jpg": "Queen Morgana le Fay",
    "ill_pg_190_sml.jpg": "Queen Morgana loses Excalibur his sheath",
    "ill_pg_204_sml.jpg": "Sir Pellias, the Gentle Knight",
    "ill_pg_214_sml.jpg": "Sir Pellias encounters the Sorrowful Lady in Arroy",
    "ill_pg_226_sml.jpg": "Parcenet covers Sir Pellias with a cloak",
    "ill_pg_240_sml.jpg": "The Lady of the Lake sits by the Fountain in Arroy",
    "ill_pg_254_sml.jpg": "Sir Gawaine sups with ye Lady Ettard",
    "ill_pg_266_sml.jpg": "The Lady of the Lake finds Sir Pellias wounded",
    "ill_pg_280_sml.jpg": "Sir Gawaine the Son of Lot, King of Orkney",
    "ill_pg_294_sml.jpg": "King Arthur findeth ye old woman in ye hut",
    "ill_pg_304_sml.jpg": "Sir Gawaine finds the beautiful Lady",
}

# Section anchors (the <a id> inside each h2/h3/h4) -> section key.
ORD = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4, "FIFTH": 5, "SIXTH": 6}
PARTS = {"A": ("K", 1), "B": ("K", 2), "C": ("K", 3),
         "D": ("W", 1), "E": ("W", 2), "F": ("W", 3)}

BOOK_K = "The Book of King Arthur"
BOOK_W = "The Book of Three Worthies"
PART_NAMES = {
    ("K", 1): "The Book of King Arthur, Part One: The Winning of Kinghood",
    ("K", 2): "The Book of King Arthur, Part Two: The Winning of a Sword",
    ("K", 3): "The Book of King Arthur, Part Three: The Winning of a Queen",
    ("W", 1): "The Book of Three Worthies, Part One: The Story of Merlin",
    ("W", 2): "The Book of Three Worthies, Part Two: The Story of Sir Pelleas",
    ("W", 3): "The Book of Three Worthies, Part Three: The Story of Sir Gawain",
}

# Exact modern heading strings, one per chapter (Pyle's titles, retold).
TITLES = {
    ("K", 1, 1): "Chapter 1: How Sir Kay Fought in a Great Tournament in London and Broke His Sword, and How Arthur Found Him a New One",
    ("K", 1, 2): "Chapter 2: How Arthur Twice Did the Miracle of the Sword in Front of Sir Ector, and How He Learned Who He Really Was",
    ("K", 1, 3): "Chapter 3: How Many Kings and Great Dukes Tried to Draw the Sword from the Anvil and Failed, and How Arthur Tried and Succeeded",
    ("K", 2, 1): "Chapter 1: How a Wounded Knight Came to King Arthur's Court, How a Young Knight Tried to Avenge Him and Failed, and How the King Took Up the Challenge Himself",
    ("K", 2, 2): "Chapter 2: How King Arthur Fought the Sable Knight and Was Badly Wounded, and How Merlin Carried Him Safely Away",
    ("K", 2, 3): "Chapter 3: How King Arthur Found a Noble Sword in a Most Wonderful Way, and How He Fought Again with It and Won",
    ("K", 3, 1): "Chapter 1: How King Arthur Went to Tintagalon with Four of His Court, and How He Disguised Himself for a Secret Purpose",
    ("K", 3, 2): "Chapter 2: How King Rience Came to Cameliard, and How King Arthur Fought the Duke of North Umber",
    ("K", 3, 3): "Chapter 3: How King Arthur Met Four Knights, and What Came of It",
    ("K", 3, 4): "Chapter 4: How the Four Knights Served the Lady Guinevere",
    ("K", 3, 5): "Chapter 5: How King Arthur Defeated King Leodegrance's Enemies, and How His Royalty Was Made Known",
    ("K", 3, 6): "Chapter 6: How King Arthur Was Married in Royal State, and How the Round Table Was Founded",
    ("W", 1, 1): "Chapter 1: How Queen Morgan le Fay Plotted Against King Arthur, and How She Sent a Damsel to Charm the Enchanter Merlin",
    ("W", 1, 2): "Chapter 2: How Merlin Traveled with Vivien to the Valley of Joyousness and Built Her a Castle There, How He Taught Her the Secrets of Magic, and How She Used Them to Bring Him Down",
    ("W", 1, 3): "Chapter 3: How Queen Morgan le Fay Came Back to Camelot Meaning to Harm King Arthur, and How the King and Others Went Hunting, and What Came of It",
    ("W", 1, 4): "Chapter 4: What Happened to Sir Accolon, and How King Arthur Fought a Duel with Swords and Nearly Lost His Life",
    ("W", 2, 1): "Chapter 1: How Queen Guinevere Went Maying, and How Sir Pelleas Took On a Quest for Her",
    ("W", 2, 2): "Chapter 2: How Sir Pelleas Defeated a Red Knight Named Sir Adresack and Freed Twenty-Two Prisoners from His Castle",
    ("W", 2, 3): "Chapter 3: How Sir Pelleas Fought Sir Engamore, the Knight of the Green Sleeves, and What Happened to the Lady Ettard",
    ("W", 2, 4): "Chapter 4: How Queen Guinevere Quarreled with Sir Gawain, and How Sir Gawain Left King Arthur's Court for a While",
    ("W", 2, 5): "Chapter 5: How Sir Gawain Met Sir Pelleas and Promised to Help Him with the Lady Ettard",
    ("W", 2, 6): "Chapter 6: How the Lady of the Lake Took Back Her Necklace from Sir Pelleas",
    ("W", 3, 1): "Chapter 1: How a White Hart Appeared Before King Arthur, How Sir Gawain and His Brother Gaheris Chased It, and What Happened to Them on That Quest",
    ("W", 3, 2): "Chapter 2: How King Arthur Got Lost in the Forest and Met with a Very Strange Adventure in a Castle He Came To",
    ("W", 3, 3): "Chapter 3: How King Arthur Overcame the Knight-Enchanter, and How Sir Gawain Showed the True Nobility of His Knighthood",
}

SPLIT_OVER = 6000


def letters(n):
    a = "abcdefghijklmnopqrstuvwxyz"
    return a[n // 26] + a[n % 26]


def clean(text):
    text = text.replace(" ", " ").replace(" ", " ")
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


def para_text(el):
    """Text of a <p>/<div>, minus page numbers, with the drop cap rejoined
    ("I" + "N ancient" -> "In ancient") and italic kept as *...*."""
    el = BeautifulSoup(str(el), "html.parser")
    for s in el.select("span.pagenum"):
        s.decompose()
    for br in el.find_all("br"):
        br.replace_with("\u2028")
    letra = el.select_one("span.letra")
    if letra:
        cap = letra.get_text()
        letra.replace_with(cap)
    # italic spans inside a paragraph; a wholly italic paragraph is wrapped
    # once by the caller
    for i in el.find_all("i"):
        t = i.get_text()
        i.replace_with(f"*{t.strip()}*" if t.strip() else t)
    txt = el.get_text()
    txt = "\n".join(clean(l) for l in txt.split("\u2028") if clean(l))
    txt = re.sub(r"^([A-Z])\*([A-Za-z])", r"*\1\2", txt)
    # drop-cap word: "IN ancient" / "*HERE beginneth" -> "In" / "*Here"
    txt = re.sub(r"^(\*?)([A-Z])([A-Z]+)\b",
                 lambda m: m.group(1) + m.group(2) + m.group(3).lower(), txt)
    # whole-paragraph italic: collapse "*a* *b*" artefacts
    txt = re.sub(r"\*\s+\*", " ", txt)
    return txt


def blocks():
    soup = BeautifulSoup(HTML.read_text(), "html.parser")
    body = soup.body
    out = []
    started = False
    for el in body.descendants:
        if not isinstance(el, Tag):
            continue
        if el.get("id") == "pg-start-separator":
            started = True
            continue
        if el.get("id") == "pg-footer":
            break
        if not started:
            continue
        # skip anything inside an element we already consumed
        if any(p is not None and getattr(p, "_used", False) for p in el.parents):
            continue
        name = el.name
        if name in ("h1", "h2", "h3", "h4"):
            el._used = True
            a = el.find("a", id=True)
            imgs = [i["src"].split("/")[-1] for i in el.find_all("img")]
            txt = clean(BeautifulSoup(str(el), "html.parser").get_text(" ").replace("\u2028", " "))
            out.append(("h", a["id"] if a else None, txt, imgs))
        elif name == "table":
            el._used = True  # front contents tables: dropped
        elif name == "div" and "sidenote" in (el.get("class") or []):
            el._used = True
            t = clean(el.get_text())
            out.append(("side", t))
        elif name in ("div", "p") and "figcenter" in (el.get("class") or []):
            el._used = True
            for i in el.find_all("img"):
                out.append(("fig", i["src"].split("/")[-1]))
        elif name == "p":
            el._used = True
            for i in el.find_all("img"):
                out.append(("fig", i["src"].split("/")[-1]))
            t = para_text(el)
            if t.strip() and not re.fullmatch(r"\{[ivxl\d]+\}", t.strip()):
                out.append(("p", t, el.find("span", class_="eng") is not None))
    return out


def sections():
    """Cut the block stream into ordered sections:
    (key, part_before, source_heading, items)."""
    bl = blocks()
    secs = []
    cur = None

    def new(key, pb, head):
        nonlocal cur
        cur = {"key": key, "part_before": pb, "head": head, "items": []}
        secs.append(cur)

    # front: frontispiece + title page go to the Foreword
    pending_figs = []
    book = None
    for b in bl:
        if b[0] == "h":
            _, aid, txt, imgs = b
            imgs = [i for i in imgs if i not in DROP_IMAGES]
            if b[2].startswith("The Story of"):  # h1: the drawn title page
                pending_figs += imgs
            elif aid == "Foreword":
                new("foreword", None, "Foreword")
                cur["items"] += [("fig", f) for f in pending_figs] + [("fig", i) for i in imgs]
                pending_figs = []
            elif aid in ("CONTENTS", "LIST_OF_ILLUSTRATIONS"):
                cur = {"items": []}  # discard sink
            elif aid == "THE_BOOK_OF_KING_ARTHUR":
                book = "K"
                pending_figs = imgs
            elif aid == "PROLOGUE":
                new("prologue-K", BOOK_K, "Prologue")
                cur["items"] += [("fig", f) for f in pending_figs] + [("fig", i) for i in imgs]
                pending_figs = []
            elif aid == "The_BOOK_of_THREE_WORTHIES":
                book = "W"
                pending_figs = imgs
            elif aid == "Sorcery_Prologue":
                new("prologue-W", None, "Prologue")
                cur["items"] += [("fig", f) for f in pending_figs] + [("fig", i) for i in imgs]
                pending_figs = []
            elif aid and aid.startswith("PART_"):
                m = re.match(r"PART_([IV]+)-([AB])", aid)
                bk, n = {"A": "K", "B": "W"}[m.group(2)], {"I": 1, "II": 2, "III": 3}[m.group(1)]
                new(f"foreword-{bk}{n}", PART_NAMES[(bk, n)], "Foreword")
            elif aid and aid.startswith("CHAPTER_"):
                m = re.match(r"CHAPTER_([A-Z]+)-([A-F])", aid)
                bk, n = PARTS[m.group(2)]
                ch = ORD[m.group(1)]
                # a full-page plate standing just before the chapter faces it
                carry = []
                while cur["items"] and cur["items"][-1][0] == "fig" and \
                        cur["items"][-1][1] in PRINTED:
                    carry.insert(0, cur["items"].pop())
                new((bk, n, ch), None, None)
                cur["items"] += carry + [("fig", i) for i in imgs]
                cur["want_title"] = True
            elif "CONCLUSION" in txt:
                cur["items"] += [("fig", i) for i in imgs]
                cur["items"].append(("sub", "Conclusion"))
            elif "Foreword" in txt or not txt:
                # Three Worthies foreword (headpiece only, no anchor)
                if book == "W" and imgs and "ill_pg_151_sml.jpg" in imgs:
                    new("foreword-W", BOOK_W, "Foreword")
                    cur["items"] += [("fig", f) for f in pending_figs] + [("fig", i) for i in imgs]
                    pending_figs = []
                else:
                    cur["items"] += [("fig", i) for i in imgs]
            else:
                raise SystemExit(f"unhandled heading {aid!r} {txt!r}")
        elif b[0] == "fig":
            if b[1] in DROP_IMAGES:
                continue
            if cur is None or cur.get("key") is None:
                pending_figs.append(b[1])
            else:
                cur["items"].append(("fig", b[1]))
        elif b[0] == "p":
            if cur is None or cur.get("key") is None:
                continue  # title page / copyright lines
            if cur.get("want_title"):
                cur["title_src"] = b[1].strip("*").strip()
                cur["want_title"] = False
                continue
            cur["items"].append(("eng" if b[2] else "p", b[1]))
        elif b[0] == "side":
            if cur is None:
                continue
            cur["items"].append(("side", b[1]))
    return [s for s in secs if s.get("key")]


def fix_worthies_front(secs):
    """Between the end of Book One and the Three Worthies Foreword the HTML
    carries the ornamented title (149) and the Lady of the Lake plate (150).
    blocks() saw 149 inside the h4 and 150 as a free figure; make sure both
    open the Three Worthies Foreword and not the tail of Book One."""
    k6 = next(s for s in secs if s["key"] == ("K", 3, 6))
    fw = next(s for s in secs if s["key"] == "foreword-W")
    moved = [it for it in k6["items"] if it == ("fig", "ill_pg_150_sml.jpg")]
    k6["items"] = [it for it in k6["items"] if it not in moved]
    have = {it[1] for it in fw["items"] if it[0] == "fig"}
    front = [("fig", "ill_pg_149_sml.jpg")] if "ill_pg_149_sml.jpg" not in have else []
    front += [m for m in moved if m[1] not in have]
    fw["items"] = front + fw["items"]
    fw["items"].sort(key=lambda it: it != ("fig", "ill_pg_149_sml.jpg"))
    # the Merlin plate (154) faces the Prologue: move it there
    pw = next(s for s in secs if s["key"] == "prologue-W")
    m154 = [it for it in fw["items"] if it == ("fig", "ill_pg_154_sml.jpg")]
    fw["items"] = [it for it in fw["items"] if it not in m154]
    pw["items"] = m154 + [it for it in pw["items"] if it not in m154]
    return secs


def render(items, ids):
    out = []
    for kind, val in items:
        if kind == "fig":
            out.append(f"[Figure {ids[val]}]")
        elif kind == "sub":
            out.append("Conclusion")
        elif kind == "side":
            # full stop OUTSIDE the closing asterisk: is_subheading sees the
            # "." and never takes a sidenote for a heading
            out.append(f"*{val.strip('*').strip().rstrip('.')}*.")
        elif kind == "eng":
            # an inscription: one line, italic, stop outside
            t = " ".join(val.replace("*", "").split()).strip("“”").rstrip(".")
            out.append(f"*{t}*.")
        else:
            # a wholly italic paragraph (Pyle's addresses to the reader) is
            # set roman: EMPH spans stop at 400 characters, and the Foreword
            # heading already marks these as Pyle speaking
            if val.startswith("*") and val.endswith("*") and val.count("*") == 2:
                val = val[1:-1]
            out.append(val)
    return out


def main():
    if not HTML.exists():
        with zipfile.ZipFile(SRC / "60184-h.zip") as z:
            z.extractall(SRC / "h")
    secs = fix_worthies_front(sections())

    # pin plate ids in reading order
    order = []
    for s in secs:
        for kind, val in s["items"]:
            if kind == "fig" and val not in order:
                order.append(val)
    pins = {}
    if PIN.exists():
        pins = {p["src"]: p["id"] for p in json.loads(PIN.read_text())}
    ids, used = {}, set(pins.values())
    n = 0
    for src in order:
        if src in pins:
            ids[src] = pins[src]
            continue
        while letters(n) in used:
            n += 1
        ids[src] = "front" if src == "ill_pg_iv_sml.jpg" else letters(n)
        used.add(ids[src])
        if ids[src] != "front":
            n += 1
    plates = [{"id": ids[s], "src": s, "printed": PRINTED.get(s)} for s in order]
    PIN.write_text(json.dumps(plates, indent=1, ensure_ascii=False) + "\n")

    IMAGES.mkdir(parents=True, exist_ok=True)
    for p in plates:
        stem = "front" if p["id"] == "front" else f"fig{p['id']}"
        dst = IMAGES / f"{stem}.jpg"
        src = SRC / "h" / "images" / p["src"]
        # NEVER overwrite a plate already on disk: fetch_plates.py puts
        # 1600px scan crops there, and a rerun of prep would silently put
        # the 550px thumbnails back. Delete the file to force a recopy.
        if dst.exists():
            continue
        im = Image.open(src)
        if max(im.size) > 1400:
            im = im.convert("L")
            im.thumbnail((1400, 1400), Image.LANCZOS)
            im.save(dst, quality=88)
        else:
            shutil.copyfile(src, dst)

    chapters = HERE / "chapters"
    chapters.mkdir(exist_ok=True)
    for f in chapters.glob("*.txt"):
        f.unlink()
    manifest, fileno = [], 0
    for s in secs:
        key = s["key"]
        if isinstance(key, tuple):
            title = TITLES[key]
            head = f"Chapter {['', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth'][key[2]]}: {s['title_src']}"
        else:
            title = s["head"]
            head = s["head"]
        pars = render(s["items"], ids)
        words = sum(len(p.split()) for p in pars if not p.startswith("[Figure"))
        pieces = [pars]
        if words > SPLIT_OVER:
            # cut at the paragraph boundary nearest the middle, never
            # before a sidenote's paragraph or on a figure
            acc, half, cut = 0, words / 2, None
            for i, p in enumerate(pars):
                acc += 0 if p.startswith("[Figure") else len(p.split())
                if acc >= half and i + 1 < len(pars) and not pars[i].startswith("*") \
                        and not pars[i + 1].startswith("[Figure") and pars[i] != "Conclusion":
                    cut = i + 1
                    break
            pieces = [pars[:cut], pars[cut:]]
        for k, piece in enumerate(pieces, 1):
            fn = f"{fileno:03d}.txt"
            lines = [head]
            if len(pieces) > 1:
                lines.append(f"(Part {k} of {len(pieces)})")
            (chapters / fn).write_text("\n\n".join(lines + piece) + "\n")
            e = {"file": fn, "title": title, "part": k, "of": len(pieces),
                 "words": sum(len(p.split()) for p in piece if not p.startswith("[Figure"))}
            if k == 1 and s["part_before"]:
                e["part_before"] = s["part_before"]
            if k == 1 and not isinstance(key, tuple):
                e["chapter"] = s["part_before"] is not None and title == "Foreword" \
                    and s["part_before"] not in (BOOK_K, BOOK_W)
                if not e["chapter"]:
                    del e["chapter"]
            manifest.append(e)
            fileno += 1
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    tot = sum(e["words"] for e in manifest)
    print(f"{len(manifest)} files, {tot} words, {len(plates)} plates")
    for e in manifest:
        print(e["file"], e["words"], e["part"], e["of"], e.get("part_before", ""), "|", e["title"][:60])


def fill_captions():
    """Write each plate's caption (captions.txt: id<TAB>caption) into the
    bare [Figure id] markers of modern_chapters/. Idempotent."""
    caps = {}
    for line in CAPTIONS.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            k, v = line.split("\t", 1)
            if k in caps:
                raise SystemExit(f"plate {k} captioned twice")
            caps[k] = v.strip()
    pinned = {p["id"] for p in json.loads(PIN.read_text())}
    missing = pinned - caps.keys()
    if missing:
        raise SystemExit(f"uncaptioned plates: {sorted(missing)}")
    pat = re.compile(r"\[Figure ([a-z]+)(?::[^\]]*)?\]")
    for f in sorted((HERE / "modern_chapters").glob("*.txt")):
        t = f.read_text()
        t2 = pat.sub(lambda m: f"[Figure {m.group(1)}: {caps[m.group(1)]}]", t)
        if t2 != t:
            f.write_text(t2)


if __name__ == "__main__":
    if "--captions" in sys.argv:
        fill_captions()
    else:
        main()
