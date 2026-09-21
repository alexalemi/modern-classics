"""Shared machinery for RESTORED EDITIONS built from Gutenberg HTML.

    import restore_lib as R
    book = R.Book(HERE, zip_name="pg5827-h.zip", ...)
    R.run(book)

Everything the earlier native preps (aesop/, irish-fairy-tales/,
calculus-made-easy/) did by hand, in one place, so a new restored edition
is a configuration plus the book's own decisions (SOURCE_FIXES, what to
drop, which headings are sections). What each prep must still supply is
the part no library can know: where the book's sections begin, what the
printed Contents says, and every judgement about the text.

THE WALKER flattens unclassed and pg_body_wrapper <div>s (calculus: six
displayed formulas were lost inside them) and emits a stream of items:
    ("H", level, text)   a heading, left to the book to classify
    ("P", text)          a paragraph, inline markup already rendered:
                         *emphasis*, \\(tex\\) / \\[tex\\] from data-tex
    ("BLOCK", text)      tab-indented lines: verse, <pre>, a table
    ("PLATE", src, printed)
    ("HR",)
Footnotes are gathered first and re-emitted as "Footnote: ..." after the
paragraph that cites them (the candle/mill pattern). Page numbers,
anchors and Gutenberg's own furniture never reach the stream.

WITNESSES, all asserted by run():
  - raw-HTML word count against emitted words (a second reading that
    shares no code with the walker -- the epictetus rule);
  - the formula sequence against every data-tex in the source;
  - every image file placed exactly once, or named in book.drop;
  - plate ids pinned in plates.json, so captions can never slide;
  - the book's own Contents, when the prep supplies it.
"""
import html as HTML
import io
import json
import re
import sys
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import assemble  # noqa: E402
import mathml    # noqa: E402

L = "abcdefghijklmnopqrstuvwxyz"
SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
BLOCKS = ("p", "div", "table", "pre", "figure", "blockquote", "ul", "ol",
          "dl", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "img")


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ").replace(" ", " ")).strip()


SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or", "as", "from", "into", "nor", "upon", "vs"}


def titlecase(s, keep=()):
    """ALL-CAPS heading -> title case. Roman numerals and words in `keep`
    stay as they are; never leave an all-caps line (assemble reads it as a
    heading of its own)."""
    words = clean(s).split()
    out = []
    for i, w in enumerate(words):
        bare = w.strip(".,:;()“”‘’\"'*")
        if re.fullmatch(r"[IVXLC]+", bare) or bare in keep or bare + "." in keep:
            out.append(w)
        elif i and bare.lower() in SMALL:
            out.append(w.lower())
        else:
            # capitalise the first LETTER: "(TANG" -> "(Tang", "“OBELISK" -> "“Obelisk"
            out.append("-".join(re.sub(r"[^\W\d_]", lambda m: m.group(0).upper(), p.lower(), count=1)
                                for p in w.split("-")))
    return " ".join(out)


def emph_safe(text):
    """Keep only asterisks assemble.EMPH renders; formulas held aside."""
    maths, keep = [], []
    text = mathml.MATH.sub(lambda m: (maths.append(m.group(0)), f"\x00F{len(maths)-1}\x00")[1], text)
    held = assemble.EMPH.sub(lambda m: (keep.append(m.group(0)), f"\x01{len(keep)-1}\x01")[1], text)
    held = held.replace("*", "")
    held = re.sub(r"\x01(\d+)\x01", lambda m: keep[int(m.group(1))], held)
    return re.sub(r"\x00F(\d+)\x00", lambda m: maths[int(m.group(1))], held)


class Book:
    def __init__(self, here, zip_name, *, html_name=None, images_subdir=None,
                 drop=(), source_fixes=(), long_side=2000, skip_classes=(),
                 transnote=True, flatten=(), replace=None):
        self.here = Path(here)
        self.dir = self.here.name
        self.zip = zipfile.ZipFile(self.here / "_src" / zip_name)
        names = self.zip.namelist()
        self.html_name = html_name or next(n for n in names if n.endswith((".html", ".htm")))
        self.images_subdir = images_subdir
        self.drop = dict(drop) if not isinstance(drop, dict) else drop
        self.source_fixes = list(source_fixes)
        self.long_side = long_side
        self.skip_classes = set(skip_classes) | {"pagenum", "pageno", "tnote"}
        self.transnote = transnote
        # more wrapper classes to open, per book (the Snark's intro/maintext)
        self.flatten = {"pg_body_wrapper", "chapter", "section", "blockquot", "container"} | set(flatten)
        # a better scan of a plate: {source name: local path}. The plate keeps
        # its place and id from the transcription; only the pixels change.
        self.replace = dict(replace or {})

    # ---------------------------------------------------------------- source
    def html(self):
        h = self.zip.read(self.html_name).decode("utf-8", "replace")
        for bad, good, why in self.source_fixes:
            n = h.count(bad)
            assert n == 1, f"SOURCE_FIX {bad!r} matches {n} times ({why})"
            h = h.replace(bad, good)
        return h

    def body_html(self, h):
        s = h.index("</header>") + len("</header>") if "</header>" in h else h.index("*** START")
        e = h.index('<footer class="pg-boilerplate') if 'class="pg-boilerplate' in h[s:] else h.index("*** END")
        return h[s:e]


