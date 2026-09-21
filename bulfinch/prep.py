"""Thomas Bulfinch, The Age of Fable (1855): a RESTORED EDITION.

    python3 bulfinch/prep.py

DRAFT STAGE. The transcription is Gutenberg #56644, Crowell's "revised and
enlarged" Bulfinch's Mythology of 1913 (DP Canada, 2018): the Age of Fable
is its first part, "Stories of Gods and Heroes". Only that part is taken.
The edition's aim is Bulfinch's own text of 1855, so everything here is to
be checked against two scans of the first edition (scan_diff.py --vote):
    ageoffableorstor00bulfiala   Sanborn, Carter and Bazin, 1855
    cu31924015904067             S. W. Tilton, 1855 (Cornell)
1913 MATTER THAT IS NOT BULFINCH'S is not taken: the Publishers' Preface,
the combined Author's Preface written for all three parts, the list of
illustrations, the maps, the family tree, the plates (photographs of
sculpture and later paintings) and the Glossary.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 41
ETC = 27         # 1855 prints &c. (the vote confirmed 8; OCR mangles the rest)

# THE FIRST EDITION'S READINGS. Every entry is a place where BOTH 1855 scans
# (SCANS) print a reading the 1913 transcription does not (scan_diff.py
# --vote), read in context. Three kinds, and one kind that is NOT restored:
#   - the 1913 revision's respellings (round -> around, upwards, hasted,
#     enamoured, banquetting, ingulphed, imbodied, nought, skilfully,
#     Valkyrior, &c.) reversed;
#   - its altered readings, many of them inside quoted verse, reversed;
#   - its plain slips corrected ("Carlos" for Claros, "Loki" for Logi in
#     the eating match, "sent" for send, "censor" for censer, "Trista");
#   - NOT a misprint of 1855's own: "ardor to the light" (for fight), which
#     both scans print because they are the same stereotype plates. A shared
#     plate shares its errors, so there the two witnesses are one.
# The 1913 punctuation and its quotation marks round titles (1855 sets them
# in italic) are kept: this corrects words, not the house style.
TEXT_FIXES = [
    ("assigned the precedence over", "assigned the presidence over", "1855"),
    ("could see all around in every", "could see all round in every", "1855"),
    ("place for your flocks to graze", "place for your flock to graze", "1855"),
    ("pulled the bough aside", "pulled the boughs aside", "1855, in the quoted verse"),
    ("was lost unless speedy remedy", "was lost unless some speedy remedy", "1855"),
    ("in Phrygia stands a linden", "in Phrygia stand a linden", "1855"),
    ("he cried. Oh, how I trembled", "he cried. O, how I trembled", "1855"),
    ("at her bosom, precious burden", "at her bosom, a precious burden", "1855"),
    ("of my lamentations shall be", "of my lamentation shall be", "1855"),
    ("a voyage to Carlos in Ionia", "a voyage to Claros in Ionia", "1913 slip; the oracle at Claros"),
    ("and tingeing the sky", "and tinging the sky", "1855 spelling"),
    ("arm, inquired her errand", "arm, enquired her errand", "1855 spelling"),
    ("whose motion is not life", "whose motion is nor life", "1855, in the quoted verse"),
    ("“Hymn on the Nativity,” stanzas", "“Hymn to the Nativity,” stanzas", "1855"),
    ("“Hymn on the Nativity,” thus alludes to the fable", "“Hymn to the Nativity,” thus alludes to the fable", "1855"),
    ("“Hymn on the Nativity”:", "“Hymn to the Nativity”:", "1855"),
    ("“Hymn on the Nativity,” thus alludes to the music", "“Hymn to the Nativity,” thus alludes to the music", "1855"),
    ("“Hymn on the Nativity,” alludes to the Egyptian", "“Hymn of the Nativity,” alludes to the Egyptian", "1855 prints 'of' here"),
    ("this view in his “Hymn on the Nativity,”", "this view in his “Hymn of the Nativity,”", "1855 prints 'of' here"),
    ("ascended the mountains, and having", "ascended the mountain, and having", "1855"),
    ("chain-swung censor teeming", "chain-swung censer teeming", "1913 slip; Keats's censer"),
    ("gave the reins to his horses", "gave the rein to his horses", "1855"),
    ("mountains and build their nests", "mountains and built their nests", "1855"),
    ("Their bold steerage", "Their bolder steerage", "1855, in the quoted verse"),
    ("full of light and heart full of play", "full of light and with heart full of play", "1855, in the quoted verse"),
    ("potent for enchantment are produced", "potent for enchantments are produced", "1855"),
    ("of the shells or tortoises", "of the shells of tortoises", "1855"),
    ("failed them and their weapons", "failed them and the weapons", "1855"),
    ("point of the spear in its flight", "point of the spear even in its flight", "1855"),
    ("daughters of Hesperus, assisted", "daughters of Hesperis, assisted", "1855"),
    ("ruddy Isle Erythea", "ruddy Isle Erytheia", "1855"),
    ("afterwards called Medea received", "afterwards called Media received", "1855; the country is Media"),
    ("deeply enamored of Theseus", "deeply enamoured of Theseus", "1855 spelling"),
    ("buoyed upward, and hung", "buoyed upwards, and hung", "1855"),
    ("followers, hastened to her rescue", "followers, hasted to her rescue", "1855"),
    ("Naxian groves of Zante’s", "Naxian groves or Zante’s", "1855, in the quoted verse"),
    ("the purple grapes\n", "the purple grape\n", "1855, in the quoted verse"),
    ("son who should grow greater", "son who should be greater", "1855"),
    ("I yield to you the victory", "I yield you the victory", "1855"),
    ("should not turn around to look", "should not turn round to look", "1855"),
    ("and dwelt in the court of Perian", "and dwelt at the court of Perian", "1855"),
    ("down into the deep blue sea", "down into the blue sea", "1855"),
    ("only on festival occasions", "only on festal occasions", "1855"),
    ("sang their hymns, rending", "sang their hymn, rending", "1855"),
    ("left the banqueting hall", "left the banquetting hall", "1855 spelling"),
    ("In act embodied my deliverance", "In act imbodied my deliverance", "1855 spelling, in the quoted verse"),
    ("trust me, naught shall save", "trust me, nought shall save", "1855 spelling"),
    ("dragged him around the tomb", "dragged him round the tomb", "1855"),
    ("perhaps on the occasion of the truce", "perhaps on occasion of the truce", "1855"),
    ("A cast of it is owned by the Boston Athenæum", "There is a cast of it in the Boston Athenæum", "1855"),
    ("stored with the richest of the flock", "stored with the riches of the flock", "1855"),
    ("thy meal of men’s flesh", "thy meal of man’s flesh", "1855"),
    ("inevitably be ingulfed", "inevitably be ingulphed", "1855 spelling"),
    ("the gods would sent her", "the gods would send her", "1913 slip"),
    ("the hall, the suitors began", "the hall, the suitors soon began", "1855"),
    ("rowers, the vessels shot", "rowers, the vessel shot", "1855"),
    ("gliding onward near the wood", "gliding onward through the wood", "1855"),
    ("against his revolting subjects", "against his revolted subjects", "1855"),
    ("looked up at the skies", "looked up to the skies", "1855"),
    ("appeared as a goddess, surrounded", "appeared as the goddess, surrounded", "1855"),
    ("advent of the Saviour", "advent of the Savior", "1855 spelling"),
    ("Pan himself,\n\tThat simple shepherd", "Pan himself,\n\tThe simple shepherd", "1855, in the quoted verse"),
    ("essayed to embody was", "essayed to imbody was", "1855 spelling"),
    ("in which it was placed. The artist", "in which it is placed. The artist", "1855"),
    ("of the poems belong to Homer", "of the poems belongs to Homer", "1855"),
    ("(the “Trista”", "(the “Tristia”", "1913 slip; Ovid's Tristia"),
    ("made of the skin of salamanders", "made of the skins of salamanders", "1855"),
    ("woman out of an elder", "woman out of an alder", "1855"),
    ("armed with helmets and spears", "armed with helmets, shields, and spears", "1855"),
    ("must come, sends them down", "must come, sends down", "1855"),
    ("The Valkyrie are his messenger", "The Valkyrior are his messenger", "1855; Mallet's form"),
    ("the monster had grown to such", "the monster has grown to such", "1855"),
    ("the hangings of the apartments", "the hangings of her apartments", "1855"),
    ("he had drunk rather less", "he had drank rather less", "1855"),
    ("but Loki was in reality", "but Logi was in reality", "1913 slip; Logi, Fire, is Loki's opponent"),
    # a page in ANOTHER book, kept as printed (the euclid-rivals rule)
    ("Longfellow’s Poems will be found", "Longfellow’s Poems, vol. ii. page 379, will be found", "1855"),
    ("on the same pile as her husband’s", "on the same pile with her husband’s", "1855"),
    ("Frigga, the Valkyrie, and his ravens", "Frigga, the Valkyrior, and his ravens", "1855"),
    ("so skillfully was it wrought", "so skilfully was it wrought", "1855 spelling"),
    ("A minister to her Maker", "A minster to her Maker", "1913 slip; Scott's minster"),
    ("for a simile, “Paradise Lost,” Book I.:", "for a simile, P. L. Book I.:", "1855; the 1913 edition expanded it"),
]


SCANS = ("ageoffableorstor00bulfiala", "cu31924015904067")


def front_1855():
    """The dedication and preface of 1855 (front_1855.txt), checked word by
    word against BOTH first-edition scans, from the dedication's first word
    to the preface's last. They were typed from those scans, so this is a
    check on the typing: every difference printed is an OCR error in one
    scan that the other does not share, and a difference BOTH scans share
    stops the build."""
    import difflib
    import scan_diff
    secs, cur = [], None
    for line in (HERE / "front_1855.txt").read_text().split("\n"):
        if line.startswith("#"):
            continue
        if line.startswith("== "):
            cur = {"title": line[3:], "stream": []}
            secs.append(cur)
        elif line.strip():
            cur["stream"].append(("BLOCK" if line.startswith("\t") else "P", line))
    for s in secs:                       # consecutive tab lines are one block
        out = []
        for it in s["stream"]:
            if it[0] == "BLOCK" and out and out[-1][0] == "BLOCK":
                out[-1] = ("BLOCK", out[-1][1] + "\n" + it[1])
            else:
                out.append(it)
        s["stream"] = out
    ours = scan_diff.words(" ".join(it[1] for s in secs for it in s["stream"]))
    wrong = {}
    for ident in SCANS:
        t = (HERE / "_src" / f"scan-{ident}-djvu.txt").read_text(errors="replace")
        t = t[t.index("HENRY"):]
        t = t[:t.index("fair", t.index("Venus")) + 4]
        t = re.sub(r"\n\s*(?:\(\d\)|\d?\s*-?\s*P\w+\.?\s*\d?|1\s*\*|1\s*•)\s*\n", "\n", t)
        theirs = scan_diff.words(t)
        sm = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "equal":
                wrong.setdefault((i1, " ".join(ours[i1:i2])), []).append(" ".join(theirs[j1:j2]))
    # the scan slice starts at HENRY, after the dedication's "TO", and carries
    # the printed PREFACE heading, which here is the section title
    wrong.pop((0, "to"), None)
    wrong = {k: v for k, v in wrong.items() if not (k[1] == "" and v == ["preface", "preface"])}
    both = {k: v for k, v in wrong.items() if len(v) == 2 and v[0] == v[1]}
    assert not both, both
    return secs


def main():
    book = R.Book(HERE, "pg56644-h.zip")
    h = book.html()
    body = book.body_html(h)
    a = body.index("<h1>STORIES OF GODS AND HEROES</h1>")
    b = body.index("<h1>KING ARTHUR AND HIS KNIGHTS</h1>")
    notes = body[body.index("FOOTNOTES</p>"):body.index("PROVERBIAL EXPRESSIONS</h2>")]
    pe_a = body.rindex("<h2", 0, body.index("PROVERBIAL EXPRESSIONS</h2>"))
    pe_b = body.rindex("<h2", 0, body.index("LIST OF ILLUSTRATIVE PASSAGES</h2>"))
    fable = body[a:b]
    soup = BeautifulSoup(fable + body[pe_a:pe_b] + notes, "html.parser")
    # only the notes the Age of Fable cites; the rest belong to the Age of
    # Chivalry and the Legends of Charlemagne
    cited = set(re.findall(r'href="#f(\d+)"', fable))
    for d in soup.select("div.footnote"):
        sp = d.select_one("span.footnote-id")
        if sp is None or sp["id"][1:] not in cited:
            d.decompose()
    # WHERE EACH PROVERB IS CITED. The appendix says "No. 1. Page 39." and a
    # page number means nothing in a reflowable book, so it names the
    # chapter the 1913 page falls in instead.
    page_chapter, chap = {}, None
    for tok in re.finditer(r'id="Page_(\d+)"|>CHAPTER ([IVXL]+)<', fable):
        if tok.group(2):
            chap = tok.group(2)
        elif chap:
            page_chapter[tok.group(1)] = chap
    for d in soup.select("div.stanza-outer, div.stanza-inner"):
        d["class"] = ["stanza"]
    for p in soup.select("p.line0"):
        p["class"] = ["line"]
    # THE NOTE ANCHORS ARE NAMED f1/r1, which the walker's pattern (fn, foot,
    # note) does not know: unrenamed, every note was left out of its place
    # and all 150 of them piled up at the end of the last chapter
    for sp in soup.select("span.footnote-id"):
        a = soup.new_tag("a", id="fn" + sp["id"][1:])
        sp.replace_with(a)
    for a in soup.find_all("a", href=re.compile(r"^#f\d+$")):
        a["href"] = "#fn" + a["href"][2:]
    for h3 in soup.find_all("h3"):
        m = re.fullmatch(r"No\. (\d+)\. Page (\d+)\.", R.clean(h3.get_text()))
        if m:
            h3.string = f"No. {m.group(1)}. Chapter {page_chapter[m.group(2)]}"
    for d in soup.select("div.figcenter"):
        d.decompose()                    # the 1913 plates (see docstring)
    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, want_title = [], None, False
    for it in items:
        if it[0] == "H":
            t = it[2]
            if it[1] == 1:
                continue
            if it[1] == 2 and t == "PROVERBIAL EXPRESSIONS":
                cur = {"roman": None, "title": "Proverbial Expressions", "stream": []}
                sections.append(cur)
                continue
            m = re.fullmatch(r"CHAPTER ([IVXL]+)\.?", t)
            if it[1] == 2 and m:
                cur = {"roman": m.group(1), "title": None, "stream": []}
                sections.append(cur)
                want_title = True
                continue
            if want_title and it[1] == 3:
                cur["title"] = f"Chapter {cur['roman']}: " + R.titlecase(t.replace("—", " — "))
                want_title = False
                continue
            if it[0] == "H":
                it = ("P", R.titlecase(t))   # a subheading inside a chapter
        if cur is not None:
            cur["stream"].append(it)
    assert len(sections) == CHAPTERS + 1, len(sections)
    for s in sections:
        del s["roman"]
        s["stream"] = [it for it in s["stream"] if it[0] != "HR"]
    R.text_fixes(sections, TEXT_FIXES)
    # "&c." -- 1855's abbreviation throughout; the 1913 edition wrote "etc."
    # -- except the two in Chapter II (Prometheus), which 1855 prints "etc."
    n = 0
    for s in sections:
        if s["title"].startswith("Chapter II:"):
            assert sum(it[1].count("etc.") for it in s["stream"] if it[0] == "P") == 2
            continue
        for k, it in enumerate(s["stream"]):
            if it[0] in ("P", "BLOCK") and "etc." in it[1]:
                n += it[1].count("etc.")
                s["stream"][k] = (it[0], re.sub(r"\betc\.", "&c.", it[1])) + tuple(it[2:])
    assert n == ETC, n
    sections = front_1855() + sections
    R.compose(book, sections, plates=[])
    print(f"{len(sections)} sections, {R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
