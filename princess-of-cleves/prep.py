"""Build chapters/ + reference/ + manifest.json for La Princesse de Clèves
(1678) with La Princesse de Montpensier (1662).

    python3 princess-of-cleves/fetch_wikisource.py   # once
    python3 princess-of-cleves/prep.py
    python3 princess-of-cleves/check.py

SOURCES (all under _src/):
  wikisource/cleves-1..4.html, montpensier.html
        French Wikisource, both novels from ONE validated transcription
        ("Textes validés", proofread twice against the scan): Lepetit's
        Œuvres complètes de Mesdames de La Fayette, de Tencin et de
        Fontaines (Paris, 1820), tome 2 -- Clèves pp. 1-210, Montpensier
        pp. 233-270. THE BODY TEXT COMES FROM HERE. fetch_wikisource.py.
  wikisource/avertissement-1689.html
        "Le libraire au lecteur", Barbin's note to the reader, from the
        1689 Barbin printing on Wikisource (long-s spelling). Lepetit
        omits it; it is in the 1678 first edition. File 000.
  pg20262.txt
        Project Gutenberg #20262: the Sledd & Gorrell school edition
        (Ginn, Boston 1896), 17th-century spelling, line-numbered, with
        English notes. SECOND WITNESS ONLY -- check.py compares it word
        for word. It is ABRIDGED for the schoolroom by about a quarter
        (47.9k against Lepetit's 64.2k, measured in check.py's
        normalised tokens; Clèves is 60,147 whitespace words): 55 silent cuts,
        among them the novel's second paragraph (Henri II's twenty-year
        passion for Diane de Poitiers), Madame de Chartres's whole history
        of Diane (~2,400 words), the Sancerre/Madame de Tournon story
        (~3,800), the Anne Boleyn history (~950) and the matchmaking for
        Mademoiselle de Chartres (~1,100), and it moves the Part One/Two
        boundary to cover the cut. Perry and #467 both carry every one of
        those passages. That is why it is not the body -- and why the
        ROADMAP's "~50k words" undercounted the book. Every word it DOES
        have is in Lepetit (check.py: Gutenberg is a subset of ours, no
        run of more than LIMIT words differs). Lepetit is a modernised
        1820 text: "était" for "étoit", "Henri II" for "Henri second",
        "Coulommiers" for "Colomiers" -- the editor's hand, not a loss.
  perry/princessofcleves0{1,2}lafaiala.txt
        Thomas Sergeant Perry's translation (Boston: Little, Brown, 1891;
        2 vols, archive.org ids princessofcleves01lafaiala /
        princessofcleves02lafaiala, the hOCR search text). Complete and
        accurate, plain 19th-century English, OCR noise (running heads,
        broken hyphens). SENSE CRIB for Clèves, sliced per file into
        reference/NNN.txt at hand-found anchors (PERRY_ANCHORS). Perry
        divides the book into FIVE parts (his II+III = Lafayette's Part
        Two); we follow Lafayette's four.
  pg2365.txt
        Gutenberg #2365, Oliver C. Colt's translation of Montpensier: a
        MODERN free translation (his own introduction says he "altered the
        exact way in which it is told"), probably still in copyright.
        SENSE CRIB for Montpensier only; agents may never borrow a phrase.
  pg467.txt
        Gutenberg #467, the anonymous English Clèves (late 17th/18th c.,
        the sweep's highest sentence score). Kept for reference, NOT
        sliced: Perry is the cleaner crib.

STRUCTURE. Lafayette published Clèves in four untitled Parts with no
chapters (Lepetit's pages carry "fin de la première partie" etc.). Each
Part (~15k French words) is cut into THREE files at paragraph boundaries
chosen by hand at scene changes (CUTS), each ~4.2-6k words, grouped in
the manifest as parts 1-3 of one section "Part One" ... "Part Four"
(word form: assemble.PART_LINE needs a Roman numeral or digit, so it
cannot match). Montpensier (~11k words) is three paragraphs in Lepetit;
it is cut into TWO files mid-paragraph at a sentence boundary (the court
ballet), grouped as one section. Files:
  000        The Publisher to the Reader (Barbin's note; carries the
             part_before "The Princess of Cleves", so the note sits inside
             that work, before Part One -- OPTIONAL, see text_analysis)
  001-003    Part One
  004-006    Part Two
  007-009    Part Three
  010-012    Part Four
  013-014    The Princess of Montpensier
The ENGLISH headings are locked here; agents are told the exact string.
"""

import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "_src"

