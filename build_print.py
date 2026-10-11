#!/usr/bin/env python3
"""Print-ready 5x8 paperback files for IngramSpark / Lightning Source, from a built epub, in Typst.

    python3 build_print.py flatland                 # interior + cover + report + proofs
    python3 build_print.py flatland --paper white
    python3 build_print.py flatland --isbn 979-8-... --price 14.99   (copyright page + cover barcode)
    python3 build_print.py flatland --spine 0.3600   (spine width from Ingram's cover template)

Writes build/print/{book}/: {isbn}_txt.pdf and {isbn}_cov.pdf (PDF/X-3:2002, the
files to upload; "book_" stands in until an ISBN is given), the Typst sources
and RGB working PDFs, report.txt, and proof/ (every page as PNG, contact
sheets of facing spreads, the cover).

WHY THE EPUB IS THE SOURCE. The built epub's XHTML is the cleanest form of a
book this project has: typogrified by `se` (curly quotes, real dashes,
ellipses), semantically marked (part/chapter/verse/figure/noteref), with the
editor's introduction and the captions in place. Converting that is far
safer than re-deriving it from modern_chapters/.

TYPESETTING. Typst: EB Garamond 11pt, justified, hyphenated, a ~3.6in
measure (60-65 characters), widows and orphans forbidden (text.costs),
chapters on a new recto with a sunk opening, running heads (book title
verso, chapter recto), folios outside. Typst has character protrusion
("overhang") but no font expansion, so report.txt includes an OVERFLOW
check read from the PDF itself: any word whose box crosses the text block's
edge is listed with its page -- the thing a too-tight line looks like.

INGRAM RULES ENCODED HERE -- IngramSpark File Creation Guide (42pp, dated
2026-08-24, www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf):
INTERIOR (B&W): PDF/X-1a:2001 or PDF/X-3:2002; grayscale; text and rules
100% black (rules >= 0.125pt); 300ppi grayscale / 600ppi 1-bit line art;
built at trim size when nothing bleeds; recommended minimum margin 0.5in on
all sides (no page-count gutter table, unlike KDP -- we widen the gutter for
thick books anyway); no crop or printer marks; single pages, not spreads;
page count divisible by 2 with the LAST PAGE BLANK for Lightning Source's
manufacturing information; no spot colours or ICC profiles beyond the
PDF/X output intent; fonts embedded; 1/16in trim variance.
COVER: PDF/X-1a:2001 or PDF/X-3:2002; CMYK; built on Ingram's Cover
Template Generator template (dashboard, My Tools) -- its spine width wins,
pass it with --spine; bleed 0.125in all sides; type safety 0.25in; spine
safety 0.0625in each side (0.03125in for spines under 0.35in); NO spine
text under 48 pages; barcode mandatory, 100% black on white, or a clear
1.75 x 1in area for LS; text 24pt and under in 100% black only; rich black
60/40/40/100; total ink no more than 240%; images >= 200ppi (300 better).
The spine default below (pages x caliper) is an estimate for proofs only.
"""
import argparse, json, re, shutil, subprocess, sys, zipfile
from pathlib import Path
from lxml import etree

ROOT = Path(__file__).resolve().parent
FONT_PATH = "/usr/share/texlive/texmf-dist/fonts/opentype/public/ebgaramond"
NS = {"x": "http://www.w3.org/1999/xhtml", "opf": "http://www.idpf.org/2007/opf"}
EPT = "{http://www.idpf.org/2007/ops}type"

TRIM_W, TRIM_H = 5.0, 8.0
OUTER, TOP, BOTTOM = 0.6, 0.7, 0.8
PAPER = {"cream": 0.0025, "white": 0.002252}   # per-page caliper ESTIMATES; Ingram's template is authoritative
GS_LIB = Path("/usr/share/ghostscript/10.02.1")
NAVY, RED, CREAM = "#24303F", "#A3291C", "#F4EFE2"


def gutter(pages):
    """Inside margin. Ingram asks only for 0.5in on every side; a thick
    perfect-bound book loses more into the spine, so widen it with bulk."""
    for limit, g in ((200, .70), (400, .80), (600, .90)):
        if pages <= limit:
            return g
    return 1.0


# ------------------------------------------------------------ XHTML -> Typst
def esc(s):
    """Plain text as Typst markup: every markup character escaped."""
    s = s.replace("⁠", "").replace("﻿", "")
    s = re.sub(r"[\\#*_`$<>@\[\]~\"'/=+]", lambda m: "\\" + m.group(0), s)
    s = s.replace("--", "-\\-")          # '--' would become an en dash
    s = re.sub(r"\s*—\s*", "—", s)
    return s


def para_start(s):
    """A paragraph opening with '1.' or '-' would become a list item."""
    return re.sub(r"^(\s*)(\d+)\.", r"\1\2\\.", re.sub(r"^(\s*)-", r"\1\\-", s))


def types(el):
    return (el.get(EPT) or "").split()


