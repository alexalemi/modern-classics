"""Albert Einstein, Relativity: The Special and General Theory, in Robert
W. Lawson's authorised translation of 1920: a RESTORED EDITION.

    python3 relativity/prep.py

Gutenberg #30155. Screened as clear (arch 0.16, calq 56.6): the calque
score is the physics, and Einstein's terms are load-bearing, so the book
needs an edition, not a retelling.

THE 1920 TEXT. Gutenberg's transcription came by way of the Einstein
Reference Archive and ends with an Appendix IV on the structure of space
that cites Friedmann and Hubble and "already in the 'twenties": it was
written for a much later edition and is not part of the 1920 book, so it
is dropped. Everything else is checked against two 1920 printings.

THE MATHEMATICS IS TYPESET. Gutenberg sets every formula as a picture
(rendered from TeX, but no source survives) and splits the sentence
around each one, even where the 1920 page has the formula inline. Each
picture is transcribed below as LaTeX, and INLINE marks the ones the
1920 Holt printing (cu31924011804774) sets in the run of the sentence;
those are joined back into it. The centred text equations Gutenberg typed
are converted mechanically. Five pictures are figures and one is the
table of the 1919 eclipse results, set here as a table.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

SQ = r"\sqrt{1 - \frac{v^2}{c^2}}"
TEX = {
    "003": r"x' = \frac{x - vt}{" + SQ + "},",
    "004": r"t' = \frac{t - \frac{v}{c^2} \cdot x}{" + SQ + "}.",
    "005": [r"x' = \frac{(c - v)t}{" + SQ + "},", r"t' = \frac{\left(1 - \frac{v}{c}\right)t}{" + SQ + "},"],
    "006": [r"x_{\text{(beginning of rod)}} = 0 \cdot " + SQ + ",", r"x_{\text{(end of rod)}} = 1 \cdot " + SQ + ","],
    "007": SQ + ".",
    "008": r"\sqrt{1 - v^2/c^2}",
    "009": r"\sqrt{1 - v^2/c^2} = 0,",
    "010": r"\sqrt{1 - v^2/c^2};",
    "011": r"t = \frac{1}{" + SQ + "}.",
    "012": r"\frac{1}{" + SQ + "}",
    "013": r"W = \frac{v + w}{1 + \frac{vw}{c^2}} \qquad (B)",
    "015": r"W = w + v\left(1 - \frac{1}{n^2}\right),",
    "016": r"n = \frac{c}{w}",
    "017": r"\frac{vw}{c^2}",
    "018": r"W = (w + v)\left(1 - \frac{vw}{c^2}\right),",
    "019": r"w + v\left(1 - \frac{1}{n^2}\right),",
    "020": r"m\frac{v^2}{2},",
    "021": r"\frac{mc^2}{" + SQ + "}.",
    "022": r"mc^2 + m\frac{v^2}{2} + \frac{3}{8} m \frac{v^4}{c^2} + \dots.",
    "023": r"\frac{v^2}{c^2}",
    "024": r"\frac{E_0}{" + SQ + "}.",
    "025": r"\frac{\left(m + \frac{E_0}{c^2}\right)c^2}{" + SQ + "}.",
    "026": r"\left(m + \frac{E_0}{c^2}\right)",
    "027": r"\frac{E_0}{c^2};",
    "028": r"\frac{mc^2 + E_0}{" + SQ + "},",
    "029": SQ + ".",
    "030": r"t' = \frac{t - \frac{v}{c^2}x}{" + SQ + "}.",
    "031": r"\sqrt{-1} \cdot ct",
    "032": r"(\text{acceleration}) = \frac{(\text{gravitational mass})}{(\text{inertial mass})} \times (\text{intensity of the gravitational field}).",
    "034": r"\sqrt{-1}\, ct,",
    "035": r"\sqrt{-1}\, ct",
    "036": r"\pi = \frac{\sin\left(\frac{r}{R}\right)}{\left(\frac{r}{R}\right)},",
    "037": r"R^2 = \frac{2}{\kappa\rho}.",
    "038": r"a = \frac{\lambda + \mu}{2},",
    "039": r"b = \frac{\lambda - \mu}{2},",
    "040": [r"x' = ax - bct, \qquad (5)", r"ct' = act - bx."],
    "041": r"x = \frac{bc}{a}t.",
    "042": r"v = \frac{bc}{a}. \qquad (6)",
    "043": r"\Delta x = \frac{1}{a}. \qquad (7)",
    "044": r"x' = a\left(1 - \frac{v^2}{c^2}\right)x.",
    "045": r"\Delta x' = a\left(1 - \frac{v^2}{c^2}\right). \qquad (7a)",
    "046": r"a^2 = \frac{1}{1 - \frac{v^2}{c^2}}. \qquad (7b)",
    "047": [r"x' = \frac{x - vt}{" + SQ + r"}, \qquad (8)", r"t' = \frac{t - \frac{v}{c^2}x}{" + SQ + "}."],
    "048": [r"y' = y, \qquad (9)", r"z' = z."],
    "049": r"r = \sqrt{x^2 + y^2 + z^2} = ct,",
    "050": [r"x_1 = x,", r"x_2 = y,", r"x_3 = z,", r"x_4 = \sqrt{-1} \cdot ct,"],
    "051": r"+\frac{24\pi^3 a^2}{T^2 c^2 (1 - e^2)}.",
    "053": r"\alpha = \frac{1.7 \text{ seconds of arc}}{\Delta}.",
    "055": r"\nu = \nu_0 " + SQ + ",",
    "056": r"\nu = \nu_0 \left(1 - \frac{1}{2}\frac{v^2}{c^2}\right).",
    "057": r"\nu = \nu_0 \left(1 - \frac{1}{c^2}\frac{\omega^2 r^2}{2}\right).",
    "058": r"\phi = -\frac{\omega^2 r^2}{2}.",
    "059": r"\nu = \nu_0 \left(1 + \frac{\phi}{c^2}\right).",
    "060": r"\frac{\nu_0 - \nu}{\nu_0} = \frac{K}{c^2}\frac{M}{r}.",
}
# set in the run of the sentence on the 1920 page, each checked in the
# Holt scan: "is √1 − v²/c² of a metre", "not one second, but 1/√… seconds"
INLINE = {"008", "009", "010", "012", "015", "016", "017", "018", "019",
          "023", "026", "027", "031", "034", "035"}
FIGURES = {"001": "Fig. 1.", "002": "Fig. 2.", "014": "Fig. 3.", "033": "Fig. 4.", "052": "Fig. 5."}
# image054, the 1919 eclipse: Schwarzschild's star positions, read off the
# picture and checked against both scans
ECLIPSE = [
    ["Number of the Star.", "First Co-ordinate. Observed.", "First Co-ordinate. Calculated.",
     "Second Co-ordinate. Observed.", "Second Co-ordinate. Calculated."],
    ["11", "−0.19", "−0.22", "+0.16", "+0.02"],
    ["5", "+0.29", "+0.31", "−0.46", "−0.43"],
    ["4", "+0.11", "+0.10", "+0.83", "+0.74"],
    ["3", "+0.20", "+0.12", "+1.00", "+0.87"],
    ["6", "+0.10", "+0.04", "+0.57", "+0.40"],
    ["10", "−0.08", "+0.09", "+0.35", "+0.32"],
    ["2", "+0.95", "+0.85", "−0.27", "−0.09"],
]
# SCAN VOTE: the edition against two 1920 printings, Holt
# (cu31924011804774) and Methuen (relativitythespe00einsuoft), keeping the
# readings both agree on. Gutenberg's text came from an online archive
# that had (a) its own OCR errors and (b) EDITORIAL INSERTIONS: glosses in
# square brackets, a note that E = mc² "has been thoroughly proved time and
# again since this time", and a footnote folded into its sentence. None
# of them is Einstein's or Lawson's; each is removed here.
TEXT_FIXES = [
    ("unable to see the forest for the trees", "unable to see the forest for trees", "both scans"),
    ("By reason of our past experience", "By reason of your past experience", "both scans"),
    ("propagation ot a ray", "propagation of a ray", "both scans"),
    ("*in vacuo* [in vacuum] must", "*in vacuo* must", "editorial gloss"),
    ("will with a vantage view the train", "will with advantage use the train", "both scans"),
    ("with respect to be embankment", "with respect to the embankment", "both scans"),
    ("Of cause this is not surprising", "Of course this is not surprising", "both scans"),
    ("for these became meaningless", "for these become meaningless", "both scans"),
    ("our considerations on the Galileian transformation", "our considerations on the Galilei transformation", "both scans"),
    ("developed trom electrodynamics", "developed from electrodynamics", "both scans"),
    ("at the present time (1920; see[Note], p. 48), owing", "at the present time, owing", "editorial insertion"),
    ("importance of the Galileian transformation", "importance of the Galilei transformation", "both scans"),
    ("were attributed the more complicated laws", "were assigned the more complicated laws", "both scans"),
    ("Let as once more analyse", "Let us once more analyse", "both scans"),
    ("on the following Iines.", "on the following lines.", "both scans"),
    ("produces in its surrounding a gravitational field", "produces in its surroundings a gravitational field", "both scans"),
    ("on a body dimishes according", "on a body diminishes according", "both scans"),
    ("in a room of a home on our earth. If he releases a body", "in a room of a house on our earth. If he release a body", "both scans"),
    ("space-time contintium—accordance with", "space-time continuum—in accordance with", "both scans"),
    ("In view of the resuIts of these", "In view of the results of these", "both scans"),
    ("We start off on a consideration of a Galileian domain", "We start off from a consideration of a Galileian domain", "both scans"),
    ("even in the case where the prevailing", "even in the case when the prevailing", "both scans"),
    ("devised solely for this purponse", "devised solely for this purpose", "both scans"),
    ("Part from the difficulty discussed", "Apart from the difficulty discussed", "both scans"),
    ("of approrimately the same kind", "of approximately the same kind", "both scans"),
    ("can be obtained from equations (5), if", "can be obtained from equation (5), if", "both scans"),
    ("*x′, y′, x′, t′*", "*x′, y′, z′, t′*", "both scans", 2),
    ("*x, y, x, t*", "*x, y, z, t*", "both scans", 2),
    ("(11a) [see the end of Appendix II] is transformed", "(11a) is transformed", "editorial insertion"),
    ("the above expression given the amount", "the above expression gives the amount", "both scans"),
    ("indebted to the [British] Royal Society", "indebted to the Royal Society", "editorial insertion"),
    ("Undaunted by the [first world] war", "Undaunted by the war", "editorial insertion"),
    ("a certain comprehensibility as compared", "a certain comprehensibleness as compared", "both scans"),
    ("as observed front the earth", "as observed from the earth", "both scans"),
    ("A. EINSTEIN", "A. Einstein", "the Preface's signature; an all-caps line renders as a heading"),
    ("nor the radius *r* are known", "nor the radius *r* is known", "both scans"),
    ("almost beyond doubt, while other investigators", "almost beyond doubt, other investigators", "both scans"),
]

GREEK = {"λ": r"\lambda", "σ": r"\sigma", "ω": r"\omega"}


def centre_tex(inner):
    """Gutenberg's typed centred equations -> LaTeX."""
    t = re.sub(r"\s+", " ", inner).strip()
    t = re.sub(r"<sup>\s*(.*?)\s*</sup>", r"^{\1}", t)
    t = re.sub(r"<sub>\s*(.*?)\s*</sub>", r"_{\1}", t)
    t = re.sub(r"</?i>", "", t)
    t = t.replace("′", "'").replace("–", "-")
    for g, c in GREEK.items():
        t = t.replace(g, c + " ")
    t = re.sub(r"\s*(?:\. ){3,}\.?\s*", r" \\qquad ", t)          # dotted leaders
    t = re.sub(r"\s*\((\d+[a-z]?|10a|11a)\)(\.?)$", r" \\qquad (\1)\2", t) if "\\qquad" not in t else t
    t = re.sub(r"(\\qquad\s*)+", r"\\qquad ", t)
    return t.strip()


