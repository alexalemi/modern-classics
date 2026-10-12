"""Per-book checks for On the Genealogy of Morals (run from the repo root).

    python3 books/genealogy/check.py               # source checks only
    python3 books/genealogy/check.py --modern      # + every modern file present
    python3 books/genealogy/check.py 004 005       # source + just these modern files

Exit status is nonzero on any FAIL. WARN lines are for the orchestrator.

SOURCE (what prep.py produced, checked against things prep did NOT produce)
  1. STRUCTURE AGAINST TWO INDEPENDENT WITNESSES. Nietzsche's book is a
     Preface of 8 numbered sections and three Essays of 17, 25 and 28.
     The counts are read (a) from zeno.org's own contents page for the
     book (its pages are "1-10 / 11-17", "1-10 / 11-20 / 21-25", ...) and
     the section headings on its pages, and (b) from Standard Ebooks'
     section ids in Samuel's translation. Neither comes from eKGWB or
     prep.py. The manifest must cover 1..n for each, once, in order.
  2. Manifest form: four headings only (Preface + three "Essay N: ..."),
     none matching assemble.PART_LINE; no part_before; each Essay's parts
     numbered 1..k with the same title; every split part opens on a
     section numeral (never on a mechanical cut); "sections" equals the
     lone roman numerals in the chapters/ file.
  3. SECOND WITNESS, word for word: each eKGWB section is compared with
     zeno's (Schlechta 1954, modernised spelling) after folding the
     spelling reform away (th->t, ß/ss, ie/i, c/k/z, -niss/-nis). Runs of
     more than LIMIT differing words are printed; more than BIG words is
     a FAIL (a dropped sentence or a leaked block). zeno is a witness
     only; nothing from it is published (except the one front note, see
     prep.FRONT_NOTE).

MODERN (modern_chapters/, once they exist)
  4. Line 1 is exactly the manifest title; a split file has "(Part n of
     k)" on line 2 and no other part marker anywhere; no "Part ...:" line.
  5. The lone roman numerals, in order, equal the manifest "sections".
  6. Emphasis: the number of *...* spans equals the German's (Sperrdruck).
  7. Verse: the number of tab-indented blocks equals the German's (one,
     the Homer lines in II 23; the file that has them).
  8. Renderability: no paragraph assemble.is_subheading would set as a
     heading, except the roman numerals.
  9. House form: straight quotes only (the collection's convention), no
     "--", no "_", no square brackets, no ALL-CAPS line, no NOTES block,
     no translator's notes.
 10. Locked vocabulary: banned forms (BANNED) -- Levy-era renderings the
     edition replaces, and the German/Greek that must not leak.
 11. Locked lines: the exact renderings in LOCKS appear in their file.
 12. Numerals in the German absent from the English: WARNINGS (first-
     edition page references are kept, so most hits are real).
 13. Ratio English/German (whitespace words): FAIL outside 0.95-1.45,
     WARN outside 1.05-1.32. Samuel's literal crib runs 1.08-1.19.
"""

import argparse
import difflib
import json
import re
import sys
from html import unescape
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent.parent
sys.path.insert(0, str(ROOT))
import assemble  # noqa: E402

EXPECTED = {"V": 8, "I": 17, "II": 25, "III": 28}
LIMIT, BIG = 3, 8
ROMAN = re.compile(r"^(?=[IVXL])(?:XL|L?X{0,3})(?:IX|IV|V?I{0,3})$")
EMPH = re.compile(r"\*[^*\n]+\*")

# zeno pages: file -> (essay, first, last)
ZENO = {"V": ("V", 1, 8), "I-01": ("I", 1, 10), "I-11": ("I", 11, 17),
        "II-01": ("II", 1, 10), "II-11": ("II", 11, 20), "II-21": ("II", 21, 25),
        "III-01": ("III", 1, 10), "III-11": ("III", 11, 20),
        "III-21": ("III", 21, 28)}

# Differences between eKGWB and zeno already read and ruled (section ->
# a substring of the differing eKGWB run). Fill as they are adjudicated.
KNOWN = {}

