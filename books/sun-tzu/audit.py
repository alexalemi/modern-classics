"""One-off structural audit of chapters/ before translation begins.

The voice label is the whole architecture of this book: a paragraph is
Sun Tzu, a commentator, or Giles, and only the label says which. Every
defect found in prep was of that class -- a verse welded into a note, a
note whose opening bracket the source had lost, a block whose closing
bracket this prep's own bracket-collapse destroyed. So before a word is
translated, check the shape of what came out.
"""
import glob
import re
from collections import Counter

bad, tally = [], Counter()
for f in sorted(glob.glob("chapters/*.txt")):
    body = open(f).read().split("\n", 1)[1]
    ps = [re.sub(r"\s+", " ", p).strip()
          for p in re.split(r"\n\s*\n", body) if p.strip()]
    for p in ps:
        if p.startswith("Commentary: "):
            tally["Commentary"] += 1
            # a commentary paragraph opening on a verse number is a verse
            # that got swallowed by the note before it
            if re.match(r"^Commentary:\s+\d+[.,]\s", p):
                bad.append((f, "verse inside a note?", p[:90]))
        elif p.startswith("Footnote: "):
            tally["Footnote"] += 1
        else:
            tally["Verse"] += 1
            if "[" in p or "]" in p:
                bad.append((f, "stray bracket in a verse", p[:90]))
            if not re.match(r"^\d+[,.\d\s]*\.|^\(\d\)|^[a-z(]|^the |^nor |^for ",
                            p):
                bad.append((f, "verse with no number", p[:90]))

print("paragraphs:", dict(tally))
print("suspect:", len(bad))
for b in bad[:15]:
    print("  ", b[0], "|", b[1], "|", b[2])
