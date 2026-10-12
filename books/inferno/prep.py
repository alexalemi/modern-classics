"""Gutenberg #997 (the Italian Inferno) -> chapters/ + manifest.json,
with Longfellow's 1867 English as a per-canto crib under reference/.

FROM THE ITALIAN, the ovid/de-officiis pattern: chapters/ holds Dante's
own text and reference/ holds a public-domain English translation
aligned to it canto by canto. Unlike sun-tzu/, this book does not have
to modernise somebody else's English.

WHY LONGFELLOW IS THE CRIB AND NOT THE SOURCE. He is line-for-line
faithful, which is exactly what a crib is for -- his English line N is
Dante's line N, so a translator can check a rendering against the Italian
without counting. He is also, by this project's own measure, the most
archaic English in the collection's screening pass after Pusey's
Augustine (28.7 archaisms per 1,000 words), and he keeps Italian word
order in English, which is why he is unreadable and why nobody should
be asked to read him. Crib, not source.

THE VERSE DECISION, and it is the whole book. Dante wrote terza rima --
interlocking triple rhyme, aba bcb cdc -- and it cannot be reproduced in
English without inventing words to reach the rhyme, because English has
perhaps a third of Italian's rhyming vocabulary. Every English poet who
has tried has padded, and padding a poem that is famous for compression
is the one thing that must not happen here. So:
  - VERSE STAYS VERSE. Turning a canto into a paragraph is this book's
    silent summarisation, exactly as with boethius/'s thirty-nine poems.
  - THE TERCETS STAY TERCETS, in the same number and the same order, so
    that a reader can follow a citation (Inf. V.121 is the 41st tercet
    of Canto Five) and so that check.py can compare the shape exactly.
  - THE LINE COUNT PER CANTO IS EXACT. Canto One is 136 lines, Canto
    Five 142, Canto Thirty-Four 139, and those are facts about the poem,
    not about any translation of it.
  - NO RHYME. This is the boethius reasoning turned around: there the
    rhyme was the TRANSLATOR'S addition and went, here the rhyme is
    Dante's own and still cannot come across -- so what is kept is the
    thing the rhyme was carrying, which is the tercet's shape and its
    forward momentum. Say so in the front matter rather than implying a
    fidelity the edition does not have.

WHAT IS NOT IN THE BOOK. Longfellow's six prefatory sonnets are HIS, a
poem about translating Dante, and are not Dante's; they are dropped.
His endnotes run to 1.8 MB -- larger than the poem several times over,
and mostly nineteenth-century citation of earlier commentators -- and go
to reference/ as a crib on the bunyan (Offor) precedent, to be drawn on
only where a modern reader genuinely cannot follow.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "_pg997.txt"
OUT = BOOK / "chapters"
REF = BOOK / "reference"

WORD = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen "
        "Twenty Twenty-One Twenty-Two Twenty-Three Twenty-Four Twenty-Five "
        "Twenty-Six Twenty-Seven Twenty-Eight Twenty-Nine Thirty Thirty-One "
        "Thirty-Two Thirty-Three Thirty-Four").split()

HEAD = re.compile(r"\nInferno\nCanto ([IVXL]+)\n")

# The canonical line count of every canto of the Inferno. Written out
# rather than derived, because it is the one description of the poem
# that does not come from the file being checked -- the grimm lesson:
# a source compared only against itself agrees with itself.
LINES = [136, 142, 136, 151, 142, 115, 130, 130, 133, 136, 115, 139,
         151, 142, 124, 136, 136, 136, 133, 130, 139, 151, 148, 151,
         151, 142, 136, 142, 139, 148, 145, 139, 157, 139]


def strip_gutenberg(text):
    return text[text.index("*** START"):text.index("*** END")]


def cantos(body):
    """(number, [tercet, ...]) for each canto, a tercet being a list of lines."""
    ms = list(HEAD.finditer(body))
    if len(ms) != 34:
        raise SystemExit(f"found {len(ms)} canto headings, expected 34")
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
             .replace("’", "’"))


def kill_noterefs(root):
    """Remove <a epub:type="noteref"> AS ELEMENTS, giving each removed
    anchor's tail to the nearest preceding sibling THAT STILL EXISTS --
    not to the parent's last child, and not to an already-detached
    sibling. Both of those bugs have shipped from this project before
    (epictetus/ and mill/), and both relocate a clause without dropping
    a single word."""
    for parent in root.iter():
        kids = list(parent)
        keep = []
        for kid in kids:
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
    """The crib, canto by canto: 34 lists of English lines.

    SE sets each line as a <span> inside one <p> per stanza, separated by
    <br/>. Parse it AS XML (the epictetus rule) -- a regex over this
    markup is how tyndall/ got the same stanza four times."""
    root = ET.fromstring(clean(path.read_text()))
    kill_noterefs(root)
    out = []
    for sec in root.iter(NS + "section"):
        sid = sec.get("id", "")
        if not re.fullmatch(r"inferno-canto-\d+", sid):
            continue
        # ONLY THE SPANS THAT ARE DIRECT CHILDREN OF A <p>. The canto's
        # own <h3> sets "Canto" and "I" as spans of their own, so a
        # recursive sweep returns 138 lines for a 136-line canto -- and
        # the two extra ones are at the TOP, which would slide the whole
        # crib two lines out of register against the Italian.
        argument = []
        # AND NOT THE BRIDGEHEAD. Longfellow heads each canto with his
        # own one-line argument, and canto three's names "Pope Celestine
        # V" with the numeral in a z3998:roman SPAN -- a bare "V" that
        # would have entered the crib as line 1 and slid all 136 lines of
        # canto three one out of register against the Italian. Nothing
        # downstream could see that: every line is present, in order, and
        # a translator checking line 121 would silently be reading 120.
        lines = []
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
    if [n for n, _, _ in out] != list(range(1, 35)):
        raise SystemExit(f"crib cantos are {[n for n, _, _ in out]}")
    return [(ls, arg) for _, ls, arg in out]


def main():
    body = strip_gutenberg(SRC.read_text())
    cs = cantos(body)
    crib = longfellow(REF / "_longfellow_inferno.xhtml")

    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    manifest, total = [], 0
    for (n, tercets), (eng, argument) in zip(cs, crib):
        lines = [l for t in tercets for l in t]
        # THE LINE COUNT IS A FACT ABOUT THE POEM. Assert it against the
        # written-out table AND against the crib, which is a second,
        # independent witness that shares no code with the parser.
        if len(lines) != LINES[n - 1]:
            raise SystemExit(f"canto {n}: {len(lines)} lines, "
                             f"expected {LINES[n - 1]}")
        if len(eng) != LINES[n - 1]:
            raise SystemExit(f"canto {n}: crib has {len(eng)} lines, "
                             f"expected {LINES[n - 1]}")
        # Every tercet is three lines except the last, which is one.
        shape = [len(t) for t in tercets]
        if shape[-1] != 1 or set(shape[:-1]) != {3}:
            raise SystemExit(f"canto {n}: tercet shape {shape}")

        title = f"Canto {WORD[n - 1]}"
        text = "\n\n".join("\n".join("\t" + l for l in t) for t in tercets)
        fn = f"{n - 1:03d}.txt"
        (OUT / fn).write_text(f"{title}\n\n{text}\n")
        # The crib is written tercet for tercet, with the line number of
        # each tercet's first line, so a translator can find Inf. V.121
        # without counting.
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

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"34 cantos, {sum(LINES)} lines, {total} Italian words; "
          f"largest {max(m['words'] for m in manifest)}")


if __name__ == "__main__":
    main()
