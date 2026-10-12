"""Audit an assembled Mill page: structure, ids, and the things the
convention-driven renderer decides for itself.

Run against site/mill-original.html BEFORE translating, so the shape is
known to be right before any file is written against it, and against
site/mill.html afterwards.
"""
import collections
import pathlib
import re
import sys

page = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                    else "site/mill.html").read_text()
plain = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()

for lvl, t in re.findall(r"<h([234])[^>]*>(.*?)</h\1>", page, re.S):
    print(f"  h{lvl}  {plain(t)[:72]}")
ids = re.findall(r'id="([^"]+)"', page)
dup = [i for i, n in collections.Counter(ids).items() if n > 1]
body = re.sub(r"<[^>]+>", "", page)
print(f"duplicate ids: {dup or 'none'}")
print(f"<pre>: {page.count('<pre')}   <em>: {page.count('<em>')}   "
      f"<hr>: {page.count('<hr')}   h4: {page.count('<h4')}")
print(f"stray asterisks in body: {body.count('*')}")
print(f"'Footnote:' paragraphs: {body.count('Footnote:')}")
print(f"'(Part ' markers left in body: {body.count('(Part ')}")
