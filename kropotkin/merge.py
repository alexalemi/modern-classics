"""Kropotkin, Mutual Aid: the word-by-word vote.

THE PIVOT IS THE PRINT. Witness A (UCLA's 1904 copy, ABBYY) supplies every
token in print order with its zone (body / note / heading), italics and
note-reference marks; B and C (the two Duke scans of the 1914 impression,
same plates) and T (Gutenberg #4341, the 1902 text, ASCII, no italics) are
aligned to A and vote on each place A might be wrong:

  T covers it (body and notes):   A==B keep A  |  T==B take T  |
                                  A==C keep A  |  T==C take T  |  B==C take B
  no T (summaries, the Appendix, 1904 additions):
                                  B==C != A take B  |  else keep A
  otherwise                       a CONFLICT, read on the page (PAGE_READINGS)

Because the pivot is the print, Kropotkin's 1904 revisions stand wherever
the two printings agree, and T only ever corrects A's misreadings.
Punctuation, capitals and accents get the same vote on tokens whose
letters already agree (T has lost every accent, so it never wins one).
"""
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import witnesses as W  # noqa: E402
from scan_diff import opcodes  # noqa: E402


def key(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("­", ""))


def norm_surface(s):
    s = s.replace("­", "")
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("„", '"'), ("—", "--"), ("–", "-")):
        s = s.replace(a, b)
    return s


