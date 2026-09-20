"""Benjamin N. Cardozo, The Nature of the Judicial Process (1921): a
RESTORED EDITION.

    python3 nature-of-the-judicial-process/fetch.py   # once
    python3 nature-of-the-judicial-process/prep.py

Not on Gutenberg. The text is Wikisource's, transcluded from a VALIDATED
index (every page proofread twice against the scan) of the Yale
University Press edition; the scan is of the eleventh printing, 1941,
from the 1921 plates. Four Storrs Lectures, given at Yale in 1921, and the
publisher's memorial leaf for Arthur P. McKinstry, in whose memory the
volume was published. Checked against the printed Contents.

Wikisource's own apparatus is removed (headers, page anchors, the drop
initial set as a separate letter), and its reference lists become the
walker's footnotes, each set after the paragraph that cites it.
"""
import io
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

ROMAN = ["I", "II", "III", "IV"]

# SCAN VOTE, against two 1921 Yale copies (natureofthejudic008454mbp,
# A0116300578212A): readings both print and the transcription lacks.
# Wikisource's pages are proofread by hand, and a typing slip survives
# proofreading exactly when it is a real word ("bad" for had, "ray" for
# my, "giver" for given, "fails" for falls). Each was located by the words
# either side of it and must match once.
TEXT_FIXES = [
    ('Yale University lost and alumnus of whom', 'Yale University lost an alumnus of whom', "both scans"),
    ('his time and though to his class', 'his time and thought to his class', "both scans"),
    ('it. In the longer run "there is', 'it. In the long run "there is', "both scans"),
    ('method of free decisions has become, I', 'method of free decision has become, I', "both scans"),
    ('behind them. Interpretation, this enlarged, becomes more', 'behind them. Interpretation, thus enlarged, becomes more', "both scans"),
    ('the significance of the constitution and statute', 'the significance of constitution and statute', "both scans"),
    ('that precedents are the ultimate sources of', 'that precedents are ultimate sources of', "both scans"),
    ('is charged with a vital power. It', 'is charged with vital power. It', "both scans"),
    ('to maturity. Those than cannot prove their', 'to maturity. Those that cannot prove their', "both scans"),
    ('not threaten to dissolved." Those are the', 'not threaten to dissolve." Those are the', "both scans"),
    ('watching the growing sceptisim of his day', 'watching the growing scepticism of his day', "both scans"),
    ('he bought for the purposes of suit', 'he bought for purposes of suit', "both scans"),
    ('who wrought them use the same tools', 'who wrought them used the same tools', "both scans"),
    ('every rule its antimony. Nothing is stable', 'every rule its antinomy. Nothing is stable', "both scans"),
    ('leave more to legislature today, and less', 'leave more to legislatures today, and less', "both scans"),
    ('of all persons of the world, should', 'of all persons in the world, should', "both scans"),
    ('fix the bounds an the tendencies of', 'fix the bounds and the tendencies of', "both scans"),
    ('legitimate one, to protect and extend itself', 'legitimate one, to project and extend itself', "both scans"),
    ('Great judges bave sometimes spoken as', 'Great judges have sometimes spoken as', "both scans"),
    ('likely," says Maitland, a “that the historical', 'likely," says Maitland, “that the historical', "both scans"),
    ('if recent history bad not discredited it', 'if recent history had not discredited it', "both scans"),
    ('blaze the path. Ever as late as', 'blaze the path. Even as late as', "both scans"),
    ('to its function, maintains its power', 'to its function, it maintains its power', "both scans"),
    ('in New York or profess to find', 'in New York profess to find', "both scans"),
    ('When that rule bas been ascertained, it', 'When that rule has been ascertained, it', "both scans"),
    ('away from what Ebrlich calls "die spielerische', 'away from what Ehrlich calls "die spielerische', "both scans"),
    ('less, within the confides of these open', 'less, within the confines of these open', "both scans"),
    ('the exercise of giver rights, by introducing', 'the exercise of given rights, by introducing', "both scans"),
    ('by judicial decisions of the development of', 'by judicial decisions or the development of', "both scans"),
    ('Digest. We should bc traveling too far', 'Digest. We should be traveling too far', "both scans"),
    ('to deduce and is the element of', 'to deduce and fix the element of', "both scans"),
    ('determined somehow, there nothing to do', 'determined somehow, there is nothing to do', "both scans"),
    ('and most often it despite of it', 'and most often in despite of it', "both scans"),
    ('of the meaning of operation of a', 'of the meaning or operation of a', "both scans"),
    ('whenever the surety car show that the', 'whenever the surety can show that the', "both scans"),
    ('of the security bas been impaired, though', 'of the security has been impaired, though', "both scans"),
    ('sweep of forces, ray petty personality should', 'sweep of forces, my petty personality should', "both scans"),
    ('tide rises and fails, but the sands', 'tide rises and falls, but the sands', "both scans"),
    ("the Hecksher Foundation", "the Heckscher Foundation", "both scans"),
    ("the truth with- out us", "the truth without us", "a word split at the page turn"),
    ("the degree of LL,B. *magna", "the degree of LL.B. *magna", "a typing slip"),
]
SPELLING = [("judgements", "judgments"), ("judgement", "judgment")]      # both scans, throughout


