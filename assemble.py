"""Assemble a book's modern_chapters into a single HTML page.

    python3 assemble.py <book_dir> [--out site/<name>.html]
    python3 assemble.py <book_dir> --original     # the source text instead

`--original` assembles chapters/ rather than modern_chapters/ and writes
site/<name>-original.html: the same book in the words it was published in,
for readers who want to see what the modernization is a modernization of.
Two things differ from the modern build, both because chapters/ is the
splitter's output rather than a translator's:

  - headings come from manifest.json, not from the file's first line
    (a source file opens on the chapter's own contents-summary paragraph);
  - a plate keeps the label the original printed under it ("Fig. 22.") and
    gets no caption, because the captions in this collection are new
    writing and belong only to the modern edition.

Set ORIGINAL_TEXT=yes in the book's env to cross-link the two pages.

Driven by two data files in <book_dir>:

  env            ORIGINAL_WORK, AUTHOR, DATE required; optional SUBTITLE,
                 SOURCE_NAME + SOURCE_URL (attribution link), MODERN_YEAR.
  manifest.json  one entry per chapter file: {"file", "title", "part", "of"}.
                 Optional per-entry fields:
                   "part_before":   part/book divider heading emitted before
                                    this chapter (e.g. "Part II: Of Commonwealth")
                   "split_headings": standalone heading lines that divide this
                                    file into several front/back-matter sections

If manifest.json is missing, every modern_chapters/NNN.txt is treated as one
chapter whose heading is its first line.

Conventions read from the chapter files themselves:
  - first non-empty line (after any part divider) = chapter heading;
    "Chapter N: Title" headings are grouped under part dividers in the TOC,
    anything else becomes a standalone top-level section
  - "(Part n of k)" marker lines and "Part X: ..." divider lines are stripped
  - a short title-case line with no terminal punctuation = subheading (h4)
  - a paragraph with indented lines is preserved as <pre> (outlines/tables)
  - "[Figure N: caption]" on its own becomes <figure><img><figcaption>, for
    illustrated books that set FIGURE_DIR in env (e.g. images/soap-bubbles);
    the image is <FIGURE_DIR>/figN.<ext> relative to site/, with any of
    jpg/png/gif. Intrinsic width and height are read from the file so
    narrow plates are not stretched and the page does not reflow as images
    load. The caption may be omitted ("[Figure 39b]") for scale bars and
    continuation plates.

The page shell comes from site/template.html.
"""

import argparse
import html
import json
import re
import struct
import sys
from pathlib import Path

