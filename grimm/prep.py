#!/usr/bin/env python3
"""Grimm's Household Tales (Margaret Hunt, 1884) -> chapters/ + manifest.json

    python3 grimm/prep.py

THE SOURCE IS THE CLEANEST IN THE PROJECT and the shape is unusual: 200
short self-contained tales plus 10 Children's Legends, none of them
chapters of anything. Two consequences drive the whole design.

1. TALES ARE GROUPED INTO FILES, NOT GIVEN ONE FILE EACH. The median tale
   is ~900 words and the smallest is 131, so a file per tale would mean 210
   files, most of them trivial, and 210 round trips to translate. Instead
   each file carries whole tales up to ~3,600 words, and the manifest entry
   lists their titles in "split_headings" -- which assemble.build_sections
   uses to carve one file into several standalone sections, each with its
   own TOC entry. build_ebook.load_sections calls the same function, so the
   epub gets the same structure for free.

   TWO TRAPS IN THAT MECHANISM, both silent:
     - re.split on the heading pattern DISCARDS whatever precedes the first
       heading, so a file MUST begin exactly with its first tale's title
       line. prep asserts this; check.py asserts it of the translation.
     - the split is on `^(exact title)$`, so a translated title that drifts
       by one character loses its section AND welds its tale onto the
       previous one. The titles are therefore fixed here, carried in the
       manifest, and checked rather than retyped.

2. ONE TALE IS TOO BIG FOR A FILE. "The Two Brothers" (60) runs 8,568
   words; a few others approach 4,000. A tale over MAX gets a file group of
   its own, split into "(Part n of k)" parts at paragraph boundaries in the
   ordinary way, with no split_headings -- assemble handles both shapes,
   since groups are formed by part == 1.

VERSE IS NOT INDENTED IN THE SOURCE. Grimm's rhymes ("Flounder, flounder
in the sea, / Come, I pray thee, here to me") arrive as ordinary blocks of
short lines. They are detected by line length and re-emitted TAB-INDENTED,
which is this project's only verse convention. Getting this wrong turns
every rhyme in the book into prose -- the same defect the Nights hit with
545 hemistichs.
"""
import json
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source" / "pg5314.txt"
OUT = BOOK / "chapters"

TARGET, MAX = 3600, 4300      # words per file; a tale is never cut to fit
VERSE_LINE = 58               # a line shorter than this may be verse

# The contents list repeats every title, so the body begins after its last
# entry. Anchored on the final legend rather than on a count.
CONTENTS_END = "Legend 10 The Hazel Branch (Die Haselrute)"

# A STAR IS PART OF THE TALE NUMBER, and dropping it loses a whole tale.
# The Grimms' final edition numbers 1-200 but contains 201 numbered tales,
# because "The Twelve Idle Servants" is 151* -- an extra hung on 151, "The
# Three Sluggards". Written \d{1,3} this heading never matched, so the tale
# was never a section: its text rode through the pipeline inside its
# neighbour's file and rendered as a stray paragraph with no title and no
# TOC entry. NOTHING in verify.py or check.py could see it -- the words are
# all present, the ratio does not move, and check.py compares the manifest
# against the FILES, so a heading missing from both agrees with itself.
# Only counting against the source's own contents list finds it: see
# assert_tale_count below.
TALE = re.compile(r"\n[ \t]*(\d{1,3}\*?)[ \t]+([A-Z][^\n]{2,70})\n")
LEGEND = re.compile(r"\n[ \t]*Legend (\d{1,2})[ \t]+([A-Z][^\n]{2,70})\n")

# Hunt's own printing errors, corrected with the assertion that keeps a
# correction honest: if the misprint ever leaves the source, the build stops
# rather than silently applying nothing.
SOURCE_FIXES = []

# TITLES ARE FIXED HERE AND NOWHERE ELSE. split_headings matches on the
# exact line, so the same string has to appear in chapters/, in
# modern_chapters/ and in the manifest; deciding them in one place is what
# stops a translated title from drifting by a character and silently
# welding its tale onto the one before. Only spellings a modern reader
# would read as errors are touched -- Hunt's titles are otherwise good, and
# her Grimm titles (Little Red-Cap, Briar-Rose) are kept over the more
# familiar French-derived ones.
TITLE_FIXES = {
    "Hansel and Grethel": "Hansel and Gretel",
    "Clever Grethel": "Clever Gretel",
    "Little Snow-white": "Little Snow-White",
}


def clean(t):
    for a, b in [(" ", " "), (" ", " "), ("﻿", "")]:
        t = t.replace(a, b)
    return t


def body():
    t = clean(SRC.read_text(encoding="utf8"))
    t = t.split("*** START OF THE PROJECT GUTENBERG EBOOK", 1)[1]
    t = t.split("*** END OF THE PROJECT GUTENBERG", 1)[0]
    for old, new in SOURCE_FIXES:
        if old not in t:
            raise SystemExit(f"source fix no longer matches: {old[:60]!r}")
        t = t.replace(old, new)
    assert CONTENTS_END in t, "contents list not found"
    return t.split(CONTENTS_END, 1)[1]


