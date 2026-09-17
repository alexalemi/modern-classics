"""Aesop's Fables, tr. V. S. Vernon Jones (1912): a RESTORED EDITION.

    python3 aesop/prep.py

Gutenberg #11339, with G. K. Chesterton's introduction and Arthur
Rackham's illustrations. Struck from the retelling roadmap as "already
brisk and clean"; restored instead (ROADMAP.md, "A second strand").

THE BOOK'S OWN LISTS ARE THE WITNESSES. The Contents names 284 fables and
the body has 284 fable headings; the List of Illustrations names 65 plates
(13 in colour, 52 in black and white) and each links an anchor that sits
on exactly one plate block. Both are asserted. The other 15 blocks are
unlisted decorations -- the drawn title page, headpieces and silhouettes
(a grape vine, a goat) -- which get alt text and no printed caption,
because the book printed none.

A HEADPIECE BELONGS TO THE FABLE AFTER IT. Rackham's small drawings sit
before a fable's heading in the source; buffered and placed at the head of
that fable, not at the tail of the one before.

EMPHASIS HAS A CAP. Chesterton's introduction is printed as long italic
paragraphs, and assemble.EMPH refuses a span over 400 characters -- so
wrapping those would ship literal asterisks. Italics are carried only
where EMPH will render them; longer spans go plain.

MODERN_CHAPTERS/ IS COMPOSED from chapters/ plus captions.txt, as in
worthington/, so the prose cannot drift and verify's ratio holds at 1.00.
Plate ids are digit-free and PINNED in plates.json.
"""
import json
import re
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
IMAGES = ROOT / "site" / "images" / "aesop"
PIN = HERE / "plates.json"
CAPTIONS = HERE / "captions.txt"
BOOK = "11339"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
FABLES, LISTED, COLOUR = 284, 65, 13
PER_FILE = 3500             # words, before a file is closed at a fable boundary
EMPH_CAP = 380              # under assemble.EMPH's 400, with room for markers
SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or", "as", "from", "into"}


def fetch():
    SRC.mkdir(exist_ok=True)
    p = SRC / f"pg{BOOK}-h.zip"
    if not p.exists():
        url = f"https://www.gutenberg.org/cache/epub/{BOOK}/pg{BOOK}-h.zip"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=300) as r:
            p.write_bytes(r.read())
    return zipfile.ZipFile(p)


def titlecase(s):
    """'THE ASS IN THE LION'S SKIN' -> "The Ass in the Lion's Skin".

    Never an all-caps line: assemble.py reads one as a heading of its own.
    """
    words = s.strip().lower().split()
    out = []
    for i, w in enumerate(words):
        if i and w in SMALL:
            out.append(w)
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


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


WORD = re.compile(r"\w")


def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name == "br":
                out.append(" ")
            elif c.name in ("i", "em"):
                inner = inline(c)
                prev = "".join(out)[-1:]
                nxt = c.next_sibling
                nxt = str(nxt)[:1] if isinstance(nxt, NavigableString) else ""
                ok = (inner.strip() and inner == inner.strip()
                      and "*" not in inner and len(clean(inner)) <= EMPH_CAP
                      and not WORD.match(prev or " ")
                      and not WORD.match(nxt or " "))
                out.append(f"*{clean(inner)}*" if ok else inner)
            else:
                out.append(inline(c))
    return "".join(out)


