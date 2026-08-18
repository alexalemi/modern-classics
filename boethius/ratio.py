"""Word-count ratio per translated file. Same measure verify.py applies,
but runnable mid-book while modern_chapters/ is still incomplete."""
import pathlib
import sys

src = pathlib.Path("boethius/chapters")
mod = pathlib.Path("boethius/modern_chapters")
names = sys.argv[1:] or sorted(p.stem for p in mod.glob("*.txt"))
for n in names:
    a = len((src / f"{n}.txt").read_text().split())
    b = len((mod / f"{n}.txt").read_text().split())
    print(f"{n}: {a} -> {b}  ratio {b/a:.2f}")
