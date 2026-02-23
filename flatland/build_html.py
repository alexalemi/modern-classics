#!/usr/bin/env python3
"""Build the Flatland HTML book from modernized chapter files."""

import re
import os

CHAPTERS_DIR = "/home/alemi/projects/modern-classics/flatland/modern_chapters"
IMAGES_DIR = "/home/alemi/projects/modern-classics/flatland/images"
OUTPUT = "/home/alemi/projects/modern-classics/flatland/index.html"

# Map (chapter_num, nth_illustration_in_chapter) -> SVG filename
# Based on Standard Ebooks edition mapping
ILLUSTRATION_MAP = {
    (1, 0): "illustration-1.svg",
    (2, 0): "illustration-2.svg",
    (6, 0): "illustration-3.svg",
    (6, 1): "illustration-4.svg",
    (9, 0): "illustration-5.svg",
    (13, 0): "illustration-6.svg",
    (14, 0): "illustration-7.svg",
    (16, 0): "illustration-8.svg",
    (18, 0): "illustration-9.svg",
    (19, 0): "illustration-10.svg",
}

def read_svg(filename):
    """Read an SVG file and return its contents for inline embedding."""
    path = os.path.join(IMAGES_DIR, filename)
    with open(path, "r") as f:
        content = f.read().strip()
    # Strip XML declaration — not valid inside HTML
    content = re.sub(r'<\?xml[^?]*\?>\s*', '', content)
    return content

# Track which chapter we're processing for illustration mapping
_current_chapter = [0]
_illustration_counter = [0]

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
    return "\n\n".join(p for p in html_parts if p)

def format_paragraph(text):
    """Apply inline formatting to a paragraph."""
    # Handle [Illustration] markers — replace with inline SVGs
    if text.strip() == "[Illustration]":
        ch = _current_chapter[0]
        idx = _illustration_counter[0]
        _illustration_counter[0] += 1
        key = (ch, idx)
        if key in ILLUSTRATION_MAP:
            svg_content = read_svg(ILLUSTRATION_MAP[key])
            return f'<figure class="illustration">\n{svg_content}\n</figure>'
        # No SVG available — skip the placeholder entirely
        return ''

    # Handle dialogue with bold speaker labels like **Sphere.** or **I.**
    # Pattern: **Name.** or **Name** at start of paragraph
    dialogue_bold = re.match(r'^\*\*([^*]+?)\.?\*\*\.?\s*(.*)$', text)
    if dialogue_bold:
        speaker = dialogue_bold.group(1).strip()
        rest = dialogue_bold.group(2).strip()
        rest = apply_inline_formatting(rest)
        return f'<p><strong>{speaker}.</strong> {rest}</p>'

    # Handle dialogue with italic speaker labels like _Stranger_.
    dialogue_italic = re.match(r'^_([^_]+?)_\.?\s+(.*)$', text)
    if dialogue_italic:
        speaker = dialogue_italic.group(1).strip()
        rest = dialogue_italic.group(2).strip()
        rest = apply_inline_formatting(rest)
        return f'<p><em>{speaker}.</em> {rest}</p>'

    # Handle numbered list items
    numbered = re.match(r'^(\d+)\.\s+(.*)$', text)
    if numbered:
        num = numbered.group(1)
        rest = apply_inline_formatting(numbered.group(2))
        return f'<p>{num}. {rest}</p>'

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
    _current_chapter[0] = chapter_num
    _illustration_counter[0] = 0
    text = read_chapter(chapter_num)
    lines = text.split("\n")

    # First line is the section title
    title = lines[0].strip()
    # Remove "Section N:" or "Section N." prefix for the id
    id_text = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

    # Rest is the body
    body_text = "\n".join(lines[1:]).strip()
    body_html = text_to_paragraphs(body_text)

    return title, id_text, body_html

# Section titles from chapter 000 for TOC
toc_entries_part1 = [
    (1, "Section 1 -- The Nature of Flatland"),
    (2, "Section 2 -- Climate and Houses in Flatland"),
    (3, "Section 3 -- The Inhabitants of Flatland"),
    (4, "Section 4 -- The Women"),
    (5, "Section 5 -- How We Recognize One Another"),
    (6, "Section 6 -- Recognition by Sight"),
    (7, "Section 7 -- Irregular Figures"),
    (8, "Section 8 -- The Ancient Practice of Painting"),
    (9, "Section 9 -- The Universal Colour Bill"),
    (10, "Section 10 -- The Suppression of the Chromatic Sedition"),
    (11, "Section 11 -- Our Priests"),
    (12, "Section 12 -- The Doctrine of Our Priests"),
]

toc_entries_part2 = [
    (13, "Section 13 -- How I Had a Vision of Lineland"),
    (14, "Section 14 -- How I Tried and Failed to Explain the Nature of Flatland"),
    (15, "Section 15 -- A Stranger from Spaceland"),
    (16, "Section 16 -- How the Stranger Tried and Failed to Explain the Mysteries of Spaceland in Words"),
    (17, "Section 17 -- How the Sphere, Having Failed with Words, Turned to Action"),
    (18, "Section 18 -- How I Came to Spaceland, and What I Saw There"),
    (19, "Section 19 -- How the Sphere Showed Me Other Mysteries of Spaceland, Yet I Still Wanted More -- and What Came of It"),
    (20, "Section 20 -- How the Sphere Encouraged Me in a Vision"),
    (21, "Section 21 -- How I Tried to Teach the Theory of Three Dimensions to My Grandson, and How That Went"),
    (22, "Section 22 -- How I Then Tried to Spread the Theory of Three Dimensions by Other Means, and What Happened Next"),
]

