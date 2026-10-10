"""Turn the Standard Ebooks Le Morte d'Arthur into chapters/ + manifest.json.

    bash malory/fetch.sh          # once; source/ is not kept in the repo
    python3 malory/prep.py

Source: standardebooks.org/ebooks/thomas-malory/le-morte-darthur, which is
A. W. Pollard's 1900 text (Caxton's 1485 edition in modernised spelling,
gaps supplied from Wynkyn de Worde), transcribed from Gutenberg #1251/#1252.

STRUCTURE. Caxton divided Malory's book into 21 Books and chaptered every
one, and wrote a one-sentence rubric for each chapter. SE keeps all of it:
one XHTML file per Caxton chapter (504 of them), the rubric as the
chapter's bridgehead. We keep Caxton's division EXACTLY, one file per
chapter, because his chapters are short (median ~600 words, max 1,404) and
his rubrics are the book's own table of contents. So:

  000.txt          Caxton's Preface (part of the book since 1485)
  001.txt-504.txt  Book I ch. 1 ... Book XXI ch. 13, in order

No chapter exceeds MAX_WORDS, so there are no split parts at all, and
"of" is 1 on every manifest entry (asserted). Each Book opens with a
"part_before" divider in WORD form ("Book Seven: ..."), never Roman: see the
PART_LINE trap in CLAUDE.md (that one matches "Part", but the house rule is
word form for every divider).

HEADINGS come from titles.json, never from the source and never from an
agent: "chapters" maps "B-C" to the exact modern heading, "Chapter C:
<modernised Caxton rubric>", which assemble.CHAP_LINE recognises and sets
as an <h3> inside its Book. The manifest keeps Caxton's rubric alongside
("caxton") so the original-text build and check.py can see both. EVERY
TITLE LIVES IN titles.json; write it there, re-run prep, never hand-edit
manifest.json.

THE SOURCE FILE OPENS ON CAXTON'S RUBRIC as its first paragraph, the
quixote convention: it is part of what the translator renders (as the
heading line), it balances the heading line in verify.py's word ratio, and
the --original build shows it as the chapter's own summary.

THE APPARATUS IS NOT TRANSLATED. SE carries 305 endnotes (single-use word
glosses, plus Pollard's textual notes on Caxton's misnumbering and de
Worde's readings) and a 379-word glossary. They go to reference/ as a crib:
reference/notes.txt lists each note against the FILE it occurs in and the
words just before its anchor, so an agent can find the glosses for its
chapter with one grep. Pollard's bibliographical note (1900) is dropped:
it is an editor's apparatus, and its identification of Malory (the
Papworth will) has since been superseded.

NOTEREFS DIE AS ELEMENTS, NOT TAGS (the bunyan rule): stripping the tags
naively welds the note number onto the preceding word ("deceivable178").
NO-BREAK SPACES AND WORD JOINERS are normalised (the bunyan rule: SE sets
\\u00a0 inside abbreviations and \\u2060 before its em dashes).
"""

import html
import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
REFERENCE = BOOK / "reference"
TITLES = BOOK / "titles.json"

MAX_WORDS = 7000        # a translation agent must OUTPUT what it reads
NOTEREF = re.compile(r'<a[^>]*epub:type="noteref"[^>]*>(\d+)</a>')


def clean(s):
    s = re.sub(r"<[^>]*>", "", s)
    s = html.unescape(s)
    for ch in (" ", " ", " "):
        s = s.replace(ch, " ")
    s = s.replace("⁠", "")
    return re.sub(r"\s+", " ", s).strip()


def paragraphs(name):
    """SE XHTML -> (rubric, [paragraphs]), noterefs removed as elements.

    Also returns the note numbers in order with the text that precedes
    each anchor, for reference/notes.txt."""
    t = (SRC / name).read_text()
    body = re.search(r"<body[^>]*>(.*)</body>", t, re.S).group(1)
    rubric = None
    m = re.search(r'<p epub:type="se:bridgehead">(.*?)</p>', body, re.S)
    notes = []
    if m:
        # the rubric carries noterefs too ("leman's70", "mass-penny.262")
        for nm in NOTEREF.finditer(m.group(1)):
            notes.append((int(nm.group(1)), "(rubric) " + " ".join(
                clean(NOTEREF.sub("", m.group(1)[:nm.start()])).split()[-6:])))
        rubric = clean(NOTEREF.sub("", m.group(1)))
        body = body.replace(m.group(0), "")
    body = re.sub(r"<h\d[^>]*>.*?</h\d>", "", body, flags=re.S)

    paras = []
    for pm in re.finditer(r"<p\b[^>]*>(.*?)</p>", body, re.S):
        inner = pm.group(1)
        for nm in NOTEREF.finditer(inner):
            before = clean(NOTEREF.sub("", inner[:nm.start()]))
            notes.append((int(nm.group(1)), " ".join(before.split()[-6:])))
        s = clean(NOTEREF.sub("", inner))
        if s:
            paras.append(s)
    return rubric, paras, notes