def main():
    z = fetch()
    html = z.read([n for n in z.namelist() if n.endswith(".html")][0]).decode(
        "utf-8", "replace")
    s = html.index("*** START")
    s = html.index(">", html.index("</div>", s)) + 1
    e = html.rindex("<div", 0, html.index("*** END"))
    soup = BeautifulSoup(html[s:e], "html.parser")

    # ---- the book's own lists
    def section(name):
        h = soup.find("h2", string=lambda t: t and clean(t) == name)
        assert h is not None, name
        out = []
        for el in h.next_siblings:
            if isinstance(el, Tag) and el.name == "h2":
                break
            out.append(el)
        return h, out
    _, contents = section("CONTENTS")
    toc = [clean(a.get_text()) for el in contents if isinstance(el, Tag)
           for a in ([el] if el.name == "a" else el.find_all("a"))]
    assert len(toc) == FABLES, f"contents lists {len(toc)} fables"
    _, loi = section("LIST OF ILLUSTRATIONS")
    listed, colour = {}, True
    for el in loi:
        if not isinstance(el, Tag):
            continue
        if el.name == "h3" and "BLACK" in el.get_text():
            colour = False
        for a in el.find_all("a", href=True) if el.name != "a" else [el]:
            listed[a["href"].lstrip("#")] = (clean(a.get_text()), colour)
    assert len(listed) == LISTED and sum(c for _, c in listed.values()) == COLOUR

    # ---- walk
    intro_h, intro = section("INTRODUCTION")
    title_page = soup.find("a", href=re.compile(r"images/002\.jpg"))
    fables_h = soup.find("h2", string=lambda t: t and "AESOP" in t
                         and "FABLES" in t and t.find_parent() is not None
                         and t.find_next("h2") is not None
                         and clean(t) != "AESOP'S FABLES" or False)
    fables_h = [h for h in soup.find_all("h2")
                if clean(h.get_text()) == "AESOP'S FABLES"][-1]

    plates, pieces = [], []   # plates: (href, printed); pieces: sections

    def plate_of(div):
        a = div.find("a", href=True)
        href = a["href"].split("/")[-1] if a else div.find("img")["src"].split("/")[-1]
        aid = a.get("id", "") if a else ""
        title, _ = listed.get(aid, ("", False))
        plates.append((href, titlecase(title) if title else ""))
        return ("PLATE", href)

    def paragraphs(nodes, stream):
        for el in nodes:
            if not isinstance(el, Tag):
                continue
            cls = el.get("class") or []
            if el.name == "div" and any(c.startswith("fig") for c in cls):
                stream.append(plate_of(el))
            elif el.name == "p" and "toc" not in cls:
                t = emph_safe(clean(inline(el)))
                if t:
                    stream.append(("P", t))
            elif el.name in ("div", "blockquote") and "pg_body_wrapper" not in cls:
                paragraphs(el.children, stream)

    intro_stream = []
    if title_page is not None:
        intro_stream.append(plate_of(title_page.find_parent("div")))
    paragraphs(intro, intro_stream)
    pieces.append(("Introduction", None, intro_stream, None))

    fable_titles, current, buffered = [], None, []
    for el in fables_h.next_siblings:
        if not isinstance(el, Tag):
            continue
        cls = el.get("class") or []
        if el.name == "h2":
            current = titlecase(clean(el.get_text()))
            fable_titles.append(current)
            stream = [("TITLE", current)] + buffered
            buffered = []
            pieces.append((current, "fable", stream, None))
            continue
        if el.name == "div" and any(c.startswith("fig") for c in cls):
            # a figure before any text of the current fable is a headpiece
            # of the NEXT one only if text has already been emitted here
            if current is None or any(k == "P" for k, _ in pieces[-1][2]):
                buffered.append(plate_of(el))
            else:
                pieces[-1][2].append(plate_of(el))
            continue
        if current is not None:
            paragraphs([el], pieces[-1][2])
    assert not buffered, f"{len(buffered)} plates after the last fable"
    assert len(fable_titles) == FABLES, f"{len(fable_titles)} fable headings"
    # Two Contents entries in the transcription carry an ANCHOR ID as their
    # link text ("THE_LAMP", "THE_MISER"), so underscores are separators
    # here, not letters. The headings themselves are right.
    key = lambda x: re.sub(r"[\W_]", "", x.lower())
    mismatch = [(a, b) for a, b in zip(toc, fable_titles) if key(a) != key(b)]
    assert not mismatch, mismatch[:3]

    # ---- plates: exactly once, ids pinned
    on_disk = {n.split("/")[-1] for n in z.namelist()
               if re.search(r"images/.*\.jpg$", n)}
    hrefs = [h for h, _ in plates]
    assert len(hrefs) == len(set(hrefs)), "a plate placed twice"
    thumbs = {n for n in on_disk if re.search(r"(t\.jpg|-t\w+\.jpg)$", n)}
    missing = on_disk - thumbs - set(hrefs)
    assert not missing, sorted(missing)
    assert sum(1 for _, t in plates if t) == LISTED, "listed plates not all captioned"
    L = "abcdefghijklmnopqrstuvwxyz"
    rows = [{"id": "front" if h == "002.jpg" else L[i // 26] + L[i % 26],
             "source": h, "printed": t, "listed": bool(t)}
            for i, (h, t) in enumerate(plates)]
    if PIN.exists():
        old = json.loads(PIN.read_text())
        assert [(r["id"], r["source"]) for r in old] == \
               [(r["id"], r["source"]) for r in rows], "plate ids moved"
    else:
        PIN.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    by = {r["source"]: r for r in rows}

    IMAGES.mkdir(parents=True, exist_ok=True)
    for old in IMAGES.iterdir():
        old.unlink()
    for h in hrefs:
        (IMAGES / f"fig{by[h]['id']}.jpg" if by[h]["id"] != "front"
         else IMAGES / "front.jpg").write_bytes(z.read(f"images/{h}"))

    # ---- group fables into files; compose both directories
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
    groups, cur, words = [], [], 0
    for piece in pieces[1:]:
        n = sum(len(x[1].split()) for x in piece[2] if x[0] == "P")
        if cur and words + n > PER_FILE:
            groups.append(cur)
            cur, words = [], 0
        cur.append(piece)
        words += n
    groups.append(cur)
    files = [[pieces[0]]] + groups

    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest, total, described = [], 0, 0
    for idx, group in enumerate(files):
        src, mod = [], []
        if idx == 0:
            src += ["Introduction", ""]
            mod += ["Introduction", ""]
        for title, kind, stream, _ in group:
            for k, v in stream:
                if k == "PLATE":
                    r = by[v]
                    src.append(f"[Figure {r['id']}]")
                    desc = captions.get(r["id"], "")
                    described += bool(desc)
                    cap = " — ".join(x for x in (r["printed"], desc) if x)
                    mod.append(f"[Figure {r['id']}: {cap}]" if cap
                               else f"[Figure {r['id']}]")
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
        entry = {"file": f"{idx:03d}.txt", "part": 1, "of": 1}
        if idx == 0:
            entry["title"] = "Introduction"
        else:
            names = [t for t, _, _, _ in group]
            entry["title"] = names[0]
            entry["split_headings"] = names
            if idx == 1:
                entry["part_before"] = "Aesop’s Fables"
        manifest.append(entry)
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(files)} files, {total:,} words, {FABLES} fables, "
          f"{len(rows)} plates ({LISTED} listed, {len(rows) - LISTED} "
          f"decorations); {described}/{len(rows)} described")


if __name__ == "__main__":
    main()
