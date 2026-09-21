"""Hermann von Helmholtz, On the Sensations of Tone, translated by Alexander
J. Ellis (second English edition, 1885): a RESTORED EDITION.

    python3 helmholtz/prep.py

THE TEXT IS helmholtz/proof/NNN.txt, one file per leaf, READ FROM THE PAGE
IMAGE of Archive.org's onsensationsofto00helmrich (the 1895 reprint of the
1885 edition, University of California copy). No usable transcription
exists: the OCR draft was a convenience only, and it wrecks the formulas,
the note names and the tables. proof_instructions.txt is the standing
instruction the leaves were read under, and proof_notes.txt records every
reading kept as printed. apply_fixes.py writes proof/ from preproof/ (the
OCR draft) and fixes/ (the corrections, anchored against the draft).

Conventions the proof files carry, resolved here:
  "page: N"         the printed folio; "none" on a page that prints none
                    (a chapter opening), which is inferred from its
                    neighbours and asserted.
  "+ "              continues the paragraph before it, across a page turn
                    or a cut; a word broken across the turn is closed up.
  "Footnote: "      a note, set after the paragraph that cites it;
  "Footnote+ "      the continuation of the last note from the page before.
  [Figure N]        a cut, whose box, printed label and caption are in
                    proof/NNN.plates; cut here from the page image.
  ^^Small Caps^^    plain words.
  ¶                 ELLIS'S QUARTER MARK, see below.

THE APPARATUS IS KEPT. Ellis cites his own pages over a thousand times, by
page and QUARTER ("see p. 77c", "pp. 466-469", "p. 243c'"), and the quarters
are the pilcrows he printed in the margin, three to a page: text before the
first is quarter a, and so on. The Index head explains the primes: "when
there are double columns, [a, b, c, d refer to the quarters] of the first
column, in which case a', b', c', d', refer to the quarters of the second".
A reflowable edition has no pages, so every page start and every pilcrow
becomes a small visible locator ({¶77}, {¶77c}) and every reference a link
to it ({@77c|77c'}), its printed text untouched (assemble.LOC_ANCHOR,
LOC_LINK). A primed reference goes to its quarter's unprimed locator,
which is on the right page and at worst a column away.

LEFT OUT, deliberately: the title pages, the Contents (except its one
headnote, which is text: that everything in [ ] is the Translator's), the
Lists of Figures, Passages in Musical Notes and Tables, and the Index,
whose page numbers mean nothing here and whose job the links now do.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
import mathml  # noqa: E402

PROOF = HERE / "proof"
PNG = HERE / "_src" / "png"
PLATE_DIR = HERE / "_src" / "plates"

# second scans of pages already proofed from a cleaner leaf (proof_notes.txt)
DUPLICATES = {230: 228, 231: 229, 452: 454, 453: 455}
LAST_PAGE = 556                     # p. 556 ends the text; the Index follows
NOTE_MARKS = "⁎†‡§‖"


def leaves():
    ns = sorted(int(p.stem) for p in PROOF.glob("*.txt"))
    for dup, keep in DUPLICATES.items():
        a = (PROOF / f"{dup:03d}.txt").read_text()
        b = (PROOF / f"{keep:03d}.txt").read_text()
        assert a.split("\n", 1)[0] == b.split("\n", 1)[0], (dup, keep)
    return [n for n in ns if n not in DUPLICATES]


def folios(ns):
    """leaf -> printed page (int), or None for the roman front matter.
    A leaf printing no folio takes its neighbour's plus one, asserted
    against the next printed folio."""
    raw = {}
    for n in ns:
        first = (PROOF / f"{n:03d}.txt").read_text().split("\n", 1)[0]
        m = re.fullmatch(r"page: (\S+)", first)
        assert m, (n, first)
        raw[n] = m.group(1)
    out, prev = {}, None
    for n in ns:
        v = raw[n]
        if v.isdigit():
            out[n] = int(v)
            assert prev is None or out[n] == prev + 1, (n, prev, v)
            prev = out[n]
        elif v == "none" and prev is not None:
            out[n] = prev = prev + 1
        elif v == "none" and n >= 27:        # the Introduction's first page, p. 1
            out[n] = prev = 1
        else:
            out[n] = None                   # roman prefaces
    assert out[max(ns)] == LAST_PAGE, out[max(ns)]
    return out


# Corrections to the proof, each (leaf, printed, corrected, reason), each
# asserted to apply exactly once. A misprint that is the author's words is
# kept (proof_notes.txt); these are the ones a reader could only take as
# ours.
PROOF_FIXES = [
    (121, "have gone out of use.", "have gone out of use.†",
     "the print sets the second note's mark as a second asterisk; the note "
     "itself is printed with †, and the proof had dropped the mark"),
    # a note mark the proof wrote as a plain asterisk (ruling 3 is ⁎); a
    # bare * is deleted by emph_safe, and the note loses its reference
    (128, "cutting quality of tone.* The", "cutting quality of tone.⁎ The", "mark typed as *"),
    (225, "all other harmonic intervals.*", "all other harmonic intervals.⁎", "mark typed as *"),
    (256, "determined by the number 7.* But", "determined by the number 7.⁎ But", "mark typed as *"),
    (281, "musical scales known.* Recent", "musical scales known.⁎ Recent", "mark typed as *"),
    (359, "magnitude on this scale.* On", "magnitude on this scale.⁎ On", "mark typed as *"),
    # italic letters glued to a number or inside a word, which the renderer
    # cannot set (ruling 2): roman, as the page-quarter letters are
    (43, "165*s*.", "165s.", "italic shilling sign glued to the figure"),
    (497, "165*s.*", "165s.", "italic shilling sign glued to the figure"),
    (548, "sh*oe*)", "shoe)", "italic letters inside a word"),
    # an italic span longer than the renderer's 400-character cap: two
    # spans, split at the semicolon, set exactly as one
    # formulas pandoc cannot set as written. A radical sign followed by a
    # bracket is the square root of the bracket; a row break "\\ [" is read by
    # LaTeX as an optional spacing argument, so the bracket is braced.
    (407, r"\surd \left[ M^2 \cdot \left(1 - \frac{n^2}{m^2}\right)^2 + T\mu \right]",
     r"\sqrt{\left[ M^2 \cdot \left(1 - \frac{n^2}{m^2}\right)^2 + T\mu \right]}", "\\surd before \\left"),
    (41, r"\\ [\text{or}", r"\\ {[}\text{or}", "row break read as an optional argument"),
    # a set-off block whose first line has no second column, where every
    # other line has two: an empty cell, so the block is one table
    (210, "\t¶ Prime tone = 300\n", "\t¶ Prime tone = 300 | \"\"\n", "uniform table"),
    (458, "uncorrupted ears; that moreover", "uncorrupted ears;* *that moreover", "span over the cap"),
]


def proof_text(n):
    t = (PROOF / f"{n:03d}.txt").read_text()
    # a page-quarter letter set italic after its page number ("p. 259*d*"):
    # roman, ruling 2
    t = re.sub(r"(\d)\*([a-d]'?)\*", r"\1\2", t)
    if n in (514, 544):
        # table rows the proof set without their TAB (a row of cells then
        # renders as a paragraph of pipes)
        t, k = re.subn(r"(?m)^(?!\t|Footnote)(?=[^\n]* \| [^\n]* \| )", "\t", t)
        assert k == {514: 6, 544: 15}[n], (n, k)
    if n == 346:
        # scales 9)-14) carry Ellis's sign for the Pythagorean minor Third
        # as a bare "|", which both renderers read as a table's cell rule:
        # the sign is ∣ (proof_notes.txt, 342-351)
        t, k = re.subn(r"(?m)^(\t\d+\) [^\n|]*?) \| (\*[a-g]₁\*)$", r"\1 ∣ \2", t)
        assert k == 6, k
    # a note with a prime and a subscript is printed with the two stacked; the
    # proof wrote them in both orders (e₁' 144 times, e'₁ 22): one order
    t = re.sub(r"([a-gA-G])('+)([₀-₉]+)", r"\1\3\2", t)
    for leaf, old, new, _ in PROOF_FIXES:
        if leaf == n:
            assert t.count(old) == 1, (n, old, t.count(old))
            t = t.replace(old, new)
    return t


def chunks(n):
    """the leaf's paragraphs. A chunk may hold a prose line and the TAB rows
    of its table with no blank line between: each prose line is a paragraph
    (the proof sets one to a line) and each run of TAB lines one block. A
    note's chunk is split by split_note instead."""
    t = proof_text(n).split("\n", 2)[2]
    out = []
    for c in re.split(r"\n[ ]*\n", t):
        c = c.strip("\n")
        if not c.strip():
            continue
        if c.startswith("Footnote"):
            out.append(c)
            continue
        run = []
        for line in c.split("\n"):
            if line.startswith("\t"):
                run.append(line)
                continue
            if run:
                out.append("\n".join(run)); run = []
            if line.strip():
                out.append(line)
        if run:
            out.append("\n".join(run))
    return out


