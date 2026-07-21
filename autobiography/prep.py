"""Build chapters/ + manifest.json from the Standard Ebooks single-page
XHTML of Franklin's Autobiography (source.html).

First SE-HTML-sourced book: the prep parses the XHTML instead of
Gutenberg plain text. Per chapter section (id="chapter-N"):
  - the h2 title block becomes "Chapter N: Title" (Pine's editorial
    chapter titles, kept for navigation),
  - paragraphs flow as single lines,
  - <ol>/<ul> lists and <table>s become two-space-indented text blocks
    (assemble.py renders indented paragraphs as <pre> outlines — this
    carries the 13-virtues list and the daily-schedule chart),
  - <blockquote>s (verse, the epitaph, letters' sign-offs) are indented
    line-per-line,
  - endnote references (SE editorial apparatus, not Franklin) are
    dropped, along with SE's word-joiner/hair-space typography.

Chapters are one file each — the largest is ~5.5k words, inside the
single-agent limit — so manifest entries are all part 1 of 1.
"""

import html as H
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

BOOK = Path(__file__).parent

BLOCK_TAGS = {"p", "li", "tr", "th", "td", "blockquote", "table", "ol",
              "ul", "thead", "tbody", "header", "h2", "h3", "h4"}


class Chapter(HTMLParser):
    """Flatten one chapter <section> into paragraphs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras = []        # finished paragraphs (str)
        self.buf = []          # current inline text
        self.skip = 0          # inside noteref/header depth
        self.indent = 0        # blockquote/list/table nesting
        self.cells = None      # current table row cells

    def flush(self):
        text = " ".join("".join(self.buf).split())
        self.buf = []
        if text:
            self.paras.append(("  " * min(self.indent, 1)) + text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            self.skip += 1
            return
        if tag == "a" and "noteref" in a.get("epub:type", ""):
            self.skip = 1
            return
        if tag in ("header", "hgroup"):        # chapter title block: handled separately
            self.skip = 1
            return
        if tag in ("blockquote", "ol", "ul", "table"):
            self.flush()
            self.indent += 1
        elif tag == "tr":
            self.cells = []
        elif tag in ("p", "li", "h3", "h4") and self.cells is None:
            self.flush()
        elif tag == "br":
            self.flush()

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag in ("blockquote", "ol", "ul", "table"):
            self.flush()
            self.indent -= 1
        elif tag in ("th", "td"):
            self.cells.append(" ".join("".join(self.buf).split()))
            self.buf = []
        elif tag == "tr":
            row = " | ".join(c for c in self.cells if c != "")
            if row:
                self.paras.append("  " + row)
            self.cells = None
        elif tag in ("p", "li", "h3", "h4") and self.cells is None:
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def clean_text(s):
    s = s.replace("⁠", "").replace(" ", " ").replace(" ", " ")
    return unicodedata.normalize("NFC", s)


text = clean_text(BOOK.joinpath("source.html").read_text())

starts = [(m.start(), int(m.group(1)))
          for m in re.finditer(r'<section[^>]* id="chapter-(\d+)"', text)]
end_all = re.search(r'<section[^>]* id="endnotes"', text).start()

manifest = []
for i, (pos, n) in enumerate(starts):
    end = starts[i + 1][0] if i + 1 < len(starts) else end_all
    chunk = text[pos:end]
    tm = re.search(r'epub:type="title"[^>]*>(.*?)</(?:p|h[23])>', chunk, re.S)
    title_words = H.unescape(re.sub(r"<[^>]+>", " ", tm.group(1))).split()
    title = f"Chapter {n}: {' '.join(title_words)}"

    parser = Chapter()
    parser.feed(chunk)
    parser.flush()

    # merge consecutive indented lines into single indented paragraphs
    out, block = [], []
    for p in parser.paras:
        if p.startswith("  "):
            block.append(p)
        else:
            if block:
                out.append("\n".join(block))
                block = []
            out.append(p)
    if block:
        out.append("\n".join(block))

    content = title + "\n\n" + "\n\n".join(out) + "\n"
    fn = f"{n - 1:03d}.txt"
    BOOK.joinpath("chapters", fn).write_text(content)
    manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                     "words": len(content.split())})

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{len(manifest)} chapters")
for m in manifest:
    print(f"  {m['file']} {m['words']:>6}  {m['title'][:58]}")
