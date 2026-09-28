"""T. H. Huxley, On a Piece of Chalk (1868): a RESTORED EDITION.

    python3 chalk/prep.py

The lecture to the working men of Norwich, 1868, in the text Huxley
revised for Collected Essays, vol. VIII, Discourses: Biological and
Geological (1894), from Project Gutenberg #10060 (source/pg10060.txt).
The words are Huxley's, unchanged. His five footnotes are set as
"Footnote: " paragraphs after the paragraph that cites them, the marker
removed. The dateline [1868] and the Gutenberg wrapper are left out.
Witness: scan_diff.py --vote against two Archive.org scans of the 1894
volume (see chalk/notes.txt).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "source" / "pg10060.txt").read_text().replace("\r\n", "\n")
a = src.index("If a well were sunk at our feet")
b = src.index("\nII\n\n\nTHE PROBLEMS OF THE DEEP SEA")
body = src[a:b].strip()

paras = [re.sub(r"\s*\n\s*", " ", re.sub(r"(?<=\w-)\n\s*", "", p.strip())) for p in re.split(r"\n\s*\n", body) if p.strip()]
# Gutenberg typos, both 1894 scans agreeing on the printed reading
# (scan_diff.py --vote a588258200huxluoft cu31924002924201)
FIXES = (("the more powder and waste", "the mere powder and waste"), ("_Cronia_", "_Crania_"))
joined = "\n\n".join(paras)
for bad, good in FIXES:
    assert joined.count(bad) == 1, bad
    joined = joined.replace(bad, good)
paras = joined.split("\n\n")
notes = {}
text = []
for p in paras:
    m = re.match(r"\[Footnote (\d+): (.*)\]$", p, re.S)
    if m:
        notes[m.group(1)] = m.group(2).strip()
        continue
    text.append(p)
out, used = [], set()
for p in text:
    cited = re.findall(r"\[(\d+)\]", p)
    out.append(re.sub(r"\[(\d+)\]", "", p))
    for n in cited:
        if n not in used:            # note 4 is cited twice: set it once
            out.append("Footnote: " + notes[n])
            used.add(n)
assert used == set(notes), (used, set(notes))
assert not re.search(r"\[\d+\]|\[Footnote", "\n".join(out))
TITLE = "On a Piece of Chalk"
body = "\n\n".join(out)
for d in ("chapters", "modern_chapters"):
    (HERE / d).mkdir(exist_ok=True)
    (HERE / d / "000.txt").write_text(f"{TITLE}\n\n{body}\n")
(HERE / "manifest.json").write_text(json.dumps(
    [{"file": "000.txt", "title": TITLE, "part": 1, "of": 1, "words": len(body.split())}],
    indent=1) + "\n")
print(len(out), "paragraphs,", len(body.split()), "words")