# Each Clèves Part: the paragraphs that OPEN files 2 and 3 of that Part
# (matched on their first words). Chosen at scene changes near the thirds.
CUTS = {
    1: ["Le prince de Clèves n’avait pas donné des marques moins publiques",
        # Madame de Chartres's history of Diane de Poitiers proper
        "Mais pour revenir à madame de Valentinois"],
    2: ["Après ces paroles, madame la dauphine quitta madame de Clèves",
        # the tennis match and the fall from the horse
        "Peu de jours avant l’arrivée du duc d’Albe"],
    3: ["Quand M. de Clèves fut revenu, elle lui dit qu’elle voulait aller",
        # the Queen Dauphine's supper: the confession is all over court
        "Peu de jour avant celui que l’on avait choisi"],
    4: ["Il lui fut impossible de s’éloigner sans voir madame de Clèves",
        # Nemours resolves to speak: the last interview
        "Lassé enfin d’un état si malheureux"],
}
# Montpensier: the sentence that opens file 2 (inside Lepetit's third
# and last paragraph).
MONT_CUT = "Le mariage du roi avec la fille de l’empereur Maximilien"

PART_WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four"}
CLEVES = "The Princess of Cleves"
MONTPENSIER = "The Princess of Montpensier"
NOTE_TITLE = "The Publisher to the Reader"

# Lines that are Lepetit's typography, not Lafayette's text.
DROP = re.compile(r"^(LA PRINCESSE|DE CLÈVES\.|DE MONTPENSIER\.|"
                  r"(SECONDE|TROISIÈME|QUATRIÈME) PARTIE\.|"
                  r"fin de la .*)$")

# Perry: the English that opens each Clèves file (regex, first match after
# the previous anchor). 001 opens on Perry's "PART I."; the crib ends at
# Perry's last sentence.
PERRY_ANCHORS = [
    r"PART +I\.\n",
    r"The Prince of Cleves had concealed his passion quite as little",
    r"\" But to return to Madame de Valentinois",
    r"PART II\.\n",
    r"Then the dauphiness left Madame de Cleves",
    r"A few days before the Duke of Alva's arrival",
    r"PART IV\.\n",
    r"When Monsieur de Cleves came home she told him",
    r"A few days before the one set for the wedding",
    r"PART +V\.\n",
    r"It was impossible for him to return without seeing Madame de Cleves",
    r"Worn out at last by grief and uncertainty",
]
PERRY_END = "furnished examples of the loftest virtue."
COLT_START = "It was while the civil war of religion was tearing France apart"
COLT_CUT = "The marriage of the King to the daughter of the Emperor Maximilian"
COLT_END = "so far from the path of prudence and virtue."


# ---------------------------------------------------------------- Wikisource

def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = s.replace("ſ", "s")
    return " ".join(s.split())


def ws_paras(name):
    """Paragraphs of one rendered Wikisource page, Lepetit typography
    (title lines, part titles, "fin de la ... partie") removed."""
    t = (SRC / "wikisource" / f"{name}.html").read_text(encoding="utf-8")
    t = t[t.index("</style>", t.index("headertemplate-journal")) + 8:]
    t = t[:t.find("<!--")]
    t = re.sub(r'<span><span class="pagenum.*?</span></span>', "", t,
               flags=re.S)
    t = re.sub(r"<figure.*?</figure>", "", t, flags=re.S)
    t = re.sub(r"</p>|<p\b[^>]*>|</div>|<div\b[^>]*>", "\x02", t)
    out, dropped = [], []
    for block in t.split("\x02"):
        s = clean(block)
        if not s:
            continue
        if DROP.match(s):
            dropped.append(s)
            continue
        out.append(s)
    assert any(d.startswith("fin de la") for d in dropped), (name, dropped)
    return out


def avertissement():
    t = (SRC / "wikisource" / "avertissement-1689.html").read_text(
        encoding="utf-8")
    t = t[t.index("AU LECTEUR.</div>") + 17:]
    t = t[:t.find("<!--")]
    s = clean(t)
    s = re.sub(r"^Q ?Velque", "Quelque", s)      # the drop capital
    assert s.startswith("Quelque approbation") and s.endswith("je l’espere."), s
    return s


# ---------------------------------------------------------------- cribs

# running heads ("48 The Princess of Cleves.", "T/ie Princess of C I eves.
# 193", "Preface. 9") and signature marks ("VOL. I. — 4"): any short line
# naming the book, whatever the OCR made of it
PERRY_HEAD = re.compile(
    r"^.{0,12}Princess +of +C.{0,14}$|^VOL\. +I+\..{0,12}$|"
    r"^Preface\. *[\d ]*$", re.M)


def perry_text():
    v1 = (SRC / "perry" / "princessofcleves01lafaiala.txt").read_text()
    v2 = (SRC / "perry" / "princessofcleves02lafaiala.txt").read_text()
    v1, v2 = (re.sub(r"[ \t]+", " ", v) for v in (v1, v2))
    v1 = v1[:v1.index("END OF VOL. I.")]
    v2 = v2[v2.index("PART III.\n"):]
    v2 = v2[:v2.index(PERRY_END) + len(PERRY_END)]
    t = v1 + "\n" + v2
    t = PERRY_HEAD.sub("", t)
    t = re.sub(r"(\w)- (?=[a-z])", r"\1", t)     # "Elisa- beth"
    t = re.sub(r"\n{2,}", "\n", t)
    # a page break inside a sentence: rejoin the halves
    t = re.sub(r"(?<=[^.!?:;\"'\n])[ ]*\n(?=[a-z,;(—\-])", " ", t)
    t = re.sub(r"(\w)-\n(?=[a-z])", r"\1", t)
    t = re.sub(r"(\w)- (?=[a-z])", r"\1", t)
    return t


