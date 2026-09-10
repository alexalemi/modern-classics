"""Per-book checks for lucretius/ -- the euclid-rivals pattern.

verify.py measures the word ratio. What it cannot see here:
  1. A LOST CARD. Each file is a run of whole cards (Perseus' paragraphs,
     and Leonard's). A modern file's paragraph count is not pinned, but its
     ratio against each card's Latin is: the file is checked card by card
     against the crib's card boundaries only in aggregate, so the guard is
     the fleming rule -- every PROPER NAME in the Latin must appear in the
     English (Iphianassa may be Iphigenia; the rest carry over), which is
     the cheap witness for a dropped passage in a poem with no digits.
  2. THE ARCHAISM SWEEP (augustine): Leonard is 1916 blank verse full of
     "thee", "thou dost", "'tis"; with him open all day the drift is into
     his English. ARCHAIC_OK stays empty.
  3. Heading/part parity (the quixote trap): 15 files, all parts.
  4. No tab-indented block in the modern file: the edition is PROSE; a
     verse-set passage is a crib pasted in.
  5. Emphasis and all-caps and stage of the renderer, as the other books.
Exit status nonzero on any finding.

    python3 lucretius/check.py [NNN ...]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import assemble                                       # noqa: E402

MIN_RATIO, MAX_RATIO = 1.55, 2.30   # Latin hexameter -> English prose;
                                    # ovid/ landed 1.68 and verified 1.4-2.4
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|art thou|"
    r"unto|ere|whilst|amongst|betwixt|methinks|forsooth|yonder|nay|"
    r"verily|behold|wherefore|whence|whither|hither|perchance|o'er|"
    r"ne'er|'tis|'twas|aught|naught|hark|lo)\b", re.I)
ARCHAIC_OK = []
PART_LINE = re.compile(r"^\(Part (\d+) of (\d+)\)$")
# Latin proper names that must carry into the English, in the form the
# ledger locks; a name absent from a file that has it in the Latin is the
# cheapest evidence of a dropped passage. Latin -> acceptable English forms.
NAMES = {
    "Venus": ["Venus"], "Memmi": ["Memmius"], "Epicur": ["Epicurus"],
    "Iphianass": ["Iphigenia", "Iphianassa"], "Heraclit": ["Heraclitus"],
    "Empedocl": ["Empedocles"], "Anaxagor": ["Anaxagoras"],
    "Democrit": ["Democritus"], "Ennius": ["Ennius"], "Homer": ["Homer"],
    "Aetna": ["Etna"], "Phaethon": ["Phaethon"], "Magnes": ["Magnesia", "magnet"],
    "Athen": ["Athens", "Athenian"], "Aegypt": ["Egypt"],
    # "Nil" fired on the LATIN WORD for nothing, which Lucretius uses
    # constantly and capitalises at the start of a line ("Nil adeo fieri",
    # III.182; "Nil igitur mors est ad nos", III.830). The river is only
    # ever "Nilus" (VI.712) or "Nili" (VI.1114), neither of which is a
    # substring of nil/Nil, so the two inflected keys are exact.
    "Nilus": ["Nile"], "Nili": ["Nile"],
    "Cybel": ["Cybele"], "Sisyph": ["Sisyphus"], "Tantal": ["Tantalus"],
    "Tityos": ["Tityos"], "Cerber": ["Cerberus"], "Scipiad": ["Scipio"],
    "Xerx": ["Xerxes"], "Ancus": ["Ancus"], "Helic": ["Helicon"],
    "Phoeb": ["Apollo", "Phoebus"], "Neptun": ["Neptune"], "Cerer": ["Ceres"],
    "Liber": ["Bacchus", "Liber"], "Iuppiter": ["Jupiter"], "Iov": ["Jupiter", "Jove"],
}


def main(argv):
    chap = os.path.join(HERE, "chapters")
    mod = os.path.join(HERE, "modern_chapters")
    want = argv[1:]
    manifest = {e["file"]: e for e in
                json.load(open(os.path.join(HERE, "manifest.json")))}
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
        lines = text.split("\n")
        body_src = "\n".join(src.split("\n")[1:])
        sw = len(body_src.split())
        mw = len("\n".join(lines[2:]).split())
        r = mw / max(1, sw)
        if not MIN_RATIO <= r <= MAX_RATIO:
            say.append(f"ratio {r:.2f} outside {MIN_RATIO}-{MAX_RATIO}")
        e = manifest[f]
        if lines[0].strip() != e["title"]:
            say.append(f"heading {lines[0]!r}, manifest {e['title']!r}")
        pm = PART_LINE.match(lines[1].strip() if len(lines) > 1 else "")
        if e["of"] > 1 and (not pm or (int(pm.group(1)), int(pm.group(2)))
                            != (e["part"], e["of"])):
            say.append("part marker missing or wrong on line 2")
        for i, ln in enumerate(lines[2:], 3):
            if ln.startswith("\t"):
                say.append(f"tab-indented line {i}: the edition is prose")
                break
        for m in ARCHAIC.finditer(text):
            ctx = text[max(0, m.start() - 40):m.start() + 40]
            if not any(ok in ctx for ok in ARCHAIC_OK):
                say.append(f"archaism {m.group(0)!r}: ...{ctx.strip()[:70]}...")
        for lat, engs in NAMES.items():
            if lat in body_src and not any(x in text for x in engs):
                say.append(f"name {lat!r} in the Latin, none of {engs} in "
                           f"the English")
        stripped = assemble.EMPH.sub("", text)
        if "*" in stripped or "_" in stripped:
            say.append("asterisk or underscore that EMPH will not render")
        # A CHECK MUST MIRROR THE RENDERER, NOT APPROXIMATE IT (the
        # epictetus lesson): assemble.py asks is_subheading about a
        # PARAGRAPH, never a line, and never about an empty one -- passing
        # it "" raises IndexError, which is how this was found.
        for par in [p.strip() for p in "\n".join(lines[2:]).split("\n\n")]:
            if not par:
                continue
            par = " ".join(par.split())
            if len(par) > 3 and par == par.upper() and any(c.isalpha()
                                                           for c in par):
                say.append(f"all-caps paragraph renders as a heading: "
                           f"{par[:50]}")
                break
            if assemble.is_subheading(par):
                say.append(f"paragraph renders as a subheading: {par[:60]}")
        if say:
            bad += 1
            print(f"{f}:")
            for s in say:
                print(f"  {s}")
        else:
            print(f"{f}: ok  (ratio {r:.2f})")
    print(f"\nchecked {seen}/{len(files)} translated files")
    if bad:
        print(f"{bad} file(s) with findings")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
