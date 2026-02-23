#!/usr/bin/env python3
"""Assemble modernized chapters into a single HTML book."""

import re
import html
from pathlib import Path

BOOK_DIR = Path(__file__).parent
MODERN_DIR = BOOK_DIR / "modern_chapters"
OUTPUT = BOOK_DIR / "progress-and-poverty.html"

# Chapter metadata: (file_number, book_label, chapter_label)
# book_label is used for grouping in the TOC
CHAPTERS = [
    (0, None, "Preface"),
    (1, "Introductory", "The Problem"),
    # Book I: Wages and Capital
    (2, "Book I: Wages and Capital", "The Current Doctrine — That Wages Are Drawn from Capital"),
    (3, None, "The Meaning of the Terms"),
    (4, None, "Wages Not Drawn from Capital, but Produced by the Labor"),
    (5, None, "The Maintenance of Laborers Not Drawn from Capital"),
    (6, None, "The Real Functions of Capital"),
    # Book II: Population and Subsistence
    (7, "Book II: Population and Subsistence", "The Malthusian Theory, Its Genesis and Support"),
    (8, None, "Inferences from Facts"),
    (9, None, "Inferences from Analogy"),
    (10, None, "Disproof of the Malthusian Theory"),
    # Book III: The Laws of Distribution
    (11, "Book III: The Laws of Distribution", "The Inquiry Narrowed to the Laws of Distribution"),
    (12, None, "Rent and the Law of Rent"),
    (13, None, "Interest and the Cause of Interest"),
    (14, None, "Of Spurious Capital and of Profits Often Mistaken for Interest"),
    (15, None, "The Law of Interest"),
    (16, None, "Wages and the Law of Wages"),
    (17, None, "Correlation and Coördination of These Laws"),
    (18, None, "The Statics of the Problem Thus Explained"),
    # Book IV: Effect of Material Progress upon the Distribution of Wealth
    (19, "Book IV: Effect of Material Progress upon the Distribution of Wealth", "The Dynamics of the Problem Yet to Seek"),
    (20, None, "Effect of Increase of Population upon the Distribution of Wealth"),
    (21, None, "Effect of Improvements in the Arts upon the Distribution of Wealth"),
    (22, None, "Effect of the Expectation Raised by Material Progress"),
    # Book V: The Problem Solved
    (23, "Book V: The Problem Solved", "The Primary Cause of Recurring Paroxysms of Industrial Depression"),
    (24, None, "The Persistence of Poverty amid Advancing Wealth"),
    # Book VI: The Remedy
    (25, "Book VI: The Remedy", "Insufficiency of Remedies Currently Advocated"),
    (26, None, "The True Remedy"),
    # Book VII: Justice of the Remedy
    (27, "Book VII: Justice of the Remedy", "Injustice of Private Property in Land"),
    (28, None, "Enslavement of Laborers the Ultimate Result of Private Property in Land"),
    (29, None, "Claim of Landowners to Compensation"),
    (30, None, "Property in Land Historically Considered"),
    (31, None, "Of Property in Land in the United States"),
    # Book VIII: Application of the Remedy
    (32, "Book VIII: Application of the Remedy", "Private Ownership of Land Inconsistent with the Best Use of Land"),
    (33, None, "How Equal Rights to the Land May Be Asserted and Secured"),
    (34, None, "The Proposition Tried by the Canons of Taxation"),
    (35, None, "Endorsements and Objections"),
    # Book IX: Effects of the Remedy
    (36, "Book IX: Effects of the Remedy", "Of the Effect upon the Production of Wealth"),
    (37, None, "Of the Effect upon Distribution and Thence upon Production"),
    (38, None, "Of the Effect upon Individuals and Classes"),
    (39, None, "Of Changes in Social Life and Development"),
    # Book X: The Law of Human Progress
    (40, "Book X: The Law of Human Progress", "The Current Theory of Human Progress — Its Insufficiency"),
    (41, None, "Differences in Civilization — To What Due"),
    (42, None, "The Law of Human Progress"),
    (43, None, "How Modern Civilization May Decline"),
    (44, None, "The Central Truth"),
    # Conclusion
    (45, "Conclusion", "The Problem of Individual Life"),
]


def extract_modernized_text(filepath):
    """Extract text between <modernized_text> and </modernized_text> tags."""
    text = filepath.read_text(encoding="utf-8")
    match = re.search(r"<modernized_text>\s*(.*?)\s*</modernized_text>", text, re.DOTALL)
    if not match:
        print(f"WARNING: No <modernized_text> tag found in {filepath}")
        return text
    return match.group(1).strip()


def text_to_html_paragraphs(text):
    """Convert plain text with blank-line-separated paragraphs to HTML."""
    lines = text.split("\n")
    blocks = []
    current = []

    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Skip chapter titles that duplicate the heading (first 1-3 lines often repeat)
        # We'll handle this in the caller

        # Handle horizontal rules
        if block.strip() in ("* * *", "---", "***"):
            html_parts.append('<hr class="section-break">')
            continue

        # Handle blockquotes (indented blocks or blocks starting with ")
        if block.startswith('"') and block.endswith('"') and len(block) > 200:
            escaped = html.escape(block)
            escaped = process_inline_formatting(escaped)
            html_parts.append(f'<blockquote><p>{escaped}</p></blockquote>')
            continue

        # Handle bold section headers like **Header Text**
        if re.match(r'^\*\*[^*]+\*\*$', block.strip()):
            header_text = block.strip().strip('*')
            html_parts.append(f'<h3>{html.escape(header_text)}</h3>')
            continue

        # Regular paragraph
        escaped = html.escape(block)
        escaped = process_inline_formatting(escaped)
        html_parts.append(f"<p>{escaped}</p>")

    return "\n\n".join(html_parts)


