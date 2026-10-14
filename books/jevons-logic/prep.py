"""Build chapters/ + manifest.json for W. Stanley Jevons's Elementary
Lessons in Logic: Deductive and Inductive (1870), from Archive.org scans.

    python3 books/jevons-logic/prep.py            # rebuild chapters/, manifest.json
    python3 books/jevons-logic/prep.py --figures  # also re-cut the figure images

SOURCES (all in _src/, none kept in git):

  BASE   elementarylesson00jevouoft (Toronto). Archive.org catalogues it as
         1898; the title page actually reads "St Martin's Press 1957", a
         late reprint from the same plates (the preface is dated Hampstead,
         November 1876 -- the revised text). We read it from its ABBYY XML
         (_src/scan/abbyy.gz), not from its _djvu.txt: ABBYY carries page
         boundaries and line coordinates, which turn every piece of page
         furniture (running heads, page numbers, signature marks,
         footnotes, figure labels) into a positional rule.
  WITNESS elementarylesson00jevo.txt (UConn). Catalogued as 1870; the
         title page reads Macmillan 1893. SAME TEXT STATE as the base.
  WITNESS elementarylogic00jevouoft.txt. Catalogued 1891; the title page
         calls Jevons "Professor of Logic in Owens College" (he left in
         1876), there is no 1876 dateline, and the preface reads
         "Archbishop Thomson" where the revised text reads "Mr George
         Bentham". The EARLY text state.

THE VOTE (vote()). All three are printed from the same plates, so their
word streams align almost token for token. A base token is replaced only
when BOTH witnesses agree on something else -- the 1893 witness shares
the base's text, so its agreement with the early edition against the base
can only mean the base's OCR is wrong. Where base and 1893 agree against
the early edition, that is a genuine revision and the base stands. Every
change is logged to _src/vote_log.txt. A change that swaps one dictionary
word for another is NOT applied automatically (it could be a revision
after 1893); those are listed in the log for eyes, and the ones read off
the page image are applied through SOURCE_FIXES.

Everything that is not a vote is DATA in this file: SOURCE_FIXES (pairs
that must match, or prep stops), REGIONS (figure crops and hand
transcriptions of tables, each keyed to a leaf and a box on the page
image), FOOTNOTE_ANCHORS.
"""

import argparse
import collections
import difflib
import gzip
import json
import pickle
import re
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent.parent
SRC = BOOK / "_src"
SCAN = SRC / "scan"
IA = "elementarylesson00jevouoft"
W93 = SRC / "elementarylesson00jevo.txt"        # 1893 printing, same text
WOLD = SRC / "elementarylogic00jevouoft.txt"    # early (pre-1876) text
SITE_IMG = ROOT / "site" / "images" / "jevons-logic"

# Leaves that are not pages: photographs of the open book (no page number,
# OCR noise only) between pp. vi-vii, 67-68, 129-130 and 273-274. The leaf
# map is contiguous across each pair, so nothing is missing.
JUNK = {12, 13, 86, 87, 150, 151, 296, 297}
PREFACE_LEAVES = [9, 10, 11, 14]
BODY_LEAVES = [lf for lf in range(19, 365) if lf not in JUNK]


# ----------------------------------------------------------------------
# sources
# ----------------------------------------------------------------------

def ensure_scan():
    """Fetch the scan files if missing (archive.org, ~110 MB)."""
    SCAN.mkdir(parents=True, exist_ok=True)
    want = {
        "abbyy.gz": f"{IA}_abbyy.gz",
        "page_numbers.json": f"{IA}_page_numbers.json",
        "jp2.zip": f"{IA}_jp2.zip",
    }
    for local, remote in want.items():
        if not (SCAN / local).exists():
            url = f"https://archive.org/download/{IA}/{remote}"
            print("fetching", url)
            subprocess.run(["curl", "-sL", "--max-time", "900", "-o",
                            str(SCAN / local), url], check=True)
    jp2 = SCAN / f"{IA}_jp2"
    if not jp2.exists():
        subprocess.run(["unzip", "-q", "-o", str(SCAN / "jp2.zip"), "-d",
                        str(SCAN)], check=True)


def page_numbers():
    pages = json.loads((SCAN / "page_numbers.json").read_text())["pages"]
    return {p["leafNum"]: p["pageNumber"] for p in pages}


def leaf_image(leaf):
    from PIL import Image
    return Image.open(SCAN / f"{IA}_jp2" / f"{IA}_{leaf:04d}.jp2")


def load_abbyy():
    cache = SCAN / "abbyy.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    root = ET.parse(gzip.open(SCAN / "abbyy.gz")).getroot()
    ns = root.tag.split("}")[0] + "}"
    pages = []
    for page in root.iter(ns + "page"):
        blocks = []
        for b in page.iter(ns + "block"):
            bb = tuple(int(b.get(k)) for k in "ltrb")
            lines = []
            for ln in b.iter(ns + "line"):
                chars, ital = [], []
                for fm in ln.iter(ns + "formatting"):
                    it = fm.get("italic") == "true"
                    for c in fm.iter(ns + "charParams"):
                        chars.append(c.text or " ")
                        ital.append(it)
                lines.append(dict(text="".join(chars),
                                  l=int(ln.get("l")), t=int(ln.get("t")),
                                  r=int(ln.get("r")), b=int(ln.get("b")),
                                  ital=sum(ital) / max(1, len(ital))))
            blocks.append(dict(type=b.get("blockType"), bb=bb, lines=lines))
        pages.append(dict(w=int(page.get("width")), h=int(page.get("height")),
                          blocks=blocks))
    cache.write_bytes(pickle.dumps(pages))
    return pages


def check_leaf_map(pn):
    """ABBYY page N == jp2 _N == page_numbers leafNum N. Pinned on leaves
    whose printed numbers were read off the images."""
    for leaf, page in [(19, ""), (21, "3"), (93, "73"), (152, "130"),
                       (320, "296"), (356, "332")]:
        if pn.get(leaf, "") != page:
            sys.exit(f"leaf map changed: leaf {leaf} -> {pn.get(leaf)!r}, "
                     f"expected {page!r}")


# ----------------------------------------------------------------------
# page furniture
# ----------------------------------------------------------------------

HEAD = re.compile(r"less|LESS|^\s*[IVXLixvl1]+\.?\s*\]|\]\s*$|^\s*\d+\s+\S|"
                  r"\S\s+\d+\s*$|^\s*\d+\s*$|PREFACE|^\s*[IVXL]+\.\]")
HEADING_LINE = re.compile(r"^\s*(L\S{1,3}SON\b|INTRODUCTION|QUESTIONS\s+AND\s+EXERCISES\s*\.?\s*$|INDEX\s*,?\s*$|PREFACE\s*$)")
SIG = re.compile(r"^[\dIil1—–\-\s.,'~^]{1,7}$|^\d{1,2}\s*[—–-]\s*\S?$")
FOOTMARK = re.compile(r"^\s*[*†‡§^•♦■]|^\s*[ft]\s+[A-Z]")


def raw_lines(pages, leaf, drop_boxes=()):
    out, seen = [], set()
    for b in pages[leaf]["blocks"]:
        if b["type"] == "Picture":
            continue
        for ln in b["lines"]:
            key = (ln["t"], ln["l"], ln["text"])
            if key in seen or not ln["text"].strip():
                continue
            cx, cy = (ln["l"] + ln["r"]) / 2, (ln["t"] + ln["b"]) / 2
            if any(l <= cx <= r and t <= cy <= bt for (l, t, r, bt) in drop_boxes):
                continue
            seen.add(key)
            out.append(dict(ln))
    return sorted(out, key=lambda x: (x["t"], x["l"]))


