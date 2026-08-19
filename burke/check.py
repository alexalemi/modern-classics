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

# EMPTY, AND DELIBERATELY SO. mill/ exempts "thou shalt" by exact
# phrase because Chapter Two of On Liberty turns on the grammatical form
# of the commandments. Nothing in this book quotes scripture that way,
# so there is nothing to exempt -- and an exemption list that is empty
# because it was checked is worth more than one that is empty by
# accident. If this ever needs an entry, add the EXACT PHRASE and never
# loosen the sweep (the grimm rule).
# EMPTY, and empty because it was checked. Burke quotes scripture and
# the Book of Common Prayer here and there, but never in a form that
# needs a thou-family word preserved. If this ever needs an entry, add
# the EXACT PHRASE and never loosen the sweep (the grimm rule).
THOU_OK = []


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
        ws, wm = strip_ast(src).count("*"), strip_ast(body).count("*")
        if ws != wm:
            out.append(f"{where}: {ws // 2} emphasis span(s) in source, "
                       f"{wm // 2} in translation")
        left = assemble.EMPH.sub("", strip_ast(body))
        for i, line in enumerate(left.split("\n"), 1):
            if "*" in line:
                out.append(f"{where}:{i}: asterisk does NOT render as <em> -- "
                           f"{line.strip()[:70]!r}")

        # 3 -- numbers, COUNTED
        lost = Counter(NUM.findall(strip_ast(src))) - Counter(NUM.findall(body))
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
