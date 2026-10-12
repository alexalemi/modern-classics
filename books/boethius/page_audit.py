"""Audit the ASSEMBLED page, which is the only artefact the reader sees.

check.py compares modern_chapters/ against chapters/; this asks the
opposite question -- did the render produce what those files meant? The
tyndall lesson (a marker present, placed once, and rendered wrong) and
the descartes one (a Part line silently deleted by strip_front) both
live downstream of every source-side check.
"""
import collections
import pathlib
import re

page = pathlib.Path("site/boethius.html").read_text()

h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", page, re.S)
h3 = re.findall(r"<h3[^>]*>(.*?)</h3>", page, re.S)
ids = re.findall(r'id="([^"]+)"', page)
dup = [i for i, n in collections.Counter(ids).items() if n > 1]
body = re.sub(r"<[^>]+>", "", page)

print(f"h2 (books + top-level): {len(h2)}")
for t in h2:
    print("   ", re.sub(r"\s+", " ", t).strip()[:70])
print(f"h3 (chapters): {len(h3)}")
print(f"<pre> verse blocks: {page.count('<pre')}")
print(f"<em> spans: {page.count('<em>')}")
print(f"duplicate ids: {dup or 'none'}")
print(f"stray asterisks in body text: {body.count('*')}")
print(f"literal tabs in body text: {body.count(chr(9))}")
songs = re.findall(r"Song ([IVXL]+):", body)
print(f"song headings in body: {len(songs)}")
