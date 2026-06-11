"""Assemble a book's modern_chapters into a single HTML page.

    python3 assemble.py <book_dir> [--out site/<name>.html]

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

The page shell comes from site/template.html.
"""

import argparse
import html
import json
import re
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


def is_subheading(par):
    if "\n" in par or len(par) > 90:
        return False
    if par[-1] in ".;:,—":
        return False
    words = par.split()
    caps = sum(1 for w in words if w[0].isupper())
    return caps >= max(1, len(words) // 2)


def render_body(text):
    out = []
    for par in re.split(r"\n\s*\n", text):
        par = par.rstrip()
        if not par.strip():
            continue
        if re.search(r"^[ \t]", par, re.M):
            out.append(f'<pre class="outline">{html.escape(par)}</pre>')
        elif is_subheading(par.strip()):
            out.append(f"<h4>{html.escape(par.strip())}</h4>")
        else:
            out.append(f"<p>{html.escape(par.strip())}</p>")
    return "\n".join(out)


def strip_front(lines, expect_heading):
    """Drop leading blanks, part dividers, the chapter heading, and part
    markers; return (heading_found, remaining_text)."""
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
    return heading, "\n".join(lines[j:]).strip()


def load_manifest(book):
    mpath = book / "manifest.json"
    if mpath.exists():
        return json.loads(mpath.read_text())
    files = sorted(p.name for p in (book / "modern_chapters").glob("*.txt"))
    if not files:
        sys.exit(f"ERROR: no modern_chapters in {book}")
    return [{"file": f, "title": "", "part": 1, "of": 1} for f in files]


def build_sections(book, manifest):
    """Return a list of {id, heading, body, is_chapter, part_before}."""
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
            lines = (book / "modern_chapters" / m["file"]).read_text().split("\n")
            h, rest = strip_front(lines, expect_heading=not g["split_headings"])
            if i == 0:
                heading = h
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


def build_body(sections):
    out = []
    for s in sections:
        if s["part_before"]:
            pid = slugify(s["part_before"].split(":")[0])
            out.append(f'<h2 id="{pid}" class="center">{html.escape(s["part_before"])}</h2>')
        tag = "h3" if s["is_chapter"] else "h2"
        out.append(f'<{tag} id="{s["id"]}">{html.escape(s["heading"])}</{tag}>')
        out.append(render_body(s["body"]))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir")
    ap.add_argument("--out", help="output path (default site/<book_dir>.html)")
    args = ap.parse_args()

    book = Path(args.book_dir)
    root = Path(__file__).parent
    out = Path(args.out) if args.out else root / "site" / f"{book.name}.html"

    env = read_env(book / "env")
    for key in ("ORIGINAL_WORK", "AUTHOR", "DATE"):
        if key not in env:
            sys.exit(f"ERROR: {key} missing from {book}/env")

    sections = build_sections(book, load_manifest(book))

    subtitle = env.get("SUBTITLE", "")
    subtitle_block = f"\t<h3>{html.escape(subtitle)}</h3>\n" if subtitle else ""
    if env.get("SOURCE_URL"):
        name = env.get("SOURCE_NAME", env["SOURCE_URL"])
        source_sentence = (f' The original is available from '
                           f'<a href="{env["SOURCE_URL"]}">{html.escape(name)}</a>.')
    else:
        source_sentence = ""

    page = (root / "site" / "template.html").read_text()
    for key, val in {
        "{{TITLE}}": html.escape(env["ORIGINAL_WORK"]),
        "{{AUTHOR}}": html.escape(env["AUTHOR"]),
        "{{DATE}}": html.escape(env["DATE"]),
        "{{MODERN_YEAR}}": env.get("MODERN_YEAR", "2026"),
        "{{SUBTITLE_BLOCK}}": subtitle_block,
        "{{SOURCE_SENTENCE}}": source_sentence,
        "{{TOC}}": build_toc(sections),
        "{{BODY}}": build_body(sections),
    }.items():
        page = page.replace(key, val)

    out.write_text(page)
    print(f"wrote {out} ({len(page)} bytes, {len(sections)} sections)")


if __name__ == "__main__":
    main()
