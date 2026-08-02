"""Build chapters/ + manifest.json for John Tyndall's SOUND from the
Gutenberg HTML edition (#54969, the 1903 Collier printing of the third
edition of 1875).

THE SEVENTH Royal Institution lecture volume in the collection, after
soap-bubbles/, candle/, forces/, fleming/, ball/ and thompson/ — and the
ancestor of all of them. Tyndall invented the lecture-demonstration style
the others descend from, and these are the lectures he gave at the Royal
Institution in 1867.

SOURCE. Unlike thompson/, this is a proofread Gutenberg text, so none of
the OCR repair machinery is needed. But the plain-text edition drops the
figure captions, so — as with soap-bubbles/ and candle/ — prep reads the
HTML edition instead, which carries both the text and the 186 numbered
figures in their proper places.

WHY PARSE THE HTML RATHER THAN THE TXT. The HTML gives, for free, four
things the plain text has thrown away:

  1. Figure position AND number. Every plate sits in a figure div whose
     caption div names it ("Fig. 1.", "Fig. 134.  Fig. 135."). No
     inference required, and no placement heuristics.
  2. The section structure: nine chapters, each divided into numbered
     sections whose headings are the book's own, and each closing with
     Tyndall's own SUMMARY OF CHAPTER N.
  3. Footnote anchors. The 94 footnotes sit at the back of the book,
     linked to their citation points; they are inlined here after the
     paragraph that cites them, as in candle/.
  4. The 34 tables, as tables. In the plain text they are columns of
     numbers held together by spaces and nothing else.

FIGURES. 186 numbered figures plus the Fog-Siren frontispiece. Several
plates carry more than one number ("Figs. 134, 135") and take the
hyphenated compound ids that forces/ introduced. Note that the figure
NUMBER must be read from the caption and not from the img alt: the alt
carries a transcription slip ("&gt;Fig. 38.") and four of the wave
diagrams put their interval ratio in the caption too ("Fig. 182. 1:2."),
so only digits that directly follow a "Fig."/"Figs." token count.

MATH. Two displayed equations were rendered as images by the transcriber
rather than set as text. They are transcribed below. A formula that
exists only as a picture cannot be read aloud, searched or resized —
and, as thompson/ proved at length, cannot be guessed either: the first
of these is Cp/Cv = V'^2/V^2, not the square root I assumed before
looking at it, and the second is 1.42, not 1.41.

Ratio note for verify: English -> English modernization of spoken lecture
prose, as the other six. Run verify.py with --min-ratio 0.85
--max-ratio 1.3.
"""

import html as htmllib
import json
import re
import shutil
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

BOOK = Path(__file__).parent
SITE_IMG = BOOK.parent / "site/images/tyndall"
TARGET = 2800
MAX = 3500

# Displayed equations the transcriber rendered as images (Laplace's
# correction to Newton's velocity of sound, and the ratio it yields).
MATH = {
    "mathtex1.jpg": "Cp / Cv  =  V′² / V²",
    "mathtex2.jpg": "Cp / Cv  =  1.42",
}

# Section boundaries, in document order. Everything before the first and
# after the last is Gutenberg wrapper, contents, index or licence.
TITLES = [
    ("PREFACE TO THE THIRD EDITION", "Front Matter"),
    ("PREFACE TO THE FIRST EDITION", "Front Matter"),
    ("CHAPTER I", "Chapter One: The Nature of Sound"),
    ("CHAPTER II", "Chapter Two: Pitch, and How It Is Measured"),
    ("CHAPTER III", "Chapter Three: Vibrating Strings"),
    ("CHAPTER IV", "Chapter Four: Vibrating Rods, Plates and Bells"),
    ("CHAPTER V", "Chapter Five: Resonance, Organ-Pipes and the Voice"),
    ("CHAPTER VI", "Chapter Six: Singing Flames and Sensitive Flames"),
    ("CHAPTER VII", "Chapter Seven: Sound in the Open Air"),
    ("CHAPTER VIII", "Chapter Eight: The Interference of Sound"),
    ("CHAPTER IX", "Chapter Nine: Musical Consonance and Dissonance"),
    ("APPENDIX I", "Appendix One"),
    ("APPENDIX II", "Appendix Two"),
]

FIG_CLASS = re.compile(r"figcenter|figleft|figright")
SENTINEL = "\x00FIG:%s\x00"


def unpack():
    work = BOOK / "html"
    if not (work / "pg54969-images.html").exists():
        work.mkdir(exist_ok=True)
        with zipfile.ZipFile(BOOK / "h.zip") as z:
            z.extractall(work)
    return work


