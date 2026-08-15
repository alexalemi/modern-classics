#!/usr/bin/env python3
"""Prepare a SELECTED Burton Nights for translation.

Burton's Thousand Nights and a Night runs to ten volumes plus six
Supplemental — about 1.8M words, five Don Quixotes. This is therefore a
SELECTED volume, the shape already used for Montaigne's essays, Cato's
letters and Plutarch's lives. What is taken, and why:

    the frame            Shahryar and Shahrazad; without the Conclusion
                         (vol 10) the book has no ending at all
    the Baghdad cycle    Trader and the Jinni, Fisherman and the Jinni,
                         Porter and the Three Ladies, the three Kalandars
    the Hunchback cycle  the comic masterpiece, and the clearest display
                         of the Nights' box-within-box construction
    vol 6                Sindbad's seven voyages, the City of Brass
    Supplemental 3       Aladdin and Ali Baba — the two "orphan" tales
                         that are not in Burton's main Calcutta II text

THE APPARATUS IS NOT THE BOOK. Every volume carries a `Footnotes`
section (31k words in vol 1 alone) of Victorian racial-sexual
ethnography, plus a Terminal Essay. All of it is cut here at the
`Footnotes` line and the inline [FN#nnn] markers are stripped. It stays
available in source/ as a crib, on the bunyan/Offor precedent: consult
where a modern reader genuinely cannot follow, never translate from.

FOUR TRAPS, all of which would have shipped silently:

 1. THE OPENING DOXOLOGY IS SET IN ALL CAPS ("PRAISE BE TO ALLAH * THE
    BENEFICENT KING * ...") and assemble.is_subheading() reads an
    all-caps line as a heading. It is also punctuated with ASTERISKS,
    which mark the rhyme-units of saj', and this pipeline is markup-free
    so those would ship as literal asterisks. Both are solved the same
    way: the doxology is emitted as a tab-indented block, one saj' unit
    per line, which is what it actually is — rhymed prose. assert_no_caps()
    then refuses to let any other all-caps paragraph through.

 2. THE VERSE IS NOT SHORT-LINED, and the short-line test that served the
    five Royal Institution books gets every poem in this book wrong. A
    couplet is ONE logical line wrapped at ~72 chars, with a centred `*`
    at the caesura between its two hemistichs — so all 176 poems looked
    like prose and 545 asterisks would have printed on the page. The
    asterisk IS the signal; see is_verse_run() and verse_lines().

 3. SEVEN FOOTNOTE MARKERS HAVE NO CLOSING BRACKET, so a strict
    `\\[FN#\\d+\\]` leaves the number welded into the sentence: "I
    winked[FN#5886 at her". This is the bunyan noteref trap exactly — a
    bare number in the text that passes every mechanical check this
    project has. assert_clean() refuses any survivor.

 4. THE NIGHT-BREAKS ARE THE FRAME'S MECHANISM, not filler ("And
    Shahrazad perceived the dawn of day and ceased to say her permitted
    say"). They are counted here and asserted, so that a translation
    cannot quietly drop them.
"""
import json, pathlib, re, sys

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"
# Burton's paragraphs are enormous -- a whole night can be one 3,700-word
# block -- so split_oversize can only cut between them. MAX is deliberately
# well under the project's usual 7k: a translation agent must OUTPUT as much
# as it reads, and a coarse cut on a 6,700-word tale is worse than an extra
# file.
TARGET, MAX = 3400, 5200

