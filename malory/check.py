#!/usr/bin/env python3
"""Per-book checks for Le Morte d'Arthur that verify.py structurally cannot make.

    python3 malory/check.py

SETUP CHECKS (run now, before anything is translated)

  1. THE BOOK'S OWN TABLE OF CONTENTS. Caxton's preface states how many
     chapters each of his 21 Books contains. That is the one description of
     the book the pipeline did not produce (checks-that-cannot-see-a-missing-
     section), so the manifest is counted against it. It disagrees in
     exactly three places, all Caxton's own numbering, and the disagreement
     is ENCODED, not waved through:
        Book I    preface XXVIII, printed 27 (the preface's slip)
        Book IV   preface XXIX, printed 28 (Pollard: "Misnumbered XX by
                  Caxton" - his numbering skips a chapter)
        Book VII  preface XXXVI, printed 35 (Pollard: chapter XXV
                  "misnumbered XXVI, setting the numeration wrong to the
                  end of the book")
     Any OTHER disagreement, or any change in these three, fails.

  2. A SECOND WITNESS. Gutenberg #1251/#1252 is a separate transcription of
     the same Pollard text. Its chapter rubrics, read in order, must match
     SE's rubric for rubric. Gutenberg's own chapter NUMERALS cannot be
     used: three of its headings have typos ("CHAPTER VII" missing its
     period, "XXVIII" for XXXVIII, "XIX" for XXXIX), which is exactly why
     the rubric text, not the numeral, is compared.

  3. THE MANIFEST AGAINST titles.json: every heading is "Chapter C: ..."
     with C running 1..n inside each Book, one divider per Book in word
     form, no "Part <Roman>:" line anywhere, "of" == 1 everywhere.

TRANSLATION CHECKS (run on whatever modern_chapters/ exist)

  4. HEADING LINE: line 1 is the manifest title EXACTLY, line 2 blank. A
     Book divider written into a file would become the chapter heading and
     swallow the real one, so no line may start "Book <Word>:".
  5. CONVENTIONS: no all-caps line (renders as a heading), no asterisk or
     underscore (renders as emphasis), no tab indent (there is no verse),
     balanced straight double quotes in every paragraph.
  6. THE SWEEP: archaic forms and pre-lock name spellings that should not
     survive (thou, hath, anon, "wit ye", Launcelot, Guenever, damosel...).
     Exempt by EXACT PHRASE in SWEEP_EXEMPT, never by loosening a pattern.
"""
import json
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
SRC, MOD = BOOK / "chapters", BOOK / "modern_chapters"
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
WORDS = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
         "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen "
         "Twenty Twenty-One").split()
ORDINAL = ("First Second Third Fourth Fifth Sixth Seventh Eighth Ninth Tenth "
           "Eleventh Twelfth Thirteenth Fourteenth Fifteenth Sixteenth "
           "Seventeenth Eighteenth Nineteenth Twentieth Twenty-first").split()
# SE rubrics Gutenberg lacks, each verified by hand. IX.14: Gutenberg
# runs it on inside IX.13 with no heading (the text is present, at
# pg1251.txt ~line 12733); SE's 44 chapters for Book IX agree with
# Caxton's preface (XLIV), Gutenberg's 43 do not.
WITNESS_OK = ["how sir maliagaunce told for what cause"]
CAXTON_SLIPS = {1: (28, 27), 4: (29, 28), 7: (36, 35)}

SWEEP = re.compile(
    r"\b(thou|thee|thy|thine|ye|hath|doth|hast|dost|art thou|wilt|shalt|"
    r"anon|wit ye|wist|hight|nigh|wroth|liefer|certes|"
    r"Launcelot|Guenever|Gawaine|Agravaine|Uwaine|Percivale|Isoud|"
    r"Carlion|Logris|Avilion|damosels?|Margawse|Morgawse|Explicit)\b")
SWEEP_EXEMPT = [
    # exact phrases a correct translation may contain; add with a reason
]

failures = []


def roman(s):
    n = 0
    for a, b in zip(s, s[1:] + " "):
        v = ROMAN[a]
        n += -v if b != " " and ROMAN[b] > v else v
    return n


def norm(s):
    s = s.replace("’", "'").lower()
    s = re.sub(r"[^a-z' ]+", " ", s)
    return " ".join(s.split()[:7])


