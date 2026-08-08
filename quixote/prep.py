"""Build chapters/ (Spanish) + reference/ (Ormsby's English crib) +
manifest.json for Don Quixote.

    bash quixote/fetch.sh && python3 quixote/prep.py

SOURCES. The Spanish is Project Gutenberg #2000 — Cervantes' 1605 and 1615
volumes in one file, 379,575 words across 126 chapters. The crib is John
Ormsby's 1885 translation from the Standard Ebooks repository, which keeps
ONE XHTML FILE PER CHAPTER; since the Spanish carries 126 chapter headings
and Ormsby carries 126 chapter files, the alignment is 1:1 and needs no
work at all. That is the whole reason this book is tractable: contrast
ovid/, where Riley's crib had to be sliced against Latin line-ranges.

Ormsby is NEVER the source. This is the de-officiis/ovid pattern: translate
from the Spanish, keep the Victorian English under reference/ per file as a
comprehension crib — who-does-what, hard idiom, the proverbs — and never as
a thing to be modernised. His prose is exactly the layer this edition
exists to get out from under.

WHY THIS BOOK. Every good modern translation is in copyright, so the free
Don Quixote is Ormsby, Jarvis, Motteux or Shelton, and the book's
reputation as a slog is very largely an artifact of that.

STRUCTURE, AND ONE TRAP IN IT. The 1605 volume is internally divided into
four "partes" — headings fall before chapters 9, 15 and 29 — and then the
1615 volume is itself "Segunda parte". So the word PART means two different
things, and using both as manifest dividers would nest a "Second Part"
inside "Part One" in the table of contents. The 1615 division is the real
one and becomes the part divider; Cervantes' four internal divisions are
kept where he put them, as headings in the text. He abandoned the scheme in
1615 and Ormsby drops it altogether; it stays here because the break at
chapter 9 is a joke — the narrative stops mid-swordstroke because the
manuscript ran out.

WHAT IS DROPPED. The printing-office paperwork bound into both volumes —
the Tasa (the price the book may be sold at), the Testimonio de las erratas,
the royal Privilegio and the three Aprobaciones. Cervantes did not write
them, they open the book with tax documents, and Ormsby drops them too.
They go to reference/licences.txt so that dropping them is recorded rather
than silent. The DEDICATIONS and both PRÓLOGOS are not paperwork and are
translated: the 1605 prologue, in which a friend advises him to pad the
book with fake citations, is one of the great prefaces in any language, and
the 1615 one answers the man who wrote a fake sequel.
"""

import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
REFERENCE = BOOK / "reference"

# Spanish 3,012 words a chapter on average; Ormsby runs 1.06x the Spanish
# and a modern retelling should land near that, so a 6,400-word Spanish
# chapter is about 7,000 words of English -- the output limit that has
# governed every book here.
MAX_WORDS = 6400

CHAPTER = re.compile(r"^\s*Cap[íi]tulo\s+(primero|Primero|[IVXLC]+)\b")
# The four internal divisions of the 1605 volume. "caballero" (not
# "hidalgo") is the 1615 volume and is handled separately.
INNER_PART = re.compile(r"^(Primera|Segunda|Tercera|Cuarta)\s+parte\s+del\s+"
                        r"ingenioso\s+hidalgo\b", re.I)
PART_TWO = "Segunda parte del ingenioso caballero"

# The paperwork, by its heading. Everything from one of these up to the
# next heading is licence matter and goes to the crib.
PAPERWORK = re.compile(r"^(TASA|TESTIMONIO DE LAS ERRATAS|EL REY|"
                       r"FEE DE ERRATAS|APROBACIONES|APROBACIÓN|"
                       r"PRIVILEGIO|EL PRÍNCIPE)\s*$")
# The front matter that IS the book.
KEEP_FRONT = re.compile(r"^(AL DUQUE DE BÉJAR|PRÓLOGO|"
                        r"DEDICATORIA|AL CONDE DE LEMOS|"
                        r"AL LIBRO DE DON QUIJOTE)")


def source_lines():
    """The Spanish body, with the Gutenberg wrapper and the whole table of
    contents gone.

    THE TABLE OF CONTENTS IS 465 LINES OF CHAPTER TITLES and it comes
    first, so anything that looks for a title finds the contents entry
    rather than the chapter. It ends where the body's own title page
    begins; that line occurs exactly twice in the file, and the second is
    the one we want."""
    raw = (SRC / "quixote_es.txt").read_text(errors="replace")
    i, j = raw.find("*** START"), raw.find("*** END")
    if i < 0 or j < 0:
        sys.exit("Gutenberg markers not found in quixote_es.txt")
    lines = raw[raw.find("\n", i):j].split("\n")
    title = "El ingenioso hidalgo don Quijote de la Mancha"
    hits = [n for n, l in enumerate(lines) if l.strip() == title]
    if len(hits) < 2:
        sys.exit(f"expected the title line at least twice, found {len(hits)}")
    return lines[hits[-1]:]