def split_note(chunk):
    """a footnote chunk -> items: its lines are the note's paragraphs, TAB
    rows a block, a [Figure] line a cut"""
    out = []
    for line in chunk.split("\n"):
        if line.startswith("\t"):
            if out and out[-1][0] == "BLOCK":
                out[-1] = ("BLOCK", out[-1][1] + "\n" + line)
            else:
                out.append(("BLOCK", line))
        elif re.fullmatch(r"\[Figure [^\]]+\]", line.strip()):
            out.append(("FIG", line.strip()[8:-1]))
        elif line.strip():
            out.append(("P", line))
    return out


def marks(p):
    # a mark may sit inside a formula as \text{⁎} (376), so formulas count
    return [c for c in p if c in NOTE_MARKS]


# A page whose FIRST pilcrow falls where no line is printed beside it -- a
# chapter opening's heading space, or a table at the head of the page --
# prints only the later marks, so its first printed mark is c, not b.
QUARTER_START = {27: 1, 33: 1, 178: 1, 400: 1, 209: 1}
# notes whose marks are printed inside a cut, not in the text (386: the
# marks sit in music cuts m5/m6)
NO_MARK_OK = {386,
              182,    # the mark is printed inside music cut m1 ("Minor Sixth.*")
              360}    # the whole page is the tabular note to Fig. 61, cited from the figure's label


