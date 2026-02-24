"""Assemble all modernized chapters into a single HTML file."""

import re
from pathlib import Path

CHAPTERS_DIR = Path(__file__).parent / "modern_chapters"
OUTPUT = Path(__file__).parent.parent / "site" / "origin-of-species.html"

CHAPTER_META = [
    ("000", "Historical Sketch", "historical-sketch"),
    ("001", "Introduction", "introduction"),
    ("002", "Chapter I: Variation Under Domestication", "chapter-1"),
    ("003", "Chapter II: Variation Under Nature", "chapter-2"),
    ("004", "Chapter III: Struggle for Existence", "chapter-3"),
    ("005", "Chapter IV: Natural Selection; or the Survival of the Fittest", "chapter-4"),
    ("006", "Chapter V: Laws of Variation", "chapter-5"),
    ("007", "Chapter VI: Difficulties of the Theory", "chapter-6"),
    ("008", "Chapter VII: Miscellaneous Objections to the Theory of Natural Selection", "chapter-7"),
    ("009", "Chapter VIII: Instinct", "chapter-8"),
    ("010", "Chapter IX: Hybridism", "chapter-9"),
    ("011", "Chapter X: On the Imperfection of the Geological Record", "chapter-10"),
    ("012", "Chapter XI: On the Geological Succession of Organic Beings", "chapter-11"),
    ("013", "Chapter XII: Geographical Distribution", "chapter-12"),
    ("014", "Chapter XIII: Geographical Distribution (Continued)", "chapter-13"),
    ("015", "Chapter XIV: Mutual Affinities of Organic Beings", "chapter-14"),
    ("016", "Chapter XV: Recapitulation and Conclusion", "chapter-15"),
    ("017", "Glossary", "glossary"),
]

def text_to_html(text, is_glossary=False):
    """Convert plain text to HTML paragraphs, detecting section headings."""
    lines = text.strip().split('\n')
    html_parts = []
    i = 0

    # Skip the first few lines if they're just the chapter title repeated
    # (our extraction sometimes duplicates the heading)
    while i < len(lines) and lines[i].strip() == '':
        i += 1

    # Check if first non-empty line looks like a chapter title we already have in h2
    first_line = lines[i].strip() if i < len(lines) else ''

    # Skip lines that are just the chapter number/title duplicated at top
    skip_patterns = [
        r'^(Chapter\s+)?[IVXLC]+:?\s',
        r'^[IVXLC]+$',
        r'^Introduction$',
        r'^Glossary$',
        r'^A Historical Sketch',
        r'^Historical Sketch',
        r'^Recapitulation',
        r'^Mutual Affinities',
        r'^Geographical Distribution',
        r'^On the (Imperfection|Geological)',
        r'^Hybridism$',
        r'^Instinct$',
        r'^Miscellaneous Objections',
        r'^Difficulties',
        r'^Laws of Variation',
        r'^Natural Selection',
        r'^Struggle for Existence',
        r'^Variation Under',
    ]

    while i < len(lines):
        line = lines[i].strip()
        if line == '':
            i += 1
            continue
        skip = False
        for pat in skip_patterns:
            if re.match(pat, line, re.IGNORECASE):
                skip = True
                break
        if skip:
            i += 1
            continue
        break

    # Now process the rest as paragraphs
    current_para = []

    def flush_para():
        if current_para:
            text = ' '.join(current_para)
            html_parts.append(f'<p>{text}</p>\n')
            current_para.clear()

    while i < len(lines):
        line = lines[i].strip()

        if line == '':
            flush_para()
            i += 1
            continue

        # Detect section subheadings - lines that are short, possibly title-case,
        # and surrounded by blank lines
        is_heading = False
        if len(line) < 120 and len(line.split()) < 20:
            # Check if previous line was blank and next line is blank
            prev_blank = (i == 0) or (lines[i-1].strip() == '')
            next_blank = (i == len(lines) - 1) or (i + 1 < len(lines) and lines[i+1].strip() == '')

            # Looks like a section heading if it's short, surrounded by blanks,
            # and doesn't end with common sentence-ending patterns
            if prev_blank and next_blank and not line.endswith(('.', ',', ';', ':', '—')):
                # But not if it looks like a short paragraph
                if not line[0].islower():
                    is_heading = True

        if is_heading:
            flush_para()
            # Make a slug for the heading
            slug = re.sub(r'[^a-z0-9]+', '-', line.lower()).strip('-')
            html_parts.append(f'<h3 id="{slug}">{line}</h3>\n')
            i += 1
            continue

        current_para.append(line)
        i += 1

    flush_para()
    return '\n'.join(html_parts)


