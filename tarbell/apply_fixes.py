"""Apply the proofreaders' patches: draft/NNN.txt + fixes/NNN.txt -> proof/NNN.txt.

    python3 godel/apply_fixes.py            # every leaf
    python3 godel/apply_fixes.py 63 64      # some leaves; prints each proof

A fixes file is a list of blocks:

    <<<
    exact text from the draft (any length, may span lines)
    ===
    the corrected text
    >>>

Each old text must occur exactly once in the draft as it stands when the
block is applied (blocks apply in order); the build stops otherwise, naming
the leaf and the block. A leaf with no fixes file is copied unchanged.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BLOCK = re.compile(r"<<<\n(.*?)\n===\n(.*?)\n>>>", re.S)


def apply(nn, show=False):
    draft = (HERE / f"draft/{nn:04d}.txt").read_text()
    f = HERE / f"fixes/{nn:04d}.txt"
    text, errors = draft, []
    if f.exists():
        for k, (old, new) in enumerate(BLOCK.findall(f.read_text()), 1):
            n = text.count(old)
            if n != 1:
                errors.append(f"leaf {nn:04d} block {k}: old text found {n} times: {old[:70]!r}")
                continue
            text = text.replace(old, new)
    (HERE / "proof").mkdir(exist_ok=True)
    (HERE / f"proof/{nn:04d}.txt").write_text(text)
    if show:
        print(text)
    return errors


def main():
    leaves = [int(a) for a in sys.argv[1:]] or sorted(int(p.stem) for p in (HERE / "draft").glob("*.txt"))
    errors = []
    for nn in leaves:
        errors += apply(nn, show=len(sys.argv) > 1)
    for e in errors:
        print("ERROR", e, file=sys.stderr)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
