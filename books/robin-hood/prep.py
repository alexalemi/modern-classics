"""Build chapters/ + manifest.json for Howard Pyle's The Merry Adventures of
Robin Hood (1883) from the Project Gutenberg plain text (#10148).

    python3 books/robin-hood/prep.py            # chapters/ + manifest.json
    python3 books/robin-hood/prep.py --captions # fill [Figure id] markers in
                                                # modern_chapters/ from
                                                # captions.tsv

THE TEXT. Gutenberg #10148 and #964 are the same transcription to within
four words (diffed 2026-10-12); #10148 is used. Both follow a later
Scribner resetting with the chapters run on from I to XXI, and BOTH LOST
PYLE'S STRUCTURE: the 1883 first edition is a Prologue, eight Parts
("Part First" ... "Part Eighth") of two or three chapters each, and an
Epilogue, and each Part opens with Pyle's own italic summary ("In which it
is told how..."). #10148 keeps only the Part First summary (with the typo
"Robing Hood"); #964 keeps none. The eight summaries and the Epilogue's are
restored below from the 1883 scan (archive.org merryadventureso00pylerich,
University of California copy), transcribed by hand from its OCR and
checked against the page images. PART_SUMMARY is that transcription.

NOT CARRIED: the 1883 page margins carry running side-notes ("Robin Hood
meets the Tinker"); the Gutenberg text has none and they duplicate the
narrative. The table of contents and list of illustrations are dropped
(the manifest is the contents).

FOOTNOTES. Pyle wrote three (Gutenberg numbers them [1], [3], [4]; there
was never a [2]). Each is cut loose from its anchor and set as its own
"Footnote: ..." paragraph directly after the paragraph that cites it; the
translation folds them into the sentence.

PLATES. Pyle drew all of them. The 1883 list of illustrations names a
frontispiece, 22 full-page plates, a head-piece and a tail-piece for the
Preface, a lettered head-piece for the Prologue, each Part and the
Epilogue, and a tail-piece for the Prologue, Parts I and III-VIII, and the
book (Part II has none). That is 44 of the 49 the 1883 list names (the other five decorate the
fly-leaf, title page, contents and list of illustrations, none reproduced), fetched and cropped from the
1883 scan by plates.py into site/images/robin-hood/fig{id}.jpg. The
small unlisted chapter-end ornaments are not carried. Ids are WORDS, not
numbers, on purpose: Pyle never numbered a plate, and an id with no digit
gets no "Figure N" label from assemble.figure_label (the frontispiece is
"front", which renders as "Frontispiece"). Full-page plates are placed at
the moment of the story they show (the 1883 binding often put them pages
away, facing a Part opening); head-pieces open their Part, tail-pieces
close it. Every anchor is a substring that must match exactly one
paragraph of its chapter, or the run stops.
"""

import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "source.txt"
CHAPTERS = BOOK / "chapters"
MODERN = BOOK / "modern_chapters"
CAPTIONS = BOOK / "captions.tsv"

MAX_WORDS = 6200   # split anything longer into two parts