BANNED = [
    (r"\bÜbermensch|\bsuperman\b|\bsupermen\b", "overman (zarathustra lock)"),
    (r"\btransvaluation\b", "revaluation (Umwerthung)"),
    (r"\bresentment\b", "ressentiment (kept in French, Nietzsche's word)"),
    (r"\bmorality of morals\b|\bmorality of mores\b", "morality of custom"),
    (r"\bblonde beast\b|\bblond brute\b", "blond beast"),
    (r"\bAbhandlung\b|\bVorrede\b|\bAnmerkung\b", "German leaked"),
    (r"[Ͱ-Ͽἀ-῿]", "Greek script (transliterate)"),
    (r"\b(thou|thee|thy|thine|ye|hath|doth|dost|hast|shalt|wilt|canst|"
     r"spake|unto|verily|methinks|whither|thither|hither|wherefore|"
     r"behold|lo)\b", "archaism"),
]
BANNED = [(re.compile(p, 0 if "Greek" in w else re.I), w) for p, w in BANNED]

# exact renderings pinned at setup (running_notes.txt "LOCKED LINES")
LOCKS = {
    "000.txt": [
        "We are unknown to ourselves, we seekers of knowledge",
        '*Added to my most recently published book, "Beyond Good and Evil," as a supplement and clarification.*',
        "*Sils-Maria*, Upper Engadine, in July 1887.",
        "Each of us is farthest from himself",
        "*chewing the cud*",
    ],
    "002.txt": ["The slave revolt in morality begins when *ressentiment* itself becomes creative and gives birth to values"],
    "008.txt": [
        "Carefree, mocking, violent — that is how wisdom wants *us*: she is a woman, she only ever loves a warrior.",
        "Thus spoke Zarathustra.",
        "he would rather will *nothingness* than *not* will.",
    ],
    "013.txt": ["man would rather will *nothingness* than *not* will…"],
    "007.txt": ["*Zarathustra the godless*…"],
    "003.txt": ['"Rome against Judea, Judea against Rome"'],
}

fails, warns = [], []


def fail(f, msg):
    fails.append(f"FAIL {f}: {msg}")


def warn(f, msg):
    warns.append(f"WARN {f}: {msg}")