def main():
    book = R.Book(HERE, "pg30155-h.zip", drop={"cover.jpg": "Gutenberg cover", **{
        f"image{n}.jpg": "formula, typeset" for n in TEX}, "image054.jpg": "table, set as text"})
    h = book.html()
    # the later Appendix IV, to the end of the book
    a = h.index('<a id="chap37"></a>APPENDIX IV') if '<a id="chap37"></a>APPENDIX IV' in h else None
    if a is None:
        a = h.index("APPENDIX IV", h.index("APPENDIX III", h.index("<h3>Contents</h3>") + 3000))
        a = h.rindex("<div", 0, a)
    e = h.index('<footer class="pg-boilerplate') if 'pg-boilerplate' in h else h.index("*** END")
    body4 = h[a:e]
    assert "Hubble" in body4 and "Friedman" in body4
    h = h[:a] + h[e:]

    # footnotes: Gutenberg already sets each after the paragraph citing it
    h, n1 = re.subn(r'<a href="#linknote-\d+" id="linknoteref-\d+" class="pginternal">\[\d+\]</a>', "", h)
    h, n2 = re.subn(r'<p>\s*<a id="linknote-\d+">\s*<!--\s*Note\s*-->\s*</a>\s*</p>', "", h)
    h, n3 = re.subn(r'<a href="#linknoteref-\d+" class="pginternal">\s*\[\d+\]</a>\s*<br>', "⟪FN⟫", h)
    print("footnotes", n1, n2, n3)
    assert n1 == n2 == n3, (n1, n2, n3)

    # formula pictures -> placeholders; the two reused ones by occurrence
    def pic(m):
        n = m.group(1)
        if n in FIGURES:
            return m.group(0)
        return f'<p class="formula">⟪F{n}⟫</p>'
    h, nf = re.subn(r'<div class="fig"[^>]*>\s*<img alt="image(\d+)"[^>]*>(?:\s*<br\s*/?>)*\s*</div>', pic, h)
    # centred text equations
    centres = []
    def cen(m):
        centres.append(centre_tex(m.group(1)))
        return f'<p class="formula">⟪C{len(centres)-1}⟫</p>'
    h, nc = re.subn(r'<p class="center">(.*?)</p>', cen, h, flags=re.S)
    print("pictures", nf, "centred", nc)

    body = book.body_html(h)
    soup = BeautifulSoup(body, "html.parser")
    soup.find("h3", string="Contents").find_next("table").decompose()
    w = R.Walker(book, soup)
    items = w.stream(soup)

    sections, cur, part = [], None, None
    for it in items:
        if it[0] == "H":
            t = it[2]
            if it[1] == 3 and t == "PREFACE":
                cur = {"title": "Preface", "stream": []}
            elif it[1] == 3 and t.startswith("PART "):
                part = R.titlecase(t.replace("PART ", "Part "), keep={"I", "II", "III"})
                cur = None
                continue
            elif it[1] == 3 and t == "APPENDICES":
                part, cur = "Appendices", None
                continue
            elif it[1] == 3 and re.match(r"[IVXL]+\. ", t):
                num, rest = t.split(". ", 1)
                cur = {"title": f"Section {num}: {R.titlecase(rest)}", "stream": [], "chapter": True}
            elif it[1] == 3 and t.startswith("APPENDIX "):
                m = re.match(r"APPENDIX ([IVX]+) (.+)", t)
                cur = {"title": f"Appendix {m.group(1)}: {R.titlecase(m.group(2))}", "stream": [], "chapter": True}
            elif it[1] == 4 and cur is not None:
                cur["stream"].append(("P", t))
                continue
            else:
                cur = None
                continue
            if part:
                cur["part_before"], part = part, None
            sections.append(cur)
            continue
        if cur is not None:
            cur["stream"].append(it)
    print(len(sections), [s["title"][:30] for s in sections[-4:]])

    # formulas back in, inline ones joined to their sentence
    seen = {}
    for s in sections:
        out = []
        st = s["stream"]
        k = 0
        while k < len(st):
            it = st[k]
            m = re.fullmatch(r"⟪(F|C)(\d+)⟫", it[1]) if it[0] == "P" else None
            if not m:
                out.append(it); k += 1; continue
            if m.group(1) == "C":
                out.append(("P", r"\[" + centres[int(m.group(2))] + r"\]")); k += 1; continue
            n = m.group(2)
            seen[n] = seen.get(n, 0) + 1
            if n == "054":
                out.append(("BLOCK", "\n".join("\t" + " | ".join(r) for r in ECLIPSE))); k += 1; continue
            tex = TEX[n]
            if n == "027" and seen[n] == 2:
                tex = tex.rstrip(";")            # the second use is not followed by ";"
            if n in INLINE:
                prev = out.pop() if out and out[-1][0] == "P" else ("P", "")
                # punctuation that ends the formula belongs to the sentence
                tail = re.search(r"[,.;]$", tex)
                core = tex[:-1] if tail else tex
                text = (prev[1] + " " if prev[1] else "") + r"\(" + core + r"\)" + (tail.group(0) if tail else "")
                if k + 1 < len(st) and st[k + 1][0] == "P" and not st[k + 1][1].startswith("⟪"):
                    nxt = st[k + 1][1]
                    text += ("" if re.match(r"[,.;:)]", nxt) else " ") + nxt
                    k += 1
                out.append(("P", text)); k += 1
                continue
            for line in (tex if isinstance(tex, list) else [tex]):
                out.append(("P", r"\[" + line + r"\]"))
            k += 1
        s["stream"] = out
    # a footnote opens on its marker; its continuation paragraphs were
    # joined to it by the inline formulas above
    for s in sections:
        s["stream"] = [(it[0], it[1].replace("⟪FN⟫", "Footnote: ").replace("Footnote:  ", "Footnote: ")) + tuple(it[2:])
                       if it[0] == "P" else it for s_ in [s] for it in s_["stream"]]
    left = [it[1][:60] for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK") and "⟪" in it[1]]
    assert not left, left
    assert set(seen) == set(TEX) | {"054"}, sorted(set(TEX) - set(seen))

    # the editor's note on E = mc², and the embankment footnote folded
    # into its sentence (the 1920 page prints it as a footnote)
    for s_ in sections:
        st = s_["stream"]
        for k, it in enumerate(st):
            if it[0] == "P" and it[1].startswith("[Note] The equation E = mc²"):
                del st[k]
                break
    R.text_fixes(sections, TEXT_FIXES)
    c = R.respell(sections, [("molluscs", "mollusks"), ("mollusc", "mollusk")])   # both printings, throughout
    assert c == {"molluscs": 1, "mollusc": 7}, c
    n = 0
    for s_ in sections:
        st = s_["stream"]
        for k, it in enumerate(st):
            if it[0] == "P" and "the flashes (as judged from the embankment) of lightning" in it[1]:
                st[k] = ("P", it[1].replace("the flashes (as judged from the embankment) of lightning", "the flashes of lightning"))
                st.insert(k + 1, ("P", "Footnote: As judged from the embankment."))
                n += 1
                break
    assert n == 1
    assert not any("[Note]" in it[1] or "mc² has been" in it[1] for s_ in sections for it in s_["stream"] if it[0] == "P")

    plates = [{"src": it[1], "printed": FIGURES[re.search(r"(\d+)", it[1]).group(1)]}
              for s in sections for it in s["stream"] if it[0] == "PLATE"]
    assert len(plates) == 5, plates
    R.all_images_placed(book, plates)
    for s in sections:
        s["stream"] = [it for it in s["stream"] if it[0] != "HR"]
    rows, described = R.compose(book, sections, plates=plates)
    print(f"{len(sections)} sections, {len(rows)} plates, {described} described")


if __name__ == "__main__":
    main()