def clean(node):
    """Visible text of a node, with page numbers and footnote-anchor
    superscripts removed first, and whitespace collapsed."""
    for junk in node.select("span.pagenum, a.fnanchor"):
        junk.decompose()
    # join with "" not " ": the printed text already carries its own
    # spaces, and a separator splits every dropcap from its word
    # ("<span class=dropcap>T</span>HE" -> "T HE")
    for br in node.find_all("br"):
        br.replace_with(" ")
    t = htmllib.unescape(node.get_text(""))
    t = t.replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def figure_id(caption, alt):
    """'Fig. 1.' -> '1'; 'Fig. 134.  Fig. 135.' -> '134-135';
    'From top: Figs. 143, 144, 145.' -> '143-144-145';
    'Fig. 182. 1:2.' -> '182' (the 1:2 is the interval the diagram draws,
    not a second figure number); 'Fog-Siren' -> 'front'.

    A TRAILING LETTER IS PART OF THE NUMBER. The Helmholtz resonator is
    captioned "Fig. 94a" — a fifth plate on a page that already has a
    Fig. 94 — and a regex reading only digits gives it the id 94, which
    silently overwrites the bell of section 9 with the resonator and then
    prints the resonator twice. Neither the word ratio nor the figure
    parity check can see that: both markers exist and both are placed.

    Singular "Fig. N" tokens are collected one by one, because a plate
    carrying two figures captions them separately; a plural "Figs." is
    followed by a comma-list and is read as a list."""
    for src in (caption, alt):
        if not src:
            continue
        nums = re.findall(r"Fig\.\s*(\d+[a-z]?)", src)
        plural = re.search(r"Figs\.\s*([\d,\s]+)", src)
        if plural:
            nums += re.findall(r"\d+", plural.group(1))
        seen, out = set(), []
        for x in nums:
            if x not in seen:
                seen.add(x); out.append(x)
        if out:
            return "-".join(out)
        if "Fog-Siren" in src:
            return "front"
    return None


def stamp_figures(soup, figs):
    """Replace every plate — however it is wrapped — with a sentinel string
    left in place in the document.

    The plates come in three wrappings and only one of them is a plain
    block: 118 sit in their own <div>, 30 are FLOATED INSIDE A PARAGRAPH as
    <span class="figright250">, and 42 sit in cells of a layout <table>
    that puts two or three of them side by side. Handling only the first
    shape loses a fifth of the plates and, worse, leaves the floated ones'
    captions embedded in the running prose, where they read as stray text.
    Turning all three into one sentinel makes the rest of the walk simple:
    a paragraph splits around its sentinels, and a table that contains one
    is a layout table, not data.

    THE APPENDIX RESTARTS THE NUMBERING. Appendix II has its own Figs. 1
    to 4, and the book already has four plates by those names in chapter
    one. Plates found after an APPENDIX heading therefore take a
    namespaced id ("app_1"), which assemble.figure_label strips back to
    "Figure 1" for the reader while keeping the two files apart. Without
    it the appendix quietly overwrote the row of solitaire balls, the row
    of boys, Cottrell's spring model and the bell in the air pump with
    four sensitive-flame diagrams from the back of the book."""
    n, ns = 0, ""
    for node in soup.find_all(["h2", "h3", "div", "span"]):
        if node.name in ("h2", "h3"):
            t = clean(node).upper()
            if t.startswith("APPENDIX"):
                ns = "app_"
            elif t.startswith("CHAPTER"):
                ns = ""
            continue
        if not FIG_CLASS.search(" ".join(node.get("class", []))):
            continue
        img = node.find("img")
        if not img:
            continue
        src = img.get("src", "").rsplit("/", 1)[-1]
        cap = node.find(class_="caption")
        fid = "MATH:" + src if src in MATH else figure_id(
            clean(cap) if cap else None, img.get("alt"))
        if not fid:
            continue
        if not fid.startswith("MATH:"):
            fid = "-".join(ns + p for p in fid.split("-"))
            # a silent overwrite here loses a plate and duplicates another
            if figs.get(fid, src) != src:
                raise SystemExit(f"figure id {fid} claimed by two plates: "
                                 f"{figs[fid]} and {src}")
            figs[fid] = src
        # A bare replacement string would end up as a child of <body> for
        # the standalone plates, where the walk never looks. Leave a real
        # inline node instead: it survives inside a paragraph, inside a
        # table cell, and on its own between blocks.
        stamp = soup.new_tag("span")
        stamp["class"] = "mc-fig"
        stamp.string = SENTINEL % fid
        node.replace_with(stamp)
        n += 1
    return n