# (source heading in #10148, modern heading, part_before or None)
CHAPTER_LIST = [
    ("How Robin Hood Came to Be an Outlaw",
     "Prologue: How Robin Hood Became an Outlaw", None),
    ("Robin Hood and the Tinker",
     "Chapter 1: Robin Hood and the Tinker",
     "Part One: The Sheriff Tries Three Times"),
    ("The Shooting Match at Nottingham Town",
     "Chapter 2: The Shooting Match at Nottingham Town", None),
    ("Will Stutely Rescued by His Companions",
     "Chapter 3: Will Stutely Is Rescued by His Friends", None),
    ("Robin Hood Turns Butcher",
     "Chapter 4: Robin Hood Turns Butcher",
     "Part Two: Robin the Butcher, and Little John at the Sheriff's"),
    ("Little John Goes to Nottingham Fair",
     "Chapter 5: Little John Goes to Nottingham Fair", None),
    ("How Little John Lived at the Sheriff's",
     "Chapter 6: How Little John Lived at the Sheriff's House", None),
    ("Little John and the Tanner of Blyth",
     "Chapter 7: Little John and the Tanner of Blyth",
     "Part Three: Sore Bones and Three New Men"),
    ("Robin Hood and Will Scarlet",
     "Chapter 8: Robin Hood and Will Scarlet", None),
    ("The Adventure with Midge the Miller's Son",
     "Chapter 9: The Adventure with Midge, the Miller's Son", None),
    ("Robin Hood and Allan a Dale",
     "Chapter 10: Robin Hood and Allan a Dale",
     "Part Four: Allan a Dale, the Curtal Friar, and a Wedding"),
    ("Robin Hood Seeks the Curtal Friar",
     "Chapter 11: Robin Hood Goes Looking for the Curtal Friar", None),
    ("Robin Hood Compasses a Marriage",
     "Chapter 12: Robin Hood Arranges a Wedding", None),
    ("Robin Hood Aids a Sorrowful Knight",
     "Chapter 13: Robin Hood Helps a Sorrowful Knight",
     "Part Five: The Sorrowful Knight"),
    ("How Sir Richard of the Lea Paid His Debts",
     "Chapter 14: How Sir Richard of the Lea Paid His Debts", None),
    ("Little John Turns Barefoot Friar",
     "Chapter 15: Little John Turns Barefoot Friar",
     "Part Six: A Beggar and a Barefoot Friar"),
    ("Robin Hood Turns Beggar",
     "Chapter 16: Robin Hood Turns Beggar", None),
    ("Robin Hood Shoots Before Queen Eleanor",
     "Chapter 17: Robin Hood Shoots Before Queen Eleanor",
     "Part Seven: Robin Hood and the Queen"),
    ("The Chase of Robin Hood",
     "Chapter 18: The Chase of Robin Hood", None),
    ("Robin Hood and Guy of Gisbourne",
     "Chapter 19: Robin Hood and Guy of Gisbourne",
     "Part Eight: Guy of Gisbourne and King Richard"),
    ("King Richard Comes to Sherwood Forest",
     "Chapter 20: King Richard Comes to Sherwood Forest", None),
    ("Epilogue", "Epilogue", None),
]

# Pyle's own summaries, keyed by the source heading of the chapter that opens
# the Part. Transcribed from the 1883 scan (see docstring); spelling as
# printed ("befel").
PART_SUMMARY = {
    "How Robin Hood Came to Be an Outlaw":
        "Giving an account of Robin Hood and his adventure with the King's "
        "foresters. Also telling how his band gathered around him; and of the "
        "merry adventure that gained him his good right-hand man, the famous "
        "Little John.",
    "Robin Hood and the Tinker":
        "Telling how the Sheriff of Nottingham swore that he would deal dole "
        "to Robin Hood. Also, how he made three trials thereat, but missed "
        "each time by a good bow's length.",
    "Robin Hood Turns Butcher":
        "In which shall be told how Robin Hood turned Butcher, and how he "
        "revenged himself upon the Sheriff. Also, of the famous adventures "
        "that befel Little John at the Nottingham Archery Match, and how he "
        "entered the Sheriff's service.",
    "Little John and the Tanner of Blyth":
        "Recounting three merry adventures that befel Robin Hood and certain "
        "others, by which he gained sore bones and three good merry men, all "
        "in one day.",
    "Robin Hood and Allan a Dale":
        "In which it is told how Allan a Dale was brought to Robin Hood, who "
        "promised to help him in trouble. Also how Robin sought the curtal "
        "Friar of Fountain Abbey with that aim in view. Likewise it is "
        "recounted how Robin Hood brought two true lovers together that "
        "would else have been made unhappy all their lives.",
    "Robin Hood Aids a Sorrowful Knight":
        "In which it is told how that Robin Hood met a sorrowful knight, and "
        "brought him to Sherwood. Also, how the Bishop of Hereford was more "
        "generous than he desired to be. Likewise it is told how Sir Richard "
        "of the Lea paid his debts in due season, both to the Prior of Emmet "
        "and to Robin Hood.",
    "Little John Turns Barefoot Friar":
        "In which it is told how that Robin Hood and Little John turned, the "
        "one a beggar and the other a strolling Friar, and went forth to seek "
        "adventures. Likewise it is told how Little John prayed to some "
        "purpose, and how Robin Hood drubbed four beggars and outwitted a "
        "corn engrosser.",
    "Robin Hood Shoots Before Queen Eleanor":
        "In which it is told how Queen Eleanor sent for Robin Hood to come to "
        "the Court at famous London Town, and how Robin Hood came at her "
        "bidding. Likewise, it is told how King Henry chased Robin through "
        "the land, yet caught him not.",
    "Robin Hood and Guy of Gisbourne":
        "In which it is told how Robin Hood met Guy of Gisbourne in Sherwood "
        "Forest, and of the famous fight betwixt them. Also, how Little John "
        "fell into the Sheriff's hands through saving the life of three men. "
        "Likewise, it is told how good King Richard of the Lion's Heart came "
        "to Nottinghamshire and visited Robin Hood in Sherwood Forest.",
    "Epilogue":
        "Telling how Robin Hood came back again to Sherwood Forest, and how "
        "Sir William Dale was sent against him to take him. Likewise it is "
        "told how Robin Hood died by the treachery of his cousin, the "
        "Prioress of the Nunnery of Kirklees.",
}

