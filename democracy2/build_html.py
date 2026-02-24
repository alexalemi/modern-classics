"""Build the final HTML file from all translated chapters."""

import re
import html
from pathlib import Path

BASE = Path(__file__).parent
MODERN = BASE / "modern_chapters"
MANIFEST = BASE / "chapter_manifest.txt"
OUT = BASE.parent / "site" / "democracy2.html"

# Read manifest for chapter metadata
manifest = {}
for line in MANIFEST.read_text().strip().split('\n'):
    num = line[:3]
    rest = line[5:]
    manifest[num] = rest

# Structure mapping: which chapters belong to which structural sections
# Based on the chapter_manifest.txt labels
STRUCTURE = {
    "volume1_front": ["000"],
    "volume1_preface": ["001"],
    "volume1_intro": ["002"],
    "volume1_tome1": list(f"{i:03d}" for i in range(3, 13)),  # 003-012
    "volume1_tome2_front": ["013"],
    "volume1_tome2": list(f"{i:03d}" for i in range(14, 32)),  # 014-031
    "volume1_conclusion": ["032"],
    "volume2_front": ["033"],
    "volume2_preface": ["034"],
    "volume2_part1": list(f"{i:03d}" for i in range(35, 56)),  # 035-055
    "volume2_part2": list(f"{i:03d}" for i in range(56, 76)),  # 056-075
    "volume2_part3_front": ["076"],
    "volume2_part3": list(f"{i:03d}" for i in range(77, 103)),  # 077-102
    "volume2_part4_front": ["103"],
    "volume2_part4": list(f"{i:03d}" for i in range(104, 112)),  # 104-111
}

def text_to_html(text):
    """Convert plain text to HTML paragraphs."""
    # Escape HTML entities
    text = html.escape(text)

    # Handle [Note: ...] as blockquotes
    text = re.sub(
        r'\[Note:\s*(.*?)\]',
        r'<blockquote><p>\1</p></blockquote>',
        text,
        flags=re.DOTALL
    )

    # Handle italics (text between *...*  or _..._)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', text)

    # Split into paragraphs on double newlines
    paragraphs = re.split(r'\n\s*\n', text.strip())

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check if it's a section heading (ALL CAPS line, short)
        if len(para) < 200 and para == para.upper() and not para.startswith('<'):
            # It's a subsection heading
            heading = para.replace('\n', ' ').strip()
            if heading:
                html_parts.append(f'<h3>{heading}</h3>')
            continue

        # Check if it looks like a section break (dots or asterisks)
        if re.match(r'^[\s*•·\-]+$', para):
            html_parts.append('<hr class="section-break">')
            continue

        # Regular paragraph
        para = para.replace('\n', ' ')
        # Clean up extra spaces
        para = re.sub(r'  +', ' ', para)
        html_parts.append(f'<p>{para}</p>')

    return '\n'.join(html_parts)

def get_chapter_title(num, text):
    """Extract a title from the chapter text or manifest."""
    # Manual titles for split chapters that lack headers
    MANUAL_TITLES = {
        "000": "Front Matter",
        "005": "The Starting Point (continued)",
        "009": "Decentralization in America",
        "013": "Volume One, Part Two",
        "028": "The Black Race (continued): Slavery and Its Abolition",
        "030": "Threats to the Union (continued): The Shifting Balance of Power",
        "033": "Volume Two",
    }
    if num in MANUAL_TITLES:
        return MANUAL_TITLES[num]

    lines = text.strip().split('\n')

    # Phase 1: Skip the "CHAPTER X." line if present
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1  # skip leading blanks

    if i < len(lines) and re.match(r'^(CHAPTER|CHAPITRE)\s+[IVXLC]+', lines[i].strip(), re.IGNORECASE):
        i += 1  # skip the CHAPTER line

    # Phase 2: Skip blank lines after CHAPTER line
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Phase 3: Collect title lines until a blank line
    title_lines = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            break
        # Stop if we hit indented subtitle/summary text
        if lines[i].startswith('     ') and title_lines:
            break
        title_lines.append(line)
        i += 1

    if title_lines:
        title = ' '.join(title_lines)
        title = title.strip(' .-—')
        if title and len(title) < 200:
            return title

    return f"Chapter {num}"

# Collect all chapters
chapters = {}
missing = []
for num in sorted(manifest.keys()):
    path = MODERN / f"{num}.txt"
    if path.exists():
        chapters[num] = path.read_text(encoding='utf-8')
    else:
        missing.append(num)

if missing:
    print(f"WARNING: Missing {len(missing)} chapters: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}")

print(f"Building HTML from {len(chapters)} chapters...")

