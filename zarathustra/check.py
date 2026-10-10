"""Per-book checks for Thus Spoke Zarathustra.

    python3 zarathustra/check.py              # structure + every modern file present
    python3 zarathustra/check.py 001 002      # just these files (and structure)

Exit status is nonzero on any FAIL. WARN lines are for the orchestrator.

STRUCTURE (runs every time, needs no translation):
  - Nietzsche's own contents list (the Inhaltsverzeichnis in _src/de_7205.txt,
    parsed HERE, not by prep) against manifest.json: 81 sections (Prologue +
    80 discourses: 22/22/16/20) in order, plus the three Part epigraphs.
    This is the one description of the book the pipeline did not produce.
  - part_before only in word form ("Part Two"), once per Part.
  - every chapters/ and reference/ file present and non-empty.

PER MODERN FILE (what verify.py cannot see):
  1. heading: line 1 is the manifest title verbatim; a split file has
     "(Part n of k)" on line 2 and nothing else does.
  2. sub-sections: the lone roman-numeral lines, in order, equal the
     manifest's "sections" (Nietzsche's numbered sections).
  3. refrain parity: "Also sprach Zarathustra" in the German == "Thus spoke
     Zarathustra" in the English. Free and exact.
  4. verse: the number of tab-indented blocks equals the German's.
  5. emphasis: the number of *...* spans equals the German's (Sperrdruck).
  6. archaism sweep, NO exemptions: thou/thee/thy/thine/ye/hath/doth/
     spake/unto/verily/-eth verbs... The thou-and-eth costume is Common's,
     not Nietzsche's (text_analysis 2).
  7. locked-term sweep: no Übermensch, superman, Superman, metamorphosis
     spelled as "transformations" in the title formula, "Backworldsmen".
  8. renderability: no paragraph the renderer would set as a heading
     (assemble.is_subheading), except the roman numerals, line 1, and the
     "Zarathustra’s Discourses" line that closes 000.
  9. house form: no "--", no ALL-CAPS line, no "Part X:" line, no "_",
     no square brackets.
 10. ratio: English/German whitespace words, FAIL outside 0.95-1.45,
     WARN outside 1.02-1.32 (Common's literal crib runs 0.99-1.17).
"""

import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT))
import assemble  # noqa: E402

ROMAN = re.compile(r"^(?=[IVXL])(?:XL|L?X{0,3})(?:IX|IV|V?I{0,3})$")
EMPH = re.compile(r"\*[^*\n]+\*")
ARCH = re.compile(
    r"\b(thou|thee|thy|thine|ye|hath|doth|dost|hast|art thou|shalt|wilt|canst|"
    r"wouldst|couldst|shouldst|didst|wast|wert|spake|unto|verily|methinks|"
    r"'tis|’tis|twas|’twas|ere|nay|yea|whither|thither|hither|wherefore|"
    r"saith|behold|lo)\b", re.I)
ETH = re.compile(r"\b[a-z]{2,}eth\b", re.I)
ETH_OK = {"teeth", "seth", "beneath", "breath"}
BANNED = re.compile(r"Übermensch|\bsuperman\b|\bsupermen\b|Backworld|Hinterworld|"
                    r"\bdown-going\b|\bpitiful ones\b", re.I)
DISCOURSES = "Zarathustra’s Discourses"

fails, warns = [], []


def fail(f, msg):
    fails.append(f"FAIL {f}: {msg}")


def warn(f, msg):
    warns.append(f"WARN {f}: {msg}")


