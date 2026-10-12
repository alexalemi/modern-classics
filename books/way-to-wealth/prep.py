"""Build chapters/ + manifest.json for The Way to Wealth from source.txt.

The Gutenberg text (#43855) is an 1810 Darton chapbook: publisher ads,
frontispiece captions, and an English publisher's introduction wrap
Franklin's actual 1758 essay. We extract only Franklin's text — from the
"COURTEOUS READER," salutation through Richard Saunders' signature —
and strip the edition artifacts: [Illustration: ...] blocks (possibly
multi-line) and the Roman-numeral paragraph markers (I. II. III. IV.)
that Darton added to Father Abraham's speech. The essay is one short
piece, so it becomes a single chapter file.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent

text = BOOK.joinpath("source.txt").read_text()
start = text.index("COURTEOUS READER,")
end = text.index("RICHARD SAUNDERS.") + len("RICHARD SAUNDERS.")
text = text[start:end]

text = re.sub(r"\[Illustration[^\]]*\]", "", text)
text = re.sub(r"^([IVX]+\.) '", lambda m: "'", text, flags=re.M)

paras = []
for p in re.split(r"\n\s*\n", text):
    if not p.strip():
        continue
    if re.fullmatch(r"\*( +\*)*", " ".join(p.split())):
        paras.append("       *       *       *       *       *")
    else:
        paras.append(" ".join(p.split()))

content = "The Way to Wealth\n\n" + "\n\n".join(paras) + "\n"
BOOK.joinpath("chapters", "000.txt").write_text(content)
manifest = [{"file": "000.txt", "title": "The Way to Wealth",
             "part": 1, "of": 1, "words": len(content.split())}]
BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"1 chapter, {manifest[0]['words']} words")
