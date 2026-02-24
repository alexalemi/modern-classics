#!/usr/bin/env python3
"""Build the Two Treatises of Government HTML book from modernized chapter files."""

import re
import os

CHAPTERS_DIR = "/home/alemi/projects/modern-classics/two-treatises/modern_chapters"
OUTPUT = "/home/alemi/projects/modern-classics/site/two-treatises.html"

# Chapter metadata: (file_num, book, chapter_num, title)
CHAPTERS = [
    (0, None, None, "Preface"),
    # Book I
    (1, "I", 1, None),
    (2, "I", 2, "Of Paternal and Regal Power"),
    (3, "I", 3, "Of Adam's Title to Sovereignty by Creation"),
    (4, "I", 4, "Of Adam's Title to Sovereignty, by Donation, Gen. 1:28"),
    (5, "I", 5, "Of Adam's Title to Sovereignty, by the Subjection of Eve"),
    (6, "I", 6, "Of Adam's Title to Sovereignty by Fatherhood"),
    (7, "I", 7, "Of Fatherhood and Property Considered Together as Fountains of Sovereignty"),
    (8, "I", 8, "Of the Conveyance of Adam's Sovereign Monarchical Power"),
    (9, "I", 9, "Of Monarchy, by Inheritance from Adam"),
    (10, "I", 10, "Of the Heir to Adam's Monarchical Power"),
    (11, "I", 11, "Who Heir?"),
    # Book II
    (12, "II", 1, None),
    (13, "II", 2, "Of the State of Nature"),
    (14, "II", 3, "Of the State of War"),
    (15, "II", 4, "Of Slavery"),
    (16, "II", 5, "Of Property"),
    (17, "II", 6, "Of Paternal Power"),
    (18, "II", 7, "Of Political or Civil Society"),
    (19, "II", 8, "Of the Beginning of Political Societies"),
    (20, "II", 9, "Of the Ends of Political Society and Government"),
    (21, "II", 10, "Of the Forms of a Commonwealth"),
    (22, "II", 11, "Of the Extent of the Legislative Power"),
    (23, "II", 12, "Of the Legislative, Executive, and Federative Power"),
    (24, "II", 13, "Of the Subordination of the Powers of the Commonwealth"),
    (25, "II", 14, "Of Prerogative"),
    (26, "II", 15, "Of Paternal, Political, and Despotical Power, Considered Together"),
    (27, "II", 16, "Of Conquest"),
    (28, "II", 17, "Of Usurpation"),
    (29, "II", 18, "Of Tyranny"),
    (30, "II", 19, "Of the Dissolution of Government"),
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


def get_chapter_body(file_num):
    """Read a chapter, strip the first few title/header lines, return body text."""
    text = read_chapter(file_num)
    lines = text.split("\n")

    # Skip initial title/header lines (chapter numbers, titles, blank lines)
    # until we hit the first substantive paragraph
    body_start = 0
    found_content = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not found_content:
            # Skip lines that are chapter numbers, titles, or blank
            if stripped == "":
                continue
            # Skip lines that look like headers (all caps, roman numerals, "CHAPTER X", etc.)
            if re.match(r'^(BOOK\s+[IV]+|CHAPTER\s+[IVXLCDM]+|[IVXLCDM]+)$', stripped, re.IGNORECASE):
                continue
            if re.match(r'^Chapter\s+\d+:', stripped):
                continue
            # Skip subtitle lines (the chapter title line after the number)
            if re.match(r'^Of\s+', stripped) and i < 5:
                continue
            if re.match(r'^Who Heir\??$', stripped, re.IGNORECASE):
                continue
            # This is the start of actual content
            body_start = i
            found_content = True
            break

    body = "\n".join(lines[body_start:]).strip()
    return body


def make_anchor(book, chapter_num, title):
    if book is None:
        return "preface"
    if title:
        s = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        return f"book-{book.lower()}-ch-{chapter_num}"
    return f"book-{book.lower()}-ch-{chapter_num}"


def make_heading(book, chapter_num, title):
    if book is None and title == "Preface":
        return "Preface"
    parts = []
    if chapter_num:
        parts.append(f"Chapter {chapter_num}")
    if title:
        if parts:
            parts.append(f": {title}")
        else:
            parts.append(title)
    return "".join(parts) if parts else f"Chapter {chapter_num}"


# Build HTML
html = []

html.append("""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>Two Treatises of Government &mdash; John Locke</title>
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

.toc-book {
  font-weight: bold;
  margin-top: 1em;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

.toc-list {
  list-style: none;
  padding-left: 1.5em;
}

.toc-list li {
  margin-bottom: 0.3em;
}
</style>
</head>

<body>
""")

# Title page
html.append("""\t<center>
\t<h1>Two Treatises of Government</h1>
\t<h3>by John Locke</h3>
\t<p class="center">
\t<s>1689</s> 2026
\t</p>
\t</center>

\t<hr>
""")

# Attribution
html.append("""\t<p><i>This is an AI modernization of Two Treatises of Government into contemporary English. The original is available from <a href="https://standardebooks.org/ebooks/john-locke/two-treatises-of-government">Standard Ebooks</a>.</i></p>

\t<hr>
""")

# Table of Contents
html.append('<h2 id="contents">Contents</h2>\n')
html.append('<p><a href="#preface">Preface</a></p>\n')

# Book I TOC
html.append('<p class="toc-book">Book I: Of Government</p>\n')
html.append('<ul class="toc-list">\n')
for file_num, book, ch_num, title in CHAPTERS:
    if book != "I":
        continue
    anchor = make_anchor(book, ch_num, title)
    heading = make_heading(book, ch_num, title)
    html.append(f'<li><a href="#{anchor}">{heading}</a></li>\n')
html.append('</ul>\n')

# Book II TOC
html.append('<p class="toc-book">Book II: Of Civil Government</p>\n')
html.append('<ul class="toc-list">\n')
for file_num, book, ch_num, title in CHAPTERS:
    if book != "II":
        continue
    anchor = make_anchor(book, ch_num, title)
    heading = make_heading(book, ch_num, title)
    html.append(f'<li><a href="#{anchor}">{heading}</a></li>\n')
html.append('</ul>\n')

html.append('<hr>\n')

# Preface
html.append('\n<h2 id="preface">Preface</h2>\n\n')
body = get_chapter_body(0)
html.append(text_to_html(body))
html.append('\n<hr>\n')

# Book I
html.append('\n<h2 id="book-i" class="center">Book I: Of Government</h2>\n')
for file_num, book, ch_num, title in CHAPTERS:
    if book != "I":
        continue
    anchor = make_anchor(book, ch_num, title)
    heading = make_heading(book, ch_num, title)
    html.append(f'\n<h3 id="{anchor}">{heading}</h3>\n\n')
    body = get_chapter_body(file_num)
    html.append(text_to_html(body))
    html.append('\n')

html.append('<hr>\n')

# Book II
html.append('\n<h2 id="book-ii" class="center">Book II: Of Civil Government</h2>\n')
for file_num, book, ch_num, title in CHAPTERS:
    if book != "II":
        continue
    anchor = make_anchor(book, ch_num, title)
    heading = make_heading(book, ch_num, title)
    html.append(f'\n<h3 id="{anchor}">{heading}</h3>\n\n')
    body = get_chapter_body(file_num)
    html.append(text_to_html(body))
    html.append('\n')

# Footer
html.append("""
<hr>
<p class="center"><em>F I N I S</em></p>

</body>
</html>
""")

with open(OUTPUT, "w") as f:
    f.write("".join(html))

print(f"Written to {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT):,} bytes")
