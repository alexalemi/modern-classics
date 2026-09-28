"""Fontenelle, Entretiens sur la pluralité des mondes -> chapters/.

    python3 fontenelle/prep.py

Source: French Wikisource, "Entretiens sur la pluralité des mondes/Texte
entier", from the Lyon (Leroy) edition of 1800, which prints Fontenelle's
final text with the Sixth Evening (added 1687) and his later revisions.
One file for the Preface and the letter to Monsieur L***, then one per
evening; none is over ~6.5k words, so nothing is split.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "source/wikisource.txt").read_text()

src = src[src.index("PRÉFACE."):]
EVENINGS = ["PREMIER", "SECOND", "TROISIEME", "QUATRIEME", "CINQUIEME", "SIXIEME"]
parts = re.split(r"\n\s*(?:%s) SOIR\.\s*\n" % "|".join(EVENINGS), src)
assert len(parts) == 7, len(parts)
# the last evening ends before Wikisource's footnote block
parts[-1] = parts[-1].split("\n _______________")[0]

TITLES = [
    "Preface",
    "The First Evening: The Earth Is a Planet That Turns on Itself and Around the Sun",
    "The Second Evening: The Moon Is an Inhabited Earth",
    "The Third Evening: The World of the Moon, and the Other Planets Inhabited Too",
    "The Fourth Evening: The Worlds of Venus, Mercury, Mars, Jupiter and Saturn",
    "The Fifth Evening: The Fixed Stars Are Suns, Each Lighting a World",
    "The Sixth Evening: New Thoughts, and the Latest Discoveries in the Sky",
]


def clean(t):
    t = t.replace(" ", " ")
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", t)]
    return "\n\n".join(p for p in paras if p) + "\n"


(HERE / "chapters").mkdir(exist_ok=True)
manifest = []
for i, (title, body) in enumerate(zip(TITLES, parts)):
    name = f"{i:03d}.txt"
    text = clean(body)
    (HERE / "chapters" / name).write_text(text)
    manifest.append({"file": name, "title": title, "part": 1, "of": 1,
                     "words": len(text.split())})
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print([m["words"] for m in manifest])
