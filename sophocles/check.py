"""Per-book checks for sophocles/ -- the euclid-rivals pattern.

verify.py compares chapters/ with modern_chapters/ and measures a word
ratio. It structurally cannot see any of what follows, and in a play the
worst defects are all of that kind: content present, in order, and wrong.

THE DECISIVE CHECK IS SPEAKER PARITY. A lost or invented speaker tag
loses no word -- it WELDS TWO SPEECHES INTO ONE and hands one
character's argument to another. The prose reads perfectly, the ratio
does not move, and in plays built almost entirely out of two people
arguing, that is the difference between a claim and its refutation. The
sequence is compared against the GREEK, mapped through SPEAKERS below.

SECOND: SUNG/SPOKEN PARITY. The edition's whole formal claim is that the
odes are songs and the scenes are speech (Alex's ruling; see
text_analysis.txt). The source marks it, so it can be asserted rather
than trusted. A dissolved ode is this book's silent summarisation.

Exit status is nonzero on any finding -- the epictetus lesson: a checker
that cannot fail a build will eventually be ignored.

    python3 sophocles/check.py [NNN ...]
"""
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import assemble                                       # noqa: E402
import prep                                           # noqa: E402

MIN_RATIO, MAX_RATIO = 1.40, 1.85

# Greek -> the English form this edition uses, locked. The English source
# files are NOT a usable witness for this: they spell Jocasta two ways
# ("Icasta"/"Iocasta"), give Ismene a trailing period in one play, and
# use three different forms for the half-chorus.
SPEAKERS = {
    "Χορός": "Chorus", "Οἰδίπους": "Oedipus", "Κρέων": "Creon",
    "Ἠλέκτρα": "Electra", "Νεοπτόλεμος": "Neoptolemus",
    "Φιλοκτήτης": "Philoctetes", "Ἀντιγόνη": "Antigone",
    "Ὀδυσσεύς": "Odysseus", "Ἄγγελος": "Messenger", "Ὀρέστης": "Orestes",
    "Ἰσμήνη": "Ismene", "Δηιάνειρα": "Deianeira", "Θησεύς": "Theseus",
    "Ὕλλος": "Hyllus", "Χρυσόθεμις": "Chrysothemis",
    "Τέκμησσα": "Tecmessa", "Ἰοκάστη": "Jocasta", "Ἡρακλῆς": "Heracles",
    "Αἴας": "Ajax", "Τειρεσίας": "Teiresias", "Τεῦκρος": "Teucer",
    "Λίχας": "Lichas", "Ἀθήνα": "Athena", "Θεράπων": "Servant",
    "Κλυταιμνήστρα": "Clytemnestra", "Παιδαγωγός": "Tutor",
    "Ἀγαμέμνων": "Agamemnon", "Αἵμων": "Haemon", "Αἴγισθος": "Aegisthus",
    "Μενέλαος": "Menelaus", "Φύλαξ": "Guard", "Ἔμπορος": "Merchant",
    "Ξένος": "Stranger", "Πολυνείκης": "Polyneices", "Τροφός": "Nurse",
    "Ἐξάγγελος": "Messenger", "Ἱερεύς": "Priest", "Πρέσβυς": "Old Man",
    "Εὐρυδίκη": "Eurydice", "Θεράπαινα": "Servant",
    "Ἡμιχόριον": "Half-Chorus", "Ἡμιχόριον 1": "First Half-Chorus",
    "Ἡμιχόριον 2": "Second Half-Chorus",
}

# The augustine thou-sweep. ARCHAIC_OK stays EMPTY: the whole point of
# the edition is that none of Campbell's and Storr's costume survives,
# and an exemption list is how a sweep quietly stops working. If this
# fires, fix the sentence (the grimm rule).
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|art thou|"
    r"unto|ere|whilst|amongst|betwixt|methinks|forsooth|prithee|"
    r"yonder|nay|verily|behold|wherefore|whence|whither|hither|"
    r"perchance|mayhap|alack|o'er|ne'er|'tis|'twas|aught|naught|"
    r"sire|maiden|hark)\b", re.I)
ARCHAIC_OK = []

# A SPEAKER TAG AND A SHORT SENTENCE ARE THE SAME REGEX -- the thompson
# lesson, and this fired on correct prose before it was fixed. The
# character class has to admit a space (for "First Half-Chorus"), which
# means "You have cause to mourn." matched too: four phantom speeches in
# Ajax alone, each shifting every index after it, so the check reported a
# divergence in a file that was right. The names are a CLOSED SET taken
# from the Greek, so require membership rather than shape.
SPEAKER_LINE = re.compile(r"^([A-Z][A-Za-z' -]{1,24})\.$")
NAMES = set(SPEAKERS.values())
STAGE_LINE = re.compile(r"^\(.*\)$")
PART_LINE = re.compile(r"^\(Part (\d+) of (\d+)\)$")


def modern_speeches(path):
    """(speaker, sung) per speech, mirroring how assemble.py will read it.

    Walks paragraphs the way render_body does rather than testing each
    line, because a check that approximates the renderer costs edits to
    correct prose (the epictetus lesson).
    """
    out = []
    speaker = None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if STAGE_LINE.match(line.strip()) or PART_LINE.match(line.strip()):
            continue
        m = SPEAKER_LINE.match(line.strip())
        if m and m.group(1) in NAMES and not line.startswith("\t"):
            speaker = m.group(1)
            out.append([speaker, None])
            continue
        if out and out[-1][1] is None:
            out[-1][1] = line.startswith("\t")
    return [(s, bool(v)) for s, v in out if v is not None]


