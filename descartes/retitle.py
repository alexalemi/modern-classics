#!/usr/bin/env python3
"""Give every descartes file its own title line, and write manifest.json.

The book collects three works, and every file opens with the WORK on
line one and the SECTION on line two. With no manifest.json,
assemble.load_manifest fell back to "heading = the file's first line",
so the contents read "DISCOURSE ON THE METHOD" seven times, "MEDITATIONS
ON THE FIRST PHILOSOPHY" nine and "PRINCIPLES OF PHILOSOPHY" six -- 19
of 23 entries duplicates of each other, and every one of them a link to
the first of its kind.

The work belongs in a part divider, which is exactly what manifest
"part_before" is for; the section title belongs in the heading. So the
fix is to drop line one from each file and let line two stand as the
heading assemble already reads.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"

DIVIDERS = {
    "000.txt": "Discourse on the Method",
    "007.txt": "Meditations on the First Philosophy",
    "016.txt": "Principles of Philosophy",
    "022.txt": "Appendix",
}

# The appendix is the geometrical demonstration from the Second Replies,
# and neither the source nor Veitch gives it a heading beyond "APPENDIX".
# Named for what is actually in it rather than given a title out of the
# scholarship, and its own "DEFINITIONS" line is left in the body, where
# it reads as the first of the four subheadings it belongs with.
OVERRIDE = {"022.txt": "Definitions, Postulates, Axioms and Propositions"}

# ROMAN PART NUMBERS GO TO WORD FORM, AND NOT FOR CONSISTENCY'S SAKE.
# assemble.strip_front skips any line matching PART_LINE (^Part [IVXLC0-9]+:
# \S) while it is reading a file's front matter -- before the heading and
# after it alike, because a translation may write its own part divider on
# either side. The four Parts of the Principles of Philosophy are titled in
# exactly that shape, so every one of them was being read as a divider and
# DELETED: the shipped page had four sections titled "PRINCIPLES OF
# PHILOSOPHY" and the words "Of the Principles of Human Knowledge" appeared
# nowhere on it. "Part One:" does not match the pattern, and word form is
# this project's house style for cross-references anyway.
WORD = {"I": "One", "II": "Two", "III": "Three",
        "IV": "Four", "V": "Five", "VI": "Six"}
ROMAN = re.compile(r"^Part ([IVX]+)\b")


def main():
    names = sorted(p.name for p in MOD.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    manifest = []
    for n in names:
        path = MOD / n
        lines = path.read_text().split("\n")
        i = next(j for j, l in enumerate(lines) if l.strip())
        title = OVERRIDE.get(n) or lines[i + 1].strip()
        title = ROMAN.sub(lambda m: f"Part {WORD[m.group(1)]}", title)
        if n in OVERRIDE:
            lines[i] = title                      # replace the work line
        else:
            del lines[i]                          # drop it; line two heads
            lines[i] = title
        path.write_text("\n".join(lines).lstrip("\n"))

        entry = {"file": n, "title": title, "part": 1, "of": 1,
                 "words": len(path.read_text().split())}
        if n in DIVIDERS:
            entry["part_before"] = DIVIDERS[n]
        manifest.append(entry)

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(manifest)} sections, "
          f"{sum(m['words'] for m in manifest):,} words")
    for m in manifest:
        print(f"  {'* ' + m['part_before'] if m.get('part_before') else ''}"
              f"\n    {m['title']}" if m.get("part_before")
              else f"    {m['title']}")


if __name__ == "__main__":
    main()
