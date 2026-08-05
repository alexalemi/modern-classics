"""Turn the Standard Ebooks Pilgrim's Progress into chapters/ + manifest.json.

    python3 bunyan/prep.py

Source: standardebooks.org/ebooks/john-bunyan/the-pilgrims-progress, which
follows George Offor's 1855 edition of Bunyan's complete works. Fetch it
with `bash bunyan/fetch.sh` first; source/ is not kept in the repo.

THE STRUCTURAL PROBLEM. Bunyan wrote one continuous dream-narrative with no
chapters at all, and the SE edition faithfully preserves that: part-1.xhtml
is a single <section> holding 924 paragraphs and one heading. So the
division has to be imposed, and the honest way to impose it is to use
Bunyan's own scene transitions. He signals a new episode with a formula —
"Now I saw in my dream, that...", "I beheld, then, that...", "So I saw
that..." — which is exactly a chapter break in seventeenth-century dress.
Every boundary below sits on one of those, or on the arrival sentence of a
named place, and each is pinned by a distinctive substring rather than a
paragraph number so that the split survives a re-transcription upstream.
ANCHORS ARE ASSERTED: an anchor that matches zero paragraphs, or more than
one, stops the run. (Same refusal-to-guess as ball/prep.py.)

THE ENDNOTES. Offor's edition carries 1,010 notes by nineteenth-century
commentators — Burder, Scott, Mason and others — and at 500 KB the notes
file is larger than either part of the book. They are NOT translated. They
are Victorian devotional commentary on a seventeenth-century allegory,
attributed to men who are not Bunyan, and rendering them would roughly
double the volume of the work for material that is not the work. They go
to reference/notes.txt instead, as a crib, and the translation draws on
them only where a modern reader genuinely cannot follow without help —
sparingly, as bracketed notes, the way soap-bubbles/ handles obsolete
chemistry. Note 1 is the model of one worth keeping: "The Den" is Bedford
jail, where Bunyan wrote the book during twelve years' imprisonment for
preaching. A reader who does not know that misses the first sentence.

NOTEREFS MUST GO AS ELEMENTS, NOT AS TAGS. Strip the tags naively and
`<a epub:type="noteref">41</a>` leaves a bare 41 welded to the preceding
word — "the Slough of Despond,41 his labourers" — which reads as a number
in the text and would sail through every mechanical check this project
has. Kill the whole anchor before any tag stripping.
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

MAX_WORDS = 7000        # a translation agent must OUTPUT what it reads

# (anchor substring, paragraphs to back up by, title). The offset exists
# because a chapter occasionally wants the two short lines of arrival that
# come before its first quotable sentence.
PART1 = [
    ("As I walked through the wilderness of this world", 0,
     "The City of Destruction"),
    ("just as they had ended this talk, they drew near to a very miry slough", 0,
     "The Slough of Despond"),
    ("Now as Christian was walking solitarily by himself", 0,
     "Mr. Worldly-Wiseman"),
    ("At last there came a grave person to the gate, named Goodwill", 2,
     "The Wicket Gate"),
    ("Then he went on till he came at the house of the Interpreter", 0,
     "The House of the Interpreter"),
    ("Now I saw in my dream, that the highway up which Christian was to go", 0,
     "The Cross and the Sepulchre"),
    ("I beheld, then, that they all went on till they came to the foot of the Hill", 0,
     "The Hill Difficulty"),
    ("So I saw in my dream, that he made haste and went forward", 0,
     "The House Beautiful"),
    ("Then I saw in my dream, that, on the morrow, he got up to go forward", 0,
     "The Valley of Humiliation and Apollyon"),
    ("I saw then in my dream, that when Christian was got to the borders", 0,
     "The Valley of the Shadow of Death"),
    ("So I saw that Christian went on his way; yet, at the sight of the Old Man", 0,
     "Faithful"),
    ("Moreover, I saw in my dream, that as they went on, Faithful", 0,
     "Talkative"),
    ("Then I saw in my dream, that when they were got out of the wilderness", 0,
     "Vanity Fair"),
    ("Then a convenient time being appointed, they brought them forth to their trial", 0,
     "The Trial of Faithful"),
    ("Now I saw in my dream, that Christian went not forth alone", 0,
     "Hopeful, and Mr. By-ends"),
    ("Then I saw in my dream, that a little off the road, over against the silver mine", 0,
     "Demas, and the Pillar of Salt"),
    ("I saw, then, that they went on their way to a pleasant river", 0,
     "Doubting Castle and Giant Despair"),
    ("They went then till they came to the Delectable Mountains", 0,
     "The Delectable Mountains"),
    ("I saw then in my dream, that they went till they came into a certain country", 0,
     "The Enchanted Ground"),
    ("Now I saw in my dream, that by this time the Pilgrims were got over", 0,
     "The Land of Beulah and the River"),
]

PART2 = [
    ("Courteous Companions,", 1,          # back up over the epigraph
     "Christiana's Summons"),
    ("Christiana answered and said to the eldest of them, whose name was Mrs. Timorous", 0,
     "Mrs. Timorous and Mercy"),
    ("But when Christiana came up to the Slough of Despond", 0,
     "The Slough and the Gate"),
    ("Thus, now when they had talked away a little more time, they drew nigh to a house", 0,
     "The House of the Interpreter"),
    ("The Interpreter then called for a manservant of His, one Great-heart", 0,
     "Great-heart, and the Cross"),
    ("Thus they went on, till they came at the foot of the Hill Difficulty", 0,
     "The Hill Difficulty and the Lions"),
    ("Now, because it was somewhat late, and because the Pilgrims were weary", 0,
     "The House Beautiful Again"),
    ("Now they began to go down the hill into the Valley of Humiliation", 0,
     "The Valley of Humiliation"),
    ("Now I saw, that they went to the ascent that was a little way off", 0,
     "The Valley of the Shadow, and Old Honest"),
    ("It would be too tedious to tell you of all", 0,
     "Vanity Town"),
    ("Christiana then wished for an inn for herself and her children", 0,
     "The House of Gaius"),
    ("Well, said Gaius, now you are here", 0,
     "Mr. Feeble-mind and Mr. Ready-to-halt"),
    ("I saw now that they went on, till they came at the river", 0,
     "By-path Meadow Revisited"),
    ("Now I saw in my dream, when all these things were finished", 0,
     "The Fall of Doubting Castle"),
    ("By this time they were got to the Enchanted Ground", 0,
     "The Enchanted Ground"),
    ("Now, when they were almost at the end of this ground", 0,
     "Mr. Stand-fast and Madam Bubble"),
    ("After this, I beheld until they were come unto the Land of Beulah", 0,
     "The Land of Beulah"),
]


def load(name):
    """SE XHTML -> list of paragraphs, verse marked by a leading tab."""
    t = (SRC / f"{name}.xhtml").read_text()
    # The noteref anchors have to die as ELEMENTS. See the module docstring.
    t = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>.*?</a>', "", t, flags=re.S)
    t = re.sub(r"<a[^>]*epub:type=\"backlink\"[^>]*>.*?</a>", "", t, flags=re.S)
    body = re.search(r"<body[^>]*>(.*)</body>", t, re.S).group(1)

    out = []
    # Walk blockquotes and paragraphs in document order so verse keeps its
    # place. Verse is emitted indented, which assemble.py renders as <pre>.
    for m in re.finditer(r"<(blockquote|p)\b[^>]*>(.*?)</\1>", body, re.S):
        kind, inner = m.group(1), m.group(2)
        if kind == "blockquote":
            # A stanza is ONE <p> whose lines are divided by <br/>, not one
            # <p> per line. Split on the breaks or the whole stanza arrives
            # as a single run-on line with the source's own newlines still
            # in it, and only its first line gets indented.
            lines = []
            for stanza in re.findall(r"<p[^>]*>(.*?)</p>", inner, re.S):
                for ln in re.split(r"<br\s*/?>", stanza):
                    ln = clean(ln)
                    if ln:
                        lines.append(ln)
            if lines:
                out.append("\n".join("\t" + x for x in lines))
        else:
            # skip paragraphs already consumed inside a blockquote
            if any(m.start() > b.start() and m.end() < b.end()
                   for b in re.finditer(r"<blockquote\b.*?</blockquote>", body, re.S)):
                continue
            s = clean(inner)
            if s:
                out.append(s)
    return out


def clean(s):
    s = re.sub(r"<[^>]*>", "", s)
    s = html.unescape(s)
    # SE sets a no-break space inside abbreviations ("Mrs. Timorous")
    # and a narrow one before some punctuation. Both are typography, not
    # text: leave them in and every anchor written with an ordinary space
    # silently fails to match — which is how this book's chapter division
    # first came out empty.
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def resolve(paras, spec, label):
    """anchor -> paragraph index, asserting exactly one match."""
    text, back, title = spec
    hits = [i for i, p in enumerate(paras) if text in p]
    if len(hits) != 1:
        sys.exit(f"{label}: anchor matched {len(hits)} paragraphs, need 1\n"
                 f"  {text!r}")
    return max(0, hits[0] - back), title


def split_oversize(paras):
    """Cut a chapter into parts of at most MAX_WORDS on paragraph bounds."""
    total = sum(len(p.split()) for p in paras)
    if total <= MAX_WORDS:
        return [paras]
    n = -(-total // MAX_WORDS)
    target = total / n
    parts, cur, run = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and run + w / 2 > target and len(parts) < n - 1:
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    if cur:
        parts.append(cur)
    return parts


def main():
    if not SRC.exists():
        sys.exit("no bunyan/source — run `bash bunyan/fetch.sh` first")
    CHAPTERS.mkdir(exist_ok=True)
    REFERENCE.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()

    entries = []
    files = []

    # Front matter: Bunyan's verse apology only. SE's "foreword" is a list
    # of the commentators whose notes Offor selected — apparatus, not book.
    ap = load("preface-1")
    files.append(ap)
    entries.append({"title": "The Author's Apology for His Book"})

    for part, specs, divider in (("part-1", PART1, "Part One: Christian"),
                                 ("part-2", PART2, "Part Two: Christiana")):
        paras = load(part)
        if part == "part-2":
            files.append(load("preface-2"))
            entries.append({"title": "The Author's Way of Sending Forth His Second Part",
                            "part_before": divider})
            divider = None
        bounds = [resolve(paras, s, f"{part}[{i}]") for i, s in enumerate(specs)]
        for j, (start, title) in enumerate(bounds):
            end = bounds[j + 1][0] if j + 1 < len(bounds) else len(paras)
            body = paras[start:end]
            for k, chunk in enumerate(split_oversize(body)):
                e = {"title": title}
                if divider:
                    e["part_before"] = divider
                    divider = None
                files.append(chunk)
                entries.append(e)

    for i, (chunk, e) in enumerate(zip(files, entries)):
        (CHAPTERS / f"{i:03d}.txt").write_text("\n\n".join(chunk) + "\n")
        e["file"] = f"{i:03d}.txt"
        e["words"] = sum(len(p.split()) for p in chunk)

    # Group multi-part chapters back under one title for the manifest.
    manifest = []
    for e in entries:
        if manifest and manifest[-1]["title"] == e["title"] \
                and "part_before" not in e:
            manifest[-1]["files"].append(e["file"])
            manifest[-1]["words"] += e["words"]
        else:
            m = {"title": e["title"], "files": [e["file"]], "words": e["words"]}
            if "part_before" in e:
                m["part_before"] = e["part_before"]
            manifest.append(m)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    write_notes()

    total = sum(m["words"] for m in manifest)
    print(f"{len(files)} files, {len(manifest)} chapters, {total:,} words")
    for m in manifest:
        if m.get("part_before"):
            print(f"  -- {m['part_before']} --")
        n = f" ({len(m['files'])} parts)" if len(m["files"]) > 1 else ""
        print(f"  {m['files'][0]}  {m['words']:6,}w  {m['title']}{n}")


def write_notes():
    """Offor's commentator notes, as a crib. Not translated - see docstring."""
    t = (SRC / "endnotes.xhtml").read_text()
    t = re.sub(r'<a[^>]*epub:type="backlink"[^>]*>.*?</a>', "", t, flags=re.S)
    notes = re.findall(r'<li id="note-(\d+)">(.*?)</li>', t, re.S)
    lines = []
    for num, body in notes:
        lines.append(f"[{num}] {clean(body)}")
    REFERENCE.mkdir(exist_ok=True)
    (REFERENCE / "notes.txt").write_text("\n\n".join(lines) + "\n")
    print(f"reference/notes.txt: {len(notes)} commentator notes (crib only)")


if __name__ == "__main__":
    main()