def slice_by(text, anchors, end=None):
    pos = []
    at = 0
    for a in anchors:
        m = re.compile(a).search(text, at)
        assert m, a
        start = text.rfind("\n", 0, m.start()) + 1
        pos.append(start)
        at = m.end()
    pos.append(len(text) if end is None else text.index(end) + len(end))
    return [text[pos[k]:pos[k + 1]].strip() + "\n" for k in range(len(anchors))]


def perry_slices():
    t = perry_text()
    return slice_by(t, PERRY_ANCHORS, PERRY_END)


def colt_slices():
    t = (SRC / "pg2365.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    a = t.index(COLT_START)
    b = t.index(COLT_CUT)
    c = t.index(COLT_END) + len(COLT_END)
    reflow = lambda s: "\n\n".join(" ".join(p.split()) for p in
                                   re.split(r"\n\s*\n", s) if p.strip()) + "\n"
    return [reflow(t[a:b]), reflow(t[b:c])]


PERRY_BANNER = ("THOMAS SERGEANT PERRY (1891) -- SENSE CRIB ONLY. Uncorrected "
                "OCR (stray characters, page breaks inside sentences). "
                "Translate the FRENCH in chapters/{fn}; consult this only for a "
                "hard sense question, and never borrow its sentences.\n\n")
COLT_BANNER = ("OLIVER C. COLT (modern; Project Gutenberg #2365) -- SENSE "
               "CRIB ONLY. A free modern translation that is probably still "
               "in copyright: never copy or echo a phrase of it. Translate "
               "the FRENCH in chapters/{fn}.\n\n")


# ---------------------------------------------------------------- main

def split_at(paras, openers):
    idx = []
    for op in openers:
        hits = [i for i, p in enumerate(paras) if p.startswith(op)]
        assert len(hits) == 1, (op, hits)
        idx.append(hits[0])
    assert idx == sorted(idx)
    bounds = [0] + idx + [len(paras)]
    return [paras[bounds[k]:bounds[k + 1]] for k in range(len(bounds) - 1)]


def words(paras):
    return sum(len(p.split()) for p in paras)


def main():
    out = BOOK / "chapters"
    ref = BOOK / "reference"
    out.mkdir(exist_ok=True)
    ref.mkdir(exist_ok=True)
    for old in list(out.glob("*.txt")) + list(ref.glob("*.txt")):
        old.unlink()

    files = []      # (paras, manifest entry)
    note = avertissement()
    files.append(([note], {"title": NOTE_TITLE, "part": 1, "of": 1,
                           "part_before": CLEVES,
                           "source": "Barbin, Le libraire au lecteur"}))
    for k in range(1, 5):
        pieces = split_at(ws_paras(f"cleves-{k}"), CUTS[k])
        for n, piece in enumerate(pieces, 1):
            e = {"title": f"Part {PART_WORD[k]}", "part": n,
                 "of": len(pieces), "source": f"Clèves, partie {k}"}
            if n == 1:
                e["chapter"] = True
            files.append((piece, e))
    mp = ws_paras("montpensier")
    assert len(mp) == 3, [p[:40] for p in mp]
    last = mp[2]
    i = last.index(MONT_CUT)
    assert last[i - 2:i] == ". ", last[i - 20:i]
    m1, m2 = mp[:2] + [last[:i].rstrip()], [last[i:]]
    for n, piece in enumerate((m1, m2), 1):
        files.append((piece, {"title": MONTPENSIER, "part": n, "of": 2,
                              "source": "Montpensier"}))

    perry = perry_slices()
    colt = colt_slices()
    manifest = []
    for no, (paras, e) in enumerate(files):
        fn = f"{no:03d}.txt"
        (out / fn).write_text("\n\n".join(paras) + "\n", encoding="utf-8")
        if 1 <= no <= 12:
            (ref / fn).write_text(PERRY_BANNER.format(fn=fn) + perry[no - 1],
                                  encoding="utf-8")
        elif no >= 13:
            (ref / fn).write_text(COLT_BANNER.format(fn=fn) + colt[no - 13],
                                  encoding="utf-8")
        entry = {"file": fn, **e, "words": words(paras)}
        manifest.append(entry)
        print(f"{fn} {e['title']:30s} {e['part']}/{e['of']} "
              f"{entry['words']:6d}  {paras[0][:50]}")
    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("total French words:", sum(m["words"] for m in manifest))


if __name__ == "__main__":
    main()
