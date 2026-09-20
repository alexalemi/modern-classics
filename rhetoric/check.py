"""Per-book checks for rhetoric/ -- the euclid-rivals pattern.

What verify.py cannot see here:
  1. VERSE PARITY. Aristotle quotes Homer, Euripides, Simonides and the
     rest, and Perseus sets every quotation as <lg>. A quoted line
     dissolved into prose is this book's silent summarisation, and a
     dropped one moves the ratio by nothing. Blocks and lines per block
     are compared EXACTLY against chapters/ (the boethius rule).
  2. THE CRIB'S APPARATUS LEAKING IN: a "[Note:" (Freese's footnotes are a
     crib, not text) or a "§" section mark (the translator's guide).
  3. THE ARCHAISM SWEEP (augustine): Freese is a 1926 Loeb and the drift
     is into his English. ARCHAIC_OK stays empty.
  4. Heading parity, renderer parity (emphasis via assemble.EMPH itself,
     all-caps and is_subheading asked of the renderer, per paragraph).
MEASURED AND NOT INCLUDED: the fleming numeric diff. The Greek writes its
numbers as words; a digit check would be inert, and an inert check that
looks like coverage is worse than none (the nights lesson).

    python3 rhetoric/check.py [NNN ...]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import assemble                                       # noqa: E402

MIN_RATIO, MAX_RATIO = 1.40, 2.20   # Greek prose -> English; Freese runs 1.49
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|art thou|"
    r"unto|ere|whilst|amongst|betwixt|methinks|forsooth|yonder|nay|"
    r"verily|behold|wherefore|whence|whither|hither|perchance|o'er|"
    r"ne'er|'tis|'twas|aught|naught|hark|lo)\b", re.I)
ARCHAIC_OK = []


def blocks(body):
    # count only lines with content: a block ending the file carries a
    # trailing newline, which split("\n") turned into a phantom line
    out = []
    for p in re.split(r"\n\s*\n", body):
        ls = [l for l in p.split("\n") if l.strip()]
        if ls and all(l.startswith("\t") for l in ls):
            out.append(len(ls))
    return out


def main(argv):
    chap = os.path.join(HERE, "chapters")
    mod = os.path.join(HERE, "modern_chapters")
    want = argv[1:]
    manifest = {e["file"]: e for e in json.load(open(os.path.join(HERE, "manifest.json")))}
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
        body = "\n".join(lines[1:])
        sw = len(re.sub(r"§\d+", "", body_src).split())
        mw = len(body.split())
        r = mw / max(1, sw)
        # A SHORT CHAPTER CANNOT CARRY THE BAND: 2.14 is some 200 Greek
        # words, and an agent padded it to clear 1.40, which is the one thing
        # the band exists to prevent the opposite of. Under 400 Greek words
        # the floor is 1.20; the ceiling is unchanged.
        lo = MIN_RATIO if sw >= 400 else 1.20
        if not lo <= r <= MAX_RATIO:
            say.append(f"ratio {r:.2f} outside {lo}-{MAX_RATIO}")
        if lines[0].strip() != manifest[f]["title"]:
            say.append(f"heading {lines[0]!r}, manifest {manifest[f]['title']!r}")
        if lines[1:2] != [""]:
            say.append("line 2 must be blank")
        vs, vm = blocks(body_src), blocks(body)
        if vs != vm:
            say.append(f"verse blocks {vm} against the Greek's {vs}")
        if "[Note" in text or "§" in text:
            say.append("crib apparatus ([Note: or §) in the translation")
        for m in ARCHAIC.finditer(text):
            ctx = text[max(0, m.start() - 40):m.start() + 40]
            if not any(ok in ctx for ok in ARCHAIC_OK):
                say.append(f"archaism {m.group(0)!r}: ...{ctx.strip()[:70]}...")
        stripped = assemble.EMPH.sub("", text)
        if "*" in stripped or "_" in stripped:
            say.append("asterisk or underscore that EMPH will not render")
        # test for the tab BEFORE stripping: an indented paragraph takes the
        # renderer's verse branch and is never asked is_subheading (the
        # stripped test flagged short verse lines, and an agent added a comma
        # to a line of verse to get past it)
        for par in [p.strip("\n") for p in body.split("\n\n")]:
            if not par.strip() or par.startswith("\t"):
                continue
            par = par.strip()
            par = " ".join(par.split())
            if len(par) > 3 and par == par.upper() and any(c.isalpha() for c in par):
                say.append(f"all-caps paragraph renders as a heading: {par[:50]}")
            elif assemble.is_subheading(par):
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