def process_inline_formatting(text):
    """Handle inline markdown-style formatting."""
    # Bold: **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Italic: *text*
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Em dashes
    text = text.replace(" -- ", " &mdash; ")
    text = text.replace("--", "&mdash;")
    return text


def get_chapter_title_from_text(text):
    """Extract the chapter title from the first few lines of text."""
    lines = text.strip().split("\n")
    # First non-empty line is typically the full title
    for line in lines:
        line = line.strip()
        if line and not line.startswith("="):
            return line
    return ""


def strip_chapter_header(text):
    """Remove the chapter title and subtitle lines from the beginning of text."""
    lines = text.strip().split("\n")
    # Skip initial title lines (often 2-6 lines of headers)
    # Pattern: Title line, === underline, blank, Roman numeral, blank, subtitle, blank
    i = 0
    # Skip the first title line
    if i < len(lines) and lines[i].strip():
        i += 1
    # Skip === underline if present
    if i < len(lines) and re.match(r'^=+$', lines[i].strip()):
        i += 1
    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1
    # Skip Roman numeral line (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
    if i < len(lines) and re.match(r'^[IVXLC]+$', lines[i].strip()):
        i += 1
    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1
    # Skip subtitle line (often repeats the title)
    if i < len(lines) and lines[i].strip():
        # Check if it looks like a subtitle (short, no punctuation at end)
        candidate = lines[i].strip()
        if len(candidate) < 100 and not candidate.endswith('.'):
            i += 1
    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    return "\n".join(lines[i:])


def build_toc(chapters):
    """Build table of contents HTML."""
    toc = ['<nav id="toc">', '<h2>Table of Contents</h2>', '<ul>']
    current_book = None
    for num, book_label, ch_label in chapters:
        if book_label and book_label != current_book:
            if current_book is not None:
                toc.append('</ul></li>')
            current_book = book_label
            toc.append(f'<li><a href="#ch{num:03d}">{html.escape(book_label)}</a>')
            toc.append('<ul>')
            if book_label in ("Introductory", "Conclusion"):
                toc.append(f'<li><a href="#ch{num:03d}">{html.escape(ch_label)}</a></li>')
            else:
                toc.append(f'<li><a href="#ch{num:03d}">{html.escape(ch_label)}</a></li>')
        elif book_label is None and current_book:
            toc.append(f'<li><a href="#ch{num:03d}">{html.escape(ch_label)}</a></li>')
        else:
            toc.append(f'<li><a href="#ch{num:03d}">{html.escape(ch_label)}</a></li>')
    if current_book:
        toc.append('</ul></li>')
    toc.append('</ul>')
    toc.append('</nav>')
    return "\n".join(toc)


def main():
    all_chapters_html = []

    for num, book_label, ch_label in CHAPTERS:
        filepath = MODERN_DIR / f"{num:03d}.txt"
        if not filepath.exists():
            print(f"WARNING: {filepath} not found, skipping")
            continue

        raw_text = extract_modernized_text(filepath)
        body_text = strip_chapter_header(raw_text)
        body_html = text_to_html_paragraphs(body_text)

        chapter_html = []

        # Add book header if this is the first chapter in a new book
        if book_label:
            if book_label in ("Introductory", "Conclusion"):
                chapter_html.append(f'<h1 id="ch{num:03d}">{html.escape(book_label)}</h1>')
            else:
                chapter_html.append(f'<h1 id="ch{num:03d}">{html.escape(book_label)}</h1>')

        # Add chapter heading
        if book_label and book_label in ("Introductory", "Conclusion"):
            chapter_html.append(f'<h2>{html.escape(ch_label)}</h2>')
        elif num == 0:
            chapter_html.append(f'<h2 id="ch{num:03d}">{html.escape(ch_label)}</h2>')
        else:
            chapter_html.append(f'<h2 id="ch{num:03d}">{html.escape(ch_label)}</h2>')

        chapter_html.append(body_html)
        all_chapters_html.append("\n".join(chapter_html))

    toc = build_toc(CHAPTERS)
    chapters_combined = "\n\n<hr>\n\n".join(all_chapters_html)

    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Progress and Poverty &mdash; Henry George (Modernized)</title>
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
<h1>Progress and Poverty</h1>
<p class="author">by Henry George</p>
<p class="date"><s>1879</s> 2026</p>
<p class="note">An inquiry into the cause of industrial depressions and of increase of want with increase of wealth &mdash; the remedy.</p>
<p class="note">Modernized into contemporary English using Claude.</p>
</div>

<hr>

{toc}

<hr>

{chapters_combined}

<hr>

<p style="text-align: center; font-style: italic; color: #666; font-family: sans-serif; margin: 4em 0;">
This modernized edition was produced using Claude by Anthropic, following the original 1879 text from Standard Ebooks. The original work is in the public domain.
</p>

</body>
</html>"""

    OUTPUT.write_text(final_html, encoding="utf-8")
    print(f"Assembled {len(CHAPTERS)} chapters into {OUTPUT}")
    print(f"File size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
