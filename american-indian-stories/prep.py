"""Zitkala-Ša, American Indian Stories (1921): a RESTORED EDITION.

    python3 american-indian-stories/prep.py

Gutenberg #10376. The book collects the three autobiographical essays of
the Atlantic Monthly (1900), "Why I Am a Pagan" (1902, here retitled The
Great Spirit), the stories from Harper's and Everybody's, two stories not
printed before, and her 1921 essay America's Indian Problem.

TWO 1921 COPIES WERE COMPARED WITH GUTENBERG WORD BY WORD, and they do not
agree with each other. Archive.org's Brigham Young copy
(`americanindianst1921zitk`) prints two sentences after the missionary's
candies that the Boston Public Library copy (`bp_666562`) and Gutenberg
both lack, and ends The Great Spirit on the 1902 essay's last line, "If
this is Paganism, then at present, at least, I am a Pagan.", where the
other two end on the paragraph about the robe of the Great Spirit. So
there are two states of the 1921 printing. Gutenberg follows one of them
faithfully, two witnesses agree on it, and this edition follows it too;
the introduction says so rather than silently choosing. Nothing here
asserts which state came first.

WHERE BOTH COPIES AGREE AGAINST GUTENBERG, the question is whose the
difference is. The printer's plain misprints ("langauge", "warrier",
"magestically", "gilt" for guilt) were corrected by Gutenberg and stay
corrected: those are errors, not the author's words. Two period spellings
Gutenberg modernised go back to print (SOURCE_FIXES), and one stray "I"
where the page has an exclamation mark is repaired.

WHAT GUTENBERG LEFT OUT, restored: the title-page epigraph, and the
author's Acknowledgments page naming the magazines these pieces first
appeared in -- typed from the scan and checked letter for letter against
BOTH copies' OCR, two readings that share nothing with this file.
WHAT THIS EDITION LEAVES OUT, deliberately: the publisher's advertisement
bound in at the end (a letter from Helen Keller praising Old Indian
Legends), asserted to be all that follows the last separator.

STRUCTURE. Ten pieces, each a section. The three Atlantic essays and The
Soft-Hearted Sioux are divided by Roman numerals, most with a title; those
become subheadings ("II. The Legends"), numeral-only where the book has no
title. The report quoted in America's Indian Problem has its own all-caps
headings, title-cased. The one footnote is set as "Footnote: ..." after
its paragraph, as in mill/.

MODERN_CHAPTERS/ IS COMPOSED (there are no plates, so it is a copy of
chapters/), and the raw-HTML word count is the witness that verify's ratio
cannot be.
"""
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
SRC = HERE / "_src"
BOOK = "10376"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
WITNESSES = {"americanindianst1921zitk": "ais-djvu.txt",
             "bp_666562": "bp-djvu.txt"}
SMALL = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "for", "by",
         "with", "but", "or", "as", "from", "into", "upon"}

# The printed Contents, in both copies.
PRINTED_CONTENTS = [
    "Impressions of an Indian Childhood", "The School Days of an Indian Girl",
    "An Indian Teacher Among Indians", "The Great Spirit",
    "The Soft-Hearted Sioux", "The Trial Path", "A Warrior's Daughter",
    "A Dream of Her Grandfather", "The Widespread Enigma of Blue-Star Woman",
    "America's Indian Problem",
]
# The book's own heading differs from its Contents line; the heading is
# what stands over the story, so the heading is used.
HEADING_DIFFERS = {
    "The Widespread Enigma of Blue-Star Woman":
        "The Widespread Enigma Concerning Blue-Star Woman",
}

# Gutenberg -> as printed; both 1921 copies agree on the printed reading.
SOURCE_FIXES = [
    ("gaily festooned", "gayly festooned"),
    ("would entrust", "would intrust"),
    ("to the floor I She spared", "to the floor! She spared"),
]

