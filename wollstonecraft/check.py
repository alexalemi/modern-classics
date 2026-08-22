"""Per-book checks for wollstonecraft/ — the euclid-rivals pattern.

verify.py sees word ratios, part markers and must_contain phrases. It
cannot see any of the following, and every one has shipped a defect in
some book of this collection before.

  1 HEADING AND PART PARITY against the manifest. assemble.strip_front
    drops the first non-blank line of EVERY file in a group and takes
    the heading from part 1 alone, so a wrong heading in a later part
    vanishes silently -- the quixote bug, where chapter 33's second half
    was titled "Chapter 34". ELEVEN of these twenty-one files are parts,
    so the trap is at close to maximum. Later parts are compared against
    part 1's MODERN heading, not the manifest title, because that is
    what the renderer uses.

  2 SECTION-HEADING PARITY AND RENDERABILITY. Chapters Five and Thirteen
    carry eleven section headings between them. A heading that loses its
    title case, or gains a terminal period, stops being an <h4> and
    becomes a paragraph shouted in capitals (the ball trap) -- and the
    section it should open silently merges into the one before. The
    check asks assemble.is_subheading ITSELF rather than approximating
    it (the epictetus lesson: every disagreement between a check and the
    renderer costs an edit to correct prose).

  3 VERSE INTEGRITY (the boethius check). Eleven verse quotations,
    Milton and Dryden and Pope, and turning a quotation into a paragraph
    is this book's silent summarisation: the words all survive, the
    ratio does not move, and the reader can no longer see that she is
    answering a poem. Blocks and line counts must match exactly.

  4 EMPHASIS PARITY against the source, per file, AND that every marker
    RENDERS. Counting is not enough: assemble.EMPH refuses a span whose
    opening asterisk follows a word character, so "can*not*" is not
    emphasis at all and ships as literal asterisks with the count still
    balanced. Mirror the renderer, do not approximate it.

  5 A COUNTED NUMERIC DIFF, not a set difference. A SET CANNOT SEE A
    DROPPED DUPLICATE (the hume lesson).

  6 THE FOOTNOTES ARE STILL THERE, all 37, still prefixed, still in the
    file prep put them in.

  7 AN ARCHAISM SWEEP. The whole justification of this book is that it
    does not sound old; a translator reaching for period colour is the
    live failure mode.

Exits NONZERO on any finding. A checker that cannot fail a build will
eventually be ignored (the epictetus lesson).
"""
import json
import pathlib
import re
import sys
from collections import Counter

BOOK = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK.parent))
import assemble                                              # noqa: E402

SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

PART = re.compile(r"^\(Part (\d+) of (\d+)\)$")
ASTERISM = re.compile(r"^\*( \*)+$")
# A separator must be followed by a digit, or a figure swallows the comma
# that ends its clause and "1600," and "1600" become different tokens.
NUM = re.compile(r"\d+(?:[,./]\d+)*")
THOU = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|wert|wilt|didst|knowest|seest|saith|ere|"
    r"whilst|amongst|betwixt|nay|behold|methinks|perchance|oft|"
    r"'tis|thereunto|whereupon|hereunto|whereof|thereof|hitherto)\b", re.I)

# QUOTED VERSE IS EXEMPT AS A CLASS, and this is the one place where a
# structural exemption beats the grimm exact-phrase rule -- with an
# argument, not for convenience.
#
# The sweep exists to catch THE TRANSLATOR reaching for period colour.
# It cannot do that inside a tab-indented block, because those blocks are
# required to be VERBATIM Milton, Dryden, Pope and Shakespeare (see
# text_analysis section 4), so any archaism in them is the poet's by
# construction and removing it would be the defect. Check 3 independently
# asserts that every verse block survives with its exact line count, so
# the exempted region cannot quietly grow, and nothing but verse is ever
# indented in this book.
#
# The first version of this file listed the Eve stanza's lines by exact
# phrase and was immediately incomplete: Adam's eleven-line reply fired
# on hast/thou/thy the moment chapter Two was written. A list that has to
# be extended every time a poet is quoted is not an exemption list, it is
# a leak.
#
# THOU_OK stays for PROSE, and stays empty, and is empty because it was
# checked rather than by accident (the subjection note).
THOU_OK = []


def body_of(path):
    """Text below the heading and the part marker."""
    lines = path.read_text().split("\n")
    i = 1
    while i < len(lines) and (not lines[i].strip()
                              or PART.match(lines[i].strip())):
        i += 1
    return "\n".join(lines[i:])