def emit(text, out, section):
    """Emit a cleaned string, breaking it around any figure sentinels."""
    for piece in re.split(r"\x00FIG:([\w:.-]+)\x00", text):
        piece = piece.strip()
        if not piece:
            continue
        if piece.startswith("MATH:"):
            out.append((section, "    " + MATH[piece[5:]]))
        elif re.fullmatch(r"[\w-]+", piece) and piece in emit.ids:
            out.append((section, f"[Figure {piece}]"))
        else:
            out.append((section, piece))


emit.ids = set()


def render_table(tab):
    """A table becomes an indented block, which assemble.py renders as
    <pre>. Columns are padded to line up, because a table whose columns do
    not line up is not a table."""
    rows = []
    for tr in tab.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            # class="h" is the transcriber's hidden spacing text: it spells
            # out the words a ditto mark stands under, so that the marks
            # line up. Take it out and the cell is bare ditto marks.
            for hid in td.select("span.h"):
                hid.decompose()
            cells.append(clean(td))
        while cells and not cells[-1]:
            cells.pop()
        # a row drawn entirely out of rule characters is a printed brace
        # spanning two columns, not data
        if any(cells) and not all(re.fullmatch(r"[╭╮—^_|\s]*", c) for c in cells):
            rows.append(cells)
    if not rows:
        return None
    # expand ditto marks from the row above: a modern reader wants the
    # value, and a screen reader cannot say "ditto"
    width0 = max(len(r) for r in rows)
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            if i and re.fullmatch(r"[”\"“',,]+", c) and j < len(rows[i - 1]):
                r[j] = rows[i - 1][j]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    cols = [max(len(r[i]) for r in rows) for i in range(width)]
    out = []
    for r in rows:
        line = "    " + "  ".join(c.ljust(cols[i]) for i, c in enumerate(r))
        out.append(line.rstrip())
    return "\n".join(out)


def subhead(text):
    """A section heading becomes a plain title-case line. assemble.py reads
    a short line with no terminal punctuation as an <h4>; a terminal period
    is the difference between a subheading and a paragraph shouted in
    capitals, so it is stripped."""
    t = re.sub(r"^§\s*\d+\.\s*", "", text).strip().rstrip(".")
    if t.isupper():
        t = t.title()
        for small in (" Of ", " The ", " A ", " An ", " And ", " In ",
                      " On ", " To ", " By ", " For ", " Or "):
            t = t.replace(small, small.lower())
        t = t[0].upper() + t[1:]
    # "Summary of Chapter IX" — .title() turns the roman numeral into "Ix"
    t = re.sub(r"\b(Chapter|Appendix|Part)\s+([IVXivx]+)\b",
               lambda m: f"{m.group(1)} {m.group(2).upper()}", t)
    return t


def collect_footnotes(soup):
    notes = {}
    for div in soup.select("div.footnote"):
        a = div.find("a", id=re.compile(r"^Footnote_"))
        if not a:
            continue
        key = a["id"]
        lab = div.find("span", class_="label")
        if lab:
            lab.decompose()
        notes[key] = clean(div)
    return notes


def walk(soup, notes):
    """Walk the body in document order and emit (section_key, paragraph)
    pairs. `None` for the paragraph marks the start of a section."""
    body = soup.find("body")
    keys = [k for k, _ in TITLES]
    section, out, cited = None, [], set()
    # the Fog-Siren frontispiece stands before the first heading; hold it
    # and let it open the front matter
    pending = []
    for node in body.find_all(["h2", "h3", "h4", "p", "div", "table",
                               "blockquote", "span"], recursive=True):
        if node.find_parent(["div", "table"], class_="footnote"):
            continue
        if node.find_parent("table") and node.name != "table":
            continue                      # cells are handled with the table
        if node.name == "span":
            # a stamped plate standing on its own between two blocks; one
            # inside a paragraph comes out with that paragraph's text
            if "mc-fig" not in node.get("class", []) or \
                    node.find_parent(["p", "blockquote"]):
                continue
            if section:
                emit(node.get_text(), out, section)
            else:
                pending.append(node.get_text())
            continue
        if node.name in ("h2", "h3", "h4"):
            t = clean(node)
            # A section key may arrive at any heading level: the two
            # appendices are <h3> under an <h2>APPENDICES</h2> wrapper.
            if t in keys:
                section = t
                out.append((section, None))
                for held in pending:
                    emit(held, out, section)
                pending = []
                # the two prefaces share one Front Matter section, so each
                # keeps its own heading as a subheading inside it
                if dict(TITLES)[t] == "Front Matter":
                    out.append((section, t.title()
                                .replace("Preface To The", "Preface to the")))
            elif node.name == "h2":
                section = None          # contents, index, footnotes, licence
            elif section:
                out.append((section, subhead(t)))
            continue
        if not section:
            continue
        if node.name == "table":
            # a table holding plates is a layout device, not data
            raw = node.get_text(" ")
            if "\x00FIG:" in raw:
                for fid in re.findall(r"\x00FIG:([\w:.-]+)\x00", raw):
                    emit(SENTINEL % fid, out, section)
                continue
            blk = render_table(node)
            if blk:
                out.append((section, blk))
            continue
        if node.name == "blockquote":
            emit(clean(node), out, section)
            continue
        # ordinary paragraph — may have plates floated inside it.
        # NOTE the order: clean() decomposes the footnote anchors as it
        # goes, so the citations have to be read off the node first.
        cites = [a["href"][1:] for a in node.select("a.fnanchor")
                 if a.get("href", "").startswith("#Footnote_")]
        txt = clean(node)
        if txt == "SOUND":       # the half-title before Chapter I
            continue
        # a short line shouted in capitals is a heading the transcriber set
        # as a paragraph; title-case it so it reads as one
        if txt.isupper() and len(txt.split()) <= 10:
            txt = subhead(txt)
        emit(txt, out, section)
        for c in cites:
            if c in notes:
                out.append((section, "Footnote: " + notes[c]))
                cited.add(c)
    return out, set(notes) - cited