def setup_checks(manifest, titles):
    chapters = [m for m in manifest if "book" in m]
    per_book = {}
    for m in chapters:
        per_book[m["book"]] = per_book.get(m["book"], 0) + 1

    # 1. Caxton's preface
    pre = (SRC / "000.txt").read_text()
    claims = re.findall(r"The (\S+) Book\b.*?containeth ([IVXLC]+) chapters", pre)
    ords = [o.lower() for o in ORDINAL]
    stated = {}
    for o, n in claims:
        o = o.lower()
        if o in ords:
            stated[ords.index(o) + 1] = roman(n)
    if len(stated) != 21:
        failures.append(f"TOC: parsed {len(stated)} Book counts from Caxton's preface, need 21")
    for b in range(1, 22):
        want, got = stated.get(b), per_book.get(b)
        if want == got:
            continue
        if CAXTON_SLIPS.get(b) == (want, got):
            continue
        failures.append(f"TOC: Book {b}: Caxton says {want}, manifest has {got}")
    if "five hundred and seven chapters" not in pre:
        failures.append("TOC: Caxton's total (507) not found in preface")
    print(f"1. Caxton's table: {sum(per_book.values())} chapters in 21 Books "
          f"(preface 507; the 3 known slips in Books {sorted(CAXTON_SLIPS)})")

    # 2. Gutenberg witness
    g = ""
    for f in ("pg1251.txt", "pg1252.txt"):
        p = BOOK / "source" / "gutenberg" / f
        if not p.exists():
            failures.append(f"WITNESS: {p} missing (run fetch.sh)")
            return
        t = p.read_text()
        t = t.split("*** START OF", 1)[1].split("*** END OF", 1)[0]
        g += t
    body = g.split("PREFACE OF WILLIAM CAXTON")[-1]  # past the contents list
    lines = body.split("\n")
    grubs = []
    for i, ln in enumerate(lines):
        # "[IVXLCl]": Gutenberg prints XII.8 as "CHAPTER VIlI."
        m = re.match(r"^CHAPTER [IVXLCl]+\.? (.*)$", ln)
        if m:
            rub = m.group(1)
            j = i + 1
            while j < len(lines) and lines[j].strip():
                rub += " " + lines[j].strip()
                j += 1
            grubs.append(norm(rub))
    ses = [norm(m["caxton"]) for m in chapters]
    # Align, don't zip: one missing heading in either witness would
    # otherwise shift every later pair. Rubrics are compared on their
    # first words with spelling noise folded (enterprized/enterprised).
    import difflib
    def key(r):
        return " ".join(r.replace("z", "s").split()[:4])
    sm = difflib.SequenceMatcher(None, [key(r) for r in ses],
                                 [key(r) for r in grubs], autojunk=False)
    bad = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            continue
        for i in range(a1, a2):
            bad.append(f"SE only: {chapters[i]['chapter']} '{ses[i]}'")
        for j in range(b1, b2):
            bad.append(f"Gutenberg only: '{grubs[j]}'")
    for x in bad:
        if x.split(":")[0] == "SE only" and any(x.endswith(f"'{ok}'") for ok in WITNESS_OK):
            continue
        failures.append("WITNESS: " + x)
    print(f"2. Gutenberg witness: {len(grubs)} rubrics, {len(bad)} mismatches")

    # 3. manifest vs titles.json
    if manifest[0]["title"] != titles["front"]["preface"]:
        failures.append("MANIFEST: 000 title")
    expect_c = {}
    for m in manifest:
        if m.get("of") != 1 or m.get("part") != 1:
            failures.append(f"MANIFEST: {m['file']} part/of not 1/1")
        if re.match(r"^Part [IVXLC0-9]+: ", m["title"]):
            failures.append(f"MANIFEST: {m['file']} PART_LINE title")
        if "book" not in m:
            continue
        b = m["book"]
        c = expect_c[b] = expect_c.get(b, 0) + 1
        if m["chapter"] != f"{b}-{c}":
            failures.append(f"MANIFEST: {m['file']} is {m['chapter']}, expected {b}-{c}")
        if m["title"] != titles["chapters"][m["chapter"]]:
            failures.append(f"MANIFEST: {m['file']} title differs from titles.json")
        if not m["title"].startswith(f"Chapter {c}: "):
            failures.append(f"MANIFEST: {m['file']} heading number")
        div = m.get("part_before")
        if (c == 1) != bool(div):
            failures.append(f"MANIFEST: {m['file']} divider placement")
        if div and not div.startswith(f"Book {WORDS[b - 1]}: "):
            failures.append(f"MANIFEST: {m['file']} divider {div!r}")
    print(f"3. manifest: {len(manifest)} files checked against titles.json")


def translation_checks(manifest):
    done = [m for m in manifest if (MOD / m["file"]).exists()]
    hits = 0
    for m in done:
        text = (MOD / m["file"]).read_text()
        lines = text.split("\n")
        if lines[0] != m["title"]:
            failures.append(f"HEADING: {m['file']} line 1 {lines[0][:60]!r}")
        if len(lines) < 2 or lines[1].strip():
            failures.append(f"HEADING: {m['file']} line 2 not blank")
        for ln in lines[1:]:
            if re.match(r"^Book [A-Z][a-z-]+:", ln):
                failures.append(f"DIVIDER: {m['file']} {ln[:50]!r}")
            letters = re.sub(r"[^A-Za-z]", "", ln)
            if len(letters) > 3 and letters.isupper():
                failures.append(f"ALLCAPS: {m['file']} {ln[:50]!r}")
            if ln.startswith(("\t", "    ")):
                failures.append(f"INDENT: {m['file']} {ln[:50]!r}")
        if "*" in text or re.search(r"(?<!\w)_|_(?!\w)", text):
            failures.append(f"MARKUP: {m['file']} has * or _")
        if "“" in text or "”" in text:
            failures.append(f"QUOTES: {m['file']} curly double quotes (house style is straight)")
        for k, par in enumerate(text.split("\n\n")):
            if par.count('"') % 2:
                failures.append(f"QUOTES: {m['file']} paragraph {k} unbalanced")
        body = text
        for ex in SWEEP_EXEMPT:
            body = body.replace(ex, "")
        for sm in SWEEP.finditer(body):
            hits += 1
            if hits <= 40:
                ctx = body[max(0, sm.start() - 30):sm.end() + 30].replace("\n", " ")
                failures.append(f"SWEEP: {m['file']} {sm.group(0)!r}: ...{ctx}...")
    print(f"4-6. modern files present: {len(done)} of {len(manifest)}"
          + (f"; sweep hits {hits}" if done else ""))


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    titles = json.loads((BOOK / "titles.json").read_text())
    setup_checks(manifest, titles)
    translation_checks(manifest)
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("all checks pass")


if __name__ == "__main__":
    main()
