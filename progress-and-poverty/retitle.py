#!/usr/bin/env python3
"""Strip the subheadings George never wrote, retitle every file, and
write manifest.json.

THE INVENTED SUBHEADINGS. The February batches broke George's chapters
up with about 340 headings of their own -- "The Whaling Ship", "The Egg
Gatherers of the Farallon Islands", "Bastiat's Plane: A Closer Look",
"The 'Abstinence' Theory Doesn't Work" -- each set as an <h4>, and
unevenly: many in 003-035 and 043-044, none at all in 036-042. George
wrote subheadings in exactly two chapters, both as a Roman ordinal over
a title (the Standard Ebooks source's <h4> + title hgroup):
  Book VI ch. 1 (025): I From Greater Economy in Government ... VI
  Book VIII ch. 3 (034): I The Effect of Taxes Upon Production ... IV
So the rule is structural: a body paragraph that the renderer would set
as a heading (assemble.is_subheading) survives only if it is a Roman
ordinal that the SOURCE file also carries as a body subheading, or the
title directly after one. Everything else in that shape is removed. The
ordinal and title are merged into one line ("I. From Cooperation") so
they render as one heading, not two stacked ones. The script asserts
that the surviving count equals the source's, file by file.

THE TITLES. With no manifest.json, assemble took each file's first line
as its heading: "Book IX, Chapter 1: How the Remedy Would Boost the
Production of Wealth" -- every chapter a top-level section, the Book
named in every entry, and Book IX retitled in modern paraphrase. Most
files then repeated the chapter number ("I") and title on the next two
lines. The heading now comes from George's own title in chapters/
("Chapter 1: Of the Effect Upon the Production of Wealth"), Arabic so
that assemble.CHAP_LINE nests it under its Book, and the Books become
part dividers. The repeated number/title lines are dropped.

Idempotent: a second run changes nothing.
"""
import difflib
import json
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT))
import assemble  # noqa: E402

SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

# George's ten Books (Gutenberg contents, pg55308.txt), keyed by the file
# that opens each one
BOOKS = {
    "002.txt": "Book I: Wages and Capital",
    "007.txt": "Book II: Population and Subsistence",
    "011.txt": "Book III: The Laws of Distribution",
    "019.txt": "Book IV: Effect of Material Progress Upon the "
               "Distribution of Wealth",
    "023.txt": "Book V: The Problem Solved",
    "025.txt": "Book VI: The Remedy",
    "027.txt": "Book VII: Justice of the Remedy",
    "032.txt": "Book VIII: Application of the Remedy",
    "036.txt": "Book IX: Effects of the Remedy",
    "040.txt": "Book X: The Law of Human Progress",
}
# sections that stand outside the Books, titled as George titled them
FIXED = {
    "000.txt": "Preface to the Fourth Edition",
    "001.txt": "Introductory: The Problem",
    "045.txt": "Conclusion: The Problem of Individual Life",
}
# 034's ordinals II-IV are "As to ...", which the translation dropped,
# leaving bare one-word headings ("Certainty"); George's wording back
SUBHEAD_FIX = {
    "Ease and Cheapness of Collection": "As to Ease and Cheapness of Collection",
    "Certainty": "As to Certainty",
    "Equality": "As to Equality",
}
ROMAN = re.compile(r"^[IVXL]+$")
MERGED = re.compile(r"^([IVXL]+)\. (.+)$")
BOOK_CH = re.compile(r"^Book [IVX]+, Chapter (\d+): ")


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def heading_like(p):
    return assemble.is_subheading(p) and not assemble.HR_LINE.fullmatch(p)


def dash(s):
    return re.sub(r"\s*—\s*", " — ", s)


def source_info(name):
    """(chapter number or None, George's title, body subhead ordinals)."""
    pars = paragraphs((SRC / name).read_text())
    m = BOOK_CH.match(pars[0])
    num = int(m.group(1)) if m else None
    # pars: [file heading + "=====" underline, ordinal, title, body...]
    title = dash(pars[2]) if m else None
    body = pars[3:] if m else pars[2:]
    ords = [p for p in body if ROMAN.fullmatch(p)]
    return num, title, ords


def similar(a, b):
    a, b = a.lower(), b.lower()
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.6 or \
        a.startswith(b[:25]) or b.startswith(a[:25])


def main():
    manifest, report = [], []
    for path in sorted(MOD.glob("[0-9][0-9][0-9].txt")):
        name = path.name
        num, src_title, src_ords = source_info(name)
        title = FIXED.get(name) or f"Chapter {num}: {src_title}"
        pars = paragraphs(path.read_text())

        # the front: old heading, "=====" underline, ordinal, repeated title
        bare = title.split(": ", 1)[-1]
        rest = pars[1:]
        while rest and (set(rest[0]) <= {"="} or ROMAN.fullmatch(rest[0])
                        or (heading_like(rest[0]) and similar(rest[0], bare))):
            rest = rest[1:]

        out, kept, dropped = [], [], []
        want = list(src_ords)
        i = 0
        while i < len(rest):
            p = rest[i]
            m = MERGED.match(p)
            if m and m.group(1) in want:          # already merged (rerun)
                want.remove(m.group(1))
                kept.append(p)
                out.append(p)
            elif ROMAN.fullmatch(p) and p in want:
                want.remove(p)
                sub = rest[i + 1] if i + 1 < len(rest) else ""
                if heading_like(sub):
                    sub = SUBHEAD_FIX.get(sub, sub)
                    p = f"{p}. {sub}"
                    i += 1
                kept.append(p)
                out.append(p)
            elif heading_like(p):
                dropped.append(p)
            else:
                out.append(p)
            i += 1
        assert len(kept) == len(src_ords), (name, kept, src_ords)

        path.write_text("\n\n".join([title] + out) + "\n")
        entry = {"file": name, "title": title, "part": 1, "of": 1,
                 "words": len(path.read_text().split())}
        if name in BOOKS:
            entry["part_before"] = BOOKS[name]
        manifest.append(entry)
        report.append((name, len(kept), dropped))

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name, k, d in report:
        if k or d:
            print(f"{name}: kept {k}, dropped {len(d)}")
    print(f"TOTAL kept {sum(r[1] for r in report)}, "
          f"dropped {sum(len(r[2]) for r in report)}")
    if "-v" in sys.argv:
        for name, _, d in report:
            for p in d:
                print(f"  {name} - {p}")


if __name__ == "__main__":
    main()
