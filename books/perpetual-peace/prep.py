"""Prepare Kant, Zum ewigen Frieden: German source + English crib, per file.

    python3 books/perpetual-peace/prep.py     # writes chapters/, reference/, manifest.json

SOURCES (in _src/, fetched by fetch.sh):
  pg46873.txt       Gutenberg #46873, the PGDP transcription of the FIRST
                    edition (Königsberg: Nicolovius, 1795), errata applied.
                    THE SOURCE for everything but the Second Supplement.
                    =x= is Sperrdruck, _x_ italic (Latin); both -> *x*.
  aa08/NNN.html     Akademie-Ausgabe vol. VIII, pp. 341-386, from Kant im
                    Kontext (korpora.org). The AA prints the 1796 "neue
                    vermehrte Auflage". A word-level diff of the whole AA
                    text against #46873 (spelling normalized) shows ONE
                    substantive difference: the 1796 edition adds the
                    "Zweiter Zusatz. Geheimer Artikel zum ewigen Frieden"
                    (AA 368-369), and renames "Zusatz" to "Erster Zusatz".
                    Everything else is spelling (seyn/sein, so fort/sofort)
                    and a dozen single words (dies/die Völkerbund, nur/nun,
                    vergrößten/vergrößerten), not applied -- except the
                    corrected definition of freedom in note 4, which is.
                    (A first diff seemed to show 1796 enlarging notes 2, 3
                    and 4; it was this script reading a note's indented
                    second paragraph as body text. Fixed below.) So: the 1795 text with
                    the 1796 addition spliced in from the AA, in the AA's
                    (Akademie) spelling, paragraphed as the 1796 print is
                    (four paragraphs; Smith, who translated Kehrbach's text
                    of 1796, agrees). The AA pages carry no emphasis markup.
  pg50922_smith.txt Gutenberg #50922, M. Campbell Smith's translation (1903).
                    THE CRIB ONLY, cut per file into reference/. Her long
                    introduction is not used; her own notes (marked [Tr.])
                    are dropped from the crib, Kant's notes are kept.

STRUCTURE IS KANT'S: an untitled preface paragraph (the innkeeper's sign),
Section One (six Preliminary Articles), Section Two (three Definitive
Articles), First Supplement, Second Supplement, Appendix I and II. Section
Two is two files (cut between the First and Second Definitive Articles);
everything else is one file per division.

FOOTNOTES: Kant's sixteen notes ("*)" in 1795, "[n]" in the transcription)
follow their citing paragraph as "Footnote: ..." paragraphs -- the house
convention (chalk, burke) -- and the marker is removed from the text.
"""

import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src"

# (file, English title, German cut-line regex that STARTS the file, part, of)
FILES = [
    ("000.txt", "Preface", r"^Ob diese satyrische", 1, 1),
    ("001.txt", "Section One: The Preliminary Articles for Perpetual Peace Between States",
     r"^Erster Abschnitt,", 1, 1),
    ("002.txt", "Section Two: The Definitive Articles for Perpetual Peace Between States",
     r"^Zweyter Abschnitt,", 1, 2),
    ("003.txt", "Section Two: The Definitive Articles for Perpetual Peace Between States",
     r"^Zweyter Definitivartikel", 2, 2),
    ("004.txt", "First Supplement: On the Guarantee of Perpetual Peace",
     r"^Zusatz\.$", 1, 1),
    ("005.txt", "Second Supplement: A Secret Article for Perpetual Peace", None, 1, 1),
    ("006.txt", "Appendix One: On the Disagreement Between Morality and Politics with Regard to Perpetual Peace",
     r"^Anhang\.$", 1, 1),
    ("007.txt", "Appendix Two: On the Agreement of Politics with Morality According to the Transcendental Concept of Public Right",
     r"^II\.$", 1, 1),
]
END = r"^Verbesserungen zum ewigen Frieden\.$"