def build_toc():
    """Build the table of contents HTML."""
    items = []
    for num, title, anchor in CHAPTER_META:
        items.append(f'<li><a href="#{anchor}">{title}</a></li>')
    return '\n'.join(items)


def build_html():
    header = '''<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>On the Origin of Species</title>
<style>
html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}

body {
	font: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1,h2,h3,h4,h5,h6 {
  margin: 3em 0 1em;
	font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}

p.footnote {
	font-size: 90%;
	text-indent: 0%;
	margin-left: 10%;
	margin-right: 10%;
	margin-top: 1em;
	margin-bottom: 1em;
}

.center {
  text-align: center;
}

dt {
  font-weight: bold;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
  margin-top: 1.5em;
}

dd {
  margin-left: 0;
  margin-bottom: 1em;
  color: #1d1d1d;
  font-family: sans-serif;
}
</style>
</head>

<body>
	<center>
	<h1>On the Origin of Species</h1>
	<h3>By Means of Natural Selection, or the Preservation of Favoured Races in the Struggle for Life</h3>
	<h2>Charles Darwin</h2>
	<p class="center">
	<s>1859</s> 2026
	</p>
	</center>
	<hr>
	<p><i>This is an AI modernization of On the Origin of Species into contemporary English. The original ebook is available from <a href="https://standardebooks.org/ebooks/charles-darwin/the-origin-of-species">Standard Ebooks</a>.</i></p>

	<hr>
'''

    toc = f'''<h2 id="contents">Contents</h2>
<ul>
{build_toc()}
</ul>
<hr>
'''

    chapters_html = []
    for num, title, anchor in CHAPTER_META:
        filepath = CHAPTERS_DIR / f"{num}.txt"
        text = filepath.read_text()

        is_glossary = (num == "017")

        if is_glossary:
            body = format_glossary(text)
        else:
            body = text_to_html(text)

        chapter_html = f'<h2 id="{anchor}">{title}</h2>\n\n{body}\n\n<hr>\n'
        chapters_html.append(chapter_html)

    footer = '''
</body>
</html>
'''

    full_html = header + toc + '\n'.join(chapters_html) + footer
    OUTPUT.write_text(full_html)
    print(f"Written to {OUTPUT}")
    print(f"File size: {OUTPUT.stat().st_size / 1024:.0f} KB")


def format_glossary(text):
    """Format glossary text as definition list.

    Format: term on its own line, blank line, definition paragraph(s),
    double blank line between entries.
    """
    # Split into entries by double blank lines
    # First, skip the title/intro lines
    lines = text.strip().split('\n')
    # Find where the actual entries start (after title and intro paragraph)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '':
            i += 1
            continue
        if line.lower().startswith('glossary') or line.startswith('('):
            i += 1
            continue
        break

    # Rejoin remaining text and split on double newlines to get entries
    remaining = '\n'.join(lines[i:]).strip()
    entries = re.split(r'\n\n\n+', remaining)

    html_parts = ['<dl>']
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # First line is the term, rest (after blank line) is the definition
        parts = entry.split('\n\n', 1)
        term = parts[0].strip()
        if len(parts) > 1:
            definition = ' '.join(parts[1].strip().split('\n'))
        else:
            definition = ''
        if term:
            html_parts.append(f'<dt>{term}</dt>')
            html_parts.append(f'<dd>{definition}</dd>')

    html_parts.append('</dl>')
    return '\n'.join(html_parts)


if __name__ == "__main__":
    build_html()
