"""Catharine E. Beecher and Harriet Beecher Stowe, The American Woman's
Home (New York: J. B. Ford, 1869): a RESTORED EDITION.

    python3 beecher/plates.py      # cut the figures from the 1869 scan
    python3 beecher/prep.py

TEXT: Project Gutenberg #6598 (Distributed Proofreaders), checked against
two scans of the 1869 first edition with scan_diff.py --vote; the readings
the scans settle are in SOURCE_FIXES.

FIGURES: Gutenberg's transcription is text only -- every figure is a bare
"[Illustration: Fig. N]". The pictures are cut from the University of
California's 500-ppi scan of the 1869 edition (Archive.org
americanwomansho00beecrich) by plates.py, and put back where Gutenberg's
markers stand. Each keeps its printed label; plates.json pins the ids.

KEPT: the dedication, the Introduction, the thirty-eight chapters, the
Appeal to American Women, and the Appendix (the authors' Glossary for the
young reader). THE CONTENTS IS NOT KEPT AS A LIST, but its chapter
summaries are -- the body chapters carry none, and the summaries are the
book's own guide to each -- each set in italics under its chapter title.
DROPPED: the title page and the Contents as a list (the renderers make
one).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 38
SOURCE_FIXES = []          # (bad, good, why), each matching exactly once
SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"}


def title(s):
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    if s.upper() != s:
        return s
    ws = s.lower().split()
    out = []
    for i, w in enumerate(ws):
        if i and w in SMALL:
            out.append(w)
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


def italic(summary):
    """A chapter summary in italics, phrase by phrase: the renderers'
    emphasis spans at most 400 characters, and most summaries run longer.
    The dashes between phrases stay roman."""
    return "—".join(f"*{p.strip()}*" if p.strip() else p for p in re.split(r"—", summary))


def contents(soup):
    """[(numeral, title, summary)] from the Contents, and remove it."""
    h = soup.find(lambda e: re.fullmatch(r"h\d", e.name or "") and R.clean(e.get_text()).startswith("TABLE OF CONTENTS"))
    nodes, node = [], h.find_next_sibling()
    while node is not None and not (re.fullmatch(r"h\d", node.name or "") and R.clean(node.get_text()).startswith("INTRODUCTION")
                                    and node.find_next_sibling() is not None
                                    and not re.match(r"The chief cause", R.clean(node.find_next_sibling().get_text()))):
        nodes.append(node)
        node = node.find_next_sibling()
    # keep the source's line breaks: a numeral can end a paragraph's last
    # line ("...mission of woman.\nXXXVIII.") and must start a line here
    text = "\n".join("\n".join(R.clean(l) for l in n.get_text().split("\n")) for n in nodes)
    for n in nodes:
        n.decompose()
    h.decompose()
    parts = re.split(r"(?:^|\n)\s*([IVXL]+)\.\s*", "\n" + text)
    intro = parts[0]
    entries = []
    for k in range(1, len(parts), 2):
        body = parts[k + 1].strip()
        # the title is the run of capitalised words before the summary,
        # whether a line break or only a stop separates them
        m = re.match(r"((?:[A-Z][A-Z,'’;\-]*|Of)(?:[ \n]+(?:[A-Z][A-Z,'’;\-]*|Of))*)\.?\s+(.*)$", body, re.S)
        assert m, (parts[k], body[:80])
        head, summ = m.group(1), m.group(2)
        entries.append((parts[k], " ".join(head.split()).rstrip(".").replace(" Of ", " OF "), " ".join(summ.split())))
    intro_sum = " ".join(re.sub(r"^\s*INTRODUCTION\.?", "", intro).split())
    return intro_sum, entries


def main():
    book = R.Book(HERE, "pg6598-h.zip", source_fixes=SOURCE_FIXES,
                  replace={p.name: str(p) for p in sorted((HERE / "plates").glob("*.jpg"))},
                  long_side=1600)
    book.drop["6598-cover.png"] = "the transcriber's cover"
    soup = BeautifulSoup(book.body_html(book.html()), "html.parser")
    intro_sum, toc = contents(soup)
    assert len(toc) == CHAPTERS, len(toc)

    # the dedication: everything before the Introduction except the title
    intro = soup.find(lambda e: re.fullmatch(r"h\d", e.name or "") and R.clean(e.get_text()) == "INTRODUCTION.")
    dedication = None
    for el in list(intro.find_all_previous()):
        if el.parent is None or el in intro.parents:
            continue
        t = R.clean(el.get_text(" "))
        if t.startswith("TO THE WOMEN OF AMERICA"):
            dedication = t
        el.decompose()
    assert dedication

    # Gutenberg's figure markers -> images the plates step supplies
    labels = {}
    MARK = re.compile(r"\[(?:Illustration|Image):?\s*(?:Fig\.?\s*(\d+)\.?)?\s*([^\]]*)\]")
    for p in soup.find_all("p"):
        t = R.clean(p.get_text())
        marks = list(MARK.finditer(t))
        if not marks:
            continue
        lead = MARK.match(t)
        if MARK.sub("", t).strip():
            # a marker opening a paragraph of text (Figs. 45, 71): the
            # picture goes before it and the marker leaves the text
            if not lead:
                continue
            marks = [lead]
            first = next(x for x in p.descendants if isinstance(x, str) and x.strip())
            assert first.strip().startswith(lead.group(0)[:12]), (first[:40], lead.group(0))
            first.replace_with(first.replace(lead.group(0), "", 1).lstrip())
        div = soup.new_tag("div")
        div["class"] = ["figcenter"]
        for m in marks:
            # every form the transcription uses: "[Illustration: Fig. 1.]",
            # "[Illustration Fig 37]", "[Illustration: Fig. 21. Floor plan]",
            # a bare "[Illustration]", "[Image: Panel screens]", and runs
            # of several in one paragraph
            if m.group(1):
                src = f"fig{int(m.group(1)):02d}.jpg"
            elif m.group(2):
                src = "panel-screens.jpg"
            else:
                src = "vignette.jpg"
            assert src not in labels, src
            labels[src] = f"Fig. {int(m.group(1))}." if m.group(1) else ""
            div.append(soup.new_tag("img", src=src))
        if MARK.sub("", R.clean(p.get_text())).strip():
            p.insert_before(div)
        else:
            p.replace_with(div)
    print(len(labels), "markers;", "numbers missing:",
          [n for n in range(1, 78) if f"fig{n:02d}.jpg" not in labels])

    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, chap = [], None, 0
    for it in items:
        if it[0] == "H":
            t = R.clean(re.sub(r"\s+", " ", it[2]))
            if t == "INTRODUCTION.":
                cur = {"title": "Introduction", "stream": [("P", italic(intro_sum))]}
                sections.append(cur)
                continue
            m = re.fullmatch(r"(?:CHAPTER )?([IVXL]+)\.(?:\s+(.*))?", t)
            if m and it[1] <= 3 and chap < CHAPTERS:
                num, name, summ = toc[chap]
                chap += 1
                cur = {"title": f"Chapter {chap}: {title(name)}", "stream": [("P", italic(summ))]}
                sections.append(cur)
                continue
            if t.startswith("AN APPEAL TO AMERICAN WOMEN"):
                cur = {"title": "An Appeal to American Women", "stream": [("P", "*By the senior author of this volume.*")]}
                sections.append(cur)
                continue
            if t == "APPENDIX.":
                cur = {"title": "Appendix: Glossary", "stream": []}
                sections.append(cur)
                continue
            if t.startswith("GLOSSARY OF SUCH WORDS"):
                cur["stream"].append(("P", title(t)))
                continue
            # the chapter title repeated as its own heading under the numeral
            # -- whatever its wording: the body sometimes prints a fuller
            # title than the Contents ("The Preservation of Good Temper in
            # the Housekeeper"), and Gutenberg misreads one ("The Case of
            # Servants"). A heading straight after the summary is the title.
            if sections and cur["title"].startswith("Chapter") and len(cur["stream"]) == 1:
                continue
            if t.startswith("CATHARINE E. BEECHER"):
                cur["stream"].append(("P", "—Catharine E. Beecher."))
                continue
            cur["stream"].append(("P", title(t)))
            continue
        assert cur is not None, it
        cur["stream"].append(it)
    sections.insert(0, {"title": "Dedication", "stream": [("P", "*" + dedication[0] + dedication[1:].lower().replace("america", "America").replace("republic", "Republic") + "*")]})
    assert chap == CHAPTERS, chap
    print([s["title"] for s in sections][:3], "...", [s["title"] for s in sections][-3:])

    # PLACEMENT beyond Gutenberg's markers. The scan settles it:
    #  - the frontispiece and the engraved title page open the book;
    #  - the two chapter headpieces sit above Chapters 1 and 2 (Gutenberg
    #    kept one bare "[Illustration]", at the end of the Introduction);
    #  - Figs. 3, 17 and 27 have no marker: each follows the paragraph that
    #    first cites it;
    #  - "[Image: Panel screens]" names no picture of its own (the screen is
    #    Fig. 5, which has its marker) and is dropped.
    for s_ in sections:
        s_["stream"] = [it for it in s_["stream"]
                        if not (it[0] == "PLATE" and it[1] in ("vignette.jpg", "panel-screens.jpg"))]
    sections[0]["stream"][:0] = [("PLATE", "frontispiece.jpg", ""), ("PLATE", "title.jpg", "")]
    sections[2]["stream"].insert(0, ("PLATE", "vignette.jpg", ""))
    sections[3]["stream"].insert(0, ("PLATE", "vignette2.jpg", ""))
    for n in (3, 17, 27):
        src = f"fig{n:02d}.jpg"
        done = False
        for s_ in sections:
            for k, it in enumerate(s_["stream"]):
                if it[0] == "P" and re.search(rf"\bFig\. {n}\b", it[1]):
                    s_["stream"].insert(k + 1, ("PLATE", src, ""))
                    done = True
                    break
            if done:
                break
        assert done, n
        labels[src] = f"Fig. {n}."
    # printed captions beyond the label, as the page readers transcribed them
    figs = {r["file"]: r for r in json.loads((HERE / "figures.json").read_text())}
    for src, r in figs.items():
        if r["caption"] and src in labels:
            labels[src] = f"{labels[src]} {r['caption']}"

    # THE TEXT, AS PRINTED. Gutenberg's 2004 transcription misreads its
    # page images in about a hundred places ("whore" for where, "broad"
    # for bread, "he" for be); scan_diff.py --vote found each where two
    # scans of the 1869 printing (Cornell, cu31924032631412; UC,
    # americanwomansho00beecrich) agree against it. vote_fixes.json holds
    # each reading as a unique phrase (a word and its neighbours); readings
    # that were only OCR noise in both scans are not in it. The period
    # spellings both copies print (unvail, milch, unfrequently, potass,
    # stupified) are restored with them.
    fixes = [(a, b, "two scans agree") for a, b in json.loads((HERE / "vote_fixes.json").read_text())]
    fixes += [("a land of combustion", "a kind of combustion", "two scans agree"),
              ("a land of pendent", "a kind of pendent", "two scans agree"),
              ("the ease, that persons", "the case, that persons", "two scans agree"),
              ("the ease that soliciting", "the case that soliciting", "two scans agree"),
              ("for milk cows", "for milch cows", "two scans agree", 2),
              ("Ha was appointed", "He was appointed", "two scans agree"),
              ("warm-air fine,", "warm-air flue,", "two scans agree"),
              ("back-damper, snake the", "back-damper, shake the", "two scans agree"),
              ("drawers or both", "drawers on both", "two scans agree"),
              ("a *Nasturtium* may", "a *Nasturtion* may", "the 1869 spelling, both scans")]
    R.text_fixes(sections, fixes)

    plates = [{"src": it[1], "printed": labels.get(it[1], "")} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    seen = [p["src"] for p in plates]
    assert len(seen) == len(set(seen)), "a figure placed twice"
    assert set(seen) == set(figs) or "--text" in sys.argv, (sorted(set(figs) - set(seen)), sorted(set(seen) - set(figs)))
    if "--text" in sys.argv:          # before the figures are cut
        for s in sections:
            s["stream"] = [it for it in s["stream"] if it[0] != "PLATE"]
        plates = []
    else:
        missing = [p["src"] for p in plates if p["src"] not in book.replace]
        assert not missing, f"no cut image for {missing[:8]}"
    rows, described = R.compose(book, sections, plates=plates, captions_dir=HERE / "captions")
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described, "
          f"{R.words([it for s in sections for it in s['stream']]):,} words")


if __name__ == "__main__":
    main()
