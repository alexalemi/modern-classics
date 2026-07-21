"""Build chapters/ + manifest.json for Seneca's Moral Letters from the
Wikisource HTML in raw/NNN.html (Gummere's translation, all 124
letters; Wikisource is the only complete public-domain source — SE's
edition is unpublished and Gutenberg lacks the work entirely).

Per letter: parse the mw-parser HTML, cut the Wikisource navigation
header (everything through the letter's own all-caps title line, e.g.
"I. ON SAVING TIME"), drop footnote markers ([1]) and the reference
list at the end, drop Gummere's section numbers ("1." at paragraph
starts), and title the letter "Letter N: <subtitle>" using the
subtitle from the title line, title-cased.

Letters are grouped into ~3800-word files of consecutive letters, each
letter inside a file introduced by its "Letter N: …" line (assemble.py
subheading convention). Files never split a letter.
"""

import html as H
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 3800

# title line: optional Roman numeral, then an ALL-CAPS subtitle (with
# possible footnote bracket cruft); e.g. "V. THE PHILOSOPHER'S MEAN" or
# "ON THE LESSON TO BE DRAWN FROM THE BURNING OF LYONS [ 1 ]"
ROMAN_RE = re.compile(r"^(?:([IVXLC]+)\.\s+)?([A-Z][A-Z'’,\- ]{6,}?)\.?(?:\s*\[[^\]]*\])?\s*$")


def parse_letter(n):
    t = BOOK.joinpath("raw", f"{n:03d}.html").read_text()
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S)
    t = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", t, flags=re.S)
    t = re.sub(r'<ol class="references">.*?</ol>', "", t, flags=re.S)
    t = re.sub(r'<span class="mw-cite-backlink">.*?</span>', "", t, flags=re.S)
    # paragraphs
    paras = re.findall(r"<p[^>]*>(.*?)</p>", t, flags=re.S)
    out = []
    started = False
    subtitle = None
    for p in paras:
        text = H.unescape(re.sub(r"<[^>]+>", " ", p))
        text = text.replace("​", "")
        text = " ".join(text.split())
        if not text:
            continue
        if not started:
            if "EPISTLES OF SENECA" in text.upper():
                continue
            m = ROMAN_RE.match(text)
            if m:
                started = True
                subtitle = m.group(2)
            continue
        # drop pure footnote text blocks (start with "Footnote" or digits+.)
        if re.match(r"^Footnote", text):
            continue
        text = re.sub(r"\s*\[\d+\]\s*", " ", text)
        text = re.sub(r"(?<![0-9])(\d+)\.\s+", lambda m: "", text, count=0)
        out.append(text)
    # remove Gummere's leading section numbers "1. " at sentence starts
    cleaned = []
    for p in out:
        p = re.sub(r"(^|(?<=[.!?»\"] ))\d{1,2}\.\s+(?=[A-Z\"“])", r"\1", p)
        cleaned.append(p)
    assert started, f"letter {n}: title line not found"
    assert cleaned, f"letter {n}: no body"
    sub = subtitle.strip().rstrip(".")
    # title-case the all-caps subtitle
    words = sub.lower().split()
    small = {"on", "of", "the", "and", "a", "an", "in", "to", "for", "from",
             "with", "as", "at", "by", "or", "not"}
    tc = [w if (i and w in small) else w.capitalize() for i, w in enumerate(words)]
    return " ".join(tc), cleaned


letters = []
for n in range(1, 125):
    sub, paras = parse_letter(n)
    letters.append((n, sub, paras))

manifest, file_no = [], 0
groups, cur, curw = [], [], 0
for n, sub, paras in letters:
    w = sum(len(p.split()) for p in paras)
    if cur and curw + w > TARGET * 1.25:
        groups.append(cur); cur, curw = [], 0
    cur.append((n, sub, paras)); curw += w
    if curw >= TARGET:
        groups.append(cur); cur, curw = [], 0
if cur:
    groups.append(cur)

for group in groups:
    lo, hi = group[0][0], group[-1][0]
    title = f"Letters {lo}–{hi}" if lo != hi else f"Letter {lo}"
    out = [title]
    for n, sub, paras in group:
        out.append(f"\nLetter {n}: {sub}\n\n" + "\n\n".join(paras))
    content = "\n".join(out) + "\n"
    fn = f"{file_no:03d}.txt"
    BOOK.joinpath("chapters", fn).write_text(content)
    manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                     "words": len(content.split()),
                     "letters": f"{lo}-{hi}"})
    file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
total = sum(m["words"] for m in manifest)
print(f"124 letters -> {file_no} files, {total} words")
for m in manifest[:8]:
    print(f"  {m['file']}  {m['title']:<16} {m['words']:>5}")
print("  ...")
