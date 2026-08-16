#!/usr/bin/env python3
"""Give every Two Treatises file a title line, and write manifest.json.

With no manifest.json, assemble.load_manifest took each file's first
line as its heading, and the file's first line is the chapter NUMBER --
in five different shapes, because the batches disagreed: "BOOK I",
"CHAPTER II", a bare "III", and twice a properly merged "Chapter 4: Of
Slavery". The contents list read "BOOK II", "CHAPTER V", "VI", "XI" and
four bare Roman numerals, with the descriptive title stranded on the
line below as a subheading.

Number and title are merged into one "Chapter N: ..." line -- Arabic,
which is what assemble.CHAP_LINE recognises -- and the two treatises
become part dividers. Locke's first chapter in each treatise carries no
title, and keeps none.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

DIVIDERS = {
    "001.txt": "The First Treatise: The False Principles and Foundation "
               "of Sir Robert Filmer",
    "012.txt": "The Second Treatise: An Essay Concerning the True "
               "Original, Extent, and End of Civil Government",
}
ROMAN = {r: i for i, r in enumerate(
    "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII "
    "XIX XX".split(), 1)}

# every shape the five batches used for a bare chapter number
NUMBER = re.compile(r"^(BOOK [IVX]+|CHAPTER [IVX]+|[IVX]+|Chapter \d+)$",
                    re.I)
MERGED = re.compile(r"^Chapter \d+: ")


def main():
    manifest = []
    for path in sorted(MOD.glob("*.txt")):
        name = path.name
        if not re.fullmatch(r"\d{3}\.txt", name):
            continue
        lines = path.read_text().split("\n")
        idx = [i for i, l in enumerate(lines) if l.strip()]

        if name == "000.txt":
            title, eat = "Preface", 1
        else:
            roman = next(l.strip() for l in
                         (SRC / name).read_text().split("\n") if l.strip())
            n = ROMAN[roman]
            eat = 0
            while eat < len(idx) and NUMBER.match(lines[idx[eat]].strip()):
                eat += 1
            nxt = lines[idx[eat]].strip() if eat < len(idx) else ""
            if MERGED.match(nxt):
                title, eat = nxt, eat + 1
            elif nxt and len(nxt) < 90 and not nxt.endswith((".", ":", "!")) \
                    and nxt[0].isupper():
                # the descriptive title, stranded on its own line
                title, eat = f"Chapter {n}: {nxt}", eat + 1
            else:
                # Locke's opening chapter in each treatise is untitled
                title = f"Chapter {n}"

        keep = [l for i, l in enumerate(lines) if i not in idx[:eat]]
        path.write_text("\n".join([title, ""] + keep).lstrip("\n"))

        entry = {"file": name, "title": title, "part": 1, "of": 1,
                 "words": len(path.read_text().split())}
        if name in DIVIDERS:
            entry["part_before"] = DIVIDERS[name]
        manifest.append(entry)

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(manifest)} sections, "
          f"{sum(m['words'] for m in manifest):,} words")
    for m in manifest:
        if m.get("part_before"):
            print("##", m["part_before"][:60])
        print("  ", m["title"][:70])


if __name__ == "__main__":
    main()
