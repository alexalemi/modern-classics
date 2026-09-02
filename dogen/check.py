"""Per-book checks for dogen/ -- the euclid-rivals pattern.

THE USUAL RATIO CHECK DOES NOT WORK HERE AND MUST NOT BE PRETENDED
INTO WORKING. verify.py measures len(text.split()); kanbun has no
spaces, so a whole chapter counts as a handful of "words" and the
ratio -- this collection's one mechanical guard against silent
summarising -- would be inert while looking like coverage. That is
strictly worse than no check (the nights lesson, learned there only
after shipping an inert numeral check). So the ratio here is
CHARACTERS of source against WORDS of translation.

MEASURED AND DELIBERATELY NOT INCLUDED, for the same reason: the
fleming numeric diff. The source contains essentially no digits --
Dogen writes 六十二見, 三千, 二十八代 in characters -- so a digit-token
check would be entirely inert. Where a source spells its numbers out,
the thing to build is a check on the spelled forms, and here that is
what NUMBERS below does.

    python3 dogen/check.py [NNN ...]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import assemble                                        # noqa: E402

# Derived from the finished files and pinned (the purgatorio rule).
# I predicted 2.0-3.0 before measuring and was wrong; a band written
# from that guess could not have been satisfied by a correct file.
MIN_RATIO, MAX_RATIO = 1.20, 1.65

# A SIGNED ALLOWANCE, WITH THE ARGUMENT WRITTEN OUT (the burke rule).
# Not a loosened band: the band still governs the other files, and an
# allowance without a reason is just a check switched off.
#
# 002 -- the Tenzo Kyokun runs at 1.00 words per character where the
# other two run at 1.49 and 1.39, and this was DIAGNOSED rather than
# waved through. Two passages that are translated in full were measured
# separately: the opening comes out at 1.36, inside the band, and the
# three-minds passage at 0.92, far below it. So the text is not
# uniformly denser -- its procedural and list-heavy stretches are. It
# is full of four-character phrases and enumerations (地獄餓鬼畜生修羅
# is eight characters for seven English words) which no faithful
# English can pad out, next to discursive passages that behave like the
# rest of the book.
# The check DID catch a real omission first, and it was fixed rather
# than allowed: the count of the assembly and the rice-grain riddle on
# Luling rice and Guishan's water buffalo had been dropped because I
# could not read the column at page resolution. Refetched at high zoom
# through the IIIF region API, transcribed and translated; that alone
# moved the file from 0.95 to 1.00. Only after the omission was closed
# was the remaining gap accepted as genre.
RATIO_EXPECT = {"002.txt": (0.95, 1.15)}

CJK = re.compile(r"[㐀-鿿]")

# The augustine thou-sweep. ARCHAIC_OK stays EMPTY. There is no
# Victorian translator to catch here -- the drift this guards against
# is MINE, towards the mock-scriptural register that English Zen
# writing falls into, which is exactly the costume this edition exists
# without.
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|unto|ere|"
    r"whilst|amongst|betwixt|methinks|forsooth|verily|behold|"
    r"wherefore|whence|whither|hither|perchance|mayhap|naught|aught|"
    r"o'er|ne'er|'tis|'twas|abide ye|hearken)\b", re.I)
ARCHAIC_OK = []

# LOCKED VOCABULARY, IN TWO CLASSES, AND THE SPLIT IS THE WHOLE POINT.
#
# A PRESENCE TEST CANNOT SEE A DROPPED DUPLICATE, because a surviving
# occurrence covers for the lost one -- the hume lesson, which this
# file first got wrong: a locked term was reworded in one place out of
# seven and the check passed. These seven are FIXED COMPOUNDS that the
# translation renders one-to-one, verified against the finished files,
# so they are COUNTED and the counts must match exactly.
COUNTED = [
    ("非思量", "beyond thinking"),
    ("本來面目", "original face"),
    ("公案現成", "koan is realised in the present"),
    ("身心自然脱落", "drop away of themselves"),
    ("名利", "name and gain"),
    ("名聞利養", "reputation and profit"),
    ("正師", "true teacher"),
]

# These are rendered variously ON PURPOSE and an exact count would fire
# on correct prose: 菩提心 picks up one extra from a section heading,
# and 坐禪/參禪 become "sit", "sitting", "take up Zen" and "practise"
# as the sentence needs. Presence only, which is weak, and is recorded
# here as weak rather than dressed up.
PRESENT = [
    ("菩提心", "thought of awakening"),
    ("正法眼藏", "treasury of the true dharma eye"),
]

# The near-misses, registered so that drift is caught rather than
# hoped against (the nights rule: lock the formula AND encode the wrong
# answers). Each is checked to be absent from the finished text before
# being listed, so none of them fires on correct prose.
BANNED = {
    "fame and fortune": "drift from the locked 名利 = 'name and gain'",
    "fame and gain": "drift from the locked 名利",
    "name and profit": "drift from the locked 名利",
    "not thinking": "非思量 is 'beyond thinking'; 'not thinking' asserts "
                    "the opposite of what the passage argues",
    "dropping off body and mind": "身心自然脱落 keeps 自然 -- 'of themselves'",
    "genuine teacher": "drift from the locked 正師 = 'true teacher'",
}

# Numbers Dogen writes as characters, since the source has essentially
# no digits. COUNTED, not set-differenced: a set cannot see a dropped
# duplicate (the hume rule).
NUMBERS = {
    "六十二見": "sixty-two",
    "三千": "three thousand",
    "二十八代": "twenty-eight",
    "六年": "six years",
    "九歳": "nine years",
    "九牛之一毛": "nine oxen",
    "十三歲": "thirteen",
}

SECTION = re.compile(r"^(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten):"
                     r" .+[^.;:,—]$")
SRC_SECTION = re.compile(r"^第[一二三四五六七八九十]+[　\s]")


def main(argv):
    chap = os.path.join(HERE, "chapters")
    mod = os.path.join(HERE, "modern_chapters")
    manifest = {e["file"]: e for e in
                json.load(open(os.path.join(HERE, "manifest.json")))}
    want = argv[1:]
    files = sorted(f for f in os.listdir(chap) if f.endswith(".txt"))
    bad = seen = 0

    for f in files:
        mp = os.path.join(mod, f)
        if not os.path.exists(mp) or (want and f[:3] not in want):
            continue
        seen += 1
        say = []
        src = open(os.path.join(chap, f), encoding="utf-8").read()
        text = open(mp, encoding="utf-8").read()
        # A PHRASE TEST MUST SEE WHAT THE RENDERER SEES. assemble.py
        # joins a paragraph's wrapped lines back into one line, so a
        # phrase straddling a line break is present on the page but
        # absent from the file. This fired on "nine\nyears" in the
        # Fukanzazengi -- correct prose, wrong check (the epictetus
        # rule). Structural tests below still use `text` and `lines`.
        flat = re.sub(r"\s+", " ", text)
        nchar = len(CJK.findall(src))
        nword = len(text.split())

        # 1. character-to-word ratio
        r = nword / max(1, nchar)
        lo, hi = RATIO_EXPECT.get(f, (MIN_RATIO, MAX_RATIO))
        if not lo <= r <= hi:
            say.append(f"ratio {r:.2f} words/char outside {lo}-{hi}")

        # 2. section parity, anchored on the source's own headings
        s = [l for l in src.split("\n") if SRC_SECTION.match(l)]
        h = [l for l in text.split("\n") if SECTION.match(l.strip())]
        if len(s) != len(h):
            say.append(f"{len(h)} section headings, source has {len(s)}")
        for i, line in enumerate(h):
            if not assemble.is_subheading(line.strip()):
                say.append(f"heading will not render as a heading: "
                           f"{line.strip()[:56]}")

        # 3. heading and part marker (the quixote trap)
        lines = text.split("\n")
        entry = manifest[f]
        if lines[0].strip() != entry["title"]:
            say.append(f"heading {lines[0].strip()!r}, manifest says "
                       f"{entry['title']!r}")

        # 4. locked vocabulary, counted where it can be
        low = flat.lower()
        for cn, en in COUNTED:
            s_n = src.count(cn)
            g_n = low.count(en.lower())
            if s_n and s_n != g_n:
                say.append(f"locked {cn} appears {s_n}x in the source but "
                           f"{en!r} {g_n}x in the translation")
        for cn, en in PRESENT:
            if cn in src and en.lower() not in low:
                say.append(f"locked term {cn} is in the source but "
                           f"{en!r} is not in the translation")
        for bad_en, why in BANNED.items():
            if bad_en in low:
                say.append(f"banned rendering {bad_en!r}: {why}")

        # 5. spelled-out numbers, counted
        for cn, en in NUMBERS.items():
            # A SPELLED-OUT NUMBER CAN SIT INSIDE A LONGER ONE. 六年 is
            # "six years" in the Fukanzazengi (the Buddha's six years of
            # sitting) but in the Tenzo Kyokun every occurrence is the
            # tail of 嘉定十六年, the sixteenth year of Jiading -- a date,
            # not a duration. Counting the bare form reported a dropped
            # number in a translation that was right. Same family as the
            # "nine years" line-break bug: the check was wrong, not the
            # prose. Occurrences preceded by another numeral do not count.
            want_n = len(re.findall(
                r"(?<![一二三四五六七八九十百千])" + re.escape(cn), src))
            got_n = len(re.findall(re.escape(en), flat, re.I))
            if want_n and got_n < want_n:
                say.append(f"number {cn} appears {want_n}x in source, "
                           f"{en!r} {got_n}x in translation")

        # 6. archaism sweep, exemptions empty on purpose
        for m in ARCHAIC.finditer(flat):
            ctx = flat[max(0, m.start() - 40):m.start() + 40]
            if any(ok in ctx for ok in ARCHAIC_OK):
                continue
            say.append(f"archaism {m.group(0)!r}: ...{ctx.strip()[:66]}...")

        # 7. emphasis: ask assemble.EMPH itself whether it renders
        if "*" in assemble.EMPH.sub("", text):
            say.append("asterisk that assemble.EMPH will not render")

        # 8. no all-caps line (assemble reads one as a heading)
        for line in lines:
            s2 = line.strip()
            if len(s2) > 3 and s2 == s2.upper() and any(c.isalpha()
                                                        for c in s2):
                say.append(f"all-caps line renders as a heading: {s2[:44]}")
                break

        if say:
            bad += 1
            print(f"{f}:")
            for x in say:
                print(f"  {x}")
        else:
            print(f"{f}: ok  ({nchar:,} chars -> {nword:,} words, "
                  f"ratio {r:.2f}, {len(h)} sections)")

    print(f"\nchecked {seen}/{len(files)} translated files")
    if bad:
        print(f"{bad} file(s) with findings")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
