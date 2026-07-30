"""Build chapters/ + manifest.json for J. A. Fleming's Waves and Ripples in
Water, Air, and Aether from the Project Gutenberg plain text (#71757).

The Christmas 1901 course at the Royal Institution — the third Royal
Institution Christmas Lecture volume in the collection, after Faraday's
two. Fleming opens by defending the word "juvenile" and then gives six
chapters that run from ripples on a pond to Marconi's coherer.

FIGURES. The Gutenberg package ships all 87 plates, but — unlike the
Faraday books — their FILENAMES carry no figure numbers at all
(image003.jpg, image046a.jpg). The mapping is recovered from the HTML
edition instead, where each <img> is followed by its own "Fig. N."
caption; prep.py copies them to site/images/fleming/figN.jpg. Four
plates are special:

  frontis.jpg   -> front   the Graphic's drawing of a Christmas Lecture
                           in progress. The book labels it "Fig. 46",
                           cross-referenced by page number, but nothing
                           in the prose refers to it, so it stays the
                           frontispiece.
  image094.jpg  -> 42a     Fig. 42 is a TWO-PART plate of yacht hull
  image095.jpg  -> 42b     lines (America/Vigilant, Genesta/Valkyrie).
  music160.jpg  -> music   the middle-C clef sign, never numbered. An id
                           with no digits renders with no "Figure N"
                           prefix; its caption stands alone. NOTE that
                           this one is a BARE "[Illustration]" with no
                           colon and no caption — the only such marker
                           in the book, and the reason ILLUS makes the
                           caption optional. Requiring the colon left it
                           unconverted in the text AND freed the "music"
                           id for the next unnumbered block to claim,
                           which put this treble clef where chapter 6's
                           line of Morse code belonged.

Ten of the 89 illustration markers name no figure: the frontispiece,
three stroboscopic photographs captioned only by elapsed time, the two
yacht plates, a "Gamut of Æther Waves", and the Morse alphabet, the
Morse numerals and a line of Morse code. The last three are TEXT set as
illustrations, not images at all — they are turned into indented blocks
rather than figure markers.

Fleming's own 27 footnotes are anchored in the body and gathered in a
FOOTNOTES block at the back. As in candle/ and forces/ they are cut
loose and inlined, but as "Note: ..." — they are the author's, not an
editor's, so they keep his voice, not a third-person one.

Dropped: the transcriber's note, the contents, the index, and the
list of corrections at the end.

Ratio note for verify: English -> English modernization of spoken
lecture prose. Run verify.py with --min-ratio 0.85 --max-ratio 1.3.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
SITE_IMAGES = BOOK.parent / "site" / "images" / "fleming"
TARGET = 2800
MAX = 3500

CHAPTER = re.compile(r"^\s*CHAPTER ([IVX]+)\.\s*$")
# The colon and caption are OPTIONAL: the middle-C clef sign in chapter 4 is
# a bare "[Illustration]" with nothing after it, and a regex demanding the
# colon walks straight past it, leaving the raw marker in the chapter text.
ILLUS = re.compile(r"\[Illustration(?::\s*(.*?))?\]", re.S)
ANCHOR = re.compile(r"\[(\d+)\]")

TITLES = [
    "Chapter One: Water Waves and Water Ripples",
    "Chapter Two: Waves and Ripples Made by Ships",
    "Chapter Three: Waves and Ripples in the Air",
    "Chapter Four: Sound and Music",
    "Chapter Five: Electric Oscillations and Electric Waves",
    "Chapter Six: Waves and Ripples in the Aether",
]

# Markers that are typeset TEXT, not plates: kept as indented blocks. Besides
# the two named Morse tables, chapter 6 spells "How are you?" out in Morse with
# the letters labelled underneath — dashes AND letters, so a dashes-only test
# misses it. Anything carrying a run of three em-dashes and no "FIG." is Morse.
AS_TEXT = re.compile(r"THE MORSE (ALPHABET|NUMERALS)|^[—\s]+$", re.I)
MORSE_RUN = re.compile(r"———")


def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("_", "").replace("=", "")


def strip_wrapper(text):
    text = re.split(r"—+ Start of Book —+\n", text, 1)[-1]
    return re.split(r"\n\s*FOOTNOTES", text, 1)[0], text


def read_notes(whole):
    """{n: text} from the FOOTNOTES block at the back."""
    block = re.split(r"\n\s*FOOTNOTES\s*\n", whole, 1)
    if len(block) < 2:
        return {}
    block = re.split(r"\n\s*INDEX\.", block[1], 1)[0]
    notes = {}
    for m in re.finditer(r"^\[(\d+)\]\s*(.*?)(?=\n\[\d+\]|\Z)", block, re.S | re.M):
        notes[m.group(1)] = clean(m.group(2))
    return notes


def figure_marker(body):
    """[Illustration: FIG. 12.—caption] -> [Figure 12]; the plates the book
    never numbered get their own ids; the Morse tables stay as text."""
    seen = set()

    def sub(m):
        body = m.group(1)
        if body is None:  # bare "[Illustration]" — the unnumbered clef sign
            if "music" in seen:
                return "\n\n"
            seen.add("music")
            return "\n\n[Figure music]\n\n"
        raw = clean(body)
        if AS_TEXT.search(raw) or (MORSE_RUN.search(body) and "FIG." not in raw.upper()):
            # DEDENT rather than strip: "How are you?" in Morse sets the
            # letters on a second row, positioned under their own groups of
            # dashes. Stripping each line independently slides the rows out
            # of register and the labels stop pointing at anything.
            lines = [l.replace("_", "").rstrip() for l in body.split("\n")]
            lines = [l for l in lines if l]
            pad = min((len(l) - len(l.lstrip()) for l in lines), default=0)
            return "\n\n" + "\n".join("    " + l[pad:] for l in lines) + "\n\n"
        # Named plates are matched FIRST: both halves of the two-page yacht
        # figure are captioned "FIG. 42", so a bare number search would
        # collide on them.
        up = raw.upper()
        if "CHRISTMAS LECTURE AT THE ROYAL INSTITUTION" in up:
            fid = "front"
        elif "AMERICA, 1851" in up:
            fid = "42a"
        elif "GENESTA, 1885" in up:
            fid = "42b"
        elif "GAMUT OF" in up:
            fid = "80"
        else:
            # the number is not always first: the milk-splash photographs
            # are captioned "Time after contact = ·0262 sec. FIG. 8."
            # A CAPTIONED plate with no number left at this point is not a
            # plate we have a file for — drop it rather than let it claim a
            # spare id. ("music" belongs to the bare marker, handled above;
            # letting a captioned block grab it put a treble clef where
            # chapter 6's line of Morse code should have been.)
            n = re.search(r"FIG\.\s*(\d+)", raw, re.I)
            fid = n.group(1) if n else None
        if fid is None or fid in seen:
            return "\n\n"
        seen.add(fid)
        return f"\n\n[Figure {fid}]\n\n"

    return ILLUS.sub(sub, body), seen


def normalise(block, notes):
    paras, cur = [], []
    for raw in block.split("\n"):
        line = raw.rstrip()
        if line.strip().startswith("[Figure"):
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(line.strip())
        elif line.startswith("    ") and line.strip():
            if cur:
                paras.append(" ".join(cur)); cur = []
            # Keep a RUN of indented lines together as one block. Emitting
            # them one per paragraph makes assemble.py open a separate <pre>
            # for every line, and each <pre> carries a 2em bottom margin —
            # which strews the 26-line Morse alphabet down half a page and
            # pulls two-line equations apart.
            if paras and paras[-1].startswith("    "):
                paras[-1] += "\n" + line
            else:
                paras.append(line)
        elif line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))

    out = []
    for p in paras:
        if p.startswith("    "):            # preserved indented block
            out.append(p)
            continue
        p = clean(p)
        if not p:
            continue
        cited = ANCHOR.findall(p)
        out.append(ANCHOR.sub("", p))
        for n in cited:
            if n in notes:
                out.append(f"Note: {notes[n]}")
    return "\n\n".join(out)


def split_body(body):
    paras = body.split("\n\n")
    words = [len(p.split()) for p in paras]
    total = sum(words)
    if total <= MAX:
        return [body]
    nparts = max(2, round(total / TARGET))
    per = total / nparts
    cum = [0]
    for w in words:
        cum.append(cum[-1] + w)
    cuts, lo = [], 1
    for k in range(1, nparts):
        target = k * per
        best, best_d = None, None
        for i in range(lo, len(paras)):
            if paras[i - 1].startswith("[Figure"):
                continue
            d = abs(cum[i] - target)
            if best_d is None or d < best_d:
                best, best_d = i, d
        cuts.append(best)
        lo = best + 1
    edges = [0] + cuts + [len(paras)]
    return ["\n\n".join(paras[a:b]) for a, b in zip(edges, edges[1:])]


def body_words(text):
    return len(re.sub(r"^\[Figure[^\]]*\]$", "", text, flags=re.M).split())


def main():
    whole = (BOOK / "source.txt").read_text()
    body_text, full = strip_wrapper(whole)
    notes = read_notes(full)
    lines = body_text.split("\n")

    heads = [i for i, l in enumerate(lines) if CHAPTER.match(l)]
    if len(heads) < 12:
        raise SystemExit(f"expected 12 CHAPTER lines (contents + body), got {len(heads)}")
    body_heads = heads[6:]                   # first six are the contents
    preface_at = next(i for i, l in enumerate(lines) if l.strip() == "PREFACE.")
    preface = "\n".join(lines[preface_at + 1:heads[0]])

    marked, placed = figure_marker("\n".join(lines))
    mlines = marked.split("\n")
    # heading positions shift once markers are substituted: re-find them
    heads = [i for i, l in enumerate(mlines) if CHAPTER.match(l)]
    body_heads = heads[6:] + [len(mlines)]

    (BOOK / "chapters").mkdir(exist_ok=True)
    front = "\n\n".join(["Front Matter", "Frontispiece", "[Figure front]",
                         "Preface", normalise(preface, notes)])
    (BOOK / "chapters" / "000.txt").write_text(front + "\n")
    manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
                 "words": body_words(front),
                 "split_headings": ["Frontispiece", "Preface"]}]

    n = 1
    appendix = None
    for k in range(6):
        block = mlines[body_heads[k] + 1:body_heads[k + 1]]
        j = 0
        while j < len(block) and (not block[j].strip()
                                  or block[j].strip().isupper()):
            j += 1
        parts = split_body(normalise("\n".join(block[j:]), notes))
        # Fleming's two-note APPENDIX trails chapter six with no CHAPTER
        # heading of its own, so it lands inside the chapter's last part.
        # Peel it off AFTER the split, never before: splitting the chapter
        # without it would change the part count and move every boundary.
        if k == 5:
            cut = re.split(r"^[ \t]*APPENDIX\.[ \t]*$", parts[-1], 1, re.M)
            if len(cut) != 2:
                raise SystemExit("APPENDIX. no longer ends chapter six")
            parts[-1] = cut[0].rstrip()
            # drop the printer's diamond rule that follows the heading
            tail = re.sub(r"^[ \t]*—\S*—[ \t]*$", "", cut[1], 1, re.M)
            appendix = "Appendix\n\n" + tail.strip()
        for i, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({"file": fname, "title": TITLES[k],
                             "part": i, "of": len(parts),
                             "words": body_words(part)})
            n += 1

    fname = f"{n:03d}.txt"
    (BOOK / "chapters" / fname).write_text(appendix + "\n")
    manifest.append({"file": fname, "title": "Appendix", "part": 1, "of": 1,
                     "words": body_words(appendix)})

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    used = {m.group(1) for e in manifest for m in
            re.finditer(r"\[Figure (\S+?)\]",
                        (BOOK / "chapters" / e["file"]).read_text())}
    have = {p.stem[3:] if p.stem != "front" else "front"
            for p in SITE_IMAGES.glob("*.jpg")}
    print(f"{len(manifest)} files, {sum(e['words'] for e in manifest)} words, "
          f"{len(used)} figures placed, {len(notes)} notes")
    if used - have:
        print("MARKERS WITH NO IMAGE:", sorted(used - have))
    if have - used:
        print("IMAGES NEVER PLACED:", sorted(have - used))
    for e in manifest:
        print(f"  {e['file']}  {e['words']:>5}  {e['title'][:44]} "
              f"({e['part']}/{e['of']})")


if __name__ == "__main__":
    main()
