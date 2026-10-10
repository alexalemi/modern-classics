#!/usr/bin/env python3
"""Repair gallic-war's headings, cut the invented framing, write manifest.json.

WHY THIS EXISTS (audit of 2026-10-09, ROADMAP.md). The book shipped with
no manifest.json, so every file's first line became its heading and the
contents mixed four conventions: "Book I", "BOOK II: THE BELGIAN WAR",
"BOOK V." with a second capitalised subtitle line, "BOOK VI" with a
subtitle and a "(53 BC)" line under it. Caesar gave his Books no titles,
and only four of the seven translations had invented one, so every Book
is now headed bare, word form: "Book One" ... "Book Seven" (odyssey,
epictetus).

The same agents wrote framing that is not Caesar's, and it went out in
his voice:
  - orientation paragraphs at the head of Books I, III and VII ("The
    year is 58 BC. Julius Caesar, newly appointed governor...");
  - closing asides at the end of Books I, IV and VI ("— and, no doubt,
    to write the dispatches that would make all of Rome talk...").
Each Book now opens and ends where the McDevitte-Bohn text does. Books
II and IV open on the source's own first sentence with a date gloss
folded in; that is a gloss, not an invented paragraph, and is kept.

Idempotent: a file already headed "Book <Word>" is left alone, and each
closing cut asserts its old text is present or already gone.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"

WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven"]

# file -> prefixes of the leading paragraphs to drop (heading, subtitle,
# invented opener, the "---" rule that followed it). Checked, so a file
# that has drifted fails loudly instead of losing a paragraph of Caesar.
FRONT = {
    "001.txt": ["Book I", "The year is 58 BC.", "---"],
    "002.txt": ["BOOK II: THE BELGIAN WAR"],
    "003.txt": ["BOOK III", "It is the winter of 57-56 BC."],
    "004.txt": ["Book IV"],
    "005.txt": ["BOOK V.\nTHE SECOND BRITISH EXPEDITION"],
    "006.txt": ["BOOK VI", "The Druid Digression"],
    "007.txt": ["BOOK VII\nThe Great Revolt", "52 BC. After six years", "---"],
}

# Invented closing asides: (old, new). The source ends each of these
# Books on the bare fact.
TAIL = {
    "001.txt": ("to hold the judicial assizes — and, no doubt, to write the "
                "dispatches that would make all of Rome talk about what he'd "
                "accomplished.",
                "to hold the judicial assizes."),
    "004.txt": ("a public thanksgiving of twenty days — an extraordinary "
                "honor for an extraordinary year.",
                "a public thanksgiving of twenty days."),
    "006.txt": ("to hold the assizes — and to tend to his political career "
                "in Rome.",
                "to hold the assizes."),
}

# Not framing but rendering: the Helvetian census was set as bare lines,
# which HTML runs together into one paragraph, and its last line ("Grand
# total: 368,000", short, unpunctuated) was set as an h4 subheading.
# Written as the one sentence it is in the source.
INLINE = {
    "001.txt": ("The totals:\n\nHelvetii: 263,000\nTulingi: 36,000\n"
                "Latobrigi: 14,000\nRauraci: 23,000\nBoii: 32,000\n\n"
                "Grand total: 368,000\n",
                "The totals: Helvetii, 263,000; Tulingi, 36,000; Latobrigi, "
                "14,000; Rauraci, 23,000; Boii, 32,000 — a grand total of "
                "368,000.\n"),
}


def fix_front(name, word):
    path = MOD / name
    text = path.read_text()
    if text.startswith(f"Book {word}\n"):
        return
    paras = [p for p in text.strip("\n").split("\n\n")]
    # collapse runs of blank lines: drop empty paragraphs at the front
    i = 0
    for want in FRONT[name]:
        while not paras[i].strip():
            i += 1
        if not paras[i].strip().startswith(want):
            raise SystemExit(f"{name}: expected paragraph starting {want!r}, "
                             f"found {paras[i][:60]!r}")
        i += 1
    while not paras[i].strip():
        i += 1
    body = "\n\n".join(paras[i:])
    path.write_text(f"Book {word}\n\n{body}\n")


def fix_tail(name, table=TAIL):
    path = MOD / name
    text = path.read_text()
    old, new = table[name]
    if old in text:
        path.write_text(text.replace(old, new))
    elif new not in text:
        raise SystemExit(f"{name}: neither old nor repaired closing found")


# INVENTED SUBHEADINGS (orchestrator ruling, 2026-10-10, as for
# progress-and-poverty). The translating agents wrote ALL-CAPS section
# heads ("THE SPEECH OF CLEON") that the source translation never prints
# -- chapters/ has no such line anywhere -- and applied them unevenly
# across files. They are removed: any paragraph that is one short line in
# capitals. Re-running finds none and changes nothing.
def strip_caps_heads(path):
    text = path.read_text()
    paras = re.split(r"\n\s*\n", text)
    keep = [p for p in paras
            if not (p.strip() and "\n" not in p.strip()
                    and p.strip().isupper() and len(p.strip()) < 90)]
    if len(keep) != len(paras):
        path.write_text("\n\n".join(keep))
    return len(paras) - len(keep)


def main():
    files = sorted(FRONT)
    for name, word in zip(files, WORDS):
        fix_front(name, word)
    for name in TAIL:
        fix_tail(name)
    for name in INLINE:
        fix_tail(name, INLINE)
    for name in FRONT:
        strip_caps_heads(MOD / name)
    manifest = [{"file": f, "title": f"Book {w}", "part": 1, "of": 1}
                for f, w in zip(files, WORDS)]
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