# Plates: (id, source heading, anchor substring, "before"|"after"|"start"|"end")
# "start" = right after the heading/summary; "end" = after the last paragraph.
PLATES = [
    ("front", "PREFACE", None, "start"),
    ("headpreface", "PREFACE", None, "start"),
    ("tailpreface", "PREFACE", None, "end"),
    ("headprologue", "How Robin Hood Came to Be an Outlaw", None, "start"),
    ("bridge", "How Robin Hood Came to Be an Outlaw",
     "Never did the Knights of Arthur's Round Table meet", "after"),
    ("tailprologue", "How Robin Hood Came to Be an Outlaw", None, "end"),
    ("headone", "Robin Hood and the Tinker", None, "start"),
    ("tinker", "Robin Hood and the Tinker",
     "No sweeter inn could be found", "after"),
    ("kinglondon", "The Shooting Match at Nottingham Town",
     "In London King Henry and his fair Queen Eleanor", "after"),
    ("palmer", "Will Stutely Rescued by His Companions",
     "Now, out upon thee, young man,\" cried the Palmer", "before"),
    ("tailone", "Will Stutely Rescued by His Companions", None, "end"),
    ("headtwo", "Robin Hood Turns Butcher", None, "start"),
    ("butcher", "Robin Hood Turns Butcher",
     "Then all began to stare and wonder and crowd around", "before"),
    ("eric", "Little John Goes to Nottingham Fair",
     "At first Eric o' Lincoln thought", "after"),
    ("cook", "How Little John Lived at the Sheriff's",
     "Then they both stepped forth into the broad passage", "after"),
    ("headthree", "Little John and the Tanner of Blyth", None, "start"),
    ("bland", "Little John and the Tanner of Blyth", "@BLAND", "after"),
    ("scarlet", "Robin Hood and Will Scarlet", "@SCARLET", "after"),
    ("miller", "The Adventure with Midge the Miller's Son", "@MILLER", "after"),
    ("tailthree", "The Adventure with Midge the Miller's Son", None, "end"),
    ("headfour", "Robin Hood and Allan a Dale", None, "start"),
    ("fountain", "Robin Hood and Allan a Dale", "@FOUNTAIN", "before"),
    ("friarsong", "Robin Hood Seeks the Curtal Friar", "@FRIARSONG", "before"),
    ("bride", "Robin Hood Compasses a Marriage", "@BRIDE", "after"),
    ("tailfour", "Robin Hood Compasses a Marriage", None, "end"),
    ("headfive", "Robin Hood Aids a Sorrowful Knight", None, "start"),
    ("knight", "Robin Hood Aids a Sorrowful Knight", "@KNIGHT", "before"),
    ("prior", "How Sir Richard of the Lea Paid His Debts", "@PRIOR", "after"),
    ("tailfive", "How Sir Richard of the Lea Paid His Debts", None, "end"),
    ("headsix", "Little John Turns Barefoot Friar", None, "start"),
    ("lasses", "Little John Turns Barefoot Friar", "@LASSES", "after"),
    ("engrosser", "Robin Hood Turns Beggar", "@ENGROSSER", "after"),
    ("tailsix", "Robin Hood Turns Beggar", None, "end"),
    ("headseven", "Robin Hood Shoots Before Queen Eleanor", None, "start"),
    ("queen", "Robin Hood Shoots Before Queen Eleanor", "@QUEEN", "after"),
    ("escape", "The Chase of Robin Hood", "@ESCAPE", "after"),
    ("tailseven", "The Chase of Robin Hood", None, "end"),
    ("headeight", "Robin Hood and Guy of Gisbourne", None, "start"),
    ("gisbourne", "Robin Hood and Guy of Gisbourne", "@GISBOURNE", "after"),
    ("bargain", "King Richard Comes to Sherwood Forest", "@BARGAIN", "after"),
    ("taileight", "King Richard Comes to Sherwood Forest", None, "end"),
    ("headepilogue", "Epilogue", None, "start"),
    ("lastshaft", "Epilogue", "@LASTSHAFT", "after"),
    ("finis", "Epilogue", None, "end"),
]

