"""Perlman, Against His-story, Against Leviathan! (1983) -> chapters/ and
modern_chapters/ (a restored edition).

    python3 perlman/prep.py            # build
    python3 perlman/prep.py --report   # also print every adjudication

THE WORDS ARE THE PRINT'S. Three witnesses, sharing no keystrokes:
  T  The Anarchist Library's transcription (_src/tal.muse, from a 2007
     blog), which carries the paragraphing, italics, block quotations and
     section breaks, and which drops or changes a word about every 125
     ("a network [of] computer centers", "a book [he] called"; both
     checked on the page).
  A  ABBYY's OCR of Archive.org's scan of Black & Red's 2010 third printing
     (_src/djvu.xml, with each word's leaf and position).
  B  Tesseract's OCR of the same printing (_src/ocrB.txt, Archive.org
     against-his-story-against-leviathan-edit-fredy-perlman). A and B
     differ in only ~130 places and never share a misreading, so where
     they AGREE against T, that is the printing.
The vote, per difference between T and A:
  A == B          the print's reading (A's surface, T's typography)
  T == B          A misread; keep T
  otherwise       CHECKED ON THE PAGE: listed in PAGE_READINGS by hand
Punctuation gets the same vote on words whose letters already agree.

STRUCTURE IS T'S, CHECKED AGAINST THE PRINT'S LAYOUT: a paragraph the
print indents on both sides is a block quotation whatever T says.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from scan_diff import opcodes  # noqa: E402

REPORT = "--report" in sys.argv


def key(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ---------------------------------------------------------------- witness T
def parse_tal():
    """[(chapter_no, [block])], block = ("P"|"Q", [line]) or ("HR",) or
    ("SIGN", [line]); a line is a list of surface tokens."""
    t = (HERE / "_src/tal.muse").read_text()
    t = re.sub(r"^#.*\n", "", t, flags=re.M)
    t = re.sub(r"</?em>", "*", t)
    t = t.replace("<sup>", "").replace("</sup>", "")
    t = t.replace("&amp;", "&")
    chapters = []
    for m in re.finditer(r"^\*\* (\d+)\n(.*?)(?=^\*\* \d+\n|\Z)", t, re.S | re.M):
        n, body = int(m.group(1)), m.group(2)
        blocks = []
        pos = 0
        for q in re.finditer(r"<quote>\n(.*?)\n</quote>", body, re.S):
            blocks += prose(body[pos:q.start()])
            inner = q.group(1).strip()
            lines = [l.strip() for l in re.split(r"<br>\s*\n?|\n", inner) if l.strip()]
            if lines == ["Detroit, March 1983"]:
                blocks.append(("SIGN", [lines[0].split()]))
            else:
                blocks.append(("Q", [l.split() for l in lines]))
            pos = q.end()
        blocks += prose(body[pos:])
        chapters.append((n, blocks))
    assert [c[0] for c in chapters] == list(range(1, 25)), [c[0] for c in chapters]
    for (n, bi), (want_first, kind) in STRUCT_FIXES.items():
        blk = chapters[n - 1][1][bi]
        assert " ".join(blk[1][0]).startswith(want_first), (n, bi, blk[1][0][:6])
        chapters[n - 1][1][bi] = (kind, [sum(blk[1], [])] if kind == "P" else blk[1])
    return chapters


# T's quotation markup against the print's layout (bold, indented both
# sides), read on the page: leaves 95, 180, 181.
STRUCT_FIXES = {
    (8, 57): ("Philip himself", "P"),           # Perlman's prose, not a quotation
    (16, 45): ("Turn the weapons", "Q"),        # Urban's proclamation
    (16, 59): ("Still more dreadful", "Q"),     # the Archbishop of Tyre
    (16, 60): ("the Archbishop tells,", "P"),
}

# Seams the token vote cannot express, read on the page.
TEXT_FIXES = [
    ("cited.) by\n\nTurner].", "cited by Turner]."),    # leaf 181: "[in the words of ..., cited by Turner]."
    # leaf 59: a sentence T dropped that the vote's insert rule missed;
    # found by crosscheck.py, the second reading
    ("mutilations on the rebels. So still", "mutilations on the rebels. This news did not embolden potential rebels. So still"),
    # T's slips inside words the vote saw as equal, found by the chapter
    # readers and checked against both OCRs (neither prints any of them)
    ("The Persians’ find", "The Persians find"),
    ("Peter and Paul;: he", "Peter and Paul”: he"),
    ("protect hima long", "protect him along"),
    ("call sthe Church", "calls the Church"),
    ("Maghreb’s shore’s,", "Maghreb’s shores,"),
    ("their labor power. and", "their labor power and"),
    # paragraph seams the insertion step got wrong (leaves 150, 202)
    ("\n\nThe\n\nVisigoths are joined", "\n\nThe Visigoths are joined"),
    ("into similar culs-de-sac. Attacked\n\nand therefore", "into similar culs-de-sac.\n\nAttacked and therefore"),
]
# Perlman spells it Provençe throughout (leaves 191, 200, 209, 220).
RESPELL = [("Provence", "Provençe")]


def prose(s):
    out = []
    for para in re.split(r"\n\s*\n", s):
        p = para.strip()
        if not p:
            continue
        if p == "* * *":
            out.append(("HR",))
            continue
        assert "<" not in p, p[:80]
        out.append(("P", [p.split()]))
    return out


# ---------------------------------------------------------------- witness A
def scan_tokens():
    """[(surface, leaf, line_box, page_body)] in reading order, from the
    first epigraph to the dateline; page and chapter numbers dropped,
    line-end hyphens joined (the joined surface remembers its hyphen)."""
    x = (HERE / "_src/djvu.xml").read_text()
    out = []
    for leaf, page in enumerate(re.findall(r"<OBJECT.*?</OBJECT>", x, re.S)):
        lines = []
        for ln in re.findall(r"<LINE>(.*?)</LINE>", page, re.S):
            ws = re.findall(r'<WORD coords="([^"]*)"[^>]*>(.*?)</WORD>', ln, re.S)
            ws = [(tuple(map(int, c.split(","))), unescape(w.strip())) for c, w in ws if w.strip()]
            if not ws:
                continue
            text = " ".join(w for _, w in ws)
            if re.fullmatch(r"[\dIl]{1,3}\.?", text):
                continue                                # page or chapter number
            box = (min(c[0] for c, _ in ws), min(c[3] for c, _ in ws),
                   max(c[2] for c, _ in ws), max(c[1] for c, _ in ws))
            lines.append((box, [w for _, w in ws]))
        if not lines:
            continue
        lefts = sorted(b[0] for b, _ in lines)
        rights = sorted(b[2] for b, _ in lines)
        body = (lefts[len(lefts) // 4], rights[3 * len(rights) // 4])
        for box, words in lines:
            for w in words:
                out.append([w, leaf, box, body])
    # join line-end hyphenation: "perpet¬" + "rators"
    joined = []
    for tok in out:
        if joined and re.search(r"[A-Za-z][¬\-]$", joined[-1][0]) and tok[2] != joined[-1][2]:
            prev = joined[-1]
            prev[0] = prev[0][:-1] + "\u00ad" + tok[0]        # soft hyphen marks the join
            continue
        joined.append(tok)
    words = [t[0] for t in joined]
    s = next(i for i in range(len(words)) if words[i:i + 5] == ["And", "we", "are", "here", "as"])
    e = next(i for i in range(len(words) - 1, 0, -1) if words[i] == "1983" and words[i - 2].startswith("Detroit"))
    return joined[s:e + 1]


def unescape(w):
    return w.replace("&amp;", "&").replace("&apos;", "'").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")


# ---------------------------------------------------------------- witness B
def b_tokens():
    t = (HERE / "_src/ocrB.txt").read_text()
    i = t.find("And we are here as on a darkling")
    t = t[i:]
    lines = [l for l in t.split("\n") if not re.fullmatch(r"\s*[\dIl|]{1,3}\.?\s*", l)]
    t = re.sub(r"([A-Za-z])[¬\-]\s*\n\s*", "\\1\u00ad", "\n".join(lines))
    return t.split()


def surface_key(s):
    return key(s.replace("\u00ad", ""))


def run():
    chapters = parse_tal()
    # flatten T to tokens with structural addresses
    T = []          # (surface, (ci, bi, li, ti))
    for ci, (_, blocks) in enumerate(chapters):
        for bi, b in enumerate(blocks):
            if b[0] == "HR":
                continue
            for li, line in enumerate(b[1]):
                for ti, tok in enumerate(line):
                    T.append((tok, (ci, bi, li, ti)))
    A = scan_tokens()
    B = b_tokens()
    tk = [surface_key(s) for s, _ in T]
    ak = [surface_key(a[0]) for a in A]
    bk = [surface_key(b) for b in B]
    # T and B alignment: per T index, B index where equal
    t2b = {}
    breads = {}
    for tag, i1, i2, j1, j2 in opcodes(tk, bk):
        if tag == "equal":
            for d in range(i2 - i1):
                t2b[i1 + d] = j1 + d
        else:
            breads[(i1, i2)] = bk[j1:j2]
    new = {}        # T index -> replacement surfaces (list) for spans
    t2a = {}
    conflicts, agreed = [], []
    for tag, i1, i2, j1, j2 in opcodes(tk, ak):
        if tag == "equal":
            for d in range(i2 - i1):
                t2a[i1 + d] = j1 + d
            continue
        akeys = ak[j1:j2]
        if "".join(akeys) == "".join(tk[i1:i2]):
            # split/joined words only. Where B splits as A does, T ran two
            # words together or split one ("Thefederated"): the print's spacing
            if breads.get((i1, i2)) == akeys and len(akeys) != i2 - i1 and all(akeys):
                if len(akeys) < i2 - i1 and any("\u00ad" in A[j][0] for j in range(j1, j2)):
                    # T's two words are the print's line-end compound: the
                    # hyphen is real ("Iroquoian-speaking", "plague-decimated")
                    for j in range(j1, j2):
                        A[j][0] = A[j][0].replace("\u00ad", "-")
                agreed.append((i1, i2, j1, j2))
                new[(i1, i2)] = [A[j][0] for j in range(j1, j2)]
                continue
            # otherwise keep T's surfaces, map loosely
            for d in range(i2 - i1):
                t2a[i1 + d] = j1 + min(d, j2 - j1 - 1) if j2 > j1 else None
            continue
        b_same_as_t = all(i in t2b for i in range(i1, i2)) and (i1 == i2 and (i1 - 1) in t2b and i1 in t2b and t2b[i1] == t2b[i1 - 1] + 1 or i1 < i2)
        if breads.get((i1, i2)) == akeys:
            agreed.append((i1, i2, j1, j2))
            new[(i1, i2)] = [A[j][0] for j in range(j1, j2)]
            for d in range(i2 - i1):
                t2a[i1 + d] = j1 + min(d, max(0, j2 - j1 - 1)) if j2 > j1 else None
        elif b_same_as_t:
            for d in range(i2 - i1):
                t2a[i1 + d] = None
        else:
            conflicts.append((i1, i2, j1, j2, breads.get((i1, i2))))
    return chapters, T, A, B, t2a, t2b, new, agreed, conflicts


# Where T and both OCRs disagree, read on the page (thumbs via look.py).
# Keyed by T's reading and the scan leaf; None keeps T.
PAGE_READINGS = {
    ("*Society Against the State*", 15): "*La société contre l’état*",   # he gives Clastres' French title
    ("Çatal Höyük,", 22): None,                     # T right; OCR garbled the diacritics
    ("Yu,", 52): "Yü,",
    ("", 173): None,                                # OCR noise from the plate on leaf 174
    ("collorary:", 236): "corollary:",
    ("the", 242): "their",                          # "love for their Lords"
    ("Yhe", 247): "The",
    ("Kukulkan-Quetzaquatal", 256): "Kukulkan-Quetzalcóatl",
    ("Quetzaquatal", 256): "Quetzalcóatl",
    ("Quetzaquatal", 257): "Quetzalcóatl",
    ("Quetzaquatal’s", 258): "Quetzalcóatl’s",
    ("Colon", 260): "Colón",
    ("Colon", 264): "Colón",
    ("thay will", 273): "they",                     # "and they are determined"
    ("Gnadenhutten", 288): "Gnadenhütten",
}
# The print's accent on Quetzalcóatl and Colón is one smudged glyph that
# both OCRs misread; Colón takes an acute, so both are set acute.

# Both OCRs read the print's ç as g and lose some accents (checked on the
# page: Provençe is Perlman's own spelling, leaves 191-220).
OCR_SURFACE = {"Provenge": "Provençe", "Provenge,": "Provençe,", "Provengal": "Provençal",
               "fagades,": "façades,", "Bartolome": "Bartolomé"}

# The printer's plain misprints -- non-words where T spells the word -- are
# left corrected (RESTORED.md). Perlman's real forms stand: exercize,
# vulcanic, bodyless, Hiroshiman, ornamenters, moronization, Michaelangelo.
MISPRINTS = {"apprently": "apparently", "agiainst": "against", "himelf": "himself",
             "monpoly": "monopoly", "pre-Levianthanic": "pre-Leviathanic",
             "Mediterraneans’s": "Mediterranean’s"}


def clean_a(s):
    """An OCR surface as the print has it: a line-end join keeps its hyphen
    only where both halves are capitalised or T would hyphenate."""
    s = OCR_SURFACE.get(s, s)
    if "­" in s:
        a, b = s.split("­", 1)
        s = a + ("-" + b if b[:1].isupper() or (a.lower() in HYPHEN_HEADS) else b)
    return MISPRINTS.get(s.strip("“”‘’,.;:!?"), None) and s.replace(s.strip("“”‘’,.;:!?"), MISPRINTS[s.strip("“”‘’,.;:!?")]) or s


HYPHEN_HEADS = {"money", "pre", "self", "non", "anti", "semi", "half", "well", "ill", "co", "neo", "ex"}


def psig(s):
    s = s.replace("\u00ad", "").replace("*", "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"[A-Za-z0-9À-ÿ]", "", s)


def rebuild(t_surf, a_surf):
    """T's word with the print's punctuation: A's surface, T's italics and
    T's typographic quotes."""
    s = clean_a(a_surf).replace("'", "’")
    if t_surf.startswith("*") and not s.startswith("*"):
        s = "*" + s
    m = re.search(r"\*([^A-Za-z]*)$", t_surf)
    if m and "*" not in s[1:]:
        core = re.match(r"(.*?[A-Za-z0-9À-ÿ])([^A-Za-z0-9À-ÿ]*)$", s)
        s = core.group(1) + "*" + core.group(2) if core else s
    return s