def paras(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def verse_blocks(text):
    return sum(1 for p in paras(text) if p.startswith("\t"))


def structure(manifest):
    raw = (BOOK / "_src" / "de_7205.txt").read_text(encoding="utf-8").replace("\r", "")
    L = raw.split("\n")
    i0 = L.index("Inhaltsverzeichnis")
    i1 = next(i for i in range(i0 + 2, len(L)) if L[i].strip() == "Erster Theil"
              and i > i0 + 10)
    toc = [l.strip() for l in L[i0 + 1:i1] if l.strip()]
    parts = [i for i, t in enumerate(toc) if t.endswith("Theil")]
    assert len(parts) == 4, toc
    counts, titles = [], []
    for a, b in zip(parts, parts[1:] + [len(toc)]):
        sec = [t for t in toc[a + 1:b] if t != "Die Reden Zarathustra’s"]
        counts.append(len(sec))
        titles += [re.sub(r" \(Oder:.*\)$", "", t) for t in sec]
    if counts != [23, 22, 16, 20]:
        fail("structure", f"contents list counts {counts}, expected [23, 22, 16, 20]")
    seen = []
    for m in manifest:
        if m["de_title"].startswith("Motto"):
            continue
        if m["part"] == 1:
            seen.append(m["de_title"])
    if seen != titles:
        bad = [(a, b) for a, b in zip(seen, titles) if a != b]
        fail("structure", f"manifest sections {len(seen)} vs contents {len(titles)}; first mismatch {bad[:3]}")
    epi = [m for m in manifest if m["de_title"].startswith("Motto")]
    if len(epi) != 3:
        fail("structure", f"{len(epi)} epigraph files, expected 3")
    pb = [m["part_before"] for m in manifest if m.get("part_before")]
    if pb != ["Part One", "Part Two", "Part Three", "Part Four"]:
        fail("structure", f"part dividers {pb}")
    if any(assemble.PART_LINE.match(p) for p in pb):
        fail("structure", "a part divider matches PART_LINE and would be deleted")
    tset = [m["title"] for m in manifest if m["part"] == 1]
    if len(tset) != len(set(tset)):
        fail("structure", "repeated section title (repeated anchor)")
    for m in manifest:
        for d in ("chapters", "reference"):
            p = BOOK / d / m["file"]
            if not p.exists() or not p.read_text().strip():
                fail(m["file"], f"{d}/ file missing or empty")
        if m["of"] > 1 and not (BOOK / "chapters" / m["file"]).read_text().lstrip().startswith(tuple("IVXL")):
            fail(m["file"], "a later part does not open on a sub-section numeral")


def check_file(m):
    f = m["file"]
    src = (BOOK / "chapters" / f).read_text()
    out_p = BOOK / "modern_chapters" / f
    if not out_p.exists():
        return False
    out = out_p.read_text()
    lines = out.split("\n")
    # 1 heading
    if lines[0].strip() != m["title"]:
        fail(f, f"line 1 is {lines[0]!r}, expected {m['title']!r}")
    body_start = 1
    if m["of"] > 1:
        want = f"(Part {m['part']} of {m['of']})"
        if len(lines) < 2 or lines[1].strip() != want:
            fail(f, f"line 2 should be {want!r}")
        body_start = 2
    body = "\n".join(lines[body_start:])
    if assemble.PART_MARK.search(body) or re.search(r"^\(Part \d+ of \d+\)$", body, re.M):
        fail(f, "a part marker below the heading")
    # 2 sub-sections
    secs = [l.strip() for l in body.split("\n") if ROMAN.match(l.strip())]
    if secs != m["sections"]:
        fail(f, f"sub-sections {secs} != {m['sections']}")
    # 3 refrain
    a = len(re.findall(r"Also sprach Zarathustra", src))
    b = len(re.findall(r"Thus spoke Zarathustra", out))
    if a != b:
        fail(f, f"'Thus spoke Zarathustra' {b}x, German 'Also sprach Zarathustra' {a}x")
    # 4 verse
    vs, vo = verse_blocks(src), verse_blocks(out)
    if vs != vo:
        fail(f, f"{vo} verse blocks, German has {vs}")
    # 5 emphasis
    es, eo = len(EMPH.findall(src)), len(EMPH.findall(out))
    if es != eo:
        fail(f, f"{eo} emphasis spans, German has {es}")
    if out.count("*") % 2:
        fail(f, "odd number of asterisks")
    # 6 archaism
    hits = [w for w in ARCH.findall(out)]
    hits += [w for w in ETH.findall(out) if w.lower() not in ETH_OK]
    if hits:
        fail(f, f"archaisms {sorted(set(h.lower() for h in hits))}")
    # 7 locked terms
    for h in set(BANNED.findall(out)):
        fail(f, f"banned term {h!r}")
    # 8 renderability
    for p in paras(body):
        s = p.strip()
        if p.startswith("\t") or ROMAN.match(s) or s == DISCOURSES:
            continue
        if assemble.is_subheading(s):
            fail(f, f"renders as a heading: {s!r}")
    if f == "000.txt" and paras(body)[-1].strip() != DISCOURSES:
        fail(f, f"000 must close on the line {DISCOURSES!r}")
    # 9 house form
    if "--" in out:
        fail(f, "double hyphen")
    for l in lines:
        s = l.strip()
        if len(s) > 3 and s.isupper() and not ROMAN.match(s):
            fail(f, f"ALL-CAPS line {s!r}")
        if assemble.PART_LINE.match(s):
            fail(f, f"Part-divider line {s!r} (it would be deleted)")
    if "_" in out or "[" in out or "]" in out:
        fail(f, "underscore or square bracket in the text")
    # 10 ratio
    r = len(body.split()) / max(1, len(src.split()))
    if not 0.95 <= r <= 1.45:
        fail(f, f"ratio {r:.2f} outside 0.95-1.45")
    elif not 1.02 <= r <= 1.32:
        warn(f, f"ratio {r:.2f} outside the expected 1.02-1.32")
    print(f"{f} ratio {r:.2f}  {m['title']}")
    return True


def main():
    manifest = json.loads((BOOK / "manifest.json").read_text())
    structure(manifest)
    want = set(a if a.endswith(".txt") else f"{int(a):03d}.txt" for a in sys.argv[1:])
    done = 0
    for m in manifest:
        if want and m["file"] not in want:
            continue
        done += check_file(m)
    for l in warns + fails:
        print(l)
    print(f"{done} modern files checked; {len(fails)} failures, {len(warns)} warnings")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
