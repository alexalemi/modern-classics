"""Per-book checks for sun-tzu/ — the euclid-rivals pattern.

verify.py sees word ratios, part markers and must_contain phrases. It
cannot see any of the following.

  1 VOICE PARITY, and it is the decisive check for this book. Every
    paragraph is Sun Tzu, a commentator, or Giles, and the reader can
    only tell by the label. A "Commentary:" that goes missing hands a
    commentator's gloss to Sun Tzu; one that is invented does the
    reverse. Both read perfectly. Counts are compared per file, and so
    is the SEQUENCE, because a label that migrates one paragraph is the
    same defect as one that vanishes.

  2 VERSE NUMBERS, in order, per file. They are the canonical citation
    system — the commentators cross-refer by them constantly — so a
    dropped or renumbered verse silently breaks every reference to it.
    Compared as a list, not a set.

  3 HEADING AND PART PARITY against the manifest (the quixote trap:
    chapter Eleven is split, and a wrong heading in part 2 vanishes
    silently because assemble takes the heading from part 1).

  4 EMPHASIS PARITY via assemble.EMPH itself, not an approximation of
    it (the boethius lesson). Giles italicises transliterated Chinese,
    which is exactly the material a translator drops.

  5 A COUNTED numeric diff (the hume lesson: a set cannot see a dropped
    duplicate). MEASURED BEFORE BEING TRUSTED, unlike nights/: the
    source carries 300+ numeral tokens — verse numbers, dates, troop
    counts, chapter cross-references — so this one has real work to do.

  6 AN ARCHAISM SWEEP. Giles is Edwardian, not archaic, so anything the
    sweep finds is the translator reaching for period colour.

Exits NONZERO on any finding.
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
VERSE = re.compile(r"^(\d+(?:\s*,\s*\d+)*)\.")
LABEL = re.compile(r"^(Commentary|Footnote): ")
NUM = re.compile(r"\d+(?:[,./]\d+)*")
THOU = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|shouldst|wouldst|"
    r"couldst|canst|mayest|wert|wilt|didst|knowest|seest|saith|ere|"
    r"whilst|amongst|betwixt|nay|behold|methinks|perchance|oft|'tis|"
    r"thereunto|whereupon|hereunto|whereof|thereof)\b", re.I)

# BY EXACT PHRASE, NEVER BY LOOSENING THE SWEEP (the grimm rule).
ARCHAIC_OK = []

# TWO SIGNED ALLOWANCE TABLES (the burke rule): a reason beside every
# entry, or the entry is just a loosened check. Both are keyed by file,
# so an allowance cannot leak into a chapter it was not argued for.
#
# GILES'S PAGE REFERENCES TO HIS OWN EDITION are meaningless in a
# reflowable one, and two of them fall here. "(See p. 57.)" resolves to
# Tu Mu's account of Chao She's march, which IS in this book, so it is
# rewritten as "Chapter Seven, verse 4, note" and the reader can follow
# it. "already alluded to on p. 28" points into Giles's own
# introduction, which this edition does not carry (see prep.py), so the
# locator has nothing to point at and is dropped -- the battle it refers
# to is then described in full in the very same sentence.
# "[See p. 90.]" is the third, and it resolves: T'ien Tan's stratagem
# with the oxen is Chapter Nine, verse 24, note, which is where the
# rewritten reference now sends the reader.
# Chapter thirteen carries three more of them, all resolvable: p. 90
# and p. 57 as above, and "(See p. 132.)" -- Pan Ch'ao's deception of
# his own officers before Yarkand, Chapter Eleven, verse 36, note.
NUM_DROPPED = {"011.txt": ["57", "28"], "012.txt": ["90"],
               "013.txt": ["90", "57", "132"]}

# *débandade* is not the locked foreign vocabulary the emphasis check
# exists to protect. Giles italicises transliterated Chinese and real
# technical terms -- *cheng*, *ch'i*, *li* -- and those stay. This is a
# French word he reached for where English has one, in the middle of a
# Chinese general's reported speech, and modern English never took it
# up: a dated WORD, not a dated claim. Rendered "stampede".
EMPH_DELTA = {"011.txt": ["débandade"]}

# GILES'S ITALICISED EDITORIAL LATIN, and why it is exempt AS A RULE
# rather than by a per-file allowance.
#
# He italicises two quite different things. Transliterated Chinese and
# real foreign words -- *cheng*, *ch'i*, *li*, *picul*, *testudo*, *ruse*
# -- stay foreign in this edition and KEEP their italics; those are the
# spans a translator drops, and they are exactly what this check is for.
# But his editorial POINTERS are Latin only because that was the scholarly
# habit of 1910: "*I.e.*" is "that is", "*supra*" is "above". Englished,
# they are ordinary words and correctly lose the italics with the Latin.
#
# Exempting them by rule beats a per-file table because it cannot grow
# into a place to hide a real drop: a missing *li* or *cheng* still fails.
LATIN_TAGS = {"I.e.", "i.e.", "e.g.", "supra", "infra", "q.d.", "et seq.",
              "circa", "sic"}


def body_of(path):
    lines = path.read_text().split("\n")
    i = 1
    while i < len(lines) and (not lines[i].strip()
                              or PART.match(lines[i].strip())):
        i += 1
    return "\n".join(lines[i:])


def paras(text):
    return [re.sub(r"\s+", " ", p).strip()
            for p in re.split(r"\n\s*\n", text) if p.strip()]


def voices(ps):
    """The label sequence: 'V' for a verse, 'C'/'F' for the two labels."""
    out = []
    for p in ps:
        m = LABEL.match(p)
        out.append(m.group(1)[0] if m else "V")
    return "".join(out)


def verse_numbers(ps):
    out = []
    for p in ps:
        if LABEL.match(p):
            continue
        m = VERSE.match(p)
        if m:
            out.append(re.sub(r"\s+", "", m.group(1)))
    return out


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
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

        # 3 -- heading and part marker
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
        sp, dp = paras("\n\n".join(src.split("\n", 1)[1:])), paras(body)

        # 1 -- voice parity: counts AND sequence
        vs, vd = voices(sp), voices(dp)
        if vs != vd:
            cs, cd = Counter(vs), Counter(vd)
            if cs != cd:
                out.append(
                    f"{where}: voice counts differ -- source "
                    f"{dict(sorted(cs.items()))}, translation "
                    f"{dict(sorted(cd.items()))} "
                    f"(V=verse, C=Commentary, F=Footnote)")
            else:
                i = next(k for k in range(min(len(vs), len(vd)))
                         if vs[k] != vd[k])
                out.append(f"{where}: voice sequence diverges at paragraph "
                           f"{i + 1}: source {vs[i]}, translation {vd[i]} "
                           f"-- {dp[i][:60]!r}")

        # 1b -- A VERSE MUST NOT END ON A CLOSING BRACKET. That is the
        # signature of a commentary block whose OPENING bracket the
        # source lost: the gloss then reads as Sun Tzu's own words and
        # nothing else can see it. Two were found this way.
        for i, ptext in enumerate(dp, 1):
            if not LABEL.match(ptext) and ptext.rstrip().endswith("]"):
                out.append(f"{where}: paragraph {i} is unlabelled but ends "
                           f"on ']' -- a note that lost its opening "
                           f"bracket? {ptext[:60]!r}")

        # 2 -- verse numbers, in order
        ns, nd = verse_numbers(sp), verse_numbers(dp)
        if ns != nd:
            out.append(f"{where}: verse numbers differ -- "
                       f"missing {[x for x in ns if x not in nd]}, "
                       f"unexpected {[x for x in nd if x not in ns]}")

        # 4 -- emphasis, counted and rendered
        # The curly apostrophe is typography, not content: the source
        # writes "ch\u2019i" and this edition writes "ch'i" throughout.
        # Giles's breve is the same class (the source writes "Sun Tz\u016d"
        # and this edition drops the diacritic throughout), and so is
        # punctuation the printer swept inside a span ("*qui vive;*").
        # A RULE, not a per-file allowance: neither can hide a reworded
        # span, because only the trailing marks are trimmed.
        apos = lambda x: (x.replace("\u2019", "'")
                           .replace("\u016d", "u").rstrip(" .,;:"))
        ss = [apos(x) for x in re.findall(r"\*([^*]+)\*", src)
              if x not in LATIN_TAGS]
        ds = [apos(x) for x in re.findall(r"\*([^*]+)\*", body)]
        ds += [apos(x) for x in EMPH_DELTA.get(fn, [])]
        if Counter(ss) != Counter(ds):
            gone = Counter(ss) - Counter(ds)
            new = Counter(ds) - Counter(ss)
            out.append(f"{where}: emphasis differs -- dropped "
                       f"{sorted(gone.elements())}, added "
                       f"{sorted(new.elements())}")
        for i, line in enumerate(assemble.EMPH.sub("", body).split("\n"), 1):
            if "*" in line:
                out.append(f"{where}:{i}: asterisk does NOT render as <em> -- "
                           f"{line.strip()[:70]!r}")

        # 5 -- numbers, COUNTED
        # A THOUSANDS SEPARATOR IS NOT A DIFFERENT NUMBER. Giles writes
        # "12500" and this edition writes "12,500"; comparing the tokens
        # raw reports the figure as lost when it is right there. Strip
        # the separators from both sides -- the check exists to catch a
        # value that VANISHED, not one that gained a comma.
        bare = lambda t: [x.replace(",", "") for x in NUM.findall(t)]
        lost = (Counter(bare(src)) - Counter(bare(body))
                - Counter(NUM_DROPPED.get(fn, [])))
        if lost:
            out.append(f"{where}: numerals lost: "
                       + ", ".join(sorted(lost.elements())))

        # 6 -- archaism
        clean = body
        for ok in ARCHAIC_OK:
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
