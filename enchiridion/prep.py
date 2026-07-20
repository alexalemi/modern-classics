"""Build chapters/ + manifest.json for the Enchiridion from source.txt.

The 53 sections are tiny (median ~150 words), so instead of one file per
section we group contiguous runs of sections into ~1700-word files. Each
file's first line is its title ("Sections A-B"); inside, every section
starts with a standalone "Section N" heading line (assemble.py renders
those as h4 subheadings). Roman numeral order is validated so a dropped
section can't pass silently. Footnote markers like [2] are stripped; the
end-of-book footnote block and the 1948 introduction (still in copyright
when the Liberal Arts Press edition appeared; PG cleared it, but we only
want Higginson's 1865 translation anyway) are cut.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 1700

text = BOOK.joinpath("source.txt").read_text()

start = re.search(r"\*\*\* START OF THE PROJECT GUTENBERG[^\n]*\n", text).end()
end = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG", text).start()
text = text[start:end]
text = text[: text.index("\n                               Footnotes\n")]

ROMAN = re.compile(r"^\s{10,}([IVXL]+)(?:\[\d+\])?\s*$", re.M)
VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}


def roman(s):
    total = 0
    for a, b in zip(s, s[1:] + "\0"):
        total += -VALUES[a] if VALUES[a] < VALUES.get(b, 0) else VALUES[a]
    return total


matches = list(ROMAN.finditer(text))
sections = []
for i, m in enumerate(matches):
    n = roman(m.group(1))
    assert n == i + 1, f"section sequence broke at {m.group(1)} (#{i + 1})"
    body = text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)]
    body = re.sub(r"\[\d+\]", "", body)
    paras = []
    for p in re.split(r"\n\s*\n", body):
        if not p.strip():
            continue
        lines = p.split("\n")
        if all(l.startswith("  ") for l in lines):
            # verse block: keep the line breaks and a marker indent
            paras.append("\n".join("  " + l.strip() for l in lines))
        else:
            paras.append(" ".join(p.split()))
    sections.append((n, "\n\n".join(paras)))

groups, cur, curw = [], [], 0
for n, body in sections:
    cur.append((n, body))
    curw += len(body.split())
    if curw >= TARGET:
        groups.append(cur)
        cur, curw = [], 0
if cur:
    groups.append(cur)

manifest = []
for i, group in enumerate(groups):
    lo, hi = group[0][0], group[-1][0]
    title = f"Sections {lo}–{hi}"
    out = [title]
    for n, body in group:
        out.append(f"\nSection {n}\n\n{body}")
    content = "\n".join(out) + "\n"
    fn = f"{i:03d}.txt"
    BOOK.joinpath("chapters", fn).write_text(content)
    manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                     "words": len(content.split())})

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{len(sections)} sections -> {len(groups)} files")
for m in manifest:
    print(f"  {m['file']}  {m['title']:<16} {m['words']:>5} words")
