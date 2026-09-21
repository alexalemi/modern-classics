"""Bertrand Russell, Introduction to Mathematical Philosophy (1919): a
RESTORED EDITION.

    python3 russell-imp/prep.py

Gutenberg #41654, the second edition of April 1920 (George Allen & Unwin,
Muirhead's Library of Philosophy). Russell wrote it in Brixton prison in
1918, as the plain man's road into Principia Mathematica.

THE MATHEMATICS IS TYPESET, NOT PICTURED (the calculus-made-easy rule):
Gutenberg sets every symbol as an SVG carrying data-tex, 1,527 of them
over 313 distinct files. A formula standing alone in span.align-center is
displayed, \\[...\\]; every other one is inline, \\(...\\). Both renderers
typeset them (mathml.py).

Kept: Russell's Preface, the series editor's note (Muirhead's, part of the
book as published), the eighteen chapters and their footnotes, the two
figures. Dropped: the publisher's advertisement, the title pages, the
Contents (the renderers make it) and the Index.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup, NavigableString  # noqa: E402

CHAPTERS = 18
LLAP_FIX = (r"\begin{aligned} \aleph_{0}^{n} &= \aleph_{0}, \text{ where } n \text{ is any inductive number.} \\ "
            r"\text{(This follows from } \aleph_{0}^{2} &= \aleph_{0} \text{ by induction; for if } "
            r"\aleph_{0}^{n} = \aleph_{0}, \\ \text{then } \aleph_{0}^{n+1} &= \aleph_{0}^{2} = \aleph_{0}.) \end{aligned}")


def main():
    book = R.Book(HERE, "pg41654-h.zip", drop={"cover.jpg": "Gutenberg's cover"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    for sp in soup.select("span.pagenum"):
        sp.decompose()

    # front matter: keep from the Preface on; the Contents and the half
    # title before Chapter I go, and so does the Index
    pref = soup.find("h2", title="PREFACE")
    for el in list(pref.find_all_previous()):
        if el.parent is not None and el not in pref.parents:
            el.decompose()
    toc = soup.find("h2", string="CONTENTS")
    first = soup.find("h2", title=re.compile(r"^I: "))
    node = toc
    while node is not None and node is not first:
        nxt = node.find_next_sibling()
        node.decompose()
        node = nxt
    idx = soup.find(lambda e: e.name == "h2" and R.clean(e.get_text()) == "INDEX")
    for el in list(idx.find_all_next()):
        el.decompose()
    idx.decompose()

    # formulas: SVG + data-tex -> LaTeX text
    n_inline = n_display = n_llap = 0
    for img in soup.find_all("img", attrs={"data-tex": True}):
        tex = " ".join(img["data-tex"].split())
        if "\\llap" in tex:
            # ONE DISPLAY PANDOC CANNOT READ: \llap{$...$} and $n$ inside
            # \text (the second \llap is also missing its closing $). The
            # same three lines, aligned on the equals signs, without them.
            tex = LLAP_FIX
            n_llap += 1
        par = img.parent
        alone = par.name == "span" and "align-center" in (par.get("class") or []) and \
            not R.clean("".join(t for t in par.find_all(string=True)))
        if alone and len(par.find_all("img")) == 1:
            p = soup.new_tag("p")
            p.string = f"\\[{tex}\\]"
            par.replace_with(p)
            n_display += 1
        else:
            img.replace_with(NavigableString(f"\\({tex}\\)"))
            n_inline += 1
    assert n_llap == 1, n_llap
    for sp in soup.select("span.nowrap"):
        sp.unwrap()

    # the two figures float left inside the paragraph that introduces them;
    # the walker only sees a plate that stands on its own, so each goes
    # after its paragraph
    for img in soup.find_all("img", src=re.compile(r"figure\d+\.jpg")):
        par = img.find_parent("p")
        fig = soup.new_tag("div")
        fig["class"] = ["figcenter"]
        fig.append(img.extract())
        par.insert_after(fig)
    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = it[2]
            if t == "INTRODUCTION TO MATHEMATICAL PHILOSOPHY":
                continue                      # the half title before Chapter I
            if t == "PREFACE":
                cur = {"title": "Preface", "stream": []}
            elif t.startswith("EDITOR"):
                cur = {"title": "Editor's Note", "stream": []}
            else:
                m = re.fullmatch(r"CHAPTER ([IVXL]+) (.+)", t)
                assert m, it
                cur = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2))}", "stream": []}
            sections.append(cur)
            continue
        cur["stream"].append(it)
    assert [s["title"] for s in sections][:2] == ["Preface", "Editor's Note"]
    assert len(sections) == 2 + CHAPTERS, [s["title"] for s in sections]

    plates = [{"src": it[1], "printed": it[2]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    R.all_images_placed(book, plates, extra_ok={f.split("/")[-1] for f in book.zip.namelist() if f.endswith(".svg")})
    # scan vote (scan_diff.py --vote) against both 1920 printings,
    # cu31924005723113 and introductiontoma00russuoft: one reading
    R.text_fixes(sections, [("keeping the order of the pairs unchanged", "keeping the order of the pair unchanged",
                             "both 1920 printings")])
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {n_inline} inline + {n_display} displayed formulas, "
          f"{len(rows)} figures, {described} described")


if __name__ == "__main__":
    main()