def load_notes():
    t = (SRC / "endnotes.xhtml").read_text()
    t = re.sub(r'<a[^>]*epub:type="backlink"[^>]*>.*?</a>', "", t, flags=re.S)
    return {int(n): clean(b) for n, b in
            re.findall(r'<li id="note-(\d+)"[^>]*>(.*?)</li>', t, re.S)}


def write_glossary():
    t = (SRC / "glossary.xhtml").read_text()
    pairs = re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", t, re.S)
    lines = [f"{clean(a)}: {clean(b)}" for a, b in pairs]
    (REFERENCE / "glossary.txt").write_text(
        "# Standard Ebooks' glossary of obsolete words in Pollard's text.\n"
        "# A CRIB, not a mapping: several entries are false friends whose\n"
        "# right modern word depends on context (see text_analysis.txt).\n\n"
        + "\n".join(lines) + "\n")
    return len(lines)


def main():
    if not SRC.exists():
        sys.exit("no malory/source - run `bash malory/fetch.sh` first")
    if not TITLES.exists():
        sys.exit("no malory/titles.json")
    titles = json.loads(TITLES.read_text())
    CHAPTERS.mkdir(exist_ok=True)
    REFERENCE.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()

    manifest, notes_out = [], []
    all_notes = load_notes()

    # 000: Caxton's preface
    _, paras, notes = paragraphs("preface-of-william-caxton.xhtml")
    files = [("000.txt", paras, {"title": titles["front"]["preface"]}, notes)]

    n = 1
    for b in range(1, 22):
        c = 1
        while (SRC / f"chapter-{b}-{c}.xhtml").exists():
            rubric, paras, notes = paragraphs(f"chapter-{b}-{c}.xhtml")
            if not rubric:
                sys.exit(f"chapter-{b}-{c}: no rubric")
            key = f"{b}-{c}"
            title = titles["chapters"].get(key)
            if not title:
                sys.exit(f"titles.json: no heading for {key}")
            if not re.fullmatch(rf"Chapter {c}: \S.*[^.\s]", title):
                sys.exit(f"titles.json {key}: bad heading {title!r}")
            e = {"title": title, "book": b, "chapter": key, "caxton": rubric}
            if c == 1:
                e["part_before"] = titles["books"][str(b)]
            files.append((f"{n:03d}.txt", [rubric] + paras, e, notes))
            n += 1
            c += 1

    for fn, paras, e, notes in files:
        (CHAPTERS / fn).write_text("\n\n".join(paras) + "\n")
        words = sum(len(p.split()) for p in paras)
        if words > MAX_WORDS:
            sys.exit(f"{fn}: {words} words - needs a part split")
        m = {"file": fn, "title": e["title"], "part": 1, "of": 1,
             "words": words}
        for k in ("part_before", "book", "chapter", "caxton"):
            if k in e:
                m[k] = e[k]
        manifest.append(m)
        for num, ctx in notes:
            notes_out.append(f"{fn[:3]} [{num}] ...{ctx} | {all_notes[num]}")

    extra = set(titles["chapters"]) - {m["chapter"] for m in manifest
                                       if "chapter" in m}
    if extra:
        sys.exit(f"titles.json has headings for no chapter: {sorted(extra)}")

    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    (REFERENCE / "notes.txt").write_text(
        "# SE/Pollard endnotes, by FILE. Format: NNN [note] ...words before\n"
        "# the anchor | gloss. A crib for the translator: never translate\n"
        "# these, never add a note. Pollard's textual notes (Caxton's\n"
        "# misnumbering, de Worde readings) are information, not text.\n\n"
        + "\n".join(notes_out) + "\n")
    g = write_glossary()

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words; "
          f"{len(notes_out)} notes, {g} glossary entries -> reference/")
    for m in manifest:
        if m.get("part_before"):
            print(f"  -- {m['part_before']} --")
    print(f"  largest file: {max(m['words'] for m in manifest)} words")


if __name__ == "__main__":
    main()
