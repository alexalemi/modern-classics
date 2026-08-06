"""Build a Standard-Ebooks-quality epub from a book's modern_chapters.

    python3 build_ebook.py <book_dir> [--out-dir site/ebooks] [--skip-build]
    python3 build_ebook.py <book_dir> --original     # the source text instead

`--original` builds the companion edition of the source text from chapters/
(see assemble.py --original), into <slug>_original.epub. It differs from the
modern build in the same two ways the web page does — headings come from the
manifest, plates keep only the number the original printed — plus three that
belong to the epub: the uid is suffixed so the two editions are distinct
works to a reader's library, the colophon says the text is unmodernized
rather than retold, and dc:title carries ": The Original Text".

Reads the same data files as assemble.py (env, manifest.json,
modern_chapters/NNN.txt) plus per-book publishing metadata from
ebook_meta.json (descriptions, subjects, cover art, fiction flag).

Produces an SE-style source tree under build/ebooks/<slug>/ using the
`se` toolset (create-draft, typogrify, build-title, build-manifest,
build-spine, build-toc, clean, lint, build), with Modern Classics
branding in place of Standard Ebooks trademarks.

Requires: pipx-installed standardebooks toolset (`se` on PATH).
"""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import assemble  # reuse section parsing conventions

BUILD_ROOT = ROOT / "build" / "ebooks"
SE = shutil.which("se") or str(Path.home() / ".local/bin/se")

# se's own titlecase via subprocess — importing se into the system python
# trips a `regex` C-extension conflict. Cached per unique string.
_tc_cache = {}
def se_titlecase(s):
    if s not in _tc_cache:
        r = subprocess.run([SE, "titlecase", s], capture_output=True, text=True)
        _tc_cache[s] = (r.stdout.strip()
                        if r.returncode == 0 and r.stdout.strip() else s.title())
    return _tc_cache[s]

PART_MARK = re.compile(r"^\(Part \d+ of \d+\)$", re.I)
HEADING = re.compile(
    r"^(?:##\s*)?(?P<label>(?:Chapter|Book|Part|Letter|Essay|Section|Federalist|CHAPTER|BOOK|LETTER|PART|SECTION|FEDERALIST)(?![A-Za-z]))?"
    r"[ .:]*(?:No\.\s*)?(?P<ord>[IVXLC]+\b|[ivxlc]+\b|\d+\b)?[.:]?\s*(?P<title>.*)$")

FRONT_BACK_TYPES = {
    "introduction": "introduction", "preface": "preface", "foreword": "foreword",
    "dedication": "dedication", "prologue": "prologue", "proem": "preface",
    "epilogue": "epilogue", "conclusion": "conclusion", "afterword": "afterword",
    "appendix": "appendix",
}
FRONTMATTER = {"dedication", "preface", "foreword"}
BACKMATTER = {"appendix", "afterword"}

