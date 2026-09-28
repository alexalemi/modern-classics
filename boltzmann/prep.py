"""Ludwig Boltzmann, "Reise eines deutschen Professors ins Eldorado" (1905),
from Populäre Schriften (Leipzig: Barth, 1905), pp. 403-435.

    python3 boltzmann/prep.py

Source: Archive.org populreschrifte00boltgoog, the scan's OCR (roman type,
clean). source/eldorado.txt is the essay cut from it, with running heads,
folios and signatures removed, line-end hyphens joined, and paragraphs the
page breaks had split rejoined (a paragraph ending without a stop runs on).
The essay has no divisions of its own; it is split at paragraph boundaries
into three parts of about 3,600 words for translation.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from splitter import split_paragraphs  # noqa: E402

TITLE = "A German Professor's Journey into Eldorado"
body = (HERE / "source" / "eldorado.txt").read_text().strip()
parts = split_paragraphs(body, 3)
(HERE / "chapters").mkdir(exist_ok=True)
manifest = []
for j, part in enumerate(parts, 1):
    fn = f"{j - 1:03d}.txt"
    (HERE / "chapters" / fn).write_text(f"{TITLE}\n(PART {j} OF 3)\n\n{part}\n")
    manifest.append({"file": fn, "title": TITLE, "part": j, "of": 3, "words": len(part.split())})
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
print([m["words"] for m in manifest])