def is_heading(p):
    letters = re.sub(r"[^A-Za-z]", "", mathml.MATH.sub("", re.sub(r"\^\^|\*", "", p)))
    return (len(letters) > 2 and letters == letters.upper()
            and not p.startswith(("\t", "+ ", "Footnote")) and len(p) < 160
            and "\n" not in p)


def join_broken(a, b, solid, hyph):
    head = a.split()[-1][:-1]
    tail = b.split()[0]
    w = re.sub(r"[^\w-]", "", head + tail)
    compound = f"{head}-{re.sub(r'[^A-Za-z-]', '', tail)}".lower()
    if compound in hyph and w.lower() not in solid:
        return a + b, compound
    return a[:-1] + b, None


def join(a, b, solid, hyph, kept, where):
    """b continues a across a page turn or a cut"""
    lead = re.match(r"(?:\{¶[^}]*\})+", b)
    if lead and a.endswith("-") and re.match(r"[a-z]", b[lead.end():]):
        # the new page's locator would land inside the rejoined word: set it
        # before the word instead
        toks, b = lead.group(0), b[lead.end():]
        cut = len(a) - len(a.split()[-1])
        a = a[:cut] + toks + a[cut:]
    if a.endswith("-") and not a.endswith(("--", "\u2014")) and re.match(r"[a-z]", b):
        j, comp = join_broken(a, b, solid, hyph)
        if comp:
            kept.append((where, comp))
        return j
    return a + ("\n" if a.split("\n")[-1].startswith("\t") and b.startswith("\t") else " ") + b


