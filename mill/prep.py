"""Standard Ebooks XHTML -> chapters/ + manifest.json for On Liberty.

PARSE THE SOURCE AS XML, NOT WITH REGEX (the epictetus rule; it is where
tyndall's four-fold Spenser stanza and bunyan's welded noteref digits
came from), and then CHECK THE PARSE AGAINST A SECOND, INDEPENDENT
READING of the raw file that shares no code with it. Two readings that
agree are evidence; one reading is a hope.

WHAT IS IN THE BOOK AND WHAT IS NOT:
  - The DEDICATION to Harriet Taylor Mill is Mill's and stays. CLAUDE.md
    requires this decision to be explicit: dedications belong in the
    book, tables of contents do not.
  - The EPIGRAPH from Humboldt is Mill's, and is the book's thesis in
    one sentence. It stays, as its own short section, as Standard
    Ebooks sets it.
  - introduction.xhtml is a later editor's biographical essay, NOT
    Mill. It is dropped from the book and kept under reference/ as a
    crib, on the bunyan precedent for Offor's commentary.
  - The endnotes split cleanly with it: notes 1-5 are that editor's
    citations to his own essay, and go with it; notes 6-14 are MILL'S
    OWN FOOTNOTES and are inlined, each as a "Footnote: ..." paragraph
    directly after the paragraph that cites it (the candle pattern).
    Four of the nine are substantial -- note 6 is the 1858 Press
    Prosecutions footnote he added rather than change a word of his
    text, and it is part of the argument.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"
REF = BOOK / "reference"
X = "{http://www.w3.org/1999/xhtml}"
EPUB = "{http://www.idpf.org/2007/ops}type"

MAXW = 7000                      # an agent must OUTPUT as much as it reads

# WORD-FORM NUMBERS, DELIBERATELY. assemble.CHAP_LINE matches only
# "Chapter <digits>: Title" and sets those as h3 INSIDE a Part divider.
# This book has no Parts, so digits would nest the five chapters under
# nothing and leave the Epigraph and Dedication looking more important
# than they are. Word form keeps every section at one level and the
# contents flat, which is what hume/ does with "Section One: ...", and
# word form is this project's cross-reference house style anyway.
TITLES = {
    1: "Chapter One: Introductory",
    2: "Chapter Two: On the Liberty of Thought and Discussion",
    3: "Chapter Three: On Individuality, as One of the Elements of Well-Being",
    4: "Chapter Four: On the Limits of Society's Authority over the Individual",
    5: "Chapter Five: Applications",
}
# Mill's own; notes 1-5 belong to the dropped editorial introduction.
MILL_NOTES = set(range(6, 15))


def clean(s):
    """NO-BREAK SPACES ARE INVISIBLE AND BREAK EVERY ANCHOR (bunyan).
    Standard Ebooks sets one inside abbreviations and around dashes, so
    a string written with an ordinary space matches nothing at all."""
    return (s.replace(" ", " ").replace(" ", " ")
             .replace("⁠", "").replace("⁡", ""))


def text_of(el):
    """All text under el, with <em>/<i> carried through as *emphasis*.

    Mill italicises both the words he stresses and the titles he cites,
    and both are <em>/<i> here; assemble.inline renders either as the
    same <em>, which is what Standard Ebooks does and is right.
    """
    out = []
    tag = el.tag.split("}")[-1]
    emph = tag in ("em", "i")
    if emph:
        out.append("*")
    out.append(el.text or "")
    for kid in el:
        out.append(text_of(kid))
    if emph:
        # the marker may not enclose a space or assemble.EMPH refuses it
        inner = "".join(out[1:]).strip()
        out = ["*" + inner + "*"] if inner else [""]
    out.append(el.tail or "")
    return "".join(out)


def kill_noterefs(root):
    """Delete noteref anchors AS ELEMENTS, giving each tail to its
    PREDECESSOR and not to the parent's last child.

    Strip the tags naively instead and "<a>7</a>" welds a bare 7 onto
    the preceding word -- which reads as a number in the text and passes
    every mechanical check in this project (bunyan). Getting the tail's
    destination wrong relocates a clause to the end of any paragraph
    carrying two notes, and reads almost plausibly (epictetus).
    """
    seen = []
    for parent in list(root.iter()):
        prev = None                  # last child STILL IN THE TREE
        for kid in list(parent):
            if kid.tag == f"{X}a" and "noteref" in (kid.get(EPUB) or ""):
                n = int(re.search(r"\d+", kid.get("href") or
                                  kid.get("id") or "0").group())
                seen.append((parent, n))
                # THE PREDECESSOR MUST BE ONE THAT SURVIVES. Taking the
                # previous element of the ORIGINAL child list hands the
                # tail to an anchor that was itself just removed, and the
                # text is silently lost -- which is what happened to the
                # Old Bailey jurymen, where notes 7, 8 and 9 sit in one
                # paragraph: note 8's tail went onto detached note 7 and
                # half a sentence disappeared.
                tail = kid.tail or ""
                if prev is None:
                    parent.text = (parent.text or "") + tail
                else:
                    prev.tail = (prev.tail or "") + tail
                parent.remove(kid)
            else:
                prev = kid
    return seen


def paragraphs(path):
    """[(text, note_numbers)] for one source file, in document order."""
    root = ET.parse(path).getroot()
    owner = dict()
    for parent, n in kill_noterefs(root):
        owner.setdefault(id(parent), []).append(n)
    out = []
    body = root.find(f"{X}body")
    for el in body.iter():
        tag = el.tag.split("}")[-1]
        if tag == "hr":
            out.append(("* * *", []))
        # <cite> is a sibling of <p> inside the epigraph's blockquote,
        # not a child of it, so a p-only walk drops the attribution --
        # and the attribution is who is being quoted.
        if tag not in ("p", "cite"):
            continue
        if (el.get(EPUB) or "") == "title":       # heading, handled apart
            continue
        s = re.sub(r"\s+", " ", clean(text_of(el))).strip()
        if s:
            out.append((s, owner.get(id(el), [])))
    return out


def notes():
    root = ET.parse(SRC / "endnotes.xhtml").getroot()
    out = {}
    for li in root.iter(f"{X}li"):
        m = re.search(r"\d+", li.get("id") or "")
        if not m:
            continue
        for a in list(li.iter(f"{X}a")):
            if "backlink" in (a.get(EPUB) or ""):
                for p in li.iter():
                    if a in list(p):
                        p.remove(a)
                        break
        s = re.sub(r"\s+", " ", clean(text_of(li))).strip().rstrip("↩").strip()
        out[int(m.group())] = s
    return out


def split_parts(pars, maxw):
    """Cut a chapter into <= maxw-word parts at paragraph boundaries."""
    total = sum(len(p.split()) for p in pars)
    k = max(1, -(-total // maxw))
    target = total / k
    parts, cur, run = [], [], 0
    for p in pars:
        w = len(p.split())
        if cur and run + w / 2 > target and len(parts) < k - 1:
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    parts.append(cur)
    return parts


def main():
    OUT.mkdir(exist_ok=True)
    REF.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    note = notes()
    assert set(note) == set(range(1, 15)), sorted(note)

    # the editor's essay, kept as a crib and not as part of the book
    intro = [t for t, _ in paragraphs(SRC / "introduction.xhtml")]
    (REF / "introduction.txt").write_text("\n\n".join(intro) + "\n")

    manifest, idx = [], 0

    def emit(title, body, part=1, of=1):
        nonlocal idx
        name = f"{idx:03d}.txt"
        (OUT / name).write_text(title + "\n\n" + body.rstrip() + "\n")
        manifest.append({"file": name, "title": title, "part": part,
                         "of": of, "words": len(body.split())})
        idx += 1

    # one tab-indented block: quotation, then who said it. No word is
    # added, so the cross-check below still compares like with like.
    ep = [t for t, _ in paragraphs(SRC / "epigraph.xhtml")]
    assert len(ep) == 2 and "Humboldt" in ep[1], ep
    emit("Epigraph", "\n".join("\t" + l for l in ep))

    ded = [t for t, _ in paragraphs(SRC / "dedication.xhtml")]
    assert ded and "beloved and deplored" in ded[0], ded[:1]
    emit("Dedication", "\n\n".join(ded))

    used = set()
    for c in range(1, 6):
        pars = []
        for text, ns in paragraphs(SRC / f"chapter-{c}.xhtml"):
            pars.append(text)
            for n in sorted(ns):
                assert n in MILL_NOTES, f"editor's note {n} in chapter {c}"
                used.add(n)
                pars.append("Footnote: " + note[n])
        parts = split_parts(pars, MAXW)
        title = TITLES[c]
        for i, part in enumerate(parts, 1):
            emit(title, "\n\n".join(part), i, len(parts))

    assert used == MILL_NOTES, sorted(MILL_NOTES - used)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # -- SECOND, INDEPENDENT READING. Shares no code with the parser.
    want = []
    for f in ["epigraph", "dedication"] + [f"chapter-{c}" for c in range(1, 6)]:
        raw = (SRC / f"{f}.xhtml").read_text()
        raw = re.sub(r"<head>.*?</head>", " ", raw, flags=re.S)
        raw = re.sub(r"<hgroup>.*?</hgroup>", " ", raw, flags=re.S)
        raw = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>.*?</a>', " ", raw,
                     flags=re.S)
        want += re.sub(r"\s+", " ", clean(re.sub(r"<[^>]+>", " ", raw))).split()
    # THE FOOTNOTES ARE COMPARED SEPARATELY. The raw reading has them at
    # the back of the book, where the source keeps them, and the parser
    # has moved them inline; excluding them from both sides keeps the
    # ordering check on the body, which is what is at risk. Placement is
    # the one thing no cheap check can see -- a correctly formatted note
    # on the wrong sentence passes everything (candle) -- so the four
    # substantial notes were also read in context.
    got = []
    for m in manifest:
        lines = (OUT / m["file"]).read_text().split("\n")
        body = "\n".join(lines[1:])
        keep = [p for p in re.split(r"\n\s*\n", body)
                if not p.strip().startswith("Footnote: ")]
        got += " ".join(keep).split()
    for n in sorted(MILL_NOTES):
        hits = sum((OUT / m["file"]).read_text().count("Footnote: " + note[n])
                   for m in manifest)
        assert hits == 1, f"note {n} appears {hits} times inline"
    # COMPARE CHARACTERS, NOT TOKENS. The independent reading replaces
    # every tag with a space, so "<i>odium theologicum</i>," tokenises
    # as "theologicum" + "," where the parser gives "theologicum," --
    # a difference in the CHECK, not in the text. Dropping whitespace
    # and the emphasis markers compares exactly what is left: the
    # letters, in order.
    squash = lambda ws: re.sub(r"\s+", "", " ".join(ws)).replace("*", "")
    a, b = squash(want), squash(got)
    if a != b:
        i = next(k for k in range(min(len(a), len(b))) if a[k] != b[k])
        raise SystemExit(f"diverges at char {i}:\n"
                         f"  source ...{a[max(0,i-60):i+60]}\n"
                         f"  output ...{b[max(0,i-60):i+60]}")
    print(f"cross-check: {len(a):,} characters match, in order")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words; "
          f"largest {max(m['words'] for m in manifest):,}")
    print(f"{sum(1 for m in manifest if m['of'] > 1)} files are chapter parts")


if __name__ == "__main__":
    main()