# Smith's crib, cut at her headings (line regexes, in file order).
CRIB = [
    ("000.txt", r"^We need not try to decide"),
    ("001.txt", r"^_FIRST SECTION_$"),
    ("002.txt", r"^_SECOND SECTION_$"),
    ("003.txt", r"^SECOND DEFINITIVE ARTICLE OF PERPETUAL PEACE$"),
    ("004.txt", r"^FIRST SUPPLEMENT$"),
    ("005.txt", r"^SECOND SUPPLEMENT$"),
    ("006.txt", r"^APPENDIX I$"),
    ("007.txt", r"^APPENDIX II$"),
]
CRIB_END = r"^INDEX$"

# The 1796 Second Supplement, paragraph openings (AA 368-369).
SECRET_PARAS = ["Ein geheimer Artikel", "Der einzige Artikel",
                "Es scheint aber", "Daß Könige"]


def paragraphs(lines, indent=False):
    """Blank-line blocks -> list of single-line paragraphs (with, if asked,
    whether the block's first line was indented)."""
    out, cur, ind = [], [], False
    for ln in lines + [""]:
        if ln.strip():
            if not cur:
                ind = ln.startswith(" ")
            cur.append(ln.strip())
        elif cur:
            out.append((" ".join(cur), ind) if indent else " ".join(cur))
            cur = []
    return out


def markup(p):
    p = re.sub(r"=([^=]+?)=", r"*\1*", p)
    p = re.sub(r"_([^_]+?)_", r"*\1*", p)
    p = p.replace("»", "„").replace("«", "“")
    p = re.sub(r"\s+--\s+", " — ", p)
    p = re.sub(r"\s*--$", " —", p)
    p = re.sub(r"^--\s*", "— ", p)
    return p.strip()


def german():
    raw = (SRC / "pg46873.txt").read_text(encoding="utf-8").replace("\r", "")
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines) if re.match(FILES[0][2], l))
    end = next(i for i, l in enumerate(lines) if re.match(END, l))
    lines = lines[start:end]
    # cut points
    cuts = []
    for f, _, rx, _, _ in FILES:
        if rx is None:
            cuts.append(None)
            continue
        cuts.append(next(i for i, l in enumerate(lines) if re.match(rx, l)))
    bounds = [c for c in cuts if c is not None] + [len(lines)]
    chunks, k = {}, 0
    for (f, *_), c in zip(FILES, cuts):
        if c is None:
            continue
        chunks[f] = lines[c:bounds[k + 1]]
        k += 1
    out, nmark = {}, 0
    for f, ls in chunks.items():
        paras, in_note = [], False
        for p, ind in paragraphs(ls, indent=True):
            m = re.match(r"^\[(\d+)\]\s+(.*)$", p)
            if m:
                paras.append("Footnote: " + markup(m.group(2)))
                in_note = True
                continue
            if re.fullmatch(r"\*( +\*){4}", p):
                paras.append("* * *")
                in_note = False
                continue
            # A NOTE'S LATER PARAGRAPHS ARE INDENTED LIKE ITS FIRST, and
            # three notes have them (2: lex permissiva and Windischgrätz;
            # 3: the threefold division of right; 4: hereditary nobility).
            # Read as body text they look like 1796 additions to the notes
            # when diffed against the AA -- they are not; both editions
            # have them in the notes. Joined into the one Footnote paragraph.
            if in_note and ind and not re.match(r"^\d\. „|^\d\. »", p):
                paras[-1] += " " + markup(p)
                continue
            in_note = False
            nmark += len(re.findall(r"\[\d+\]", p))
            p = re.sub(r"\[\d+\]", "", p)
            paras.append(markup(p))
        out[f] = paras
    # 1796 corrects the definition of freedom in note 4, which in 1795 runs
    # the tautology into one quotation; the AA (1796) prints it as two
    # sentences, which is the point of the note. Taken from AA 350.
    f4 = [i for i, p in enumerate(out["002.txt"]) if p.startswith("Footnote: *Rechtliche*")][0]
    old = ("„Freyheit ist die Möglichkeit der Handlungen, dadurch man keinem "
           "Unrecht thut (man mag auch thun, was man will), wenn man nur Keinem "
           "Unrecht thut:“ folglich")
    new = ("„Freyheit ist die Möglichkeit der Handlungen, dadurch man Keinem "
           "Unrecht thut. Man thut Keinem Unrecht (man mag auch thun, was man "
           "will), wenn man nur Keinem Unrecht thut:“ folglich")
    assert old in out["002.txt"][f4]
    out["002.txt"][f4] = out["002.txt"][f4].replace(old, new)
    # The book's title is also the innkeeper's inscription the preface
    # paragraph is about ("diese satyrische Ueberschrift"), so it opens 000.
    out["000.txt"].insert(0, "Zum ewigen Frieden.")
    # 1796: "Zusatz." became "Erster Zusatz."
    assert out["004.txt"][0] == "Zusatz.", out["004.txt"][0]
    out["004.txt"][0] = "Erster Zusatz."
    nfoot = sum(p.startswith("Footnote:") for ps in out.values() for p in ps)
    assert nmark == nfoot == 16, (nmark, nfoot)
    return out


