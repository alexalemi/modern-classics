"""Build chapters/ (Latin) + reference/ (Riley's English prose crib) +
manifest.json for Ovid's Metamorphoses.

SOURCES (kept raw under src_raw/):
- Latin: The Latin Library's 15 books (met1.html .. met15.html) — clean
  verse-per-line with line numbers every 5 lines.
- English crib: Henry T. Riley's literal prose translation (Bohn, 1851)
  from Project Gutenberg #21765 (Books I-VII) and #26073 (VIII-XV).

This project translates FROM THE LATIN into a vivid modern PROSE
retelling; Riley's prose is kept per-file under reference/ as a
comprehension crib (mythological names, who-does-what), never as the
source. The de-officiis/ directory is the Latin+crib pipeline precedent.

ALIGNMENT KEY: every Riley segment heads with its Latin line-range, e.g.
"FABLE I. [I.5-31]" or "THE ARGUMENT. [I.1-4]". We slice the Latin by
those ranges and pair each fable's cleaned prose to the same lines. Parts
are cut at FABLE boundaries so episodes never split across files.

Riley cleaning: drop [Footnote N: ...] blocks and the EXPLANATION essays
(mythological commentary, not translation); strip inline [N] markers and
{supplied-word} braces (contents kept); keep the fable summary blurb as a
short [line-range — gist] label at the head of each crib segment.

Structure: 15 books = 15 chapters titled "Book I".."Book XV"; each book
split into ~TARGET-Latin-word parts (most books -> 2-3 parts). Latin
verse is dense, and a vivid English retelling runs long, so expect modern
English >= ~1.6x the Latin word count -- run verify.py with
--min-ratio 1.4 --max-ratio 2.4.
"""

import html as H
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
RAW = BOOK / "src_raw"
TARGET = 2600          # Latin words per part (episode-aligned)
MAXPART = 3600         # never exceed

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV"]
RVAL = {"I": 1, "V": 5, "X": 10, "L": 50}


def roman_to_int(s):
    tot, prev = 0, 0
    for c in reversed(s):
        v = RVAL[c]
        tot += -v if v < prev else v
        prev = max(prev, v)
    return tot


def latin_verses(n):
    """Return the list of Latin verses for book n (1-indexed line k -> verses[k-1])."""
    t = (RAW / f"met{n}.html").read_text(encoding="latin-1")
    t = re.sub(r"<[^>]+>", "", t)
    t = H.unescape(t.replace("&nbsp;", " "))
    out = []
    for ln in t.split("\n"):
        s = ln.rstrip()
        if not s.strip():
            continue
        low = s.strip().lower()
        if ("metamorphoseon" in low or low.startswith("ovid:") or low == "ovid"
                or "classics page" in low or "the latin library" in low):
            continue
        # some verse-pairs are joined on one line with the 5-line number
        # embedded between them: "...illis.    495    Ecce..." -> split
        for piece in re.split(r"\s{2,}\d+\s{2,}", s):
            piece = re.sub(r"\s+\d+[a-z]?\s*$", "", piece)   # trailing (a/b) line no.
            if piece.strip():
                out.append(piece.strip())
    return out


def clean_prose(text):
    """Strip Riley's apparatus from a fable's prose translation."""
    # drop footnote blocks (non-nested)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\[Footnote\b[^\[\]]*\]", "", text, flags=re.S)
    text = re.sub(r"\[\d+\]", "", text)         # inline footnote markers
    text = re.sub(r"\{([^{}]*)\}", r"\1", text)  # {supplied words} -> words
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # rejoin hard-wrapped lines into paragraphs
    paras, cur = [], []
    for ln in text.split("\n"):
        s = ln.strip()
        if s:
            cur.append(s)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(paras).strip()


def riley_segments(path, books):
    """Parse a Riley volume into per-book ordered fable segments.
    Returns {book_int: [(start, end, blurb, prose), ...]}."""
    t = path.read_text(encoding="utf-8")
    # isolate the translation body: from 'BOOK THE FIRST.' onward
    # split on segment headings, keeping the ref
    # headings vary: "FABLE I. [I.5-31]", "FABLES I. AND II. [XII.1-145]",
    # "FABLES IV. V. AND VI. [XV.479-621]", "THE ARGUMENT. [I.1-4]"
    hdr = re.compile(
        r"^(?:FABLES?\b[^\[\]]*|THE ARGUMENT\.?\s*)\[([IVXL]+)\.(\d+)-(\d+)\]\s*$",
        re.M)
    marks = list(hdr.finditer(t))
    result = {}
    for i, m in enumerate(marks):
        bk = roman_to_int(m.group(1))
        if bk not in books:
            continue
        start, end = int(m.group(2)), int(m.group(3))
        body = t[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(t)]
        # cut off the EXPLANATION essay (commentary, not translation)
        cut = re.search(r"^\s*EXPLANATION\.\s*$", body, re.M)
        if cut:
            body = body[:cut.start()]
        # the fable summary blurb = the indented lines right after heading,
        # before the first non-indented prose line; capture then remove
        blurb = ""
        lines = body.split("\n")
        j = 0
        while j < len(lines) and not lines[j].strip():
            j += 1
        blurb_lines = []
        while j < len(lines) and (lines[j].startswith("  ") and lines[j].strip()):
            blurb_lines.append(lines[j].strip()); j += 1
        if blurb_lines:
            blurb = clean_prose(" ".join(blurb_lines))
            blurb = re.sub(r"\s+", " ", blurb).strip()
        prose = clean_prose("\n".join(lines[j:]))
        result.setdefault(bk, []).append((start, end, blurb, prose))
    return result


