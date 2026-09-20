"""A. N. Whitehead, An Introduction to Mathematics (1911): a RESTORED EDITION.

    python3 introduction-to-mathematics/prep.py

Gutenberg #41568 exists ONLY as the LaTeX a Distributed Proofreaders
volunteer typeset it in (no HTML), so this prep reads the TeX through
tex_restore.py: the mathematics is already mathematics, and the
transcriber's editorial macros say exactly what was changed. House rule
(see tex_restore): misprints stay corrected, regularisations are
reversed to the print, added stops after displayed formulas are kept.

Structure: seventeen chapters, the Notes and the Bibliography, checked
against the book's own Contents (\\ToCLine). The Index is omitted. The 35
figures are vector PDFs in the source, rendered here to PNG.
"""
import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
import tex_restore as T  # noqa: E402

SRC = HERE / "_src" / "t" / "41568-t"
TEX = SRC / "41568-t.tex"
ZIP = HERE / "_src" / "whitehead.zip"


def build_zip():
    """The TeX and every figure, rendered, in one archive for restore_lib."""
    if ZIP.exists() and ZIP.stat().st_mtime > TEX.stat().st_mtime:
        return
    with zipfile.ZipFile(ZIP, "w") as z:
        z.write(TEX, "41568-t.tex")
        for pdf in sorted((SRC / "images").glob("*.pdf")):
            out = HERE / "_src" / "png" / pdf.stem
            out.parent.mkdir(exist_ok=True)
            subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", str(pdf), str(out)], check=True)
            z.write(str(out) + ".png", f"images/{pdf.stem}.png")


def main():
    build_zip()
    book = R.Book(HERE, "whitehead.zip", html_name="41568-t.tex", long_side=1600)
    src = TEX.read_text()
    toc = re.findall(r"\\ToCLine\{([IVXL]*)\}\{([^}]*)\}\{\d+\}", src)
    doc0 = src.index("\\begin{document}")
    body = src[src.index("\\MainMatter", doc0):src.index("\\printindex", doc0)]
    doc = T.Doc(body)
    sections = doc.convert(body)
    for s in sections:
        s["title"] = s["title"].replace("*", "")      # headings are plain
        if s.get("subtitle"):                          # "Note on the Study of Mathematics"
            s["stream"].insert(0, ("P", s["subtitle"]))
    ours = [s["title"] for s in sections]
    theirs = [f"Chapter {n}: {t}" if n else t for n, t in toc if t != "Index"]
    assert ours == theirs, list(zip(ours, theirs))
    left = doc.leftovers(sections)
    print("unconverted macros:", left)
    n = doc.resolve_pagerefs(sections)
    print("page refs", n, "footnotes", doc.footnotes)
    # the three footnotes that send the reader to the Notes, and the one
    # reference into its own chapter ("the expression on page 191 above")
    R.text_fixes(sections, [
        ("Note A, Notes.", "Note A, in the Notes.", "p. 250 is the Notes"),
        ("Note B, Notes.", "Note B, in the Notes.", "p. 250 is the Notes"),
        ("Note C, Notes.", "Note C, in the Notes.", "p. 250 is the Notes"),
        ("in the expression on \x06SAME\x06 above,", "in the expression above,", "p. 191 is this chapter"),
        # the transcription against the 1911 page images
        # (anintroductionto00whituoft), each read on the page
        (r"where \(0A = 1\)", r"where \(OA = 1\)", "a zero for the letter O; the page prints OA"),
        (r"this point \((A)\) are \(1\) and \(0\)", r"this point \((A)\) are \(-1\) and \(0\)",
         "the minus sign dropped; both scans print -1, and the text has just found x = -1"),
        (r"put \(v\) for the fraction \(\dfrac{PM}{OM}\)", r"put \(v\) for the fraction \(\dfrac{PM}{OP}\)",
         "page 183 prints PM/OP, which is the definition two sentences earlier"),
        # the printer's misprint, in both scans, corrected (house rule)
        ("Then the sign of this generalized angle", "Then the sine of this generalized angle", "printer's misprint for sine"),
    ])
    plates = [{"src": it[1] + ".png", "printed": (f"Fig. {it[1][3:]}." if it[1].startswith("fig") else "")}
              for s in sections for it in s["stream"] if it[0] == "PLATE"]
    for s in sections:
        s["stream"] = [("PLATE", it[1] + ".png", "") if it[0] == "PLATE" else it for it in s["stream"]]
    R.all_images_placed(book, plates)
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described")


if __name__ == "__main__":
    main()
