"""Give every modern chapter the heading line its source file has.

assemble.strip_front takes the first non-blank line of a file as that
section's heading and drops it. The source files carry their heading
because prep.py writes it; the translations were written before that
was true, so each needs the manifest title prepended once.

Idempotent: a file that already opens with its title is left alone.
"""
import json
import pathlib
import sys

BOOK = pathlib.Path(__file__).resolve().parent
manifest = json.loads((BOOK / "manifest.json").read_text())

changed = 0
for m in manifest:
    p = BOOK / "modern_chapters" / m["file"]
    if not p.exists():
        continue
    t = p.read_text()
    first = t.lstrip("\n").split("\n", 1)[0].strip()
    if first == m["title"]:
        continue
    p.write_text(m["title"] + "\n\n" + t.lstrip("\n"))
    changed += 1
    print(f"  {m['file']}: prepended {m['title']!r}")

print(f"{changed} file(s) retitled")
sys.exit(0)