def build_stream(ns, page):
    alltext = " ".join((PROOF / f"{n:03d}.txt").read_text() for n in ns)
    solid = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", alltext))
    hyph = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]+-[A-Za-z]+\b", alltext))
    stream, held, kept = [], [], []
    anchors = []                          # every locator emitted, in order
    unplaced, orphans = [], []
    # the last note's place: ("held", i) while it waits for its paragraph to
    # end, ("stream", i) once set; a "Footnote+" on the next page joins it
    last = [None]

    def flush():
        nonlocal held
        if last[0] and last[0][0] == "held":
            last[0] = ("stream", len(stream) + last[0][1])
        stream.extend(held)
        held = []

    def note_list():
        return held if last[0][0] == "held" else stream

    for n in ns:
        pg = page[n]
        q = QUARTER_START.get(n, 0)
        carry = [f"{{¶{pg}}}"] if pg else []  # tokens waiting for the next text
        if pg:
            anchors.append(str(pg))

        def tokens(text):
            """¶ -> the next quarter's locator; any waiting tokens in front"""
            nonlocal q, carry
            def rep(m):
                nonlocal q
                if not pg:
                    return ""
                q += 1
                assert q <= 3, (n, "more than three quarter marks")
                anchors.append(f"{pg}{'abcd'[q]}")
                return f"{{¶{pg}{'abcd'[q]}}}"
            text = re.sub(r"¶ ?", rep, text)
            lead = "".join(carry)
            carry = []
            if text.startswith("\t"):
                return "\t" + lead + text[1:]
            return lead + text

        body = [c for c in chunks(n) if not c.startswith("Footnote")]
        notes = [c for c in chunks(n) if c.startswith("Footnote")]
        pending, places = [], []           # places: stream index of each text item
        for c in body:
            cont = c.startswith("+ ")
            if cont:
                c = c[2:]
            fig = re.fullmatch(r"\[Figure ([^\]]+)\]", c.strip())
            if fig:
                flush()
                stream.append(("PLATE", f"{n:03d}-{fig.group(1)}"))
                continue
            if not cont and is_heading(c):
                # a heading carries no locator: a ¶ beside it waits for the text
                c2 = re.sub(r"^¶ ?", "", c)
                if c2 != c and pg:
                    q += 1
                    anchors.append(f"{pg}{'abcd'[q]}")
                    carry.append(f"{{¶{pg}{'abcd'[q]}}}")
                flush()
                stream.append(("H", c2))
                pending.append(c2)
                places.append(len(stream) - 1)
                continue
            text = tokens(c)
            if cont:
                i = next(i for i in range(len(stream) - 1, -1, -1) if stream[i][0] in ("P", "BLOCK"))
                if stream[i][0] == "BLOCK" and not text.startswith("\t"):
                    # prose resuming after a table set inside its paragraph:
                    # a paragraph of its own, or it is welded into the last cell
                    flush()
                    stream.append(("P", text))
                    i = len(stream) - 1
                else:
                    stream[i] = (stream[i][0], join(stream[i][1], text, solid, hyph, kept, n))
                pending.append(text)
                places.append(i)
            else:
                flush()
                stream.append(("BLOCK" if text.startswith("\t") else "P", text))
                pending.append(text)
                places.append(len(stream) - 1)
        # notes: each follows the paragraph that cites it
        cited = Counter(m for t in pending for m in marks(t))
        used, plan, log = Counter(), [], []
        for c in notes:
            items = split_note(c)
            head = items[0][1]
            if head.startswith("Footnote+"):
                # the rest of the last note of the page before (which may
                # open straight into a table: a bare "Footnote+")
                assert last[0] is not None, n
                lst, k = note_list(), last[0][1]
                if head.strip() != "Footnote+":
                    rest = tokens(head[len("Footnote+ "):])
                    lst[k] = (lst[k][0], join(lst[k][1], rest, solid, hyph, kept, n))
                more = [(t, tokens(x) if t != "FIG" else x) for t, x in items[1:]]
                extra = [("PLATE", f"{n:03d}-{x}") if t == "FIG" else (t, x) for t, x in more]
                idx = k + 1
                for e in extra:
                    lst.insert(idx, e); idx += 1
                if extra and extra[-1][0] == "P":
                    last[0] = (last[0][0], idx - 1)
                continue
            assert head.startswith("Footnote: "), (n, head[:40])
            mark = head[len("Footnote: "):][:1]
            conv = []
            for t, x in items:
                if t == "FIG":
                    conv.append(("PLATE", f"{n:03d}-{x}"))
                else:
                    # a locator waiting at a page that opens on a note goes
                    # after the note's label and mark, not in front of them
                    x = re.sub(r"^((?:\{¶[^}]*\})+)(Footnote: \S+ ?)", r"\2\1", tokens(x))
                    conv.append((t, x))
            if mark in NOTE_MARKS and cited[mark] > 0:
                cited[mark] -= 1
            elif n not in NO_MARK_OK:
                orphans.append((n, head[:70]))
            # A NOTE FOLLOWS THE PARAGRAPH THAT CITES IT: the first on this
            # page carrying its mark that no earlier note has claimed. If
            # that paragraph is the page's last (it may run on overleaf) or
            # a heading, the note waits until the paragraph is finished.
            where = None
            for idx in dict.fromkeys(places):
                have = stream[idx][1].count(mark) if mark in NOTE_MARKS else 0
                if have > used[(idx, mark)]:
                    used[(idx, mark)] += 1
                    where = idx
                    break
            if where is not None and where != places[-1] and stream[where][0] != "H":
                plan.append((where, conv))
                log.append(("plan", conv))
            else:
                held.extend(conv)
                log.append(("held", conv))
        # set the planned notes into the stream, later positions first so
        # earlier indices hold; notes after one paragraph keep their order
        for where in sorted({w for w, _ in plan}, reverse=True):
            flat = [x for w, c in plan if w == where for x in c]
            stream[where + 1:where + 1] = flat
            if last[0] and last[0][0] == "stream" and last[0][1] > where:
                last[0] = ("stream", last[0][1] + len(flat))
        # the page's LAST note is the one a "Footnote+" overleaf continues
        if log:
            dest, conv = log[-1]
            lst = held if dest == "held" else stream
            i = next(i for i in range(len(lst)) if lst[i] is conv[0])
            ks = [j for j in range(i, i + len(conv)) if lst[j][0] == "P"]
            last[0] = (dest, ks[-1])
        if carry and pg:
            unplaced.append((n, carry))
    flush()
    for o in orphans:
        print("ORPHAN NOTE", o)
    assert not orphans, len(orphans)
    return stream, anchors, kept, unplaced


