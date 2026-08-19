"""Per-book checks for burke/ — the euclid-rivals pattern.

verify.py sees word ratios, part markers and must_contain phrases. It
cannot see any of the following, and every one of them has shipped a
defect in some book of this collection before:

  1 HEADING AND PART PARITY against the manifest. assemble.strip_front
    drops the first non-blank line of EVERY file in a group and takes
    the heading from part 1 alone, so a wrong heading in a later part
    vanishes silently -- the quixote bug, where chapter 33's second
    half was titled "Chapter 34". Nine of these twelve files are parts.
    Later parts are compared against part 1's MODERN heading, not
    against the manifest title, because that is what the renderer uses.

  2 EMPHASIS PARITY against the source, per file, AND that every marker
    RENDERS. Mill italicises the word carrying the logical stress, and
    52 spans do real work. Counting them is not enough: assemble.EMPH
    refuses a span whose opening asterisk follows a word character (the
    guard that protects "app_1" and "S_n"), so "can*not*" is not
    emphasis at all and ships as literal asterisks with the count still
    balanced. MIRROR THE RENDERER, DO NOT APPROXIMATE IT -- ask
    assemble.EMPH itself and require that no asterisk survives it,
    except the "* * *" asterisms, which are counted separately.

  3 A COUNTED NUMERIC DIFF, not a set difference. The fleming check is
    a set, and A SET CANNOT SEE A DROPPED DUPLICATE: hume dates two
    parallel suppositions to the same 1st of January 1600, and spelling
    one of them out passes a set difference untouched because the other
    survives. Counter subtraction catches it. Mill's footnotes are
    dense with dates and case citations, which is exactly the material
    this protects.

  4 THE FOOTNOTES ARE STILL THERE, all nine, still prefixed, and still
    in the file prep put them in. A footnote that quietly merges into
    the body reads perfectly and loses Mill's own voice-within-a-voice.

  5 AN ARCHAISM SWEEP. Light, because Mill has almost none to begin
    with -- but a translator reaching for period colour is a real
    failure mode, and this book's whole justification is that it does
    not sound old.

Exits NONZERO on any finding. A checker that cannot fail a build will
eventually be ignored (the epictetus lesson, where it printed findings
and returned success for 48 files).
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
# A separator must be followed by a digit, or a figure swallows the
# comma that ends its clause and "1600," and "1600" become different
# tokens -- every number ending a clause then fires a false positive.
NUM = re.compile(r"\d+(?:[,./]\d+)*")
THOU = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|wert|wilt|didst|knowest|seest|saith|ere|"
    r"whilst|amongst|betwixt|nay|behold|methinks|perchance|oft|"
    r"'tis|thereunto|whereupon|hereunto)\b", re.I)

# Words the archaism sweep would otherwise flag, exempted by EXACT
# PHRASE and never by loosening the sweep (the grimm rule). This list
# began empty and grew one entry at a time, each with its reason; the
# reason is the point, because an exemption without one is just a hole.
THOU_OK = [
    # Exemptions are by EXACT PHRASE, never by loosening the sweep (the
    # grimm rule). All but the last are VERBATIM QUOTATIONS -- a statute,
    # a scripture, a sermon, a poem -- which Burke quotes because the
    # exact words are the point, and which are not ours to modernise.
    "doth, under God, wholly depend",        # the Declaration of Right
    "hath _abdicated_ the government",       # the same statute
    "whilst 't is changed by",               # Waller, on Cromwell
    "he that hath little business",          # Ecclesiasticus 38
    "whilst we are _mocked_",                # Dr Price's sermon
    "now lettest thou thy servant depart in peace, for mine eyes have "
    "seen thy salvation",                    # the Nunc dimittis, quoted
                                             # by Price and by Peters
    # Section Nine's footnote quotes a Dissenting minister's letter
    # VERBATIM, in order to dispute the terms it uses -- which is why
    # Burke italicises them. Modernising a word inside the quotation
    # would put our English into another man's mouth in the one place
    # where the exact wording is the thing under argument.
    "enlightened and liberal amongst the English",
    # Denham's "Cooper's Hill", quoted at length in a Section Ten
    # footnote. A poem is not ours to re-metre: "Betwixt their frigid
    # and our torrid zone" scans on the word, and "between" does not.
    "Betwixt their frigid and our torrid zone",
    # The one judgement call. "Never, never more shall we behold..."
    # stands inside the chivalry passage, which must_contain pins
    # UNCHANGED because it is the reason the book is still read. "See"
    # for "behold" is a real modernisation and it wrecks the cadence of
    # the most famous sentence Burke wrote. The check fired on correct
    # prose, so the check is what changes (the boethius rule).
    "never more shall we behold",
]

# Numerals in the source that are NOT numbers, per file, with the
# reason. Same discipline as EMPH_DELTA: subtracted from the source
# side so the counted diff stays exact everywhere else.
NUM_DROPPED = {
    # "Cic. Off. 1. 2." is "Cic. Off. l. 2" -- LIBER 2 -- with the ell
    # scanned as a one. The citation renders as "Cicero, On Duties, book
    # 2", so the digit is correctly absent from the translation. This is
    # the numeric-diff analogue of the ocr_sweep.py findings: a scan
    # artefact that looks exactly like content.
    "014.txt": ["1"],
}

# Deliberate, per-file departures from exact emphasis parity, with the
# reason. The value is added to the SOURCE count before comparing, so a
# POSITIVE number means spans the source has and the translation drops,
# and a NEGATIVE number means spans the translation adds. Everywhere
# else the check stays exact -- an allowance without a reason written
# beside it is just a loosened check.
EMPH_DELTA = {
    # Burke's printer sets the pound sign as an italic "l." after the
    # figure: "2,200,000 _l._ sterling". The italics are a typographic
    # convention for an abbreviation, not emphasis on a word, and the
    # modern text writes the figure with the £ sign instead. A dated WORD, not
    # a dated claim -- silently modernised, like Mahomedan -> Muslim in
    # mill/. Four of them in this file.
    "011.txt": 4,
    # Burke's printer sets two words of the arithmetic in Section Eleven
    # in small capitals for contrast -- "pay one sixth LESS", "will have
    # three voices MORE" -- which the transcription can only render as
    # shouting capitals. They are emphasis, and every word they are
    # contrasted against in those two sentences is already italic, so
    # they are set as emphasis too. Modernising the TYPOGRAPHY, which is
    # what the pipeline exists to do; the words are untouched.
    "016.txt": -2,
}


def body_of(path):
    """Text below the heading and the part marker."""
    lines = path.read_text().split("\n")
    i = 1
    while i < len(lines) and (not lines[i].strip()
                              or PART.match(lines[i].strip())):
        i += 1
    return "\n".join(lines[i:])


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    out = []
    part1_heading = {}

    for m in manifest:
        fn, where = m["file"], m["file"]
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

        # 2 -- emphasis and asterisms
        aster = sum(1 for l in body.split("\n") if ASTERISM.match(l.strip()))
        saster = sum(1 for l in src.split("\n") if ASTERISM.match(l.strip()))
        if aster != saster:
            out.append(f"{where}: {saster} asterism(s) in source, {aster} kept")
        strip_ast = lambda s: "\n".join(
            "" if ASTERISM.match(l.strip()) else l for l in s.split("\n"))
        # BURKE'S ITALICS ARE UNDERSCORES, not asterisks: Gutenberg sets
        # them as _x_, which assemble.EMPH renders exactly as it renders
        # *x*. Counting asterisks alone -- which is what the mill/ and
        # subjection/ versions of this check do, correctly, for a
        # Standard Ebooks source -- would leave the parity guard blind on
        # the book that needs it most: 442 spans, and Burke's sarcasm
        # lives in the italic. Count the SPANS assemble.EMPH actually
        # matches, on both sides, and then require that no delimiter of
        # either kind survives it (the epictetus rule: mirror the
        # renderer, do not approximate it).
        ws = len(assemble.EMPH.findall(strip_ast(src)))
        ws -= EMPH_DELTA.get(m["file"], 0)
        wm = len(assemble.EMPH.findall(strip_ast(body)))
        if ws != wm:
            out.append(f"{where}: {ws} emphasis span(s) in source, "
                       f"{wm} in translation")
        left = assemble.EMPH.sub("", strip_ast(body))
        for i, line in enumerate(left.split("\n"), 1):
            stray = line.count("*") + line.count("_")
            if stray:
                out.append(f"{where}:{i}: {stray} emphasis delimiter(s) do "
                           f"NOT render -- {line.strip()[:66]!r}")

        # 3 -- numbers, COUNTED
        lost = (Counter(NUM.findall(strip_ast(src)))
                - Counter(NUM_DROPPED.get(m["file"], []))
                - Counter(NUM.findall(body)))
        if lost:
            out.append(f"{where}: numbers lost: "
                       + ", ".join(sorted(lost.elements())))

        # 4 -- footnotes
        ns = src.count("Footnote: ")
        nm = body.count("Footnote: ")
        if ns != nm:
            out.append(f"{where}: {ns} footnote(s) in source, {nm} kept")

        # 5 -- archaism
        clean = body
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