class Walker:
    """Flattens the body into a stream (see the module docstring)."""

    def __init__(self, book, soup):
        self.book = book
        self.notes = {}
        self.pending = []
        self.tex = []                       # every formula emitted, in order
        for d in soup.select("div.footnotes, div.footnote, p.footnote"):
            for a in d.find_all("a", id=re.compile(r"(?i)^f(oot)?n(ote)?_?\w+$")):
                key = a["id"]
                p = a.find_parent(["p", "div"])
                # a note of several paragraphs (or with a table) is the whole
                # div.footnote, not the paragraph holding its anchor
                box = a.find_parent("div", class_="footnote")
                if box is not None and len(box.find_all(["p", "table", "blockquote", "div"], recursive=False)) > 1:
                    p = box
                a.decompose()
                if p is not None and key not in self.notes:
                    self.notes[key] = p
            if d.name == "div" and "footnotes" in (d.get("class") or []):
                for h in d.find_all(re.compile("^h[1-6]$")):
                    h.decompose()
        self.note_text = {}
        for key, p in self.notes.items():
            kids = p.find_all(["p", "table", "blockquote", "div"], recursive=False) if p.name == "div" else []
            if len(kids) > 1:
                items = self.stream_list(kids)
                assert items and items[0][0] == "P", key
                self.note_text[key] = [("P", "Footnote: " + items[0][1])] + items[1:]
            else:
                self.note_text[key] = [("P", "Footnote: " + self.para(p, collect=False))]
            p.decompose()
        for d in soup.select("div.footnotes"):
            d.decompose()

    def inline(self, el):
        out = []
        for c in el.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                # A compound broken at the HTML's line end ("psycho-\nanalysts")
                # would come out "psycho- analysts" once whitespace collapses.
                # A suspended hyphen ("sand- or emery-paper") is left alone.
                out.append(re.sub(r"(\w)-\r?\n[ \t]*(?!(?:or|and|to|nor)\b)(\w)", r"\1-\2", str(c)))
                continue
            if not isinstance(c, Tag):
                continue
            cls = set(c.get("class") or [])
            if cls & self.book.skip_classes:
                continue
            if c.name == "img":
                tex = c.get("data-tex")
                if tex:
                    out.append(" " + tex.strip() + " ")
                    self.tex.append(tex.strip())
                # decorative inline images (initials) carry nothing
                continue
            if c.name == "a" and ("fnanchor" in cls or re.fullmatch(r"\[?\d+\]?|\*|†|‡", clean(c.get_text()) or "x")) \
                    and c.get("href", "").startswith("#") and ("fn" in c["href"].lower() or "foot" in c["href"].lower() or "note" in c["href"].lower()):
                self.pending.append(c["href"][1:])
                continue
            if c.name == "br":
                out.append(" ")
            elif c.name in ("i", "em", "cite"):
                inner = clean(self.inline(c))
                out.append(f"*{inner}*" if inner else "")
            elif c.name in ("b", "strong"):
                out.append(self.inline(c))
            elif c.name == "sup":
                t = clean(c.get_text())
                out.append(t.translate(SUP) if all(ch in "0123456789+-=()n" for ch in t) else "^" + t)
            elif c.name == "sub":
                t = clean(c.get_text())
                out.append(t.translate(SUB) if all(ch in "0123456789+-=()" for ch in t) else "_" + t)
            else:
                out.append(self.inline(c))
        return "".join(out)

    def para(self, el, collect=True):
        t = clean(self.inline(el))
        t = re.sub(r"(\\\)|\\\]) ([.,;:!?)])", r"\1\2", t)
        t = re.sub(r"\( (\\\()", r"(\1", t)
        return emph_safe(t)

    def flat(self, nodes):
        for n in nodes:
            if isinstance(n, Tag) and n.name == "div" and not n.find(re.compile("^h[1-6]$"), recursive=False) is None:
                pass
            if isinstance(n, Tag) and n.name in ("div", "section") and (
                    not n.get("class") or set(n["class"]) & self.book.flatten) \
                    and not (set(n.get("class") or []) & {"poetry-container", "poetry", "figcenter", "figleft", "figright", "footnote"}):
                yield from self.flat(n.children)
            else:
                yield n

    def stream_list(self, nodes):
        wrap = BeautifulSoup("<div></div>", "html.parser").div
        for n in nodes:
            wrap.append(n.extract() if n.parent is not None else n)
        pend, self.pending = self.pending, []
        out = self.stream(wrap)
        self.pending = pend
        return out

    def stream(self, soup):
        out = []
        for el in self.flat(list(soup.children)):
            if not isinstance(el, Tag):
                if isinstance(el, NavigableString) and not isinstance(el, Comment) and clean(str(el)):
                    out.append(("P", emph_safe(clean(str(el)))))
                continue
            cls = set(el.get("class") or [])
            if cls & self.book.skip_classes:
                continue
            if el.name in ("br", "a") and not clean(el.get_text()):
                continue                       # spacer <br>, empty anchor
            if el.name in ("map", "area", "script", "style"):
                continue                       # an image map carries nothing
            if re.fullmatch(r"h[1-6]", el.name):
                out.append(("H", int(el.name[1]), clean(self.inline(el))))
                continue
            if el.name == "hr":
                out.append(("HR",))
                continue
            if el.name in ("figure", "img") or cls & {"figcenter", "figleft", "figright", "fig", "figure", "illustration"}:
                imgs = [el] if el.name == "img" else el.find_all("img")
                cap = el.find(["figcaption"]) or el.find(class_=re.compile("caption"))
                printed = clean(self.inline(cap)) if cap else ""
                for k, img in enumerate(imgs):
                    if img.get("data-tex"):
                        continue
                    out.append(("PLATE", img["src"].split("/")[-1], printed if k == len(imgs) - 1 else ""))
                continue
            if el.name == "table":
                rows = []
                for tr in el.find_all("tr"):
                    cells = [self.para(td) for td in tr.find_all(["td", "th"])]
                    rows.append("\t" + " | ".join(cells))
                if rows:
                    out.append(("BLOCK", "\n".join(rows)))
                continue
            if el.name == "pre":
                lines = el.get_text().replace("\r", "").split("\n")
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                if lines:
                    ind = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
                    out.append(("BLOCK", "\n".join("\t" + l[ind:].rstrip() for l in lines)))
                continue
            if cls & {"poetry-container", "poetry"} or el.select_one(".stanza, .verse"):
                for st in (el.select(".stanza") or [el]):
                    lines = []
                    # lines are .verse/.line, or span.i0/i1/..., or bare text
                    # broken by <br> (James's one-line quotations were lost
                    # when only the first shape was known)
                    # ... and "iq" / "i2q", a line that opens on a quotation
                    # mark and hangs it: matching only i\d+ dropped every
                    # such line (Hoffmann's Byron couplet lost its first)
                    vs = st.select(".verse, .line") or st.find_all("span", class_=re.compile(r"^i\d*q?$"))
                    if vs:
                        for v in vs:
                            t = clean(self.inline(v))
                            if t:
                                c = " ".join(v.get("class") or [])
                                m = re.search(r"indent(\d+)", c) or re.fullmatch(r"i(\d+)q?", c)
                                lines.append("\t" + "  " * (int(m.group(1)) if m else 0) + t)
                    else:
                        for br in st.find_all("br"):
                            br.replace_with("\x00")
                        lines = ["\t" + clean(t) for t in self.inline(st).split("\x00") if clean(t)]
                    if lines:
                        out.append(("BLOCK", "\n".join(lines)))
                continue
            if el.name in ("ul", "ol"):
                for li in el.find_all("li", recursive=False):
                    t = self.para(li)
                    if t:
                        out.append(("P", t))
                continue
            if el.name in ("p", "div", "blockquote", "dl", "span", "center"):
                figs = el.find_all(["figure"]) + el.find_all(class_=re.compile(r"^fig"))
                if el.name == "p" and figs and not el.find("table"):
                    # A PLATE FLOATED INTO A SENTENCE (James, Fig. 3: "formed
                    # by a tough [plate] white membrane"). Splitting around it
                    # cut the sentence in two; the plate goes after the
                    # paragraph instead, which is where a reader looks.
                    figs = [f for f in figs if not any(g in f.parents for g in figs)]
                    for f in figs:
                        f.extract()
                    t = self.para(el)
                    if t:
                        out.append(("P", t))
                        for n in self.pending:
                            if n in self.note_text:
                                out.extend(self.note_text.pop(n))
                        self.pending = []
                    out.extend(self.stream_list(figs))
                    continue
                if el.find(["figure", "table"]) or el.find(class_=re.compile("fig")):
                    # a block wrapping a plate: split around it
                    out.extend(self.stream(el))
                    continue
                t = self.para(el)
                if t:
                    out.append(("P", t))
                    for n in self.pending:
                        if n in self.note_text:
                            out.extend(self.note_text.pop(n))
                    self.pending = []
                continue
            raise SystemExit(f"unhandled <{el.name} {sorted(cls)}>: {clean(el.get_text())[:80]!r}")
        return out