# ---------------------------------------------------------------- selection
# Each range is (volume, start-anchor, end-anchor). Anchors are distinctive
# substrings and each MUST match exactly once -- a silently-missed anchor
# would take the wrong span of text and nothing downstream would notice.
RANGES = [
    # volume, start anchor, end anchor, title for an UNTITLED opening block.
    # That last field matters: two of these ranges begin mid-tale, and
    # without it the closing Conclusion silently inherits "Prologue" and
    # the book's ending ships under the book's opening title.
    ("pg3435", "In the Name of Allah,", "THE TALE OF THE THREE APPLES",
     "The Story of King Shahryar and His Brother"),
    ("pg3435", "THE HUNCHBACK’S TALE.", None, None),
    ("pg3440", "Sindbad The Seaman", "CRAFT AND MALICE OF WOMEN", None),
    ("pg3447", "ALAEDDIN; OR, THE WONDERFUL LAMP.", "KHUDADAD", None),
    ("pg3447", "ALI BABA AND THE FORTY THIEVES.", "ALI KHWAJAH", None),
    ("pg3444", "Now, during this time, Shahrazad had borne", "FINIS.",
     "Conclusion"),
]

# (anchor, title, lines of display matter to drop after it). See find_extras.
ORD = ("First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh")
EXTRA_HEADINGS = [
    (f"{'' if o == 'First' else 'The '}{o} Voyage of Sindbad the Seaman.",
     f"The {o} Voyage of Sindbad the Seaman", 0) for o in ORD
] + [
    # Burton prints the Calcutta recension's wholly different seventh voyage
    # after the first, behind seven centred lines of display matter. Kept --
    # it is a real tale, it is short, and the Nights having more than one of
    # everything is part of what the book is -- but the scholarly billboard
    # is replaced by a title that says the same thing in five words.
    ("A Translation of",
     "The Seventh Voyage of Sindbad the Seaman: The Calcutta Version", 14),
]

SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "his", "her", "in",
         "of", "on", "or", "the", "to", "with"}

PROPER = ("Allah", "Mohammed", "Lord", "Amen")
# Burton uses TWO wordings for the same formula -- "Shahrazad perceived the
# dawn of day" (70) and "Shahrazad was surprised by the dawn of day" (76).
# Counting only the first reports half the frame and hides a loss.
NIGHT_BREAK = re.compile(r"(perceived|surprised by) the dawn of day")
# Seven markers in the four volumes are missing their closing bracket, so a
# strict pattern welds a footnote number into the sentence -- "I winked[FN#5886
# at her". assert_clean() below refuses to let any survivor through.
FN = re.compile(r"\[FN#\d+\]?")


# (volume, wrong, right). Each MUST still be present or prep stops -- the
# thompson/appendix_fixes.py discipline: a correction that silently stops
# matching is worse than no correction, because it looks like it is working.
# Both of these were found by check.py's numeral diff, which is the only
# thing in the toolchain that looks at digits at all.
SOURCE_FIXES = [
    # "ante" for "and" in a night header. Caught by check.py's night-number
    # sequence, not by anything mechanical in verify.py: the header is
    # otherwise well formed, the count of night breaks is right, and the
    # word ratio does not move. A translator reading only this file has no
    # way to know whether the oddity is Burton's or the compositor's.
    ("pg3440", "the Five Hundred ante Seventy-fifth Night",
     "the Five Hundred and Seventy-fifth Night"),
    # the same "ante" for "and" misprint, in a different Gutenberg volume --
    # so it is the transcription's habit, not a one-off. Ali Baba's headers
    # take the other form ("The end of the Nth Night"), which is why this
    # one reads oddly next to its neighbour above.
    ("pg3447", "The end of the Six Hundred ante Thirty-fourth Night",
     "The end of the Six Hundred and Thirty-fourth Night"),
    # a zero set for the letter O in a vocative
    ("pg3435", '"0 my master what hast thou here',
     '"O my master what hast thou here'),
    # print furniture: the volume colophon sits inside the last kept
    # section and would have been translated as though it were text
    ("pg3435", "\n\nEnd of Vol. 1.\n", "\n"),
    # A DITTOGRAPH in the second voyage: the compositor's eye skipped back
    # a line, so a whole clause repeats and the roc is made to carry off
    # the rhinoceros's EYES. The sense is plain from the surrounding
    # sentences -- the elephant's fat blinds the rhinoceros, and THEN the
    # roc carries off rhinoceros and elephant together. The duplicate goes.
    ("pg3440",
     "the shore. Then comes the bird Rukh and carrieth off both the\n"
     "rhinoceros’s eyes and blindeth him, so that he lieth down on the "
     "shore.\nThen comes",
     "the shore. Then comes"),
]


