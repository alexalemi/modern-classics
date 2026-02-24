#!/usr/bin/env python3
"""Assemble all 26 translated chapters into a single HTML file."""

import html
import re

BOOKS = [
    ("I", "Origins and Causes", [1, 2, 3, 4, 5]),
    ("II", "The First Years", [6, 7, 8]),
    ("III", "Escalation", [9, 10, 11]),
    ("IV", "Turning Points", [12, 13, 14]),
    ("V", "Uneasy Peace", [15, 16, 17]),
    ("VI", "The Sicilian Expedition", [18, 19, 20]),
    ("VII", "Catastrophe at Syracuse", [21, 22, 23]),
    ("VIII", "The War in Ionia", [24, 25, 26]),
]

HEADER = """<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>History of the Peloponnesian War &mdash; Thucydides</title>
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

.dialogue-label {
  font-weight: bold;
  font-variant: small-caps;
}

hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 3em 0;
}
</style>
</head>

<body>
\t<center>
\t<h1>History of the Peloponnesian War</h1>
\t<h3>by Thucydides</h3>
\t<p class="center">
\t<s>c. 431 BC</s> 2026
\t</p>
\t</center>

\t<hr>
\t<p><i>This is an AI modernization of History of the Peloponnesian War into contemporary English.
\tThe original Richard Crawley translation (1874) is available on
\t<a href="https://standardebooks.org/ebooks/thucydides/history-of-the-peloponnesian-war/richard-crawley">Standard Ebooks</a>.</i></p>

\t<hr>
"""

FOOTER = """
</body>
</html>
"""


def read_chapter(num):
    """Read a chapter file and return (title_line, subtitle_line, body_text)."""
    path = f"modern_chapters/{num:03d}.txt"
    with open(path, "r") as f:
        text = f.read().strip()

    lines = text.split("\n")

    # First line is chapter heading (e.g. "CHAPTER 1" or Roman numeral)
    title = lines[0].strip() if lines else ""

    # Find subtitle: skip any blank lines after title
    idx = 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    subtitle = lines[idx].strip() if idx < len(lines) else ""

    # Check if subtitle looks like body text (too long = it's a paragraph, not a subtitle)
    # Subtitles are typically short descriptive headers
    if len(subtitle) > 200:
        # This line is body text, not a subtitle
        body = "\n".join(lines[idx:])
        subtitle = ""
    else:
        # Find body start (skip blank lines after subtitle)
        body_start = idx + 1
        while body_start < len(lines) and lines[body_start].strip() == "":
            body_start += 1
        body = "\n".join(lines[body_start:])

    return title, subtitle, body


def text_to_html(text):
    """Convert plain text body to HTML paragraphs."""
    paragraphs = re.split(r"\n\n+", text.strip())
    result = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check for section headers (all caps, short, standalone)
        if para == para.upper() and len(para) < 80 and "\n" not in para and len(para.split()) < 12:
            # Subheading like "THE MELIAN DIALOGUE"
            result.append(f'\n<h4 class="center">{html.escape(para)}</h4>\n')
            continue

        # Check for dialogue labels (e.g. "ATHENIANS: ...")
        dialogue_match = re.match(r"^([A-Z]{3,}(?:\s[A-Z]+)?)\s*:\s*(.+)", para, re.DOTALL)
        if dialogue_match:
            label = dialogue_match.group(1)
            speech = dialogue_match.group(2).strip()
            speech = html.escape(speech).replace("\n", " ")
            result.append(f'<p><span class="dialogue-label">{html.escape(label)}:</span> {speech}</p>')
            continue

        # Regular paragraph
        escaped = html.escape(para).replace("\n", " ")
        result.append(f"<p>{escaped}</p>")

    return "\n\n".join(result)


def build_toc():
    """Build table of contents HTML."""
    lines = ['<h2 id="contents">Contents</h2>', "<ul>"]
    for book_num, (roman, title, chapters) in enumerate(BOOKS, 1):
        lines.append(
            f'<li><a href="#book-{book_num:03d}">Book {roman}: {html.escape(title)}</a>'
        )
        lines.append("<ul>")
        for ch in chapters:
            ch_title, ch_subtitle, _ = read_chapter(ch)
            display = html.escape(ch_subtitle) if ch_subtitle else html.escape(ch_title)
            lines.append(f'<li><a href="#ch-{ch:03d}">{display}</a></li>')
        lines.append("</ul>")
        lines.append("</li>")
    lines.append("</ul>")
    return "\n".join(lines)


def main():
    parts = [HEADER]

    # Table of contents
    parts.append(build_toc())
    parts.append("\n<hr>\n")

    # Each book
    for book_num, (roman, title, chapters) in enumerate(BOOKS, 1):
        parts.append(f'<h2 id="book-{book_num:03d}">Book {roman}: {html.escape(title)}</h2>')
        parts.append("")

        for ch in chapters:
            ch_title, ch_subtitle, body = read_chapter(ch)
            parts.append(f'<h3 id="ch-{ch:03d}">{html.escape(ch_title)}</h3>')
            if ch_subtitle:
                parts.append(f"<p><i>{html.escape(ch_subtitle)}</i></p>")
            parts.append("")
            parts.append(text_to_html(body))
            parts.append("\n<hr>\n")

    parts.append(FOOTER)

    output = "\n".join(parts)
    with open("../site/peloponnesian-war.html", "w") as f:
        f.write(output)

    print(f"Written to site/peloponnesian-war.html ({len(output):,} bytes)")


if __name__ == "__main__":
    main()