def split_page(lines):
    """-> (furniture, body, footnote) lines of one page."""
    if not lines:
        return [], [], []
    furn = []
    t0 = lines[0]["t"]
    band = [x for x in lines if x["t"] < t0 + 45]
    # Every leaf that does not open on a heading carries a running head in
    # its top band; some OCR beyond any pattern ("Xvii.1 OF The SYLLOGtSM.
    # 14^"), so position decides: a top band above y=330 is furniture.
    numbered = any(re.search(r"\d{2,3}\s*$|^\s*\S{3}\s", x["text"]) for x in band)
    if ((t0 < 330 or any(HEAD.search(x["text"]) for x in band))
            and not (any(HEADING_LINE.match(x["text"]) for x in band) and not
                     (numbered and any("QUESTIONS" in x["text"] for x in band)))):
        furn = band
        lines = [x for x in lines if x["t"] >= t0 + 45]
    if (len(lines) > 1 and SIG.match(lines[-1]["text"].strip())
            and lines[-1]["t"] - lines[-2]["t"] > 50):
        furn.append(lines.pop())
    foot = []
    if len(lines) > 4:
        gaps = [b["t"] - a["t"] for a, b in zip(lines, lines[1:]) if b["t"] - a["t"] > 20]
        pitch = statistics.median(gaps) if gaps else 66
        for i in range(len(lines) - 1, max(0, len(lines) - 12), -1):
            if lines[i]["t"] - lines[i - 1]["t"] > 1.3 * pitch and FOOTMARK.match(lines[i]["text"]):
                foot, lines = lines[i:], lines[:i]
                break
    return furn, lines, foot


# ----------------------------------------------------------------------
# the vote
# ----------------------------------------------------------------------

def dictionary():
    words = set()
    for f in ("/usr/share/dict/words", "/usr/share/dict/british-english",
              "/usr/share/dict/american-english"):
        p = Path(f)
        if p.exists():
            words |= {w.strip().lower() for w in p.read_text(errors="ignore").split()}
    return words


def core(tok):
    return re.sub(r"^[^\w]+|[^\w]+$", "", tok)


def align_map(base, wit, chunk=2500, slack=900):
    """For each base token, the index of the witness token aligned with it
    (1:1 'equal' or equal-length 'replace' spans), else None."""
    out = [None] * len(base)
    w0 = 0
    i = 0
    while i < len(base):
        a = base[i:i + chunk]
        b = wit[w0:w0 + chunk + slack]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        last = None
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
                for k in range(i2 - i1):
                    out[i + i1 + k] = w0 + j1 + k
                    last = (i + i1 + k, w0 + j1 + k)
        # restart the window a little before the last matched pair
        if last is None:
            w0 += chunk
        else:
            w0 = max(0, last[1] - (i + len(a) - 1 - last[0]))
        i += len(a)
    return out


# Word-for-word swaps the witnesses agree on that are NOT applied: here the
# witnesses share a misreading, or the base is right (checked on the image).
VOTE_DENY = {
    ("III.", "in."),
    ("in", "m"),
    ("true", "tine"),
    ("all", "aU"),
    ("(l)", "(i)"),          # it is "(1)": SOURCE_FIXES
}
# ...and the held swaps that were read on the image and found right.
VOTE_ACCEPT = {
    ("IV.", "W."), ("B,", "E,"), ("Z>,", "D,"), ("Example*", "Examples"),
    ("F", "Y"), ("\\V.", "W."), ("slop", "stop"), ("be", "he"),
    ("factor)'", "factory"), ("by", "b,"), ("healing", "heating"),
    ("modem", "modern"), ("Modem", "Modern"), ("s-,", "z,"), ("B", "E"),
}


def vote(stream, words, log):
    """stream: list of [token, ...] mutable lists (one per line). Applies
    witness-agreed corrections in place; returns stats."""
    refs = [(li, ti) for li, toks in enumerate(stream) for ti in range(len(toks))]
    base = [stream[li][ti] for li, ti in refs]
    w93 = W93.read_text(errors="ignore").split()
    wold = WOLD.read_text(errors="ignore").split()
    m93 = align_map(base, w93)
    mold = align_map(base, wold)
    stats = collections.Counter()
    held = []
    freq = collections.Counter(core(t).lower() for t in base)
    for k, (li, ti) in enumerate(refs):
        if m93[k] is None or mold[k] is None:
            stats["unaligned"] += 1
            continue
        b, x, y = base[k], w93[m93[k]], wold[mold[k]]
        if b == x:
            stats["agree"] += 1
            continue
        if x != y:
            stats["no_majority"] += 1
            continue
        cb, cx = core(b).lower(), core(x).lower()
        ctx = " ".join(base[max(0, k - 4):k + 5])
        if cb == cx:
            kind = "punct"
        elif cb in words and cx in words and cb.isalpha():
            # Both are words. Nearly all of these are still OCR ("docs" for
            # does, "arc" for are, "m" for in, "modem" for modern), and the
            # tell is frequency: the misreading is rare in this very book,
            # the reading common. A swap the other way round is held.
            if (((freq[cx] >= 3 * max(1, freq[cb])) or (b, x) in VOTE_ACCEPT)
                    and (b, x) not in VOTE_DENY):
                kind = "freq"
            else:
                stats["held_word_vs_word"] += 1
                held.append(f"HELD  {b!r} -> {x!r}   | {ctx}")
                continue
        else:
            kind = "word"
        stream[li][ti] = x
        stats["fixed_" + kind] += 1
        log.append(f"{kind:5s} {b!r} -> {x!r}   | {ctx}")
    log.extend(held)
    return stats


# ----------------------------------------------------------------------
# character-level repairs
# ----------------------------------------------------------------------

# Mechanical rules for this scan's systematic misreadings, applied to every
# OCR line after the vote (never to the hand transcriptions):
CLEAN = [
    # Jevons's O (the particular negative) is a bold sans capital the OCR
    # reads as a zero, everywhere; no bare zero survives in the OCR text
    # (the zeros of Lesson XXVI are in transcriptions.py)
    (re.compile(r"\b[0O]/\s*"), "of "),
    (re.compile(r"(?<![\w.,])0(?![\w°^])"), "O"),
    # an italic word's trailing letter or stop read as a caret
    (re.compile(r"(?<=[A-Za-z])\^"), ""),
    # broken v and y
    (re.compile(r"\\'"), "v"),
    (re.compile(r"(?<=[a-z])>'"), "y"),
    (re.compile(r"(?<=[a-z])\)'"), "y"),
    (re.compile(r"«S:c\.|&C\b"), "&c."),
    # Jevons numbers sub-items (1), (2): the OCR reads the 1 as i, l or I
    (re.compile(r"\((?:i|l|I)\)(?=\s)"), "(1)"),
    # an italic parenthesis read as a brace
    (re.compile(r"\{"), "("),
    (re.compile(r"\}"), ")"),
]


def clean_line(text):
    for pat, rep in CLEAN:
        text = pat.sub(rep, text)
    return text


# ----------------------------------------------------------------------
# lines -> paragraphs
# ----------------------------------------------------------------------