# ------------------------------------------------------------------ A
def stream_a():
    """A's tokens in print order: dict(t, it, mark, zone, leaf, line, fs,
    lpos, page_left). Zones: body, quote, note, head. Line-end hyphens
    joined (a soft hyphen marks the join)."""
    pages = W.abbyy()
    toks = []
    prev_notes = False
    for lines in pages:
        lines = [l for i, l in enumerate(lines) if not W.is_head(l, i)]
        lines = [l for l in lines if not re.fullmatch(r"[\divxlcIl]{1,4}", " ".join(w for w, *_ in l["toks"]).strip())]
        if not lines:
            continue
        # LINE SPACING, not font size, tells body from small type: ABBYY's
        # sizes drift within a page (11 to 12.5 for one body), but body
        # lines sit ~75px apart and quotations and notes ~53-57px.
        tops = [l["box"][1] for l in lines]
        lead = []
        for i in range(len(lines)):
            gaps = [g for g in ((tops[i + 1] - tops[i]) if i + 1 < len(lines) else None,
                                (tops[i] - tops[i - 1]) if i > 0 else None) if g is not None and g > 0]
            lead.append(min(gaps) if gaps else 75)
        # "small" is relative to the page: the Appendix is set in small type
        # throughout, and its own notes are smaller still
        ls = sorted(lead)
        med = ls[3 * len(ls) // 4]      # body spacing, even on a page half notes
        small = [ld < min(64, med * 0.86) for ld in lead]
        notey = [small[i] and lines[i]["fs"] <= 10.25 or lines[i]["toks"][0][2] for i in range(len(lines))]
        body_fs = 12.0
        lefts = sorted(l["box"][0] for i, l in enumerate(lines) if not small[i])
        left = lefts[len(lefts) // 4] if lefts else lines[0]["box"][0]
        # notes: within the trailing run of small-type lines at the foot,
        # from the first line that opens on a note number (lines before it
        # are a quotation ending the page); a run with no number is a note
        # continued from the page before only if it is in note-size type
        s = len(lines)
        while s > 0 and (small[s - 1] or lines[s - 1]["toks"][0][2]):
            s -= 1
        opener = next((i for i in range(s, len(lines))
                       if lines[i]["toks"][0][2] or (re.fullmatch(r"[\d*†]{1,2}", lines[i]["toks"][0][0])
                                                      and lines[i]["fs"] <= 10.75)), None)
        if opener is not None:
            k = opener
        elif s < len(lines) and prev_notes and all(lines[i]["fs"] <= 10.75 for i in range(s, len(lines))):
            k = s
        else:
            k = len(lines)
        # ABBYY sometimes sizes a note like the body; a line near the foot
        # that OPENS on a superscript number is a note all the same
        for i in range(len(lines) - 1, max(-1, len(lines) - 12), -1):
            if lines[i]["toks"][0][2] and i > 0:
                k = min(k, i)
        if k < len(lines):
            first = lines[k]["toks"][0][0]
            numbered = bool(re.match(r"^[\d*†Il]{1,3}$", first)) or lines[k]["toks"][0][2]
            if " ".join(w for w, *_ in lines[k]["toks"]).startswith("Bromley"):
                k = len(lines)                       # the Introduction's signature
            elif not numbered and not prev_notes:
                k = len(lines)
        prev_notes = k < len(lines)
        # headings: lines before the first body line on a page that
        # carries CHAPTER / INTRODUCTION / CONCLUSION / APPENDIX
        def caps(l):
            s = "".join(w for w, *_ in l["toks"])
            return s.upper() == s and any(c.isalpha() for c in s)
        first_body = next((i for i, l in enumerate(lines)
                           if not small[i] and 10.75 <= l["fs"] <= 13 and not caps(l)), 0)
        txt0 = " ".join(w for l in lines[:max(first_body, 1)] for w, *_ in l["toks"])
        opening = bool(re.search(r"\b(CHAPTER|INTRODUCTION|CONCLUSION|APPENDIX)\b", txt0)) and first_body > 0
        for li, l in enumerate(lines):
            if li >= k:
                zone = "note"
            elif opening and li < first_body:
                zone = "head"
            elif small[li]:
                zone = "quote"
            else:
                zone = "body"
            for ti, (t, it, mark) in enumerate(l["toks"]):
                toks.append({"t": t, "it": it, "mark": mark, "zone": zone, "leaf": l["leaf"],
                             "line": (l["leaf"], li), "lpos": ti, "l": l["box"][0], "left": left,
                             "fs": l["fs"], "body_fs": body_fs})
    # the book proper: from the Introduction's first words to the Index
    s = next(i for i in range(len(toks)) if toks[i]["t"] == "Two" and toks[i + 1]["t"] == "aspects")
    app0 = next(i for i in range(s, len(toks)) if toks[i]["t"] == "APPENDIX" and toks[i]["zone"] == "head")
    # the Index opens on a line holding only "INDEX"; stop there
    e = next(i for i in range(app0, len(toks)) if toks[i]["t"] == "INDEX"
             and toks[i - 1]["line"] != toks[i]["line"] and toks[i + 1]["line"] != toks[i]["line"])
    toks = toks[s:e]
    app = next(i for i, x in enumerate(toks) if x["t"] == "APPENDIX" and x["zone"] == "head")
    for x in toks[app:]:
        if x["zone"] in ("body", "quote", "head"):
            x["zone"] = "app" if x["zone"] != "head" else "head"
        x["appendix"] = True
    return toks


def stream_djvu(name):
    pages = W.djvu(name)
    toks = []
    for lines in pages:
        lines = [l for i, l in enumerate(lines) if not W.is_head(l, i)]
        lines = [l for l in lines if not re.fullmatch(r"[\divxlcIl]{1,4}", " ".join(w for w, *_ in l["toks"]).strip())]
        for li, l in enumerate(lines):
            for t, *_ in l["toks"]:
                toks.append({"t": t, "line": (l["leaf"], li), "leaf": l["leaf"], "box": l["box"]})
    out = []
    for tok in toks:
        prev = out[-1] if out else None
        if prev and prev["line"] != tok["line"] and re.search(r"[A-Za-z][-¬]$", prev["t"]) and tok["t"][:1].isalpha():
            prev["t"] = prev["t"][:-1] + "­" + tok["t"]
            continue
        out.append(tok)
    # the print spaces ; : ! ? and some quotes off their word, and djvu
    # keeps them as words of their own: attach them as ABBYY does
    merged = []
    for k, tok in enumerate(out):
        s = tok["t"]
        if merged and re.fullmatch(r"[;:!?,.)\]”’]+", s):
            merged[-1]["t"] += s
            continue
        if merged and s in ('"', "'") and re.search(r"[,.;:!?]$", merged[-1]["t"]):
            merged[-1]["t"] += s
            continue
        if re.fullmatch(r"[“‘(\[\"']+", s) and k + 1 < len(out):
            out[k + 1]["t"] = s + out[k + 1]["t"]
            continue
        merged.append(tok)
    return merged


# ------------------------------------------------------------------ T
TSTRUCT = {}
ORACLE_CHANGED = []
AB_OVER_T = []


def stream_t():
    """(body_tokens, note_tokens) from Gutenberg's plain text: markers
    "(n)" removed from the body, "n. " prefixes from the notes. The
    structure goes to TSTRUCT: "refs" = [(body index the marker follows,
    note id)], "notes" = {note id: (start, end) in note tokens}, a note id
    being (chapter ordinal, number)."""
    t = (HERE / "_src/pg4341.txt").read_text()
    t = t[t.find("INTRODUCTION\n"):t.find("End of the Project Gutenberg")]
    body, notes, refs, spans = [], [], [], {}
    chap = 0
    for pi, part in enumerate(re.split(r"\nNOTES:\n", t)):
        if pi > 0:
            m = re.search(r"\n(CHAPTER [IVX]+|CONCLUSION)\n", part)
            nb, part = (part[:m.start()], part[m.start():]) if m else (part, "")
            for nm in re.finditer(r"^(\d+)\. (.*?)(?=^\d+\. |\Z)", nb, re.M | re.S):
                s = len(notes)
                notes += nm.group(2).split()
                spans[(chap, int(nm.group(1)))] = (s, len(notes))
            chap += 1
        part = re.sub(r"^(CHAPTER [IVX]+|INTRODUCTION|CONCLUSION)\s*$", " ", part, flags=re.M)
        for tok in part.split():
            ms = re.findall(r"\((\d+)\)", tok)
            core = re.sub(r"\(\d+\)", "", tok)
            if core:
                body.append(core)
            for n in ms:
                refs.append((len(body) - 1, (chap, int(n))))
    TSTRUCT.update(refs=refs, notes=spans)
    return body, notes


# ------------------------------------------------------------------ alignment helpers
def same_letters(x, y):
    """The same letters in the same case, accents aside: the punctuation
    vote may change marks and diacritics, never a letter or a capital."""
    strip = lambda s: re.sub(r"[^A-Za-z0-9]", "", "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"))
    return strip(x) == strip(y)


def anchors(ak, bk):
    """A index -> B index for equal runs."""
    m = {}
    for tag, i1, i2, j1, j2 in opcodes(ak, bk):
        if tag == "equal":
            for d in range(i2 - i1):
                m[i1 + d] = j1 + d
    return m


def reading(m, other, j1, j2):
    """The other witness's tokens for A's span [j1, j2), when both ends
    are anchored; None when the alignment cannot say."""
    if (j1 - 1) not in m and j1 > 0:
        return None
    if j2 not in m and j2 < len(m) + 10**9:
        if j2 not in m:
            return None
    lo = m[j1 - 1] + 1 if j1 > 0 else 0
    hi = m[j2]
    return other[lo:hi] if hi >= lo else None


def oracle(A, T_body, T_notes):
    """Relabel A's zones from Gutenberg, which keeps body and notes apart:
    a run of 4+ consecutive tokens matching a Gutenberg note is note text,
    one matching the body is body. Done chapter by chapter (the chapter
    heads split A; TSTRUCT's note ids split T's notes), then each LINE takes
    the majority label of its matched tokens. Lines Gutenberg does not
    have (the 1904 additions) keep their layout zone."""
    import difflib
    chap_of_a, c = [], -1
    for i, a in enumerate(A):
        if a["zone"] == "head" and a["t"] in ("CHAPTER", "CONCLUSION") and (i == 0 or A[i - 1]["zone"] != "head"):
            c += 1
        chap_of_a.append(c)
    # T notes by chapter: Gutenberg's first NOTES block follows Chapter I
    # (the Introduction has none), so note chapter 0 is A's chapter 0
    tn_by_chap = {}
    for (ch, n), (s0, e0) in TSTRUCT["notes"].items():
        tn_by_chap.setdefault(ch, []).append((s0, e0))
    label = {}
    for ch, spans in tn_by_chap.items():
        achap = ch
        idx = [i for i, a in enumerate(A) if chap_of_a[i] == achap and a["zone"] not in ("head", "app")
               and not a["mark"] and not a.get("appendix")]
        tk = [key(x) for s0, e0 in sorted(spans) for x in T_notes[s0:e0]]
        ak = [key(A[i]["t"]) for i in idx]
        sm = difflib.SequenceMatcher(None, ak, tk, autojunk=False)
        for blk in sm.get_matching_blocks():
            if blk.size >= 4:
                for d in range(blk.size):
                    label[idx[blk.a + d]] = "note"
    by_line = {}
    for i, a in enumerate(A):
        if a["zone"] in ("head", "app") or a.get("appendix"):
            continue
        by_line.setdefault(a["line"], []).append(i)
    changed = 0
    for ln, ids in by_line.items():
        votes = [label.get(i) for i in ids if not A[i]["mark"]]
        n = sum(v == "note" for v in votes)
        if n * 2 > len(votes):
            want = "note"
        elif n == 0 and any(A[i]["zone"] == "note" for i in ids):
            # layout called it a note but Gutenberg's notes do not have it:
            # body if Gutenberg's body has the line, else leave it
            want = None
        else:
            want = None
        if want == "note":
            for i in ids:
                if A[i]["zone"] != "note":
                    A[i]["zone"] = "note"
                    changed += 1
    return changed


# Conflicts read on the page (Duke's scan; crops via conflicts.py). Keyed by
# A's reading and A's leaf; the value replaces A's span ("" deletes, None
# keeps A). The print sets æ, ç, accents and old German forms that every
# OCR reads differently and Gutenberg's ASCII text has lost.
PAGE_READINGS = {
    ("animates,", 15): "animales,", ("I'association pour", 15): "l'association pour",
    ("mediaeval", 20): "mediæval", ("Kentt", 22): "Kent,",
    ("(Viverridce)", 63): "(*Viverridæ*)", ("(Afustelidce)", 63): "(*Mustelidæ*)",
    ("(C/iauna ckavarria),", 79): "(*Chauna chavarria*),", ("savissima)", 93): "*sævissima*)",
    ("I877.", 95): "1877.", ("scholcz", 160): "*scholæ*", ("fof", 168): "*çof*",
    ("schola,", 178): "*scholæ*,", ("schola— kings,", 180): "*scholæ*—kings,", ("schola;", 182): "*scholæ*;",
    ("schola", 188): "*scholæ*", ("(Bohemices", 189): "(*Bohemicæ*", ("fof:", 194): "*çof*:", ("fof", 194): "*çof*",
    ("vnd richeri2)", 204): "*vnd richer*)",            # old German, as printed
    ("sous-pr£fe£s", 221): "sous-préfet's", ("Eiablissemenfs", 224): "Établissements",
    ("djemmdd].", 267): "*djemmâa*].", ("arttl—makes", 295): "*artél*—makes",
    ("arttls", 295): "*artéls*", ("artdl", 295): "*artél*", ("arUls,", 296): "*artéls*,", ("artSl.", 296): "*artél*.",
    ("#r/^/-member", 296): "*artél*-member", ("arttl", 297): "*artél*", ("js.", 311): "7s.", ("165-.", 312): "16s.",
    ("Ge'neve, 1810; re\u00adprinted as Les fourmis indigenes", 35): "Génève, 1810; reprinted as *Les fourmis indigènes*",
    ("Ddmidoff s", 45): "Démidoff's", ("Jdger", 69): "Jäger", ("See Appendix VII.", 109): None,
    ("revolution", 110): "l'évolution", ("'875", 110): "1875.", ("ii.", 115): "11.",
    ("Soti'ete (?Anthropologie,", 116): "Société d'Anthropologie,", ("Waltz's", 127): "Waitz's",
    ("Geographic Universelltt", 133): "Géographie Universelle,", ("franfais:", 145): "français:",
    ("fancien", 145): "l'ancien", ("Studteri),", 146): "Studien),", ("§", 155): None,
    ("d'Italic,", 178): "d'Italie,", ("solidi,", 179): None, ("walls.", 183): None,
    ("Gcschichte", 183): "Geschichte", ("surFhistoire", 184): "sur l'histoire", ("d 1 Italic,", 190): "d'Italie,",
    ("franfaises;", 191): "françaises;", ("XIP", 192): "XIIe", ("fhistoire", 200): "l'histoire",
    ("franfaises,", 200): "françaises,", ("/. c.t", 201): "l. c.,", ('I"Italic,', 203): "l'Italie,",
    ("I Industrie", 205): "l'Industrie", ("XlVme", 205): "XIVme", ("FItalie", 206): "l'Italie",
    ("stecle", 206): "siècle", ("Fancien rtgime,", 207): "l'ancien régime,", ("Alterthiimer", 213): "Alterthümer",
    ("Ib'nsystemets", 217): "lönsystemets", ("jFranfais,", 239): "Français,", ("Wiedertdufer,", 248): "Wiedertäufer,",
    ("FAnrien", 254): "l'Ancien", ("", 260): None,     # Gutenberg's Slater note is from a later edition (1907)
    ("Obsc/rina),", 273): "*Obschina*),", ("", 290): "the", ("iBs.", 291): "18s.", ("i*.", 291): "1s.",
    ("43 l M?-), gi", 291): "431 *seq.*), gi", ("18,437,5007.; 3,675,0007.", 295): "18,437,500l.; 3,675,000l.",
    ("getneinnutzlicher", 304): "gemeinnützlicher",
    ("corn\u00admit", 243): "commit",            # "com-" | the page's notes | "mit"
    ("See Appendix X.", 199): None,             # the print's note; Gutenberg has "None"
    ("Strassburg 1 s Bliithe ;", 222): "Strassburg's Blüthe;",
    ("Strassburg 1 s Bliithe;", 222): "Strassburg's Blüthe;",
}


def page_reading(span, leaf):
    """PAGE_READINGS lookup: exact, else a key on the same leaf that opens
    the span (long spans are keyed by their opening). False = no reading."""
    if (span, leaf) in PAGE_READINGS:
        return PAGE_READINGS[(span, leaf)]
    hits = [k for k in PAGE_READINGS if k[1] == leaf and k[0] and span.startswith(k[0]) and len(k[0]) >= 12]
    if len(hits) == 1:
        r = PAGE_READINGS[hits[0]]
        return None if r is None else r + span[len(hits[0][0]):]
    return False


def attach_punct(A):
    """UCLA's OCR also keeps the print's spaced ; : ! ? and quotes as words
    of their own; attach them to their word, as for the djvu streams, so
    the witnesses compare word for word."""
    out = []
    for k, a in enumerate(A):
        s = a["t"]
        if a["mark"]:
            out.append(a)
            continue
        if out and not out[-1]["mark"] and re.fullmatch(r"[;:!?,.)\]”’]+", s) and out[-1]["zone"] == a["zone"]:
            out[-1]["t"] += s
            continue
        if out and not out[-1]["mark"] and s in ('"', "'") and re.search(r"[,.;:!?]$", out[-1]["t"]):
            out[-1]["t"] += s
            continue
        if re.fullmatch(r"[“‘(\[\"']+", s) and k + 1 < len(A) and not A[k + 1]["mark"] and A[k + 1]["zone"] == a["zone"]:
            A[k + 1]["t"] = s + A[k + 1]["t"]
            continue
        out.append(a)
    return out


def join_hyphens(A):
    """Line-end hyphenation, joined AFTER the zones are settled: a token
    ending in a hyphen at a line end joins the next token OF THE SAME ZONE,
    skipping notes and references between (a body word broken at the foot
    of a page resumes after the page's notes: "com-" ... "mit"). A soft
    hyphen marks the join; prep decides whether the hyphen was real."""
    zone_of = lambda a: "text" if a["zone"] in ("body", "quote") else a["zone"]
    drop = set()
    for i, a in enumerate(A):
        if i in drop or a["mark"] or not re.search(r"[A-Za-zÀ-ÿ][-¬]$", a["t"]):
            continue
        j = i + 1
        while j < len(A) and (A[j]["mark"] or zone_of(A[j]) != zone_of(a)) and j - i < 400:
            j += 1
        if j >= len(A) or A[j]["line"] == a["line"] or not A[j]["t"][:1].isalpha():
            continue
        if j > i + 1 and A[j]["leaf"] == a["leaf"]:
            continue                    # skipped notes only across a page break
        a["t"] = a["t"][:-1] + "\u00ad" + A[j]["t"]
        a["it"] = a["it"] or A[j]["it"]
        drop.add(j)
    return [a for k, a in enumerate(A) if k not in drop]


def run(report=False):
    A = stream_a()
    T_body0, T_notes0 = stream_t()
    ORACLE_CHANGED.append(oracle(A, T_body0, T_notes0))
    A = attach_punct(join_hyphens(A))
    B = stream_djvu("mutualaidfactoro1902krop_djvu.xml")
    C = stream_djvu("mutualaid01krop_djvu.xml")
    ak = [key(a["t"]) for a in A]
    bk = [key(b["t"]) for b in B]
    ck = [key(c["t"]) for c in C]
    mB, mC = anchors(ak, bk), anchors(ak, ck)
    T_body, T_notes = stream_t()
    out = [a["t"] for a in A]          # final surface per A index ("" = deleted)
    ins = {}                            # A index -> tokens inserted before it
    log, conflicts = [], []
    covered = set()
    for zone_set, T in (({"body", "quote"}, T_body), ({"note"}, T_notes)):
        idx = [i for i, a in enumerate(A) if a["zone"] in zone_set and not a["mark"] and not a.get("appendix")]
        sub = [ak[i] for i in idx]
        tk = [key(x) for x in T]
        tmap = TSTRUCT.setdefault("body2a" if "body" in zone_set else "note2a", {})
        for tag, i1, i2, j1, j2 in opcodes(sub, tk):
            if tag == "equal":
                for d in range(i2 - i1):
                    covered.add(idx[i1 + d])
                    A[idx[i1 + d]]["T"] = T[j1 + d]
                    tmap[j1 + d] = idx[i1 + d]
                continue
            aspan = idx[i1:i2]
            tspan = T[j1:j2]
            if not tspan:
                continue                      # A has words T lacks: the scans decide
            if "".join(sub[i1:i2]) == "".join(key(x) for x in tspan):
                continue                      # split/joined only
            lo, hi = (aspan[0], aspan[-1] + 1) if aspan else (idx[i1] if i1 < len(idx) else len(A), None)
            if hi is None:
                hi = lo
            b = reading(mB, B, lo, hi)
            c = reading(mC, C, lo, hi)
            bks = [key(x["t"]) for x in b] if b is not None else None
            cks = [key(x["t"]) for x in c] if c is not None else None
            akeys = [ak[i] for i in range(lo, hi)]
            tkeys = [key(x) for x in tspan]
            for i in range(lo, hi):
                covered.add(i)

            def take(tokens, why):
                log.append((why, " ".join(A[i]["t"] for i in range(lo, hi)), " ".join(tokens), A[lo]["leaf"] if lo < len(A) else None))
                if hi > lo:
                    out[lo] = " ".join(tokens)
                    for i in range(lo + 1, hi):
                        out[i] = ""
                else:
                    ins.setdefault(lo, []).extend(tokens)

            if bks is not None and "".join(bks) == "".join(akeys):
                AB_OVER_T.append((A[lo]["leaf"] if lo < len(A) else None, " ".join(A[i]["t"] for i in range(lo, hi)), " ".join(tspan)))
                continue                                          # A==B: the print
            if bks is not None and "".join(bks) == "".join(tkeys):
                take(tspan, "T=B")
            elif cks is not None and "".join(cks) == "".join(akeys):
                continue
            elif cks is not None and "".join(cks) == "".join(tkeys):
                take(tspan, "T=C")
            elif bks is not None and cks is not None and bks == cks:
                take([x["t"] for x in b], "B=C")
            elif page_reading(" ".join(A[i]["t"] for i in range(lo, hi)), A[lo]["leaf"] if lo < len(A) else None) is not False:
                r = page_reading(" ".join(A[i]["t"] for i in range(lo, hi)), A[lo]["leaf"])
                if r is not None:
                    take(r.split(), "page")
            else:
                conflicts.append({"leaf": A[lo]["leaf"] if lo < len(A) else None, "A": " ".join(A[i]["t"] for i in range(lo, hi)),
                                  "T": " ".join(tspan), "B": " ".join(x["t"] for x in b) if b is not None else None,
                                  "C": " ".join(x["t"] for x in c) if c is not None else None, "lo": lo, "hi": hi})
    # regions T does not cover: B and C outvote A
    for tag, i1, i2, j1, j2 in opcodes(ak, bk):
        if tag == "equal" or any(i in covered for i in range(i1, max(i2, i1 + 1))):
            continue
        if A[i1]["mark"] if i1 < len(A) else False:
            continue
        b = B[j1:j2]
        c = reading(mC, C, i1, i2)
        if c is not None and [key(x["t"]) for x in c] == [key(x["t"]) for x in b] and \
                "".join(key(x["t"]) for x in b) != "".join(ak[i1:i2]):
            log.append(("B=C", " ".join(A[i]["t"] for i in range(i1, i2)), " ".join(x["t"] for x in b), A[min(i1, len(A) - 1)]["leaf"]))
            if i2 > i1:
                out[i1] = " ".join(x["t"] for x in b)
                for i in range(i1 + 1, i2):
                    out[i] = ""
            else:
                ins.setdefault(i1, []).extend(x["t"] for x in b)
    # punctuation and accents: on tokens whose letters agree, B and C
    # together outvote A ("species^" is A's comma; "Societe" B and C may
    # both read "Société")
    def sig(s):
        s = s.replace("\u00ad", "")
        for x, y in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "--"), ("–", "-")):
            s = s.replace(x, y)
        return s
    for i, a in enumerate(A):
        if out[i] != a["t"] or a["mark"] or a["zone"] == "head" or i not in mB or i not in mC:
            continue
        bs, cs = sig(B[mB[i]]["t"]), sig(C[mC[i]]["t"])
        noq = lambda s: re.sub(r"[\"'\-]", "", s)
        if bs == cs and noq(bs) != noq(sig(a["t"])) and same_letters(bs, a["t"]) and "\u00ad" not in a["t"]:
            # quotes and dashes left alone: which word a straight quote
            # clings to is OCR tokenising, not the print
            if re.search(r"[^\w.,;:!?'\"()\[\]\-À-ÿ]", bs):
                continue                       # B and C agreeing on junk is still junk
            # keep A's own quotes and dashes, take B's other marks and accents
            new = B[mB[i]]["t"]
            lead = re.match(r"^[\"'“‘(\[—\-]*", a["t"]).group()
            trail = re.search(r"[\"'”’)\]—\-]*$", a["t"]).group()
            core = new.strip("\"'“”‘’—-")
            if re.match(r"^[.,;:!?]", core) or core.count(".") < a["t"].count(".") - 1:
                continue                       # a stop drifting onto the next word
            new = lead + core + trail if core else a["t"]
            if new != a["t"]:
                log.append(("punct", a["t"], new, a["leaf"]))
                out[i] = new
    return A, B, C, mB, mC, out, ins, log, conflicts


if __name__ == "__main__":
    A, B, C, mB, mC, out, ins, log, conflicts = run()
    import collections
    print(len(A), "A tokens;", collections.Counter(a["zone"] for a in A))
    print(collections.Counter(k for k, *_ in log), len(conflicts), "conflicts")
    for c in conflicts[:60]:
        print(f"  leaf {c['leaf']}: A={c['A'][:40]!r} T={c['T'][:40]!r} B={(c['B'] or '')[:40]!r} C={(c['C'] or '')[:40]!r}")
