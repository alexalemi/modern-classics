"""Fabre, The Story-Book of Science (1917): a RESTORED EDITION.

    python3 books/story-book-of-science/prep.py

Jean-Henri Fabre's Le Livre d'histoires (Delagrave, 1869; "nineteenth French
edition"), in Florence Constable Bicknell's English translation, New
York: The Century Co., August 1917, from Project Gutenberg #56795 (HTML,
which carries the 69 plates and their printed labels). Screened clean --
arch 0.07, sentence 20.9 -- so it needs an edition, not a retelling.
The first book in the collection written for children.

Kept: the Translator's Preface (with its footnote), the book's motto
"Sursum corda" from the half-title (set after a break at the end of the
front section, which is where the half-title stands), the eighty chapters, all four footnotes (set
after the paragraph -- or, for the La Fontaine verse, the poem -- that
cites them), every plate with its printed label.
Dropped: Gutenberg's transcriber-made cover, the title page and its
publisher's device, the copyright page, the Contents (the renderers make
one, and the printed Contents is the witness for the headings below),
the second copy of the half-title, "FINIS", and the transcriber's notes.

THE DROP CAP. Each chapter opens on a drop cap with the rest of its
first word (or name) in small capitals, which Gutenberg transcribes as
capitals: "ONE evening", "UNCLE PAUL showed", "A PLANT-LOUSE, we". Set
in running text that is a shout, so the leading capitals are put in
sentence case, keeping the household's names capitalised.

HEADINGS are the chapter's own head, title-cased ("Chapter VII: A
Numerous Family"), checked against the printed Contents, which differs
in three places, all confirmed on the 1917 scans: the Contents prints
"The Numerous Family", "The Metals" and "Running Water" where the chapter
heads (and the running heads) print A NUMEROUS FAMILY, METALS and RUNNING
WATERS. The page the reader is on wins. (Gutenberg's own head for XXXI
is "THE VIPER AND THE SCORP</span>ION"; the walker reads it whole.)

WITNESSES (the epictetus rule: a reading that shares no code with the
walker): per chapter, the words of the raw HTML between this chapter's
anchor and the next, tags stripped with a regex, must equal -- as a
multiset of lower-case letter words -- the words prep emitted, after
the known differences (heading, drop-cap case, footnote labels). And
scan_diff.py --vote against two Archive.org scans of the 1917 printing
(see notes.txt).
"""
import collections
import html as HTML
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 80
NAMES = {"UNCLE", "PAUL", "MOTHER", "AMBROISINE", "JULES", "EMILE", "EMILE’S", "CLAIRE", "JACQUES"}
# the printed Contents and the chapter head both set "WAVES   SALT
# SEAWEEDS" with wide spaces and no punctuation (three scans agree). It
# stays as printed: no commas added.
TITLE_FIX = {}   # none: Alex's ruling of 2026-10-12, the text stands as printed
CONTENTS_DIFFERS = {"The Numerous Family": "A Numerous Family", "The Metals": "Metals",
                    "Running Water": "Running Waters"}
# Gutenberg normalisations reversed / misreadings corrected, each where the
# two 1917 scans agree on the printed reading (scan_diff --vote, notes.txt)
# A LABEL OF TWO PRINTED LINES flattens into one run ("Ladybug (a) larva
# (b) pupa ...", "Female Male Cabbage Butterfly"). Left as printed, words
# only; no punctuation is added for the line break (Alex, 2026-10-12). The
# Cabbage Butterfly's description says which insect is which.
LABEL = {}
TEXT_FIXES = [
    ("found ever where and", "found everywhere and", "Gutenberg typo; all three scans print everywhere"),
    ("The net must he spun.", "The net must be spun.", "Gutenberg typo; all three scans print be"),
]
# Left as Gutenberg has them (the vote's other hits): the print's own
# misprints, which the transcriber corrected -- "runs, drink, enjoys",
# "The larva finally reached the ramparts" (lava), "naseau", "vetteran",
# "themseleves" -- and ABBYY misreadings of R that both Internet Archive
# OCRs share ("Barely", "bather", "bushing", "Eomas"), where the Google
# scan's OCR and the sense agree with Gutenberg ("Rarely are the clouds").


