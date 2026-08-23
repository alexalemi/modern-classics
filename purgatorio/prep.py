"""Gutenberg #998 (the Italian Purgatorio) -> chapters/ + manifest.json,
with Longfellow's 1867 English as a per-canto crib under reference/.

THE SECOND BOOK OF THE COMEDY, and inferno/prep.py is its parent: read
that file first. Everything there about the form applies here unchanged
-- verse stays verse, the tercets stay tercets in the same number and
order, the line count per canto is exact, and there is NO RHYME, because
English cannot carry terza rima without padding and padding is the one
thing this poem must not suffer. Say so in the front matter rather than
implying a fidelity the edition does not have.

THREE THINGS ARE DIFFERENT FROM THE INFERNO, and each is a small trap:

  1 THE LINE-COUNT TABLE IS DERIVED-THEN-PINNED, NOT WRITTEN OUT. In
    inferno/ the table came from outside the file, which is the grimm
    rule (a source compared only against itself agrees with itself). I
    do not have a canto-by-canto count of the Purgatorio I trust from
    memory -- my recollection differed from the file at canto VIII --
    and A TABLE WRITTEN FROM A SHAKY MEMORY IS WORSE THAN NO TABLE,
    because it would either fire on correct text or, worse, pin a wrong
    number that some later re-run quietly satisfies. So the table below
    was READ OFF THIS FILE ONCE and is pinned here as a regression
    guard, and the load-bearing checks are the two that do come from
    outside it: the crib, which is a second text parsed by different
    code, must agree canto for canto, and the TOTAL must be 4,755 lines
    in 33 cantos, which is a fact about the poem and not about any file.

  2 THE CRIB'S SECTION IDS ARE "purgatorio-canto-N", and the Standard
    Ebooks file for this cantica carries a fourth kind of paragraph the
    Inferno's did not (see below). The two Inferno traps are still live
    and still guarded: take only spans that are DIRECT CHILDREN of a
    <p>, so the canto's own <h3> does not contribute two lines at the
    top, and skip any <p> typed bridgehead, so Longfellow's one-line
    argument does not enter the crib as line 1. Either one slides the
    whole canto out of register without dropping a word.

  3 THE ITALIAN IS NOT ONLY ITALIAN. Canto XXVI ends with eight lines of
    Provençal (Arnaut Daniel answering in his own language, "Tan m'abellis
    vostre cortes deman"), and they are Dante's, in Dante's tercets, and
    ride through untouched like any other line. The translation keeps
    them in Provençal and glosses them in the next tercet's English, the
    way Dante's own readers were expected to cope.

WHAT IS NOT IN THE BOOK, as in inferno/: Longfellow's prefatory sonnets
are his own poem about translating Dante and are dropped, and his
endnotes are nineteenth-century citation of earlier commentators and are
not carried at all.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "_pg998.txt"
OUT = BOOK / "chapters"
REF = BOOK / "reference"

WORD = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen "
        "Twenty Twenty-One Twenty-Two Twenty-Three Twenty-Four Twenty-Five "
        "Twenty-Six Twenty-Seven Twenty-Eight Twenty-Nine Thirty Thirty-One "
        "Thirty-Two Thirty-Three").split()

HEAD = re.compile(r"\nPurgatorio\nCanto ([IVXL]+)\n")

# Read off the source once and pinned (see the docstring). The witnesses
# that are independent of this file are the crib and the two totals.
LINES = [136, 133, 145, 139, 136, 151, 136, 139, 145, 139, 142, 136,
         154, 151, 145, 145, 139, 145, 145, 151, 136, 154, 133, 154,
         139, 148, 142, 148, 154, 145, 145, 160, 145]
TOTAL_LINES = 4755
CANTOS = 33


def strip_gutenberg(text):
    return text[text.index("*** START"):text.index("*** END")]


def cantos(body):
    """(number, [tercet, ...]) for each canto, a tercet being a list of lines."""
    ms = list(HEAD.finditer(body))
    if len(ms) != CANTOS:
        raise SystemExit(f"found {len(ms)} canto headings, expected {CANTOS}")
    out = []
    for k, m in enumerate(ms):
        end = ms[k + 1].start() if k + 1 < len(ms) else len(body)
        seg = body[m.end():end].strip("\n")
        blocks = [[l.strip() for l in b.split("\n") if l.strip()]
                  for b in re.split(r"\n\s*\n", seg) if b.strip()]
        out.append((k + 1, blocks))
    return out


def clean(s):
    """Standard Ebooks sets a no-break space inside abbreviations, and an
    ordinary-space anchor then matches nothing (the bunyan trap)."""
    return (s.replace(" ", " ").replace(" ", " ")
             .replace("﻿", ""))


def kill_noterefs(root):
    """Remove <a epub:type="noteref"> AS ELEMENTS, giving each removed
    anchor's tail to the nearest preceding sibling THAT STILL EXISTS --
    not to the parent's last child, and not to an already-detached
    sibling (epictetus/ and mill/ shipped both bugs; each relocates a
    clause without dropping a single word)."""
    for parent in root.iter():
        keep = []
        for kid in list(parent):
            if kid.get("{http://www.idpf.org/2007/ops}type") == "noteref":
                tail = kid.tail or ""
                if keep:
                    keep[-1].tail = (keep[-1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
                parent.remove(kid)
            else:
                keep.append(kid)


NS = "{http://www.w3.org/1999/xhtml}"
EPUB = "{http://www.idpf.org/2007/ops}"


def longfellow(path):
    """The crib, canto by canto: 33 lists of English lines.

    Parsed AS XML (the epictetus rule) -- a regex over this markup is how
    tyndall/ got the same stanza four times."""
    root = ET.fromstring(clean(path.read_text()))
    kill_noterefs(root)
    out = []
    for sec in root.iter(NS + "section"):
        sid = sec.get("id", "")
        if not re.fullmatch(r"purgatorio-canto-\d+", sid):
            continue
        argument, lines = [], []
        for para in sec.iter(NS + "p"):
            if "bridgehead" in (para.get(EPUB + "type") or ""):
                argument.append("".join(para.itertext()).strip())
                continue
            for span in para:
                if span.tag != NS + "span":
                    continue
                txt = "".join(span.itertext()).strip()
                if txt:
                    lines.append(re.sub(r"\s+", " ", txt))
        out.append((int(sid.rsplit("-", 1)[1]), lines, argument))
    out.sort()
    if [n for n, _, _ in out] != list(range(1, CANTOS + 1)):
        raise SystemExit(f"crib cantos are {[n for n, _, _ in out]}")
    return [(ls, arg) for _, ls, arg in out]


def main():
    body = strip_gutenberg(SRC.read_text())
    cs = cantos(body)
    crib = longfellow(REF / "_longfellow_purgatorio.xhtml")

    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    manifest, total = [], 0
    for (n, tercets), (eng, argument) in zip(cs, crib):
        lines = [l for t in tercets for l in t]
        if len(lines) != LINES[n - 1]:
            raise SystemExit(f"canto {n}: {len(lines)} lines, "
                             f"expected {LINES[n - 1]}")
        # THE SECOND WITNESS: a different text, read by different code.
        if len(eng) != LINES[n - 1]:
            raise SystemExit(f"canto {n}: crib has {len(eng)} lines, "
                             f"expected {LINES[n - 1]}")
        shape = [len(t) for t in tercets]
        if shape[-1] != 1 or set(shape[:-1]) != {3}:
            raise SystemExit(f"canto {n}: tercet shape {shape}")

        title = f"Canto {WORD[n - 1]}"
        text = "\n\n".join("\n".join("\t" + l for l in t) for t in tercets)
        fn = f"{n - 1:03d}.txt"
        (OUT / fn).write_text(f"{title}\n\n{text}\n")

        rows = []
        for i in range(0, len(eng), 3):
            rows.append(f"[{i + 1}]\n" + "\n".join(eng[i:i + 3]))
        head = f"{title} (Longfellow)\n"
        if argument:
            head += f"\nArgument (Longfellow's, not Dante's): {argument[0]}\n"
        (REF / fn).write_text(head + "\n" + "\n\n".join(rows) + "\n")

        words = len(" ".join(lines).split())
        total += words
        manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                         "chapter": True, "words": words})

    if sum(LINES) != TOTAL_LINES:
        raise SystemExit(f"table sums to {sum(LINES)}, not {TOTAL_LINES}")
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{CANTOS} cantos, {sum(LINES)} lines, {total} Italian words; "
          f"largest {max(m['words'] for m in manifest)}")


if __name__ == "__main__":
    main()