def tstr(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Conv:
    def __init__(self, notes):
        self.notes, self.figures = notes, []

    def inline(self, el):
        out = [esc(el.text or "")]
        for c in el:
            tag = etree.QName(c).localname
            t = types(c)
            inner = self.inline(c)
            if "noteref" in t:
                note = self.notes.get(c.get("href", "").split("#")[-1])
                inner = f"#footnote[{note}]" if note else ""
            elif tag in ("i", "em", "cite"):
                inner = f"#emph[{inner}]"
            elif tag in ("b", "strong"):
                inner = f"#strong[{inner}]"
            elif tag == "br":
                inner = " \\\n"
            elif tag == "span" and ("z3998:small-caps" in t or "small-caps" in (c.get("class") or "")):
                inner = f"#smallcaps[{inner.lower()}]"
            elif tag == "sup":
                inner = f"#super[{inner}]"
            elif tag == "sub":
                inner = f"#sub[{inner}]"
            elif tag == "img":
                inner = ""
            out.append(inner)
            out.append(esc(c.tail or ""))
        return re.sub(r"[ \t]*\n[ \t]*", " ", "".join(out)).replace(" \\ ", " \\\n")

    def block(self, el, out):
        tag = etree.QName(el).localname
        t = types(el)
        cls = el.get("class") or ""
        verse = any(v in t for v in ("z3998:verse", "z3998:poem", "z3998:song", "z3998:hymn"))
        if tag in ("section", "article", "div") and not verse:
            self.section(el, out)
        elif tag == "p":
            if "subhead" in cls or "se:bridgehead" in t:
                out.append(f"#subhead[{self.inline(el)}]\n\n")
            else:
                out.append(para_start(self.inline(el).strip()) + "\n\n")
        elif tag in ("h2", "h3", "h4", "h5", "h6", "hgroup"):
            out.append(f"#subhead[{self.inline(el)}]\n\n")
        elif tag == "hr":
            out.append("#scenebreak\n\n")
        elif verse:
            self.verse(el, out)
        elif tag == "blockquote":
            inner = []
            for c in el:
                self.block(c, inner)
            out.append("#quote(block: true)[\n" + "".join(inner) + "]\n\n")
        elif tag == "figure":
            img = el.find(".//x:img", NS)
            cap = el.find(".//x:figcaption", NS)
            if img is not None:
                name = Path(img.get("src")).name
                self.figures.append(name)
                capt = " ".join(self.inline(p) for p in cap) if cap is not None else ""
                out.append(f'#plate("images/{name}")[{capt}]\n\n')
        elif tag in ("ul", "ol"):
            fn = "list" if tag == "ul" else "enum"
            out.append(f"#{fn}(" + ", ".join(f"[{self.inline(li)}]" for li in el) + ")\n\n")
        elif tag == "table":
            rows = el.findall(".//x:tr", NS)
            if rows:
                n = max(len(r) for r in rows)
                cells = ", ".join(f"[{self.inline(c)}]" for r in rows for c in r)
                out.append(f"#align(center, text(size: 0.9em, table(columns: {n}, stroke: none, {cells})))\n\n")
        elif tag == "header":
            for c in el:
                self.block(c, out)
        else:
            txt = self.inline(el).strip()
            if txt:
                out.append(para_start(txt) + "\n\n")

    def verse(self, el, out):
        stanzas = []
        for p in el.iter("{%s}p" % NS["x"]):
            spans = p.findall("x:span", NS)
            lines = [self.inline(s).strip() for s in spans] if spans else [self.inline(p).strip()]
            stanzas.append(" \\\n".join(l for l in lines if l))
        nlines = sum(st.count("\\\n") + 1 for st in stanzas)
        brk = "true" if nlines > 24 else "false"      # short verse never splits
        out.append(f"#verse(breakable: {brk})[\n" + "\n\n".join(stanzas) + "\n]\n\n")

    def heading(self, sec):
        hg = sec.find("x:hgroup", NS)
        h = hg if hg is not None else sec.find("x:header", NS)
        if h is None:
            for tagname in ("h2", "h3", "h4", "h5"):
                h = sec.find(f"x:{tagname}", NS)
                if h is not None:
                    break
        if h is None:
            return None, "", ""
        title_el = None
        if etree.QName(h).localname in ("hgroup", "header"):
            title_el = next((c for c in h.iter() if "title" in types(c)
                             and etree.QName(c).localname == "p"), None)
        hx = next((c for c in h.iter() if etree.QName(c).localname in ("h2", "h3", "h4", "h5", "h6")), h)
        label = re.sub(r"\s+", " ", self.inline(hx)).strip()
        title = re.sub(r"\s+", " ", self.inline(title_el)).strip() if title_el is not None else ""
        if not title:
            label, title = "", label
        return h, label, title

    def section(self, sec, out):
        t = types(sec)
        h, label, title = self.heading(sec)
        if "part" in t:
            out.append(f"#part[{title or label}]\n\n")
        elif title or label:
            plain = re.sub(r"#footnote\[.*?\]", "", title or label)
            out.append(f"#chapter([{label}], [{title or label}], [{plain}])\n\n")
        for c in sec:
            if c is not h:
                self.block(c, out)


# ------------------------------------------------------------ the book
SKIP = ("titlepage", "imprint", "halftitlepage", "colophon", "uncopyright", "toc", "endnotes", "loi")


def read_epub(path):
    z = zipfile.ZipFile(path)
    opf = etree.fromstring(z.read("epub/content.opf"))
    man = {i.get("id"): i.get("href") for i in opf.findall(".//opf:manifest/opf:item", NS)}
    spine = [man[r.get("idref")] for r in opf.findall(".//opf:spine/opf:itemref", NS)]
    docs = {h: etree.fromstring(z.read("epub/" + h)) for h in spine}
    notes = {}
    for d in docs.values():
        for li in d.iter("{%s}li" % NS["x"]):
            if "endnote" in types(li):
                for a in li.findall(".//x:a", NS):
                    if "backlink" in types(a):
                        a.getparent().remove(a)
                notes[li.get("id")] = " ".join(Conv({}).inline(p) for p in li.findall("x:p", NS)).strip()
    return z, spine, docs, notes


TEMPLATE = r"""// generated by build_print.py -- edit the generator, not this file
#let navy = rgb("%(navy)s")
#let booktitle = %(booktitle)s
#let shorttitle = %(shorttitle)s
#set document(title: booktitle, author: %(author)s)
#set text(font: "EB Garamond", size: 11pt, lang: "en", hyphenate: true,
  number-type: "old-style", costs: (widow: 100%%, orphan: 100%%))
#set par(justify: true, leading: 0.62em, spacing: 0.62em,
  first-line-indent: 1.2em)
#set page(width: 5in, height: 8in,
  margin: (inside: %(inner).3fin, outside: %(outer).3fin, top: %(top).3fin, bottom: %(bottom).3fin))
#set footnote.entry(separator: line(length: 25%%, stroke: 0.4pt), gap: 0.4em)
#show footnote.entry: set text(size: 9pt)
#set figure(numbering: none, gap: 0.6em)
#show figure.caption: it => text(size: 9pt, style: "italic", it.body)

// chapter openings: a recto, sunk a sixth of the page, small-caps label, italic title
#let chapter(label, title, plain) = {
  pagebreak(to: "odd", weak: true)
  v(16%%)
  align(center)[
    #if label != [] [#text(tracking: 0.08em, smallcaps(lower(label))) #v(0.5em)]
    #heading(level: 2, outlined: true, bookmarked: true, title)
  ]
  v(2.2em)
}
#show heading.where(level: 2): it => text(size: 1.45em, style: "italic", weight: "regular", hyphenate: false, it.body)
#show heading: set par(justify: false)
#let part(title) = {
  pagebreak(to: "odd", weak: true)
  v(30%%)
  align(center, heading(level: 1, outlined: true, text(size: 1.6em, weight: "regular", tracking: 0.06em, smallcaps(lower(title)))))
  pagebreak(to: "odd")
}
#show heading.where(level: 1): it => it.body
#let subhead(body) = block(above: 1.4em, below: 0.8em, width: 100%%, sticky: true, align(center, text(hyphenate: false, smallcaps(lower(body)))))
#let scenebreak = align(center, block(above: 1em, below: 1em)[\* #h(1em) \* #h(1em) \*])
#let verse(body, breakable: true) = block(above: 1em, below: 1em, inset: (left: 1.5em), breakable: breakable,
  { set par(justify: false, first-line-indent: 0em, hanging-indent: 1.5em); body })
#let plate(src, caption) = figure(image(src, width: 90%%, height: 45%%, fit: "contain"), caption: caption)
#show quote.where(block: true): it => block(inset: (left: 1.2em, right: 1.2em), it.body)

// running heads: book title on the verso, chapter on the recto; none on openings
#let runhead() = context {
  let p = here().page()
  let opens = query(heading).filter(h => h.location().page() == p)
  if opens.len() > 0 or counter(page).get().first() == 0 { return }
  let n = counter(page).display()
  let style = s => text(size: 9pt, tracking: 0.06em, smallcaps(lower(s)))
  if calc.even(p) {
    [#n #h(1fr) #style(shorttitle) #h(1fr) #hide(n)]
  } else {
    let prev = query(heading.where(level: 2).before(here()))
    let t = if prev.len() > 0 { prev.last().body } else { shorttitle }
    [#hide(n) #h(1fr) #style(t) #h(1fr) #n]
  }
}

// ---------------- front matter (no folios) ----------------
#set page(header: none, numbering: none)
#set text(hyphenate: false)
#v(30%%)
#align(center, block(width: 85%%, text(size: 1.3em, tracking: 0.08em, smallcaps(lower(booktitle)))))
#pagebreak(to: "odd")
#v(12%%)
#align(center)[
  #text(size: 2.1em, booktitle) \
  #v(1em)
  #text(size: 1.15em, style: "italic", %(author)s) \
  #v(2em)
  #text(size: 0.9em, tracking: 0.08em, smallcaps(lower(%(retold)s)))
]
#v(1fr)
#align(center, image("brand/emend-wordmark.svg", height: 0.42in))
#pagebreak()
#v(1fr)
#block(text(size: 8pt)[
  #set par(justify: false, first-line-indent: 0em, spacing: 0.9em)
  %(copyright)s
])
#pagebreak(to: "odd")
#{
  show outline.entry.where(level: 1): it => block(above: 1.2em, smallcaps(lower(it.element.body)))
  outline(title: align(center, text(size: 1.2em, tracking: 0.08em, smallcaps[contents])), depth: 2, indent: 0em)
}
#set text(hyphenate: true)
#set page(numbering: "i", footer: context align(center, text(size: 9pt, counter(page).display("i"))))
%(intro)s
// ---------------- body ----------------
#set page(header: runhead(), numbering: "1", footer: auto)
#counter(page).update(1)
%(body)s
// Lightning Source: page count even, the last page blank for its imprint
#set page(header: none, footer: none)
%(tail)s
"""


def copyright_block(env):
    title, author = esc(env["ORIGINAL_WORK"]), esc(env["AUTHOR"])
    restored = env.get("EDITION", "").lower() == "restored"
    trl = env.get("TRANSLATOR") or env.get("TRANSLATORS")
    src = env.get("SOURCE_NAME")
    what = ("The author’s text, restored" if restored else "Retold in contemporary English")
    lines = [f"#emph[{title}]" + (f", {esc(env['SUBTITLE'])}" if env.get("SUBTITLE") else ""),
             f"{what} from the work of {author} ({esc(env.get('DATE', ''))})"
             + (f", working from the translation by {esc(trl)}" if trl else "")
             + (f", with the source text drawn from {esc(src)}" if src else "") + ".",
             ("This edition was prepared" if restored else "This retelling was made")
             + " with the help of Claude, an AI model by Anthropic, and is part of Modern Classics, a series from Emend Press. "
             "The original work is in the public domain in the United States. Every stage of how this book was made can be inspected at github.com\\/alexalemi\\/modern-classics.",
             ("ISBN " + esc(env["_ISBN"])) if env.get("_ISBN") else "ISBN #box(width: 8em, line(length: 100%, stroke: 0.4pt))",
             f"Published {esc(env.get('MODERN_YEAR', '2026'))} by Emend Press.",
             "Set in EB Garamond."]
    return "\n\n".join(lines)


def build_typ(book, env, epub, workdir, inner, tail=0):
    z, spine, docs, notes = read_epub(epub)
    imgdir = workdir / "images"
    imgdir.mkdir(parents=True, exist_ok=True)
    for n in z.namelist():
        if n.startswith("epub/images/") and Path(n).name not in ("cover.jpg", "titlepage.png", "logo.png", "logo.svg"):
            (imgdir / Path(n).name).write_bytes(z.read(n))
    conv = Conv(notes)
    body, intro = [], []
    for h in spine:
        stem = Path(h).stem
        if stem in SKIP:
            continue
        tgt = intro if "introduction" in stem else body
        for sec in docs[h].find("x:body", NS):
            conv.block(sec, tgt)
    restored = env.get("EDITION", "").lower() == "restored"
    doc = TEMPLATE % dict(
        navy=NAVY, booktitle=tstr(env["ORIGINAL_WORK"]), author=tstr(env["AUTHOR"]),
        shorttitle=tstr(env.get("SHORT_TITLE") or re.split(r"[:;]| — ", env["ORIGINAL_WORK"])[0].strip()),
        retold=tstr("Restored edition" if restored else "Retold in contemporary English"),
        inner=inner, outer=OUTER, top=TOP, bottom=BOTTOM,
        copyright=copyright_block(env), intro="".join(intro), body="".join(body),
        tail="#pagebreak()\n#box()\n" * tail)
    return doc, conv.figures


def typst(workdir, name):
    r = subprocess.run(["typst", "compile", "--font-path", FONT_PATH, "--ignore-system-fonts",
                        f"{name}.typ", f"{name}.pdf"], cwd=workdir, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"typst failed on {name}.typ:\n{r.stderr[-3000:]}")
    return workdir / f"{name}.pdf", r.stderr


def pages_of(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


# ------------------------------------------------------------ cover
COVER = r"""// colours set in CMYK at the source (Ingram: CMYK, total ink <= 240%%,
// text 24pt and under in 100%% black only)
#let navy = cmyk(82%%, 64%%, 36%%, 38%%)     // 220%% total
#let kblack = cmyk(0%%, 0%%, 0%%, 100%%)
#let cream = cmyk(2%%, 4%%, 11%%, 0%%)
#set page(width: %(W).4fin, height: %(H).4fin, margin: 0pt, fill: cream)
#set text(font: "EB Garamond", fill: navy)
// spine
#place(top + left, dx: %(sx0).4fin, rect(width: %(spine).4fin, height: 100%%, fill: navy, stroke: none))
%(spinetext)s
// front
#place(top + left, dx: %(fx).4fin, dy: 0.85in, block(width: %(fw).4fin, align(center)[
  #image(%(art)s, width: 3.9in, height: 3.4in, fit: "contain")
  #v(0.35in)
  #text(size: 25pt, %(title)s) \
  #v(0.12in)
  #text(size: 13pt, style: "italic", fill: kblack, %(author)s) \
  #v(0.08in)
  #text(size: 9.5pt, fill: kblack, tracking: 0.08em, smallcaps(lower(%(retold)s)))
]))
#place(bottom + left, dx: %(fx).4fin, dy: -0.55in, block(width: %(fw).4fin, align(center, image("brand/emend-wordmark-cover.svg", height: 0.42in))))
// back: blurb, imprint, barcode area (kept clear)
#place(top + left, dx: %(bx).4fin, dy: 0.95in, block(width: 3.9in, [
  #set par(justify: true, spacing: 0.8em)
  #set text(size: 10.5pt, fill: kblack)   // Ingram: text 24pt and under in 100%% black
  %(blurb)s
]))
#place(bottom + left, dx: %(bx).4fin, dy: -0.55in, image("brand/emend-mark-cover.svg", height: 0.5in))
%(barcode)s
"""


def prep_art(src, dst, tac=235):
    """Cover art to CMYK with total ink capped below Ingram's 240%.

    RGB -> CMYK through Ghostscript's sRGB and CMYK profiles (ImageMagick),
    then wherever C+M+Y+K exceeds the cap, C, M and Y are scaled down and K
    is left alone -- the dark areas keep their weight, the ink load drops.
    Done here because pdfwrite's own conversion ran a painting to ~290%."""
    import numpy as np
    from PIL import Image
    tif = dst.with_suffix(".cmyk.tif")
    subprocess.run(["convert", str(src), "-profile", str(GS_LIB / "iccprofiles" / "default_rgb.icc"),
                    "-profile", str(GS_LIB / "iccprofiles" / "default_cmyk.icc"), str(tif)], check=True)
    im = Image.open(tif)
    a = np.asarray(im).astype(float)
    c, k = a[..., :3], a[..., 3]
    tot = c.sum(axis=2) + k
    cap = tac / 100 * 255
    over = tot > cap
    scale = np.ones_like(tot)
    scale[over] = np.clip((cap - k[over]) / np.maximum(c[over].sum(axis=1), 1e-6), 0, 1)
    a[..., :3] = c * scale[..., None]
    Image.fromarray(a.round().clip(0, 255).astype("uint8"), "CMYK").save(dst, quality=95, dpi=im.info.get("dpi", (300, 300)))
    tif.unlink()

def build_cover(book, env, meta, pages, paper, workdir, spine_override=None, price=None):
    spine = spine_override or pages * PAPER[paper]
    W, H = 2 * (TRIM_W + 0.125) + spine, TRIM_H + 0.25
    sx0 = 0.125 + TRIM_W
    art = ROOT / "build" / "covers" / f"{book}.jpg"
    if art.exists():
        prep_art(art, workdir / "cover-art.jpg")
    restored = env.get("EDITION", "").lower() == "restored"
    if pages >= 48:
        safety = 0.0625 if spine >= 0.35 else 0.03125
        size = max(6.0, min(10.0, (spine - 2 * safety) * 72 * 0.62))
        spinetext = (f'#place(top + left, dx: {sx0 + safety:.4f}in, block(width: {spine - 2 * safety:.4f}in, height: 100%, '
                     f'align(center + horizon, rotate(90deg, reflow: true, text(fill: cmyk(0%, 0%, 0%, 0%), size: {size:.1f}pt, '
                     f'[{esc(env["ORIGINAL_WORK"])} #h(1.5em) #emph[{esc(env["AUTHOR"])}]])))))')
    else:
        spinetext = "// under 48 pages: Ingram allows no spine text"
    # barcode: ours (100% black on white) when we have an ISBN, else the
    # 1.75 x 1in clear area Ingram asks for, white, for LS to fill
    if env.get("_ISBN"):
        (workdir / "barcode.svg").write_text(barcode_svg(env["_ISBN"], price))
        barcode = (f'#place(bottom + left, dx: {0.125 + TRIM_W - 0.5 - 2.0:.4f}in, dy: -0.5in, '
                   f'box(fill: white, inset: 0.06in, image("barcode.svg", width: 1.9in)))')
    else:
        barcode = (f'#place(bottom + left, dx: {0.125 + TRIM_W - 0.5 - 1.85:.4f}in, dy: -0.5in, '
                   f'rect(width: 1.85in, height: 1.1in, fill: white, stroke: none))')
    blurb = "\n\n".join(esc(p) for p in meta.get("long_description", [meta.get("description", "")]))
    doc = COVER % dict(navy=NAVY, cream=CREAM, W=W, H=H, sx0=sx0, spine=spine, spinetext=spinetext,
                       fx=sx0 + spine, fw=TRIM_W + 0.125, bx=0.125 + 0.55, bcx=0.125 + TRIM_W - 0.5 - 2.0,
                       art=tstr("cover-art.jpg"), title=tstr(env["ORIGINAL_WORK"]), author=tstr(env["AUTHOR"]),
                       retold=tstr("Restored edition" if restored else "Retold in contemporary English"),
                       blurb=blurb, barcode=barcode)
    (workdir / "cover.typ").write_text(doc)
    pdf, _ = typst(workdir, "cover")
    return pdf, spine, (W, H)



# ------------------------------------------------------------ barcode (EAN-13 + 5-digit price add-on)
_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
_G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
_R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
_PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]
_ADD5 = ["GGLLL", "GLGLL", "GLLGL", "GLLLG", "LGGLL", "LLGGL", "LLLGG", "LGLGL", "LGLLG", "LLGLG"]


def barcode_svg(isbn, price=None):
    """Bookland EAN-13 for the ISBN, with the EAN-5 price add-on
    ("5" + dollars-and-cents for USD; "90000" = no suggested price), drawn
    as 100% black bars on white -- what Ingram asks a publisher's barcode to be."""
    d = re.sub(r"\D", "", isbn)
    if len(d) != 13:
        raise SystemExit(f"ISBN must be 13 digits, got {isbn!r}")
    check = (10 - sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d[:12])) % 10) % 10
    if check != int(d[12]):
        raise SystemExit(f"ISBN {isbn} has a bad check digit (expected {check})")
    bits = "101" + "".join((_L if p == "L" else _G)[int(c)] for p, c in zip(_PARITY[int(d[0])], d[1:7]))
    bits += "01010" + "".join(_R[int(c)] for c in d[7:]) + "101"
    add = "90000" if price is None else "5" + f"{round(float(price) * 100):04d}"
    a_check = (sum(int(c) * (3 if i % 2 == 0 else 9) for i, c in enumerate(add))) % 10
    abits = "1011" + "01".join((_L if p == "L" else _G)[int(c)] for p, c in zip(_ADD5[a_check], add))
    m = 1.0                                   # module width, user units
    quiet = 11
    W = quiet + len(bits) + 9 + len(abits) + 7
    H = 72.0
    rects = []
    for i, b in enumerate(bits):
        if b == "1":
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append(f'<rect x="{quiet + i}" y="12" width="{m}" height="{H - (6 if guard else 12)}"/>')
    ax = quiet + len(bits) + 9
    for i, b in enumerate(abits):
        if b == "1":
            rects.append(f'<rect x="{ax + i}" y="12" width="{m}" height="{H - 12}"/>')
    hy = f"{d[:3]}-{d[3]}-{d[4:8]}-{d[8:12]}-{d[12]}"
    txt = [f'<text x="{quiet + len(bits) / 2}" y="9" font-size="7.5" text-anchor="middle">ISBN {hy}</text>',
           f'<text x="{quiet - 2}" y="{H + 7}" font-size="9" text-anchor="end">{d[0]}</text>',
           f'<text x="{quiet + 24}" y="{H + 7}" font-size="9" text-anchor="middle" letter-spacing="1.6">{d[1:7]}</text>',
           f'<text x="{quiet + 70}" y="{H + 7}" font-size="9" text-anchor="middle" letter-spacing="1.6">{d[7:]}</text>',
           f'<text x="{ax + len(abits) / 2}" y="9" font-size="8" text-anchor="middle" letter-spacing="1.4">{add}</text>']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H + 10}" '
            f'font-family="Helvetica, Arial, sans-serif" fill="#000">'
            f'<rect width="{W}" height="{H + 10}" fill="#fff"/>' + "".join(rects) + "".join(txt) + "</svg>")