REF_HEAD = re.compile(r"\b([Pp]p?\.\s*)")
LOC = r"(\d{1,3})([a-d])?('?)"
SEP = re.compile(r"(,\s*|\s+and\s+|\s+to\s+|\s*[-–]\s*|\.\s+)")


def link_refs(text, anchors, stats):
    """Ellis's references -> link tokens. Only a reference introduced by
    p./pp. is linked, with the list or range that follows it ("pp. 77c and
    78d'", "pp. 59b to 65b", "p. 76a, b, c"); the lettered numbers left
    over are equation labels, "(1c)", and are not references at all."""
    held = []
    text = mathml.MATH.sub(lambda m: (held.append(m.group(0)), f"\x00{len(held) - 1}\x00")[1], text)

    def target(pg, q):
        # a primed letter (the second column) goes to its quarter's locator
        if pg > LAST_PAGE:
            return None
        for cand in ([f"{pg}{q}"] if q else []) + [f"{pg}{c}" for c in "dcb" if q and c < q] + [str(pg)]:
            if cand in anchors:
                return cand
        return None

    out, pos = [], 0
    for m in REF_HEAD.finditer(text):
        if m.start() < pos:
            continue
        j = m.end()
        first = re.compile(LOC).match(text, j)
        if not first:
            continue
        out.append(text[pos:j])
        page_now = None
        k = j
        cur = first
        while cur:
            if cur.group(1):
                pg = int(cur.group(1))
                page_now = pg
            else:
                pg = page_now
            q = cur.group(2) or ""
            # ONLY A LETTERED REFERENCE IS LINKED. The quarter letters are this
            # book's own system and nobody else's, while a bare page number is
            # as often another book's ("Hopkins, p. 113", "Zamminer [p. 312",
            # "vol. lx. p. 449") as this one's, and a wrong link is worse than
            # none. The unlettered ones stay as printed; the page locators
            # still find them.
            tgt = target(pg, q) if pg and q else None
            shown = cur.group(0)
            if tgt:
                out.append(f"{{@{tgt}|{shown}}}")
                stats["linked"] += 1
            else:
                out.append(shown)
                stats["unlinked"] += 1
                if q:
                    stats.setdefault("_u", []).append(text[max(0, m.start()-30):cur.end()+10])
            k = cur.end()
            sep = SEP.match(text, k)
            if not sep:
                break
            nxt = re.compile(LOC).match(text, sep.end())
            letter = re.compile(r"([a-d])('?)(?![\w*])").match(text, sep.end())
            if nxt and not sep.group(0).startswith("."):
                out.append(sep.group(0))
                cur = nxt
            elif letter and page_now and not sep.group(0).strip() in ("to",):
                # a bare quarter letter continuing the same page: "76a, b, c"
                out.append(sep.group(0))
                cur = re.compile(r"()([a-d])('?)").match(text, sep.end())
            else:
                break
        pos = k
    out.append(text[pos:])
    text = "".join(out)
    return re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], text)


