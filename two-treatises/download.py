#!/usr/bin/env python3
"""Download Two Treatises of Government from Standard Ebooks GitHub."""
import urllib.request
import re
import os

BASE = "https://raw.githubusercontent.com/standardebooks/john-locke_two-treatises-of-government/master/src/epub/text"
OUT = os.path.join(os.path.dirname(__file__), "chapters")
os.makedirs(OUT, exist_ok=True)

def strip_html(html):
    """Strip HTML tags and clean up text."""
    # Remove everything before <body>
    html = re.sub(r'.*?<body[^>]*>', '', html, flags=re.DOTALL)
    html = re.sub(r'</body>.*', '', html, flags=re.DOTALL)
    # Remove header/hgroup tags but keep their text
    html = re.sub(r'</?(?:header|hgroup|section)[^>]*>', '', html)
    # Convert <br/> to newline
    html = re.sub(r'<br\s*/?>', '\n', html)
    # Convert block elements to double newline
    html = re.sub(r'<(?:p|h[1-6]|blockquote|div)[^>]*>', '\n\n', html)
    html = re.sub(r'</(?:p|h[1-6]|blockquote|div)>', '', html)
    # Remove remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # Decode HTML entities
    html = html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    html = html.replace('&quot;', '"').replace('&#8220;', '\u201c').replace('&#8221;', '\u201d')
    html = html.replace('&mdash;', '\u2014').replace('&ndash;', '\u2013')
    html = html.replace('&nbsp;', ' ')
    html = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), html)
    html = re.sub(r'&\w+;', '', html)  # catch remaining entities
    # Clean up whitespace
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)
    return html.strip()

def download(url):
    """Download a URL and return the text content."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')

# Chapter mapping: chapter number -> filename
chapters = []

# Preface -> 000
chapters.append(("000", "preface.xhtml", "Preface"))

# Book 1 chapters 1-11 -> 001-011
for i in range(1, 12):
    chapters.append((f"{i:03d}", f"chapter-1-{i}.xhtml", f"Book I, Chapter {i}"))

# Book 2 chapters 1-19 -> 012-030
for i in range(1, 20):
    chapters.append((f"{i+11:03d}", f"chapter-2-{i}.xhtml", f"Book II, Chapter {i}"))

for num, filename, label in chapters:
    outpath = os.path.join(OUT, f"{num}.txt")
    if os.path.exists(outpath):
        print(f"  Skipping {num} ({label}) - already exists")
        continue
    url = f"{BASE}/{filename}"
    print(f"  Downloading {num}: {label} from {filename}...")
    try:
        html = download(url)
        text = strip_html(html)
        with open(outpath, 'w') as f:
            f.write(text)
        print(f"    -> {len(text)} chars")
    except Exception as e:
        print(f"    ERROR: {e}")

print("Done!")
