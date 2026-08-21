import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S

parts = dict(S.split_parts(S.body()))
WANT = [
    (2, "PROP. XI.", "by the same Axiom"),
    (2, "PROP. XLI.", "in the foregoing note"),
    (3, None, "by the foregoing definition"),
    (5, "PROP. XXXIII.", "by the same Axiom"),
]
for part, anchor, phrase in WANT:
    t = parts[part]
    start = t.find(anchor) if anchor else 0
    i = t.find(phrase, start)
    if i < 0:
        i = t.find(phrase)
    print("=" * 70)
    print(f"PART {part}  ({phrase})")
    print("=" * 70)
    print(re.sub(r"\n{3,}", "\n\n", t[max(0, i - 1100):i + 200]).strip())
    print()
