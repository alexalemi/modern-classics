"""Build a Standard-Ebooks-quality epub from a book's modern_chapters.

    python3 build_ebook.py <book_dir> [--out-dir site/ebooks] [--skip-build]

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


def load_sections(book):
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
    return assemble.build_sections(book, manifest)


def classify_block(par):
    """paragraph | subhead | verse | lines"""
    stripped = par.strip()
    if re.search(r"^[ \t]", par, re.M):
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

def render_block(par, kind):
    s = par.strip()
    if ASTERISM.match(re.sub(r"\s+", " ", s)):
        return "\t\t\t<hr/>"
    if kind == "paragraph":
        if is_all_caps(s) and len(s) < 200 and "\n" not in s:
            return f'\t\t\t<p class="subhead">{esc(nice_title(s))}</p>'
        text = ERA.sub(r'<abbr epub:type="se:era">\1\2</abbr>', esc(s))
        return f"\t\t\t<p>{text}</p>"
    if kind == "subhead":
        return f'\t\t\t<p class="subhead">{esc(s)}</p>'
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    if kind == "verse":
        inner = "\n".join(
            f'\t\t\t\t\t\t<p><span>{esc(l)}</span></p>' for l in lines)
        return ("\t\t\t<blockquote epub:type=\"z3998:verse\">\n"
                "\t\t\t\t<div>\n" + inner + "\n\t\t\t\t</div>\n\t\t\t</blockquote>")
    # generic lined matter (outlines, tables of figures, speaker lists)
    inner = "<br/>\n\t\t\t\t".join(esc(l) for l in lines)
    return f"\t\t\t<blockquote class=\"lines\">\n\t\t\t\t<p>{inner}</p>\n\t\t\t</blockquote>"


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
        req = urllib.request.Request(commons_url(art["commons"]),
                                     headers={"User-Agent": "modern-classics-ebooks/1.0"})
        src.write_bytes(urllib.request.urlopen(req).read())
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
    subprocess.run(["convert", str(src)] + geom +
                   ["-resize", "1400x2100!", "-quality", "90",
                    str(dest / "images/cover.jpg")], check=True)


def run(cmd, cwd, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, input="y\n")
    if check and r.returncode not in (0, 18):  # 18 = NoResults on finder tools
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed:\n{r.stdout}\n{r.stderr}")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("book_dir")
    ap.add_argument("--out-dir", default=str(ROOT / "site" / "ebooks"))
    ap.add_argument("--skip-build", action="store_true")
    args = ap.parse_args()

    book = Path(args.book_dir)
    env = assemble.read_env(book / "env")
    all_meta = json.loads((ROOT / "ebook_meta.json").read_text())
    meta = all_meta[book.name]

    author, work = env["AUTHOR"], env["ORIGINAL_WORK"]
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

    sections = load_sections(book)
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
    rebrand.apply(dest, env, meta, spine)
    prepare_cover(dest, meta)

    for step in (["typogrify", "."], ["clean", "."], ["build-manifest", "."],
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
            run([SE, "build", "--check", f"--output-dir={td}", "."], cwd=dest)
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