def title_of(h):
    t = R.titlecase(h.rstrip(".").lower())
    t = re.sub(r"\b[IVXL][ivxl]+\b", lambda m: m.group(0).upper(), t)
    return t.replace("Electro-magnetic", "Electro-Magnetic").replace("Bosanquet's", "Bosanquet's")


PART_WORDS = {"I": "One", "II": "Two", "III": "Three"}
FRONT = {"TRANSLATOR'S NOTICE": "Translator's Notice to the Second English Edition",
         "AUTHOR'S PREFACE": None}
# the Contents' one line of text (leaf 015), which the renderers' contents
# would otherwise take with it: set as its own short section after the
# prefaces, where the Contents stood
BRACKET_NOTE = ("⁂ All passages and notes in [ ] are due to the Translator, and the Author "
                "is in no way responsible for their contents.")
NOT_HEADINGS = {"1 [*C*]⁎ 2 [*C*] 3 [*C*]"}      # a row of mode labels, p. 256


def sections_of(stream):
    secs = []
    part = None
    i = 0
    items = list(stream)

    def heads(i):
        out = []
        while i < len(items) and items[i][0] == "H" and items[i][1] not in NOT_HEADINGS:
            out.append(items[i][1]); i += 1
        return out, i

    while i < len(items):
        k, v = items[i]
        if k == "H" and v not in NOT_HEADINGS:
            hs, j = heads(i)
            h0 = hs[0]
            if h0 == "TRANSLATOR'S NOTICE":
                secs.append({"title": FRONT[h0], "stream": []}); i = j; continue
            if h0 == "AUTHOR'S PREFACE":
                assert hs[1] == "TO THE", hs
                secs.append({"title": f"Author's Preface to the {title_of(hs[2])}", "stream": []}); i = j; continue
            if h0 == "INTRODUCTION.":
                secs.append({"title": "Note on the Brackets", "stream": [("P", BRACKET_NOTE)]})
                secs.append({"title": "Introduction", "stream": []}); i = j; continue
            m = re.fullmatch(r"PART (I|II|III)\.", h0)
            if m:
                assert len(hs) >= 5, hs
                part = f"Part {PART_WORDS[m.group(1)]}: {title_of(hs[1])} — {title_of(hs[2].replace('⁎', ''))}"
                hs = hs[3:]
                h0 = hs[0]
            if h0 == "APPENDICES.":
                part = "Appendices"
                hs = hs[1:]; h0 = hs[0]
            m = re.fullmatch(r"(CHAPTER|APPENDIX|SECTION) ([IVXL]+|[A-N])\.", h0)
            if m:
                assert len(hs) >= 2, hs
                kind = m.group(1).title()
                if h0 == "APPENDIX XX.":
                    # Ellis's own appendix, in twelve Sections: a divider of
                    # its own, since the Sections are its chapters
                    part = f"Appendix XX: {title_of(hs[1])}"
                    rest = hs[2:]
                    i = j
                    pending_xx = True
                    if not rest:
                        continue
                    hs = rest; h0 = hs[0]
                    m = re.fullmatch(r"(SECTION) ([A-N])\.", h0)
                    kind = "Section"
                sec = {"title": f"{kind} {m.group(2)}: {title_of(hs[1])}", "stream": [], "chapter": True}
                if part:
                    sec["part_before"], part = part, None
                secs.append(sec)
                for extra in hs[2:]:
                    sec["stream"].append(("P", title_of(extra)))
                i = j
                continue
            # an in-chapter heading ("ASCENDING SCALES."), or a signature
            for h in hs:
                if re.fullmatch(r"[A-Z. ]+\.", h) and len(h.split()) <= 3 and "." in h[:-1]:
                    secs[-1]["stream"].append(("P", h))          # H. HELMHOLTZ.
                else:
                    secs[-1]["stream"].append(("P", title_of(h)))
            i = j
            continue
        if k == "H":
            k = "P"
        secs[-1]["stream"].append((k, v))
        i += 1
    return secs


def plate_specs(ns):
    """{source name: (leaf, box, blanks, label, caption)} from proof/*.plates"""
    out = {}
    for n in ns:
        f = PROOF / f"{n:03d}.plates"
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            pid, box, label, cap = line.split("\t")
            parts = [tuple(int(x) for x in b.split(",")) for b in box.split(" - ")]
            out[f"{n:03d}-{pid}.jpg"] = (n, parts[0], parts[1:], label.strip(), cap.strip())
    return out