def raw_words(body):
    b = re.sub(r"<span class=\"pagenum.*?</span>", " ", body, flags=re.S)
    b = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", b, flags=re.S)
    b = re.sub(r"<img[^>]*>", " ", b)
    t = HTML.unescape(re.sub(r"<[^>]+>", " ", b))
    return len([w for w in t.split() if re.search(r"\w", w)])


def words(items):
    n = 0
    for it in items:
        if it[0] in ("P", "BLOCK"):
            t = mathml.MATH.sub(" ", it[1]).replace("*", "").replace(" | ", " ")
            n += len([w for w in t.split() if re.search(r"\w", w)])
        elif it[0] == "H":
            n += len(it[2].split())
    return n


def compose(book, sections, *, plates, captions_dir=None, front=None):
    """sections: [{"title", "stream", "part_before"?, "chapter"?}].
    plates: list of {"src", "printed"} in first-seen order (from place())."""
    here = book.here
    rows = [{"id": L[i // 26] + L[i % 26], "source": p["src"], "printed": p["printed"]}
            for i, p in enumerate(plates)]
    pin = here / "plates.json"
    if rows:
        if pin.exists():
            old = json.loads(pin.read_text())
            assert [(r["id"], r["source"]) for r in old] == [(r["id"], r["source"]) for r in rows], "plate ids moved"
        pin.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
        copy_plates(book, rows)
    by_src = {r["source"]: r for r in rows}
    caps = {}
    cdir = here / "captions"
    if cdir.is_dir():
        for f in sorted(cdir.glob("*.txt")):
            for line in f.read_text().splitlines():
                if line.strip() and not line.startswith("#"):
                    k, _, v = line.partition("\t")
                    assert k.strip() not in caps, f"{k} captioned twice"
                    caps[k.strip()] = v.strip()
    assert not set(caps) - set(by_src[r]["id"] for r in by_src), "caption for an unknown plate"
    for d in ("chapters", "modern_chapters"):
        (here / d).mkdir(exist_ok=True)
        for f in (here / d).glob("*.txt"):
            f.unlink()
    manifest, described = [], 0
    for idx, s in enumerate(sections):
        src, mod = [s["title"], ""], [s["title"], ""]
        for it in s["stream"]:
            if it[0] == "PLATE":
                r = by_src[it[1]]
                desc = caps.get(r["id"], "")
                described += bool(desc)
                cap = " — ".join(y for y in (r["printed"], desc) if y)
                src.append(f"[Figure {r['id']}]")
                mod.append(f"[Figure {r['id']}: {cap}]" if cap else f"[Figure {r['id']}]")
            elif it[0] == "HR":
                src.append("* * *"); mod.append("* * *")
            elif it[0] == "H":
                src.append(it[2]); mod.append(it[2])
            else:
                src.append(it[1]); mod.append(it[1])
            src.append(""); mod.append("")
        (here / "chapters" / f"{idx:03d}.txt").write_text("\n".join(src).rstrip() + "\n")
        (here / "modern_chapters" / f"{idx:03d}.txt").write_text("\n".join(mod).rstrip() + "\n")
        e = {"file": f"{idx:03d}.txt", "title": s["title"], "part": 1, "of": 1}
        if s.get("part_before"):
            e["part_before"] = s["part_before"]
        if s.get("chapter"):
            e["chapter"] = True
        manifest.append(e)
    (here / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    texs = [f for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK") for f in mathml.formulas(it[1])]
    if texs:
        mathml.convert_all(texs)
    return rows, described


def copy_plates(book, rows):
    from PIL import Image
    out = ROOT / "site" / "images" / book.dir
    out.mkdir(parents=True, exist_ok=True)
    for f in out.iterdir():
        f.unlink()
    names = {n.split("/")[-1]: n for n in book.zip.namelist()}
    for r in rows:
        rp = book.replace.get(r["source"])
        data = Path(rp).read_bytes() if rp else book.zip.read(names[r["source"]])
        im = Image.open(io.BytesIO(data))
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if has_alpha and im.convert("RGBA").getchannel("A").getextrema()[0] == 255:
            # an alpha channel with nothing transparent in it: se lint's
            # f-019 rejects such a PNG, so it goes out as a JPEG (Newcomb)
            has_alpha = False
        if max(im.size) > book.long_side:
            im.thumbnail((book.long_side, book.long_side))
        elif not has_alpha and r["source"].lower().endswith((".jpg", ".jpeg")):
            (out / f"fig{r['id']}.jpg").write_bytes(data)
            continue
        if has_alpha:
            im.save(out / f"fig{r['id']}.png", optimize=True)
        else:
            im.convert("RGB").save(out / f"fig{r['id']}.jpg", "JPEG", quality=88)


def check_formulas(walker, sections):
    """Every data-tex the walker read, in order, must reach the text."""
    norm = lambda t: re.sub(r"\s+", " ", mathml.formulas(t)[0][0] if mathml.formulas(t) else t).strip()
    src = [norm(t) for t in walker.tex]
    got = [re.sub(r"\s+", " ", t).strip() for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK")
           for t, _ in mathml.formulas(it[1])]
    # footnote formulas were read by the walker too
    assert sorted(src) == sorted(got), f"formula witness: read {len(src)}, emitted {len(got)}"


def all_images_placed(book, plates, extra_ok=()):
    on_disk = {n.split("/")[-1] for n in book.zip.namelist()
               if re.search(r"\.(jpg|jpeg|png|gif)$", n, re.I)}
    placed = [p["src"] for p in plates]
    assert len(placed) == len(set(placed)), "a plate placed twice"
    missing = on_disk - set(placed) - set(book.drop) - set(extra_ok)
    assert not missing, f"images never placed: {sorted(missing)[:10]}"


def text_fixes(sections, fixes):
    """(bad, good, why[, count]) applied to the walked text, each asserted
    to match exactly `count` times (default 1). Applied after walking, so
    a phrase wrapped across lines in the HTML still matches."""
    for fx in fixes:
        bad, good, why = fx[:3]
        want = fx[3] if len(fx) > 3 else 1
        n = 0
        for s in sections:
            for k, it in enumerate(s["stream"]):
                if it[0] in ("P", "BLOCK") and bad in it[1]:
                    n += it[1].count(bad)
                    s["stream"][k] = (it[0], it[1].replace(bad, good)) + tuple(it[2:])
        assert n == want, f"text fix {bad!r} matched {n} times, expected {want} ({why})"


def respell(sections, pairs):
    """Word-level spelling restoration, e.g. judgement -> judgment. Case is
    kept; returns the count per pair so the prep can assert it."""
    counts = {}
    for bad, good in pairs:
        pat = re.compile(r"\b" + bad + r"\b")
        cap = re.compile(r"\b" + bad[:1].upper() + bad[1:] + r"\b")
        n = 0
        for s in sections:
            for k, it in enumerate(s["stream"]):
                if it[0] in ("P", "BLOCK"):
                    t, a = pat.subn(good, it[1])
                    t, b = cap.subn(good[:1].upper() + good[1:], t)
                    n += a + b
                    s["stream"][k] = (it[0], t) + tuple(it[2:])
        counts[bad] = n
    return counts


def mend_plate_splits(sections):
    """A paragraph the TRANSCRIPTION cut in two around a plate: the first
    half ends mid-sentence, the plates follow, the second half opens in
    lower case. Join the halves and set the plates after the paragraph.
    Returns how many were mended, for the prep to assert."""
    n = 0
    for s in sections:
        st = s["stream"]
        k = 0
        while k < len(st):
            if st[k][0] == "P" and re.search(r"[a-z,;]$", st[k][1]):
                j = k + 1
                while j < len(st) and st[j][0] == "PLATE":
                    j += 1
                if j > k + 1 and j < len(st) and st[j][0] == "P" and re.match(r"[a-z]", st[j][1]):
                    plates = st[k + 1:j]
                    st[k:j + 1] = [("P", st[k][1] + " " + st[j][1])] + plates
                    n += 1
                    continue
            k += 1
    return n
