"""Mechanical checks for herodotus/ that verify.py cannot make.

    python3 herodotus/check.py            # source + whatever modern files exist
    python3 herodotus/check.py --strict   # NAMES warnings fail too

SOURCE (always):
  STRUCTURE   51 files, chapter numbers 1..N in order, titles unique, no
              title matching assemble.PART_LINE, a word-form "Book N: Muse"
              divider on the first file of each Book and nowhere else.
  SECTIONS    every Macaulay section of every Book is in exactly one file,
              in order, from 1 to the Book's last: the book's own numbering
              is the contents list the pipeline did not produce. The one
              known exception is VII.35, unnumbered in both witnesses (run
              on into VII.34).
  SEAMS       no file opens or closes mid-sentence.
  SIZE        no file over 7,200 words (agent output limit).
  WITNESS     each Book's word total within 0.5% of the Gutenberg-derived
              herodotus.txt with its note-reference numbers removed.

MODERN (for each modern_chapters/NNN.txt that exists):
  HEADING     line 1 is the manifest title exactly; line 2 blank.
  DIVIDER     no "Book One: ..." / "Part ..." line and no "(Part n of k)".
  SECTIONS    the paragraph-initial section numbers ("43. ") are exactly the
              source file's, in the same order. This is what catches a
              dropped section outright; the ratio only catches it in bulk.
  MARKUP      no asterisks or underscores, no curly quotes, no ALL-CAPS line.
  NAMES       (warning) proper names in the source file with no counterpart
              in the modern file, matched on a consonant skeleton through the
              locked name map, so Mardonios = Mardonius, Plataia = Plataea,
              Hellenes = Greeks. This is the check that would have caught the
              v1 army catalogue (35 commanders in Macaulay, 9 in the modern).
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

BOOK = Path(__file__).resolve().parent
MAX_WORDS = 7200
PART_LINE = re.compile(r"^Part [IVXLC0-9]+: \S")
DIVIDER = re.compile(r"^(Book (One|Two|Three|Four|Five|Six|Seven|Eight|Nine)|Part \S+):")
PART_MARK = re.compile(r"^\(Part \d+ of \d+\)$", re.I)
SECNUM = re.compile(r"^(\d+)\. ", re.M)
MUSES = ["Clio", "Euterpe", "Thalia", "Melpomene", "Terpsichore", "Erato",
         "Polymnia", "Urania", "Calliope"]
WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
LAST = {1: 216, 2: 182, 3: 160, 4: 205, 5: 126, 6: 140, 7: 239, 8: 144, 9: 122}
UNNUMBERED = {(7, 35)}

# Macaulay's name -> the modern words that count as its rendering, where the
# skeleton match cannot see it. Keys are lower-case Macaulay forms.
NAME_MAP = {
    "hellenes": ["greek"], "hellene": ["greek"], "hellenic": ["greek"],
    "hellas": ["greece", "greek"], "barbarians": ["non-greek", "foreign",
    "persian", "barbarian", "invader", "enemy", "king"], "barbarian":
    ["non-greek", "foreign", "persian", "barbarian", "invader", "enemy", "king"],
    "lacedaemonians": ["spartan", "lacedaemonian", "laconia"],
    "lacedaemonian": ["spartan", "lacedaemonian", "laconia"],
    "lacedaemon": ["sparta", "laconia", "lacedaemon"],
    "spartiates": ["spartan", "spartiate"],
    "egina": ["aegina"], "eginetans": ["aegina"],
    "ister": ["danube"], "borysthenes": ["dnieper"], "tanais": ["don"],
    "tyras": ["dniester"], "pontus": ["black sea"], "euxine": ["black sea"],
    "erythraean": ["indian ocean", "persian gulf", "southern"],
    "magians": ["magi", "magus"], "magian": ["magi", "magus"],
    "pythian": ["pythia", "delphi"],
    "ilion": ["troy"], "ilium": ["troy"],
    "athene": ["athena"], "phenicians": ["phoenician"],
    "heracleidai": ["heraclid"], "alcmaionidai": ["alcmaeonid"],
    "olympos": ["olympus"], "olympia": ["olympia", "olympic"],
    "arabian": ["arabia", "red sea"],
    "necos": ["necho"],
}


def deaccent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def skeleton(word):
    w = deaccent(word.lower()).replace("k", "c").replace("ph", "f")
    return w[0] + re.sub(r"[aeiouyh\-’']", "", w[1:])


def names(text):
    """Capitalised tokens that never occur in lower case anywhere in the
    whole source (so "Now", "Oracle", "State", "North" drop out)."""
    toks = re.findall(r"[A-Za-zÀ-ÿ’]+", text)
    return {t.rstrip("’") for t in toks if t[0].isupper() and len(t) > 2}


def main():
    strict = "--strict" in sys.argv
    manifest = json.loads((BOOK / "manifest.json").read_text())
    fails, warns = [], []
    src = {m["file"]: (BOOK / "chapters" / m["file"]).read_text() for m in manifest}
    lower = {t for txt in src.values() for t in re.findall(r"\b[a-zà-ÿ’]+", txt)}

    # STRUCTURE
    if len(manifest) != 51:
        fails.append(f"STRUCTURE: {len(manifest)} files, expected 51")
    titles = [m["title"] for m in manifest]
    if len(set(titles)) != len(titles):
        fails.append("STRUCTURE: duplicate titles")
    seen_books = []
    for i, m in enumerate(manifest, 1):
        if m["file"] != f"{i:03d}.txt" or not m["title"].startswith(f"Chapter {i}: "):
            fails.append(f"STRUCTURE: {m['file']} numbered wrong: {m['title']}")
        if PART_LINE.match(m["title"]) or (m["part"], m["of"]) != (1, 1):
            fails.append(f"STRUCTURE: {m['file']} title/part")
        b = m["book"]
        if b not in seen_books:
            seen_books.append(b)
            want = f"Book {WORDS[b - 1]}: {MUSES[b - 1]}"
            if m.get("part_before") != want:
                fails.append(f"STRUCTURE: {m['file']} part_before {m.get('part_before')!r} != {want!r}")
        elif "part_before" in m:
            fails.append(f"STRUCTURE: {m['file']} has a second Book divider")
    if seen_books != list(range(1, 10)):
        fails.append(f"STRUCTURE: books {seen_books}")

    # SECTIONS, SEAMS, SIZE
    per_book = {b: [] for b in range(1, 10)}
    for m in manifest:
        txt = src[m["file"]]
        per_book[m["book"]] += [int(x) for x in SECNUM.findall(txt)]
        n = len(txt.split())
        if n > MAX_WORDS:
            fails.append(f"SIZE: {m['file']} {n} words")
        first = txt.lstrip()
        lead = re.sub(r"^\d+\. ", "", first)
        if not lead[:1].isupper():
            fails.append(f"SEAMS: {m['file']} opens mid-sentence: {first[:60]!r}")
        if txt.rstrip()[-1] not in ".!?”’:":
            fails.append(f"SEAMS: {m['file']} ends mid-sentence: {txt.rstrip()[-60:]!r}")
    for b, got in per_book.items():
        want = [n for n in range(1, LAST[b] + 1) if (b, n) not in UNNUMBERED]
        if got != want:
            miss = sorted(set(want) - set(got))
            extra = sorted(set(got) - set(want))
            dup = sorted({n for n in got if got.count(n) > 1})
            fails.append(f"SECTIONS: Book {b} missing {miss} extra {extra} dup {dup}"
                         + ("" if miss or extra or dup else " (order)"))

    # WITNESS
    wit = BOOK / "herodotus.txt"
    if wit.exists():
        parts = re.split(r"^BOOK [IVX]+\..*$", wit.read_text(), flags=re.M)[1:]
        for b, p in enumerate(parts, 1):
            w = len([t for t in p.split() if not t.isdigit()])
            s = sum(len(src[m["file"]].split()) for m in manifest if m["book"] == b)
            if abs(w - s) / w > 0.005:
                fails.append(f"WITNESS: Book {b} SE {s} vs Gutenberg {w}")

    # MODERN
    modern_dir = BOOK / "modern_chapters"
    done = 0
    for m in manifest:
        p = modern_dir / m["file"]
        if not p.exists():
            continue
        done += 1
        f = m["file"]
        txt = p.read_text()
        lines = txt.split("\n")
        if lines[0] != m["title"]:
            fails.append(f"HEADING: {f} line 1 {lines[0]!r} != {m['title']!r}")
        if len(lines) < 2 or lines[1].strip():
            fails.append(f"HEADING: {f} line 2 not blank")
        for ln in lines[1:]:
            s = ln.strip()
            if DIVIDER.match(s) or PART_MARK.match(s):
                fails.append(f"DIVIDER: {f}: {s[:60]!r}")
            if len(s) > 3 and s.isupper():
                fails.append(f"MARKUP: {f} all-caps line {s[:40]!r}")
        if re.search(r"[*_]", txt):
            fails.append(f"MARKUP: {f} asterisk or underscore")
        if re.search("[“”‘’]", txt):
            fails.append(f"MARKUP: {f} curly quotes")
        want = [int(x) for x in SECNUM.findall(src[f])]
        got = [int(x) for x in SECNUM.findall(txt)]
        if got != want:
            miss = sorted(set(want) - set(got))
            extra = sorted(set(got) - set(want))
            fails.append(f"SECTIONS: {f} modern section numbers differ: missing {miss} extra {extra}"
                         + ("" if miss or extra else " (order/duplicate)"))
        # NAMES
        mod_low = deaccent(txt.lower())
        mod_skel = {skeleton(t) for t in re.findall(r"[A-Za-zÀ-ÿ]+", txt) if len(t) > 2}
        missing = []
        for name in sorted(names(src[f])):
            if name.lower() in lower:
                continue
            key = deaccent(name.lower())
            if key in NAME_MAP and any(x in mod_low for x in NAME_MAP[key]):
                continue
            sk = skeleton(name)
            stem = sk[:max(3, len(sk) - 2)]
            if any(ms.startswith(stem) or sk.startswith(ms) and len(ms) >= 4 for ms in mod_skel):
                continue
            missing.append(name)
        if missing:
            warns.append(f"NAMES: {f} {len(missing)} source names not found: {', '.join(missing)}")

    for w in warns:
        print("WARN ", w)
    for x in fails:
        print("FAIL ", x)
    total = sum(len(t.split()) for t in src.values())
    print(f"{len(manifest)} source files, {total} words; {done} modern files checked; "
          f"{len(fails)} failures, {len(warns)} warnings")
    sys.exit(1 if fails or (strict and warns) else 0)


if __name__ == "__main__":
    main()
