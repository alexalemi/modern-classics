"""Build chapters/ + manifest.json for Roman Lives from source.txt
(Gutenberg #674, Plutarch's Lives, Dryden translation ed. Clough).

The volume takes five lives — the fall-of-the-Republic arc the founders
studied: Caesar, Cato the Younger, Cicero, Brutus, Antony. Each life is
one *section* (title = the subject's name) stitched from ~4200-word
part files split at paragraph boundaries; Dryden's text has no chapter
divisions, so files carry no internal headings. A life's text runs from
its body heading (the SECOND occurrence of the all-caps name — the
first is the table of contents) to the next all-caps heading of any
kind (the next life or a COMPARISON).
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 4200

LIVES = [("CAESAR", "Caesar"),
         ("CATO THE YOUNGER", "Cato the Younger"),
         ("CICERO", "Cicero"),
         ("MARCUS BRUTUS", "Brutus"),
         ("ANTONY", "Antony")]

text = BOOK.joinpath("source.txt").read_text()
start = re.search(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n", text)
end = re.search(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG", text)
text = text[start.end():end.start()]

headings = [(m.start(), m.end(), m.group(0).strip())
            for m in re.finditer(r"^[A-Z][A-Z .]+$", text, flags=re.M)]

manifest, file_no = [], 0
for caps, title in LIVES:
    occ = [h for h in headings if h[2] == caps]
    assert len(occ) == 2, f"{caps}: {len(occ)} occurrences"
    hstart, hend, _ = occ[1]
    following = [h for h in headings if h[0] > hstart]
    body = text[hend:following[0][0]]
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", body) if p.strip()]
    total = sum(len(p.split()) for p in paras)
    nparts = max(1, round(total / TARGET))
    per = total / nparts
    groups, cur, curw = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and curw + w > per * 1.2:
            groups.append(cur); cur, curw = [], 0
        cur.append(p); curw += w
        if curw >= per:
            groups.append(cur); cur, curw = [], 0
    if cur:
        groups.append(cur)
    for part, group in enumerate(groups, 1):
        out = [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
        out.append("\n" + "\n\n".join(group))
        content = "\n".join(out) + "\n"
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text(content)
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups),
                         "words": len(content.split())})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{len(LIVES)} lives -> {file_no} files")
for m in manifest:
    print(f"  {m['file']}  {m['title']:<17} part {m['part']}/{m['of']} {m['words']:>6}")