ACKNOWLEDGMENTS = [
    "To The Atlantic Monthly for permission to reprint from its 1900 issue "
    "\"Impressions of an Indian Childhood,\" \"The School Days of an Indian "
    "Girl,\" \"An Indian Teacher Among Indians,\" and from its 1902 issue, "
    "\"Why I Am a Pagan.\"",
    "To Harper's Magazine for permission to reprint from its 1901 issues, "
    "\"The Trial Path,\" and \"The Soft-Hearted Sioux.\"",
    "To Everybody's Magazine for permission to reprint from its 1902 issue, "
    "\"A Warrior's Daughter.\"",
]

ROMAN = re.compile(r"([IVX]+)\.?")


def fetch():
    SRC.mkdir(exist_ok=True)
    p = SRC / f"pg{BOOK}-h.zip"
    if not p.exists():
        url = f"https://www.gutenberg.org/cache/epub/{BOOK}/pg{BOOK}-h.zip"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=300) as r:
            p.write_bytes(r.read())
    ocr = {}
    for ident, name in WITNESSES.items():
        f = SRC / name
        if not f.exists():
            url = f"https://archive.org/download/{ident}/{ident}_djvu.txt"
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=300) as r:
                f.write_bytes(r.read())
        ocr[ident] = f.read_text(errors="replace")
    return zipfile.ZipFile(p), ocr


def clean(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def titlecase(s):
    words = clean(s).rstrip(".").lower().split()
    return " ".join(w if i and w in SMALL else
                    "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
                    for i, w in enumerate(words))


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]+", " ", s.lower()).strip()


def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name == "br":
                out.append(" ")
            elif c.name in ("i", "em"):
                out.append(f"*{inline(c)}*")
            else:
                out.append(inline(c))
    return "".join(out)


def emph_safe(text):
    """Keep only the asterisks assemble.EMPH renders (see aesop/prep.py)."""
    sys.path.insert(0, str(ROOT))
    import assemble
    keep = []

    def hold(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"
    held = assemble.EMPH.sub(hold, text).replace("*", "")
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], held)


def check_acknowledgments(ocr):
    typed = norm(" ".join(ACKNOWLEDGMENTS)).replace(" ", "")
    for ident, text in ocr.items():
        m = re.search(r"ACKNO\s*WLED\s*GMENTS(.*?)Copyright", text, re.S)
        assert m, f"{ident}: no Acknowledgments page"
        got = norm(m.group(1)).replace(" ", "")
        assert got == typed, f"{ident} disagrees: {got!r}"