# ------------------------------------------------------------ PDF/X (Ghostscript)
def pdfx(src, dst, gray, title):
    """Typst writes RGB PDF/A-ish files; Ingram wants PDF/X-1a or X-3.
    Ghostscript's pdfwrite does PDF/X-3:2002 with an output intent. DO NOT
    use -dBlackText/-dBlackVector: they force EVERY vector fill to black (the
    first cover proof came out solid black). Pure-K text is instead specified
    at the source -- the cover is built in Typst cmyk() colours, which pass
    through unconverted, and the grayscale interior is K by definition."""
    icc = GS_LIB / "iccprofiles" / ("default_gray.icc" if gray else "default_cmyk.icc")
    defs = (GS_LIB / "lib" / "PDFX_def.ps").read_text()
    defs = defs.replace("/Title (Title)", "/Title (" + re.sub(r"[()\\\\]", "", title) + ")")
    defs = defs.replace("(ISO Coated sb.icc)", "(" + str(icc) + ")")
    if gray:
        defs = defs.replace("/OutputCondition (Commercial and specialty printing)", "/OutputCondition (Grayscale)")
        defs = defs.replace("/OutputConditionIdentifier (CGATS TR001)", "/OutputConditionIdentifier (Custom)")
    dfile = dst.with_suffix(".pdfx_def.ps")
    dfile.write_text(defs)
    args = ["gs", "-q", "-dPDFX=true", "-dBATCH", "-dNOPAUSE", "-dNOSAFER", "-dNOOUTERSAVE",
            "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dEmbedAllFonts=true", "-dSubsetFonts=true", "-dAutoRotatePages=/None",
            "-sColorConversionStrategy=" + ("Gray" if gray else "CMYK"),
            # the logos and barcode are RGB SVGs: ICC conversion makes their
            # black a ~290% rich black; the plain conversion gives pure K
            # (CMYK art and Typst cmyk() colours pass through untouched)
            *([] if gray else ["-dUseFastColor=true"]),
            "-sProcessColorModel=" + ("DeviceGray" if gray else "DeviceCMYK"),
            "-dDownsampleGrayImages=false", "-dDownsampleColorImages=false", "-dDownsampleMonoImages=false",
            "-sOutputFile=" + str(dst), str(dfile), str(src)]
    r = subprocess.run(args, capture_output=True, text=True)
    dfile.unlink()
    if r.returncode:
        raise SystemExit("ghostscript PDF/X conversion failed:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    return dst


def max_ink(pdf, dpi=100):
    """Highest total CMYK coverage on the page, from a CMYK rendering."""
    import numpy as np
    from PIL import Image
    tif = pdf.with_suffix(".ink.tif")
    subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=tiff32nc", f"-r{dpi}",
                    "-sOutputFile=" + str(tif), str(pdf)], check=True)
    a = np.asarray(Image.open(tif)).astype(np.uint16)
    tif.unlink()
    tot = a.sum(axis=2) / 255 * 100
    return float(np.percentile(tot, 99.9)), float(tot.max())