def sentence_case_dropcap(t):
    lead = re.match(r"([“‘]?)((?:[A-Z][A-Z’\-]*[,.]?\s+)*[A-Z][A-Z’\-]*)(?=[\s,.;:!?”]|$)", t)
    if not lead:
        return t
    q, run = lead.group(1), lead.group(2)
    toks = re.split(r"(\s+)", run)
    words = [w for w in toks if w.strip()]
    if len(words) == 1 and len(words[0]) == 1:      # "I" or "A" alone
        return t
    out, first = [], True
    for w in toks:
        if not w.strip():
            out.append(w)
            continue
        core = w.rstrip(",.")
        if not re.fullmatch(r"[A-Z][A-Z’\-]*", core):
            out.append(w)
        elif first or core in NAMES or core == "I":
            out.append(core[0] + core[1:].lower() + w[len(core):])
        else:
            out.append(w.lower())
        first = False
    return q + "".join(out) + t[lead.end():]


def prepare(soup):
    # printed labels sit in div.ic001; the walker looks for a "caption" class
    for d in soup.select("div.ic001"):
        d["class"] = ["caption"]
    # verse: Gutenberg's linegroup/group/line -> the walker's poetry shape
    for d in soup.select("div[class^=lg-container]"):
        d["class"] = ["poetry-container"]
        for g in d.select("div.group"):
            g["class"] = ["stanza"]
        for ln in d.select("div.line"):
            c = ln.get("class")
            ind = next((int(x[2:]) // 2 for x in c if re.fullmatch(r"in\d+", x)), 0)
            ln["class"] = ["line"] + ([f"indent{ind}"] if ind else [])
    # footnotes: ids f1..f4 -> fn1..fn4, the walker's shape
    for a in soup.find_all("a", href=re.compile(r"^#f\d+$")):
        a["href"] = "#fn" + a["href"][2:]
    for d in soup.select("div.footnote"):
        n = d["id"][1:]
        lab = d.select_one("span.label")
        new = soup.new_tag("a", id=f"fn{n}")
        lab.replace_with(new)
    for a in soup.find_all("a", id=re.compile(r"^r\d+$")):
        a.decompose()


def main():
    book = R.Book(HERE, "pg56795-h.zip",
                  drop={"cover.jpg": "the transcriber's cover",
                        "publogo.jpg": "the publisher's device on the title page"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")

    toc = [(a, R.clean(b.get_text())) for a, b in
           ((tr.find_all("td")[0].get_text(strip=True), tr.find_all("td")[1]) for tr in soup.select("table.table0 tr")[1:])]
    assert len(toc) == CHAPTERS, len(toc)

    # front matter: everything before the Translator's Preface goes
    pref = soup.find("h2", string=re.compile("TRANSLATOR"))
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    # the two half-titles ("THE STORY-BOOK OF SCIENCE / Sursum corda")
    halves = [d for d in soup.select("div.nf-center-c0") if "Sursum" in d.get_text()]
    assert len(halves) == 2
    for d in halves:
        d.decompose()
    # the end: FINIS and the transcriber's notes
    fin = [d for d in soup.select("div.nf-center-c0") if R.clean(d.get_text()) == "FINIS"]
    assert len(fin) == 1
    for el in list(fin[0].find_all_next()):
        el.decompose()
    fin[0].decompose()
    raw_chapters = str(soup)          # for the witness, before prepare()
    prepare(soup)

    w = R.Walker(book, soup)
    items = w.stream(soup)
    assert not w.note_text, f"footnotes never cited: {list(w.note_text)}"

    sections = []
    for it in items:
        if it[0] == "H":
            t = it[2]
            if t == "TRANSLATOR’S PREFACE":
                sections.append({"title": "Translator’s Preface", "stream": []})
                continue
            m = re.fullmatch(r"CHAPTER ([IVXL]+) (.+)", t)
            assert m, t
            num, listed = toc[len(sections) - 1]
            assert num == m.group(1), (num, t)
            name = R.titlecase(m.group(2))
            same = re.sub(r"\W+", "", listed.upper()) == re.sub(r"\W+", "", m.group(2).upper())
            assert same or CONTENTS_DIFFERS.get(listed) == name, (listed, name)
            if same:
                assert listed == name or listed.lower() == name.lower(), (listed, name)
                name = listed            # the Contents' capitalisation ("Its", "De Romas")
            sections.append({"title": f"Chapter {num}: {TITLE_FIX.get(name, name)}", "stream": []})
            continue
        assert sections, it
        sections[-1]["stream"].append(it)
    assert len(sections) == CHAPTERS + 1

    # the motto stands on the half-title, between the Preface and Chapter I;
    # set at the head of Chapter I it read as that chapter's epigraph, so it
    # closes the front section after a break, where it falls in the book
    sections[0]["stream"] += [("HR",), ("P", "*Sursum corda*")]

    # drop caps: the first paragraph of every chapter
    dropped = 0
    for s in sections[1:]:
        k = next(i for i, it in enumerate(s["stream"]) if it[0] == "P")
        new = sentence_case_dropcap(s["stream"][k][1])
        dropped += new != s["stream"][k][1]
        if new == s["stream"][k][1]:
            print("  drop cap kept:", new[:40])
        s["stream"][k] = ("P", new)
    print("drop caps set in sentence case:", dropped)

    # footnote 4 is cited from the last line of the La Fontaine verse; the
    # walker sets a note after the next PARAGRAPH, which here is the one
    # after the poem. Move it up to follow the poem.
    for src, (walked, _) in LABEL.items():
        got = [it[2] for s in sections for it in s["stream"] if it[0] == "PLATE" and it[1] == src]
        assert got == [walked], (src, got)
    for s in sections:
        st = s["stream"]
        for k, it in enumerate(st):
            if it[0] == "P" and it[1].startswith("Footnote: The translation is that of Elizur Wright"):
                assert st[k - 2][0] == "BLOCK" and "In vain shall I protest" in st[k - 2][1], st[k - 2]
                st.insert(k - 1, st.pop(k))

    witness(raw_chapters, sections)          # of the transcription, before our fixes
    R.text_fixes(sections, TEXT_FIXES)

    print("paragraphs mended around a plate:", R.mend_plate_splits(sections))
    # captions are escaped, not inline-rendered (assemble.py figure()), so the
    # italic letters of "(*a*) larva" would ship as asterisks: set them roman
    plates = [{"src": it[1], "printed": (LABEL[it[1]][1] if it[1] in LABEL else it[2]).replace("*", "")}
              for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


def letters(s):
    s = HTML.unescape(s).replace("’", "'")
    return [x.lower() for x in re.findall(r"[A-Za-zÀ-ÿ]+", s)]


def witness(raw, sections):
    """Per section, the raw HTML's words (regex-stripped) against prep's."""
    parts = re.split(r'<h2[^>]*>', raw)[1:]
    assert len(parts) == len(sections), (len(parts), len(sections))
    bad = []
    for part, s in zip(parts, sections):
        part = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", part, flags=re.S)
        part = re.sub(r'<span class="label">.*?</span>', " ", part, flags=re.S)   # "1."
        part = re.sub(r"<sup>\[\d+\]</sup>", " ", part)                             # "[1]"
        part = re.sub(r"</?(span|i|sup|a)\b[^>]*>", "", part)                   # inline: no space
        rawc = collections.Counter(letters(re.sub(r"<[^>]+>", " ", part)))
        got = []
        for it in s["stream"]:
            if it[0] in ("P", "BLOCK"):
                got += letters(it[1].replace("*", ""))
            elif it[0] == "PLATE":
                got += letters(it[2])
        gotc = collections.Counter(got)
        gotc.subtract({"footnote": sum(1 for it in s["stream"] if it[0] == "P" and it[1].startswith("Footnote: "))})
        gotc.update(letters(s["title"].replace("Chapter", "chapter")))
        if s["title"] == "Translator’s Preface":
            gotc.subtract({"sursum": 1, "corda": 1})
        diff = {k: v for k, v in (rawc - gotc).items()}
        diff2 = {k: v for k, v in (gotc - rawc).items()}
        if diff or diff2:
            bad.append((s["title"], diff, diff2))
    assert not bad, bad[:5]
    print("witness: raw words equal emitted words in all", len(sections), "sections")


if __name__ == "__main__":
    main()