def main():
    z, ocr = fetch()
    check_acknowledgments(ocr)
    html = z.read([n for n in z.namelist() if n.endswith(".html")][0]).decode(
        "utf-8", "replace")
    for bad, good in SOURCE_FIXES:
        assert html.count(bad) == 1, (bad, html.count(bad))
        html = html.replace(bad, good)
    s = html.index("</header>", html.index("*** START")) + len("</header>")
    e = html.index('<footer class="pg-boilerplate')
    soup = BeautifulSoup(html[s:e], "html.parser")

    phase, contents, stories, pending = "front", [], [], None
    epigraph, tail, dividers = None, [], 0
    tags = []
    for el in soup.children:
        if isinstance(el, Tag):
            tags.append(el)
        elif clean(str(el)):
            raise SystemExit(f"loose text: {clean(str(el))[:60]!r}")
    for k, el in enumerate(tags):
        t = clean(el.get_text())
        if phase == "tail":
            tail.append(t)
            continue
        if phase == "front":
            if el.name == "p" and "There is no great" in t:
                epigraph = t
            if el.name == "h2" and t == "CONTENTS":
                phase = "contents"
            continue
        if phase == "contents":
            if el.name == "p":
                contents.append(t)
                continue
            assert contents == PRINTED_CONTENTS, contents
            wanted = {norm(HEADING_DIFFERS.get(c, c)): HEADING_DIFFERS.get(c, c)
                      for c in contents}
            phase = "body"
        # ---- body
        if el.name in ("h2", "h4") and norm(t) in wanted:
            stories.append({"title": wanted[norm(t)], "stream": []})
            pending = None
            continue
        stream = stories[-1]["stream"]
        if el.name in ("h2", "h5") and ROMAN.fullmatch(t):
            pending = ROMAN.fullmatch(t).group(1)
            stream.append(["SUB", pending])
            continue
        if el.name == "h5" and t.startswith('"'):
            # a letter's signature, set as a heading by the transcription
            stream.append(["P", '"' + titlecase(t[1:]) + "."])
            pending = None
            continue
        if el.name == "h5":
            assert pending and stream[-1] == ["SUB", pending], t
            stream[-1][1] = f"{pending}. {titlecase(t)}"
            pending = None
            continue
        if el.name == "h4":
            stream.append(["SUB", titlecase(t)])
            pending = None
            continue
        if el.name == "p":
            pending = None
            if re.fullmatch(r"[*\s]+", t):
                # A row of asterisks. The book sets one between two pieces and
                # one before the advertisement; anywhere else it would be a
                # break in the text and is kept.
                nxt = clean(tags[k + 1].get_text()) if k + 1 < len(tags) else ""
                if nxt == "This Book should be in every home":
                    phase = "tail"         # the publisher's advertisement
                elif norm(nxt) in wanted:
                    dividers += 1
                else:
                    stream.append(["P", "* * *"])
                continue
            p = emph_safe(clean(inline(el)))
            m = re.fullmatch(r"\[Footnote 1: (.*)\]", p)
            if m:
                stream.append(["P", f"Footnote: {m.group(1)}"])
                continue
            if "[1]" in p:
                assert p.count("[1]") == 1
                p = p.replace("[1]", "")
            assert "[" not in p, p
            stream.append(["P", p])
            continue
        raise SystemExit(f"unhandled <{el.name}> {t[:60]!r}")
    assert len(stories) == 10, [x["title"] for x in stories]
    assert phase == "tail", "the advertisement was never reached"
    assert epigraph, "no epigraph"
    assert "HELEN KELLER" in " ".join(tail) and len(" ".join(tail).split()) < 260, \
        "something other than the advertisement follows the last separator"
    body = " ".join(v for x in stories for k, v in x["stream"] if k == "P")
    assert "in a fleeting quiet" in body and "generous distribution" not in body, \
        "the 1921 state Gutenberg follows has changed"
    assert sum(1 for x in stories for k, v in x["stream"]
               if v.startswith("Footnote:")) == 1

    # ---- witness: the raw HTML's word count, tags stripped
    raw = html[html.index('<h2 id="id00018"'):html.index('id="id00598"')]
    raw_words = len(re.sub(r"<[^>]+>", " ", raw).split())
    got = sum(len(x["title"].split()) +
              sum(len(v.split()) for k, v in x["stream"]) for x in stories)
    assert abs(raw_words - got) <= 0.005 * raw_words, (raw_words, got)

    # ---- compose
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    sections = [("Epigraph", ["\t" + epigraph]),
                ("Acknowledgments", ACKNOWLEDGMENTS)]
    sections += [(x["title"], [v for _, v in x["stream"]]) for x in stories]
    manifest = []
    for idx, (title, paras) in enumerate(sections):
        text = "\n\n".join([title] + paras).rstrip() + "\n"
        for d in ("chapters", "modern_chapters"):
            (HERE / d / f"{idx:03d}.txt").write_text(text)
        manifest.append({"file": f"{idx:03d}.txt", "title": title,
                         "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    subs = sum(1 for x in stories for k, _ in x["stream"] if k == "SUB")
    print(f"{len(stories)} pieces, {subs} subheadings, {got:,} words "
          f"(raw HTML {raw_words:,}); epigraph and acknowledgments restored")


if __name__ == "__main__":
    main()
