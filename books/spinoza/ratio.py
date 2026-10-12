"""Per-file word ratio, source against translation."""
import pathlib
import sys

BOOK = pathlib.Path(__file__).resolve().parent
args = sys.argv[1:]
names = [f"{a.zfill(3)}.txt" for a in args] if args else \
    sorted(p.name for p in (BOOK / "modern_chapters").glob("*.txt"))

tot_s = tot_m = 0
for n in names:
    s = BOOK / "chapters" / n
    m = BOOK / "modern_chapters" / n
    if not m.exists():
        continue
    a, b = len(s.read_text().split()), len(m.read_text().split())
    tot_s += a
    tot_m += b
    flag = "" if 0.85 <= b / a <= 1.15 else "   <-- outside 0.85-1.15"
    print(f"{n}: {a:>6,} -> {b:>6,}  ratio {b / a:.2f}{flag}")
if tot_s:
    print(f"\ntotal: {tot_s:,} -> {tot_m:,}  ratio {tot_m / tot_s:.2f} "
          f"({len(names)} files)")
