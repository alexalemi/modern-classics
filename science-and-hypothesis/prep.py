"""Henri Poincaré, Science and Hypothesis, in W. J. Greenstreet's
translation with Joseph Larmor's introduction (Walter Scott, 1905): a
RESTORED EDITION.

    python3 science-and-hypothesis/prep.py

Gutenberg #37157 exists only as the LaTeX a Distributed Proofreaders
volunteer typeset (no HTML); it is read through tex_restore.py, under the
same house rule as Whitehead: misprints stay corrected, regularisations
revert to the print, added stops after displayed formulas are kept.

Everything in the 1905 book is kept: the translator's note, Larmor's
introduction, Poincaré's preface, the four Parts and thirteen chapters.
Checked against the book's own Contents. No index is printed.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
import tex_restore as T  # noqa: E402

TEX = HERE / "_src" / "t" / "37157-t" / "37157-t.tex"


def main():
    src = TEX.read_text()
    d0 = src.index("\\begin{document}")
    body = src[src.index("\\OtherChapter{Translator", d0):src.index("\\PGLicense", d0)]
    body = body[:body.index("\\footnotesize THE END.")]          # the colophon
    body = body[:body.rindex("\\begin{center}")]
    # the heading's footnote: Chapter XII is taken from two of his prefaces
    body, n = re.subn(r"\\Chapter\{XII\.\\protect\\footnotemark\}\{([^}]*)\}\s*\\footnotetext",
                      r"\\Chapter{XII.}{\1}\n\n\\footnote", body)
    assert n == 1
    doc = T.Doc(body)
    # the book's own macros
    body = doc.replace_macro(body, "Reword", 2, lambda o, a, b: b)     # see the docstring
    body = doc.replace_macro(body, "Signature", 2, lambda o, a, b: f"\n\n{a}\n\n{b}\n\n")
    body = doc.replace_macro(body, "Pagerefs", 2, lambda o, a, b: f"\\Pageref{{{a}}}")
    body = doc.replace_macro(body, "Dict", 2, lambda o, a, b:
                             "\n\n\\begin{flushleft}" + re.sub(r"\s+", " ", a.replace("\\raggedright", "")).strip()
                             + " — " + re.sub(r"\s+", " ", b.replace("\\raggedright", "")).strip() + "\\end{flushleft}\n\n")
    body = body.replace("\\Transl", "---[\\textsc{Tr}.]").replace("\\ParSkip", "")
    sections = doc.convert(body)
    for s_ in sections:
        s_["title"] = re.sub(r"^Chapter ([IVXL]+)\.: (.*?)\.?$", r"Chapter \1: \2", s_["title"]).rstrip(".")
        if s_["title"].startswith("Chapter"):
            s_["chapter"] = True
        # the dictionary: consecutive "term — meaning" lines are one table
        st, out = s_["stream"], []
        for it in st:
            if it[0] == "BLOCK" and " — " in it[1] and out and out[-1][0] == "BLOCK" and " — " in out[-1][1]:
                out[-1] = ("BLOCK", out[-1][1] + "\n" + it[1])
            else:
                out.append(it)
        s_["stream"] = out
    # witness: the printed Contents (kept in the source inside \\iffalse)
    c0 = src.index("CONTENTS.", d0)
    block = src[c0:src.index("\\fi", c0)]
    toc = [re.sub(r"\.{3,}\s*[ivxl\d]+$", "", l).strip() for l in block.splitlines()
           if re.search(r"\.{3,}\s*[ivxl\d]+$", l)]
    key = lambda t: re.sub(r"[^a-z]", "", re.sub(r"^chapter [ivxl]+:", "", t.lower()))
    assert [key(s_["title"]) for s_ in sections] == [key(t) for t in toc], (
        [s_["title"] for s_ in sections], toc)
    parts = [s_["part_before"] for s_ in sections if s_.get("part_before")]
    assert parts == ["Part I: Number and Magnitude", "Part II: Space", "Part III: Force", "Part IV: Nature"], parts
    left = doc.leftovers(sections)
    assert not left, left
    n = doc.resolve_pagerefs(sections)
    print("page refs", n, "footnotes", doc.footnotes)
    for s_ in sections:
        for it in s_["stream"]:
            if it[0] in ("P", "BLOCK") and ("\x06SAME\x06" in it[1] or re.search(r"\bp\. ?Chapter|pp\. ?Chapter", it[1])):
                print("REF:", it[1][:300])
    # SCAN VOTE, against two 1905 copies (scienceandhypoth00poinuoft,
    # sciencehypothesi00poin): the transcription silently modernised
    # "cathodic rays" twice (the third, "the cathode rays, the X-rays", is
    # printed so), and marked the one "negligeable" a typo; it is the
    # period spelling, and both copies print it.
    R.text_fixes(sections, [
        ("whose dilatation is negligible, and", "whose dilatation is negligeable, and", "both scans"),
        ("in the same way for cathode rays;", "in the same way for cathodic rays;", "both scans"),
        ("Now, these cathode rays are", "Now, these cathodic rays are", "both scans"),
    ])
    zp = HERE / "_src" / "poincare.zip"
    if not zp.exists():
        import zipfile
        with zipfile.ZipFile(zp, "w") as z:
            z.write(TEX, "37157-t.tex")
    book = R.Book(HERE, "poincare.zip", html_name="37157-t.tex")
    rows, described = R.compose(book, sections, plates=[])
    print(f"{len(sections)} sections")


if __name__ == "__main__":
    main()
