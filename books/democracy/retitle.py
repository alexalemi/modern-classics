#!/usr/bin/env python3
"""Group democracy's split chapters and write manifest.json.

With no manifest.json, assemble.load_manifest fell back to "one file,
one section, heading = the file's first line". Eighteen of Tocqueville's
chapters are long enough that the splitter cut them into two to ten
files, and the source names every piece ("Chapter VIII: The Federal
Constitution-Part IV"), so the grouping is fully derivable from it.

FIVE OF THOSE PIECES OPEN ON A SENTENCE in the translation, and
strip_front drops the first line of every file it is given: five
opening sentences were being set as contents entries instead of as
text. Four more opened on one of Tocqueville's own subsection titles,
which was being promoted to a chapter heading and detached from the
chapter it belongs to -- the contents listed "The Legislative Branch"
and "Re-election of the President" as though they were chapters of the
book.

Each group now carries its chapter's heading and a part marker, and
whatever the file opened with stays in the body where it belongs. 119
files become 91 sections.

The four Book headings become part dividers, and take the Volume/Part
form used by the from-the-French edition in democracy2/ -- the
transcription's own numbering is broken (its four divisions of the
second volume are labelled "Book Two", "Section 2", "Book Three" and
"Book Four"), and the two editions of one work should not disagree
about how many parts it has.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"

HEAD = re.compile(r"^Chapter ([IVXLC]+): (.*?)(?:—Part ([IVXLC]+))?$")
ROMAN = {r: i for i, r in enumerate(
    "I II III IV V VI VII VIII IX X".split(), 1)}

DIVIDERS = {
    "000.txt": "Volume One",
    "043.txt": "Volume Two, Part One: The Influence of Democracy on "
               "Intellectual Life in the United States",
    "065.txt": "Volume Two, Part Two: The Influence of Democracy on the "
               "Feelings of the Americans",
    "085.txt": "Volume Two, Part Three: The Influence of Democracy on "
               "Manners Properly So Called",
    "111.txt": "Volume Two, Part Four: The Influence of Democratic "
               "Opinions on Political Society",
}
# (title, how many leading non-blank lines it replaces) for the files
# that open on a Book label rather than on a chapter of their own.
OPENERS = {
    "000.txt": ("Introductory Chapter", 2),
    "043.txt": ("Tocqueville's Preface to the Second Volume", 4),
    "065.txt": ("Chapter I: Why Democratic Nations Love Equality More "
                "Passionately Than Freedom", 3),
    "085.txt": ("Chapter I: How Equality Softens Social Behavior", 3),
    "111.txt": ("Chapter I: Equality Naturally Makes People Want Free "
                "Institutions", 3),
}

# A section title the translation wrapped in asterisks. The pipeline is
# markup-free -- structure comes from convention alone -- so these ship
# as literal asterisks on the page. Only TITLE lines are unwrapped here;
# emphasis inside prose is left alone, since stripping it would throw
# away the only record of where the author's emphasis falls.
TITLE_STAR = re.compile(r"^\*(.+)\*$")

# The translation carried the source's mechanical part labels into some
# of its titles ("... -- Part I"). The manifest holds the part number
# now, so the title should not repeat it.
TITLE_PART = re.compile(r"\s*(?:--|—)\s*Part [IVXLC]+\s*$")


def source_parts():
    """file -> (chapter key, part number) from the source headings."""
    out, book = {}, 0
    for f in sorted(SRC.glob("*.txt")):
        if not re.fullmatch(r"\d{3}\.txt", f.name):
            continue
        # THE HEADING CAN WRAP. Four of Chapter XVII's parts and the
        # first of Chapter XVIII's print "...Democratic" on one line and
        # "Republic-Part III" on the next, so a first-line-only read
        # loses the part number and collapses the whole chapter into a
        # single part 1 -- silently, since every file still appears.
        # The heading is the first PARAGRAPH.
        para = []
        for l in f.read_text().split("\n"):
            if not l.strip():
                if para:
                    break
                continue
            para.append(l.strip())
        head = " ".join(para)
        if f.name in DIVIDERS:
            book += 1
        m = HEAD.match(head)
        if not m:
            out[f.name] = (f"front{book}", 1)
            continue
        out[f.name] = ((book, m.group(1)), ROMAN[m.group(3)] if m.group(3)
                       else 1)
    return out


def main():
    parts = source_parts()
    order = sorted(parts)
    sizes = {}
    for name in order:
        key, _ = parts[name]
        sizes[key] = sizes.get(key, 0) + 1

    manifest = []
    for name in order:
        key, part = parts[name]
        of = sizes[key]
        path = MOD / name
        lines = path.read_text().split("\n")
        idx = [i for i, l in enumerate(lines) if l.strip()]

        if name in OPENERS:
            title, eat = OPENERS[name]
            lines = [l for i, l in enumerate(lines) if i not in idx[:eat]]
            head = [title]
        elif part == 1:
            title = TITLE_PART.sub(
                "", TITLE_STAR.sub(r"\1", lines[idx[0]].strip()))
            lines = [l for i, l in enumerate(lines) if i != idx[0]]
            head = [title]
        else:
            # a continuation: whatever it opens with is BODY, not a
            # heading, so the chapter's own heading is prepended above it
            title = manifest[-1]["title"]
            head = [title]
        if of > 1:
            head.append(f"(Part {part} of {of})")
        path.write_text("\n".join(head + [""] + lines).lstrip("\n"))

        entry = {"file": name, "title": title, "part": part, "of": of,
                 "words": len(path.read_text().split())}
        if name in DIVIDERS:
            entry["part_before"] = DIVIDERS[name]
        manifest.append(entry)

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(manifest)} files, "
          f"{sum(1 for m in manifest if m['part'] == 1)} sections, "
          f"{sum(m['words'] for m in manifest):,} words")


if __name__ == "__main__":
    main()
