"""Diff a restored edition's chapters/ against an Archive.org scan's OCR.

    python3 scan_diff.py <book> <archive-id> [--start "first words"] [--all]
    python3 scan_diff.py <book> <id> --vote <id2> [--start ...]

--vote: report ONLY the differences where TWO scans agree with each other
and not with the edition -- the American Indian Stories method. Two OCRs
rarely make the same error, so what survives is the printing, not noise.

The witness that found Gutenberg's modernised spellings and dropped
passages in Zitkala-Ša and Calculus Made Easy. The OCR is fetched once
into <book>/_src/scan-<id>-djvu.txt. Both sides are reduced to lower-case
letter words (formulas and plate markers out, line-end hyphens joined),
aligned, and the differences that are only OCR noise are filtered:
line-split words, running heads (any run made of words from the book's
own section titles or the title), page numbers. What is left is printed
for READING -- it is a list to look at, never a list to apply.

  replace/delete  the edition's wording differs from the print
  INSERT n>8      the print has a run of words the edition lacks
"""
import difflib
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import mathml  # noqa: E402


def words(s):
    s = re.sub(r"[¬-]\s*\n\s*", "", s)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return [w.lower() for w in re.findall(r"[A-Za-z]+", s)]


def fetch(d, ident):
    cache = d / "_src" / f"scan-{ident}-djvu.txt"
    if not cache.exists():
        meta = urllib.request.urlopen(f"https://archive.org/metadata/{ident}", timeout=120).read().decode()
        name = re.search(r'"name":"([^"]+_djvu\.txt)"', meta).group(1)
        data = urllib.request.urlopen(urllib.request.Request(
            f"https://archive.org/download/{ident}/{urllib.request.quote(name)}",
            headers={"User-Agent": "modern-classics/1.0"}), timeout=300).read()
        cache.write_bytes(data)
    return cache.read_text(errors="replace")


def vote(book, id1, id2, start):
    d = ROOT / book
    text = ""
    for f in sorted((d / "chapters").glob("*.txt")):
        t = mathml.MATH.sub(" ", f.read_text())
        text += re.sub(r"\[Figure [^\]]*\]", " ", t) + "\n"
    ew = words(text)
    scans = []
    for ident in (id1, id2):
        s = fetch(d, ident)
        if start:
            # OCR sets two spaces between words and breaks lines anywhere
            m = re.search(r"\s+".join(map(re.escape, start.split())), s, re.I)
            assert m, f"start phrase not in {ident}"
            s = s[m.start():]
        scans.append(" ".join(words(s)))
    heads = set(words(" ".join(f.read_text().split("\n", 1)[0] for f in (d / "chapters").glob("*.txt"))))
    envt = (d / "env").read_text() if (d / "env").exists() else ""
    for key in ("ORIGINAL_WORK", "AUTHOR"):
        m = re.search(key + r"=(.*)", envt)
        if m:
            heads |= set(words(m.group(1)))
    out, found = [], []
    sm = difflib.SequenceMatcher(None, ew, scans[0].split(), autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        # an INSERT is a word the print has and the edition lacks -- a dropped
        # word, which reads perfectly ("the law always approaching" for "the
        # law is always approaching"). Short ones only; long runs are page
        # furniture and are the non-vote mode's business.
        if tag not in ("replace", "delete", "insert") or i2 - i1 > 6 or j2 - j1 > 6:
            continue
        if tag == "insert" and j2 - j1 > 3:
            continue
        if tag == "insert" and set(scans[0].split()[j1:j2]) <= heads:
            continue                                  # a running head
        a = scans[0].split()[j1:j2]
        if "".join(ew[i1:i2]) == "".join(a):
            continue
        L = " ".join(ew[max(0, i1 - 3):i1]); R = " ".join(ew[i2:i2 + 3])
        printed = " ".join(x for x in (L, " ".join(a), R) if x)
        edited = " ".join(x for x in (L, " ".join(ew[i1:i2]), R) if x)
        if printed in scans[1] and edited not in scans[1]:
            out.append(f"  ED '{' '.join(ew[i1:i2])}'  PRINT '{' '.join(a)}'   [{L} _ {R}]")
            found.append({"tag": tag, "left": L, "edition": " ".join(ew[i1:i2]), "print": " ".join(a), "right": R})
    if "--json" in sys.argv:
        (d / "_src" / "vote.json").write_text(json.dumps(found, indent=1))
    print(f"{book}: {len(out)} readings where {id1} and {id2} agree against the edition")
    print("\n".join(out))


def main(argv):
    if "--vote" in argv:
        st = argv[argv.index("--start") + 1] if "--start" in argv else None
        return vote(argv[1], argv[2], argv[argv.index("--vote") + 1], st)
    book, ident = argv[1], argv[2]
    start = argv[argv.index("--start") + 1] if "--start" in argv else None
    show_all = "--all" in argv
    d = ROOT / book
    cache = d / "_src" / f"scan-{ident}-djvu.txt"
    if not cache.exists():
        url = f"https://archive.org/download/{ident}/{ident}_djvu.txt"
        req = urllib.request.Request(url, headers={"User-Agent": "modern-classics/1.0"})
        data = urllib.request.urlopen(req, timeout=300).read()
        if len(data) < 5000:
            # the file may be named after the item's own file stem
            meta = urllib.request.urlopen(f"https://archive.org/metadata/{ident}", timeout=120).read().decode()
            name = re.search(r'"name":"([^"]+_djvu\.txt)"', meta).group(1)
            data = urllib.request.urlopen(urllib.request.Request(
                f"https://archive.org/download/{ident}/{urllib.request.quote(name)}",
                headers={"User-Agent": "modern-classics/1.0"}), timeout=300).read()
        cache.write_bytes(data)
    scan = cache.read_text(errors="replace")
    text = ""
    for f in sorted((d / "chapters").glob("*.txt")):
        t = f.read_text()
        t = mathml.MATH.sub(" ", t)
        t = re.sub(r"\[Figure [^\]]*\]", " ", t)
        text += t + "\n"
    ew = words(text)
    if start:
        i = scan.lower().find(start.lower())
        assert i >= 0, "start phrase not in the scan"
        scan = scan[i:]
    sw = words(scan)
    heads = set(words(" ".join(f.read_text().split("\n", 1)[0] for f in (d / "chapters").glob("*.txt"))))
    env = (d / "env").read_text()
    heads |= set(words(re.search(r"ORIGINAL_WORK=(.*)", env).group(1)))
    heads |= set(words(re.search(r"AUTHOR=(.*)", env).group(1)))
    sm = difflib.SequenceMatcher(None, ew, sw, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        E, S = ew[i1:i2], sw[j1:j2]
        if "".join(E) == "".join(S):
            continue
        Sn = [w for w in S if w not in heads]
        if "".join(E) == "".join(Sn):
            continue
        if tag == "insert" and (len(Sn) <= 8 and not show_all):
            continue
        ctx_e = " ".join(ew[max(0, i1 - 4):i2 + 3])
        ctx_s = " ".join(sw[max(0, j1 - 4):j2 + 3])
        big = (i2 - i1) > 4 or len(Sn) > 8
        out.append(("BIG " if big else "    ") + f"{tag:7} ED[{ctx_e[:120]}]  SCAN[{ctx_s[:160]}]")
    print(f"{book} vs {ident}: {len(ew):,} edition words, {len(sw):,} scan words, "
          f"ratio {sm.ratio():.3f}, {len(out)} residual differences")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
