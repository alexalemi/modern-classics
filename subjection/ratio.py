"""Word-count ratio per translated file, runnable mid-book while
modern_chapters/ is still incomplete and verify.py would fail on the
files that do not exist yet."""
import pathlib
import sys

BOOK = pathlib.Path(__file__).resolve().parent
names = sys.argv[1:] or sorted(p.stem for p in
                               (BOOK / "modern_chapters").glob("*.txt"))
for n in names:
    a = len((BOOK / "chapters" / f"{n}.txt").read_text().split())
    b = len((BOOK / "modern_chapters" / f"{n}.txt").read_text().split())
    print(f"{n}: {a} -> {b}  ratio {b/a:.2f}")
