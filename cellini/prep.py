"""The Italian Vita -> chapters/ + manifest.json, with Symonds as a crib.

FROM THE ITALIAN (it.wikisource, cached by fetch.py into _italian.json),
with John Addington Symonds's 1888 English (Gutenberg #4028) aligned
chapter by chapter under reference/ — the ovid/de-officiis pattern.

WHY SYMONDS IS THE CRIB AND NOT THE SOURCE. His is the standard English
Cellini and it is very good scholarship, but it is 1888 prose put on a
man who wrote the way he talked: Cellini's Italian is fast, obscene,
boastful, ungrammatical and often one sentence long for half a page,
and Symonds irons all of that into decorous Victorian narrative. Using
him as the source would be modernising a costume rather than a book.
Crib, not source.

THE ALIGNMENT IS NOT ONE TO ONE, AND THE DIFFERENCE IS REAL. Wikisource
has 128 chapters in Libro primo; Symonds has 127. Every chapter from 1
to 126 matches within the normal Italian-to-English word ratio, and the
divergence starts exactly at 127 — because SYMONDS RUNS THE ITALIAN'S
127 AND 128 TOGETHER as his CXXVII, and then prints the Capitolo, the
poem Cellini wrote in the dungeon of Sant'Angelo, at the end of it.
Found by comparing per-chapter word counts across the whole book rather
than by trusting the totals; the counts are asserted here, so a future
re-fetch that quietly renumbers cannot slide the crib out of register.

WHAT IS IN THE BOOK. The Proemio sonnet and the Capitolo are CELLINI'S
OWN VERSE and are kept, as verse. Symonds's own footnotes are his, not
Cellini's, and stay in reference/ with the rest of him.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
OUT = BOOK / "chapters"
REF = BOOK / "reference"

# Italian words per file. The mean chapter is 672 words, so this groups
# five or six of them; no chapter is ever split, because Cellini is
# cited by book and chapter and a cut inside one would be uncitable.
TARGET = 4200

WORD = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen "
        "Twenty").split()

# Per-chapter word counts that prove the crib is in register. Written out
# rather than derived (the grimm rule).
IT_BOOK1, IT_BOOK2 = 128, 113
EN_BOOK1, EN_BOOK2 = 127, 113


def clean(w):
    """Wikitext -> plain paragraphs.

    The source is unusually clean: five templates in the whole book.
    {{R|n}} is a line-number marker in the verse and is dropped; {{Ac}}
    and {{AutoreCitato}} are link templates whose visible text is kept.
    """
    w = re.sub(r"\{\{\s*(?:Qualità|IncludiIntestazione)\b[^{}]*\}\}", "", w)
    w = re.sub(r"\{\{\s*R\s*\|[^{}]*\}\}", "", w)
    w = re.sub(r"\{\{\s*(?:Ac|AutoreCitato)\s*\|([^{}|]*)(?:\|[^{}]*)?\}\}",
               r"\1", w)
    if "{{" in w:
        raise SystemExit(f"unhandled template: {re.findall(r'{{[^}]*', w)[:3]}")
    w = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", w)
    w = re.sub(r"\[\[([^\]]*)\]\]", r"\1", w)
    w = w.replace("''", "")
    w = re.sub(r"<br\s*/?>", "\n", w)
    return w


def verse_blocks(w):
    """Split into (is_verse, text) runs on <poem>...</poem>."""
    out, pos = [], 0
    for m in re.finditer(r"<poem>(.*?)</poem>", w, flags=re.S):
        if w[pos:m.start()].strip():
            out.append((False, w[pos:m.start()]))
        out.append((True, m.group(1)))
        pos = m.end()
    if w[pos:].strip():
        out.append((False, w[pos:]))
    return out


def render(w):
    """Plain-text body: prose paragraphs, verse lines tab-indented."""
    parts = []
    for is_verse, text in verse_blocks(clean(w)):
        if is_verse:
            for stanza in re.split(r"\n\s*\n", text):
                lines = [l.strip() for l in stanza.split("\n") if l.strip()]
                if lines:
                    parts.append("\n".join("\t" + l for l in lines))
        else:
            for para in re.split(r"\n\s*\n", text):
                # A WIKI COLON INDENT IS VERSE, and collapsing it is
                # silent summarisation of the quietest kind. Four
                # chapters quote verse this way -- his father's Latin
                # motto on the mirror, the four-line epigram under the
                # Medici arms, and two more -- ten lines in all, and
                # every one of them had been run into the surrounding
                # prose as a single paragraph, where nothing downstream
                # could tell it from a sentence.
                block = [l.strip() for l in para.split("\n") if l.strip()]
                if block and all(l.startswith(":") for l in block):
                    parts.append("\n".join(
                        "\t" + l.lstrip(":").strip() for l in block))
                    continue
                para = re.sub(r"\s+", " ", para).strip()
                if para:
                    parts.append(para)
    return "\n\n".join(parts)


def symonds():
    """(book, chapter) -> Symonds's English, his own notes included."""
    t = (BOOK / "_pg4028.txt").read_text()
    body = t[t.index("Autobiography of Benvenuto Cellini"):]
    body = body[:body.index("*** END OF THE PROJECT GUTENBERG")]
    parts = re.split(r"\n\n([IVXLC]+)\n\n", body)
    chunks = [parts[i].strip() for i in range(2, len(parts), 2)]
    if len(chunks) != EN_BOOK1 + EN_BOOK2:
        raise SystemExit(f"crib has {len(chunks)} chapters, expected "
                         f"{EN_BOOK1 + EN_BOOK2}")
    out = {}
    for i, c in enumerate(chunks):
        if i < EN_BOOK1:
            out[(1, i + 1)] = c
        else:
            out[(2, i + 1 - EN_BOOK1)] = c
    # SYMONDS'S CXXVII IS THE ITALIAN'S 127 AND 128, plus the Capitolo.
    # Give it to both, so a translator working on either has the whole
    # of the English in front of them and can see the seam.
    out[(1, 128)] = out[(1, 127)]
    return out