ANCHORS = {     # "@NAME" -> substring of the paragraph the plate follows
    "@BLAND": "So, without more ado, each gripped his staff in the middle",
    "@SCARLET": "Wherefore should I hold, good fellow?",
    "@MILLER": "So they stood, all with their heads close together",
    "@FOUNTAIN": "that liest there killing all the green",
    "@FRIARSONG": "Then, singing first with a voice deep and gruff",
    "@BRIDE": "Let me look upon this lass",
    "@KNIGHT": "who dost stop a traveler in this manner",
    "@PRIOR": "I would crave thy mercy",
    "@LASSES": "Surely, it is a pity that such fair lasses",
    "@ENGROSSER": "merry Robin stepped straightway forth, in all his rags",
    "@QUEEN": "Thus Allan sang, and as he sang",
    "@ESCAPE": "But of all this Robin knew not a whit",
    "@GISBOURNE": "Then Robin Hood wiped his sword",
    "@BARGAIN": "Thereupon he rolled up his sleeve",
    "@LASTSHAFT": "drawing the bowstring to his ear",
}


def body_text():
    t = SRC.read_text()
    t = t[t.index("*** START"):t.index("*** END")]
    t = t.split("\n", 1)[1]
    return t.replace("\r", "")


def paragraphs(block):
    """Unwrap prose; keep indented verse lines as they are."""
    out = []
    for p in re.split(r"\n\s*\n", block):
        if not p.strip():
            continue
        lines = p.split("\n")
        m = re.match(r"\s+\[(\d)\]\s*(.*)", p, re.S)
        if m:   # one of Pyle's footnotes
            out.append("Footnote: " + " ".join(m.group(2).split()))
            continue
        if any(re.match(r"\s", l) for l in lines if l.strip()):
            out.append("\n".join("    " + l.strip() for l in lines if l.strip()))
        else:
            out.append(" ".join(l.strip() for l in lines if l.strip()))
    return out


def anchor_index(pars, needle, where):
    hits = [i for i, p in enumerate(pars) if needle in " ".join(p.split())]
    if len(hits) != 1:
        sys.exit(f"anchor {needle!r} ({where}) matched {len(hits)} paragraphs")
    return hits[0]


def build():
    t = body_text()
    lines = t.split("\n")
    # locate headings
    def find(h, start=0):
        c = [i for i, l in enumerate(lines) if l.strip().lower() == h.lower()
             and i >= start]
        if not c:
            sys.exit(f"heading {h!r} not found")
        return c[0]
    pre = find("PREFACE")
    contents = find("CONTENTS")
    starts = []
    pos = contents + 30
    for src, _, _ in CHAPTER_LIST:
        i = find(src, pos)
        starts.append(i)
        pos = i + 1
    starts.append(len(lines))

    sections = [("PREFACE", "Preface: From the Author to the Reader", None,
                 paragraphs("\n".join(lines[pre + 3:contents])))]
    for k, (src, modern, pb) in enumerate(CHAPTER_LIST):
        block = "\n".join(lines[starts[k] + 1:starts[k + 1]])
        pars = paragraphs(block)
        # drop the Prologue/Part headings and summaries that trail the
        # previous chapter in #10148 (PROLOGUE..., PART FIRST + summary)
        nxt = CHAPTER_LIST[k + 1][0] if k + 1 < len(CHAPTER_LIST) else None
        # #10148 welds the two lines into one paragraph: "PART FIRST Telling..."
        while pars and pars[-1].startswith("PART FIRST"):
            pars.pop()
        sections.append((src, modern, pb, pars))
    # the Prologue heading + summary sit before "How Robin Hood Came..."
    # (between CONTENTS and the first heading) and are replaced by ours.

    # "THUS END the Merry Adventures..." and the two paragraphs after it
    # close Part Eighth in the 1883 edition (an italic page of its own
    # between the Part VIII tail-piece and the Epilogue); #10148 sets them
    # under the Epilogue heading. They go back to the end of chapter 20,
    # AFTER its tail-piece, marked "@CODA" for the plate pass below.
    src, modern, pb, pars = sections[-1]
    k = anchor_index(pars, "And now, dear friend, you who have journeyed", "coda")
    coda, sections[-1] = pars[:k], (src, modern, pb, pars[k:])
    assert coda[0].startswith("THUS END"), coda[0][:40]

    # footnotes: move each "Footnote:" right after the paragraph citing it
    fixed = []
    for src, modern, pb, pars in sections:
        pars = [re.sub(r"\[\d\]", "", p) for p in pars]
        fixed.append((src, modern, pb, pars))
    sections = fixed

    # plates
    plate_map = {}
    for pid, src, anchor, where in PLATES:
        plate_map.setdefault(src, []).append((pid, anchor, where))
    out = []
    for src, modern, pb, pars in sections:
        starts_, ends_, inserts = [], [], {}
        for pid, anchor, where in plate_map.get(src, []):
            if where == "start":
                starts_.append(pid)
            elif where == "end":
                ends_.append(pid)
            else:
                needle = ANCHORS.get(anchor, anchor)
                if needle.startswith("@"):
                    sys.exit(f"anchor {anchor} for {pid} not set")
                i = anchor_index(pars, needle, pid)
                key = i if where == "after" else i - 1
                inserts.setdefault(key, []).append(pid)
        body = []
        for i, p in enumerate(pars):
            body.append(p)
            for pid in inserts.get(i, []):
                body.append(f"[Figure {pid}]")
        for pid in inserts.get(-1, []):
            body.insert(0, f"[Figure {pid}]")
        # 1883 order: head-piece, PART title, summary (italic), chapter
        front = [f"[Figure {pid}]" for pid in starts_]
        if src in PART_SUMMARY:
            front.append("_" + PART_SUMMARY[src] + "_")
        body = front + body + [f"[Figure {pid}]" for pid in ends_]
        if src == CHAPTER_LIST[-2][0]:
            body += coda
        out.append((src, modern, pb, body))
    return out


