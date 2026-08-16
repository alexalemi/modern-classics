#!/usr/bin/env python3
"""Give every democracy2 file a real title line, and write manifest.json.

WHY THIS EXISTS. The book shipped with no manifest.json, so
assemble.load_manifest fell back to "one file, one section, heading =
the file's first line". Tocqueville's chapters print their number and
their descriptive title on two separate lines, so every heading in the
contents was the number alone: "CHAPTER I." six times over, each
pointing at the first of them. Two files (028, 030) are mechanical
mid-chapter cuts whose first line is a SENTENCE — and strip_front drops
the first line of every file it is given, so those two opening
sentences were being set as contents entries instead of as text.

The fix is in two halves, because assemble takes the heading from the
FILE (m["title"] is only read by the --original build):
  - merge the number line and the title line into one "Chapter I: ..."
    line in the file itself;
  - write a manifest that groups 027+028 and 029+030 into two-part
    chapters, drops the three 1848 Paris title pages, and carries the
    Volume and Part dividers.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"

# The 1848 publisher's title pages ("Pagnerre, Publisher, Rue de Seine,
# 14 bis"), one per printer's tome. They are the French edition's
# furniture, not Tocqueville's text, and site/template.html sets this
# edition's own title page. Left on disk, out of the manifest.
DROP = {"000.txt", "033.txt", "076.txt"}

# Files whose first line is a running head or a bare part label rather
# than a title of their own.
OVERRIDE = {
    "001.txt": "Preface to the Tenth Edition",
    "013.txt": "Introduction to Part Two",
    "103.txt": "Introduction to Part Four",
}
# How many leading lines the override replaces (heading + subtitle).
OVERRIDE_EATS = {"001.txt": 2, "013.txt": 1, "103.txt": 2}

# 027+028 and 029+030 are one chapter each, cut mid-argument. Every other
# cut in this book falls on one of Tocqueville's own titled divisions, so
# these two are the only files that are not sections in their own right.
PARTS = {"027.txt": (1, 2), "028.txt": (2, 2),
         "029.txt": (1, 2), "030.txt": (2, 2)}
CONTINUES = {"028.txt": "027.txt", "030.txt": "029.txt"}

DIVIDERS = {
    "001.txt": "Volume One, Part One",
    "013.txt": "Volume One, Part Two",
    "034.txt": "Volume Two, Part One: The Influence of Democracy on "
               "Intellectual Life in the United States",
    "056.txt": "Volume Two, Part Two: The Influence of Democracy on the "
               "Feelings of the Americans",
    "077.txt": "Volume Two, Part Three: The Influence of Democracy on "
               "Manners Properly So Called",
    "103.txt": "Volume Two, Part Four: The Influence of Democratic Ideas "
               "and Feelings on Political Society",
}

CHAPTER = re.compile(r"CHAPTER ([IVXLC]+)\.?$")
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
         "into", "of", "on", "or", "over", "the", "to", "upon", "with"}


def titlecase(s):
    """Normalise a title to Title Case, whatever case it arrives in.

    The four tomes were translated at different times and disagree: tomes
    1 and 2 print their titles in capitals, tomes 3 and 4 in ordinary
    sentence case ("Why Americans are more attached to the practical"),
    and a contents list that mixes the two reads as a mistake. An
    all-caps title is rebuilt from scratch; any other is touched only
    where a word is entirely lower case, so proper nouns keep whatever
    the translation gave them.
    """
    s = s.strip().rstrip(".")
    words = s.split()
    upper = s.isupper()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        first = i == 0 or i == len(words) - 1 or out[-1].endswith(":")
        if low in SMALL and not first:
            out.append(low if upper else w)
        elif upper or w.islower():
            # a hyphenated compound capitalises both halves:
            # "Anglo-Americans", not "Anglo-americans"
            src = low if upper else w
            out.append("-".join(p[:1].upper() + p[1:]
                                for p in src.split("-")))
        else:
            out.append(w)
    return " ".join(out)


def head_lines(text):
    """Indices of the first two non-blank lines."""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()][:2]
    return lines, idx


def retitle(name):
    """Rewrite one file's opening; return its heading line."""
    path = MOD / name
    lines, idx = head_lines(path.read_text())
    first = lines[idx[0]].strip()
    second = lines[idx[1]].strip() if len(idx) > 1 else ""

    if name in OVERRIDE:
        title = OVERRIDE[name]
        eat = idx[:OVERRIDE_EATS[name]]
    elif name in CONTINUES:
        # a mechanical cut: the file opens on prose and must NOT lose it
        title = None
        eat = []
    elif (m := CHAPTER.match(first)) and second and len(second) < 200:
        title = f"Chapter {m.group(1)}: {titlecase(second)}"
        eat = idx[:2]
    else:
        title = titlecase(first)
        eat = idx[:1]

    return path, lines, eat, title


def main():
    names = sorted(p.name for p in MOD.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    heads, plan = {}, {}
    for n in names:
        if n in DROP:
            continue
        plan[n] = retitle(n)
        heads[n] = plan[n][3]
    # a part 2 repeats its chapter's heading, then the part marker
    for n, parent in CONTINUES.items():
        heads[n] = heads[parent]

    for n, (path, lines, eat, title) in plan.items():
        keep = [l for i, l in enumerate(lines) if i not in eat]
        head = [heads[n]]
        if n in PARTS:
            head.append("(Part {} of {})".format(*PARTS[n]))
        path.write_text("\n".join(head + [""] + keep).lstrip("\n"))

    manifest = []
    for n in sorted(plan):
        part, of = PARTS.get(n, (1, 1))
        entry = {"file": n, "title": heads[n], "part": part, "of": of,
                 "words": len((MOD / n).read_text().split())}
        if n in DIVIDERS:
            entry["part_before"] = DIVIDERS[n]
        manifest.append(entry)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    chapters = sum(1 for m in manifest if m["part"] == 1)
    print(f"{len(manifest)} files, {chapters} sections, "
          f"{sum(m['words'] for m in manifest):,} words")
    for m in manifest:
        if m.get("part_before"):
            print(f"  divider before {m['file']}: {m['part_before'][:60]}")


if __name__ == "__main__":
    main()
