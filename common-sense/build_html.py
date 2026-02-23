#!/usr/bin/env python3
"""Build the Common Sense HTML book from modernized chapter files."""

import re
import os

CHAPTERS_DIR = "/home/alemi/projects/modern-classics/common-sense/modern_chapters"
OUTPUT = "/home/alemi/projects/modern-classics/site/common-sense.html"

def read_chapter(n):
    path = os.path.join(CHAPTERS_DIR, f"{n:03d}.txt")
    with open(path, "r") as f:
        return f.read().strip()

def text_to_paragraphs(text):
    """Convert plain text to HTML paragraphs with formatting."""
    lines = text.split("\n")
    html_parts = []
    current_para = []

    def flush_para():
        if current_para:
            p = " ".join(current_para).strip()
            if p:
                html_parts.append(format_paragraph(p))
            current_para.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            flush_para()
        else:
            current_para.append(stripped)
    flush_para()
    return "\n\n".join(html_parts)

def format_paragraph(text):
    """Apply inline formatting to a paragraph."""
    # Handle indented table-like lines (naval costs etc.)
    if text.strip().startswith("|") or re.match(r'^\s{4,}', text):
        return f'<pre>{text}</pre>'

    # Handle blockquote markers
    if text.startswith("> "):
        inner = apply_inline_formatting(text[2:])
        return f'<blockquote><p>{inner}</p></blockquote>'

    text = apply_inline_formatting(text)
    return f'<p>{text}</p>'

def apply_inline_formatting(text):
    """Apply bold and italic markdown formatting."""
    # Bold: **text**
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    # Italic: _text_ (but not in the middle of words)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<em>\1</em>', text)
    # Italic: *text* (single asterisks)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    return text

def process_section(chapter_num):
    """Process a chapter file into section HTML."""
    text = read_chapter(chapter_num)
    lines = text.split("\n")

    # First line is the section title
    title = lines[0].strip()
    id_text = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

    # Rest is the body
    body_text = "\n".join(lines[1:]).strip()
    body_html = text_to_paragraphs(body_text)

    return title, id_text, body_html

# Section info for TOC
toc_entries = [
    (1, "Introduction"),
    (2, "Of the Origin and Design of Government in General"),
    (3, "Of Monarchy and Hereditary Succession"),
    (4, "Thoughts on the Present State of American Affairs"),
    (5, "Of the Present Ability of America"),
    (6, "Appendix"),
]

# Build HTML
html = []

# Head
html.append("""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>Common Sense &mdash; Thomas Paine</title>
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

p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}

p.footnote {
\tfont-size: 90%;
\ttext-indent: 0%;
\tmargin-left: 10%;
\tmargin-right: 10%;
\tmargin-top: 1em;
\tmargin-bottom: 1em;
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

.epigraph {
  font-style: italic;
  text-align: center;
  margin: 1em 0 2em;
}

pre {
  font-family: "Courier New", monospace;
  font-size: 0.85em;
  overflow-x: auto;
  margin: 1em 0;
  padding: 1em;
  background: #f8f8f8;
}

table {
  border-collapse: collapse;
  margin: 1.5em auto;
  font-family: sans-serif;
  font-size: 0.9em;
}

table th, table td {
  padding: 0.4em 1em;
  text-align: right;
}

table th {
  border-bottom: 2px solid #333;
  text-align: center;
}

table td:first-child {
  text-align: left;
}
</style>
</head>

<body>
""")

# Title page
html.append("""\t<center>
\t<h1>Common Sense</h1>
\t<h3>by Thomas Paine</h3>
\t<p class="center">
\t<s>1776</s> 2026
\t</p>
\t</center>

\t<p class="epigraph">"Man knows no Master save creating Heaven<br>
\tOr those whom choice and common good ordain."<br>
\t&mdash; Thomson</p>

\t<hr>
""")

# Attribution
html.append("""\t<p><i>This is an AI modernization of Common Sense into contemporary English. The original is available on <a href="https://www.gutenberg.org/ebooks/147">Project Gutenberg</a>.</i></p>

\t<hr>
""")

# Table of Contents
html.append('<h2 id="contents">Contents</h2>\n<ul>\n')
for num, title in toc_entries:
    anchor = f"section-{num}"
    html.append(f'<li><a href="#{anchor}">{title}</a></li>\n')
html.append('</ul>\n')
html.append('<hr>\n')

# Chapters 1-6
for ch_num, toc_title in toc_entries:
    title, id_text, body = process_section(ch_num)
    anchor = f"section-{ch_num}"
    html.append(f'\n<h2 id="{anchor}">{title}</h2>\n\n')
    html.append(body)
    html.append('\n')

# Footer
html.append("""
<hr>
<p class="center"><em>F I N I S</em></p>

</body>
</html>
""")

# Write output
with open(OUTPUT, "w") as f:
    f.write("".join(html))

print(f"Written to {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT)} bytes")