def clean_page(html, notes_prefix):
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.select("style, .ws-noexport, .wst-header, .ws-header, .pagenum, .ws-pagenum, .__nop"):
        s.decompose()
    # the drop initial: "T" + small-capital "HE" -> "The"
    for d in soup.select(".dropinitial"):
        letter = d.get_text()
        nxt = d.find_next(string=True)
        while nxt is not None and not nxt.strip():
            nxt = nxt.find_next(string=True)
        rest = str(nxt)
        m = re.match(r"^(\s*)([A-Z]+)", rest)
        new = letter + (m.group(2).lower() + rest[m.end():] if m else rest)
        nxt.replace_with(new)
        d.decompose()
    # references -> footnotes the walker knows
    for li in soup.select("ol.references li"):
        n = li["id"].split("-")[-1]
        txt = li.select_one(".reference-text")
        p = soup.new_tag("p", attrs={"class": "footnote"})
        a = soup.new_tag("a", attrs={"id": f"fn_{notes_prefix}{n}"})
        p.append(a)
        for c in list(txt.contents):
            p.append(c.extract())
        li.replace_with(p)
    for ol in soup.select("ol.references"):
        ol.unwrap()
    for a in soup.select('sup.reference a[href^="#cite_note"]'):
        n = a["href"].split("-")[-1]
        a["href"] = f"#fn_{notes_prefix}{n}"
        a.string = n
        a.parent.unwrap()
    return soup


def main():
    zp = HERE / "_src" / "cardozo.zip"
    z = zipfile.ZipFile(zp)
    book = R.Book(HERE, "cardozo.zip", html_name="lectureI.html",
                  flatten={"prp-pages-output", "mw-parser-output", "mw-content-ltr", "wst-block-center", "tiInherit"})
    # the Contents (page 7): the witness for the lecture titles
    toc_soup = BeautifulSoup(z.read("page7.html").decode(), "html.parser")
    toc = [R.clean(a.get_text()) for a in toc_soup.find_all("a") if "Lecture" in a.get_text()]
    assert len(toc) == 4, toc
    sections = []
    # the memorial leaf (pages 5-6), from the page WIKITEXT: the rendered
    # Page: HTML carries Wikisource's proofreading notice and the folio.
    # One paragraph crosses the page turn ("Hecksher Founda-" / "tion").
    wiki = "".join(re.sub(r"<noinclude>.*?</noinclude>", "", z.read(f"page{p}.wiki").decode(), flags=re.S)
                   for p in (5, 6))
    wiki = wiki.replace("Founda-tion", "Foundation")
    wiki = re.sub(r"\{\{(?:c|larger|smaller|center)\|", "", wiki).replace("}}", "")
    wiki = re.sub(r"''(.+?)''", r"*\1*", wiki).replace(",--", ",—").replace("--", "—")
    memo = []
    for par in re.split(r"\n\s*\n", wiki):
        for line in [l.strip() for l in par.split("\n") if l.strip()]:
            pass
        t = R.clean(par)
        if t:
            if re.fullmatch(r"[A-Z .]+Mc[A-Z]+", t):
                t = "Arthur P. McKinstry"
            elif t.isupper():
                t = R.titlecase(t)
            memo.append(("P", re.sub(r"^BORN in", "Born in", t)))
    sections.append({"title": "In Memoriam", "stream": memo})
    for i, n in enumerate(ROMAN):
        s = clean_page(z.read(f"lecture{n}.html").decode(), f"{n}_")
        title = s.select_one(".wst-center")
        head = R.clean(title.get_text(" "))
        assert f"Lecture {n}." in head, head
        title.decompose()
        w = R.Walker(book, s)
        items = [it for it in w.stream(s) if it[0] != "HR"]
        name = toc[i].split(". ", 1)[1]
        sections.append({"title": f"Lecture {n}: {name.rstrip('.')}", "stream": items})
    for s_ in sections:
        print(s_["title"], sum(len(it[1].split()) for it in s_["stream"] if it[0] == "P"),
              sum(1 for it in s_["stream"] if it[0] == "P" and it[1].startswith("Footnote:")))
    # witness: every reference in the four lecture pages is a footnote here
    nrefs = sum(len(BeautifulSoup(z.read(f"lecture{n}.html").decode(), "html.parser").select("ol.references li"))
                for n in ROMAN)
    nfoot = sum(1 for s_ in sections for it in s_["stream"] if it[0] == "P" and it[1].startswith("Footnote:"))
    assert nrefs == nfoot, (nrefs, nfoot)
    left = [it for s_ in sections for it in s_["stream"] if it[0] not in ("P", "BLOCK")]
    assert not left, left[:3]
    R.text_fixes(sections, TEXT_FIXES)
    c = R.respell(sections, SPELLING)
    print("respelled", c)
    rows, _ = R.compose(book, sections, plates=[])


if __name__ == "__main__":
    main()