def compose():
    chapters, T, A, B, t2a, t2b, new, agreed, conflicts = run()
    out = [s for s, _ in T]
    global_B = B                      # surface per T token
    before = {}                                  # T index -> tokens inserted before it
    after_block = {}                             # (ci, bi) -> tokens appended to that block
    log = []

    def place(i1, i2, surf, aidx=None):
        if i2 > i1:
            surf = list(surf)
            if surf:
                if out[i1].startswith("*") and not surf[0].startswith("*"):
                    surf[0] = "*" + surf[0]
                if out[i2 - 1].rstrip(".,;:!?’”").endswith("*") and "*" not in surf[-1]:
                    m = re.match(r"(.*?)([.,;:!?’”]*)$", surf[-1])
                    surf[-1] = m.group(1) + "*" + m.group(2)
            out[i1] = " ".join(surf)
            for i in range(i1 + 1, i2):
                out[i] = ""
            return
        # an insertion: before T[i1], unless T[i1] opens a block and the
        # print sets the run at the end of the block before
        ci, bi, li, ti = T[i1][1] if i1 < len(T) else T[-1][1]
        if i1 < len(T) and li == 0 and ti == 0 and i1 > 0:
            after_block.setdefault(T[i1 - 1][1][:2], []).extend(zip(surf, aidx or [None] * len(surf)))
        else:
            before.setdefault(i1, []).extend(surf)

    for i1, i2, j1, j2 in agreed:
        surf = [clean_a(A[j][0]) for j in range(j1, j2)
                if not re.fullmatch(r"[*•■►·]+", A[j][0])]    # the print's section bullets
        log.append(("vote", " ".join(s for s, _ in T[i1:i2]), " ".join(surf), A[j1][1] if j1 < len(A) else None))
        place(i1, i2, surf, list(range(j1, j2)))
    for i1, i2, j1, j2, br in conflicts:
        k = (" ".join(s for s, _ in T[i1:i2]), A[j1][1])
        assert k in PAGE_READINGS, f"unread conflict {k}"
        r = PAGE_READINGS[k]
        if r is not None:
            log.append(("page", k[0], r, k[1]))
            place(i1, i2, r.split())
    # punctuation: on words whose letters agree, the two OCRs outvote T --
    # but only for the marks OCR reads reliably; hyphens (line-end joins)
    # and quote styles stay T's.
    touched = {i for i1, i2, *_ in agreed for i in range(i1, i2)}
    for i, (s, _) in enumerate(T):
        j, k = t2a.get(i), t2b.get(i)
        if j is None or k is None or i in touched or not out[i]:
            continue
        tl, al, bl = (re.sub(r"[^A-Za-zÀ-ÿ]", "", x) for x in (s, A[j][0], B[k]))
        if al == bl != tl and al.lower() == tl.lower():
            new_s = re.sub(r"[A-Za-zÀ-ÿ]+", lambda m, it=iter(re.findall(r"[A-Za-zÀ-ÿ]+", A[j][0])): next(it, m.group()), s) \
                if len(re.findall(r"[A-Za-zÀ-ÿ]+", s)) == len(re.findall(r"[A-Za-zÀ-ÿ]+", A[j][0])) else s
            if new_s != s:
                log.append(("case", s, new_s, A[j][1]))
                out[i] = s = new_s
        ts, as_, bs = psig(s), psig(A[j][0]), psig(B[k])
        if as_ == bs != ts and not set(ts + as_) - set(",.;:!?[]()'/\\"):
            if ts.count("'") > as_.count("'"):
                continue                  # an apostrophe OCR lost, not the print
            if "..." in s or ts.count(".") > as_.count(".") and "(" not in ts + as_:
                continue                  # spaced ellipses, and periods: OCR tokenising
            new_s = rebuild(s, A[j][0])
            log.append(("punct", s, new_s, A[j][1]))
            out[i] = new_s
    for i, s in enumerate(out):
        if s and i not in {a for a, *_ in agreed}:
            fixed = clean_a(s) if s.strip("“”‘’,.;:!?*") in MISPRINTS else s
            if fixed != s:
                log.append(("misprint", s, fixed, None))
                out[i] = fixed
    return chapters, T, A, out, before, after_block, log, t2a