def paras(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def fold(s):
    s = s.lower().replace("’", "").replace("'", "")
    s = s.replace("ß", "ss")
    s = re.sub(r"th", "t", s)
    s = s.replace("ie", "i").replace("ss", "s")
    s = re.sub(r"[czk]", "k", s)
    return re.findall(r"\w+", s)


def zeno_sections():
    """{(essay, n): text} and the per-essay section counts zeno shows."""
    out, counts = {}, {}
    idx = (BOOK / "_src" / "zeno").glob("*.html")
    for p in sorted(idx):
        e, a, b = ZENO[p.stem]
        t = p.read_bytes().decode("latin-1")
        t = t[t.index('<div class="zenoCOMain">'):]
        t = t[:t.index('<div class="zenoCOFooter">')]
        t = re.sub(r'<a [^>]*class="zenoTXKonk"[^>]*>.*?</a>', " ", t)
        parts = re.split(r"<h5>\s*(\d+)\s*</h5>", t)
        nums = [int(x) for x in parts[1::2]]
        if nums != list(range(a, b + 1)):
            fail("structure", f"zeno {p.stem}: sections {nums} != {a}-{b}")
        counts[e] = max(counts.get(e, 0), max(nums))
        for k in range(1, len(parts), 2):
            body = re.sub(r"<[^>]+>", " ", parts[k + 1])
            out[(e, int(parts[k]))] = unescape(body)
    return out, counts


def se_counts():
    files = {"V": "preface.xhtml", "I": "chapter-1.xhtml",
             "II": "chapter-2.xhtml", "III": "chapter-3.xhtml"}
    out = {}
    for e, f in files.items():
        t = (BOOK / "_src" / "se" / "epub" / "text" / f).read_text()
        ids = [int(x) for x in re.findall(r'<section id="(?:chapter-\d|preface)-(\d+)"', t)]
        if ids != list(range(1, len(ids) + 1)):
            fail("structure", f"SE {f}: section ids out of order {ids[:5]}...")
        out[e] = len(ids)
    return out


def source_sections(manifest):
    """{(essay, n): text} from chapters/, split on the roman lines."""
    out = {}
    for m in manifest:
        t = (BOOK / "chapters" / m["file"]).read_text()
        cur = None
        for p in paras(t):
            s = p.strip()
            if ROMAN.match(s):
                cur = (m["essay"], m["sections"].index(s) + m["first"])
                out[cur] = []
            elif cur:
                out[cur].append(s)
    return {k: "\n".join(v) for k, v in out.items()}


def check_source(manifest):
    zeno, zc = zeno_sections()
    sc = se_counts()
    print("section counts: zeno", zc, " SE", sc, " expected", EXPECTED)
    if zc != EXPECTED:
        fail("structure", f"zeno counts {zc} != {EXPECTED}")
    if sc != EXPECTED:
        fail("structure", f"SE counts {sc} != {EXPECTED}")
    # coverage, in order
    cover = []
    for m in manifest:
        secs = [l.strip() for l in (BOOK / "chapters" / m["file"]).read_text().split("\n")
                if ROMAN.match(l.strip())]
        if secs != m["sections"]:
            fail(m["file"], f"chapters/ numerals {secs} != manifest {m['sections']}")
        if not (BOOK / "reference" / m["file"]).exists():
            fail(m["file"], "reference/ crib missing")
        cover += [(m["essay"], n) for n in range(m["first"], m["last"] + 1)]
    want = [(e, n) for e in EXPECTED for n in range(1, EXPECTED[e] + 1)]
    if cover != want:
        fail("structure", "manifest does not cover every section once, in order")
    # form
    titles = []
    for m in manifest:
        if m.get("part_before"):
            fail(m["file"], "part_before present (the Essays are top-level)")
        if assemble.PART_LINE.match(m["title"]):
            fail(m["file"], "title matches PART_LINE and would be deleted")
        if m["part"] == 1:
            titles.append(m["title"])
        if m["part"] > 1:
            first = paras((BOOK / "chapters" / m["file"]).read_text())[0].strip()
            if not ROMAN.match(first):
                fail(m["file"], f"a later part opens on {first[:40]!r}, not a section numeral")
    if len(titles) != 4 or len(set(titles)) != 4:
        fail("structure", f"expected 4 distinct headings, got {titles}")
    if titles[0] != "Preface" or not all(t.startswith(f"Essay {w}: ")
                                         for t, w in zip(titles[1:], ["One", "Two", "Three"])):
        fail("structure", f"heading forms {titles}")
    for e in EXPECTED:
        parts = [m for m in manifest if m["essay"] == e]
        if [m["part"] for m in parts] != list(range(1, len(parts) + 1)) or \
                any(m["of"] != len(parts) or m["title"] != parts[0]["title"] for m in parts):
            fail("structure", f"essay {e}: part numbering or titles inconsistent")
    # second witness
    ours = source_sections(manifest)
    odd = 0
    for key in want:
        a, b = fold(zeno.get(key, "")), fold(ours.get(key, ""))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            n = max(i2 - i1, j2 - j1)
            if op == "equal" or n <= LIMIT:
                continue
            run = " ".join(b[j1:j2])
            if any(k == key and s in run for k, s in KNOWN.items()):
                continue
            odd += 1
            tag = "FAIL" if n > BIG else "diff"
            print(f"  {tag} {key[0]} {key[1]} {op}: zeno={' '.join(a[i1:i2])[:80]!r} "
                  f"ours={run[:80]!r}")
            if n > BIG:
                fail("witness", f"{key[0]} {key[1]}: {n}-word difference vs zeno")
    print(f"second witness: {len(want)} sections compared, {odd} runs > {LIMIT} words differ")


def check_modern(m):
    f = m["file"]
    out_p = BOOK / "modern_chapters" / f
    if not out_p.exists():
        return False
    src = (BOOK / "chapters" / f).read_text()
    out = out_p.read_text()
    lines = out.split("\n")
    # 4 heading
    if lines[0].strip() != m["title"]:
        fail(f, f"line 1 is {lines[0]!r}, expected {m['title']!r}")
    start = 1
    if m["of"] > 1:
        want = f"(Part {m['part']} of {m['of']})"
        if len(lines) < 2 or lines[1].strip() != want:
            fail(f, f"line 2 should be {want!r}")
        start = 2
    body = "\n".join(lines[start:])
    if re.search(r"^\s*\(Part \d+ of \d+\)\s*$", body, re.M):
        fail(f, "a part marker below the heading")
    for i, l in enumerate(lines):
        s = l.strip()
        if i > 0 and (assemble.PART_LINE.match(s) or re.match(r"^(Part|Essay) \w+:", s)):
            fail(f, f"divider-like line {s[:50]!r}")
        if len(s) > 3 and s.isupper() and not ROMAN.match(s):
            fail(f, f"ALL-CAPS line {s!r}")
        if s in ("NOTES", "Notes") or re.match(r"^(Translator|Editor)'?s? note", s, re.I):
            fail(f, f"note block {s!r}")
    # 5 sections
    secs = [l.strip() for l in body.split("\n") if ROMAN.match(l.strip())]
    if secs != m["sections"]:
        fail(f, f"sections {secs} != {m['sections']}")
    # 6 emphasis
    es, eo = len(EMPH.findall(src)), len(EMPH.findall(out))
    if es != eo:
        fail(f, f"{eo} emphasis spans, German has {es}")
    if out.count("*") % 2:
        fail(f, "odd number of asterisks")
    # 7 verse
    vs = sum(1 for p in paras(src) if p.startswith("\t"))
    vo = sum(1 for p in paras(body) if p.startswith("\t"))
    if vs != vo:
        fail(f, f"{vo} verse blocks, German has {vs}")
    for p in paras(body):
        if not p.startswith("\t") and re.search(r"^[ \t]", p, re.M):
            fail(f, f"indented prose (would render as <pre>): {p.strip()[:40]!r}")
    # 8 renderability
    for p in paras(body):
        s = p.strip()
        if p.startswith("\t") or ROMAN.match(s):
            continue
        if assemble.is_subheading(s):
            fail(f, f"renders as a heading: {s!r}")
    # 9 house form
    if re.search("[‘’“”„«»]", out):
        fail(f, "curly or German quotation marks (the collection uses straight)")
    if "--" in out:
        fail(f, "double hyphen (use a real em dash)")
    if "_" in out or "[" in out or "]" in out:
        fail(f, "underscore or square bracket in the text")
    # 10 banned
    for rx, why in BANNED:
        for h in set(rx.findall(out)):
            fail(f, f"banned {h!r} -> {why}")
    # 11 locks
    for s in LOCKS.get(f, []):
        if s not in out.replace("\n", " "):
            fail(f, f"locked line missing: {s!r}")
    # 12 numerals (warnings)
    nums = lambda s: set(re.findall(r"\d+", s))
    missing = nums(src) - nums(out)
    if missing:
        warn(f, f"German numerals absent in English: {sorted(missing, key=int)}")
    # 13 ratio
    r = len(body.split()) / max(1, len(src.split()))
    if not 0.95 <= r <= 1.45:
        fail(f, f"ratio {r:.2f} outside 0.95-1.45")
    elif not 1.05 <= r <= 1.32:
        warn(f, f"ratio {r:.2f} outside the expected 1.05-1.32")
    print(f"{f} ratio {r:.2f}  {m['title']} ({m['part']}/{m['of']})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modern", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    manifest = json.loads((BOOK / "manifest.json").read_text())
    check_source(manifest)
    want = {a if a.endswith(".txt") else f"{int(a):03d}.txt" for a in args.files}
    done = 0
    if args.modern or want:
        for m in manifest:
            if want and m["file"] not in want:
                continue
            done += check_modern(m)
    for l in warns + fails:
        print(l)
    print(f"{done} modern files checked; {len(fails)} failures, {len(warns)} warnings")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