def blocks(raw):
    """Source block -> list of paragraphs; verse keeps its line breaks."""
    out = []
    for chunk in re.split(r"\n\s*\n", raw):
        lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        if not lines:
            continue
        # VERSE: two or more lines, all of them short. Grimm's rhymes are
        # set exactly like prose in this transcription, so length is the
        # only signal there is.
        if len(lines) >= 2 and all(len(l) < VERSE_LINE for l in lines) \
                and sum(len(l) for l in lines) / len(lines) < 46:
            out.append("\n".join("\t" + l for l in lines))
        else:
            out.append(" ".join(lines))
    return out


def parse():
    b = body()
    # legends live after the "Children's Legends" divider; cut them off
    # first so the tale regex cannot run into them.
    assert "Children’s Legends" in b, "legend divider missing"
    tales_part, legend_part = b.split("Children’s Legends", 1)

    items = []
    parts = TALE.split(tales_part)
    for i in range(1, len(parts) - 2, 3):
        t = parts[i + 1].strip()
        items.append((int(parts[i]), TITLE_FIXES.get(t, t), blocks(parts[i + 2])))
    assert [n for n, _, _ in items] == list(range(1, 201)), \
        f"expected tales 1..200, got {len(items)}"

    legends = []
    parts = LEGEND.split(legend_part)
    for i in range(1, len(parts) - 2, 3):
        t = parts[i + 1].strip()
        legends.append((int(parts[i]), TITLE_FIXES.get(t, t),
                        blocks(parts[i + 2])))
    assert [n for n, _, _ in legends] == list(range(1, 11)), \
        f"expected legends 1..10, got {len(legends)}"
    return items, legends


def wc(pars):
    return sum(len(p.split()) for p in pars)


def split_oversize(pars, n):
    """Cut one long tale into n parts at paragraph boundaries."""
    total = wc(pars)
    want = total / n
    out, cur, run = [], [], 0
    for p in pars:
        cur.append(p)
        run += len(p.split())
        if run >= want and len(out) < n - 1:
            out.append(cur)
            cur, run = [], 0
    if cur:
        out.append(cur)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    tales, legends = parse()
    units = [(f"{t}", pars) for _, t, pars in tales] + \
            [(f"{t}", pars) for _, t, pars in legends]

    manifest, files = [], []
    group = []                       # [(title, pars)] pending for one file
    for title, pars in units:
        n = wc(pars)
        if n > MAX:                  # a tale that needs a file group of its own
            if group:
                files.append(group)
                group = []
            k = -(-n // TARGET)
            for i, chunk in enumerate(split_oversize(pars, k), 1):
                files.append([(title, chunk, i, k)])
            continue
        if group and wc([p for _, ps in group for p in ps]) + n > MAX:
            files.append(group)
            group = []
        group.append((title, pars))
    if group:
        files.append(group)

    for idx, entries in enumerate(files):
        name = f"{idx:03d}.txt"
        if len(entries[0]) == 4:                  # a part of an oversize tale
            title, pars, part, of = entries[0]
            head = [title, f"(Part {part} of {of})"] if of > 1 else [title]
            (OUT / name).write_text("\n\n".join(head + pars) + "\n")
            manifest.append({"file": name, "title": title,
                             "part": part, "of": of, "words": wc(pars)})
            continue
        chunks, titles = [], []
        for title, pars in entries:
            titles.append(title)
            chunks.append(title)
            chunks.extend(pars)
        text = "\n\n".join(chunks) + "\n"
        # the split discards anything before the first heading
        assert text.startswith(titles[0] + "\n"), name
        (OUT / name).write_text(text)
        manifest.append({"file": name, "title": titles[0], "part": 1, "of": 1,
                         "words": wc([p for _, ps in entries for p in ps]),
                         "split_headings": titles})

    # every tale placed exactly once, and no title claimed twice
    placed = []
    for m in manifest:
        placed.extend(m.get("split_headings") or [m["title"]])
    seen = {}
    for t in placed:
        seen[t] = seen.get(t, 0) + 1
    dupes = {t: c for t, c in seen.items() if c > 1 and
             sum(1 for m in manifest if m["title"] == t and m["of"] > 1) == 0}
    assert not dupes, f"title claimed twice: {dupes}"
    assert len({t for t in placed}) >= 209, f"only {len(set(placed))} titles"

    for bad in TITLE_FIXES:
        assert bad not in placed, f"title fix did not fire: {bad!r}"
    for good in TITLE_FIXES.values():
        assert good in placed, f"title fix produced nothing: {good!r}"

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    words = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {len(set(placed))} tales, {words:,} words")
    print(f"largest file: {max(m['words'] for m in manifest):,} words")


if __name__ == "__main__":
    main()