# THE BOOK IS FULL OF VERSE and the source does not mark any of it. Undoing
# the hard wraps blindly turns Grisostomo's song, the ten preliminary poems
# and every sonnet in the book into one long prose paragraph -- and the
# translator then has no way of knowing a poem was ever there.
#
# The wrap width is the tell. Gutenberg fills prose to about 75 characters,
# so every prose paragraph of more than one line has at least one long line;
# verse lines are set as the poet wrote them and here run 21 to 43. A block
# with no line longer than this is verse, and keeps its line breaks.
VERSE_MAX = 62


def paragraphs(lines):
    """Blank-line-separated blocks. Prose is unwrapped; verse keeps its
    lines, tab-indented, which is how this project stores verse."""
    out, cur = [], []

    def flush():
        if not cur:
            return
        if len(cur) > 1 and max(len(x) for x in cur) <= VERSE_MAX:
            out.append("\n".join("\t" + x for x in cur))
        else:
            out.append(" ".join(cur))
        cur.clear()

    for l in lines:
        if l.strip():
            cur.append(l.strip())
        else:
            flush()
    flush()
    return out


def split_front(lines):
    """(kept front matter blocks, dropped paperwork blocks).

    Both are lists of (heading, [paragraphs]). A block runs from its
    heading to the next heading of either kind."""
    heads = [n for n, l in enumerate(lines)
             if PAPERWORK.match(l.strip()) or KEEP_FRONT.match(l.strip())]
    keep, drop = [], []
    for k, n in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        block = (lines[n].strip(), paragraphs(lines[n + 1:end]))
        (drop if PAPERWORK.match(lines[n].strip()) else keep).append(block)
    return keep, drop


def sections():
    """The whole book as (kind, title, [paragraphs]) in order.

    kind is "front" (a dedication, a prologue, the preliminary verses) or
    "chapter". Chapters carry Cervantes' own Spanish title, which is
    frequently a joke and is translated later -- see titles.json."""
    lines = source_lines()
    starts = [n for n, l in enumerate(lines) if CHAPTER.match(l)]
    if len(starts) != 126:
        sys.exit(f"expected 126 chapters, found {len(starts)}")
    p2 = next((n for n, l in enumerate(lines)
               if l.strip().startswith(PART_TWO)), None)
    if p2 is None:
        sys.exit("the 1615 volume's title line was not found")

    out, dropped = [], []
    p2_first = next(n for n in starts if n > p2)

    def front(lo, hi):
        keep, drop = split_front(lines[lo:hi])
        dropped.extend(drop)
        for head, pars in keep:
            if pars:
                out.append(("front", head, pars))

    def chapters(lo, hi):
        here = [n for n in starts if lo <= n < hi]
        for k, n in enumerate(here):
            end = here[k + 1] if k + 1 < len(here) else hi
            back_end = end - 1
            while back_end > n and not lines[back_end].strip():
                back_end -= 1
            if back_end > n and INNER_PART.match(lines[back_end].strip()):
                end = back_end
            # THE INNER-PART HEADING STANDS BEFORE THE CHAPTER IT OPENS, so
            # by line order it falls at the END of the previous chapter --
            # where it read as that chapter's last sentence. Take it off the
            # tail and put it at the head of the chapter it belongs to.
            opener, back = [], n - 1
            while back > lo and not lines[back].strip():
                back -= 1
            if back > lo and INNER_PART.match(lines[back].strip()):
                opener = [lines[back].strip()]
            body_start = here[k]
            title_lines, body_at = [lines[body_start].strip()], body_start + 1
            while body_at < end and lines[body_at].strip():
                title_lines.append(lines[body_at].strip())
                body_at += 1
            out.append(("chapter", " ".join(title_lines),
                        opener + paragraphs(lines[body_at:end])))

    # IN DOCUMENT ORDER. Each volume's front matter belongs to its own
    # volume: emitting all of it first put the 1615 prologue -- which is a
    # reply to a book that had not been written yet in 1605 -- in front of
    # Part One, chapter one.
    front(0, starts[0])
    chapters(starts[0], p2)
    front(p2, p2_first)
    chapters(p2_first, len(lines))
    return out, dropped


