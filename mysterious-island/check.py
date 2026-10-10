"""Book-specific checks for mysterious-island/ (run from the repo root).

    python3 mysterious-island/check.py            # source checks only
    python3 mysterious-island/check.py --modern   # + translated files

What verify.py cannot see here (see the memory notes on silent defect
classes and on checks that cannot see a missing section):

SOURCE (prep.py's output)
  1. The structure matches the book's OWN table of contents, read from
     the Gutenberg French TOC (not from anything prep.py produced):
     3 Parts, 22 + 20 + 20 chapters.
  2. Manifest headings: "Chapter N: Title" (assemble.CHAP_LINE, so each
     nests under its Part), N restarting per Part and running 1..n;
     exactly three part_before dividers, in WORD form, none matching
     assemble.PART_LINE (which would delete it); no split files.
  3. Every file opens on its Hetzel summary (= manifest summary_fr), and
     every [n] footnote marker resolves to exactly one NOTES entry.
  4. COMPLETENESS AGAINST A SECOND WITNESS: prep.py's bodies (summary and
     NOTES removed, [n] markers removed) are diffed word for word against
     the Gutenberg French #14287. The only expected residue is the
     I.1/I.2 boundary (Gutenberg gives the balloon's landing to chapter
     II; Hetzel's own summary for I ends "Une côte à l'horizon. — Le
     dénouement du drame"). Any other difference longer than LIMIT words
     is printed: an illustration caption that leaked into the body, or a
     paragraph that the HTML extraction dropped.
  5. The White crib has 62 chapters; chapters where White cut heavily
     (crib/French word ratio < 0.7) are listed, because there the crib
     is a trap, not a help.

MODERN (modern_chapters/, once they exist)
  6. Line 1 is exactly the manifest title; the first paragraph after it
     is the translated summary in _underscores_ (under assemble's
     400-char EMPH limit); no "(Part" marker, no "Part ...:" divider
     line, no NOTES block, no "[n]" marker left; no paragraph that
     assemble.is_subheading would set as a heading (the book has none,
     so a hit is a leaked inscription or signature); straight quotes.
  7. Locked names: none of the Victorian translators' renamings (Neb,
     Herbert, Harding, Pencroft, Gideon) and none of the unlocked place
     forms listed in BANNED.
  8. Numeral parity (the fleming/ pattern): digits in the French that
     are absent from the English are printed for a human to read —
     WARNINGS, since converted temperatures and dropped conversion notes
     legitimately remove numbers.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT))
from assemble import CHAP_LINE, PART_LINE, is_subheading  # noqa: E402

LIMIT = 4
# Differences already read against the Hetzel scan and found to be
# Gutenberg's loss, not ours: file -> the start of OUR extra text.
KNOWN = {
    # I.19: Gutenberg stops the sentence at "le boucher hermétiquement."
    # and drops "et, s'il le faut même, en dissimuler absolument l'entrée
    # en provoquant, au moyen d'un barrage, un relèvement des eaux du lac."
    "018.txt": "s il le faut même en dissimuler",
}
EXPECTED = {1: 22, 2: 20, 3: 20}
WORD_PARTS = ("Part One: ", "Part Two: ", "Part Three: ")

BANNED = [
    r"\bNeb\b", r"\bHerbert\b", r"\bHarding\b", r"\bPencroft\b",
    r"\bGideon\b", r"\bTippo", r"\bBundelkund\b", r"\bGrande-Vue\b",
    r"\bGrand View\b", r"\bFlotsam Point\b", r"\bFalls River\b",
    r"\bPort Balloon\b", r"\bTadorns?\b", r"\bDakkar Grotto\b",
    r"\bCape Claw\b", r"\bMonsieur Cyrus\b", r"\bMonsieur Smith\b",
    r"\bcentigrade\b", r"\bCelsius\b", r"\bBonaventure\b",
]

fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def words(s):
    s = s.replace("’", "'").replace(" ", " ")
    s = re.sub(r"\[\d+\]", " ", s)
    return re.findall(r"\w+", s.lower())


def body_of(text):
    """Source file minus its summary paragraph and its NOTES block."""
    text = text.split("\nNOTES\n")[0]
    return text.split("\n\n", 1)[1]


def gutenberg_chapters():
    t = (BOOK / "_src" / "pg14287-fr.txt").read_text(encoding="utf-8")
    t = t.replace("\r\n", "\n")
    t = t[t.index("*** START"):t.index("*** END")]
    toc_end = t.index("\nPARTIE 1\n")
    toc = t[:toc_end]
    # the book's own contents list: parts and chapter entries
    toc_parts = re.split(r"\n\s*PARTIE \d [^\n]*\n", toc)[1:]
    toc_counts = [len(re.findall(r"^\s*CHAPITRE [IVXL]+\s*$", p, re.M))
                  for p in toc_parts]
    body = t[toc_end:]
    parts = re.split(r"\nPARTIE \d\n", body)[1:]
    chs = [re.split(r"\nCHAPITRE [IVXL]+\n", p)[1:] for p in parts]
    return toc_counts, chs


def check_source(manifest):
    # 1. structure against the book's own contents list
    toc_counts, gchs = gutenberg_chapters()
    print("Gutenberg TOC counts per Part:", toc_counts)
    if toc_counts != list(EXPECTED.values()):
        fail(f"TOC counts {toc_counts} != {list(EXPECTED.values())}")
    if [len(c) for c in gchs] != list(EXPECTED.values()):
        fail(f"Gutenberg body counts {[len(c) for c in gchs]}")
    if len(manifest) != sum(EXPECTED.values()):
        fail(f"manifest has {len(manifest)} entries, expected 62")

    # 2. headings and dividers
    dividers = [m for m in manifest if m.get("part_before")]
    if len(dividers) != 3:
        fail(f"{len(dividers)} part_before dividers, expected 3")
    for m, pref in zip(dividers, WORD_PARTS):
        pb = m["part_before"]
        if not pb.startswith(pref) or PART_LINE.match(pb):
            fail(f"{m['file']}: divider {pb!r} not in word form")
    expect_n = 0
    for m in manifest:
        if m.get("part_before"):
            expect_n = 0
        expect_n += 1
        cm = CHAP_LINE.match(m["title"])
        if not cm:
            fail(f"{m['file']}: title {m['title']!r} fails CHAP_LINE")
        elif int(cm.group(1)) != expect_n:
            fail(f"{m['file']}: chapter number {cm.group(1)} != {expect_n}")
        if (m["part"], m["of"]) != (1, 1):
            fail(f"{m['file']}: unexpected split {m['part']}/{m['of']}")

    # 3. summaries and footnotes
    for m in manifest:
        text = (BOOK / "chapters" / m["file"]).read_text(encoding="utf-8")
        if text.split("\n\n", 1)[0] != m["summary_fr"]:
            fail(f"{m['file']}: does not open on its summary")
        main, _, notes = text.partition("\nNOTES\n")
        refs = sorted(map(int, re.findall(r"\[(\d+)\]", main)))
        defs = sorted(map(int, re.findall(r"^\[(\d+)\] ", notes, re.M)))
        if refs != defs or len(set(refs)) != len(refs):
            fail(f"{m['file']}: note refs {refs} vs defs {defs}")

    # 4. second-witness completeness
    flat_g = [c for part in gchs for c in part]
    ours = [body_of((BOOK / "chapters" / m["file"]).read_text(
        encoding="utf-8")) for m in manifest]
    # compare I.1+I.2 as one unit (the known boundary difference)
    pairs = [("000+001", ours[0] + "\n\n" + ours[1],
              flat_g[0] + "\n\n" + flat_g[1])]
    pairs += [(m["file"], o, g) for m, o, g in
              zip(manifest[2:], ours[2:], flat_g[2:])]
    total_odd = 0
    for name, o, g in pairs:
        a, b = words(g), words(o)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "equal" and max(i2 - i1, j2 - j1) > LIMIT:
                if name in KNOWN and op == "insert" and \
                        " ".join(b[j1:j2]).startswith(KNOWN[name]):
                    print(f"  known Gutenberg omission in {name}: kept ours")
                    continue
                total_odd += 1
                print(f"  DIFF {name} {op}: gutenberg={' '.join(a[i1:i2])[:90]!r}"
                      f" ours={' '.join(b[j1:j2])[:90]!r}")
    if total_odd:
        fail(f"{total_odd} body differences > {LIMIT} words vs Gutenberg")
    else:
        print(f"second witness: all 62 bodies agree with Gutenberg "
              f"(no run > {LIMIT} words differs)")
    # the boundary itself: Gutenberg's I.1 must end where ours does NOT
    if words(flat_g[0])[-6:] == words(ours[0])[-6:]:
        print("  note: I.1 boundary now agrees with Gutenberg")

    # 5. crib coverage
    thin = []
    for m in manifest:
        ref = (BOOK / "reference" / m["file"]).read_text()
        w = len(ref.split("\n\n", 1)[1].split())     # minus the banner
        r = w / m["words"]
        if r < 0.7:
            thin.append(f"{m['file']} ({m['chapter']}) {r:.2f}")
    print("thin White crib (<0.7 of the French):", ", ".join(thin) or "none")


def check_modern(manifest):
    mod = BOOK / "modern_chapters"
    for m in manifest:
        f = mod / m["file"]
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        if paras[0].strip() != m["title"]:
            fail(f"{m['file']}: heading {paras[0][:60]!r} != {m['title']!r}")
        if len(paras) < 2 or not re.fullmatch(r"_[^_]+_", paras[1].strip()):
            fail(f"{m['file']}: second paragraph is not the _summary_")
        elif len(paras[1]) > 400:
            fail(f"{m['file']}: summary over assemble's 400-char EMPH limit")
        # this book has no subheadings: anything assemble would set as
        # one is a leaked short line (an inscription, a signature)
        for par in paras[1:]:
            if not par.startswith(" ") and is_subheading(par.strip()):
                fail(f"{m['file']}: would render as a heading: {par[:50]!r}")
        if re.search("[\u2018\u2019\u201c\u201d]", text):
            fail(f"{m['file']}: curly quotes (collection uses straight)")
        for ln in text.splitlines()[1:]:
            s = ln.strip()
            if re.match(r"^\(Part \d", s) or re.match(r"^Part \w+:", s):
                fail(f"{m['file']}: stray part line {s[:50]!r}")
            if s == "NOTES":
                fail(f"{m['file']}: NOTES block carried over")
        if re.search(r"\[\d+\]", text):
            fail(f"{m['file']}: footnote marker left in text")
        for pat in BANNED:
            for hit in re.finditer(pat, text):
                fail(f"{m['file']}: banned form {hit.group(0)!r}")
        # 8. numeral parity (warnings)
        src = (BOOK / "chapters" / m["file"]).read_text(encoding="utf-8")
        src = src.split("\nNOTES\n")[0]
        nums = lambda s: set(re.findall(r"\d+", s.replace(" ", "")))
        missing = nums(src) - nums(text)
        if missing:
            print(f"  WARN {m['file']}: French numerals absent in English: "
                  f"{sorted(missing, key=int)[:12]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modern", action="store_true")
    args = ap.parse_args()
    manifest = json.loads((BOOK / "manifest.json").read_text())
    check_source(manifest)
    if args.modern:
        check_modern(manifest)
    print(f"\n{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