def load(stem):
    """Gutenberg wrapper off, and everything from `Footnotes` down."""
    t = (SRC / f"{stem}.txt").read_text(errors="replace")
    for vol, wrong, right in SOURCE_FIXES:
        if vol != stem:
            continue
        if wrong not in t:
            sys.exit(f"{stem}: source fix no longer matches: {wrong!r}")
        t = t.replace(wrong, right)
    a = re.search(r"\*\*\* ?START OF.*?\*\*\*", t, re.S)
    b = re.search(r"\*\*\* ?END OF", t)
    body = t[a.end():b.start()]
    lines = body.split("\n")
    cut = [i for i, l in enumerate(lines) if re.match(r"^\s*Footnotes\s*$", l)]
    if not cut:
        sys.exit(f"{stem}: no `Footnotes` line -- apparatus cannot be separated")
    return "\n".join(lines[:cut[0]])


def span(text, start, end, label):
    i = text.find(start)
    if i < 0 or text.count(start) != 1:
        sys.exit(f"{label}: start anchor {start!r} matched {text.count(start)} times")
    if end is None:
        return text[i:]
    j = text.find(end, i)
    if j < 0 or text.count(end) != 1:
        sys.exit(f"{label}: end anchor {end!r} matched {text.count(end)} times")
    return text[i:j]


def clean(s):
    s = FN.sub("", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 (" ", " "), (" ", " "), ("—", "—"), ("_", "")):
        s = s.replace(a, b)
    return re.sub(r"[ \t]+", " ", s).strip()