def starts_paragraph(A, j):
    """The print's paragraph opening: first word on its line, indented."""
    w, leaf, box, body = A[j]
    first = j == 0 or A[j - 1][2] != box
    return first and box[0] > body[0] + 25


def write():
    chapters, T, A, out, before, after_block, log, t2a = compose()
    # rebuild the blocks from the adjudicated tokens
    lines = {}
    for i, (s, addr) in enumerate(T):
        toks = before.get(i, []) + ([s] if False else [])
        lines.setdefault(addr[:3], []).extend(before.get(i, []) + ([out[i]] if out[i] else []))
    files = []
    for ci, (n, blocks) in enumerate(chapters):
        body = [f"Chapter {n}", "", "{PLATE c%s}" % "abcdefghijklmnopqrstuvwx"[n - 1], ""]
        for bi, b in enumerate(blocks):
            if b[0] == "HR":
                body += ["* * *", ""]
                continue
            ls = [" ".join(lines.get((ci, bi, li), [])) for li in range(len(b[1]))]
            extra = []
            if (ci, bi) in after_block:
                run_, paras = after_block[(ci, bi)], []
                for s, j in run_:
                    if j is not None and starts_paragraph(A, j):
                        paras.append([])
                    if paras:
                        paras[-1].append(s)
                    else:
                        ls[-1] += " " + s      # the print continues this block
                extra = [" ".join(p) for p in paras if p]
            ls = [re.sub(r"\s+", " ", l).strip() for l in ls]
            if b[0] == "P":
                body += [" ".join(ls), ""]
            elif b[0] == "Q":
                body += ["\n".join("\t" + l for l in ls), ""]
            elif b[0] == "SIGN":
                body += [ls[0], "", "{PLATE zz}", ""]       # the dateline, then the closing vignette
            for e in extra:
                body += [e, ""]
        text = "\n".join(body).rstrip() + "\n"
        for old, new_ in RESPELL:
            text = text.replace(old, new_)
        for old, new_ in TEXT_FIXES:
            if old in text:
                text = text.replace(old, new_)
                log.append(("text", old, new_, None))
        files.append(text)
    assert sum(k == "text" for k, *_ in log) == len(TEXT_FIXES), "a TEXT_FIX matched nothing"
    return files, log