def cut_plates(specs):
    """each cut from its page image, blank boxes whitened, the paper lifted
    to white so the cut sits on the page rather than on a grey patch"""
    from PIL import Image, ImageOps
    PLATE_DIR.mkdir(parents=True, exist_ok=True)
    for f in PLATE_DIR.glob("*.jpg"):
        if f.name not in specs:
            f.unlink()
    for name, (n, box, blanks, _, _) in specs.items():
        dst = PLATE_DIR / name
        src = PNG / f"{n:03d}.png"
        if dst.exists() and dst.stat().st_mtime > max(src.stat().st_mtime, (PROOF / f"{n:03d}.plates").stat().st_mtime):
            continue
        im = Image.open(src).convert("L")
        W, H = im.size
        x0, y0, x1, y1 = box
        assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H, (name, box, im.size)
        for b in blanks:
            im.paste(255, b)
        c = im.crop(box)
        c = ImageOps.autocontrast(c, cutoff=(1, 1))
        c.save(dst, "JPEG", quality=90)
    return {name: str(PLATE_DIR / name) for name in specs}


# FOUR SHAPES WITH NO UNICODE FORM, in the ⁎ note on p. 312 (leaf 340):
# Ellis's account of how the square b became both the natural and the sharp.
# Each is cut from the page and set inline (assemble's ⟦g:ID⟧, the byrne
# mechanism), in the order the "[?]"s stand. Boxes are in png/340.png.
GLYPH_CUTS = [
    ((714, 2872, 740, 2910), "a b with a square instead of a round bottom"),
    ((1590, 2452, 1618, 2500), "the cursive written form of h"),
    ((1052, 2566, 1074, 2600), "the b made with two strokes afterwards crossed"),
    ((1628, 2562, 1654, 2618), "the crossed form it degenerated into, the precursor of the sharp"),
    ((1598, 2992, 1620, 3028), "the square-bottomed b"),
]


def glyph_tokens(secs):
    k = 0
    for sec in secs:
        for i, (kind, v) in enumerate(sec["stream"]):
            while "[?]" in v:
                k += 1
                v = v.replace("[?]", f"⟦g:{k:04d}⟧", 1)
            sec["stream"][i] = (kind, v)
    assert k == len(GLYPH_CUTS), k


def write_glyphs():
    """after compose, which clears the image directory"""
    import base64
    import io
    from PIL import Image, ImageOps
    im = Image.open(PNG / "340.png").convert("L")
    out = HERE.parent / "site" / "images" / HERE.name
    meta = {}
    for k, (box, alt) in enumerate(GLYPH_CUTS, 1):
        c = ImageOps.autocontrast(im.crop(box), cutoff=(1, 1))
        # the ink's own box, then black ink on transparency
        bw = c.point(lambda v: 255 if v < 150 else 0)
        c = c.crop(bw.getbbox())
        a = c.point(lambda v: 255 - v)
        rgba = Image.new("RGBA", c.size, (0, 0, 0, 0))
        rgba.putalpha(a)
        buf = io.BytesIO()
        rgba.save(buf, "PNG")
        w, h = c.size
        # rendered at the height of the type: the page image is ~1.9x print
        rh = max(12, round(h * 0.55))
        rw = max(4, round(w * rh / h))
        data = base64.b64encode(buf.getvalue()).decode()
        (out / f"g{k:04d}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{rw}" height="{rh}" viewBox="0 0 {w} {h}">'
            f'<image width="{w}" height="{h}" xlink:href="data:image/png;base64,{data}"/></svg>\n')
        meta[f"{k:04d}"] = {"w": rw, "h": rh, "alt": alt}
    (HERE / "glyphs.json").write_text(json.dumps(meta, indent=0, ensure_ascii=False) + "\n")


def primes(v):
    """THE ACCENTS ON NOTE NAMES ARE PRIMES, NOT APOSTROPHES. The proof
    types them as ASCII ' (c', a'', e₁'), and `se typogrify` curls every
    one into a quotation mark, so the epub printed a'' as a””. Set as the
    prime ′: on an italic note name, on a page-column letter (78d'), and on
    a roman letter standing alone (Merkel's clear vowels A', E'; b'♭).
    An apostrophe inside a word (d'Alembert, Helmholtz's) is untouched."""
    held = []
    v = mathml.MATH.sub(lambda m: (held.append(m.group(0)), f"\x00{len(held) - 1}\x00")[1], v)
    v = R.assemble.EMPH.sub(lambda m: re.sub(r"(?<=[a-gA-G₀-₉⁰-⁹′])'", "′", m.group(0)), v)
    v = re.sub(r"(?<=\d[a-d])'", "′", v)
    v = re.sub(r"(?<![A-Za-z'’])([a-gA-G][₀-₉]*)('+)(?![A-Za-z])",
               lambda m: m.group(1) + "′" * len(m.group(2)), v)
    return re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], v)


