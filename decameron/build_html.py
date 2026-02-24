#!/usr/bin/env python3
"""Build the Decameron HTML book from modernized chapter files."""

import re
import os
from pathlib import Path

CHAPTERS_DIR = Path(__file__).parent / "modern_chapters"
OUTPUT = Path(__file__).parent.parent / "site" / "decameron.html"

# Chapter structure: (chapter_num, section_type, day, story, title)
SECTIONS = []

# Proem
SECTIONS.append((0, "proem", 0, 0, "Proem"))

# Days 1-10
for day in range(1, 11):
    base = 1 + (day - 1) * 11  # each day: 1 intro + 10 stories
    SECTIONS.append((base, "intro", day, 0, f"Day {day} — Introduction"))
    for story in range(1, 11):
        SECTIONS.append((base + story, "story", day, story, f"Day {day}, Story {story}"))

# Conclusion
SECTIONS.append((111, "conclusion", 0, 0, "Conclusion of the Author"))

DAY_THEMES = {
    1: "Free topic",
    2: "Those who attain happiness after misfortune",
    3: "People who obtain something desired through ingenuity",
    4: "Love with unhappy endings",
    5: "Love with happy endings",
    6: "Clever retorts that save the day",
    7: "Tricks wives play on husbands",
    8: "Tricks people play on each other",
    9: "Free topic",
    10: "Generosity and magnificence",
}


def read_chapter(n):
    path = CHAPTERS_DIR / f"{n:03d}.txt"
    if not path.exists():
        return None
    return path.read_text().strip()


def text_to_html(text):
    """Convert plain text chapter to HTML paragraphs."""
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
        elif stripped.startswith("## "):
            flush_para()
            # Skip chapter headers — we generate our own
            continue
        else:
            current_para.append(stripped)
    flush_para()
    return "\n\n".join(p for p in html_parts if p)


def format_paragraph(text):
    """Apply inline formatting to a paragraph."""
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic: _text_ or *text*
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)\*(.+?)\*(?!\w)', r'<em>\1</em>', text)
    # Em dash normalization
    text = text.replace(" -- ", " — ")
    text = text.replace("--", "—")

    # Detect if this is a verse/song line (starts with indentation or has
    # very short lines separated by <br>)
    if text.startswith("> "):
        text = text[2:]
        return f'<blockquote><p>{text}</p></blockquote>'

    return f'<p>{text}</p>'


def make_anchor(section_type, day, story):
    """Generate an HTML anchor ID for a section."""
    if section_type == "proem":
        return "proem"
    if section_type == "conclusion":
        return "conclusion"
    if section_type == "intro":
        return f"day-{day}"
    return f"day-{day}-story-{story}"


def build_toc():
    """Build the table of contents HTML."""
    toc = ['<nav id="toc">', '<h2>Contents</h2>']

    toc.append(f'<p><a href="#proem">Proem</a></p>')

    for day in range(1, 11):
        theme = DAY_THEMES[day]
        toc.append(f'<h3><a href="#day-{day}">Day {day}</a> <small>— {theme}</small></h3>')
        toc.append('<ul>')
        for story in range(1, 11):
            anchor = f"day-{day}-story-{story}"
            toc.append(f'  <li><a href="#{anchor}">Story {story}</a></li>')
        toc.append('</ul>')

    toc.append(f'<p><a href="#conclusion">Conclusion of the Author</a></p>')
    toc.append('</nav>')
    return "\n".join(toc)


def build_html():
    """Assemble the complete HTML book."""
    chapters_html = []

    for chapter_num, section_type, day, story, title in SECTIONS:
        text = read_chapter(chapter_num)
        if text is None:
            print(f"WARNING: Missing chapter {chapter_num:03d} ({title})")
            continue

        anchor = make_anchor(section_type, day, story)

        if section_type == "intro":
            heading = f'<h2 id="{anchor}">{title}</h2>'
        elif section_type == "story":
            heading = f'<h3 id="{anchor}">{title}</h3>'
        elif section_type == "proem":
            heading = f'<h2 id="{anchor}">{title}</h2>'
        else:
            heading = f'<h2 id="{anchor}">{title}</h2>'

        body = text_to_html(text)
        chapters_html.append(f'{heading}\n\n{body}')

        # Print progress
        chars = len(text)
        print(f"  {chapter_num:03d} {title}: {chars:,} chars")

    toc = build_toc()
    body = "\n\n<hr>\n\n".join(chapters_html)

    html = f"""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>The Decameron &mdash; Giovanni Boccaccio</title>
<style>
html {{
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}}

body {{
\tfont: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}}

h1,h2,h3,h4,h5,h6 {{
  margin: 3em 0 1em;
\tfont-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}}

h1 {{
  margin-top: 1em;
  text-align: center;
}}

h2 {{
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.3em;
}}

h3 {{
  color: #444;
}}

p,ul,ol {{
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}}

blockquote {{
  margin: 1.5em 2em;
  padding-left: 1em;
  border-left: 3px solid #ccc;
  font-style: italic;
}}

blockquote p {{
  margin-bottom: 1em;
}}

hr {{
  border: none;
  border-top: 1px solid #ddd;
  margin: 3em 0;
}}

#toc {{
  margin: 2em 0;
}}

#toc h3 {{
  margin: 1.5em 0 0.3em;
  font-size: 1em;
  border: none;
  color: #333;
}}

#toc h3 small {{
  font-weight: normal;
  color: #888;
  font-style: italic;
}}

#toc ul {{
  list-style: none;
  padding: 0;
  margin: 0.3em 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0 1.5em;
}}

#toc ul li {{
  margin: 0;
}}

#toc a {{
  text-decoration: none;
  color: #555;
  font-family: sans-serif;
  font-size: 0.85em;
}}

#toc a:hover {{
  color: #000;
  text-decoration: underline;
}}

.center {{
  text-align: center;
}}

.epigraph {{
  font-style: italic;
  text-align: center;
  margin: 1em 0 2em;
}}
</style>
</head>

<body>
\t<center>
\t<h1>The Decameron</h1>
\t<h3>Giovanni Boccaccio (1353)</h3>
\t</center>
\t<p><i>This is an AI-assisted modernization of Giovanni Boccaccio's Decameron,
\toriginally written in 1353, working from the John Payne translation (1886).
\tThe goal is a faithful but accessible retelling in contemporary English,
\tpreserving the wit, warmth, and storytelling brilliance of the original
\twhile making it genuinely enjoyable for modern readers.</i></p>
\t<hr>

{toc}

<hr>

{body}

</body>
</html>"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html)
    print(f"\nOutput: {OUTPUT}")
    print(f"Size: {len(html):,} chars")


if __name__ == "__main__":
    build_html()
