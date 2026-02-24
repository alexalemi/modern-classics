#!/usr/bin/env python3
"""Download The Decameron from Standard Ebooks GitHub and split into numbered chapters."""

import urllib.request
import re
import os
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/standardebooks/giovanni-boccaccio_the-decameron_john-payne/master/src/epub/text"
OUT_DIR = Path(__file__).parent / "chapters"
OUT_DIR.mkdir(exist_ok=True)

# Define the chapter order: proem, then day intros and stories, then conclusion
SECTIONS = ["proem"]
for day in range(1, 11):
    SECTIONS.append(f"day-{day}-introduction")
    for story in range(1, 11):
        SECTIONS.append(f"day-{day}-{story}")
SECTIONS.append("conclusion")

def strip_html(xhtml: str) -> str:
    """Convert XHTML to plain text, preserving paragraph breaks."""
    # Remove XML declaration and head
    xhtml = re.sub(r'<\?xml.*?\?>', '', xhtml)
    xhtml = re.sub(r'<head>.*?</head>', '', xhtml, flags=re.DOTALL)

    # Remove footnote references like <a href="endnotes.xhtml#...">N</a>
    xhtml = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>\d+</a>', '', xhtml)

    # Convert <br/> to newlines
    xhtml = re.sub(r'<br\s*/?\s*>', '\n', xhtml)

    # Convert headers to plain text with markers
    xhtml = re.sub(r'<h\d[^>]*>(.*?)</h\d>', r'\n## \1\n', xhtml, flags=re.DOTALL)

    # Convert <em> and <i> to _text_
    xhtml = re.sub(r'<(?:em|i)[^>]*>(.*?)</(?:em|i)>', r'_\1_', xhtml, flags=re.DOTALL)

    # Convert <strong> and <b> to **text**
    xhtml = re.sub(r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', xhtml, flags=re.DOTALL)

    # Convert blockquotes
    xhtml = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n> \1\n', xhtml, flags=re.DOTALL)

    # Convert paragraphs to text with double newlines
    xhtml = re.sub(r'<p[^>]*>', '\n', xhtml)
    xhtml = re.sub(r'</p>', '\n', xhtml)

    # Remove all remaining HTML tags
    xhtml = re.sub(r'<[^>]+>', '', xhtml)

    # Decode HTML entities
    xhtml = xhtml.replace('&amp;', '&')
    xhtml = xhtml.replace('&lt;', '<')
    xhtml = xhtml.replace('&gt;', '>')
    xhtml = xhtml.replace('&quot;', '"')
    xhtml = xhtml.replace('&#8217;', '\u2019')
    xhtml = xhtml.replace('&nbsp;', ' ')
    xhtml = xhtml.replace('\u2060', '')  # word joiner

    # Clean up whitespace: collapse multiple blank lines, strip trailing spaces
    lines = xhtml.split('\n')
    lines = [line.strip() for line in lines]
    # Collapse multiple empty lines to max 2
    result = []
    blank_count = 0
    for line in lines:
        if line == '':
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return '\n'.join(result).strip() + '\n'


def section_title(name: str) -> str:
    """Generate a human-readable title from a section name."""
    if name == "proem":
        return "Proem"
    if name == "conclusion":
        return "Conclusion of the Author"
    m = re.match(r'day-(\d+)-introduction', name)
    if m:
        return f"Day {int(m.group(1))} — Introduction"
    m = re.match(r'day-(\d+)-(\d+)', name)
    if m:
        return f"Day {int(m.group(1))}, Story {int(m.group(2))}"
    return name


def main():
    total_chars = 0
    for i, section in enumerate(SECTIONS):
        url = f"{BASE_URL}/{section}.xhtml"
        filename = OUT_DIR / f"{i:03d}.txt"

        print(f"Downloading {section}...", end=" ", flush=True)
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                xhtml = resp.read().decode('utf-8')
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        text = strip_html(xhtml)
        title = section_title(section)

        # Prepend the title if not already present in the text
        if not text.startswith(f"## {title}"):
            text = f"## {title}\n\n{text}"

        filename.write_text(text)
        chars = len(text)
        total_chars += chars
        print(f"{chars:,} chars -> {filename.name}")

    print(f"\nTotal: {len(SECTIONS)} sections, {total_chars:,} characters")
    print(f"Output: {OUT_DIR}/")


if __name__ == "__main__":
    main()