def source_speeches(files):
    """(speaker-in-English, sung) per speech, from the GREEK, per file."""
    per = {}
    idx = 0
    for n, title, date, eng in prep.PLAYS:
        g = prep.stream(prep.fetch(n, "grc2"))
        cuts = prep.split_points(g)
        bounds = [0] + cuts + [len(g)]
        for p in range(len(bounds) - 1):
            a, b = bounds[p], bounds[p + 1]
            per[f"{idx:03d}.txt"] = [
                (SPEAKERS.get(name, "?" + name), prep.is_sung(kind))
                for kind, name, lines, _ in g[a:b] if lines]
            idx += 1
    return per


def runs(seq):
    """Collapse a sung/spoken flag sequence into its alternating runs."""
    out = []
    for v in seq:
        if not out or out[-1] != v:
            out.append(v)
    return out


def main(argv):
    chap = os.path.join(HERE, "chapters")
    mod = os.path.join(HERE, "modern_chapters")
    want = argv[1:]
    files = sorted(f for f in os.listdir(chap) if f.endswith(".txt"))
    src = source_speeches(files)
    bad = 0
    seen = 0

    for f in files:
        mp = os.path.join(mod, f)
        if not os.path.exists(mp):
            continue
        if want and f[:3] not in want:
            continue
        seen += 1
        say = []
        text = open(mp, encoding="utf-8").read()
        sw = len(open(os.path.join(chap, f), encoding="utf-8").read().split())
        mw = len(text.split())

        # 1. ratio
        r = mw / max(1, sw)
        if not MIN_RATIO <= r <= MAX_RATIO:
            say.append(f"ratio {r:.2f} outside {MIN_RATIO}-{MAX_RATIO}")

        # 2. speaker sequence, against the Greek
        got = modern_speeches(mp)
        exp = src[f]
        gs = [s for s, _ in got]
        es = [s for s, _ in exp]
        if gs != es:
            say.append(f"speaker sequence: {len(gs)} speeches, source "
                       f"{len(es)}")
            for i, (a, b) in enumerate(zip(gs, es)):
                if a != b:
                    say.append(f"    first divergence at #{i+1}: "
                               f"wrote {a!r}, source has {b!r}")
                    break
            else:
                n = min(len(gs), len(es))
                say.append(f"    identical for {n}, then "
                           f"{'extra ' + str(gs[n:]) if len(gs) > n else 'missing ' + str(es[n:])}")

        # 3. sung/spoken structure
        if gs == es:
            gr, er = [v for _, v in got], [v for _, v in exp]
            if gr != er:
                for i, (a, b) in enumerate(zip(gr, er)):
                    if a != b:
                        say.append(
                            f"sung/spoken: speech #{i+1} ({es[i]}) is "
                            f"{'verse' if a else 'prose'} but the Greek "
                            f"marks it {'sung' if b else 'spoken'}")
                        break
            if runs(gr) != runs(er):
                say.append(f"sung/spoken runs {len(runs(gr))} vs "
                           f"{len(runs(er))} in source")

        # 4. heading and part marker (the quixote trap)
        lines = [l.rstrip("\n") for l in text.split("\n")]
        head = lines[0].strip() if lines else ""
        m = [x for x in prep.__dict__ if False]
        entry = None
        import json
        for e in json.load(open(os.path.join(HERE, "manifest.json"))):
            if e["file"] == f:
                entry = e
        if entry["of"] > 1:
            pm = PART_LINE.match(lines[1].strip() if len(lines) > 1 else "")
            if not pm:
                say.append("multi-part file with no '(Part n of k)' on "
                           "line 2 -- assemble.py will not warn")
            elif (int(pm.group(1)), int(pm.group(2))) != (entry["part"],
                                                          entry["of"]):
                say.append(f"part marker {pm.group(0)} but manifest says "
                           f"part {entry['part']} of {entry['of']}")
        if head != entry["title"]:
            say.append(f"heading {head!r}, manifest title "
                       f"{entry['title']!r}")

        # 5. archaism sweep, exemptions empty on purpose
        for mm in ARCHAIC.finditer(text):
            ctx = text[max(0, mm.start() - 40):mm.start() + 40]
            if any(ok in ctx for ok in ARCHAIC_OK):
                continue
            say.append(f"archaism {mm.group(0)!r}: "
                       f"...{ctx.strip()[:70]}...")

        # 6. emphasis: ask assemble.EMPH itself whether it renders
        stripped = assemble.EMPH.sub("", text)
        if "*" in stripped or "_" in stripped.replace("app_", ""):
            for line in text.split("\n"):
                if ("*" in assemble.EMPH.sub("", line)):
                    say.append(f"asterisk that EMPH will not render: "
                               f"{line.strip()[:60]}")
                    break

        # 7. no all-caps lines (assemble reads one as a heading)
        for line in lines:
            s = line.strip()
            if len(s) > 3 and s == s.upper() and any(c.isalpha() for c in s):
                say.append(f"all-caps line renders as a heading: {s[:50]}")
                break

        if say:
            bad += 1
            print(f"{f}:")
            for s in say:
                print(f"  {s}")
        else:
            print(f"{f}: ok  (ratio {r:.2f}, {len(gs)} speeches, "
                  f"{sum(1 for _, v in got if v)} sung)")

    print(f"\nchecked {seen}/{len(files)} translated files")
    if bad:
        print(f"{bad} file(s) with findings")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
