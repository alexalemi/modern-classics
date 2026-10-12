#!/usr/bin/env python3
"""Strip the paragraph (section) numbers the translation invented.

The Standard Ebooks source prints no section numbers, but ten of the
31 modern files (001, 013, 021, 023-025, 027-030) opened paragraphs with
"N. " -- and the numbering drifted: 030 ran one behind from "So much for
the great advocate" on, 027 ended at 197 where 028 began at 197, and
029 stopped at 208, short of Locke's 210. A wrong section number is
worse than none, and the other 21 files carry none, so they all go.

Locke's OWN numbered lists survive: 004 ("1. That this donation...",
"2. Whatever God gave...") and 011 ("1. Because it will be but an ill
example...", "2. Because this place..."). A leading number is kept only
when the source file has a paragraph opening on that same number.

Idempotent: a second run changes nothing.
"""
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"
NUM = re.compile(r"^(\d{1,3})\. (?=\S)")


def main():
    total = 0
    for path in sorted(MOD.glob("[0-9][0-9][0-9].txt")):
        src_nums = {m.group(1) for line in
                    (SRC / path.name).read_text().split("\n")
                    if (m := NUM.match(line))}
        lines = path.read_text().split("\n")
        n = 0
        for i, line in enumerate(lines):
            m = NUM.match(line)
            if m and m.group(1) not in src_nums:
                lines[i] = line[m.end():]
                n += 1
        if n:
            path.write_text("\n".join(lines))
            print(f"{path.name}: stripped {n}")
            total += n
    print(f"total stripped: {total}")


if __name__ == "__main__":
    main()
