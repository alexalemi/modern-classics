"""Bertrand Russell, The Problems of Philosophy (1912): a RESTORED EDITION.

    python3 problems-of-philosophy/prep.py

Gutenberg #5827, the Home University Library text of 1912. Screened as
clear (arch 0.00, calq 35.3, 27-word sentences): Russell wrote it for the
general reader and it needs an edition, not a retelling.

Structure is the book's own and is checked against its printed Contents:
the Preface, fifteen chapters and the Bibliographical Note. The Contents
table itself, the title page and the byline are dropped.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

CHAPTERS = 15

# THE TEXT IS THE FIRST EDITION OF 1912, AND GUTENBERG'S IS NOT. A word diff
# against three 1912 printings on Archive.org -- two copies of the British
# Home University Library edition (problemsofphilo00russuoft,
# problemsofphilos1912russ) and the Holt American printing
# (problemsphiloholt00russuoft) -- found Gutenberg's text matching none of
# them: Oxford house spelling (-ize, judgement, connexion) where all three
# print -ise, judgment, connection, and a handful of later wordings. Each
# fix below is a reading all three printings share, checked in their OCR
# (scan_diff.py --vote), except the Emperor, where the two British copies
# say Russia and Holt says China; the edition follows the British first
# edition and the introduction says what Holt prints. The printed Index,
# which Gutenberg omits, confirms it: "Russia, Emperor of, 70, 116".
TEXT_FIXES = [
    ("Emperor of China", "Emperor of Russia", "British first edition; Holt prints China", 2),
    ("premisses do not tell us", "premisses did not tell us", "all three 1912 printings"),
    ("it is the cause of sensations. In the", "it is the cause of sensation. In the", "all three"),
    ("that knowledge of physical objects, as opposed to sense-data, is only obtained by an inference, and that they are not things",
     "that physical objects, as opposed to sense-data, are only obtained by an inference, and are not things",
     "all three 1912 printings; Gutenberg carries a later rewording"),
    ("Prolegomena to any Future Metaphysic", "Prolegomena to every Future Metaphysic", "all three"),
    ("beleagured", "beleaguered", "Gutenberg typo; all three print beleaguered"),
    ("Thus utility does not", "This utility does not", "all three"),
    ("unchanged. This colour is not", "unchanged. Thus colour is not", "all three"),
    # words the later state dropped, found once scan_diff's vote learned to
    # see a word the print has and the edition lacks (2026-09-20)
    ("writings of G. E. Moore and J. M. Keynes", "writings of Mr. G. E. Moore and Mr. J. M. Keynes", "1912 printings"),
    ("by considering which among them is most possible", "by considering which among them it is most possible", "1912 printings"),
    ("The first of these views, advocated by Spinoza", "The first of these views, which was advocated by Spinoza", "1912 printings"),
    ("in our own day by Bradley", "in our own day by Mr. Bradley", "1912 printings"),
    ("the second, advocated by Leibniz", "the second, which was advocated by Leibniz", "1912 printings"),
    ("the human mind, which was a part of philosophy, has now", "the human mind, which was, until very lately, a part of philosophy, has now", "1912 printings"),
]
# Word-level: all three printings use these forms throughout.
SPELLING = [("judgements", "judgments"), ("judgement", "judgment"),
            ("connexions", "connections"), ("connexion", "connection")] + [
    (w, w.replace("iz", "is")) for w in (
        "generalizations", "generalization", "realize", "realizing", "realizes",
        "realized", "realization", "recognized", "recognizes", "organization",
        "organizing", "harmonize", "systematize", "philosophize", "emphasized",
        "criticized")]


def main():
    book = R.Book(HERE, "pg5827-h.zip", drop={"cover.jpg": "Gutenberg cover"})
    h = book.html()
    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    toc = [R.clean(tr.get_text(" ")).strip(". ") for tr in soup.find("table").find_all("tr")]
    toc = [re.sub(r"^\.\s*", "", t) for t in toc if t]
    soup.find("table").decompose()
    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur = [], None
    for it in items:
        if it[0] == "H":
            t = it[2]
            m = re.fullmatch(r"CHAPTER ([IVXL]+)\. (.+)", t)
            if m:
                cur = {"title": f"Chapter {m.group(1)}: {R.titlecase(m.group(2))}", "stream": []}
            elif t in ("PREFACE", "BIBLIOGRAPHICAL NOTE"):
                cur = {"title": R.titlecase(t), "stream": []}
            else:
                cur = None                 # title page, byline, "Contents"
                continue
            sections.append(cur)
            continue
        if cur is not None:
            cur["stream"].append(it)
    key = lambda t: re.sub(r"[^a-z]+", " ", t.lower()).strip()
    ours, theirs = [key(s["title"]) for s in sections], [key(t) for t in toc]
    assert ours == theirs, [(a, b) for a, b in zip(ours, theirs) if a != b][:3] or (len(ours), len(theirs))
    assert sum(s["title"].startswith("Chapter") for s in sections) == CHAPTERS

    # witness: the raw HTML from the Preface to the end
    raw = R.raw_words(body[body.index("PREFACE", body.index("</table>")):])
    got = R.words([it for s in sections for it in s["stream"]]) + sum(len(s["title"].split()) for s in sections) \
        - sum(1 for s in sections if s["title"].startswith("Chapter"))   # "Chapter I:" vs "CHAPTER I."
    assert abs(raw - got) <= 0.005 * raw, (raw, got)
    for s in sections:
        s["stream"] = [it for it in s["stream"] if it[0] != "HR"]
    R.text_fixes(sections, TEXT_FIXES)
    counts = R.respell(sections, SPELLING)
    assert counts["judgement"] + counts["judgements"] == 64 and \
        counts["connexion"] + counts["connexions"] == 22, counts
    assert all(counts[w] for w, _ in SPELLING), [w for w, _ in SPELLING if not counts[w]]
    R.compose(book, sections, plates=[])
    print(f"{len(sections)} sections, {got:,} words (raw {raw:,})")


if __name__ == "__main__":
    main()