# Build HTML
html = []

# Head
html.append("""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>Flatland: A Romance of Many Dimensions</title>
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

.dedication {
  text-align: center;
  margin: 3em 0;
  line-height: 2;
}

.part-header {
  text-align: center;
  margin: 4em 0 3em;
}

.part-header h2 {
  margin-bottom: 0.5em;
}

.part-header .epigraph {
  font-style: italic;
  margin-top: 0.5em;
}

.center {
  text-align: center;
}

figure.illustration {
  margin: 2em auto;
  text-align: center;
}

figure.illustration svg {
  max-width: 100%;
  height: auto;
}
</style>
</head>

<body>
""")

# Title page
html.append("""\t<center>
\t<h1>Flatland</h1>
\t<h3>A Romance of Many Dimensions</h3>
\t<h2 class="no-break">by the Author, A SQUARE</h2>
\t<p class="center">
\t<i>"Fie, fie, how frantically I square my talk!"</i>
\t</p>
\t<p class="center">
\t<s>1884</s> 2025
\t</p>
\t</center>
\t<hr>
""")

# Attribution
html.append("""\t<p><i>This is an AI modernization of Flatland into contemporary English. The original is available on <a href="https://www.gutenberg.org/cache/epub/97/pg97-images.html">Project Gutenberg</a>. A beautiful version of the original ebook is available from <a href="https://standardebooks.org/ebooks/edwin-a-abbott/flatland">Standard Ebooks</a>.</i></p>

\t<hr>
""")

# Dedication
html.append("""<div class="dedication">
<p>
To<br>
The Inhabitants of SPACE IN GENERAL<br>
And H.C. IN PARTICULAR<br>
This Work is Dedicated<br>
By a Humble Native of Flatland<br>
In the Hope that<br>
Even as he was Introduced to the Mysteries<br>
Of THREE Dimensions<br>
Having previously known<br>
ONLY TWO<br>
So the Citizens of that Celestial Region<br>
May aspire ever higher and higher<br>
To the Secrets of FOUR FIVE or EVEN SIX Dimensions<br>
Thereby contributing<br>
To the Enlargement of THE IMAGINATION<br>
And the possible Development<br>
Of that most rare and excellent Gift of MODESTY<br>
Among the Superior Races<br>
Of SOLID HUMANITY
</p>
</div>

<hr>
""")

# Table of Contents
html.append('<h2 id="contents">Contents</h2>\n')
html.append('<h3>PART I: THIS WORLD</h3>\n<ul>\n')
for num, title in toc_entries_part1:
    anchor = f"section-{num}"
    html.append(f'<li><a href="#{anchor}">{title}</a></li>\n')
html.append('</ul>\n')

html.append('<h3>PART II: OTHER WORLDS</h3>\n<ul>\n')
for num, title in toc_entries_part2:
    anchor = f"section-{num}"
    html.append(f'<li><a href="#{anchor}">{title}</a></li>\n')
html.append('<li><a href="#preface-second-edition">Preface to the Second and Revised Edition</a></li>\n')
html.append('</ul>\n')

html.append('<hr>\n')

# Part I header
html.append("""
<div class="part-header">
<h2>PART I: THIS WORLD</h2>
<p class="epigraph">"Be patient, for the world is broad and wide."</p>
</div>
""")

# Sections 1-12
for ch in range(1, 13):
    title, id_text, body = process_section(ch)
    anchor = f"section-{ch}"
    html.append(f'\n<h2 id="{anchor}">{title}</h2>\n\n')
    html.append(body)
    html.append('\n')

# Part II header
html.append("""
<div class="part-header">
<h2>PART II: OTHER WORLDS</h2>
<p class="epigraph">"O brave new worlds,<br>That have such people in them!"</p>
</div>
""")

# Sections 13-22
for ch in range(13, 23):
    title, id_text, body = process_section(ch)
    anchor = f"section-{ch}"
    html.append(f'\n<h2 id="{anchor}">{title}</h2>\n\n')
    html.append(body)
    html.append('\n')

# Preface to Second Edition (chapter 23)
text_023 = read_chapter(23)
lines_023 = text_023.split("\n")
title_023 = lines_023[0].strip()
body_023 = "\n".join(lines_023[1:]).strip()
body_023_html = text_to_paragraphs(body_023)

html.append(f'\n<hr>\n\n<h2 id="preface-second-edition">{title_023}</h2>\n\n')
html.append(body_023_html)
html.append('\n')

# Close
html.append("""
</body>
</html>
""")

# Write output
with open(OUTPUT, "w") as f:
    f.write("".join(html))

print(f"Written to {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT)} bytes")