def verse(text):
    """(blocks, total lines) of tab-indented matter, grouped as the
    renderer groups it: consecutive indented lines are ONE block."""
    blocks, run = [], 0
    for line in text.split("\n"):
        if line.startswith(("\t", "    ")):
            run += 1
        elif run:
            blocks.append(run)
            run = 0
    if run:
        blocks.append(run)
    return len(blocks), sum(blocks)


def section_titles():
    """Every section heading prep wrote, per file."""
    import prep
    return {t for t in prep.SECTION_TITLES.values()}


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    titles = section_titles()
    out = []
    part1_heading = {}

    for m in manifest:
        fn = where = m["file"]
        if not (MOD / fn).exists():
            continue
        text = (MOD / fn).read_text()
        lines = text.split("\n")
        head = lines[0].strip()
        src = (SRC / fn).read_text()

        # 1 -- heading and part marker
        key = (m["title"], m["of"])
        if m["part"] == 1:
            part1_heading[key] = head
        want = part1_heading.get(key)
        if want is None:
            out.append(f"{where}: part {m['part']} seen before part 1")
        elif head != want:
            out.append(f"{where}: heading {head!r} != part 1's {want!r}")
        marker = next((l.strip() for l in lines[1:4] if PART.match(l.strip())),
                      None)
        if m["of"] > 1:
            if marker is None:
                out.append(f"{where}: MISSING '(Part {m['part']} of "
                           f"{m['of']})' -- verify.py cannot see this")
            elif marker != f"(Part {m['part']} of {m['of']})":
                out.append(f"{where}: {marker} should be "
                           f"(Part {m['part']} of {m['of']})")
        elif marker is not None:
            out.append(f"{where}: part marker {marker} in a single-part file")

        body = body_of(MOD / fn)

        # 2 -- section headings: present, in order, and renderable
        srcsecs = [l.strip() for l in src.split("\n") if l.strip() in titles]
        modsecs = [l.strip() for l in body.split("\n") if l.strip() in titles]
        if srcsecs != modsecs:
            out.append(f"{where}: section headings {modsecs} != {srcsecs}")
        for t in modsecs:
            if not assemble.is_subheading(t):
                out.append(f"{where}: {t!r} will NOT render as a heading")

        # 3 -- verse
        vb, vl = verse(src)
        mb, ml = verse(body)
        if (vb, vl) != (mb, ml):
            out.append(f"{where}: verse {vb} block(s)/{vl} line(s) in source, "
                       f"{mb}/{ml} kept")

        # 4 -- emphasis and asterisms
        aster = sum(1 for l in body.split("\n") if ASTERISM.match(l.strip()))
        saster = sum(1 for l in src.split("\n") if ASTERISM.match(l.strip()))
        if aster != saster:
            out.append(f"{where}: {saster} asterism(s) in source, {aster} kept")
        strip_ast = lambda s: "\n".join(
            "" if ASTERISM.match(l.strip()) else l for l in s.split("\n"))
        ws, wm = strip_ast(src).count("*"), strip_ast(body).count("*")
        if ws != wm:
            out.append(f"{where}: {ws // 2} emphasis span(s) in source, "
                       f"{wm // 2} in translation")
        left = assemble.EMPH.sub("", strip_ast(body))
        for i, line in enumerate(left.split("\n"), 1):
            if "*" in line:
                out.append(f"{where}:{i}: asterisk does NOT render as <em> -- "
                           f"{line.strip()[:70]!r}")

        # 5 -- numbers, COUNTED
        lost = Counter(NUM.findall(strip_ast(src))) - Counter(NUM.findall(body))
        if lost:
            out.append(f"{where}: numbers lost: "
                       + ", ".join(sorted(lost.elements())))

        # 6 -- footnotes
        ns, nm = src.count("Footnote: "), body.count("Footnote: ")
        if ns != nm:
            out.append(f"{where}: {ns} footnote(s) in source, {nm} kept")

        # 7 -- archaism, over PROSE only (see THOU_OK above)
        clean = "\n".join(l for l in body.split("\n")
                          if not l.startswith(("\t", "    ")))
        for ok in THOU_OK:
            clean = clean.replace(ok, "")
        hits = Counter(w.lower() for w in THOU.findall(clean))
        if hits:
            out.append(f"{where}: archaic forms survive: "
                       + ", ".join(f"{w}x{n}" if n > 1 else w
                                   for w, n in sorted(hits.items())))

    done = sum(1 for m in manifest if (MOD / m["file"]).exists())
    print(f"checked {done}/{len(manifest)} translated files")
    for line in out:
        print("  " + line)
    if out:
        print(f"\n{len(out)} finding(s)")
        raise SystemExit(1)
    print("clean")


if __name__ == "__main__":
    main()