def secret_article():
    rows = []
    for pg in (368, 369, 370):
        t = (SRC / "aa08" / f"{pg}.html").read_text(encoding="latin1")
        for m in re.finditer(r'<td[^>]*colspan="3" width="60%">(.*?)</td>', t, re.S):
            s = m.group(1)
            if "Zeile:" in s or "Text (Kant)" in s or s.strip().startswith("<a name="):
                continue
            s = html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
            if s:
                rows.append(s)
    i = rows.index("Zweiter Zusatz.")
    j = next(k for k, r in enumerate(rows) if r.startswith("Anhang"))
    rows = rows[i:j]
    assert rows[1] == "Geheimer Artikel zum ewigen Frieden.", rows[1]
    text = " ".join(rows[2:])
    text = re.sub(r"\s+", " ", text).replace(" - ", " — ")
    text = text.replace("( ", "(").replace(" )", ")")
    text = re.sub(r'"([^"]*)"', "„\\1“", text)
    paras, pos = [], []
    for o in SECRET_PARAS:
        pos.append(text.index(o))
    pos.append(len(text))
    for a, b in zip(pos, pos[1:]):
        paras.append(text[a:b].strip())
    return ["Zweiter Zusatz.", "Geheimer Artikel zum ewigen Frieden."] + paras


def crib():
    raw = (SRC / "pg50922_smith.txt").read_text(encoding="utf-8").replace("\r", "")
    lines = raw.split("\n")
    first = next(i for i, l in enumerate(lines) if re.match(CRIB[0][1], l))
    idx = [next(i for i, l in enumerate(lines) if i >= first and re.match(rx, l))
           for _, rx in CRIB]
    end = next(i for i, l in enumerate(lines) if i > idx[-1] and re.match(CRIB_END, l))
    idx.append(end)
    out = {}
    for (f, _), a, b in zip(CRIB, idx, idx[1:]):
        paras = paragraphs(lines[a:b])
        keep = []
        for p in paras:
            if re.match(r"^\[\d+\]", p) and p.rstrip().endswith("[Tr.]"):
                continue
            keep.append(p)
        out[f] = keep
    return out


def main():
    de = german()
    de["005.txt"] = secret_article()
    en = crib()
    manifest = []
    for f, title, _, part, of in FILES:
        paras = de[f]
        (BOOK / "chapters" / f).write_text("\n\n".join(paras) + "\n", encoding="utf-8")
        (BOOK / "reference" / f).write_text("\n\n".join(en[f]) + "\n", encoding="utf-8")
        words = sum(len(p.split()) for p in paras)
        manifest.append({"file": f, "title": title, "part": part, "of": of,
                         "words": words})
        print(f, part, of, words, title)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
