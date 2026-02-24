#!/usr/bin/env python3
"""Build the Herodotus Histories HTML book from modernized chapter files."""

import re
import os

CHAPTERS_DIR = "/home/alemi/projects/modern-classics/herodotus/modern_chapters"
OUTPUT = "/home/alemi/projects/modern-classics/site/herodotus.html"

# Book structure: (book_num, muse_name, [(chapter_num, title), ...])
# 25 chapters total (000-024), mapped to 9 books
BOOKS = [
    (1, "Clio", [
        (0, "The Rise of Croesus"),
        (1, "The Fall of Croesus"),
        (2, "Lydian Marvels and the Rise of Cyrus"),
        (3, "The Conquests and Death of Cyrus"),
    ]),
    (2, "Euterpe", [
        (4, "Egypt: The Land and the Nile"),
        (5, "Egyptian Customs, Religion, and Sacred Animals"),
        (6, "Egyptian History and Marvels"),
    ]),
    (3, "Thalia", [
        (7, "Cambyses Invades Egypt"),
        (8, "The Fall of the Magi and the Rise of Darius"),
        (9, "Darius' Empire and the Fall of Babylon"),
    ]),
    (4, "Melpomene", [
        (10, "Scythia: The People"),
        (11, "Scythian Customs and Neighbors"),
        (12, "Darius in Scythia and Libya"),
    ]),
    (5, "Terpsichore", [
        (13, "The Ionian Revolt Begins"),
        (14, "Athens Rises, Sardis Burns"),
    ]),
    (6, "Erato", [
        (15, "The Fall of the Ionians"),
        (16, "Marathon"),
    ]),
    (7, "Polymnia", [
        (17, "Xerxes Prepares"),
        (18, "The March"),
        (19, "Greece Responds"),
        (20, "Thermopylae"),
    ]),
    (8, "Urania", [
        (21, "Artemisium and Salamis"),
        (22, "The Battle of Salamis"),
    ]),
    (9, "Calliope", [
        (23, "Plataea"),
        (24, "Plataea and the End"),
    ]),
]


def read_chapter(n):
    path = os.path.join(CHAPTERS_DIR, f"{n:03d}.txt")
    with open(path, "r") as f:
        return f.read().strip()


def apply_inline_formatting(text):
    """Apply bold and italic markdown formatting."""
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    return text


def format_paragraph(text):
    """Convert a plain text paragraph to HTML."""
    if text.startswith("> "):
        inner = apply_inline_formatting(text[2:])
        return f'<blockquote><p>{inner}</p></blockquote>'
    text = apply_inline_formatting(text)
    return f'<p>{text}</p>'


def text_to_html(text):
    """Convert plain text with blank-line-separated paragraphs to HTML."""
    lines = text.split("\n")
    html_parts = []
    current_para = []

    def flush():
        if current_para:
            p = " ".join(current_para).strip()
            if p:
                html_parts.append(format_paragraph(p))
            current_para.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            flush()
        else:
            current_para.append(stripped)
    flush()
    return "\n\n".join(html_parts)


def get_chapter_body(chapter_num):
    """Read a chapter file and strip the header line."""
    text = read_chapter(chapter_num)
    lines = text.split("\n")

    # Skip initial title/header lines until substantive content
    body_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "":
            continue
        # Skip lines that look like chapter headers
        if re.match(r'^Book [IVX]+', stripped, re.IGNORECASE):
            continue
        if stripped.startswith("---") or stripped.startswith("==="):
            continue
        body_start = i
        break

    return "\n".join(lines[body_start:]).strip()


def roman(n):
    """Convert integer to Roman numeral."""
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
            (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
            (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for val, sym in vals:
        while n >= val:
            result += sym
            n -= val
    return result


# Build HTML
html = []

html.append("""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>The Histories &mdash; Herodotus</title>
<style>
html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}

body {
\tfont: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1,h2,h3,h4,h5,h6 {
  margin: 3em 0 1em;
\tfont-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1 {
  margin-top: 1em;
  text-align: center;
}

h2 {
  text-align: center;
}

h3 {
  margin: 2em 0 0.5em;
}

p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}

blockquote {
  margin: 1.5em 2em;
  padding-left: 1em;
  border-left: 3px solid #ccc;
  font-style: italic;
}

blockquote p {
  margin-bottom: 1em;
}

.center {
  text-align: center;
}

.subtitle {
  text-align: center;
  font-style: italic;
  margin-top: -1em;
  margin-bottom: 3em;
}

.muse-name {
  text-align: center;
  font-style: italic;
  font-size: 0.9em;
  color: #666;
  margin-top: -2em;
  margin-bottom: 2em;
  font-family: sans-serif;
}

.toc-group {
  font-weight: bold;
  margin-top: 1.5em;
  margin-bottom: 0.3em;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

.toc-list {
  list-style: none;
  padding-left: 1.5em;
  margin-top: 0.3em;
}

.toc-list li {
  margin-bottom: 0.3em;
}

pre {
  font-family: "Courier New", monospace;
  font-size: 0.85em;
  overflow-x: auto;
  margin: 1em 0;
  padding: 1em;
  background: #f8f8f8;
}
</style>
</head>

<body>
""")

# Title page
html.append("""\t<center>
\t<h1>The Histories</h1>
\t<h3>by Herodotus</h3>
\t<p class="center">
\tTranslated by G.C. Macaulay<br>
\t<s>c. 430 BC</s> 2026
\t</p>
\t</center>

\t<hr>
""")

# Attribution
html.append("""\t<p><i>This is an AI modernization of Herodotus' Histories (from the G.C. Macaulay translation, 1890) into contemporary English. The original is available from <a href="https://www.gutenberg.org/ebooks/2707">Project Gutenberg</a> (Vol. 1) and <a href="https://www.gutenberg.org/ebooks/2456">Project Gutenberg</a> (Vol. 2).</i></p>

\t<hr>
""")

# Table of Contents
html.append('<h2 id="contents">Contents</h2>\n')

for book_num, muse_name, chapters in BOOKS:
    book_id = f"book-{book_num}"
    html.append(f'<p class="toc-group">Book {roman(book_num)}: {muse_name}</p>\n')
    html.append('<ul class="toc-list">\n')
    for ch_num, ch_title in chapters:
        anchor = f"ch-{ch_num:03d}"
        html.append(f'<li><a href="#{anchor}">{ch_title}</a></li>\n')
    html.append('</ul>\n')

html.append('<hr>\n')

# Each book and its chapters
for book_num, muse_name, chapters in BOOKS:
    book_id = f"book-{book_num}"
    html.append(f'\n<h2 id="{book_id}">Book {roman(book_num)}: {muse_name}</h2>\n')

    for ch_num, ch_title in chapters:
        anchor = f"ch-{ch_num:03d}"
        html.append(f'\n<h3 id="{anchor}">{ch_title}</h3>\n\n')

        body = get_chapter_body(ch_num)
        html.append(text_to_html(body))
        html.append('\n')

    html.append('<hr>\n')

# Footer
html.append("""
<p class="center"><em>F I N I S</em></p>

</body>
</html>
""")

with open(OUTPUT, "w") as f:
    f.write("".join(html))

print(f"Written to {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT):,} bytes")