def ormsby(part, num):
    """Ormsby's chapter as plain paragraphs.

    KILL THE NOTEREFS AS ELEMENTS, NOT AS TAGS. Strip tags naively and
    <a epub:type="noteref">32</a> welds a bare 32 onto the preceding word
    -- "call to mind32 there lived" -- which reads as a number in the text
    and would pass every mechanical check this project has. (bunyan/.)"""
    p = SRC / "ormsby" / f"chapter-{part}-{num}.xhtml"
    s = p.read_text()
    s = re.sub(r"<a\b[^>]*epub:type=\"noteref\"[^>]*>.*?</a>", "", s, flags=re.S)
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S)
    s = re.sub(r"^.*?<body[^>]*>", "", s, flags=re.S)
    s = re.sub(r"</(p|h[1-6]|blockquote|li|div|section)>", "\n\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&#160;", " "), ("&nbsp;", " "), ("&amp;", "&"),
                 ("&lt;", "<"), ("&gt;", ">"), ("&#8217;", "’")):
        s = s.replace(a, b)
    pars = [re.sub(r"[ \t]+", " ", x).strip() for x in s.split("\n\n")]
    return [x for x in pars if x]


def split_oversize(pars):
    total = sum(len(p.split()) for p in pars)
    if total <= MAX_WORDS:
        return [pars]
    n = total // MAX_WORDS + 1
    target, parts, cur, count = total / n, [], [], 0
    for p in pars:
        if cur and count >= target:
            parts.append(cur)
            cur, count = [], 0
        cur.append(p)
        count += len(p.split())
    if cur:
        parts.append(cur)
    return parts


def main():
    if not (SRC / "quixote_es.txt").exists():
        sys.exit("run fetch.sh first")
    secs, dropped = sections()

    REFERENCE.mkdir(exist_ok=True)
    (REFERENCE / "licences.txt").write_text(
        "PRINTING-OFFICE PAPERWORK, NOT TRANSLATED\n"
        "The price the book might be sold at, the certificate of errata, the\n"
        "royal privilege and the censors' approvals, bound into both volumes\n"
        "as the law required. Cervantes did not write them. Kept here so that\n"
        "leaving them out is a recorded decision rather than a silent one.\n\n"
        + "\n\n".join(head + "\n\n" + "\n\n".join(pars)
                      for head, pars in dropped) + "\n")

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()
    (REFERENCE / "ormsby").mkdir(exist_ok=True)
    for f in (REFERENCE / "ormsby").glob("*.txt"):
        f.unlink()

    titles = {}
    tf = BOOK / "titles.json"
    if tf.exists():
        titles = json.loads(tf.read_text())

    manifest, idx, overall = [], 0, 0
    for kind, head, pars in secs:
        if kind == "chapter":
            # DERIVE the part and number, never mutate a counter: a
            # "reset at 53" fires a second time when Part Two reaches its
            # own chapter 53, and silently labels it 2-1 all over again.
            overall += 1
            part = 1 if overall <= 52 else 2
            chap_no = overall if part == 1 else overall - 52
            key = f"{part}-{chap_no}"
            title = titles.get(key) or head
            crib = ormsby(part, chap_no)
        else:
            key, title, crib = None, head, None
        chunks = split_oversize(pars)
        for k, chunk in enumerate(chunks):
            name = f"{idx:03d}.txt"
            (CHAPTERS / name).write_text("\n\n".join(chunk) + "\n")
            if crib is not None and k == 0:
                (REFERENCE / "ormsby" / name).write_text(
                    "\n\n".join(crib) + "\n")
            e = {"file": name, "title": title, "part": k + 1,
                 "of": len(chunks),
                 "words": sum(len(p.split()) for p in chunk)}
            if key:
                e["chapter"] = key
            if kind == "chapter" and chap_no == 1 and k == 0:
                e["part_before"] = ("Part One (1605)" if part == 1
                                    else "Part Two (1615)")
            manifest.append(e)
            idx += 1

    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} Spanish words; "
          f"{sum(1 for m in manifest if m['of'] > 1)} split parts; "
          f"{len(list((REFERENCE / 'ormsby').glob('*.txt')))} crib files")
    for m in manifest[:6]:
        pre = f"  -- {m['part_before']} --\n" if m.get("part_before") else ""
        print(f"{pre}  {m['file']}  {m['words']:6,}w  {m['title'][:64]}")


if __name__ == "__main__":
    main()
