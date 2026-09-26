"""Render about.md into site/about.html in the site's house style.

    python3 build_about.py     (or: make about)

The prose lives in about.md (repo root) — standard Markdown: paragraphs,
## headings, links, *emphasis*, lists. This script converts it and wraps
it in build_index.page_shell(), the shell and stylesheet (site/site.css)
the index and restored pages use, so the three pages cannot drift apart.
"""

import re
from pathlib import Path

import markdown

import build_index

ROOT = Path(__file__).parent

md = (ROOT / "about.md").read_text()
body = markdown.markdown(md, extensions=["smarty"])

page = build_index.page_shell(
    "about.html", "About &mdash; Modern Classics", "About",
    "Classic texts, retold in contemporary English",
    f'<article class="prose">\n{body}\n</article>')

(ROOT / "site" / "about.html").write_text(page)
print(f"wrote site/about.html ({len(page)} bytes)")