def titlecase(t):
    """Burton sets some tale headings in caps and some in title case. Level
    them, so that nothing all-caps reaches the manifest and the translation
    prompts can quote an exact heading string."""
    letters = [c for c in t if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.9:
        return t
    words, out = t.lower().split(), []
    for i, w in enumerate(words):
        # first word, and the word after a ; or : , always take a capital
        big = i == 0 or w not in SMALL or out[-1].endswith((";", ":"))
        out.append(w[:1].upper() + w[1:] if big else w)
    return " ".join(out)


def is_heading(lines, i):
    """>=3 blank lines, a short line, then >=2 blank. A range may OPEN on
    its own heading (Aladdin, Ali Baba, the Hunchback are extracted by
    anchoring on the heading itself), so at the top of a block only the
    trailing blanks are required -- otherwise the title falls into the body
    as an all-caps paragraph and assemble.py renders it as a heading twice."""
    l = lines[i].strip()
    if not l or len(l) > 75:
        return False
    if i >= 3:
        if any(lines[i - k].strip() for k in (1, 2, 3)):
            return False
    elif any(lines[k].strip() for k in range(i)):
        return False
    return i + 2 < len(lines) and not lines[i + 1].strip() and not lines[i + 2].strip()


def find_extras(lines):
    """Headings the white-space rule cannot reach -> {index: (title, drop)}.

    Burton sets the seven voyage headings behind only TWO blank lines, so the
    strict rule misses every one of them and Sindbad ships as a single
    32,000-word tale in ten unlabelled parts. Relaxing the rule is not the
    answer: at two-before/one-after it also promotes 28 verse lead-ins ("And
    another saith:—") to headings. Name them instead, and assert each anchor
    resolves exactly once."""
    found = {}
    for anchor, title, drop in EXTRA_HEADINGS:
        hits = [i for i, l in enumerate(lines) if clean(l).startswith(anchor)]
        if len(hits) > 1:
            sys.exit(f"extra heading {anchor!r} matched {len(hits)} lines")
        if hits:
            found[hits[0]] = (title, drop)
    return found


def is_verse_run(run):
    """Burton's verse, TWO shapes -- and the second is the one that matters.

    The short-line test that served the five lecture books is WRONG here.
    This transcription sets each couplet as ONE logical line wrapped at ~72
    characters, so every verse line is long, and 176 poems were classified
    as prose. What actually marks them is the ASTERISK: Burton prints a
    centred `*` at the caesura between the two hemistichs of an Arabic
    verse line. In a markup-free pipeline those would have shipped as 545
    literal asterisks on the page."""
    letters = [c for c in " ".join(run) if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.9:
        return False   # the all-caps doxology: saj', not verse. fix_doxology
    if any("*" in l for l in run):
        return True
    if len(run) < 2:
        return False
    return all(len(l.rstrip()) <= 62 for l in run) and \
        (any(len(l) - len(l.lstrip()) >= 3 for l in run) or len(run) >= 3)


HEMI_BREAK = re.compile(r"[.!?;](?=\s)")


def split_middle(chunk):
    """Cut a between-asterisks chunk into (end of couplet k, start of k+1).

    Splitting the run on `*` gives one chunk per caesura, but the boundary
    between one couplet's SECOND hemistich and the next couplet's FIRST is
    unmarked -- Burton only prints the caesura. What marks it is that a
    couplet closes a sentence: ".! ?" then a capital.

    Do NOT simply take the first such boundary. A hemistich may end a
    sentence inside itself ("Lot! Enjoy the Present passing well"), and
    cutting there leaves a four-character line. Take the boundary nearest
    the chunk's midpoint instead, and only if both halves survive it --
    the two hemistichs of a line are near enough the same length, which is
    what makes the poem scan."""
    best, mid = None, len(chunk) / 2
    for m in HEMI_BREAK.finditer(chunk):
        i = m.end()
        if i < 12 or len(chunk) - i < 12:
            continue
        if not chunk[i:].lstrip()[:1].isupper():
            continue
        if best is None or abs(i - mid) < abs(best - mid):
            best = i
    return [chunk[:best].strip(), chunk[best:].strip()] if best else [chunk]


def verse_lines(run):
    """Physical lines -> hemistichs, one per output line.

    The run is joined back into one string FIRST and cut on the asterisks,
    rather than un-wrapping line by line. Line-by-line cannot work: a
    wrapped continuation usually begins in lower case, but not always, and
    a hemistich opening on a capital ("Yet ne'er a star but / Sun and Moon
    by eclipse is overta'en") gets torn in half while its neighbour is left
    carrying two hemistichs at once. Both halves of that failure are
    invisible to every check in the toolchain -- the words are all present,
    in order, with the right total."""
    joined = clean(" ".join(l.strip() for l in run))
    chunks = [c.strip() for c in joined.split("*")]
    out = []
    for i, c in enumerate(chunks):
        if not c:
            continue
        out += [c] if i in (0, len(chunks) - 1) else split_middle(c)
    return [x for x in out if x]


def normalise(block):
    """One paragraph per line; verse kept as a tab-indented block."""
    paras, run = [], []

    def flush():
        if not run:
            return
        if is_verse_run(run):
            paras.append("\t" + "\n\t".join(verse_lines(run)))
        else:
            paras.append(clean(" ".join(x.strip() for x in run)))
        run.clear()

    for raw in block.split("\n"):
        if raw.strip():
            run.append(raw.rstrip())
        else:
            flush()
    flush()
    return "\n\n".join(p for p in paras if p.strip())


def fix_doxology(paras):
    """The all-caps saj' invocation -> a tab-indented block, one rhyme-unit
    per line. Solves the all-caps-reads-as-heading trap and the literal
    asterisks in one move."""
    out = []
    for p in paras:
        letters = [c for c in p if c.isalpha()]
        if len(p.split()) > 12 and letters and \
                sum(c.isupper() for c in letters) / len(letters) > 0.9:
            units = [u.strip(" *") for u in p.split("*")]
            units = [u[0] + u[1:].lower() for u in units if u.strip()]
            block = "\n".join(units)
            # Case is information the caps destroyed: "PRAISE BE TO ALLAH"
            # sentence-cases to "allah". Restore the proper nouns by name,
            # and refuse to run if one of them is no longer there -- a silent
            # miss would ship the name of God in lower case.
            for w in PROPER:
                if w.lower() not in block.lower():
                    sys.exit(f"doxology: expected proper noun {w!r} not found")
                block = re.sub(rf"\b{w}\b", w, block, flags=re.I)
            out.append("\t" + block.replace("\n", "\n\t"))
        else:
            out.append(p)
    return out


def assert_clean(text, label):
    """No apparatus survivors, and no literal asterisk: the pipeline is
    markup-free, so a `*` on the page is a bug and not a caesura."""
    for bad in ("FN#", "*"):
        if bad in text:
            i = text.index(bad)
            sys.exit(f"{label}: {bad!r} survived into the text:\n  "
                     f"{text[max(0, i - 60):i + 60]!r}")


def assert_no_caps(text, label):
    """NEVER write an all-caps line: assemble.py renders it as a heading."""
    for line in text.split("\n"):
        s = line.strip()
        letters = [c for c in s if c.isalpha()]
        if len(s.split()) >= 4 and letters and \
                sum(c.isupper() for c in letters) / len(letters) > 0.9:
            sys.exit(f"{label}: all-caps line would render as a heading:\n  {s[:90]}")


def split_oversize(paras):
    words = [len(p.split()) for p in paras]
    total = sum(words)
    if total <= MAX:
        return [paras]
    # A greedy proportional cut cannot hit the target when one paragraph is
    # 2,193 words long -- it just lands after it, and part 1 comes out at
    # 5,965. So ask for more parts until every part actually fits.
    for n in range(max(2, round(total / TARGET)), len(paras) + 1):
        per, cum, cuts = total / n, 0, []
        for i, w in enumerate(words):
            cum += w
            if len(cuts) < n - 1 and cum >= per * (len(cuts) + 1):
                cuts.append(i + 1)
        parts, prev = [], 0
        for c in cuts + [len(paras)]:
            parts.append(paras[prev:c]); prev = c
        parts = [p for p in parts if p]
        if all(sum(len(x.split()) for x in p) <= MAX for p in parts):
            return parts
    return parts


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.txt"):
        old.unlink()

    tales = []
    for vol, start, end, opening in RANGES:
        text = load(vol)
        block = span(text, start, end, vol)
        lines = block.split("\n")
        given = find_extras(lines)
        marks = sorted(set(given) |
                       {i for i in range(len(lines)) if is_heading(lines, i)})
        # text before the first heading belongs to the opening section
        bounds = ([0] if 0 not in marks else []) + marks + [len(lines)]
        for k in range(len(bounds) - 1):
            i, j = bounds[k], bounds[k + 1]
            titled = i in marks
            if i in given:
                title, drop = given[i]
            else:
                title = titlecase(clean(lines[i]).rstrip(".")) if titled else opening
                drop = 0
            body = "\n".join(lines[i + 1 + drop:j] if titled else lines[i:j])
            if len(body.split()) < 150:
                continue
            tales.append((title, body))

    manifest, n = [], 0
    for title, body in tales:
        paras = fix_doxology(normalise(body).split("\n\n"))
        parts = split_oversize(paras)
        for pi, part in enumerate(parts, 1):
            text = "\n\n".join(part) + "\n"
            assert_no_caps(text, f"{title} part {pi}")
            assert_clean(text, f"{title} part {pi}")
            (OUT / f"{n:03d}.txt").write_text(text)
            manifest.append({
                "file": f"{n:03d}.txt",
                "title": title or "Prologue",
                "part": pi, "of": len(parts),
                "words": len(text.split()),
            })
            n += 1

    nights = sum(len(NIGHT_BREAK.findall((OUT / m["file"]).read_text()))
                 for m in manifest)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    total = sum(m["words"] for m in manifest)
    print(f"{n} files, {total:,} words, {len(tales)} tales")
    print(f"night-breaks carried through: {nights}")
    if nights < 20:
        sys.exit("too few night-breaks -- the frame mechanism has been lost")


if __name__ == "__main__":
    main()
