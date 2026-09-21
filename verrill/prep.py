"""A. Hyatt Verrill, Knots, Splices and Rope Work (1917): a RESTORED EDITION.

    python3 verrill/prep.py

Gutenberg #13510, from the Norman W. Henley second edition of 1917 (the
preface is dated January 1917). Screened clean -- arch 0.00, 16-word
sentences -- an edition, not a retelling.

THE PLATES CARRY THE BOOK: 149 drawings, one knot or one stage of a splice
each, with the printed label ("FIG. 1.--Construction of Rope.") kept as the
plate's label. Gutenberg records those labels only in each image's alt
text, so they are read from there. What this edition adds is a description
of every drawing (captions/): the label names the knot, the description
says how the rope runs, which is what a reader who cannot see the drawing
needs in order to tie it.

THE NUMBERING SKIPS FIG. 134 IN PRINT: the 1917 scan goes from "Fig. 133.--
Matthew Walker (complete)" straight to the Turk's head, "Figs. 135 and
136", so 148 drawings is the whole set and nothing is missing.

This transcription is an early one, with most of its body in
pg_body_wrapper divs that open around an image and swallow the paragraph
after it (the aesop/calculus trap); the walker flattens them, and the raw
word count is the witness that nothing inside them was lost.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 7
# Gutenberg's alt text gives fig65.gif the label of the drawing before it;
# the plate prints "FIG. 65." and the text says "Figs. 62-65"
LABEL_FIX = {"fig65.gif": "FIG. 65.—Loop knot."}


def main():
    book = R.Book(HERE, "pg13510-h.zip", drop={"title.gif": "the title page"} if False else {})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")

    # chapter titles from the book's own Contents ("CHAPTER VI / LASHINGS,
    # SEIZINGS, SPLICES, ETC."); each must also open its chapter in the body
    toc_text = "\n".join(R.clean(x) for x in soup.find(string="CONTENTS").find_parent().find_all_next(string=True)
                          if R.clean(x))
    toc_text = toc_text[:toc_text.index("INDEX")]
    toc = dict(re.findall(r"CHAPTER ([IVX]+)\n([A-Z][A-Z ,.'\-]+)\n", toc_text))
    assert len(toc) == CHAPTERS, toc
    intro = soup.find("h2", string="INTRODUCTION")
    title_img = soup.find("img", alt="Title Page")
    dropped = {title_img["src"].split("/")[-1]: "the title page"} if title_img else {}
    for el in list(intro.find_all_previous()):
        if el.parent is not None and el not in intro.parents:
            el.decompose()
    idx = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "INDEX")
    for el in list(idx.find_all_next()):
        el.decompose()
    idx.decompose()
    book.drop.update(dropped)

    # printed labels live in the alt text
    labels = {}
    for img in soup.find_all("img"):
        alt = R.clean(img.get("alt") or "")
        src = img["src"].split("/")[-1]
        m = re.fullmatch(r"\[?Illustration: (.+?)\]?", alt)
        assert m, (src, alt)
        lab = m.group(1).replace("—", ".—") if re.match(r"FIGS?\. [\d, and]+—", m.group(1)) else m.group(1)
        # a few alt texts carry the label's italic letter as markup,
        # "(<i>A</i>)"; an alt attribute is plain text
        lab = re.sub(r"</?i>", "", lab)
        labels.setdefault(src, LABEL_FIX.get(src, lab))
        # the walker takes a plate from a figure-class element
        wrap = soup.new_tag("div")
        wrap["class"] = ["figcenter"]
        img.replace_with(wrap)
        wrap.append(img)

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = it[2]
            if t == "INTRODUCTION":
                cur = {"title": "Introduction", "stream": []}
                sections.append(cur)
                continue
            m = re.fullmatch(r"CHAPTER ([IVX]+)", t)
            if m:
                cur = {"title": f"Chapter {m.group(1)}", "stream": [], "roman": m.group(1)}
                sections.append(cur)
                continue
            cur["stream"].append(("P", R.titlecase(t)))
            continue
        if it[0] == "P" and cur.get("roman") and cur["title"] == f"Chapter {cur['roman']}":
            # the chapter's own title, set in bold capitals under its number
            # the heading as printed over the chapter governs; the Contents
            # must agree on the words (it punctuates IV differently)
            key = lambda t: re.findall(r"[A-Z]+", t)
            assert key(it[1]) == key(toc[cur["roman"]]), (it[1], toc[cur["roman"]])
            cur["title"] += ": " + R.titlecase(it[1].strip("*"), keep=("ETC.",)).replace("ETC.", "etc.")
            continue
        cur["stream"].append(it)
    for s in sections:
        s.pop("roman", None)
    print([s["title"] for s in sections])
    assert len(sections) == 1 + CHAPTERS

    # witness: the raw HTML's words from the Introduction to the Index
    import html as HTML
    raw_b = body[body.index("<h2>INTRODUCTION</h2>"):]
    raw_b = re.sub(r"<img[^>]*>", " ", raw_b[:raw_b.index(">INDEX<")])
    raw = len([x for x in HTML.unescape(re.sub(r"<[^>]+>", " ", raw_b)).split() if re.search(r"\w", x)])
    got = R.words([it for s in sections for it in s["stream"]]) + sum(len(s["title"].split()) for s in sections)
    assert abs(raw - got) <= 0.005 * raw, (raw, got)
    # two paragraphs the transcription cut around a plate
    assert R.mend_plate_splits(sections) == 2

    plates = []
    for s in sections:
        for k, it in enumerate(s["stream"]):
            if it[0] == "PLATE":
                plates.append({"src": it[1], "printed": labels[it[1]]})
    srcs = [p["src"] for p in plates]
    dup = sorted({x for x in srcs if srcs.count(x) > 1})
    print("placed twice:", dup)
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