def _crib_of(group):
    return "\n\n".join(
        f"[lines {a}-{b} — {bl}]\n{pr}" if bl else f"[lines {a}-{b}]\n{pr}"
        for (a, b, bl, pr) in group)


def split_fables(fables, verses):
    """Group ordered fables into even parts of ~TARGET Latin words, cut at
    fable boundaries (cutting *before* a fable that would overshoot). A
    post-pass line-splits any part still larger than MAXPART, so no file
    is unmanageably big; a line-split part carries its crib on the first
    piece and a pointer on the rest. Returns [(lat_text, crib_text), ...]."""
    def wc(a, b):
        return sum(len(v.split()) for v in verses[a - 1:b])

    total = sum(wc(s, e) for (s, e, _, _) in fables)
    nparts = max(1, round(total / TARGET))
    per = total / nparts if nparts else total

    grouped, cur, cur_start, made = [], [], None, 0
    for (s, e, blurb, prose) in fables:
        this = wc(s, e)
        if (cur and made < nparts - 1
                and wc(cur_start, cur[-1][1]) + this > per * 1.25):
            grouped.append((cur_start, cur[-1][1], list(cur)))
            made += 1
            cur, cur_start = [], None
        if cur_start is None:
            cur_start = s
        cur.append((s, e, blurb, prose))
    if cur:
        grouped.append((cur_start, cur[-1][1], list(cur)))

    parts = []
    for (a, b, group) in grouped:
        lines = verses[a - 1:b]
        if len(" ".join(lines).split()) <= MAXPART:
            parts.append(("\n".join(lines), _crib_of(group)))
            continue
        nsub = max(2, round(len(" ".join(lines).split()) / TARGET))
        step = -(-len(lines) // nsub)
        for si in range(0, len(lines), step):
            chunk = lines[si:si + step]
            if si == 0:
                crib = _crib_of(group)
            else:
                ln0 = a + si
                crib = (f"[lines {ln0}-{ln0 + len(chunk) - 1} — continues the "
                        f"previous part; see its crib for this stretch]")
            parts.append(("\n".join(chunk), crib))
    return [p for p in parts if p[0].strip()]


def main():
    (BOOK / "chapters").mkdir(exist_ok=True)
    (BOOK / "reference").mkdir(exist_ok=True)
    seg1 = riley_segments(RAW / "riley_21765.txt", set(range(1, 8)))
    seg2 = riley_segments(RAW / "riley_26073.txt", set(range(8, 16)))
    segs = {**seg1, **seg2}

    manifest, fileno = [], 0
    tot_lat = 0
    for bi in range(1, 16):
        verses = latin_verses(bi)
        fables = sorted(segs.get(bi, []))
        title = f"Book {ROMAN[bi - 1]}"
        if not fables:
            print(f"  !! no crib segments for book {bi}")
            continue
        parts = split_fables(fables, verses)
        for pi, (lat, crib) in enumerate(parts, 1):
            fn = f"{fileno:03d}.txt"
            out = [title]
            if len(parts) > 1:
                out.append(f"\n(Part {pi} of {len(parts)})")
            out.append("\n" + lat)
            (BOOK / "chapters" / fn).write_text("\n".join(out) + "\n",
                                                encoding="utf-8")
            (BOOK / "reference" / fn).write_text(crib + "\n", encoding="utf-8")
            w = len(lat.split())
            tot_lat += w
            manifest.append({"file": fn, "title": title, "roman": ROMAN[bi - 1],
                             "part": pi, "of": len(parts), "words": w})
            fileno += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"-> {fileno} files (15 books), {tot_lat} Latin words")
    for m in manifest:
        print(f"  {m['file']}  {m['title']:<9} {m['part']}/{m['of']} {m['words']:>5}w")


if __name__ == "__main__":
    main()
