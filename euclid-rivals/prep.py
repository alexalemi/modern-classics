"""Turn the 1885 Archive.org scan of Euclid and His Modern Rivals into
chapters/ + manifest, with the Appendices as a crib in reference/.

    bash euclid-rivals/fetch.sh && python3 euclid-rivals/prep.py

Carroll's 1879 farce, revised 1885: Minos, a college examiner marking
papers at midnight, is visited by the ghost of Euclid and then by Herr
Niemand, the phantom of a German professor who speaks for each modern
geometry textbook in turn. Four Acts. It is very funny and almost nobody
has read it.

NOT ON GUTENBERG, so this is the thompson/ OCR path -- see
source_notes.txt for the full assessment, and abbyy.py and speakers.py for
the two modules this leans on.

WHY THIS WORKS FROM THE ABBYY XML AND NOT THE PLAIN TEXT

Archive also offers a djvu.txt, and it is a flat dump: no page boundaries,
no block types, and no record of which text was italic. This book is a
play, its stage directions and speaker tags are italic, and italic is what
the 1885 scan recognises worst ("a College dudy. Time, midvigJtf"). The
XML records italic per run, so the STRUCTURE survives even where the
CHARACTERS do not -- which is the only reason all 1,068 speaker tags could
be resolved (speakers.py).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from abbyy import pages, clean                            # noqa: E402
from speakers import resolve, looks_like_tag              # noqa: E402

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
REFERENCE = BOOK / "reference"
XML = SRC / "euclidhismodernr00carr_abbyy.gz"

MAX_WORDS = 7000

# Scan pages, not printed pages. The body opens on the ACT I title page and
# the Appendices begin at the first APPENDIX heading.
BODY_FIRST, APPENDIX_FIRST = 38, 265

# PAGE 38 AND PAGE 40 ARE THE SAME PRINTED PAGE. An erratum slip is pasted
# over the stage direction on 38, so the scan holds the opening of the play
# twice -- once destroyed. Concatenated naively the book opens with a line
# of pure noise and then repeats itself.
DUPLICATE_PAGES = {38, 39}

# Running heads sit at the top of the page in nine-point ("MINOS AND
# EUCLID. [Act I."); signature marks sit at the foot in seven- or
# eight-point ("'^ B"). Both are page furniture and both are INSIDE the
# text, which is the thompson/ trap: strip one and it leaves a blank line,
# a blank line is a paragraph break, and paragraphs then split at every
# page turn.
HEAD_ZONE, FOOT_ZONE = 0.12, 0.90
HEAD_MAX_CHARS = 60


def is_running_head(par, page):
    if par[0].top >= HEAD_ZONE * page.height:
        return False
    txt = clean(" ".join(l.text for l in par))
    if len(txt) > HEAD_MAX_CHARS:
        return False
    size = par[0].runs[0].size if par[0].runs else ""
    if size not in ("9.", "8."):
        return False
    letters = [c for c in txt if c.isalpha()]
    caps = sum(1 for c in letters if c.isupper())
    return (bool(re.search(r"\[\s*A[Cc][Tt]", txt))
            or re.fullmatch(r"[\d ivxl]+", txt.lower().strip())
            or (letters and caps / len(letters) > 0.6))


def is_signature(par, page):
    if par[0].top <= FOOT_ZONE * page.height:
        return False
    txt = clean(" ".join(l.text for l in par))
    size = par[0].runs[0].size if par[0].runs else ""
    return len(txt) <= 6 or size in ("6.", "7.")


ACT = re.compile(r"^ACT\s*([IVXL]+)\.?$", re.I)
SCENE = re.compile(r"^Scene\s*([IVXL]+)\.?$", re.I)
APPENDIX = re.compile(r"^APPENDIX\s*([IVXL]*)\.?$", re.I)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "L": 1}          # the scan reads "ACT I." as "ACT L." twice


def read_pages():
    """Every page as (number, [(kind, text)]), furniture already gone."""
    out = []
    for pg in pages(XML):
        if pg.number in DUPLICATE_PAGES or not pg.blocks:
            continue
        items = []
        for b in pg.blocks:
            if b.kind == "Picture":
                # a full-bleed Picture block is the scan of a whole leaf,
                # not a plate
                if (b.right - b.left) < pg.width * 0.95:
                    items.append(("picture", f"{pg.number}"))
                continue
            if b.kind == "Table":
                items.append(("table", f"{pg.number}"))
                continue
            for par in b.paragraphs:
                if is_running_head(par, pg) or is_signature(par, pg):
                    continue
                txt = clean(" ".join(l.text for l in par))
                if not txt:
                    continue
                tag = None
                r0 = par[0].runs[0] if par[0].runs else None
                if r0 and r0.italic and looks_like_tag(clean(r0.text)):
                    who, _ = resolve(clean(r0.text))
                    if who:
                        tag = who
                        txt = clean(txt[len(clean(r0.text)):])
                items.append(("speech" if tag else "par",
                              f"{tag}\t{txt}" if tag else txt))
        out.append((pg.number, items))
    return out


def mend(paras):
    """Rejoin paragraphs split by a page turn.

    thompson/'s rule, and it is the one that matters most on a scan: no
    English paragraph begins in lower case. Stripping the running head
    leaves the two halves of a sentence as separate paragraphs, and
    nothing downstream can tell.
    """
    out = []
    for kind, text in paras:
        if (out and kind == "par" and out[-1][0] in ("par", "speech")
                and text[:1].islower()):
            k, prev = out[-1]
            joiner = "" if prev.endswith("-") else " "
            out[-1] = (k, prev.rstrip("-") + joiner + text)
        else:
            out.append((kind, text))
    return out
