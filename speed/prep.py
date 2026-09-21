"""Harold Speed, The Practice and Science of Drawing (1913): a RESTORED
EDITION.

    python3 speed/prep.py

Gutenberg #14264, from Seeley, Service & Co.'s first edition of 1913.
Screened clean -- arch 0.04 -- an edition, not a retelling.

Kept: the Preface, the twenty-one chapters, the Appendix (Speed's own note
on proportion), and all eighty-eight illustrations: the plates (drawings by
Leonardo, Holbein, Dürer, Michelangelo and others, and Speed's own studies)
and the diagrams. Gutenberg ships every image twice, at two sizes; the
larger (30ppi) is used. Dropped: the title page, the Contents, the Lists
of Plates and Diagrams (the renderers make them) and the Index.

THE PRINTED LABELS are the book's ("Plate II. Drawing by Leonardo da Vinci
from the Royal Collection at Windsor"). Gutenberg keeps them twice, as
figure text in capitals and in each image's alt; the alt is used, cased as
a title, with the printers' photograph credits kept.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 21
IMAGES = 88


def label(alt):
    """'Plate I. FOUR PHOTOGRAPHS OF ... BRUSH' -> 'Plate I. Four Photographs
    of ... Brush'. Only a run in capitals is recased; a credit in ordinary
    type after it ("Copyright photo, Braun & Co.") stays as printed."""
    m = re.match(r"((?:Plate|Diagram|PLATE|DIAGRAM) [IVXLC]+\.)\s*(.*)", alt)
    if not m:
        return alt
    head, rest = m.groups()
    # the title is the leading run of words in capitals; a one-letter word
    # followed by a lower-case one ("... SHANNON A splendid example") opens
    # the note in ordinary type, not the title
    words = rest.split()
    k = 0
    while k < len(words) and not re.search(r"[a-z]", words[k]) and re.search(r"[A-Z]", words[k]):
        if len(words[k]) == 1 and k + 1 < len(words) and re.match(r"[a-z]", words[k + 1]):
            break
        k += 1
    if k:
        # single letters and two-letter codes ("CONE A", "WINDOW BC") are the
        # diagrams' own letter names, not words to be cased
        cased = R.titlecase(" ".join(words[:k])).split()
        assert len(cased) == k
        for j, w in enumerate(words[:k]):
            # a punctuated letter or pair ("A,", "BC;", "D.") is a label
            if re.fullmatch(r"[A-Z]{1,2}[.,;:]", w) or (re.fullmatch(r"[A-Z]", w) and j + 1 == k):
                cased[j] = w
        rest = " ".join(cased + words[k:])
    head = re.sub(r"^(PLATE|DIAGRAM)", lambda x: x.group(1).title(), head)
    return f"{head} {rest}".strip().replace(" Da Vinci", " da Vinci").replace(" Van ", " van ").replace(" Del ", " del ")


def main():
    names = [n for n in R.Book(HERE, "pg14264-h.zip").zip.namelist() if "/30ppi/" in n]
    src_dir = HERE / "_src" / "pg" / "images"
    book = R.Book(HERE, "pg14264-h.zip",
                  drop={**{n.split("/")[-1]: "the larger copy is used" for n in names}, "cover.jpg": "Gutenberg cover"},
                  replace={n.split("/")[-1]: str(src_dir / "30ppi" / n.split("/")[-1]) for n in names})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum"):
        sp.decompose()

    labels = {}
    for img in soup.find_all("img"):
        labels[img["src"].split("/")[-1]] = label(R.clean(img.get("alt") or ""))
    labels["plate19.jpg"] = labels["plate19.jpg"].replace("Curved Links", "Curved Lines")   # the plate prints LINES
    # the two halves of Diagram XIV print "(1)" and "(2)"; the label names neither
    for part in ("1", "2"):
        labels[f"diagram14-{part}.jpg"] = labels[f"diagram14-{part}.jpg"].replace("Diagram XIV.", f"Diagram XIV ({part}).")
    # a slip in the transcribed label, read against the plate itself
    old = labels["plate46.jpg"]
    labels["plate46.jpg"] = old.replace("low direct light elimination half-tones", "low direct light eliminating half-tones")
    assert labels["plate46.jpg"] != old
    # the figure text repeats the label in capitals: drop it, the plate
    # keeps the label
    for fig in soup.select("div.figure"):
        for p in fig.find_all("p"):
            p.decompose()

    pref = soup.find("h2", string="PREFACE")
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    for title in ("CONTENTS", "LIST OF PLATES", "LIST OF DIAGRAMS"):
        hh = soup.find("h2", string=title)
        node = hh
        while node is not None:
            nxt = node.find_next_sibling()
            if node is not hh and node.name == "h2":
                break
            node.decompose()
            node = nxt
    idx = soup.find("h2", string="INDEX")
    for el in list(idx.find_all_next()):
        el.decompose()
    idx.decompose()

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H" and it[1] == 2:
            t = it[2]
            if t == "PREFACE":
                # Plate I is the frontispiece, before the dropped title page
                cur = {"title": "Preface", "stream": [("PLATE", "plate01.jpg", "")]}
            elif t == "APPENDIX":
                cur = {"title": "Appendix", "stream": []}
            elif t == "THE PRACTICE AND SCIENCE OF DRAWING":
                continue
            else:
                m = re.fullmatch(r"([IVXL]+) (.+)", t)
                assert m, it
                cur = {"title": f"{m.group(1)}. {R.titlecase(m.group(2))}", "stream": []}
            sections.append(cur)
            continue
        if it[0] == "H":
            cur["stream"].append(("P", R.titlecase(it[2]) if it[2].isupper() else it[2]))
            continue
        cur["stream"].append(it)
    assert len(sections) == 2 + CHAPTERS, [s["title"] for s in sections]

    plates = [{"src": it[1], "printed": labels[it[1]]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert len(plates) == IMAGES, len(plates)
    R.all_images_placed(book, plates)
    n = R.mend_plate_splits(sections)
    # PAGE REFERENCES. Speed cites illustrations by page ("on page 114") and
    # the transcription adds a note naming the plate ("[Transcribers Note:
    # Plate XXVI]"). A reflowable book has no pages, so the reference becomes
    # the plate's own name. Two of the notes name the wrong plate and are
    # corrected first, each checked against the label and the picture: page
    # 114 is the brush strokes, Plate XXV; page 60 is Las Meninas, Plate XI.
    R.text_fixes(sections, [
        ("page 114 [Transcribers Note: Plate XXVI]", "page 114 [Transcribers Note: Plate XXV]", "the brush-stroke plate is XXV", 2),
        ("page 60 [Transcribers Note: Plate IX]", "page 60 [Transcribers Note: Plate XI]", "Las Meninas is Plate XI"),
    ])
    nref = 0
    for s in sections:
        for k, it in enumerate(s["stream"]):
            if it[0] in ("P", "BLOCK") and "Transcriber" in it[1]:
                t = re.sub(r"\b(\d+) \[Transcribers? Note: ([^\]]+)\]", r"\2", it[1])
                nref += it[1].count("Transcriber")
                t = re.sub(r"\bpages? (?=(?:Plate|Diagram) [IVXLC]+\b)", "", t)
                assert "Transcriber" not in t and not re.search(r"\bpages? \d", t), t[:200]
                s["stream"][k] = (it[0], t) + tuple(it[2:])
    assert nref == 48, nref
    # Speed's own page references, with no note: each mapped through the
    # transcription's page anchors to what stood on that page
    R.text_fixes(sections, [
        ("On pages 66 and 67 a reproduction", "In Plates XII and XIII a reproduction", "pp. 66-67 hold Plates XII and XIII"),
        ("what is said later (page 162) about", "what is said later (in Chapter XII) about", "p. 162 is in Chapter XII"),
        ("(see later, pages 192 *et seq.*, variety of edges)", "(see later, Chapter XIII, variety of edges)", "p. 192 is in Chapter XIII"),
        ("this description on pages 110 and 122.", "this description in Plates XXIII-XXIV and XXVI-XXIX.", "pp. 110-111 and 122-123"),
        ("(See diagrams, pages 166 and 168,", "(See Diagrams XV and XVI,", "pp. 166 and 168"),
        ("in the Appendix, page 289, you", "in the Appendix you", "p. 289 is the Appendix"),
    ])
    # scan vote (scan_diff.py --vote) against both 1913 printings,
    # practicescienceo00speeiala and cu31924014534881. Most of its readings
    # are Speed's marginal sidenotes read into the line by the OCR; two are
    # real, and Gutenberg's "Los Meninas" is left corrected (a misprint)
    R.text_fixes(sections, [
        ("another form of balance that must be although", "another form of balance that must be mentioned, although",
         "a word the transcription dropped; both printings"),
        ("line of the hacks of the sheep", "line of the backs of the sheep", "transcription typo; both printings"),
    ])
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, {n} mended, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")
    print([s["title"] for s in sections])


if __name__ == "__main__":
    main()