def words(pars):
    return sum(len(p.split()) for p in pars if not p.startswith("[Figure"))


def split_point(pars):
    total = words(pars)
    acc, best, bestd = 0, None, None
    for i, p in enumerate(pars[:-1]):
        acc += len(p.split())
        nxt = pars[i + 1]
        # never cut before verse, a footnote or a plate, or after an
        # introducing colon
        if nxt.startswith(("    ", "Footnote:", "[Figure")) or p.rstrip().endswith(":"):
            continue
        d = abs(acc - total / 2)
        if bestd is None or d < bestd:
            best, bestd = i + 1, d
    return best


def write():
    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()
    manifest = []
    n = 0
    for src, modern, pb, pars in build():
        pieces = [pars]
        if words(pars) > MAX_WORDS:
            k = split_point(pars)
            pieces = [pars[:k], pars[k:]]
        for j, piece in enumerate(pieces, 1):
            name = f"{n:03d}.txt"
            head = src if src != "PREFACE" else "PREFACE: From the Author to the Reader"
            text = head + "\n\n"
            if len(pieces) > 1:
                text += f"(Part {j} of {len(pieces)})\n\n"
            text += "\n\n".join(piece) + "\n"
            (CHAPTERS / name).write_text(text)
            e = {"file": name, "title": modern, "part": j, "of": len(pieces),
                 "words": words(piece)}
            if pb and j == 1:
                e["part_before"] = pb
            manifest.append(e)
            n += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{n} files, {sum(e['words'] for e in manifest)} words")
    for e in manifest:
        print(e["file"], e["words"], f"{e['part']}/{e['of']}", e["title"])


FIG = re.compile(r"\[Figure ([A-Za-z0-9_]+)(?::[^\]]*)?\]")


def captions():
    caps = {}
    for line in CAPTIONS.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            pid, cap = line.split("\t", 1)
            if pid in caps:
                sys.exit(f"plate {pid} captioned twice")
            caps[pid] = cap.strip()
    seen = set()
    for f in sorted(MODERN.glob("*.txt")):
        t = f.read_text()
        def sub(m):
            pid = m.group(1)
            if pid not in caps:
                sys.exit(f"{f.name}: no caption for {pid}")
            seen.add(pid)
            return f"[Figure {pid}: {caps[pid]}]"
        new = FIG.sub(sub, t)
        if new != t:
            f.write_text(new)
    missing = set(caps) - seen
    if missing:
        print("captions not used:", sorted(missing))
    print(f"captioned {len(seen)} plates")


if __name__ == "__main__":
    if "--captions" in sys.argv:
        captions()
    else:
        write()
