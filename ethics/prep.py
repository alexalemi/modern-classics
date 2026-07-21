"""Build chapters/ + manifest.json from the SE single-page XHTML of the
Nicomachean Ethics (Peters translation) — source.html.

Structure in the source: <section id="book-N"> wraps <section
id="part-N-M"> (Peters' thematic part titles: "The End", "Moral
Virtue", …) which wrap <section id="chapter-N-M-C"> — the 116
traditional chapters, numbered continuously per book across parts.

Output: one *section* per Book ("Book I".."Book X") stitched from
~3800-word part files (never crossing book boundaries). Inside a file:
"Chapter C" standalone headings (per-book numbering, the standard
citation scheme), with Peters' part title emitted as a subheading line
before its first chapter. SE endnote references (Peters' apparatus, 784
of them) are stripped, as are word-joiner/hair-space typography.
"""

import html as H
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 3800
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


class Chapter(HTMLParser):
    """Flatten one chapter <section> into paragraphs (autobiography's
    converter, minus tables — the Ethics has none)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras, self.buf = [], []
        self.skip = 0
        self.indent = 0

    def flush(self):
        text = " ".join("".join(self.buf).split())
        self.buf = []
        if text:
            self.paras.append(("  " if self.indent else "") + text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            self.skip += 1
            return
        if tag == "a" and "noteref" in a.get("epub:type", ""):
            self.skip = 1
            return
        if tag in ("header", "hgroup", "h2", "h3", "h4"):
            self.skip = 1
            return
        if tag in ("blockquote", "ol", "ul"):
            self.flush()
            self.indent += 1
        elif tag in ("p", "li"):
            self.flush()
        elif tag == "br":
            self.flush()

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag in ("blockquote", "ol", "ul"):
            self.flush()
            self.indent -= 1
        elif tag in ("p", "li"):
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def clean_text(s):
    s = s.replace("⁠", "").replace(" ", " ").replace(" ", " ")
    return unicodedata.normalize("NFC", s)


text = clean_text(BOOK.joinpath("source.html").read_text())

# part titles: id="part-N-M" -> its title text
part_titles = {}
for m in re.finditer(r'<section[^>]* id="part-(\d+-\d+)"[^>]*>\s*'
                     r'<h3 epub:type="title">(.*?)</h3>', text, re.S):
    words = H.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split()
    part_titles[m.group(1)] = " ".join(words)

starts = [(m.start(), m.group(1))
          for m in re.finditer(r'<section[^>]* id="chapter-(\d+-\d+-\d+)"', text)]
end_all = re.search(r'<section[^>]* id="endnotes"', text).start()

# books[b] = list of (chapter_no, part_key, paragraphs)
books = {}
for i, (pos, cid) in enumerate(starts):
    end = starts[i + 1][0] if i + 1 < len(starts) else end_all
    b, pt, c = (int(x) for x in cid.split("-"))
    parser = Chapter()
    parser.feed(text[pos:end])
    parser.flush()
    books.setdefault(b, []).append((c, f"{b}-{pt}", parser.paras))

manifest, file_no = [], 0
for b in sorted(books):
    chaps = books[b]
    nums = [c for c, _, _ in chaps]
    assert nums == list(range(1, len(nums) + 1)), f"book {b} chapter seq: {nums}"
    title = f"Book {ROMAN[b - 1]}"
    total = sum(len(" ".join(p).split()) for _, _, p in chaps)
    per = total / max(1, round(total / TARGET))
    groups, cur, curw = [], [], 0
    for entry in chaps:
        w = len(" ".join(entry[2]).split())
        if cur and curw + w > per * 1.15:
            groups.append(cur); cur, curw = [], 0
        cur.append(entry); curw += w
        if curw >= per:
            groups.append(cur); cur, curw = [], 0
    if cur:
        groups.append(cur)
    seen_parts = set()
    for part, group in enumerate(groups, 1):
        out = [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
        for c, pk, paras in group:
            if pk not in seen_parts:
                seen_parts.add(pk)
                out.append(f"\n{part_titles[pk]}")
            body, block = [], []
            for p in paras:
                if p.startswith("  "):
                    block.append(p)
                else:
                    if block:
                        body.append("\n".join(block)); block = []
                    body.append(p)
            if block:
                body.append("\n".join(block))
            out.append(f"\nChapter {c}\n\n" + "\n\n".join(body))
        content = "\n".join(out) + "\n"
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text(content)
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups),
                         "words": len(content.split()),
                         "chapters": f"{group[0][0]}-{group[-1][0]}",
                         "book": b})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{sum(len(c) for c in books.values())} chapters -> {file_no} files")
for m in manifest:
    print(f"  {m['file']}  Book {m['book']:<2} part {m['part']}/{m['of']}"
          f"  ch {m['chapters']:<7} {m['words']:>5}")