def main():
    ns = leaves()
    page = folios(ns)
    stream, anchors, kept, unplaced = build_stream(ns, page)
    print(len(ns), "leaves;", len(stream), "items;", len(anchors), "locators; hyphens kept:", len(kept))
    print("tokens left waiting at a leaf end:", unplaced[:10])
    (HERE / "_src" / "stream.txt").write_text("\n\n".join(f"{k}\t{v}" for k, v in stream))
    aset = set(anchors)
    assert len(aset) == len(anchors), "a locator twice"
    stats = Counter()
    stream = [(k, link_refs(v, aset, stats) if k in ("P", "BLOCK") else v) for k, v in stream]
    print("references:", {k: v for k, v in stats.items() if k != "_u"})
    for u in stats.get("_u", []):
        print("   unlinked:", repr(u))
    secs = sections_of(stream)

    # the text's last conventions
    for sec in secs:
        new = []
        for k, v in sec["stream"]:
            if k in ("P", "BLOCK"):
                v = re.sub(r"\^\^(.+?)\^\^", r"\1", v)
                v = primes(v)
                # a locator landed in an empty cell: the cell is the locator
                v = re.sub(r'(\{¶[^}]*\})""(?= \| |$)', r"\1", v, flags=re.M)
                assert "^^" not in v, v[:80]
                assert R.emph_safe(v) == v, ("an asterisk the renderer cannot set", v[:200])
            new.append((k, v))
        sec["stream"] = new

    # plates: every cut in the text is in a .plates file, and every
    # .plates line is placed exactly once
    specs = plate_specs(ns)
    placed = [v for sec in secs for k, v in sec["stream"] if k == "PLATE"]
    placed = [f"{p}.jpg" for p in placed]
    assert len(placed) == len(set(placed)), "a plate placed twice"
    assert set(placed) == set(specs), (sorted(set(placed) ^ set(specs)))[:10]
    for sec in secs:
        sec["stream"] = [("PLATE", f"{v}.jpg") if k == "PLATE" else (k, v) for k, v in sec["stream"]]
    replace = cut_plates(specs)
    plates = [{"src": p, "printed": specs[p][3]} for p in placed]
    L = "abcdefghijklmnopqrstuvwxyz"
    cdir = HERE / "captions"
    cdir.mkdir(exist_ok=True)
    (cdir / "plates.txt").write_text(
        "# written by prep.py from proof/*.plates: the proofreaders captioned each cut\n"
        # a caption is new writing, and a "]" inside it would end the
        # [Figure id: caption] marker early (verify.py and both renderers)
        + "".join(f"{L[i // 26] + L[i % 26]}\t{specs[p][4].replace('[', '(').replace(']', ')')}\n"
                  for i, p in enumerate(placed)))
    assert not any(re.search(r"[][]", specs[p][3]) for p in placed), "a printed label with a bracket"
    glyph_tokens(secs)
    # compose pins plate ids against plates.json so a HAND-WRITTEN caption
    # cannot drift onto its neighbour. Here no caption is hand-written: every
    # one is regenerated above from proof/*.plates in placed order, keyed by
    # the same order, so an id that moves takes its caption with it.
    (HERE / "plates.json").unlink(missing_ok=True)
    book = R.Book(HERE, "hel_jp2.zip", html_name="-", replace=replace)
    rows, described = R.compose(book, secs, plates=plates, captions_dir=cdir)
    write_glyphs()
    nmath = sum(len(mathml.formulas(v)) for sec in secs for k, v in sec["stream"] if k in ("P", "BLOCK"))
    notes = sum(1 for sec in secs for k, v in sec["stream"] if k == "P" and v.startswith("Footnote: "))
    print(len(secs), "sections;", len(rows), "plates,", described, "described;", nmath, "formulas;", notes, "notes;",
          f"{R.words([it for s in secs for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