PART_LINE = re.compile(r"^Part [IVXLC0-9]+: \S.*$")
PART_MARK = re.compile(r"^\(Part \d+ of \d+\)$", re.I)
CHAP_LINE = re.compile(r"^Chapter (\d+): (.*)$")


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def is_subheading(par, next_par=None):
    if "\n" in par or len(par) > 90:
        return False
    if par[-1] in ".;:,—":
        return False
    # A QUOTED LINE IS SPEECH, NOT A TITLE. Two-sentence dialogue slips
    # past the "?"/"!" rule below -- "\u201cYes. A Frenchman named
    # Passepartout.\u201d", "\u201cWorried? No.\u201d" -- and twenty-eight of
    # them were being set as section headings across the two Verne novels,
    # Twenty Thousand Leagues and the Memorabilia. Nothing in this project
    # titles a section with a quotation mark in front of it.
    if par[0] in "\"'\u201c\u2018":
        return False
    # AND SO IS A LINE THAT ENDS ON ONE -- but only when the quote is
    # INTRODUCED. The rule above catches speech that begins with the
    # quotation mark; narration in front of it hides the line completely
    # ('Hans answered, "To Gretel."', 'Said St. Peter, "You go first."'),
    # because the terminal stop is inside the quotes where the test above
    # cannot see it. Eleven lines of Clever Hans were set as section
    # headings in the middle of their own conversation.
    # THE BLUNT RULE -- any line ending in a closing quote -- REGRESSES
    # LEVIATHAN, whose real section titles quote a TERM: 'The Different
    # Meanings of the Word "Prophet"', 'The Names "Sacerdotes" and
    # "Sacrifices"'. What separates them is what stands before the opening
    # quote. Reported speech introduces it with a comma or a full stop;
    # a quoted term sits inside a noun phrase with nothing but a space.
    if par[-1] in "\"'\u201d\u2019" and QUOTE_INTRO.search(par):
        return False
    # NEITHER IS ANYTHING CARRYING A SQUARE BRACKET. Brackets mark the
    # author in a lower voice throughout this project -- Carroll's glosses
    # on a definition, Boys' modern notes -- and Carroll sets every step of
    # a worked example inside them: "[(6) The Proposition now becomes]",
    # "[(4) Let Univ. be 'persons.']", "No Conclusion. [Fallacy of Unlike
    # Eliminands with an Entity-Premiss.]". Short, majority-capitalised and
    # with no terminal stop, fifty of them read as section titles.
    if "[" in par:
        return False
    # A short spoken line ending in "?" or "!" is not a heading. This has to
    # be narrow: Leviathan and The Social Contract both give whole sections
    # question-form titles ("Could Church Councils Make Scripture Law?"),
    # so the terminal mark alone cannot decide it. What separates the two is
    # that dialogue carries a speaker tag ("Christian. What were you once?")
    # or runs to more than one sentence ("Pliable. Well said. And what
    # else?"); a heading does neither. Without this, every short question in
    # a dialogue book is set as a section heading mid-conversation.
    if par[-1] in "?!" and (SPEAKER_TAG.match(par) or SENTENCE_BREAK.search(par)):
        return False
    words = par.split()
    caps = sum(1 for w in words if w[0].isupper())
    return caps >= max(1, len(words) // 2)


QUOTE_INTRO = re.compile(r"[,.]\s+[\"'\u201c\u2018]")
SPEAKER_TAG = re.compile(r"[A-Z][A-Za-z'\u2019-]{0,20}\.\s+\S")
SENTENCE_BREAK = re.compile(r"[.?!]\s+[A-Z]")
SPEAKER_NAME = re.compile(r"[A-Z][A-Za-z .'’-]{0,30}")
HR_LINE = re.compile(r"\*+( \*+)*|-{2,}")
FIGURE = re.compile(
    r"^\[Figure ([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)(?::\s*(.+?))?\]$", re.S)


def figure_label(num):
    """'12' -> 'Figure 12'; '42a' -> 'Figure 42a' (one half of a two-part
    plate); '15-16-17' -> 'Figures 15, 16 and 17' (one block carrying
    several numbered figures, as Victorian books often print them).

    An id may carry a NAMESPACE prefix ending in '_': 'app_1' -> 'Figure 1'.
    A book that restarts its figure numbering — an appendix with its own
    Fig. 1 while chapter one also has a Fig. 1 — needs two plates with the
    same printed label and different filenames. The prefix picks the file;
    only what follows it is shown to the reader.

    An id with no digits at all ('front', 'music') is a plate the book
    never numbered: it gets no "Figure N" prefix and its caption stands
    alone. "Frontispiece" is the one such id with a conventional name."""
    if num == "front":
        return "Frontispiece"
    if not any(c.isdigit() for c in num):
        return None
    parts = [p.rsplit("_", 1)[-1] for p in num.split("-")]
    if len(parts) == 1:
        return f"Figure {parts[0]}"
    return f"Figures {', '.join(parts[:-1])} and {parts[-1]}"


FIG_EXTS = ("jpg", "jpeg", "png", "gif")


def figure_name(site, figdir, num):
    """Plate filename for figure `num`, whatever extension it was saved as
    (photographic plates arrive as JPEG, line-art woodcuts as PNG)."""
    stem = "front" if num == "front" else f"fig{num}"
    for ext in FIG_EXTS:
        if (site / figdir / f"{stem}.{ext}").exists():
            return f"{stem}.{ext}"
    return f"{stem}.jpg"


def image_size(path):
    """(width, height) for a JPEG or PNG, or None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker == 0xD8 or 0xD0 <= marker <= 0xD9:
            i += 2
        else:
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def render_figure(num, caption, figdir, site, bare_label=False):
    """<figure> for a [Figure N: caption] paragraph. `num` names the file
    (fig12.jpg), except "front" which is the frontispiece plate.

    `bare_label` is for the original-text edition, where the source has no
    captions to give: the plate keeps the number the book printed under it
    and nothing else."""
    caption = " ".join(caption.split()) if caption else None
    if bare_label and not caption:
        label = figure_label(num)
        src = f"{figdir}/{figure_name(site, figdir, num)}"
        dims = image_size(site / src)
        size = f' width="{dims[0]}" height="{dims[1]}"' if dims else ""
        cap = (f'\n<figcaption><b>{label}</b></figcaption>' if label else "")
        return (f'<figure id="fig-{num}">\n<img src="{src}" '
                f'alt="{html.escape(label or "Plate", quote=True)}"{size} '
                f'loading="lazy">{cap}\n</figure>')
    src = f"{figdir}/{figure_name(site, figdir, num)}"
    label = figure_label(num)
    dims = image_size(site / src)
    size = f' width="{dims[0]}" height="{dims[1]}"' if dims else ""
    alt = html.escape(caption or label or "Plate", quote=True)
    out = [f'<figure id="fig-{num}">',
           f'<img src="{src}" alt="{alt}"{size} loading="lazy">']
    if caption and label:
        out.append(f'<figcaption><b>{label}</b> &mdash; '
                   f'{html.escape(caption)}</figcaption>')
    elif caption:
        out.append(f'<figcaption>{html.escape(caption)}</figcaption>')
    out.append("</figure>")
    return "\n".join(out)


FIGURE_INLINE = re.compile(
    r"\[Figure ([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)(?::\s*([^\]]+))?\]")


def render_plate_table(par, figdir, site, bare_label=False):
    """An indented block whose cells include figure markers -> a table.

    Cells are split on the spaced pipe the rest of the pipeline uses. A cell
    that is a figure marker becomes the plate itself; anything else is set
    as text, with the marker's caption carried into the img's alt so a
    reader who cannot see the plate still gets what is on it."""
    rows = []
    for line in par.split("\n"):
        if not line.strip():
            continue
        cells = [c.strip() for c in line.strip().split(" | ")]
        tds = []
        for c in cells:
            m = FIGURE_INLINE.fullmatch(c)
            if m:
                tds.append("<td>" + render_figure(m.group(1), m.group(2),
                                                  figdir, site, bare_label)
                           + "</td>")
            else:
                parts, last = [], 0
                for m in FIGURE_INLINE.finditer(c):
                    parts.append(html.escape(c[last:m.start()]))
                    parts.append(render_figure(m.group(1), m.group(2),
                                               figdir, site, bare_label))
                    last = m.end()
                parts.append(html.escape(c[last:]))
                tds.append("<td>" + "".join(parts) + "</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return '<table class="plates">\n' + "\n".join(rows) + "\n</table>"


# UNICODE SUPERSCRIPTS AND SUBSCRIPTS ARE A FONT LOTTERY. "x²" needs the
# reader's font to carry U+00B2; "x⁴" needs U+2074, "sin⁻¹" needs U+207B and
# U+00B9, and S₁₀₀ needs the subscript digits -- and an e-ink reader that has
# the first of those very often has none of the rest, so the page comes out
# with tofu boxes in the middle of the mathematics. Rendered as markup they
# need nothing but an ordinary digit.
SUPERS = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
          "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁺": "+", "⁻": "−",
          "⁼": "=", "⁽": "(", "⁾": ")", "ⁿ": "n", "ⁱ": "i"}
SUBS = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5",
        "₆": "6", "₇": "7", "₈": "8", "₉": "9", "₊": "+", "₋": "−",
        "₌": "=", "₍": "(", "₎": ")", "ₙ": "n", "ₐ": "a", "ₑ": "e",
        "ₓ": "x"}
SCRIPT_RUN = re.compile("([" + "".join(SUPERS) + "]+)|([" + "".join(SUBS) + "]+)")


def scripts(escaped):
    """Runs of Unicode super/subscript characters -> <sup>/<sub> markup.

    Takes ALREADY-ESCAPED text and returns text with markup in it, so it must
    be the last thing applied to a fragment.
    """
    def sub(m):
        if m.group(1):
            return "<sup>" + "".join(SUPERS[c] for c in m.group(1)) + "</sup>"
        return "<sub>" + "".join(SUBS[c] for c in m.group(2)) + "</sub>"
    return SCRIPT_RUN.sub(sub, escaped)


# EMPHASIS. _like this_ and *like this* become <em>, which reverses this
# project's markup-free rule for one specific case, by Alex's ruling of
# 2026-08-17. The rule stands everywhere else: structure still comes only
# from convention (tab indent = verse or table, ALL CAPS = heading), and
# nothing else in the pipeline reads markup.
#
# THE PATTERN HAS TO BE NARROW, because a bare asterisk means other
# things in these books:
#   - "* * *" is a SCENE SEPARATOR and is already an <hr> by HR_LINE. It
#     survives here anyway, because the delimiters must not enclose
#     whitespace: "* *" would otherwise become an empty <em>. 52 of
#     democracy2's asterisks and 291 of progress-and-poverty's are this,
#     not emphasis, and a blanket conversion would have wrecked both.
#   - an underscore inside a word (a figure id like "app_1") is not a
#     delimiter, so both sides are anchored against word characters.
# What legitimately matches is emphasis (flatland's 78 spans, the
# Federalist's "must", "might", "intend"), species binomials in
# origin-of-species ("C. livia"), and the Decameron's story rubrics.
#
# A SPAN MAY CROSS A LINE BREAK. The Decameron marks each day's and each
# story's rubric with a single pair of asterisks around a summary that
# runs to several lines inside one paragraph; forbidding "\n" left 78 of
# them unconverted with their asterisks showing. The span is capped at
# 400 characters and still cannot enclose whitespace at either end, so it
# cannot run away across a paragraph.
#
# Applied to ALREADY-ESCAPED text and returning markup, exactly like
# scripts(), so it must be among the last things done to a fragment.
EMPH = re.compile(
    r"(?<![A-Za-z0-9_])_(?!\s)([^_]{1,400}?)(?<!\s)_(?![A-Za-z0-9_])"
    r"|(?<![*\w])\*(?!\s)([^*]{1,400}?)(?<!\s)\*(?!\*)", re.S)


def emphasis(escaped):
    return EMPH.sub(lambda m: "<em>" + (m.group(1) or m.group(2)) + "</em>",
                    escaped)


def inline(escaped):
    """Every inline transform, in one place, for BOTH renderers.
    build_ebook.esct() calls this too, so the page and the epub cannot
    drift apart."""
    return scripts(emphasis(escaped))


def find_speakers(pars):
    """Dialogue speakers: short bare names that repeatedly open a block's
    first line (Plato's dialogues put the speaker on its own line)."""
    counts = {}
    for par in pars:
        lines = par.strip().split("\n")
        head = lines[0].strip()
        if (len(lines) >= 2 and SPEAKER_NAME.fullmatch(head)
                and not head.isupper() and not head.endswith(".")):
            counts[head] = counts.get(head, 0) + 1
    return {name for name, n in counts.items() if n >= 3}


def render_body(text, figdir=None, site=None, bare_label=False):
    pars = [p.rstrip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    speakers = find_speakers(pars)
    out = []
    for i, par in enumerate(pars):
        nxt = pars[i + 1] if i + 1 < len(pars) else None
        s = par.strip()
        lines = s.split("\n")
        fig = FIGURE.match(s) if figdir else None
        if fig:
            out.append(render_figure(fig.group(1), fig.group(2), figdir,
                                     site, bare_label))
        elif HR_LINE.fullmatch(s):
            out.append("<hr>")
        elif re.search(r"^[ \t]", par, re.M):
            # AN INDENTED BLOCK HOLDING PLATES IS A TABLE, NOT AN OUTLINE.
            # Carroll tabulates his diagrams against their readings, so a
            # figure marker is frequently one CELL of a row; set as <pre> it
            # printed the marker as literal text and the plate never
            # appeared at all -- 248 of the 308 in symbolic-logic/. Only a
            # block that actually carries a marker takes this path, so no
            # other book's tables change.
            if figdir and FIGURE_INLINE.search(par):
                out.append(render_plate_table(par, figdir, site, bare_label))
            else:
                out.append(f'<pre class="outline">{inline(html.escape(par))}</pre>')
        elif len(lines) >= 2 and lines[0].strip() in speakers:
            rest = " ".join(l.strip() for l in lines[1:])
            out.append(f"<p><b>{html.escape(lines[0].strip())}</b>: "
                       f"{inline(html.escape(rest))}</p>")
        elif is_subheading(s, nxt):
            out.append(f"<h4>{inline(html.escape(s))}</h4>")
        else:
            out.append(f"<p>{inline(html.escape(s))}</p>")
    while out and out[0] == "<hr>":
        out.pop(0)
    while out and out[-1] == "<hr>":
        out.pop()
    return "\n".join(out)


def strip_front(lines, expect_heading):
    """Drop leading blanks, part dividers, the chapter heading, and part
    markers; return (heading_found, remaining_text).

    Trims blank lines only, never the leading spaces of the first surviving
    line: a chapter whose body opens with an indented block (verse, an
    outline) must keep that indentation, which is what marks it as <pre>."""
    heading = None
    j = 0
    while j < len(lines):
        s = lines[j].strip()
        if not s or PART_LINE.match(s) or PART_MARK.match(s):
            j += 1
        elif heading is None and expect_heading:
            heading = s
            j += 1
        else:
            break
    return heading, "\n".join(lines[j:]).strip("\n").rstrip()


UID = re.compile(r'<dc:identifier id="uid">([^<]*)</dc:identifier>')


def find_epub(book, root, original=False):
    """This book's epub in site/ebooks, matched on the dc:identifier.

    NOT on dc:source: both editions of a book cite the same repo directory
    there, so matching dc:source hands the modern page the original-text
    epub. The identifier is the one field the two are guaranteed to differ
    in — the original carries "#original-text" — because it is what makes
    them distinct works to a reader's library in the first place."""
    import zipfile
    want = f"/tree/main/{book.name}{'#original-text' if original else ''}"
    for f in sorted((root / "site" / "ebooks").glob("*.epub")):
        if f.name.endswith("_advanced.epub"):
            continue
        try:
            opf = zipfile.ZipFile(f).read("epub/content.opf").decode()
        except Exception:
            continue
        m = UID.search(opf)
        if m and m.group(1).endswith(want):
            return f.name
    return None


def load_manifest(book):
    mpath = book / "manifest.json"
    if mpath.exists():
        return json.loads(mpath.read_text())
    # NNN.txt only — the directory also holds NNN_notes.txt translation notes
    files = sorted(p.name for p in (book / "modern_chapters").glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    if not files:
        sys.exit(f"ERROR: no modern_chapters in {book}")
    return [{"file": f, "title": "", "part": 1, "of": 1} for f in files]


def build_sections(book, manifest, source="modern_chapters", titles=False):
    """Return a list of {id, heading, body, is_chapter, part_before}.

    `titles` takes each section's heading from manifest.json instead of from
    the file's first line, which is what the original-text build needs: a
    source file has no heading of its own and opens straight on the
    chapter's contents summary."""
    groups = []
    for m in manifest:
        if m["part"] == 1:
            groups.append({"entries": [], "part_before": m.get("part_before"),
                           "split_headings": m.get("split_headings")})
        groups[-1]["entries"].append(m)

    sections = []
    for g in groups:
        bodies, heading = [], None
        for i, m in enumerate(g["entries"]):
            lines = (book / source / m["file"]).read_text().split("\n")
            h, rest = strip_front(
                lines, expect_heading=not (g["split_headings"] or titles))
            if i == 0:
                heading = m.get("title") if titles else h
            bodies.append(rest)
        body = "\n\n".join(bodies)

        if g["split_headings"]:
            # carve one file into several standalone sections
            pat = "|".join(re.escape(h) for h in g["split_headings"])
            pieces = re.split(rf"^({pat})$", body, flags=re.M)
            # pieces: [before, head1, body1, head2, body2, ...]
            for k in range(1, len(pieces), 2):
                sections.append({"id": slugify(pieces[k]), "heading": pieces[k],
                                 "body": pieces[k + 1].strip(),
                                 "is_chapter": False,
                                 "part_before": g["part_before"] if k == 1 else None})
            continue

        cm = CHAP_LINE.match(heading or "")
        sections.append({
            "id": f"ch-{cm.group(1)}" if cm else slugify(heading or "section"),
            "heading": heading or "(untitled)",
            "body": body,
            "is_chapter": bool(cm),
            "part_before": g["part_before"],
        })
    return unique_ids(sections)


def unique_ids(sections):
    """Make every section id unique, keeping the first of each.

    AN ID IS A DESTINATION, AND A REPEATED ONE SILENTLY SENDS THE READER
    TO THE WRONG PLACE — the browser jumps to the first match. Don Quixote
    numbers its chapters from 1 twice, once per Part, so every Part Two
    entry in its table of contents pointed at the Part One chapter of the
    same number: 52 wrong links in the collection's largest novel. The
    same shape appears wherever a heading repeats — six "CHAPTER I." in
    democracy2, nine "MEDITATIONS ON THE FIRST PHILOSOPHY" in descartes,
    eleven "Persons of the dialogue:" in Plato.

    The FIRST occurrence keeps the bare id, so every link that already
    worked still works and only the broken ones move.
    """
    seen = {}
    for s in sections:
        base = s["id"]
        n = seen.get(base, 0) + 1
        seen[base] = n
        if n > 1:
            s["id"] = f"{base}-{n}"
    return sections


def build_toc(sections):
    toc, open_list = [], False
    for s in sections:
        if s["part_before"]:
            if open_list:
                toc.append("</ul>")
                open_list = False
            toc.append(f'<p class="toc-book">{html.escape(s["part_before"])}</p>')
        if s["is_chapter"]:
            if not open_list:
                toc.append('<ul class="toc-list">')
                open_list = True
            toc.append(f'<li><a href="#{s["id"]}">{html.escape(s["heading"])}</a></li>')
        else:
            if open_list:
                toc.append("</ul>")
                open_list = False
            toc.append(f'<p><a href="#{s["id"]}">{html.escape(s["heading"])}</a></p>')
    if open_list:
        toc.append("</ul>")
    return "\n".join(toc)


def build_body(sections, figdir=None, site=None, bare_label=False):
    out = []
    for s in sections:
        if s["part_before"]:
            pid = slugify(s["part_before"].split(":")[0])
            out.append(f'<h2 id="{pid}" class="center">{html.escape(s["part_before"])}</h2>')
        tag = "h3" if s["is_chapter"] else "h2"
        out.append(f'<{tag} id="{s["id"]}">{html.escape(s["heading"])}</{tag}>')
        out.append(render_body(s["body"], figdir, site, bare_label))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir")
    ap.add_argument("--out", help="output path (default site/<book_dir>.html)")
    ap.add_argument("--original", action="store_true",
                    help="assemble chapters/ into site/<book_dir>-original.html")
    args = ap.parse_args()

    book = Path(args.book_dir)
    root = Path(__file__).parent

    env = read_env(book / "env")
    # PAGE: the published filename, when it is not the directory name.
    # Two early books were published under the name of the WORK rather
    # than of the directory -- descartes/ as philosophical-works.html and
    # malthus/ as population.html -- and only build_feeds.py knew it, in a
    # hard-coded dict of its own. So assemble wrote site/descartes.html,
    # which nothing linked to, and the page the site actually served went
    # on being the stale one: a repair to descartes/ in August 2026 fixed
    # nineteen duplicate contents entries and restored four Part titles
    # that had been deleted outright, and NONE of it reached a reader.
    # Nothing caught it, because every check looked at a file that was
    # being written correctly. One fact, one place.
    page = env.get("PAGE", book.name)
    stem = f"{page}-original" if args.original else page
    out = Path(args.out) if args.out else root / "site" / f"{stem}.html"
    for key in ("ORIGINAL_WORK", "AUTHOR", "DATE"):
        if key not in env:
            sys.exit(f"ERROR: {key} missing from {book}/env")

    sections = build_sections(book, load_manifest(book),
                              source="chapters" if args.original
                              else "modern_chapters", titles=args.original)

    subtitle = env.get("SUBTITLE", "")
    subtitle_block = f"\t<h3>{html.escape(subtitle)}</h3>\n" if subtitle else ""
    if env.get("SOURCE_URL"):
        name = env.get("SOURCE_NAME", env["SOURCE_URL"])
        source_sentence = (f' The original is available from '
                           f'<a href="{env["SOURCE_URL"]}">{html.escape(name)}</a>.')
    else:
        source_sentence = ""
    epub = find_epub(book, root, original=args.original)
    epub_sentence = (f' Also available as an <a href="ebooks/{epub}">epub</a>.'
                     if epub else "")
    title = html.escape(env["ORIGINAL_WORK"])
    if args.original:
        date_line = html.escape(env["DATE"])
        intro = (f'<p><i>This is the original text of {title}, as it was '
                 f'published, for readers who want to see what the '
                 f'modernization is a modernization of. '
                 f'<a href="{book.name}.html">The modern retelling is '
                 f'here</a>.{source_sentence}{epub_sentence}</i></p>')
    else:
        date_line = f'<s>{html.escape(env["DATE"])}</s> ' \
                    f'{env.get("MODERN_YEAR", "2026")}'
        original_sentence = (
            f' <a href="{book.name}-original.html">The original text is also '
            f'here</a>.' if env.get("ORIGINAL_TEXT") else "")
        intro = (f'<p><i>This is an AI modernization of {title} into '
                 f'contemporary English.{source_sentence}{epub_sentence}'
                 f'{original_sentence}</i></p>')

    page = (root / "site" / "template.html").read_text()
    for key, val in {
        "{{TITLE}}": title,
        "{{AUTHOR}}": html.escape(env["AUTHOR"]),
        "{{DATE_LINE}}": date_line,
        "{{SUBTITLE_BLOCK}}": subtitle_block,
        "{{INTRO}}": intro,
        "{{TOC}}": build_toc(sections),
        "{{BODY}}": build_body(sections, env.get("FIGURE_DIR"), root / "site",
                               bare_label=args.original),
    }.items():
        page = page.replace(key, val)

    out.write_text(page)
    print(f"wrote {out} ({len(page)} bytes, {len(sections)} sections)")


if __name__ == "__main__":
    main()
