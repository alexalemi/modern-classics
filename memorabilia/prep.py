"""Build chapters/ + manifest.json for the Memorabilia from source.txt.

Source is Dakyns' translation (Gutenberg #1177): four Books, chapters as
bare Roman-numeral lines, with Dakyns' scholarly footnotes interleaved as
indented " (n) ..." paragraphs and (n) reference markers in the body. We
strip both — the notes are the translator's apparatus, not Xenophon —
along with the {Greek transliteration} braces that live in them.

Book III's fourteenth chapter is mislabeled "XII" in the source (a
second XII); the sequence validator patches it to the expected number
rather than trusting the printed numeral.

Output structure: one *section* per Book ("Book I".."Book IV"), each
split into ~4200-word part files at chapter boundaries. Inside a file,
every chapter starts with a standalone "Chapter N" heading line
(assemble.py renders these as h4 subheadings), preserving the standard
Book+chapter citation scheme. Manifest entries for a k-part book share
the title "Book N" with part=1..k — assemble.py stitches them back into
a single section.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 4200

VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}


def roman(s):
    total = 0
    for a, b in zip(s, s[1:] + "\0"):
        total += -VALUES[a] if VALUES[a] < VALUES.get(b, 0) else VALUES[a]
    return total


text = BOOK.joinpath("source.txt").read_text()
start = re.search(r"^BOOK I$", text, re.M).start()
end = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG", text).start()
text = text[start:end]

# Parse into books -> chapters
books = []          # list of (book_no, [(chap_no, body), ...])
cur_book = None
cur_chap = None


def clean(body):
    paras = []
    for p in re.split(r"\n\s*\n", body):
        if not p.strip():
            continue
        if re.match(r"\s+\(\d+\)", p):          # footnote block
            continue
        p = " ".join(p.split())
        p = re.sub(r" ?\(\d+\)", "", p)          # in-text note markers
        p = re.sub(r" ?\{[^}]*\}", "", p)        # Greek transliterations
        paras.append(p)
    return "\n\n".join(paras)


chunks = re.split(r"^(BOOK [IVX]+|[IVX]+)$", text, flags=re.M)
# chunks: [prefix, heading, body, heading, body, ...]
for i in range(1, len(chunks), 2):
    head, body = chunks[i], chunks[i + 1]
    if head.startswith("BOOK "):
        n = roman(head.split()[1])
        assert n == len(books) + 1, f"book sequence broke at {head}"
        books.append((n, []))
    else:
        chaps = books[-1][1]
        n = roman(head)
        expect = len(chaps) + 1
        if n != expect:
            print(f"  patching Book {books[-1][0]} chapter numeral "
                  f"{head} -> {expect}")
            n = expect
        chaps.append((n, clean(body)))

# Group each book's chapters into part files
manifest, file_no = [], 0
for book_no, chaps in books:
    title = f"Book {['I', 'II', 'III', 'IV'][book_no - 1]}"
    total = sum(len(b.split()) for _, b in chaps)
    nparts = max(1, round(total / TARGET))
    per = total / nparts
    groups, cur, curw = [], [], 0
    for n, body in chaps:
        w = len(body.split())
        # close the current file rather than let a big chapter overshoot it
        if cur and curw + w > per * 1.15:
            groups.append(cur)
            cur, curw = [], 0
        cur.append((n, body))
        curw += w
        if curw >= per:
            groups.append(cur)
            cur, curw = [], 0
    if cur:
        groups.append(cur)
    for part, group in enumerate(groups, 1):
        out = [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
        for n, body in group:
            out.append(f"\nChapter {n}\n\n{body}")
        content = "\n".join(out) + "\n"
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text(content)
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups), "words": len(content.split()),
                         "chapters": f"{group[0][0]}-{group[-1][0]}"})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{sum(len(c) for _, c in books)} chapters -> {file_no} files")
for m in manifest:
    print(f"  {m['file']}  {m['title']:<9} part {m['part']}/{m['of']}"
          f"  ch {m['chapters']:<7} {m['words']:>5} words")
