#!/usr/bin/env python3
"""Assemble modernized chapters into a single HTML book."""

import re
import html
from pathlib import Path

BOOK_DIR = Path(__file__).parent
MODERN_DIR = BOOK_DIR / "modern_chapters"
OUTPUT = Path(__file__).parent.parent / "site" / "wealth-of-nations.html"

# Chapter metadata: (file_numbers, book_label, chapter_label)
# file_numbers is a list of file indices that make up this logical chapter
# book_label triggers a Book heading in the TOC (None = same book as previous)
# chapter_label is the chapter title shown in TOC and as heading
CHAPTERS = [
    ([0], None, "Introduction and Plan of the Work"),
    # Book I: Of the Causes of Improvement in the Productive Powers of Labour
    ([1], "Book I: Of the Causes of Improvement in the Productive Powers of Labor", "Chapter I: Of the Division of Labor"),
    ([2], None, "Chapter II: Of the Principle Which Gives Occasion to the Division of Labor"),
    ([3], None, "Chapter III: That the Division of Labor Is Limited by the Extent of the Market"),
    ([4], None, "Chapter IV: Of the Origin and Use of Money"),
    ([5], None, "Chapter V: Of the Real and Nominal Price of Commodities"),
    ([6], None, "Chapter VI: Of the Component Parts of the Price of Commodities"),
    ([7], None, "Chapter VII: Of the Natural and Market Price of Commodities"),
    ([8], None, "Chapter VIII: Of the Wages of Labor"),
    ([9], None, "Chapter IX: Of the Profits of Stock"),
    ([10, 11], None, "Chapter X: Of Wages and Profit in the Different Employments of Labor and Stock"),
    ([12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], None, "Chapter XI: Of the Rent of Land"),
    # Book II: Of the Nature, Accumulation, and Employment of Stock
    ([24], "Book II: Of the Nature, Accumulation, and Employment of Capital", "Introduction"),
    ([25], None, "Chapter I: Of the Division of Stock"),
    ([26, 27], None, "Chapter II: Of Money Considered as a Particular Branch of the General Stock of the Society"),
    ([28], None, "Chapter III: Of the Accumulation of Capital, or of Productive and Unproductive Labor"),
    ([29], None, "Chapter IV: Of Stock Lent at Interest"),
    ([30], None, "Chapter V: Of the Different Employment of Capitals"),
    # Book III: Of the Different Progress of Opulence in Different Nations
    ([31], "Book III: Of the Different Progress of Opulence in Different Nations", "Chapter I: Of the Natural Progress of Opulence"),
    ([32], None, "Chapter II: Of the Discouragement of Agriculture in the Ancient State of Europe After the Fall of the Roman Empire"),
    ([33], None, "Chapter III: Of the Rise and Progress of Cities and Towns, After the Fall of the Roman Empire"),
    ([34], None, "Chapter IV: How the Commerce of the Towns Contributed to the Improvement of the Country"),
    # Book IV: Of Systems of Political Economy
    ([35], "Book IV: Of Systems of Political Economy", "Introduction"),
    ([36, 37], None, "Chapter I: Of the Principle of the Commercial or Mercantile System"),
    ([38], None, "Chapter II: Of Restraints upon the Importation from Foreign Countries"),
    ([39, 40], None, "Chapter III: Of the Extraordinary Restraints upon Importation"),
    ([41], None, "Chapter IV: Of Drawbacks"),
    ([42, 43], None, "Chapter V: Of Bounties"),
    ([44], None, "Chapter VI: Of Treaties of Commerce"),
    ([45, 46, 47, 48], None, "Chapter VII: Of Colonies"),
    ([49, 50, 51], None, "Chapter VIII: Conclusion of the Mercantile System"),
    ([52, 53], None, "Chapter IX: Of the Agricultural Systems"),
    # Book V: Of the Revenue of the Sovereign or Commonwealth
    ([54, 55, 56, 57, 58, 59, 60, 61, 62, 63], "Book V: Of the Revenue of the Sovereign or Commonwealth", "Chapter I: Of the Expenses of the Sovereign or Commonwealth"),
    ([64, 65, 66, 67, 68, 69, 70], None, "Chapter II: Of the Sources of the General or Public Revenue of the Society"),
    ([71, 72], None, "Chapter III: Of Public Debts"),
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


def strip_chapter_header(text):
    """Remove the chapter title and subtitle lines from the beginning of text."""
    lines = text.strip().split("\n")
    i = 0
    # Skip the first title line (e.g., "The Wealth of Nations — Introduction...")
    if i < len(lines) and lines[i].strip():
        i += 1
    # Skip === underline if present
    if i < len(lines) and re.match(r'^=+$', lines[i].strip()):
        i += 1
    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1
    # Skip subtitle or section heading line (e.g., "Introduction and Plan of the Work")
    if i < len(lines) and lines[i].strip():
        candidate = lines[i].strip()
        if len(candidate) < 120 and not candidate.endswith('.'):
            i += 1
    # Skip blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    return "\n".join(lines[i:])


def build_toc(chapters):
    """Build table of contents HTML."""
    toc = ['<nav id="toc">', '<h2>Table of Contents</h2>', '<ul>']
    current_book = None

    for file_nums, book_label, ch_label in chapters:
        anchor = f"ch{file_nums[0]:03d}"

        if book_label and book_label != current_book:
            if current_book is not None:
                toc.append('</ul></li>')
            current_book = book_label
            toc.append(f'<li><a href="#{anchor}">{html.escape(book_label)}</a>')
            toc.append('<ul>')
            toc.append(f'<li><a href="#{anchor}">{html.escape(ch_label)}</a></li>')
        elif book_label is None and current_book:
            toc.append(f'<li><a href="#{anchor}">{html.escape(ch_label)}</a></li>')
        else:
            toc.append(f'<li><a href="#{anchor}">{html.escape(ch_label)}</a></li>')

    if current_book:
        toc.append('</ul></li>')
    toc.append('</ul>')
    toc.append('</nav>')
    return "\n".join(toc)


def main():
    all_chapters_html = []

    for file_nums, book_label, ch_label in CHAPTERS:
        # Combine all sub-chapter files for this logical chapter
        combined_text_parts = []
        for num in file_nums:
            filepath = MODERN_DIR / f"{num:03d}.txt"
            if not filepath.exists():
                print(f"WARNING: {filepath} not found, skipping")
                continue
            raw_text = extract_modernized_text(filepath)
            combined_text_parts.append(raw_text)

        if not combined_text_parts:
            continue

        # Strip header from first part, keep rest as-is
        first_part = strip_chapter_header(combined_text_parts[0])
        rest_parts = [strip_chapter_header(p) for p in combined_text_parts[1:]]

        all_text = "\n\n".join([first_part] + rest_parts)
        body_html = text_to_html_paragraphs(all_text)

        chapter_html = []
        anchor = f"ch{file_nums[0]:03d}"

        # Add book header if this is the first chapter in a new book
        if book_label:
            chapter_html.append(f'<h1 id="{anchor}">{html.escape(book_label)}</h1>')

        # Add chapter heading
        if book_label:
            chapter_html.append(f'<h2>{html.escape(ch_label)}</h2>')
        else:
            chapter_html.append(f'<h2 id="{anchor}">{html.escape(ch_label)}</h2>')

        chapter_html.append(body_html)
        all_chapters_html.append("\n".join(chapter_html))

    toc = build_toc(CHAPTERS)
    chapters_combined = "\n\n<hr>\n\n".join(all_chapters_html)

    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Wealth of Nations &mdash; Adam Smith (Modernized)</title>
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
<h1>The Wealth of Nations</h1>
<p class="author">by Adam Smith</p>
<p class="date"><s>1776</s> 2026</p>
<p class="note">An inquiry into the nature and causes of the wealth of nations.</p>
<p class="note">Modernized into contemporary English using Claude.</p>
</div>

<hr>

{toc}

<hr>

{chapters_combined}

<hr>

<p style="text-align: center; font-style: italic; color: #666; font-family: sans-serif; margin: 4em 0;">
This modernized edition was produced using Claude by Anthropic, following the original 1776 text from Standard Ebooks. The original work is in the public domain.
</p>

</body>
</html>"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(final_html, encoding="utf-8")
    print(f"Assembled {len(CHAPTERS)} chapters into {OUTPUT}")
    print(f"File size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
