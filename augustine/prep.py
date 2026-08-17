#!/usr/bin/env python3
"""Augustine's Confessions (Pusey, 1838) -> chapters/ + manifest.json

    ./fetch.sh && python3 augustine/prep.py

Source: Project Gutenberg #3296, E. B. Pusey's translation of 1838 —
the classic English Confessions, and the one that made "Thou" the voice
of the book in English. Measured at 35.9 archaisms per 1,000 words,
higher than anything else in this collection.

THE CHAPTER DIVISIONS ARE NOT IN THE SOURCE, AND ARE NOT INVENTED HERE.
Augustine is cited by book, chapter and section — Conf. VIII.12.29 —
and every scholarly edition prints all three. This transcription prints
none: thirteen BOOK headings and then continuous prose. That was checked
rather than assumed, in the plain text AND in Gutenberg's HTML edition,
which elsewhere in this project has carried structure the .txt drops
(soap-bubbles' plates, candle's captions). It carries nothing here: one
<h1>, fourteen <h2>, and no chapter headings at all.

Recovering them from the Latin (Gutenberg #33849) was considered and
rejected for now: the Latin has 971 numbered sections and Pusey's
English has 461 paragraphs, so there is no 1:1 map and an alignment
would be a project of its own with real risk of putting a citation on
the wrong sentence. A wrong chapter number is worse than none, because
a reader would trust it. So the edition ships thirteen books, and says
so.

WHAT IS ADDED, and it is NEW WRITING, on the soap-bubbles precedent
where the captions were written for this edition rather than
translated: each book gets a DESCRIPTIVE title. "Book Eight" tells a
reader nothing; "Book Eight: The Garden at Milan" tells them they have
reached the conversion. These are the standard editorial
characterisations, not a summary of anything Augustine says.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source" / "pg3296.txt"
OUT = BOOK / "chapters"

TARGET, MAX = 3600, 4300      # words per file; cut at paragraph boundaries

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII"]
WORD = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
        "Nine", "Ten", "Eleven", "Twelve", "Thirteen"]

TITLES = [
    "Infancy, Boyhood, and the Beginnings of Sin",
    "The Pear Tree",
    "Carthage, the Theatre, and the Manichees",
    "Friendship, Grief, and the Death of a Friend",
    "Faustus, Rome, and the Road to Milan",
    "Ambrose, Alypius, and the Struggle to Believe",
    "The Platonists and the Problem of Evil",
    "The Garden at Milan",
    "Baptism, Ostia, and the Death of Monica",
    "Memory",
    "Time and Eternity",
    "Heaven and Earth",
    "The Days of Creation",
]


def clean(t):
    for a, b in [(" ", " "), (" ", " "), ("﻿", "")]:
        t = t.replace(a, b)
    return t


def body():
    t = clean(SRC.read_text(encoding="utf8", errors="replace"))
    i = t.find("*** START OF")
    t = t[t.find("\n", i) + 1:]
    j = t.find("*** END OF")
    if j > 0:
        t = t[:j]
    return t


def blocks(raw):
    """Source block -> paragraphs; an indented run stays one block.

    The 23 indented lines in this text are quoted verse and the Psalms
    set as lined matter. Emitting one paragraph per line would put each
    line in its own <pre> and strew a quatrain down the page — the
    fleming rule."""
    out = []
    for chunk in re.split(r"\n\s*\n", raw):
        lines = [l.rstrip() for l in chunk.split("\n") if l.strip()]
        if not lines:
            continue
        if all(re.match(r"^[ \t]{2,}\S", l) for l in lines):
            # dedent as a block, never per line, so the rows stay in register
            pad = min(len(l) - len(l.lstrip()) for l in lines)
            out.append("\n".join("\t" + l[pad:] for l in lines))
        else:
            out.append(" ".join(l.strip() for l in lines))
    return out


def parse():
    b = body()
    parts = re.split(r"(?m)^\s*BOOK ([IVXL]+)\s*$", b)
    found = parts[1::2]
    assert found == ROMAN, f"book numbering is not I..XIII: {found}"
    return [(found[i], blocks(parts[2 * i + 2])) for i in range(len(found))]


def wc(ps):
    return sum(len(p.split()) for p in ps)


def split_oversize(pars, n):
    total, out, cur, run = wc(pars), [], [], 0
    for p in pars:
        cur.append(p)
        run += len(p.split())
        if run >= total / n and len(out) < n - 1:
            out.append(cur)
            cur, run = [], 0
    if cur:
        out.append(cur)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    books = parse()
    manifest, idx = [], 0
    for i, (roman, pars) in enumerate(books):
        title = f"Book {WORD[i]}: {TITLES[i]}"
        n = wc(pars)
        chunks = [pars] if n <= MAX else split_oversize(pars, -(-n // TARGET))
        for part, chunk in enumerate(chunks, 1):
            name = f"{idx:03d}.txt"
            head = [title] + ([f"(Part {part} of {len(chunks)})"]
                              if len(chunks) > 1 else [])
            (OUT / name).write_text("\n\n".join(head + chunk) + "\n")
            manifest.append({"file": name, "title": title, "part": part,
                             "of": len(chunks), "words": wc(chunk)})
            idx += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    words = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, 13 books, {words:,} words")
    print(f"largest file: {max(m['words'] for m in manifest):,} words")
    for m in manifest:
        if m["part"] == 1:
            of = f"  ({m['of']} parts)" if m["of"] > 1 else ""
            print(f"  {m['file']}  {m['title']}{of}")


if __name__ == "__main__":
    main()