def split_body(paras):
    words = [len(p.split()) for p in paras]
    total = sum(words)
    if total <= MAX:
        return [paras]
    nparts = max(2, round(total / TARGET))
    per = total / nparts
    cum = [0]
    for w in words:
        cum.append(cum[-1] + w)
    cuts, lo = [], 1
    for k in range(1, nparts):
        target = k * per
        best, best_d = None, None
        for i in range(lo, len(paras)):
            if paras[i - 1].startswith("[Figure"):
                continue
            d = abs(cum[i] - target)
            if best_d is None or d < best_d:
                best, best_d = i, d
        cuts.append(best)
        lo = best + 1
    edges = [0] + cuts + [len(paras)]
    return [paras[a:b] for a, b in zip(edges, edges[1:])]


def body_words(text):
    return len(re.sub(r"^\[Figure[^\]]*\]$", "", text, flags=re.M).split())


def main():
    work = unpack()
    soup = BeautifulSoup((work / "pg54969-images.html").read_text("utf-8"),
                         "html.parser")
    notes = collect_footnotes(soup)
    print(f"{len(notes)} footnotes collected")
    figs = {}
    print(f"{stamp_figures(soup, figs)} plates stamped "
          f"({len(figs)} distinct ids)")
    emit.ids = set(figs)
    items, missing = walk(soup, notes)
    if missing:
        raise SystemExit(f"footnotes never cited: {sorted(missing)[:8]}")

    SITE_IMG.mkdir(parents=True, exist_ok=True)
    for fid, src in figs.items():
        ext = src.rsplit(".", 1)[-1].lower()
        shutil.copy(work / "images" / src, SITE_IMG / f"fig{fid}.{ext}")
    print(f"copied {len(figs)} plates to {SITE_IMG}")

    # group into sections, in the order TITLES gives
    order, seen = [], {}
    for key, par in items:
        title = dict(TITLES)[key]
        bucket = "Front Matter" if title == "Front Matter" else key
        if bucket not in seen:
            seen[bucket] = []
            order.append(bucket)
        if par is not None:
            seen[bucket].append(par)
    TITLE_OF = {k if dict(TITLES)[k] != "Front Matter" else "Front Matter":
                dict(TITLES)[k] for k, _ in TITLES}

    (BOOK / "chapters").mkdir(exist_ok=True)
    manifest, n = [], 0
    for key in order:
        title = TITLE_OF[key]
        paras = seen[key]
        if not paras:
            continue
        parts = split_body(paras)
        for i, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            text = "\n\n".join(part)
            (BOOK / "chapters" / fname).write_text(text + "\n")
            manifest.append({"file": fname, "title": title, "part": i,
                             "of": len(parts), "words": body_words(text)})
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    for m in manifest:
        print(f"  {m['file']}  {m['words']:>5}  {m['title'][:50]} "
              f"({m['part']}/{m['of']})")
    used = set()
    for f in (BOOK / "chapters").glob("*.txt"):
        used |= set(re.findall(r"^\[Figure ([\w-]+)\]$", f.read_text(), re.M))
    print(f"{len(manifest)} files, {sum(m['words'] for m in manifest)} words, "
          f"{len(used)} plates placed")
    if set(figs) - used:
        print(f"  WARNING: plates copied but never placed: "
              f"{sorted(set(figs) - used)}")


if __name__ == "__main__":
    main()
