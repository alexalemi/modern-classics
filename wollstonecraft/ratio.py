"""Per-file word ratios, so progress is visible while translating."""
import pathlib
import sys

BOOK = pathlib.Path(__file__).resolve().parent
tot_s = tot_m = 0
for p in sorted((BOOK / "chapters").glob("*.txt")):
    q = BOOK / "modern_chapters" / p.name
    s = len(p.read_text().split())
    if not q.exists():
        print(f"  {p.name}  {s:6d}  --")
        continue
    m = len(q.read_text().split())
    tot_s += s
    tot_m += m
    flag = "" if 0.85 <= m / s <= 1.15 else "   <-- OUT OF BAND"
    print(f"  {p.name}  {s:6d} -> {m:6d}  {m/s:.3f}{flag}")
if tot_s:
    print(f"\n{tot_s:,} -> {tot_m:,} words, ratio {tot_m/tot_s:.3f}")