# ------------------------------------------------------------ checks + proofs
def overflow(pdf, inner):
    """Words whose box crosses the text block edge, read from the PDF."""
    xml = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    hits = []
    for i, page in enumerate(re.findall(r"<page .*?</page>", xml, re.S), 1):
        left = (inner if i % 2 else OUTER) * 72
        right = (TRIM_W - (OUTER if i % 2 else inner)) * 72
        for xmin, xmax, w in re.findall(r'<word xMin="([\d.]+)" yMin="[\d.]+" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>', page):
            over = float(xmax) - right
            # Typst hangs trailing punctuation and hyphens into the margin on
            # purpose (overhang, its protrusion): up to ~3pt is the design.
            hang = w[-1:] in ",.;:-\u00ad\u2019\u201d!?\u2014)" and over <= 3.2
            if (over > 1.0 and not hang) or float(xmin) < left - 1.5:
                hits.append((i, w, round(over, 1)))
    return hits


def report(workdir, pdf, pages, inner, figs, warnings, cover_pdf, spine, size, paper, txt_x, cov_x, spine_given):
    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout.splitlines()[2:]
    unemb = [l for l in fonts if len(l.split()) > 5 and l.split()[-5] == "no"]
    ovf = overflow(pdf, inner)
    last_blank = not subprocess.run(["pdftotext", "-f", str(pages), "-l", str(pages), str(pdf), "-"],
                                    capture_output=True, text=True).stdout.strip()
    p99, pmax = max_ink(cov_x)
    L = [f"UPLOAD: {txt_x.name} (interior)  {cov_x.name} (cover)  -- PDF/X-3:2002 via Ghostscript",
         f"interior: {pages} pages; even: {'yes' if pages % 2 == 0 else 'NO'}; last page blank for LS: {'yes' if last_blank else 'NO'}",
         f"trim 5x8in, no bleed; margins inside {inner:.2f}in, outside {OUTER}in, top {TOP}in, bottom {BOTTOM}in (Ingram: >= 0.5in all sides)",
         f"lines overrunning the text block: {len(ovf)}" + "".join(f"\n   p.{p}: {w!r} (+{d}pt)" for p, w, d in ovf[:25]),
         "widows/orphans: forbidden (text.costs 100%)",
         f"fonts not embedded: {len(unemb)}" + "".join("\n   " + u for u in unemb),
         f"typst warnings: {len([l for l in warnings.splitlines() if 'warning' in l])}",
         f"figures: {len(figs)}"]
    measure = TRIM_W - inner - OUTER
    for f in figs:
        try:
            w = int(subprocess.run(["identify", "-format", "%w", str(workdir / "images" / f)],
                                   capture_output=True, text=True).stdout)
            dpi = w / (0.9 * measure)
            L.append(f"   {f}: {w}px -> ~{dpi:.0f} ppi at 90% of the measure" + ("   LOW: Ingram wants 300 (grayscale), 600 (line art)" if dpi < 300 else ""))
        except ValueError:
            L.append(f"   {f}: could not measure")
    L += [f"cover: {size[0]:.4f} x {size[1]:.4f}in incl. 0.125in bleed; spine {spine:.4f}in "
          + ("(from Ingram's template)" if spine_given else f"(ESTIMATE, {paper} paper: order Ingram's cover template and rerun with --spine)"),
          "spine text: " + ("yes" if pages >= 48 else "none (Ingram: under 48 pages)"),
          f"cover total ink: 99.9th percentile {p99:.0f}%, max {pmax:.0f}% (Ingram limit 240%)" + ("   OVER" if p99 > 240 else ""),
          "barcode: " + ("ours, ISBN + price add-on, 100% K on white" if (workdir / "barcode.svg").exists() else "none yet: a 1.85 x 1.1in white area is left for LS to place one")]
    (workdir / "report.txt").write_text("\n".join(L) + "\n")
    return "\n".join(L)