LESSON_LINE = re.compile(r"^\s*L\S{1,3}SON\s+([IVXLl1]+)\s*\.?\s*$")
QE_ITEM = re.compile(r"^\s*(\d{1,3}\s*\.|[Il\[]\.|\(\s*[\dil]{1,2}\s*\)|\d{1,2}\))\s")
FOOT_IN_TEXT = re.compile(r"(?<=[\w.,;:'\"’”)])\s?[*•♦]\^?(?=\s|$|[.,;:])")


def body_left(lines, mode="prose"):
    if not lines:
        return 0
    if mode == "qe":
        ls = sorted(x["l"] for x in lines)
        return ls[len(ls) // 10]
    right = max(x["r"] for x in lines)
    full = sorted(x["l"] for x in lines if x["r"] > right - 60)
    if len(full) < 3:
        full = sorted(x["l"] for x in lines)
    return full[len(full) // 3]


def classify(lines, mode):
    """Give each line a kind: start / cont / disp / lesson / qhead."""
    left = body_left(lines, mode)
    right = max((x["r"] for x in lines), default=0)
    for x in lines:
        x["mode"] = mode
        off = x["l"] - left
        s = x["text"].strip()
        x["off"] = off
        if LESSON_LINE.match(s):
            x["kind"] = "lesson"
        elif mode == "qe" and re.match(r"^\s*(L\S{1,3}sons?\s+\S.{0,60}[—~\-^]|MISCELLANEOUS)", s):
            x["kind"] = "qhead"
        elif mode == "qe":
            # numbered items hang: the number sits at the page's left
            # column and the turnover lines ~140 px in; the number itself
            # is often misread ("I.", "\.", "[."), so geometry decides
            x["kind"] = "start" if off < 100 else "cont"
            if re.match(r"^\(\s*[\dil]{1,2}\s*\)|^\^\^?\d\)", s) and off < 260:
                x["kind"] = "start"     # a lettered sub-item, "(1)" ... "(14)"
            # a line that opens a question the witnesses number is a start,
            # whatever its indent (the base lost some numbers in the gutter)
            global WITNESS_ITEMS
            if WITNESS_ITEMS is None:
                WITNESS_ITEMS = witness_items()
            bare = re.sub(r"^[\dIil\[\\,.]{1,4}\s+", "", s)
            key = " ".join(re.sub(r"[^a-z ]", "", " ".join(bare.split()[:4]).lower()).split())
            if key in WITNESS_ITEMS and len(key) > 12:
                x["kind"] = "start"
                x["witem"] = True
        elif re.search(r"\.{5,}|…{2,}", s) and off < 135:
            x["kind"] = "disp"          # a line with dot leaders is a table row
        elif off >= 135 and not (x["r"] > right - 40 and off < 200):
            x["kind"] = "disp"
        elif off >= 40:
            x["kind"] = "start"
        else:
            x["kind"] = "cont"
    if mode == "prose":
        # DISPLAYED ARGUMENTS SET AT THE PARAGRAPH INDENT: justified prose
        # runs to the right margin, so a SHORT line ending on a comma or
        # semicolon is a premise set on its own line, and so is the line
        # after it and a closing "Therefore ..."
        prev = None
        for x in lines:
            s = x["text"].strip()
            short = x["r"] < right - 90
            ps = prev["text"].strip() if prev is not None else ""
            opener = (prev is not None and (prev["kind"] == "disp"
                      or (re.search(r"(:|:—|:-|—|thus|follows)$", ps) and not re.match(r"\d+\.", ps))
                      or prev["r"] < right - 90))
            if (x["kind"] in ("start", "cont") and short and re.search(r"[,;]$", s)
                    and s[:1].isupper() and len(s.split()) <= 12 and opener):
                x["kind"] = "disp"
            elif (prev is not None and prev["kind"] == "disp" and x["kind"] in ("start", "cont")
                  and s[:1].isupper() and len(s.split()) <= 12
                  and ((short and re.search(r"[,;]$", ps)) or re.match(r"(Therefore|Hence)\b", s))):
                x["kind"] = "disp"
            prev = x
    return lines


QE_FIRST_LEAF = 320      # p. 296, QUESTIONS AND EXERCISES
INDEX_FIRST_LEAF = 356   # p. 332, INDEX


def roman(s):
    s = s.upper().replace("L1", "LI").replace("1", "I")
    vals = dict(I=1, V=5, X=10, L=50)
    n = 0
    for a, b in zip(s, s[1:] + " "):
        v = vals[a]
        n += -v if b != " " and vals.get(b, 0) > v else v
    return n


def page_events(pages, leaf, mode, regions, witness_pages):
    """Events for one leaf, in reading order."""
    boxes = [r["box"] for r in regions if r["leaf"] == leaf]
    lines = raw_lines(pages, leaf, boxes)
    furn, body, foot = split_page(lines)
    if leaf in witness_pages:
        body = witness_pages[leaf]["body"]
        foot = witness_pages[leaf]["foot"]
    else:
        classify(body, mode)
    ev = []
    regs = sorted((r for r in regions if r["leaf"] == leaf), key=lambda r: r["box"][1])
    for x in body:
        while regs and regs[0]["box"][1] <= x["t"]:
            ev.append(("region", regs.pop(0)))
        ev.append(("line", x))
    for r in regs:
        ev.append(("region", r))
    if foot:
        ev.append(("foot", foot))
    return ev


TERMINAL = re.compile(r"(?:[.:;!?]|—)['\"’”)]*\s*$")


def assemble(events_by_leaf):
    """events -> {key: [paragraph, ...]} with key 'preface', 1..33, 'qe'.
    A paragraph is a dict(kind, lines, notes)."""
    sections = collections.OrderedDict(preface=[])
    key = "preface"
    cur = None
    pending = []
    skip_title = False
    log = []

    def close():
        nonlocal cur
        if cur is not None:
            sections[key].append(cur)
            cur = None
        while pending:
            sections[key].append(pending.pop(0))

    for leaf, events in events_by_leaf:
        marks = []
        for kind, x in events:
            if kind == "region" and not x["figure"]:
                # a hand transcription: TAB paragraphs are set verbatim, prose
                # paragraphs flow -- the first joins a sentence the OCR left
                # open, the last stays open for the next page to continue.
                chunks = [c for c in re.split(r"\n\s*\n", x["text"]) if c.strip()]
                for i, c in enumerate(chunks):
                    if c.startswith("\t"):
                        close()
                        sections[key].append(dict(kind="disp", raw=True, notes=[], leaf=leaf,
                                                  lines=[dict(text=l) for l in c.split("\n")]))
                    elif (cur is not None and cur["kind"] == "prose"
                          and (c[:1].islower()
                               or not TERMINAL.search(cur["lines"][-1]["text"]))):
                        cur["lines"].append(dict(text=c))
                    else:
                        close()
                        cur = dict(kind="prose", lines=[dict(text=c)], notes=[], leaf=leaf)
                if cur is not None and TERMINAL.search(cur["lines"][-1]["text"]):
                    close()
                continue
            if kind == "region":
                para = dict(kind="region", region=x, notes=[], leaf=leaf)
                if (cur is not None and cur["kind"] == "prose"
                        and not TERMINAL.search(cur["lines"][-1]["text"])):
                    pending.append(para)        # floats past the sentence
                else:
                    close()
                    sections[key].append(para)
                continue
            if kind == "foot":
                # one note per marked line (a page may carry * and a dagger)
                groups = []
                for ln in x:
                    if re.match(r"^\s*[*†‡•♦■]|^\s*[ft]\s+[A-Z]", ln["text"]) or not groups:
                        groups.append([])
                    groups[-1].append(" ".join(ln["text"].split()))
                for gi, g in enumerate(groups):
                    text = join_lines(g)
                    text = re.sub(r"^\s*[*•♦^†■]\s*|^\s*[ft]\s+(?=[A-Z])", "", text)
                    target = marks[gi] if gi < len(marks) else None
                    if target is None:
                        target = cur if cur is not None else (sections[key][-1] if sections[key] else None)
                        log.append(f"leaf {leaf}: no mark found, note attached to last paragraph: {text[:60]}")
                    target["notes"].append(text)
                continue
            s = x["text"].strip()
            k = x["kind"]
            if re.match(r"^F[il1][gzi]\w{0,2}\.?\s*\S{0,3}\.?$", s):
                continue                # a figure label outside its region
            if k == "lesson":
                close()
                key = roman(LESSON_LINE.match(s).group(1))
                sections[key] = []
                skip_title = True
                continue
            if k == "qsection":
                close()
                key = "qe"
                sections[key] = []
                continue
            if k == "index":
                close()
                key = "index"
                sections[key] = []
                continue
            if skip_title:
                letters = [c for c in s if c.isalpha()]
                if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
                    continue
                skip_title = False
                k = "start"
            if k == "qhead":
                close()
                cur = dict(kind="qhead", lines=[x], notes=[], leaf=leaf)
                continue
            if (k == "cont" and cur is not None and cur["kind"] == "qhead"
                    and (not TERMINAL.search(cur["lines"][-1]["text"])
                         or s.startswith("Lessons"))):
                cur["lines"].append(x)      # a set heading that wraps
                continue
            # the conclusion of a displayed syllogism is set out-dented
            if (k in ("start", "cont") and cur is not None and cur["kind"] == "disp"
                    and re.match(r"(Therefore|Hence|\.\s?\*\.|∴|\.•\.|\*\.)", s)
                    and len(s) < 70):
                k = "disp"
            if (k == "start" and x.get("mode") == "qe" and cur is not None
                    and not x.get("witem")
                    and cur["kind"] == "prose"
                    and not re.match(r"^[\dIil\[\\]{1,3}\s?[.,]|^\(|^\^", s)
                    and not TERMINAL.search(cur["lines"][-1]["text"])):
                k = "cont"
            # NO ENGLISH PARAGRAPH OPENS IN LOWER CASE: a lower-case "start"
            # after an unfinished sentence is the hanging indent of a
            # reference, or the far side of a page turn (thompson's rule)
            if (k == "start" and cur is not None and cur["kind"] == "prose"
                    and s[:1].islower()
                    and (not TERMINAL.search(cur["lines"][-1]["text"])
                         or cur["lines"][-1]["text"].rstrip().endswith(";"))):
                k = "cont"
            if k == "start" or (k == "cont" and (cur is None or cur["kind"] != "prose")):
                close()
                cur = dict(kind="prose", lines=[x], notes=[], leaf=leaf)
            elif k == "cont":
                cur["lines"].append(x)
            elif (k == "disp" and cur is not None and cur["kind"] == "prose"
                  and s[:1].islower() and not TERMINAL.search(cur["lines"][-1]["text"])
                  or k == "disp" and cur is not None and cur["kind"] == "prose"
                  and re.search(r"\w-$", cur["lines"][-1]["text"].strip())):
                # the hanging indent of a reading-list reference, or a word
                # broken at the line end: a continuation, not a display
                cur["lines"].append(x)
            elif k == "disp":
                if cur is None or cur["kind"] != "disp":
                    close()
                    cur = dict(kind="disp", lines=[x], notes=[], leaf=leaf)
                else:
                    cur["lines"].append(x)
            if FOOT_IN_TEXT.search(x["text"]):
                marks.append(cur)
                x["text"] = FOOT_IN_TEXT.sub("", x["text"], count=1)
    close()
    return sections, log


HYPHEN_COUNTS = collections.Counter()
DICT = set()


def join_lines(texts):
    out = ""
    for t in texts:
        t = " ".join(t.split())
        if not out:
            out = t
            continue
        m = re.search(r"(\w+)-$", out)
        if m and not out.endswith("--") and t and (t[0].islower()):
            a = m.group(1)
            b = re.match(r"[\w']+", t)
            b = b.group(0) if b else ""
            joined, hyph = (a + b).lower(), (a + "-" + b).lower()
            keep = HYPHEN_COUNTS[hyph] > HYPHEN_COUNTS[joined]
            # a compound whose halves are words and whose join is not
            # ("fellow-creature", "self-consistent", "seed-vessel")
            if (not keep and DICT and joined not in DICT and a.lower() in DICT
                    and b.lower() in DICT and len(a) > 2 and len(b) > 2
                    and HYPHEN_COUNTS[joined] == 0):
                keep = True
            if keep:
                out = out + t
            else:
                out = out[:-1] + t
        else:
            out = out + " " + t
    return out


def count_words(all_texts):
    for t in all_texts:
        for w in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", t):
            HYPHEN_COUNTS[w.lower()] += 1
            if "-" in w:
                pass


def tidy(text):
    text = re.sub(r"\s+([;:?!,.])", r"\1", text)
    text = re.sub(r'(^|\s)"\s+', r'\1"', text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def apply_joins(chunks, owner):
    """JOINS: (end of one paragraph, start of the next) that the page
    layout split -- the hanging indent of a reading-list reference, a
    sentence over a page turn whose second half opens on a capital.
    Every pair must match, or prep stops."""
    for end, start in JOINS:
        hit = [i for i in range(len(chunks) - 1)
               if chunks[i].rstrip().endswith(end) and chunks[i + 1].lstrip("\t").startswith(start)]
        inner = [i for i, c in enumerate(chunks) if (end + "\n\t" + start) in c]
        if len(hit) + len(inner) != 1:
            sys.exit(f"JOINS entry matched {len(hit) + len(inner)} times: {end!r} + {start!r}")
        if inner:
            i = inner[0]
            chunks[i] = chunks[i].replace(end + "\n\t" + start, end + " " + start)
            continue
        i = hit[0]
        nxt = chunks[i + 1]
        if nxt.startswith("\t") and not chunks[i].startswith("\t"):
            nxt = " ".join(l.strip() for l in nxt.split("\n"))    # a reference set as a display
        chunks[i] = chunks[i].rstrip() + (" " if not chunks[i].startswith("\t") else "\n\t") + nxt.lstrip("\t").strip() \
            if not chunks[i].startswith("\t") else chunks[i].rstrip() + " " + nxt.lstrip("\t").strip()
        del chunks[i + 1]
        del owner[i + 1]
    for start in UNDISPLAY:
        hit = [i for i, c in enumerate(chunks) if c.startswith("\t" + start)]
        if len(hit) != 1:
            sys.exit(f"UNDISPLAY entry matched {len(hit)} times: {start!r}")
        i = hit[0]
        chunks[i] = " ".join(l.strip() for l in chunks[i].split("\n"))
    return chunks, owner


def apply_source_fixes(chunks):
    """SOURCE_FIXES over a list of rendered paragraphs; every pair must hit."""
    text = "\n\n".join(chunks)
    missing = []
    for old, new in SOURCE_FIXES:
        if old not in text:
            missing.append(old)
        text = text.replace(old, new)
    if missing:
        sys.exit("SOURCE_FIXES entries no longer match (see _src/debug.txt):\n  " + "\n  ".join(map(repr, missing)))
    return text.split("\n\n")


def render(paras):
    out = []
    for p in paras:
        if p["kind"] == "prose":
            out.append(tidy(join_lines([x["text"] for x in p["lines"]])))
        elif p["kind"] == "disp" and p.get("raw"):
            out.append("\n".join(x["text"] for x in p["lines"]))
        elif p["kind"] == "disp":
            out.append("\n".join("\t" + tidy(x["text"]) for x in p["lines"]))
        elif p["kind"] == "qhead":
            out.append("@@QHEAD " + tidy(" ".join(x["text"] for x in p["lines"])))
        elif p["kind"] == "region":
            r = p["region"]
            out.append(f"[Figure {r['id']}]" if r.get("figure") else r["text"])
        for n in p["notes"]:
            out.append("Footnote: " + tidy(n))
    return out


# ----------------------------------------------------------------------
# figures and hand-set blocks
# ----------------------------------------------------------------------
#
# A REGION is a band of one leaf, (y0, y1) in scan pixels (x0, x1 optional),
# read off the page image. Every OCR line whose centre falls inside it is
# dropped, and the region takes its place in the text: a FIGURE becomes a
# "[Figure id]" marker and a PNG cut from the scan; a TEXT region becomes
# the transcription given here, read off the page image (not the OCR).
#
# Figure ids: the printed numbers where Jevons numbers them (Fig. 1-12 ->
# fig1..fig12), and digit-free names for the diagrams he does not number,
# so assemble.figure_label prints no "Figure N" for them (euler precedent).
# A figure that interrupts a sentence floats to the end of that paragraph.

def F(id, leaf, y0, y1, x0=None, x1=None):
    return dict(id=id, leaf=leaf, y0=y0, y1=y1, x0=x0, x1=x1, figure=True)


def T(id, leaf, y0, y1, text, x0=None, x1=None):
    return dict(id=id, leaf=leaf, y0=y0, y1=y1, x0=x0, x1=x1, figure=False,
                text=text.strip("\n"))


FIGURES = [
    F("brackets", 23, 1065, 1308),        # p.5   (Y) / (X) ... is ... (Z)
    F("knowledge", 72, 1232, 1795),       # p.54  Leibnitz's division of knowledge
    F("sentence", 81, 786, 1188),         # p.63  kinds of sentence
    F("proposition", 84, 492, 798),       # p.66  universal/particular, A E I O
    F("1", 92, 962, 1540, 560, 1240),                # p.72  A: metals inside elements
    F("2", 93, 238, 862),                 # p.73  I: metals / brittle substances
    F("3", 93, 1905, 2492, 434, 1400),               # p.73  E: metals / compounds
    F("4", 95, 1345, 1960, 470, 1300),               # p.75  O
    F("square", 98, 474, 1336),           # p.78  square of opposition
    F("5", 104, 492, 1062),               # p.84  contrapositive
    F("metals", 113, 2204, 2466),         # p.93  Iron, Copper, Lead, Zinc are ...
    F("lover", 114, 952, 1420),           # p.94  "No one who is a lover of money ..."
    F("burbidge", 115, 225, 905),         # p.95  Burbidge's lines
    F("wordsworth", 115, 1515, 2496),     # p.95  Wordsworth's lines
    F("notions", 116, 1520, 2316),        # p.96  "We find that the two classes ..."
    F("gravitation", 117, 1012, 2076),    # p.97  the law of gravitation sentence
    F("porphyry", 124, 432, 1982),        # p.104 Tree of Porphyry
    F("rectilineal", 126, 1058, 1532),    # p.106 division of rectilineal figures
    F("parallelogram", 126, 2004, 2476),  # p.106 division of parallelograms
    F("dichotomy", 127, 1228, 1694),      # p.107 the same by dichotomy
    F("aryan", 128, 492, 856),            # p.108 Man: Aryan / not-Aryan ...
    F("greater", 140, 1594, 1792),        # p.120 greater / not-greater
    F("lines", 143, 480, 884),            # p.123 lines A-E
    F("6", 149, 1880, 2526),              # p.129 Frenchmen / Russians / Europeans
    F("7", 152, 962, 1794),               # p.130 Parisians / Frenchmen / Europeans
    F("8", 154, 1448, 2284),              # p.132 Anglo-Saxons / loving liberty
    F("9", 155, 1498, 2432, 446, 1300),              # p.133 Colonists / Americans / Europeans
    F("10", 164, 725, 1438, 306, 1000),   # p.142 Cesare
    F("11", 164, 725, 1438, 1000, 1720),  # p.142 Camestres
    F("12", 164, 1436, 2192),             # p.142 Festino
    F("conditional", 182, 1602, 1832),    # p.160 categorical / conditional
    F("hamaffirm", 211, 505, 748),        # p.189 Hamilton's notation, A U I
    F("hamnegative", 211, 1040, 1262),     # p.189 E O omega
    F("barbara", 211, 1612, 1836),        # p.189
    F("celarent", 211, 1908, 2150),       # p.189
    F("cesare", 211, 2222, 2436),         # p.189
]

from transcriptions import TEXTS  # noqa: E402  (hand transcriptions)
from fixes import LINE_FIXES, SOURCE_FIXES, JOINS, UNDISPLAY  # noqa: E402
from vocabulary import VOCABULARY  # noqa: E402


def regions():
    out = []
    for r in FIGURES + TEXTS:
        r = dict(r)
        r["box"] = (r["x0"] if r["x0"] is not None else 0, r["y0"],
                    r["x1"] if r["x1"] is not None else 10 ** 5, r["y1"])
        out.append(r)
    ids = [r["id"] for r in out]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit(f"region ids claimed twice: {dup}")
    return out


# LO is higher than thompson's 0.12: this scan shows the facing page through
# the paper, and at 0.12 that ghost text survives inside the circles.
PAPER_PCT, INK_PCT, LO, HI, MIN_SPAN = 99, 2, 0.38, 0.85, 40


def to_ink(gray):
    """Darkness -> alpha over pure black (thompson/replate.py's method):
    the paper goes, the ink stays anti-aliased as scanned."""
    import numpy as np
    from PIL import Image
    paper = float(np.percentile(gray, PAPER_PCT))
    floor = float(np.percentile(gray, INK_PCT))
    span = max(paper - floor, MIN_SPAN)
    a = (paper - gray.astype(np.float32)) / span
    a = np.clip((a - LO) / (HI - LO), 0.0, 1.0)
    a = np.round(np.round(a * 15) / 15 * 255).astype(np.uint8)
    out = np.zeros(gray.shape + (2,), dtype=np.uint8)
    out[..., 1] = a
    return Image.fromarray(out, mode="LA")


def cut_figures(pages, regs):
    import numpy as np
    SITE_IMG.mkdir(parents=True, exist_ok=True)
    for r in regs:
        if not r["figure"]:
            continue
        leaf = r["leaf"]
        im = leaf_image(leaf).convert("L")
        g = np.array(im)
        lines = raw_lines(pages, leaf)
        left = min(x["l"] for x in lines) - 40
        right = max(x["r"] for x in lines) + 40
        x0 = max(r["x0"] if r["x0"] is not None else left, 0)
        x1 = min(r["x1"] if r["x1"] is not None else right, g.shape[1])
        y0, y1 = r["y0"], r["y1"]
        band = g[y0:y1, x0:x1].copy()
        # the printed label ("Fig. 3.") is the renderer's job, not the plate's
        for x in lines:
            if re.match(r"\s*Fi[gz]", x["text"]) and y0 <= (x["t"] + x["b"]) / 2 <= y1:
                band[max(0, x["t"] - y0 - 6):x["b"] - y0 + 6,
                     max(0, x["l"] - x0 - 6):x["r"] - x0 + 6] = 255
        paper = np.percentile(band, PAPER_PCT)
        ink = band < paper - 60
        rows = np.where(ink.sum(1) >= 2)[0]
        cols = np.where(ink.sum(0) >= 2)[0]
        if not len(rows):
            sys.exit(f"figure {r['id']}: no ink in band")
        t, b = max(rows[0] - 14, 0), min(rows[-1] + 15, band.shape[0])
        l, rr = max(cols[0] - 14, 0), min(cols[-1] + 15, band.shape[1])
        img = to_ink(band[t:b, l:rr])
        img.save(SITE_IMG / f"fig{r['id']}.png", optimize=True)

# ----------------------------------------------------------------------
# structure: titles, question sets, parts
# ----------------------------------------------------------------------

# The heading of each lesson as printed over it (the body, not the
# contents, where XVII and XXIV are worded slightly differently).
TITLES = {
    1: "Definition and Sphere of the Science",
    2: "The Three Parts of Logical Doctrine",
    3: "Terms, and Their Various Kinds",
    4: "Of the Ambiguity of Terms",
    5: "Of the Twofold Meaning of Terms, in Extension and Intension",
    6: "The Growth of Language",
    7: "Leibnitz on Knowledge",
    8: "Kinds of Propositions",
    9: "The Opposition of Propositions",
    10: "Conversion of Propositions, and Immediate Inference",
    11: "Logical Analysis of Sentences",
    12: "The Predicables, Division, and Definition",
    13: "Pascal and Descartes on Method",
    14: "The Laws of Thought",
    15: "The Rules of the Syllogism",
    16: "The Moods and Figures of the Syllogism",
    17: "Reduction of the Imperfect Figures of the Syllogism",
    18: "Irregular and Compound Syllogisms",
    19: "Of Conditional Arguments",
    20: "Logical Fallacies",
    21: "Material Fallacies",
    22: "The Quantification of the Predicate",
    23: "Boole's System of Logic",
    24: "On Method, Analysis and Synthesis",
    25: "Perfect Induction and the Inductive Syllogism",
    26: "Geometrical and Mathematical Induction, Analogy and Example",
    27: "Observation and Experiment",
    28: "Methods of Induction",
    29: "Methods of Quantitative Induction",
    30: "Empirical and Deductive Methods",
    31: "Explanation, Tendency, Hypothesis, Theory, and Fact",
    32: "Classification, and Abstraction",
    33: "Requisites of a Philosophical Language",
}

# The groups of the printed contents, as part dividers in WORD form (a
# "Part I:" line is deleted by assemble.strip_front). The body prints
# INTRODUCTION over Lesson I, which the contents leave ungrouped.
PART_BEFORE = {
    1: "Introduction",
    3: "Terms",
    8: "Propositions",
    14: "Syllogism",
    20: "Fallacies",
    22: "Recent Logical Views",
    24: "Method",
    25: "Induction",
    32: "Subsidiaries of Induction",
}

QE_SUB = "Questions and Exercises"
# Question sets that cover several lessons: (lessons covered, the lesson
# whose file carries the set, subheading).
GROUP_SETS = [
    ((8, 9, 10), 10, "Examples of Propositions"),
    ((20, 21), 21, "Questions on Fallacies"),
    (tuple(range(9, 22)), 21, "Miscellaneous Examples"),
    ((28, 29), 29, "Questions on the Methods of Induction"),
]

PREFACE_TITLE = "Preface"
VOCAB_TITLE = "A Vocabulary of Logical Terms"
TARGET_MAX = 7000


def set_lessons(head):
    """The lessons a Q&E set heading names, read leniently off the OCR."""
    h = head.replace("@@QHEAD ", "")
    if h.startswith("MISCELLANEOUS"):
        return "misc"
    m = re.match(r"L\S{1,3}sons?\s+(.*?)\s*[—~^-]", h)
    if not m:
        sys.exit(f"cannot read question-set heading: {head!r}")
    nums = re.findall(r"[IVXLYlUKW\\]+", m.group(1).replace("and", " "))
    fix = str.maketrans({"Y": "V", "l": "I", "U": "I", "K": "X", "W": "V", "\\": "I"})
    return tuple(roman(n.translate(fix)) for n in nums if n.translate(fix))


# OCR readings of set headings that the lenient reader gets wrong,
# checked against the page: heading prefix -> lessons
SET_OVERRIDES = {
    "Lesson \\\\.~Three Parts": (2,),
    "Lesson lY.": (4,),
    "Lesson V\\\\\\.": (8,),
    "Lesson XU.": (12,),
    "Lesson XIIL": (13,),
    "Lesson XW.": (14,),
    "Lesson XY.": (15,),
    "Lesson y\\.": (16,),
    "Lessons VIII. IX. and Y": (8, 9, 10),
    "Lessons XX. and XKl": (20, 21),
    "Lesson XXUl.": (23,),
    "Lesson XXIY.": (24,),
    "Lesson XXW": (25,),
    "Lesson XXNW.": (27,),
    "Lessons XXVIII. and XXlX.": (28, 29),
    "Lesson XXXU.": (32,),
    "Lesson XXXlll.": (33,),
}


# Items whose number the OCR lost entirely (read off the page): text prefix -> n
QE_NUMBER_INSERT = {
    "What are the two chief requisites of a philosophical language": 2,
    "By what considerations should we be guided in choosing": 3,
    "Distinguish a Descriptive Terminology and a Nomenclature": 4,
    "What does Mr Mill mean by the expression Natural Kind": 5,
}
NUMTOK = re.compile(r"^([\dIil\[\\]{1,3})\s?[.,]?\s(?=\S)")


def witness_items():
    """First words of every numbered question in either witness -> its
    number: where the base scan lost a number in the gutter, a witness
    printed from the same plates usually kept it."""
    out = {}
    for f in (W93, WOLD):
        for line in f.read_text(errors="ignore").splitlines():
            m = re.match(r"^\s*(\d{1,3})\.\s+(\S+(?:\s+\S+){3})", line)
            if m:
                key = " ".join(re.sub(r"[^a-z ]", "", m.group(2).lower()).split())
                out.setdefault(key, int(m.group(1)))
    return out


WITNESS_ITEMS = None


def renumber(body, log, head):
    """Repair the item numbers of one question set: the OCR reads 1 as
    I, [ or \\, and misreads single digits (46 46 for 45 46, 60-63 for
    50-53). The printed numbering is consecutive, so an item whose
    number disagrees with its place AND whose neighbour confirms the
    place is renumbered; every change is logged."""
    global WITNESS_ITEMS
    if WITNESS_ITEMS is None:
        WITNESS_ITEMS = witness_items()
    out = []
    for b in body:
        b = re.sub(r"^[,.]\s+", "", b)
        for pre, n in QE_NUMBER_INSERT.items():
            if b.startswith(pre):
                b = f"{n}. {b}"
                log.append(f"    inserted number {n}: {pre[:40]}")
        if not NUMTOK.match(b) and not b.startswith(("(", "\t", "[", '"')):
            key = " ".join(re.sub(r"[^a-z ]", "", " ".join(b.split()[:4]).lower()).split())
            n = WITNESS_ITEMS.get(key)
            if n:
                b = f"{n}. {b}"
                log.append(f"    number {n} from a witness: {b[:50]!r}")
        out.append(b)
    idx = [i for i, b in enumerate(out) if NUMTOK.match(b) and not out[i].startswith("(")]
    toks = [NUMTOK.match(out[i]).group(1) for i in idx]
    expected = None
    for j, (i, t) in enumerate(zip(idx, toks)):
        val = int(t) if t.isdigit() else None
        if val == 1 or (val is None and expected in (None, 1)) and t in ("I", "[", "\\", "l", "i"):
            want = 1 if (val == 1 or expected in (None, 1) or j == 0) else expected
            if t in ("I", "[", "\\", "l", "i") and (expected in (None, 1) or j == 0):
                want = 1
        else:
            want = expected if expected is not None else val
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        nval = int(nxt) if nxt and nxt.isdigit() else None
        if val is not None and (val == expected or expected is None or val == 1):
            final = val
        elif want is not None and (nval == want + 1 or val is None or nval is None):
            final = want
        else:
            final = val if val is not None else want
        if str(final) != t:
            out[i] = NUMTOK.sub(f"{final}. ", out[i], count=1)
            log.append(f"    renumbered {t!r} -> {final} in {head[:30]!r}: {out[i][:50]!r}")
        else:
            out[i] = NUMTOK.sub(f"{final}. ", out[i], count=1)
        expected = final + 1
    nums = [int(NUMTOK.match(out[i]).group(1)) for i in idx]
    # a run whose first and last numbers agree with its length is
    # consecutive by count: renumber its middle (Misc. Examples 50-56)
    segs, s = [], 0
    for j in range(1, len(nums) + 1):
        if j == len(nums) or (nums[j] == 1 or (nums[j] > 20 and nums[j - 1] < 10 and j - s <= 6)):
            segs.append((s, j))
            s = j
    for s, e in segs:
        run = nums[s:e]
        if run and run[-1] - run[0] + 1 == len(run) and run != list(range(run[0], run[-1] + 1)):
            for k in range(s, e):
                want = run[0] + (k - s)
                if nums[k] != want:
                    log.append(f"    renumbered {nums[k]} -> {want} (run {run[0]}-{run[-1]} is consecutive by count)")
                    out[idx[k]] = NUMTOK.sub(f"{want}. ", out[idx[k]], count=1)
                    nums[k] = want
    gaps = [(a, b) for a, b in zip(nums, nums[1:]) if b != a + 1 and b != 1]
    if gaps:
        log.append(f"    NUMBERING GAPS in {head[:40]!r}: {gaps}")
    return out


def fold_questions(lessons, qe_paras):
    """Attach each question set to its lesson; return the coverage log."""
    sets, cur = [], None
    for para in qe_paras:
        if para.startswith("@@QHEAD "):
            if para.startswith("@@QHEAD MISCELLANEOUS"):
                cur = ("misc", para, [])
            else:
                h = para[len("@@QHEAD "):]
                key = next((v for k, v in SET_OVERRIDES.items() if h.startswith(k)), None)
                cur = (key or set_lessons(para), para, [])
            sets.append(cur)
        else:
            if cur is None:
                sys.exit("question text before the first set heading")
            cur[2].append(para)
    log, covered = [], collections.Counter()
    for key, head, body in sets:
        if key == "misc":
            covers, target, sub = GROUP_SETS[2][0], GROUP_SETS[2][1], GROUP_SETS[2][2]
        else:
            g = [gs for gs in GROUP_SETS if gs[0] == key]
            if g:
                covers, target, sub = g[0]
            elif len(key) == 1:
                covers, target, sub = key, key[0], QE_SUB
            else:
                sys.exit(f"unplanned group set {key}: {head}")
        if sub != "Miscellaneous Examples":
            for n in covers:
                covered[n] += 1
        body = renumber(body, log, head[8:])
        lessons[target].append(sub)
        lessons[target].extend(body)
        n_items = sum(1 for b in body if re.match(r"\d{1,3}\.\s", b))
        log.append(f"{head[8:60]!r:62} -> Lesson {target} under '{sub}' ({n_items} numbered items)")
    missing = [n for n in range(1, 34) if covered[n] == 0]
    double = [n for n in range(1, 34) if covered[n] > 1]
    log.append(f"{len(sets)} question sets; lessons with no set of their own: {missing}; "
               f"lessons covered twice: {double}")
    return log


def split_parts(paras, limit=TARGET_MAX):
    """Split a lesson's paragraphs into roughly equal parts under the limit,
    at paragraph boundaries, never just after a subheading or a colon."""
    total = sum(len(p.split()) for p in paras)
    if total <= limit:
        return [paras]
    k = -(-total // limit)
    target = total / k
    parts, cur, n = [], [], 0
    for i, p in enumerate(paras):
        cur.append(p)
        n += len(p.split())
        nxt = paras[i + 1] if i + 1 < len(paras) else None
        if (len(parts) < k - 1 and n >= target * (len(parts) + 1) - sum(0 for _ in ())
                and nxt is not None and not nxt.startswith("\t")
                and not nxt.startswith("[Figure") and not p.rstrip().endswith((":", ":—", "—"))
                and not p.startswith("\t")):
            parts.append(cur)
            cur = []
    parts.append(cur)
    return parts


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------

def index_lines(pages):
    """The two-column index (pp. 332-340), column by column: each line
    tagged start (a headword at the column margin) or cont (indented)."""
    out = []
    for leaf in range(INDEX_FIRST_LEAF, 365):
        lines = raw_lines(pages, leaf)
        mid = pages[leaf]["w"] / 2
        lines = [x for x in lines if not re.match(r"^\s*(INDEX\.?|[\dSs3]{3}\.?)\s*$", x["text"])
                 and not re.search(r"AND CONCISE VOCABULARY|PHILOSOPHICAL TERMS|PRINTED|Clay|Suffolk|Bungay", x["text"])]
        for col in (0, 1):
            cl = [x for x in lines if ((x["l"] + x["r"]) / 2 < mid) == (col == 0)]
            if not cl:
                continue
            left = sorted(x["l"] for x in cl)[len(cl) // 5]
            for x in sorted(cl, key=lambda x: x["t"]):
                x["kind"] = "start" if x["l"] - left < 22 else "cont"
                x["leaf"] = leaf
                out.append(x)
    return out


def index_entries(lines):
    entries = []
    for x in lines:
        if x["kind"] == "start" or not entries:
            entries.append([x["text"]])
        else:
            entries[-1].append(x["text"])
    return [tidy(join_lines(e)) for e in entries]


PAGE_REF = re.compile(r"(?:[,;:]?\s*(?:pp?\.\s*)?[\d'IiloOS]{0,2}\d[\d'IiloOSa]{0,2}(?:\s*[—–-]\s*[\dIilo]{1,3})?)+\.?\s*$")


# index entries about a person's works, not a term: pointers, not definitions
VOCAB_DROP = ("Bentham, George", "Bools, George", "Herschel, Sir J.")


def vocabulary(entries):
    """Split the index into entries that DEFINE (kept, page numbers off)
    and entries that only point (dropped)."""
    keep, drop = [], []
    for e in entries:
        body = e
        # page references anywhere: ", 123", ", 12-3", "; Third, 245"
        stripped = re.sub(r"(?<=[,;:])\s*(?:pp?\.\s*)?[\d'Iilo]{1,3}(?:\s*[—–-]\s*[\d'Iilo]{1,3})?(?=[,;.]|\s*$)", "", body)
        stripped = re.sub(r"[,;:]\s*(?=[,;.]|$)", "", stripped).strip(" ,;")
        head, _, rest = stripped.partition(",")
        # a definition is a phrase; a pointer is a list of short sub-entries
        # ("Accident, fallacy of; the predicable")
        longest = max((len(re.findall(r"[A-Za-z]{2,}", seg)) for seg in re.split(r"[;:]", rest)), default=0)
        defines = re.match(r"^\S+(?: \S+){0,4} (is|are|imply|assigns|denotes|means)\b", e)
        if ((longest >= 5 or defines) and not e.startswith(VOCAB_DROP)):
            keep.append(stripped.rstrip(" ,;") + ("" if stripped.endswith(".") else "."))
        else:
            drop.append(e)
    return keep, drop


def report_index(ilines):
    entries = index_entries(ilines)
    keep, drop = vocabulary(entries)
    print(f"  index: {len(entries)} OCR entries read; {len(keep)} look like definitions, "
          f"{len(drop)} are page references only; VOCABULARY holds {len(VOCABULARY)} "
          f"(transcribed from the page images)")


def write_out(texts):
    out = BOOK / "chapters"
    out.mkdir(exist_ok=True)
    for f in out.glob("*.txt"):
        f.unlink()
    manifest, n = [], 0
    for key, paras in texts.items():
        if key == "preface":
            title = PREFACE_TITLE
        elif key == "vocab":
            title = VOCAB_TITLE
        else:
            title = f"Lesson {key}: {TITLES[key]}"
        parts = split_parts(paras)
        for i, part in enumerate(parts, 1):
            head = [title] + ([f"(Part {i} of {len(parts)})"] if len(parts) > 1 else [])
            body = "\n\n".join(part)
            fname = f"{n:03d}.txt"
            (out / fname).write_text("\n\n".join(head) + "\n\n" + body.rstrip() + "\n")
            entry = {"file": fname, "title": title, "part": i, "of": len(parts),
                     "words": len(body.split())}
            if i == 1 and key in PART_BEFORE:
                entry["part_before"] = PART_BEFORE[key]
            if isinstance(key, int):
                entry["lesson"] = key
            manifest.append(entry)
            n += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"  wrote {n} files, {sum(m['words'] for m in manifest)} words")


def build_events(pages, regions, witness_pages):
    out = []
    for leaf in PREFACE_LEAVES + BODY_LEAVES:
        mode = "qe" if QE_FIRST_LEAF <= leaf < INDEX_FIRST_LEAF else "prose"
        if leaf >= INDEX_FIRST_LEAF:
            continue
        ev = page_events(pages, leaf, mode, regions, witness_pages)
        for kind, x in ev:
            if kind == "line" and leaf == QE_FIRST_LEAF and re.match(r"\s*QUESTIONS", x["text"]):
                x["kind"] = "qsection"
        out.append((leaf, ev))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figures", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    ensure_scan()
    pages = load_abbyy()
    pn = page_numbers()
    check_leaf_map(pn)
    regs = regions()
    witness_pages = {}
    if args.figures:
        cut_figures(pages, regs)
    if args.debug:
        rep = []
        for r in regs:
            inside = [x["text"] for x in raw_lines(pages, r["leaf"])
                      if x not in raw_lines(pages, r["leaf"], [r["box"]])]
            rep.append(f"== {r['id']} leaf {r['leaf']} {r['y0']}-{r['y1']}")
            rep.extend("   " + t for t in inside)
        (SRC / "regions_dropped.txt").write_text("\n".join(rep) + "\n")
    events = build_events(pages, regs, witness_pages)
    # the vote, on every OCR line (body and footnotes) in reading order
    lines = [x for _, ev in events for kind, x in ev if kind == "line"]
    lines += [ln for _, ev in events for kind, x in ev if kind == "foot" for ln in x]
    ilines = index_lines(pages)
    lines += ilines
    stream = [x["text"].split() for x in lines]
    vlog = []
    stats = vote(stream, dictionary(), vlog)
    for x, toks in zip(lines, stream):
        x["text"] = " ".join(toks)
    (SRC / "vote_log.txt").write_text("\n".join(vlog) + "\n")
    for x in lines:
        x["text"] = clean_line(x["text"])
    for old, new in LINE_FIXES:
        hit = [x for x in lines if old in x["text"]]
        if not hit:
            sys.exit(f"LINE_FIXES entry no longer matches: {old!r}")
        for x in hit:
            x["text"] = x["text"].replace(old, new)
    print("vote:", dict(stats))
    count_words(x["text"] for x in lines)
    DICT.update(dictionary())
    sections, alog = assemble(events)
    for a in alog:
        print("  note:", a)
    # ---- render every section, then the fixes over the whole text
    order = ["preface"] + list(range(1, 34))
    missing = [k for k in order + ["qe"] if k not in sections]
    if missing or len([k for k in sections if isinstance(k, int)]) != 33:
        sys.exit(f"structure: sections missing {missing}; have {list(sections)}")
    chunks, owner = [], []
    for k in order + ["qe"]:
        for c in render(sections[k]):
            chunks.append(c)
            owner.append(k)
    chunks, owner = apply_joins(chunks, owner)
    texts = collections.OrderedDict((k, []) for k in order + ["qe"])
    for k, c in zip(owner, chunks):
        texts[k].append(c)
    # SOURCE_FIXES section by section (a fix may split or merge paragraphs)
    joined = {k: "\n\n".join(v) for k, v in texts.items()}
    missing = []
    for old, new in SOURCE_FIXES:
        hit = False
        for k in joined:
            if old in joined[k]:
                joined[k] = joined[k].replace(old, new)
                hit = True
        if not hit:
            missing.append(old)
    if missing:
        sys.exit("SOURCE_FIXES entries no longer match:\n  " + "\n  ".join(map(repr, missing)))
    texts = collections.OrderedDict((k, v.split("\n\n")) for k, v in joined.items())
    # preface: the scan's own heading line and the INTRODUCTION over Lesson I
    pre = [c for c in texts["preface"] if c.strip() not in ("PREFACE", "INTRODUCTION")]
    texts["preface"] = pre
    qlog = fold_questions(texts, texts.pop("qe"))
    for line in qlog:
        print("  Q&E:", line)
    vocab = [f"{h}, {d}" if not d.startswith(("(", "=", "is ", "are ", "of ", "or ", "imply", "assigns"))
             else f"{h} {d}" for h, d in VOCABULARY]
    texts["vocab"] = vocab
    write_out(texts)
    report_index(ilines)

    if args.debug:
        dbg = []
        for k, paras in sections.items():
            dbg.append(f"=================== {k}")
            dbg.extend(render(paras))
        keep, drop = vocabulary(index_entries(ilines))
        dbg.append("=================== vocabulary")
        dbg.extend(keep)
        (SRC / "index_dropped.txt").write_text("\n".join(drop) + "\n")
        (SRC / "debug_raw.txt").write_text("\n\n".join(dbg) + "\n")
        dbg = apply_source_fixes(dbg)
        (SRC / "debug.txt").write_text("\n\n".join(dbg) + "\n")


if __name__ == "__main__":
    main()