# Build the HTML
css = """html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}

body {
  font: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
  color: #1d1d1d;
}

h1, h2, h3, h4, h5, h6 {
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1 {
  margin: 4em 0 1em;
  text-align: center;
  font-size: 1.8em;
  border-bottom: 2px solid #333;
  padding-bottom: 0.5em;
}

h2 {
  margin: 3em 0 1em;
  font-size: 1.4em;
}

h3 {
  margin: 2em 0 0.5em;
  font-size: 1.1em;
  color: #444;
}

p, ul, ol {
  margin-bottom: 1.5em;
  font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
}

blockquote {
  margin: 2em 2em;
  padding: 0.5em 1em;
  border-left: 3px solid #ccc;
  font-style: italic;
  color: #444;
}

blockquote p {
  margin-bottom: 0.5em;
}

em {
  font-style: italic;
}

hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 3em 0;
}

hr.section-break {
  border: none;
  text-align: center;
  margin: 2em 0;
}

hr.section-break::after {
  content: "\\2022  \\2022  \\2022";
  color: #999;
}

nav#toc {
  margin: 2em 0 4em;
}

nav#toc h2 {
  text-align: center;
}

nav#toc ul {
  list-style: none;
  padding-left: 1.5em;
}

nav#toc > ul {
  padding-left: 0;
}

nav#toc li {
  margin: 0.3em 0;
}

nav#toc a {
  text-decoration: none;
  color: #333;
}

nav#toc a:hover {
  text-decoration: underline;
}

.title-page {
  text-align: center;
  margin: 4em 0;
}

.title-page h1 {
  border-bottom: none;
  font-size: 2.5em;
  margin-bottom: 0.2em;
}

.title-page .author {
  font-size: 1.3em;
  margin: 0.5em 0;
}

.title-page .date {
  font-size: 1.1em;
  color: #666;
}

.title-page .note {
  font-style: italic;
  font-size: 0.9em;
  color: #666;
  margin-top: 2em;
  font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
}

.subtitle {
  margin-top: -1em;
  color: #555;
  text-align: center;
  font-size: 1.1em;
  border: none;
}

h1.section-heading {
  font-size: 1.5em;
  border-bottom: 1px solid #999;
}

@media (max-width: 600px) {
  html {
    padding: 1em 0.5em;
    font-size: 1.1em;
  }
  blockquote {
    margin: 1em 0.5em;
  }
}"""

# Build TOC and body content
toc_items = []
body_parts = []

# Section headers for the TOC
section_headers = {
    "volume1_preface": ("Preface to the Tenth Edition", "preface"),
    "volume1_intro": ("Introduction", "intro"),
    "volume1_tome1": ("Volume One", "vol1"),
    "volume1_tome2": ("Volume One (continued)", "vol1b"),
    "volume1_conclusion": ("Conclusion", "conclusion"),
    "volume2_preface": ("Preface to Volume Two", "preface2"),
    "volume2_part1": ("Part One: Democracy's Influence on Intellectual Life", "part1"),
    "volume2_part2": ("Part Two: Democracy's Influence on Feelings", "part2"),
    "volume2_part3": ("Part Three: Democracy's Influence on Customs", "part3"),
    "volume2_part4": ("Part Four: Democracy's Influence on Political Society", "part4"),
}

for section_key, (section_title, section_id) in section_headers.items():
    if section_key not in STRUCTURE:
        continue

    nums = STRUCTURE[section_key]
    available = [n for n in nums if n in chapters]
    if not available:
        continue

    toc_items.append(f'<li><a href="#{section_id}"><strong>{section_title}</strong></a>')
    body_parts.append(f'<h1 class="section-heading" id="{section_id}">{section_title}</h1>')

    sub_items = []
    for num in available:
        text = chapters[num]
        title = get_chapter_title(num, text)
        ch_id = f"ch{num}"
        sub_items.append(f'<li><a href="#{ch_id}">{title}</a></li>')
        body_parts.append(f'<div id="{ch_id}">')
        body_parts.append(text_to_html(text))
        body_parts.append('</div>')
        body_parts.append('<hr>')

    if sub_items:
        toc_items.append('<ul>' + '\n'.join(sub_items) + '</ul>')
    toc_items.append('</li>')

toc_html = '\n'.join(toc_items)
body_html = '\n'.join(body_parts)

final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Democracy in America &mdash; Alexis de Tocqueville (From the French)</title>
<style>
{css}
</style>
</head>
<body>

<div class="title-page">
<h1>Democracy in America</h1>
<p class="author">by Alexis de Tocqueville</p>
<p class="date"><s>1835/1840</s> 2026</p>
<p class="note">Translated directly from the original French into contemporary English using Claude. This is a fresh translation from Tocqueville's own words, not a modernization of any existing English version. The French originals are available from Project Gutenberg: <a href="https://www.gutenberg.org/ebooks/30513">Tome 1</a>, <a href="https://www.gutenberg.org/ebooks/30514">Tome 2</a>, <a href="https://www.gutenberg.org/ebooks/30515">Tome 3</a>, <a href="https://www.gutenberg.org/ebooks/30516">Tome 4</a>.</p>
</div>

<hr>

<nav id="toc">
<h2>Table of Contents</h2>
<ul>
{toc_html}
</ul>
</nav>

<hr>

{body_html}

</body>
</html>
"""

OUT.write_text(final_html, encoding='utf-8')
print(f"HTML written to {OUT} ({len(final_html)} chars)")