def main():
    data = json.loads((BOOK / "_italian.json").read_text())
    extra = json.loads((BOOK / "_extra.json").read_text())
    n1 = sum(1 for c in data if c["book"] == 1)
    n2 = sum(1 for c in data if c["book"] == 2)
    if (n1, n2) != (IT_BOOK1, IT_BOOK2):
        raise SystemExit(f"Italian has {n1}+{n2} chapters, expected "
                         f"{IT_BOOK1}+{IT_BOOK2}")

    proem = next(v for k, v in extra.items() if k.endswith("/Proemio"))
    capit = next(v for k, v in extra.items() if k.endswith("/Capitolo"))

    # THE UNITS. The Proemio opens the book; the Capitolo closes Book
    # One, where Cellini himself puts it.
    units = [("front", 0, "Proem", render(proem))]
    for c in data:
        if c["book"] == 2 and c["chapter"] == 1:
            pass
        units.append((c["book"], c["chapter"],
                      f"Chapter {c['chapter']}", render(c["wikitext"])))
    cap_at = max(i for i, u in enumerate(units) if u[0] == 1) + 1
    units.insert(cap_at, ("capitolo", 129, "The Capitolo", render(capit)))

    crib = symonds()

    OUT.mkdir(exist_ok=True)
    REF.mkdir(exist_ok=True)
    for f in list(OUT.glob("*.txt")) + list(REF.glob("*.txt")):
        f.unlink()

    # GROUP INTO FILES, never cutting a chapter and never crossing a Book.
    groups, cur, run, book = [], [], 0, None
    for u in units:
        w = len(u[3].split())
        if cur and (u[0] != book or run + w / 2 > TARGET):
            groups.append((book, cur))
            cur, run = [], 0
        book = u[0]
        cur.append(u)
        run += w
    groups.append((book, cur))

    manifest, total = [], 0
    for i, (bk, us) in enumerate(groups):
        fn = f"{i:03d}.txt"
        nums = [u[1] for u in us if isinstance(u[0], int) and u[1] <= 128]
        # TITLES MUST BE UNIQUE, because assemble.py makes a section's
        # anchor by slugifying its heading, and both Books have a chapter
        # 97 (the democracy2 trap: a repeated heading is a repeated
        # anchor, and every link goes to the first of its kind). So every
        # section names its Book. Mechanical rather than descriptive, on
        # the spinoza precedent: the Vita is cited by book and chapter,
        # and a reader looking for the casting of the Perseus wants Book
        # Two, chapter 75, not a theme.
        if bk == "front":
            title = "Proem"
        elif bk == "capitolo":
            title = "The Capitolo"
        else:
            where = f"Book {WORD[bk]}"
            title = (f"{where}, {us[0][2]}" if len(us) == 1 else
                     f"{where}, Chapters {us[0][1]} to {us[-1][1]}")
        body = "\n\n".join(
            (u[2] + "\n\n" + u[3]) if len(us) > 1 else u[3] for u in us)
        (OUT / fn).write_text(f"{title}\n\n{body}\n")

        rows = []
        for u in us:
            key = (bk, u[1]) if isinstance(bk, int) else None
            eng = crib.get(key)
            if eng:
                rows.append(f"[Book {bk}, chapter {u[1]}]\n\n{eng}")
        (REF / fn).write_text(f"{title} (Symonds)\n\n" + "\n\n".join(rows) + "\n")

        words = len(body.split())
        total += words
        entry = {"file": fn, "title": title, "part": 1, "of": 1,
                 "chapter": True, "words": words}
        if i == 0:
            pass
        elif isinstance(bk, int) and bk != groups[i - 1][0]:
            entry["part_before"] = f"Book {WORD[bk]}"
        manifest.append(entry)
    manifest[1]["part_before"] = "Book One"

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{len(groups)} files, {total} Italian words; "
          f"largest {max(m['words'] for m in manifest)}")


if __name__ == "__main__":
    main()