XHTML_HEAD = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/, se: https://standardebooks.org/vocab/1.0" xml:lang="en-US">
\t<head>
\t\t<title>{title}</title>
\t\t<link href="../css/core.css" rel="stylesheet" type="text/css"/>
\t\t<link href="../css/local.css" rel="stylesheet" type="text/css"/>
\t</head>
\t<body epub:type="bodymatter {fic}">
"""

def esc(s):
    return html.escape(s, quote=False)


def slugify(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # match se create-draft: apostrophes vanish rather than become dashes
    text = re.sub(r"[''’]", "", text)
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def is_all_caps(s):
    letters = [c for c in s if c.isalpha()]
    return letters and all(c.isupper() for c in letters)


def nice_title(s):
    s = s.strip().rstrip(".,;")
    if is_all_caps(s):
        s = se_titlecase(s.lower())
    return s


NUMBER_WORDS = {w: str(i + 1) for i, w in enumerate(
    ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
     "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
     "eighteen", "nineteen", "twenty"])}

NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
     "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
     "sixteen", "seventeen", "eighteen", "nineteen", "twenty"])}

def parse_heading(raw):
    """'CHAPTER IV. OF X' -> ('Chapter', 'IV', 'Of X'); bare titles -> (None, None, title)."""
    m = HEADING.match(raw.strip())
    label = (m.group("label") or "").title() or None
    ordinal = m.group("ord") or None
    title = nice_title(m.group("title") or "")
    if label and not ordinal and title.lower() in NUMBER_WORDS:
        ordinal, title = NUMBER_WORDS[title.lower()], ""
    if ordinal and ordinal.isalpha():
        ordinal = ordinal.upper()
    if label and not ordinal and title.lower() in NUMBER_WORDS:
        ordinal, title = NUMBER_WORDS[title.lower()], ""
    if not label and not ordinal:
        title = nice_title(raw.strip().lstrip("# ").rstrip(".,;"))
    return label, ordinal, title


def load_sections(book, original=False):
    """assemble.build_sections, with part grouping reconstructed for books
    that predate manifest.json (via '(Part n of k)' markers)."""
    mpath = book / "manifest.json"
    if mpath.exists():
        manifest = json.loads(mpath.read_text())
    else:
        files = sorted(p.name for p in (book / "modern_chapters").glob("*.txt")
                       if re.fullmatch(r"\d{3}\.txt", p.name))
        manifest = []
        for f in files:
            head = (book / "modern_chapters" / f).read_text()[:400].splitlines()
            part, of = 1, 1
            for line in head[:6]:
                pm = re.match(r"^\(Part (\d+) of (\d+)\)$", line.strip(), re.I)
                if pm:
                    part, of = int(pm.group(1)), int(pm.group(2))
                    break
            manifest.append({"file": f, "title": "", "part": part, "of": of})
    return assemble.build_sections(
        book, manifest, source="chapters" if original else "modern_chapters",
        titles=original)


def classify_block(par):
    """figure | paragraph | subhead | verse | lines"""
    stripped = par.strip()
    # must precede the subhead test: "[Figure 1]" looks like a subheading
    if assemble.FIGURE.match(stripped):
        return "figure"
    if re.search(r"^[ \t]", par, re.M):
        # AN INDENTED BLOCK HOLDING PLATES IS A TABLE. Carroll tabulates his
        # diagrams against their readings, so a figure marker is frequently
        # one CELL of a row rather than a paragraph of its own. Rendered as
        # lined matter it printed the marker as literal text and the plate
        # never appeared -- 248 of symbolic-logic's 308, all of them present
        # in the package and referenced by nothing. Mirrors the same fix in
        # assemble.render_plate_table; only a block that carries a marker
        # takes this path, so no other book's tables move.
        if FIGURE_DIR[0] and assemble.FIGURE_INLINE.search(stripped):
            return "plates"
        lines = [l.strip() for l in stripped.splitlines() if l.strip()]
        short = sum(1 for l in lines if len(l) < 65)
        if len(lines) >= 2 and short == len(lines) and not any(" -- " in l or l.endswith("--") for l in lines):
            return "verse"
        return "lines"
    if assemble.is_subheading(stripped):
        return "subhead"
    return "paragraph"


ASTERISM = re.compile(r"^(\*+( \*+)*|-{2,})$")
ERA = re.compile(r"\b([AB])\.([DC])\.")


# set from env in main(); render_block() is reached through several layers of
# generic rendering code, so the book's figure directory rides in a cell
FIGURE_DIR = [None]
# likewise for the original-text build: the source has no captions to give,
# so a plate keeps the number the book printed under it and nothing else
BARE_LABEL = [False]


def render_figure(s):
    """A "[Figure N: caption]" block, for illustrated books (FIGURE_DIR in
    env). Plates live in the draft at src/epub/images/, so text/*.xhtml
    reaches them with ../images/. A caption-less marker (a scale bar, a
    continuation plate) gets an img with no figcaption."""
    m = assemble.FIGURE.match(s)
    num = m.group(1)
    caption = " ".join(m.group(2).split()) if m.group(2) else None
    if BARE_LABEL[0]:
        caption = None
    name = assemble.figure_name(ROOT / "site", FIGURE_DIR[0] or "", num)
    label = assemble.figure_label(num)
    alt = caption or label or "Plate"
    if alt[-1] not in ".!?":       # se lint t-026 wants alt text punctuated
        alt += "."
    # alt is an ATTRIBUTE: quotes must be escaped too, or a caption that
    # names something in quotation marks produces unparseable XHTML
    out = [f'\t\t\t<figure id="fig-{num}">',
           f'\t\t\t\t<img alt="{html.escape(alt, quote=True)}" src="../images/{name}"/>']
    if caption or (BARE_LABEL[0] and label):
        if caption:
            inner = f"<b>{label}</b>—{esc(caption)}" if label else esc(caption)
        else:
            inner = f"<b>{label}</b>"   # the number the original printed
        out.append("\t\t\t\t<figcaption>\n"
                   f"\t\t\t\t\t<p>{inner}</p>\n"
                   "\t\t\t\t</figcaption>")
    out.append("\t\t\t</figure>")
    return "\n".join(out)


# se's own artwork, which lives in the same directory as the plates
SE_IMAGES = {"cover.jpg", "cover.source.jpg", "cover.svg", "titlepage.svg",
             "logo.svg"}


def copy_figures(book, env, dest):
    """Copy an illustrated book's plates into the draft. `se build-manifest`
    picks them up from src/epub/images/ on its own.

    The draft is reused between runs, so a plate that changes format has
    to be swept out or BOTH copies ship: re-cutting Thompson's 127 JPEGs
    as PNGs took the epub from 25 MB to 51 MB, because `se
    build-manifest` faithfully listed the JPEGs still sitting there."""
    figdir = env.get("FIGURE_DIR")
    if not figdir:
        return 0
    src = ROOT / "site" / figdir
    images = dest / "src/epub/images"
    images.mkdir(parents=True, exist_ok=True)
    keep, n = set(SE_IMAGES), 0
    for f in sorted(src.iterdir()):
        if f.suffix.lstrip(".").lower() in assemble.FIG_EXTS:
            shutil.copy(f, images / f.name)
            keep.add(f.name)
            n += 1
    stale = [f for f in images.iterdir()
             if f.name not in keep
             and f.suffix.lstrip(".").lower() in assemble.FIG_EXTS]
    for f in stale:
        f.unlink()
    print(f"copied {n} figures from {src}"
          + (f"; removed {len(stale)} stale" if stale else ""))
    return n

def render_block(par, kind):
    s = par.strip()
    if kind == "figure":
        return render_figure(s)
    if ASTERISM.match(re.sub(r"\s+", " ", s)):
        return "\t\t\t<hr/>"
    if kind == "paragraph":
        if is_all_caps(s) and len(s) < 200 and "\n" not in s:
            return f'\t\t\t<p class="subhead">{esc(nice_title(s))}</p>'
        text = ERA.sub(r'<abbr epub:type="se:era">\1\2</abbr>', esc(s))
        return f"\t\t\t<p>{text}</p>"
    if kind == "subhead":
        return f'\t\t\t<p class="subhead">{esc(s)}</p>'
    if kind == "plates":
        return render_plate_table(s)
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    if kind == "verse":
        inner = "\n".join(
            f'\t\t\t\t\t\t<p><span>{esc(l)}</span></p>' for l in lines)
        return ("\t\t\t<blockquote epub:type=\"z3998:verse\">\n"
                "\t\t\t\t<div>\n" + inner + "\n\t\t\t\t</div>\n\t\t\t</blockquote>")
    # generic lined matter (outlines, tables of figures, speaker lists)
    inner = "<br/>\n\t\t\t\t".join(esc(l) for l in lines)
    return f"\t\t\t<blockquote class=\"lines\">\n\t\t\t\t<p>{inner}</p>\n\t\t\t</blockquote>"


def render_plate_table(s):
    """An indented block whose cells include figure markers -> a table.

    The plate goes in as a bare <img>: the caption is already the adjacent
    cell of the same row, so a figcaption would set it twice. It rides into
    the alt instead, which is what a reader who cannot see the plate gets."""
    rows = []
    for line in s.split("\n"):
        if not line.strip():
            continue
        tds = []
        for cell in (c.strip() for c in line.strip().split(" | ")):
            parts, last = [], 0
            for m in assemble.FIGURE_INLINE.finditer(cell):
                parts.append(esc(cell[last:m.start()]))
                num = m.group(1)
                caption = " ".join(m.group(2).split()) if m.group(2) else None
                if BARE_LABEL[0]:
                    caption = None
                alt = caption or assemble.figure_label(num) or "Plate"
                if alt[-1] not in ".!?":   # se lint t-026 wants it punctuated
                    alt += "."
                name = assemble.figure_name(ROOT / "site", FIGURE_DIR[0] or "",
                                            num)
                parts.append(f'<img alt="{html.escape(alt, quote=True)}" '
                             f'src="../images/{name}"/>')
                last = m.end()
            parts.append(esc(cell[last:]))
            tds.append("\t\t\t\t\t\t<td>" + "".join(parts) + "</td>")
        rows.append("\t\t\t\t\t<tr>\n" + "\n".join(tds) + "\n\t\t\t\t\t</tr>")
    return ("\t\t\t<table>\n\t\t\t\t<tbody>\n" + "\n".join(rows)
            + "\n\t\t\t\t</tbody>\n\t\t\t</table>")


def render_body(text, indent="\t\t\t"):
    pars = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    speakers = assemble.find_speakers(pars)
    out = []
    for par in pars:
        kind = classify_block(par)
        lines = par.strip().split("\n")
        if kind == "paragraph" and len(lines) >= 2 and lines[0].strip() in speakers:
            rest = ERA.sub(r'<abbr epub:type="se:era">\1\2</abbr>',
                           esc(" ".join(l.strip() for l in lines[1:])))
            out.append(f'\t\t\t<p><b epub:type="z3998:persona">{esc(lines[0].strip())}</b>: {rest}</p>')
            continue
        out.append(render_block(par, kind))
    # a scene break at a section boundary is meaningless (and illegal per s-012)
    while out and out[0].endswith("<hr/>"):
        out.pop(0)
    while out and out[-1].endswith("<hr/>"):
        out.pop()
    return "\n".join(out)


def heading_xml(level, label, ordinal, title, subtitle=None):
    h = f"h{level}"
    parts = []
    if ordinal:
        ord_type = "z3998:ordinal z3998:roman" if ordinal.isalpha() else "z3998:ordinal"
        ord_val = f'<span epub:type="{ord_type}">{ordinal}</span>' if label else ordinal
        if label and title:
            parts.append(f'\t\t\t\t<{h}>\n\t\t\t\t\t<span epub:type="se:label">{label}</span>\n\t\t\t\t\t<span epub:type="{ord_type}">{ordinal}</span>\n\t\t\t\t</{h}>')
            parts.append(f'\t\t\t\t<p epub:type="title">{esc(title)}</p>')
            return "\t\t\t<hgroup>\n" + "\n".join(parts) + "\n\t\t\t</hgroup>"
        if title:
            parts.append(f'\t\t\t\t<{h} epub:type="{ord_type}">{ordinal}</{h}>')
            parts.append(f'\t\t\t\t<p epub:type="title">{esc(title)}</p>')
            return "\t\t\t<hgroup>\n" + "\n".join(parts) + "\n\t\t\t</hgroup>"
        if label and label != "Chapter":
            return (f'\t\t\t<{h}>\n\t\t\t\t<span epub:type="se:label">{label}</span>\n'
                    f'\t\t\t\t<span epub:type="{ord_type}">{ordinal}</span>\n\t\t\t</{h}>')
        return f'\t\t\t<{h} epub:type="{ord_type}">{ordinal}</{h}>'
    return f'\t\t\t<{h} epub:type="title">{esc(title)}</{h}>'


COMPOUND = re.compile(
    r"^(?P<plabel>Book|Part|BOOK|PART)\s+(?P<pord>[IVXLC]+|\d+)[,.]\s+"
    r"(?P<clabel>Chapter|Section|CHAPTER|SECTION)\s+(?P<cord>[IVXLC]+|\d+)[.:]?\s*(?P<title>.*)$")

def synthesize_parts(sections):
    """'Book I, Chapter 2: X' headings become part dividers + plain chapters."""
    current = None
    for s in sections:
        m = COMPOUND.match(s["heading"].strip())
        if not m:
            continue
        part = f"{m.group('plabel').title()} {m.group('pord').upper()}"
        s["heading"] = f"{m.group('clabel').title()} {m.group('cord')}: {m.group('title')}".rstrip(": ")
        if part != current and not s.get("part_before"):
            s["part_before"] = part
            current = part
    return sections


def build_chapter_files(book, sections, meta, textdir):
    """Write one XHTML file per section (plus part files); return spine order."""
    sections = synthesize_parts(sections)
    fic = "z3998:fiction" if meta.get("fiction") else "z3998:non-fiction"
    spine, part_id, chap_no, part_no = [], None, 0, 0
    matters = []
    for s in sections:
        if s["part_before"]:
            part_no += 1
            plabel, pord, ptitle = parse_heading(s["part_before"])
            part_id = f"part-{part_no}"
            fname = f"{part_id}.xhtml"
            h2 = (f'\t\t\t<h2>\n\t\t\t\t<span epub:type="se:label">{plabel or "Part"}</span>\n'
                  f'\t\t\t\t<span epub:type="z3998:ordinal z3998:roman">{pord or part_no}</span>\n\t\t\t</h2>')
            if ptitle:
                body_part = ("\t\t\t<header>\n" + h2.replace("\t\t\t<h2>", "\t\t\t\t<h2>").replace("\n\t\t\t\t<span", "\n\t\t\t\t\t<span").replace("\n\t\t\t</h2>", "\n\t\t\t\t</h2>")
                             + f'\n\t\t\t\t<p epub:type="se:bridgehead">{esc(ptitle)}</p>\n\t\t\t</header>\n')
            else:
                body_part = h2 + "\n"
            xml = (XHTML_HEAD.format(title=f"{plabel or 'Part'} {pord or part_no}", fic=fic)
                   + f'\t\t<section id="{part_id}" epub:type="part">\n'
                   + body_part + "\t\t</section>\n\t</body>\n</html>\n")
            (textdir / fname).write_text(xml)
            spine.append(fname)
            matters.append("bodymatter")

        label, ordinal, title = parse_heading(s["heading"])
        body_text = s["body"]
        if not title:
            first, _, rest = body_text.partition("\n\n")
            fl = first.strip()
            cand = fl.rstrip(".")
            if fl and "\n" not in fl and len(fl) < 200 and (
                    is_all_caps(cand) or (fl[-1] not in ".…" and assemble.is_subheading(fl))):
                fl = cand
                title = nice_title(fl)
                body_text = rest
        sec_type = FRONT_BACK_TYPES.get((title or "").lower(), "chapter")
        if sec_type == "chapter":
            chap_no += 1
            sid = f"chapter-{chap_no}"
        else:
            sid = slugify(title) or f"section-{chap_no}"
            # A work can repeat matter-type sections (e.g. each volume of
            # Democracy in America opens with its own preface); keep filenames unique.
            if f"{sid}.xhtml" in spine:
                n = 2
                while f"{sid}-{n}.xhtml" in spine:
                    n += 1
                sid = f"{sid}-{n}"
        fname = f"{sid}.xhtml"
        level = 3 if part_id else 2
        parent = f' data-parent="{part_id}"' if part_id else ""
        head = heading_xml(level, label if label not in (None, "Chapter") else None,
                           ordinal, title)
        body = render_body(body_text)
        matter = ("frontmatter" if sec_type in FRONTMATTER else
                  "backmatter" if sec_type in BACKMATTER else "bodymatter")
        matters.append(matter)
        page_head = XHTML_HEAD.format(title=esc(title or f"Chapter {ordinal or chap_no}"), fic=fic)
        page_head = page_head.replace('epub:type="bodymatter', f'epub:type="{matter}')
        xml = (page_head
               + f'\t\t<section{parent} id="{sid}" epub:type="{sec_type}">\n'
               + head + "\n" + body + "\n\t\t</section>\n\t</body>\n</html>\n")
        (textdir / fname).write_text(xml)
        spine.append(fname)
    return spine, matters


def commons_url(title):
    import urllib.request, urllib.parse, time
    q = urllib.parse.quote(title)
    url = (f"https://commons.wikimedia.org/w/api.php?action=query&titles={q}"
           f"&prop=imageinfo&iiprop=url|size&iiurlwidth=4000&format=json")
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "modern-classics-ebooks/1.0 (contact: alexalemi@gmail.com)"})
            d = json.load(urllib.request.urlopen(req))
            break
        except Exception:
            time.sleep(5 * (i + 1))
    else:
        raise RuntimeError(f"commons api failed for {title}")
    for p in d["query"]["pages"].values():
        ii = p["imageinfo"][0]
        # very large originals: use the 4000px rendition instead
        if ii["width"] > 4200 and ii.get("thumburl"):
            return ii["thumburl"]
        return ii["url"]
    raise RuntimeError(f"no imageinfo for {title}")


def prepare_cover(dest, meta):
    art = meta.get("cover")
    if not art:
        return
    cache = ROOT / "build" / "covers"
    cache.mkdir(parents=True, exist_ok=True)
    src = cache / f"{meta['dir']}.jpg"
    if not src.exists():
        import urllib.request
        # TIMEOUT AND AN EXPLICIT FAILURE, both learned the hard way. A cover
        # whose Commons filename is wrong resolves to a URL that never
        # answers, and urlopen with no timeout then blocks forever -- the
        # whole build hangs before printing its first line of output, so it
        # looks like a slow `se` step rather than a typo in ebook_meta.json.
        req = urllib.request.Request(commons_url(art["commons"]),
                                     headers={"User-Agent": "modern-classics-ebooks/1.0"})
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
        except Exception as e:
            sys.exit(f"could not fetch cover art {art['commons']!r}: {e}\n"
                     f"check the file actually exists on Commons")
        if len(data) < 20_000:
            sys.exit(f"cover art {art['commons']!r} came back as {len(data)} "
                     f"bytes -- almost certainly an error page, not a painting")
        src.write_bytes(data)
    shutil.copy(src, dest / "images/cover.source.jpg")
    if art.get("crop"):
        geom = ["-crop", art["crop"], "+repage"]
    else:
        out = subprocess.run(["identify", "-format", "%w %h", str(src)],
                             capture_output=True, text=True).stdout.split()
        w, h = int(out[0]), int(out[1])
        fx, fy = art.get("focus_x", 0.5), art.get("focus_y", 0.5)
        if w / h > 2 / 3:
            cw, ch = int(h * 2 / 3), h
            x, y = int((w - cw) * fx), 0
        else:
            cw, ch = w, int(w * 3 / 2)
            x, y = 0, int((h - ch) * fy)
        geom = ["-crop", f"{cw}x{ch}+{x}+{y}", "+repage"]
    out = dest / "images/cover.jpg"
    for quality in ("90", "80", "70", "60"):
        subprocess.run(["convert", str(src)] + geom +
                       ["-resize", "1400x2100!", "-quality", quality,
                        str(out)], check=True)
        if out.stat().st_size <= 1_500_000:  # se lint f-016 cap
            break


LONE_LT = re.compile(r"<(?![/!?a-zA-Z])")


def reescape_lt(dest):
    """`se typogrify` unescapes every form of the less-than sign — &lt;,
    &#x3C; and &#60; alike — into a bare "<", which makes the file invalid
    XML for every step after it. In the modern text the fix is to reword
    ("h1 is less than h2"), and main() refuses to build until someone does.
    In the ORIGINAL text there is nothing to reword: Thompson printed
    "h1 < h2" and the edition reproduces what he printed. So put the
    escape back, on the one form a bare "<" can take in running prose —
    followed by something that cannot begin a tag."""
    n = 0
    for f in sorted((dest / "src/epub/text").glob("*.xhtml")):
        s = f.read_text()
        fixed = LONE_LT.sub("&lt;", s)
        if fixed != s:
            f.write_text(fixed)
            n += 1
    return n


def run(cmd, cwd, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, input="y\n")
    if check and r.returncode not in (0, 18):  # 18 = NoResults on finder tools
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed:\n{r.stdout}\n{r.stderr}")
    return r


ORIGINAL_SUFFIX = ": The Original Text"


def original_meta(meta, env):
    """Publishing metadata for the companion edition of the source text.

    The book's own first long-description paragraph describes the book, not
    the modernization, so it carries over; everything that describes the
    retelling is replaced by a plain statement of what this edition is."""
    work = env["ORIGINAL_WORK"]
    m = dict(meta)
    m["description"] = (f"The original text of {work} as published in "
                        f"{env['DATE']} — the source behind the Modern "
                        f"Classics retelling, not the retelling itself.")
    first = (meta.get("long_description") or [""])[0]
    m["long_description"] = [
        first,
        (f"This is that book in its own words. Modern Classics publishes a "
         f"retelling of {work} in contemporary English; this companion "
         f"edition is the text it was made from, unaltered, so that a reader "
         f"can see what was changed and what was not. The plates are the "
         f"same, carrying the numbers the original printed under them and "
         f"none of the descriptive captions, which are new writing and "
         f"belong to the retelling alone."),
    ]
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("book_dir")
    ap.add_argument("--out-dir", default=str(ROOT / "site" / "ebooks"))
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--original", action="store_true",
                    help="build the source text from chapters/ instead")
    args = ap.parse_args()

    book = Path(args.book_dir)
    env = assemble.read_env(book / "env")
    all_meta = json.loads((ROOT / "ebook_meta.json").read_text())
    meta = dict(all_meta[book.name])
    FIGURE_DIR[0] = env.get("FIGURE_DIR")
    BARE_LABEL[0] = args.original

    author, work = env["AUTHOR"], env["ORIGINAL_WORK"]
    if args.original:
        meta = original_meta(meta, env)
        work = work + ORIGINAL_SUFFIX
    slug = f"{slugify(author)}_{slugify(work)}"
    dest = BUILD_ROOT / slug

    if not dest.exists():
        BUILD_ROOT.mkdir(parents=True, exist_ok=True)
        run([SE, "create-draft", "--author", author, "--title", work],
            cwd=BUILD_ROOT)

    textdir = dest / "src/epub/text"
    for old in textdir.glob("chapter-*.xhtml"):
        old.unlink()
    for old in list(textdir.glob("part-*.xhtml")) + list(textdir.glob("body.xhtml")):
        old.unlink()

    sections = load_sections(book, original=args.original)
    spine, matters = build_chapter_files(book, sections, meta, textdir)

    # SE requires a half title page when the book has frontmatter
    if "frontmatter" in matters:
        inner = f'\t\t\t<h2 epub:type="fulltitle">{esc(work)}</h2>'
        fic = "z3998:fiction" if meta.get("fiction") else "z3998:non-fiction"
        ht = (XHTML_HEAD.format(title=esc(work), fic=fic)
              .replace('epub:type="bodymatter', 'epub:type="frontmatter')
              + '\t\t<section id="halftitlepage" epub:type="halftitlepage">\n'
              + inner + "\n\t\t</section>\n\t</body>\n</html>\n")
        (textdir / "halftitlepage.xhtml").write_text(ht)
        first_body = next((i for i, m in enumerate(matters) if m != "frontmatter"), len(matters))
        spine = spine[:first_body] + ["halftitlepage.xhtml"] + spine[first_body:]

    # local.css additions — only rules actually used by the generated text
    used = "".join((textdir / f).read_text() for f in spine)
    rules = []
    if 'class="subhead"' in used:
        rules.append('p.subhead{\n\tfont-style: italic;\n\tmargin-top: 1.5em;\n\ttext-indent: 0;\n}')
    if 'class="lines"' in used:
        rules.append('blockquote.lines p{\n\ttext-indent: 0;\n}')
    if "se:era" in used:
        rules.append('[epub|type~="se:era"]{\n\tfont-variant: all-small-caps;\n}')
    figdir = env.get("FIGURE_DIR")
    if figdir and any(f.suffix.lower() == ".png"
                      for f in (ROOT / "site" / figdir).iterdir()):
        # Plates with a transparent ground are black ink on nothing, which
        # is invisible in a reader set to a dark theme. Give them the white
        # page they were printed on.
        rules.append("figure img{\n\tbackground: #fff;\n}")
    if "z3998:verse" in used:
        rules.append('[epub|type~="z3998:verse"] p{\n\ttext-align: initial;\n\ttext-indent: 0;\n}\n\n[epub|type~="z3998:verse"] p > span{\n\tdisplay: block;\n\tpadding-left: 1em;\n\ttext-indent: -1em;\n}')
    css = dest / "src/epub/css/local.css"
    base = css.read_text().split("/* modern-classics */")[0].rstrip()
    css.write_text(base + ("\n\n/* modern-classics */\n" + "\n\n".join(rules) + "\n" if rules else "\n"))
    toc = dest / "src/epub/toc.xhtml"
    toc.write_text(toc.read_text().replace('xml:lang="LANG"', 'xml:lang="en-US"'))

    import rebrand
    meta["_has_dedication"] = (textdir / "dedication.xhtml").exists()
    meta["_has_preface"] = (textdir / "preface.xhtml").exists()
    rebrand.apply(dest, env, meta, spine, original=args.original)
    prepare_cover(dest, meta)
    copy_figures(book, env, dest)

    # `se typogrify` turns an escaped &lt; back into a bare "<", which makes
    # the file unparseable for every step after it — and the error you get is
    # a raw XML "invalid element name", pages away from the cause. Refuse to
    # ship a bare comparison operator in prose, and say why.
    if not args.original:
        for f in sorted((dest / "src/epub/text").glob("*.xhtml")):
            if "&lt;" in f.read_text():
                raise SystemExit(
                    f"{f.name} contains an escaped '<'. `se typogrify` will "
                    "unescape it and break the XHTML. Reword the sentence "
                    "(\"h1 is less than h2\") in modern_chapters/ instead.")
    run([SE, "typogrify", "."], cwd=dest)
    reescape_lt(dest)
    for step in (["clean", "."], ["build-manifest", "."],
                 ["build-spine", "."], ["build-title", "."]):
        run([SE] + step, cwd=dest)
    rebrand.order_spine(dest, spine)
    run([SE, "build-toc", "."], cwd=dest)
    run([SE, "build-images", "."], cwd=dest)
    run([SE, "prepare-release", "."], cwd=dest)
    run([SE, "clean", "."], cwd=dest)

    lint = run([SE, "--plain", "lint", "."], cwd=dest, check=False)
    print(lint.stdout or "LINT CLEAN")

    if not args.skip_build:
        import tempfile
        out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            r = run([SE, "build", "--check", f"--output-dir={td}", "."],
                    cwd=dest, check=False)
            if r.returncode:
                # epubcheck's PKG-021 ("Corrupted image file encountered")
                # fires for EVERY image in this environment — including the
                # cover and title page that `se` generates itself, and
                # including books already published from this repo. It is a
                # broken Java image reader, not a broken book. Tolerate that
                # one code and nothing else; verify the images ourselves.
                blob = (r.stdout or "") + (r.stderr or "")
                codes = set(re.findall(r"\b([A-Z]{3}-\d{3})\b", blob))
                if codes and codes <= {"PKG-021"}:
                    from PIL import Image
                    for img in sorted((dest / "src/epub/images").glob("*")):
                        if img.suffix.lower() in (".jpg", ".jpeg", ".png"):
                            Image.open(img).verify()
                    print("NOTE: epubcheck reported only PKG-021 "
                          "(corrupted image) for every image, including its "
                          "own cover — a local Java image-reader fault. All "
                          "images verified independently; building without "
                          "--check.")
                    run([SE, "build", f"--output-dir={td}", "."], cwd=dest)
                else:
                    raise RuntimeError(f"se build --check failed:\n{blob}")
            built = sorted(Path(td).glob("*.epub"))
            if not built:
                raise RuntimeError("se build produced no epub")
            for f in built:
                suffix = "_advanced.epub" if f.stem.endswith("_advanced") else ".epub"
                target = out / f"{slug}{suffix}"
                shutil.move(str(f), target)
                print("BUILT:", target)


if __name__ == "__main__":
    main()
