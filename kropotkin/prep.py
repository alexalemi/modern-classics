"""Kropotkin, Mutual Aid: A Factor of Evolution -> chapters/ and
modern_chapters/ (a RESTORED EDITION of the 1904 Revised and Cheaper
Edition, Heinemann).

    python3 kropotkin/prep.py            # build
    python3 kropotkin/prep.py --report   # also list every adjudication

The words come from merge.py's vote (UCLA's 1904 copy as the pivot, two
Duke scans of the 1914 impression and Gutenberg #4341 voting). Structure
is read off the print: the chapter heads and Kropotkin's analytical
summaries, paragraph indents, the smaller type of block quotations, and
the footnotes, each matched to its superscript reference on the same page
and set as "Footnote: ..." after the paragraph that cites it (the house
convention, restore_lib). The Appendix's twelve notes keep their headings
and their "(To p. N.)" pointers, which name the 1904 page they annotate.

Dropped: the press opinions, title page, Contents (the renderers make
one) and the Index. Gutenberg's text (the 1902 first edition, accents
stripped, no Appendix) is only ever a witness.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import merge as M  # noqa: E402

REPORT = "--report" in sys.argv
JOINED = []
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}


def surface(A, out, ins, i):
    toks = list(ins.get(i, []))
    if out[i]:
        toks.append(out[i])
    return toks


def emph(toks_it):
    """Join (text, italic) tokens, wrapping italic runs in *...*, keeping
    punctuation outside the asterisks."""
    out, run = [], []

    def flush():
        if run:
            s = " ".join(run)
            m = re.match(r"^([(\[“\"‘']*)(.*?)([)\],.;:!?”\"’']*)$", s, re.S)
            out.append(f"{m.group(1)}*{m.group(2)}*{m.group(3)}" if m.group(2) else s)
            run.clear()
    for t, it in toks_it:
        if it and re.search(r"[A-Za-zÀ-ÿ]", t):
            run.append(t.replace("*", ""))     # a page reading's own italics, inside A's
        else:
            flush()
            out.append(t)
    flush()
    return " ".join(out)


def build():
    A, B, C, mB, mC, out, ins, log, conflicts = M.run()
    # NOTES. Boundaries: where a Gutenberg note starts (carried onto the
    # print by the alignment) or where the print opens a numbered note
    # line. A segment holding a Gutenberg note's start IS that note; the
    # rest are notes new in 1904 (or in the Appendix), placed by the
    # leftover superscripts on their own page.
    TS = M.TSTRUCT
    tstart = {}
    for nid, (s0, e0) in TS["notes"].items():
        mapped = [TS["note2a"][j] for j in range(s0, e0) if j in TS["note2a"]]
        if mapped:
            tstart[min(mapped)] = nid
    nidx = [i for i, a in enumerate(A) if a["zone"] == "note"]
    segs = []                          # [note id or None, leaf, [token indices]]
    for i in nidx:
        a = A[i]
        line_start = A[i - 1]["line"] != a["line"]
        is_num = line_start and (a["mark"] or re.fullmatch(r"[\d*†\-]{1,2}", a["t"]))
        if i in tstart and (not segs or segs[-1][0] != tstart[i]):
            if segs and segs[-1][0] is None and len(segs[-1][2]) <= 12 and \
                    (not segs[-1][2] or A[segs[-1][2][0]]["leaf"] == a["leaf"]):
                # the print's numbered line opened it a few words before the
                # alignment found Gutenberg's text ("1 H. W. | Bates, ...")
                segs[-1][0] = tstart[i]
            else:
                segs.append([tstart[i], a["leaf"], []])
        elif is_num:
            segs.append([None, a["leaf"], []])
            continue
        if not segs:
            segs.append([None, a["leaf"], []])
        if is_num:
            continue
        segs[-1][2].append(i)
    segs = [s for s in segs if s[2]]
    notes = [[(x, A[i]["it"]) for i in idxs for x in surface(A, out, ins, i)] for _, _, idxs in segs]
    # placement: Gutenberg's references first
    place = {}                         # A body index -> [note numbers]
    by_id = {nid: k for k, (nid, _, _) in enumerate(segs) if nid is not None}
    b2a = TS["body2a"]
    used_marks = set()
    marks = [i for i, a in enumerate(A) if a["mark"] and a["zone"] != "note"]
    for tb, nid in TS["refs"]:
        if nid not in by_id:
            continue
        j = tb
        while j >= 0 and j not in b2a:
            j -= 1
        ai = b2a[j] if j >= 0 else 0
        place.setdefault(ai, []).append(by_id[nid])
        # the print's own mark for it, so it is not used twice
        near = [m for m in marks if m not in used_marks and abs(m - ai) <= 3]
        if near:
            used_marks.add(near[0])
    # the rest: leftover marks on the same page, in order
    done = {n for v in place.values() for n in v}
    for k, (nid, leaf, idxs) in enumerate(segs):
        if k in done:
            continue                   # placed by Gutenberg's reference (two
                                       # of its notes have lost theirs)
        cand = [m for m in marks if m not in used_marks and A[m]["leaf"] == leaf]
        if not cand:
            # a note continued from the page before: join it to the last note
            prev = next((j for j in range(k - 1, -1, -1) if notes[j] is not None), None)
            if prev is not None:
                JOINED.append((leaf, " ".join(x for x, _ in notes[prev][-6:]), " ".join(x for x, _ in notes[k][:10])))
                notes[prev].extend(notes[k])
                notes[k] = None
                continue
            raise SystemExit(f"note on leaf {leaf} has no reference: {' '.join(x for x, _ in notes[k])[:80]}")
        used_marks.add(cand[0])
        place.setdefault(cand[0], []).append(k)
    placed = sorted(n for v in place.values() for n in v)
    want = [k for k, n in enumerate(notes) if n is not None]
    assert placed == want, (len(placed), len(want), sorted(set(want) - set(placed))[:10])
    sections, cur, para, para_kind = [], None, [], None
    pending_notes = []

    def end_para():
        nonlocal para, para_kind
        if para and cur is not None:
            text = emph(para)
            if para_kind == "quote":
                cur["blocks"].append("\t" + text)
            else:
                cur["blocks"].append(text)
            for n in pending_notes:
                cur["blocks"].append("Footnote: " + emph(notes[n]))
            pending_notes.clear()
        para, para_kind = [], None

    sections.append({"title": "Introduction", "blocks": []})
    cur = sections[-1]
    i = 0
    while i < len(A):
        a = A[i]
        z = a["zone"]
        if z == "note":
            i += 1
            continue
        line_start = i == 0 or A[i - 1]["line"] != a["line"]
        if z == "head":
            end_para()
            # collect the whole heading run
            run = []
            while i < len(A) and A[i]["zone"] == "head":
                run.append((A[i], surface(A, out, ins, i)))
                i += 1
            sections_add_heading(sections, run)
            cur = sections[-1]
            continue
        if i in place:
            pending_notes.extend(place[i])
        if a["mark"]:
            i += 1
            continue
        text = " ".join(surface(A, out, ins, i))
        # appendix subheadings: "I. SWARMS OF ..." and "(To p. 10.)"
        if line_start and z in ("app", "quote", "body") and a.get("appendix"):
            line_toks = [x for x in A[i:i + 40] if x["line"] == a["line"]]
            lt = " ".join(x["t"] for x in line_toks)
            if re.match(r"^[IVX]+\.\s*—?\s*[A-Z“\"]", lt) and lt.upper() == lt:
                end_para()
                # a heading may run to a second line of capitals before its pointer
                head = [lt]
                j = i + len(line_toks)
                while j < len(A):
                    nxt = [x for x in A[j:j + 40] if x["line"] == A[j]["line"]]
                    nt = " ".join(x["t"] for x in nxt)
                    if nt.upper() == nt and not nt.startswith("(To") and re.search(r"[A-Z]", nt):
                        head.append(nt)
                        j += len(nxt)
                    else:
                        break
                cur["blocks"].append(sub_title(" ".join(head)))
                i = j
                continue
            if re.fullmatch(r"\(To pp?\. [\dIlS\-–, ]+[.\-]?\)", lt.strip()):
                end_para()
                ptr = re.sub(r"(?<=\d)S|S(?=\d)", "8", lt.strip()).replace("l", "1").replace("I", "1")
                ptr = re.sub(r"(\d)-\)$", r"\1.)", ptr)
                cur["blocks"].append("*" + ptr + "*")
                i += len(line_toks)
                continue
        kind = "quote" if z == "quote" else "body"
        indent = line_start and a["l"] > a["left"] + 35
        if para and (indent or kind != para_kind):
            end_para()
        if not para:
            para_kind = kind
        for s in surface(A, out, ins, i):
            para.append((s, a["it"]))
        i += 1
    end_para()
    return sections, log, conflicts, notes


def sub_title(s):
    m = re.match(r"^([IVX]+)\.\s*—?\s*(.*)$", s.strip())
    words = m.group(2).rstrip(".").split()
    small = {"of", "the", "and", "in", "on", "to", "at", "a", "an", "for"}
    t = " ".join(w.lower() if w.lower() in small and k else w.capitalize() if w.isupper() else w for k, w in enumerate(words))
    t = t.replace("Medieval", "Mediæval").replace("Mediaeval", "Mediæval").replace("Netherlands", "Netherland")
    t = re.sub(r"\b(Etc)\b", "etc", t)
    t = re.sub(r"(?<=-)([A-Z])([A-Z]+)", lambda x: x.group(1).lower() + x.group(2).lower(), t)
    return f"{m.group(1)}. {t}"


def sections_add_heading(sections, run):
    text = " ".join(" ".join(s) for _, s in run)
    m = re.match(r"^CHAPTER\s+([IVX]+)\s+(.*)$", text)
    if text.startswith("INTRODUCTION"):
        sections.append({"title": "Introduction", "blocks": []})
        return
    if text.startswith("CONCLUSION"):
        sections.append({"title": "Conclusion", "blocks": []})
        return
    if text.startswith("APPENDIX"):
        sections.append({"title": "Appendix", "blocks": []})
        rest = text[len("APPENDIX"):].strip()
        if rest:
            m2 = re.match(r"^([IVX]+\.\s+.*?)\s*(\(To p\..*?\))?$", rest)
            sections[-1]["blocks"].append(sub_title(m2.group(1)))
            if m2.group(2):
                sections[-1]["blocks"].append("*" + m2.group(2) + "*")
        return
    assert m, text[:80]
    # the title is the run of capitals; the summary follows
    lines = {}
    for a, s in run:
        lines.setdefault(a["line"], []).extend(s)
    ls = [" ".join(v) for v in lines.values()]
    title = ls[1]
    summary = " ".join(ls[2:])
    small = {"of", "the", "and", "in", "among", "amongst", "a"}
    tt = " ".join(w.lower() if w.lower() in small and k else w.capitalize() for k, w in enumerate(title.split()))
    tt = tt.replace("(continued)", "(continued)").replace("Mediaeval", "Mediæval").replace("Medieval", "Mediæval")
    want = TITLES[m.group(1)]
    assert key_title(tt) == key_title(want), (tt, want)
    sections.append({"title": f"Chapter {m.group(1)}: {want}", "blocks": [f"*{summary}*"] if summary else []})


# The chapter titles as the 1904 print heads them (the OCR garbles the
# brackets of "(continued)"; VIII is not headed "continued" in the body).
TITLES = {"I": "Mutual Aid among Animals", "II": "Mutual Aid among Animals (continued)",
          "III": "Mutual Aid among Savages", "IV": "Mutual Aid among the Barbarians",
          "V": "Mutual Aid in the Mediæval City", "VI": "Mutual Aid in the Mediæval City (continued)",
          "VII": "Mutual Aid amongst Ourselves", "VIII": "Mutual Aid amongst Ourselves"}


def key_title(s):
    return re.sub(r"[^a-z]", "", s.lower().replace("æ", "ae").replace("mediaeval", "medieval"))


def hyphen_words():
    """Words Gutenberg prints with a hyphen, and those it prints joined."""
    t = (HERE / "_src/pg4341.txt").read_text()
    hy = {w.lower() for w in re.findall(r"[A-Za-z]+-[A-Za-z]+", t)}
    plain = {w.lower() for w in re.findall(r"[A-Za-z]+", t)}
    return hy, plain


HY, PLAIN = hyphen_words()
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}


def unsoft(m):
    a, b = m.group(1), m.group(2)
    if f"{a}-{b}".lower() in HY:
        return f"{a}-{b}"
    if (a + b).lower() in PLAIN or (a + b).lower() in DICT:
        return a + b
    if b[:1].isupper():
        return f"{a}-{b}"
    return a + b


def accent_dictionary():
    """Accented words as any scan reads them: stripped form -> accented
    form, when the accented reading occurs at least twice across the three
    OCRs and the stripped form is not itself an English word."""
    import collections
    import unicodedata
    strip = lambda s: "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    seen = collections.Counter()
    for name in ("mutualaidfactoro1902krop_djvu.txt", "mutualaid01krop_djvu.txt", "mutualaidfactor00kropiala_djvu.txt"):
        for w in re.findall(r"[A-Za-zÀ-ÿ]+", (HERE / "_src" / name).read_text()):
            if strip(w) != w and len(w) > 3:
                seen[w] += 1
    best = {}
    for w, n in seen.most_common():
        s = strip(w)
        if n >= 2 and s.lower() not in DICT and s not in best:
            best[s] = w
    return best


ACCENTS = accent_dictionary()


# Accents the print sets and every OCR loses (the djvu layers strip them,
# ABBYY renders them as stray apostrophes). Only certain spellings: the
# French and German of Kropotkin's notes, and OCR's "ii" for ü (the Latin
# and Russian -ii words -- convivii, collegiis, Przewalskii -- are left).
ACCENT_MAP = {
    "Etudes": "Études", "Societe": "Société", "societe": "société", "Societes": "Sociétés",
    "Geographie": "Géographie", "siecle": "siècle", "Siecle": "Siècle", "propriete": "propriété",
    "Propriete": "Propriété", "Etablissements": "Établissements", "republiques": "républiques",
    "Republiques": "Républiques", "Memoires": "Mémoires", "Bibliotheque": "Bibliothèque",
    "generale": "générale", "francais": "français", "Francais": "Français", "francaises": "françaises",
    "Ariege": "Ariège", "Bonnemere": "Bonnemère", "economique": "économique", "Economie": "Économie",
    "Besan^on": "Besançon", "biens^ance": "bienséance", "J6msviking": "Jómsviking",
    "Konigswarter": "Königswarter", "Koln": "Köln", "Wurzburg": "Würzburg", "Schonberg": "Schönberg",
    "Buchner": "Büchner", "Bucher": "Bücher", "Volker": "Völker", "Stadte": "Städte",
    "Stadteverfassung": "Städteverfassung", "Alterthumer": "Alterthümer", "Geschichtsblatter": "Geschichtsblätter",
    "Handworterbuch": "Handwörterbuch", "Volkerpsychologie": "Völkerpsychologie",
    "Hiiter": "Hüter", "siidlichen": "südlichen", "Biirgschaften": "Bürgschaften", "Miinzinger": "Münzinger",
    "iiber": "über", "Ziinfte": "Zünfte", "Liibeck": "Lübeck", "miinsterischen": "münsterischen",
    "Biirgernutzen": "Bürgernutzen", "Wiirttemberg": "Württemberg", "Kegelbriider": "Kegelbrüder",
    "Biichner": "Büchner",
}


# Misreadings BOTH OCRs share (so the vote kept them), nearly all in the
# italic of the notes; Gutenberg or the page gives the word.
OCR_WORDS = {
    "cesulon": "æsalon", "ccesia": "cæsia", "soeial": "social", "djemmda": "djemmâa",
    "fofs": "çofs", "scholce": "scholæ", "basilicse": "basilicæ", "Weickbild": "Weichbild",
    "fruittires": "fruitières", "associatious": "associations", "Geographic": "Géographie",
    "CEuvres": "Œuvres", "fhistoire": "l'histoire", "rhistoire": "l'histoire", "Thistoire": "l'histoire",
    "Fagriculture": "l'agriculture", "ddpouiller": "dépouiller", "accommodd": "accommodé",
    "Stddte": "Städte", "Stddteverfassung": "Städteverfassung", "Beitrdge": "Beiträge",
    "Xlllme": "XIIIme", "arces": "acres", "Elisee": "Élisée",
}
# ABBYY's accent-as-apostrophe: "Elise’e", "accommode’", "Ge’neve"
APOS_ACCENT = {"Elise’e": "Élisée", "Elise'e": "Élisée", "accommode’": "accommodé", "accommode'": "accommodé",
               "Ge’neve": "Génève", "Le’on": "Léon", "Socie’te’s": "Sociétés", "Fe’e": "Fée",
               "not’but": "not but", "priv’e": "privé", "simule’es": "simulées", "The’ron": "Théron",
               "jusqu’b": "jusqu’à", "talioniS": "talionis", "Gesprache": "Gespräche", "Drummond(London": "Drummond (London"}


def accent(text):
    text = re.sub(r"[A-Za-z]{3,}", lambda m: OCR_WORDS.get(m.group(), m.group()), text)
    text = re.sub(r"\bot\b", "of", text)                  # "ot" is never the print's word
    for k, v in APOS_ACCENT.items():
        text = text.replace(k, v)
    text = re.sub(r"\bist ed\.", "1st ed.", text)
    text = re.sub(r"\bi,(\d{3})\b", r"1,\1", text)
    text = re.sub(r"[A-Za-z\^0-9]{4,}", lambda m: ACCENT_MAP.get(m.group(), m.group()), text)
    return re.sub(r"[A-Za-z]{4,}", lambda m: ACCENTS.get(m.group(), m.group()), text)


def ocr_marks(text):
    """OCR's habitual confusions in italic passages: none of these
    characters occurs in the book itself."""
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ.)])\^", ",", text)
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ])>", ",", text)
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ.])\\(?=[*,.\s]|$)", ")", text)
    text = text.replace("{", "(").replace("}", ")")
    text = re.sub(r"(?<=[a-z])[12](?=[,)—.;]|\s)", "", text)   # a note reference left on its word
    return text


def finish(text):
    """The print's typography in modern form: line-end joins decided, the
    space before ; : ! ? dropped, straight quotes made curly."""
    text = re.sub(r"([A-Za-zÀ-ÿ]+)\u00ad([A-Za-zÀ-ÿ]+)", unsoft, text)
    text = text.replace("\u00ad", "")
    text = ocr_marks(accent(text))
    text = text.replace("mediaeval", "mediæval").replace("Mediaeval", "Mediæval")
    text = re.sub(r"\s+([;:!?])", r"\1", text)
    text = re.sub(r'"\s+(?=\w)', '"', text) if False else text
    text = re.sub(r'(^|[\s(\[—])"\s*', r"\1“", text)
    text = re.sub(r'\s*"', "”", text)
    text = re.sub(r"(^|[\s(\[—])'", r"\1‘", text)
    text = text.replace("'", "’")
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


# Single readings settled by context, Gutenberg or the page (leaf noted
# where the page decided). Each must match exactly once.
FINAL_FIXES = [
    ("*Prehistoric Times*, > pp. 232", "*Prehistoric Times*, pp. 232"),     # Gutenberg
    ("*\\loc. cit*. p. 31)", "(*loc. cit*. p. 31)"),
    ("of human history. \\/", "of human history."),                      # a note mark
    ("agglomerate into/&**&£, gentes", "agglomerate into gentes"),       # Gutenberg
    ("called into existence by the\n\n‘S3 social genius", "called into existence by the social genius"),
    ("*Weichbild-\\aw*", "*Weichbild*-law"),
    ("pp. 26-47, 75> etc-", "pp. 26-47, 75, etc."),
    ("PP- I3-I5-", "pp. 13-15."),
    ("1s. out of 25^.,", "1s. out of 25s.,"),
    ("pp. 130^.).", "pp. 130 *seq.*)."),                                   # the page
    ("pp. 360^363).", "pp. 360-363)."),
    ("Martin-Saint-L6on", "Martin-Saint-Léon"),
    ("(PP- 431 *seq.*), gi ves", "(pp. 431 *seq.*), gives"),
    ("ix.—THE “UNDIVIDED FAMILY.\n\n(Top. 124.)", "IX. The “Undivided Family”\n\n*(To p. 124.)*"),
]


def write(sections):
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    texts = [s["title"] + "\n\n" + "\n\n".join(finish(b) for b in s["blocks"]) + "\n" for s in sections]
    for old, new in FINAL_FIXES:
        n = sum(x.count(old) for x in texts)
        assert n == 1, (old, n)
        texts = [x.replace(old, new) for x in texts]
    texts = [re.sub(r"(\d)/\.", r"\1l.", x) for x in texts]       # pounds: OCR's "/." is the print's "l."
    for k, s in enumerate(sections):
        text = texts[k]
        for d in ("chapters", "modern_chapters"):
            (HERE / d / f"{k:03d}.txt").write_text(text)
        manifest.append({"file": f"{k:03d}.txt", "title": s["title"], "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sections, log, conflicts, notes = build()
    write(sections)
    print(len(sections), "sections:", [s["title"] for s in sections])
    print(len(notes), "notes;", sum(b.startswith("Footnote:") for s in sections for b in s["blocks"]), "placed")
    print(sum(len(b.split()) for s in sections for b in s["blocks"]), "words;", len(conflicts), "conflicts")