def proofs(workdir, pdf, cover_pdf):
    d = workdir / "proof"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    subprocess.run(["pdftoppm", "-r", "60", "-png", str(pdf), str(d / "p")], check=True)
    subprocess.run(["pdftoppm", "-r", "40", "-png", str(cover_pdf), str(d / "cover")], check=True)
    pngs = sorted(d.glob("p-*.png"))
    blank = d / "_blank.png"
    subprocess.run(["convert", str(pngs[0]), "-fill", "white", "-colorize", "100", str(blank)], check=True)
    spreads = [(blank, pngs[0])] + [tuple(pngs[i:i + 2]) if i + 1 < len(pngs) else (pngs[i], blank)
                                    for i in range(1, len(pngs), 2)]
    rows = []
    for j, (l, r) in enumerate(spreads):
        row = d / f"_s{j:04d}.png"
        subprocess.run(["convert", str(l), str(r), "+append", "-bordercolor", "#888", "-border", "1", str(row)], check=True)
        rows.append(row)
    for k in range(0, len(rows), 6):
        subprocess.run(["montage"] + [str(r) for r in rows[k:k + 6]] + ["-tile", "2x3", "-geometry", "+10+10",
                        "-background", "#bbb", str(d / f"sheet-{k // 6 + 1:02d}.png")], check=True)
    for r in rows + [blank]:
        r.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("--paper", choices=PAPER, default="cream")
    ap.add_argument("--isbn")
    ap.add_argument("--price", help="US list price for the barcode add-on, e.g. 14.99")
    ap.add_argument("--spine", type=float, help="spine width in inches from Ingram's cover template")
    a = ap.parse_args()
    book = a.book
    env = {}
    for line in (ROOT / book / "env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.split("  #")[0].strip()
    if a.isbn:
        env["_ISBN"] = a.isbn
    meta = json.load(open(ROOT / "ebook_meta.json"))[book]
    sys.path.insert(0, str(ROOT))
    import assemble
    found = assemble.find_epub(ROOT / book, ROOT)
    epub = (ROOT / "site" / "ebooks" / Path(found).name) if found else None
    if not epub or not epub.exists():
        raise SystemExit(f"no epub for {book}: run build_ebook.py first")
    workdir = ROOT / "build" / "print" / book
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "brand").mkdir(exist_ok=True)
    for name in ("emend-mark", "emend-wordmark"):
        shutil.copy(ROOT / "brand" / f"{name}.svg", workdir / "brand")
        # the cover's copies print the navy as pure black: an RGB navy
        # converts to ~241% total ink, black to 100% K (Ingram limit 240%)
        (workdir / "brand" / f"{name}-cover.svg").write_text(
            (ROOT / "brand" / f"{name}.svg").read_text().replace("#24303F", "#000000"))
    inner, tail = gutter(0), 0
    for _ in range(4):   # gutter <- page count <- gutter; then pad to even with a blank last page
        doc, figs = build_typ(book, env, epub, workdir, inner, tail)
        (workdir / "interior.typ").write_text(doc)
        pdf, warnings = typst(workdir, "interior")
        pages = pages_of(pdf)
        need = gutter(pages)
        if abs(need - inner) > 1e-6:
            inner = need
            continue
        if tail == 0:
            tail = 1 if (pages - 0) % 2 else 2       # odd -> one blank; even -> two (keeps it even)
            continue
        break
    cover_pdf, spine, size = build_cover(book, env, meta, pages, a.paper, workdir, a.spine, a.price)
    stem = re.sub(r"\D", "", a.isbn) if a.isbn else "book"
    txt_x = pdfx(pdf, workdir / f"{stem}_txt.pdf", True, env["ORIGINAL_WORK"])
    cov_x = pdfx(cover_pdf, workdir / f"{stem}_cov.pdf", False, env["ORIGINAL_WORK"])
    print(report(workdir, txt_x, pages, inner, figs, warnings, cover_pdf, spine, size, a.paper,
                 txt_x, cov_x, a.spine is not None))
    proofs(workdir, pdf, cover_pdf)
    print(f"\nproofs: {workdir}/proof/  (sheet-*.png = facing spreads; p-*.png = each page; cover-1.png)")


if __name__ == "__main__":
    main()
