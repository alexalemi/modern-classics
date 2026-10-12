"""Per-book checks for solferino/ that verify.py cannot make.

    python3 books/solferino/check.py

There is no English crib, so these are the only second witness:
  1. footnote parity: every "NOTE n:" paragraph in chapters/NNN.txt has an
     "Author's note:" paragraph in modern_chapters/NNN.txt (same count);
  2. no "[n]" note markers left in the modern text;
  3. numeral diff: every digit-string in the source file appears in the
     modern file (numbers the French spells out are not covered);
  4. the locked false friend: "ambulance" never appears in English.
Exits nonzero on failure.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
NUM = re.compile(r"\d[\d,]*\d|\d")

def nums(text):
    return {n.replace(",", "") for n in NUM.findall(text)}


def main():
    bad = 0
    for src in sorted((HERE / "chapters").glob("*.txt")):
        mod = HERE / "modern_chapters" / src.name
        s, m = src.read_text(), mod.read_text()
        sn = len(re.findall(r"^NOTE \d+:", s, re.M))
        mn = len(re.findall(r"^Author's note:", m, re.M))
        if sn != mn:
            print(f"{src.name}: {sn} source notes, {mn} modern notes")
            bad += 1
        if re.search(r"\[\d+\]", m):
            print(f"{src.name}: note marker left in modern text")
            bad += 1
        if re.search(r"\bambulance", m, re.I):
            print(f"{src.name}: 'ambulance' in English text")
            bad += 1
        s_body = re.sub(r"\[\d+\]|^NOTE \d+:", "", s, flags=re.M)
        missing = nums(s_body) - nums(m)
        if missing:
            print(f"{src.name}: numerals missing from modern: {sorted(missing)}")
            bad += 1
    print("all checks passed" if not bad else f"{bad} failure(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
