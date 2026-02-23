#!/usr/bin/env python3
"""Assemble Democracy in America modern chapters into a single HTML file."""

import re
from pathlib import Path

BOOK_DIR = Path("democracy/modern_chapters")
OUT_FILE = Path("site/democracy.html")
NUM_CHAPTERS = 119  # 000 through 118


def read_chapter(num):
    """Read a chapter file and return its text content."""
    path = BOOK_DIR / f"{num:03d}.txt"
    return path.read_text(encoding="utf-8")


def text_to_html_paragraphs(text):
    """Convert plain text to HTML paragraphs, handling *** as section breaks."""
    paragraphs = []
    current = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    html_parts = []
    for p in paragraphs:
        if p.strip() == "***":
            html_parts.append('<hr class="section-break">')
        elif p.startswith("*") and p.endswith("*") and not p.startswith("**"):
            # Italic paragraph (like Tocqueville's preface note)
            inner = p.strip("*").strip()
            html_parts.append(f"<p><em>{escape_html(inner)}</em></p>")
        else:
            html_parts.append(f"<p>{escape_html(p)}</p>")

    return "\n\n".join(html_parts)


def escape_html(text):
    """Minimal HTML escaping, preserving em-dashes and common punctuation."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Convert markdown-style italics to HTML
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Convert -- to em-dash
    text = text.replace(" -- ", " &mdash; ")
    return text


def classify_first_line(line):
    """Classify what kind of heading the first line represents."""
    line = line.strip()
    if not line:
        return "empty", ""
    upper = line.upper()
    if upper.startswith("BOOK ") or (line.startswith("Book ") and "Chapter" not in line):
        return "book", line
    if line.startswith("Section "):
        return "section", line
    if line.startswith("Chapter "):
        return "chapter", line
    # Known sub-section headings (from continuation files)
    return "text", line


# Define the structure: each entry is (chapter_num, heading_override)
# heading_override is used for continuation files that need a sub-heading
# None means use auto-detection from first line
STRUCTURE = []
for i in range(NUM_CHAPTERS):
    STRUCTURE.append(i)

# Build TOC entries and body content
toc_entries = []
body_parts = []


def make_id(num):
    return f"ch{num:03d}"


def add_toc(level, text, anchor):
    toc_entries.append((level, text, anchor))


# Process each chapter
for num in range(NUM_CHAPTERS):
    text = read_chapter(num)
    lines = text.strip().split("\n")
    first_line = lines[0].strip() if lines else ""
    kind, heading = classify_first_line(first_line)

    anchor = make_id(num)
    body = []

    if kind == "book":
        # Book-level heading (h1)
        # Check if there's a subtitle on the next non-empty line
        subtitle = ""
        content_start = 1
        for j in range(1, len(lines)):
            if lines[j].strip():
                # Check if it's a subtitle (not a chapter heading, not ***)
                candidate = lines[j].strip()
                if not candidate.startswith("Chapter") and candidate != "***":
                    subtitle = candidate
                    content_start = j + 1
                else:
                    content_start = j
                break

        body.append(f'<h1 id="{anchor}">{escape_html(heading)}</h1>')
        if subtitle:
            body.append(f'<h3 class="subtitle">{escape_html(subtitle)}</h3>')
        add_toc(1, heading, anchor)

        # Check for embedded chapter heading (skip past *** and blank lines)
        remaining_text = "\n".join(lines[content_start:]).strip()
        remaining_lines = remaining_text.split("\n")
        found_chapter = False
        for k, rl in enumerate(remaining_lines):
            stripped_rl = rl.strip()
            if not stripped_rl or stripped_rl == "***":
                continue
            if stripped_rl.startswith("Chapter"):
                ch_heading = stripped_rl
                ch_anchor = f"{anchor}-ch"
                body.append(f'<h2 id="{ch_anchor}">{escape_html(ch_heading)}</h2>')
                add_toc(2, ch_heading, ch_anchor)
                remaining_text = "\n".join(remaining_lines[k + 1:]).strip()
                found_chapter = True
            else:
                remaining_text = "\n".join(remaining_lines[k:]).strip()
            break

        if remaining_text:
            body.append(text_to_html_paragraphs(remaining_text))

    elif kind == "section":
        # Section heading (h2 styled as section divider)
        body.append(f'<h1 id="{anchor}" class="section-heading">{escape_html(heading)}</h1>')
        add_toc(1, heading, anchor)

        # Check for embedded chapter
        remaining_text = "\n".join(lines[1:]).strip()
        remaining_lines = remaining_text.split("\n")
        # Skip *** separator
        start = 0
        for j, l in enumerate(remaining_lines):
            if l.strip() == "***":
                start = j + 1
                continue
            if l.strip().startswith("Chapter"):
                ch_heading = l.strip()
                ch_anchor = f"{anchor}-ch"
                body.append(f'<h2 id="{ch_anchor}">{escape_html(ch_heading)}</h2>')
                add_toc(2, ch_heading, ch_anchor)
                remaining_text = "\n".join(remaining_lines[j + 1:]).strip()
                break
            elif l.strip():
                remaining_text = "\n".join(remaining_lines[j:]).strip()
                break

        if remaining_text:
            body.append(text_to_html_paragraphs(remaining_text))

    elif kind == "chapter":
        # Standard chapter heading
        body.append(f'<h2 id="{anchor}">{escape_html(heading)}</h2>')

        # Check for chapter overview / description on next lines
        remaining = "\n".join(lines[1:]).strip()
        add_toc(2, heading, anchor)

        if remaining:
            body.append(text_to_html_paragraphs(remaining))

    else:
        # Continuation / sub-section
        # Check if the first line looks like a sub-heading (short, no period)
        if len(first_line) < 120 and not first_line.endswith(".") and not first_line.endswith(","):
            # Treat as sub-heading
            body.append(f'<hr class="section-break">')
            body.append(f'<h3 id="{anchor}">{escape_html(first_line)}</h3>')
            remaining = "\n".join(lines[1:]).strip()
            add_toc(3, first_line, anchor)
        else:
            # Pure continuation - just a break and content
            body.append(f'<hr class="section-break">')
            body.append(f'<a id="{anchor}"></a>')
            remaining = text.strip()

        if remaining:
            body.append(text_to_html_paragraphs(remaining))

    body_parts.append("\n".join(body))

# Build the TOC HTML
toc_html_parts = ['<nav id="toc">', '<h2>Table of Contents</h2>', '<ul>']
prev_level = 0
open_uls = 0

for level, text, anchor in toc_entries:
    if level == 1:
        # Close any open sub-lists
        while open_uls > 0:
            toc_html_parts.append('</ul></li>')
            open_uls -= 1
        toc_html_parts.append(f'<li><a href="#{anchor}"><strong>{escape_html(text)}</strong></a>')
        toc_html_parts.append('<ul>')
        open_uls += 1
    elif level == 2:
        if open_uls == 0:
            toc_html_parts.append('<li><ul>')
            open_uls += 1
        toc_html_parts.append(f'<li><a href="#{anchor}">{escape_html(text)}</a></li>')
    elif level == 3:
        toc_html_parts.append(f'<li><a href="#{anchor}"><em>{escape_html(text)}</em></a></li>')

# Close remaining
while open_uls > 0:
    toc_html_parts.append('</ul></li>')
    open_uls -= 1

toc_html_parts.append('</ul>')
toc_html_parts.append('</nav>')
toc_html = "\n".join(toc_html_parts)

# Assemble the full HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Democracy in America &mdash; Alexis de Tocqueville (Modernized)</title>
<style>
html {{
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}}

body {{
  font: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
  color: #1d1d1d;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}}

h1 {{
  margin: 4em 0 1em;
  text-align: center;
  font-size: 1.8em;
  border-bottom: 2px solid #333;
  padding-bottom: 0.5em;
}}

h2 {{
  margin: 3em 0 1em;
  font-size: 1.4em;
}}

h3 {{
  margin: 2em 0 0.5em;
  font-size: 1.1em;
  color: #444;
}}

p, ul, ol {{
  margin-bottom: 1.5em;
  font-family: sans-serif;
}}

blockquote {{
  margin: 2em 2em;
  padding: 0.5em 1em;
  border-left: 3px solid #ccc;
  font-style: italic;
  color: #444;
}}

blockquote p {{
  margin-bottom: 0.5em;
}}

em {{
  font-style: italic;
}}

hr {{
  border: none;
  border-top: 1px solid #ddd;
  margin: 3em 0;
}}

hr.section-break {{
  border: none;
  text-align: center;
  margin: 2em 0;
}}

hr.section-break::after {{
  content: "\\2022  \\2022  \\2022";
  color: #999;
}}

nav#toc {{
  margin: 2em 0 4em;
}}

nav#toc h2 {{
  text-align: center;
}}

nav#toc ul {{
  list-style: none;
  padding-left: 1.5em;
}}

nav#toc > ul {{
  padding-left: 0;
}}

nav#toc li {{
  margin: 0.3em 0;
}}

nav#toc a {{
  text-decoration: none;
  color: #333;
}}

nav#toc a:hover {{
  text-decoration: underline;
}}

.title-page {{
  text-align: center;
  margin: 4em 0;
}}

.title-page h1 {{
  border-bottom: none;
  font-size: 2.5em;
  margin-bottom: 0.2em;
}}

.title-page .author {{
  font-size: 1.3em;
  margin: 0.5em 0;
}}

.title-page .date {{
  font-size: 1.1em;
  color: #666;
}}

.title-page .note {{
  font-style: italic;
  font-size: 0.9em;
  color: #666;
  margin-top: 2em;
  font-family: sans-serif;
}}

.subtitle {{
  margin-top: -1em;
  color: #555;
  text-align: center;
  font-size: 1.1em;
  border: none;
}}

h1.section-heading {{
  font-size: 1.5em;
  border-bottom: 1px solid #999;
}}

@media (max-width: 600px) {{
  html {{
    padding: 1em 0.5em;
    font-size: 1.1em;
  }}
  blockquote {{
    margin: 1em 0.5em;
  }}
}}
</style>
</head>
<body>

<div class="title-page">
<h1>Democracy in America</h1>
<p class="author">by Alexis de Tocqueville</p>
<p class="date"><s>1835/1840</s> 2026</p>
<p class="note">Translated from the Henry Reeve edition into contemporary English using Claude.</p>
</div>

<hr>

{toc_html}

<hr>

{chr(10).join(body_parts)}

</body>
</html>
"""

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(html, encoding="utf-8")
print(f"Assembled {NUM_CHAPTERS} chapters into {OUT_FILE}")
print(f"TOC entries: {len(toc_entries)}")
print(f"File size: {OUT_FILE.stat().st_size:,} bytes")
