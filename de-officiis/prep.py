"""Build chapters/ (Latin), reference/ (Miller's English) + manifest.json
for De Officiis from source.txt.

Source is Gutenberg #47001: the 1913 Loeb parallel edition — Cicero's
Latin and Walter Miller's English translation alternating chapter by
chapter within each of the three books. This project translates FROM THE
LATIN; Miller's version is kept per-file under reference/ as a
comprehension crib for the translation agents, never as the source.

Within a book, each Roman-numeral chapter appears twice: first the Latin
block (with Loeb *n* margin section numbers and bracketed
textual-apparatus footnotes), then Miller's English. The first
occurrence of a numeral is Latin, the second English — a stopword
heuristic double-checks the classification and the script aborts on
disagreement.

Stripped: *n* margin numbers, [n] footnote markers, indented apparatus
paragraphs (first line "[n] …"), #sidenotes#, ^superscript marks, and
editorial square brackets around suspected interpolations (contents
kept). Chapters are grouped into ~2800-Latin-word part files at chapter
boundaries (expect modern English ≈ 1.3–1.5x the Latin word count — run
verify.py with --min-ratio 1.0 --max-ratio 1.8).
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 2800

VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}
BOOK_TITLES = {1: "Moral Goodness", 2: "Expediency",
               3: "The Conflict Between the Right and the Expedient"}
STOPWORDS = re.compile(r"\b(the|and|of|to|that|which|for)\b")


def roman(s):
    total = 0
    for a, b in zip(s, s[1:] + "\0"):
        total += -VALUES[a] if VALUES[a] < VALUES.get(b, 0) else VALUES[a]
    return total


def clean(body, latin):
    paras = []
    for p in re.split(r"\n\s*\n", body):
        if not p.strip():
            continue
        if re.match(r"\s+\[\w+\]", p):        # textual-apparatus block
            continue
        if "[Illustration" in p:
            continue
        p = " ".join(p.split())
        p = re.sub(r"\*\d+\* ?", "", p)        # Loeb margin section numbers
        p = re.sub(r"\[\w+\]", "", p)          # footnote markers (incl. [CH])
        p = re.sub(r"#[^#]*#", "", p)          # sidenotes
        p = p.replace("^", "")
        p = re.sub(r"[\[\]]", "", p)           # editorial brackets, keep text
        p = re.sub(r"  +", " ", p).strip()
        if p:
            paras.append(p)
    return "\n\n".join(paras)


text = BOOK.joinpath("source.txt").read_text()
start = text.index("LIBER PRIMUS / BOOK I")
end = text.index("\nINDEX\n")
text = text[start:end]

# remove the "BOOK N" + ALL-CAPS-title header blocks that precede each
# "LIBER … / BOOK N" line, then split on the LIBER lines only
text = re.sub(r"^BOOK [IVX]+\n+[A-Z][A-Z ,&]+\n", "", text, flags=re.M)

books = []   # (book_no, [(chap_no, latin, english), ...])
for chunk in re.split(r"^LIBER [A-Z]+ / BOOK [IVX]+$", text, flags=re.M)[1:]:
    book_no = len(books) + 1
    # Chapters strictly alternate Latin-then-English with ascending
    # numerals; anything else matching the numeral pattern (e.g. the
    # praenomen "L. Manlio…" at a paragraph start) is ordinary text.
    latin_next = english_next = 1
    bounds = []   # (match, kind)
    # numerals start at a line, or mid-line right after a "#sidenote#"
    for m in re.finditer(r"(?:^(?:\*\d+\* )?|(?<=# ))([IVXL]+)\. ", chunk,
                         flags=re.M):
        n = roman(m.group(1))
        # Latin leads; occasionally two short Latin chapters print
        # before their English pair, so Latin may run ahead by more
        # than one.
        if n == latin_next and latin_next >= english_next:
            bounds.append((m, "L")); latin_next += 1
        elif n == english_next and english_next < latin_next:
            bounds.append((m, "E")); english_next += 1
    assert latin_next == english_next and latin_next > 1, \
        f"book {book_no}: unbalanced chapters (L{latin_next}/E{english_next})"
    seen = {}
    for k, (m, kind) in enumerate(bounds):
        end = bounds[k + 1][0].start() if k + 1 < len(bounds) else len(chunk)
        body = chunk[m.end():end]
        n = roman(m.group(1))
        if kind == "L":
            seen[n] = [body, None]
        else:
            seen[n][1] = body
    chaps = []
    for n in sorted(seen):
        latin_raw, english_raw = seen[n]
        assert english_raw is not None, f"book {book_no} ch {n}: no English pair"
        latin = clean(latin_raw, True)
        english = clean(english_raw, False)
        # sanity: stopword density must separate the two languages
        ld = len(STOPWORDS.findall(latin.lower())) / max(1, len(latin.split()))
        ed = len(STOPWORDS.findall(english.lower())) / max(1, len(english.split()))
        assert ed > 0.08 > ld, f"book {book_no} ch {n}: language mixup ({ld:.2f}/{ed:.2f})"
        chaps.append((n, latin, english))
    assert [n for n, _, _ in chaps] == list(range(1, len(chaps) + 1)), \
        f"book {book_no}: chapter sequence broke"
    books.append((book_no, chaps))

manifest, file_no = [], 0
for book_no, chaps in books:
    title = f"Book {['I', 'II', 'III'][book_no - 1]}: {BOOK_TITLES[book_no]}"
    total = sum(len(l.split()) for _, l, _ in chaps)
    per = total / max(1, round(total / TARGET))
    groups, cur, curw = [], [], 0
    for n, latin, english in chaps:
        w = len(latin.split())
        if cur and curw + w > per * 1.15:
            groups.append(cur); cur, curw = [], 0
        cur.append((n, latin, english)); curw += w
        if curw >= per:
            groups.append(cur); cur, curw = [], 0
    if cur:
        groups.append(cur)
    for part, group in enumerate(groups, 1):
        out, ref = [title], [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
            ref.append(f"\n(Part {part} of {len(groups)})")
        for n, latin, english in group:
            out.append(f"\nChapter {n}\n\n{latin}")
            ref.append(f"\nChapter {n}\n\n{english}")
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text("\n".join(out) + "\n")
        BOOK.joinpath("reference", fn).write_text("\n".join(ref) + "\n")
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups),
                         "words": len(("\n".join(out)).split()),
                         "chapters": f"{group[0][0]}-{group[-1][0]}"})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{sum(len(c) for _, c in books)} chapters -> {file_no} files (Latin words shown)")
for m in manifest:
    print(f"  {m['file']}  {m['title'][:12]:<13} part {m['part']}/{m['of']}"
          f"  ch {m['chapters']:<7} {m['words']:>5}")
