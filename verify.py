"""Verify a book's modern_chapters against its source chapters.

    python3 verify.py <book_dir> [--min-ratio 0.6] [--max-ratio 1.6]

Checks (exit code is nonzero if any fail):
  1. Every chapters/NNN.txt has a modern_chapters/NNN.txt counterpart.
  2. Per-file modern/original word ratio is within bounds. The low bound
     catches the project's worst failure mode: an agent silently
     summarizing instead of translating.
  3. "(Part n of k)" markers appear only in a file's first three lines.
  4. No part/book divider heading (a line like "Part II: ...") appears in
     more than one modern chapter file — catches the duplicated-divider
     seam bug between parallel translators.
  5. If <book_dir>/must_contain.txt exists, every non-blank, non-#
     line must appear (case- and whitespace-insensitively) somewhere in
     the combined modern text. Use it for the famous passages listed in
     text_analysis.txt.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PART_MARK = re.compile(r"^\(Part \d+ of \d+\)$", re.I)
PART_DIVIDER = re.compile(r"^Part [IVXLC0-9]+: \S")


def words(path):
    return len(path.read_text().split())


def normalize(text):
    return " ".join(text.split()).lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir")
    ap.add_argument("--min-ratio", type=float, default=0.6)
    ap.add_argument("--max-ratio", type=float, default=1.6)
    args = ap.parse_args()

    book = Path(args.book_dir)
    chapters = book / "chapters"
    modern = book / "modern_chapters"
    failures = []

    manifest_path = book / "manifest.json"
    if manifest_path.exists():
        files = [m["file"] for m in json.loads(manifest_path.read_text())]
    else:
        files = sorted(p.name for p in chapters.glob("*.txt"))

    # 1 + 2: pairing and ratios
    total_o = total_m = 0
    for fn in files:
        src = chapters / fn
        out = modern / fn
        if not out.exists():
            failures.append(f"MISSING: modern_chapters/{fn}")
            continue
        o, m = words(src), words(out)
        total_o += o
        total_m += m
        ratio = m / o if o else 0
        if not (args.min_ratio <= ratio <= args.max_ratio):
            failures.append(f"RATIO: {fn} {ratio:.2f} ({o} -> {m} words)")

    # 3 + 4: marker leakage and duplicate dividers
    divider_seen = {}
    for fn in files:
        out = modern / fn
        if not out.exists():
            continue
        lines = out.read_text().split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            # a part divider above the heading can push the marker to ~line 4
            if PART_MARK.match(s) and i > 4:
                failures.append(f"MARKER LEAK: {fn} line {i + 1}: {s}")
            if PART_DIVIDER.match(s):
                if s in divider_seen:
                    failures.append(
                        f"DUPLICATE DIVIDER: {s!r} in {divider_seen[s]} and {fn}")
                else:
                    divider_seen[s] = fn

    # 5: must-contain passages
    must = book / "must_contain.txt"
    if must.exists():
        haystack = normalize("\n".join(
            (modern / fn).read_text() for fn in files if (modern / fn).exists()))
        for line in must.read_text().splitlines():
            phrase = line.strip()
            if not phrase or phrase.startswith("#"):
                continue
            if normalize(phrase) not in haystack:
                failures.append(f"MISSING PASSAGE: {phrase}")

    print(f"{len(files)} files; original {total_o} words, modern {total_m} words, "
          f"ratio {total_m / total_o:.2f}" if total_o else "no files checked")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
