"""Render about.md into site/about.html in the site's house style.

    python3 build_about.py     (or: make about)

The prose lives in about.md (repo root) — standard Markdown: paragraphs,
## headings, links, *emphasis*, lists. This script converts it and wraps
it in the same shell as the index page, borrowing the <style> block from
site/index.html verbatim so the two pages can never drift apart.
"""

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent

md = (ROOT / "about.md").read_text()
body = markdown.markdown(md, extensions=["smarty"])

index = (ROOT / "site" / "index.html").read_text()
style = re.search(r"<style>.*?</style>", index, re.S).group(0)

page = f"""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>About &mdash; Modern Classics</title>
\t<link rel="alternate" type="application/rss+xml" title="Modern Classics" href="feed.xml">
\t<link rel="alternate" type="application/atom+xml;profile=opds-catalog;kind=acquisition" title="Modern Classics OPDS catalog" href="opds.xml">
{style}
</head>
<body>

<h1>About</h1>

{body}

<p><a href="index.html">&larr; Back to the library</a></p>

</body>
</html>
"""

(ROOT / "site" / "about.html").write_text(page)
print(f"wrote site/about.html ({len(page)} bytes)")