# Perlman's acknowledgments, facing the title page (leaf 5), typed from
# the two OCRs, which agree but for "FinkeJ" (ABBYY) / "Finkel" (Tesseract,
# and the page).
FRONT = """Acknowledgments

{PLATE aa}

{PLATE ab}

*Many thanks to Lorraine Perlman, Jim O’Brien, Peter Rachleff, Jeff Gilbert, Kemal Orcan, Peter Werbe and Terri Finkel for their helpful suggestions and comments, to Millard Berry for donating darkroom supplies, to Steve Izma and friends at Dumont Press Graphix for lending their typesetting equipment, and to numerous unmentioned friends for their stimulation, encouragement, friendship and love.*

F.P.
"""


def captions():
    caps = {}
    for f in sorted((HERE / "captions").glob("*.txt")):
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                k, _, v = line.partition("\t")
                assert k not in caps, f"{k} captioned twice"
                caps[k.strip()] = v.strip()
    return caps


def emit(files):
    ids = [r["id"] for r in json.loads((HERE / "plates.json").read_text())]
    caps = captions() if (HERE / "captions").is_dir() else {}
    assert not set(caps) - set(ids), set(caps) - set(ids)
    texts = [FRONT] + files
    seen = re.findall(r"\{PLATE (\w+)\}", "".join(texts))
    assert sorted(seen) == sorted(ids), (sorted(set(ids) - set(seen)), sorted(set(seen) - set(ids)))
    manifest = []
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    for i, text in enumerate(texts):
        src = re.sub(r"\{PLATE (\w+)\}", r"[Figure \1]", text)
        mod = re.sub(r"\{PLATE (\w+)\}",
                     lambda m: f"[Figure {m.group(1)}: {caps[m.group(1)]}]" if m.group(1) in caps else f"[Figure {m.group(1)}]",
                     text)
        (HERE / "chapters" / f"{i:03d}.txt").write_text(src)
        (HERE / "modern_chapters" / f"{i:03d}.txt").write_text(mod)
        manifest.append({"file": f"{i:03d}.txt", "title": text.split("\n", 1)[0], "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    return len(caps), len(ids)


if __name__ == "__main__":
    files, log = write()
    described, total = emit(files)
    print(f"{described}/{total} plates captioned")
    print(len(files), "chapters,", sum(len(f.split()) for f in files), "words")
    import collections
    print(collections.Counter(k for k, *_ in log))
    if REPORT:
        for k, a, b, leaf in log:
            print(f"{k:8} leaf {leaf}: {a!r} -> {b!r}")
