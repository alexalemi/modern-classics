"""Build chapters/ + manifest.json for George Boole, An Investigation of the
Laws of Thought (1854), the LOGIC HALF: the Preface and Chapters I-XV.

    python3 books/laws-of-thought/prep.py

SOURCE: Gutenberg #15114, which exists ONLY as LaTeX (_src/15114-t.tex, not
kept in git). It is an early (2004) Distributed Proofreaders transcription,
not one of the later DP books with \\Typo/\\Chg macros, so tex_restore.py
does not fit it; this prep reads the TeX itself. The transcriber's notes are
TeX comments, harvested into NOTES below before the comments are stripped.

WHAT IS KEPT: the dedication and Preface (000.txt, carved by split_headings),
Chapters I-XV. Dropped: the Gutenberg wrapper, the title page, the Contents
(read only to assert the chapter list), the unheaded NOTE before Chapter I
(an erratum to Chapter XX's Prop. II, p. 261, and its urn problem, p. 270),
and Chapters XVI-XXII on probabilities.

MATHEMATICS stays LaTeX: inline \\(...\\), displayed \\[...\\] as its own
paragraph (the convention of every typeset book here; assemble.render_body
sends a TAB-INDENTED block to the table path instead). Inside a footnote a
display stays in the footnote's one paragraph.

EQUATION NUMBERS ARE COMPILED, NOT SIMULATED. Boole numbers equations within
each chapter and the transcription reproduces his numbering with
\\setcounter resets (one inside a footnote, one "restarts from 3 for no
apparent reason"), per-row eqnarray numbers, \\nonumber, and explicit
\\tag{I.}..\\tag{VI.}. Rather than re-implement LaTeX's counters, the source
is compiled once with pdflatex, every number written to the log with its
input line (eqtags(): cached in _src/eqtags.txt), and each environment's
numbers are taken from the lines it spans. The number of rows this prep
thinks are numbered must equal the number LaTeX printed, or the prep stops.
The number is set inside the display, after the formula, as
"\\qquad (n)" (tex_restore's \\Tag convention), so it travels with the
formula through translation and the math-identity check covers it.

TRANSCRIPTION ERRORS RESTORED (run with --report to list them):
  - the OCR read the digit 1 as the letter l inside formulas ("v(l-x)");
    Boole never uses l as a symbol in Chapters I-XV, so every bare l in a
    formula is a 1 (fix_l; 15 formulas);
  - a bare {..} group holding a sum is one of Boole's printed braces, which
    TeX (and pandoc) would silently drop, changing the equation (fix_braces;
    11 rows, all in Chapter IX);
  - three proofers' page markers ran an article into the one before;
  - the Greek: LGR typed through an OCR, corrected in FIXES against the
    received texts of Aristotle (Metaphysics 1005b, De Caelo 268a, EN).

ITALICS: _x_ for words and phrases; a span longer than ITALIC_MAX, or one
covering a whole paragraph (an enunciation beside its label), is roman.
"""
import bisect
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "_src" / "15114-t.tex"
TAGS = HERE / "_src" / "eqtags.txt"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV"]

# Chapter titles. FULL is Boole's heading in title case; where it runs past
# about twelve words the heading uses SHORT, Boole's own short title from his
# Contents (the full title is kept in manifest.json as "full_title").
TITLES = [
    ("Nature and Design of This Work", None),
    ("Of Signs in General, and of the Signs Appropriate to the Science of Logic in "
     "Particular; Also of the Laws to Which That Class of Signs Are Subject",
     "Signs and Their Laws"),
    ("Derivation of the Laws of the Symbols of Logic from the Laws of the "
     "Operations of the Human Mind", "Derivation of the Laws"),
    ("Of the Division of Propositions into the Two Classes of \u201cPrimary\u201d and "
     "\u201cSecondary;\u201d of the Characteristic Properties of Those Classes, and of "
     "the Laws of the Expression of Primary Propositions", "Division of Propositions"),
    ("Of the Fundamental Principles of Symbolical Reasoning, and of the Expansion "
     "or Development of Expressions Involving Logical Symbols",
     "Principles of Symbolic Reasoning"),
    ("Of the General Interpretation of Logical Equations, and the Resulting "
     "Analysis of Propositions. Also, of the Condition of Interpretability of "
     "Logical Functions", "Of Interpretation"),
    ("On Elimination", None),
    ("On the Reduction of Systems of Propositions", None),
    ("On Certain Methods of Abbreviation", None),
    ("Of the Conditions of a Perfect Method", None),
    ("Of Secondary Propositions, and of the Principles of Their Symbolical "
     "Expression", None),
    ("Of the Methods and Processes to Be Adopted in the Treatment of Secondary "
     "Propositions", "Methods in Secondary Propositions"),
    ("Analysis of a Portion of Dr. Samuel Clarke\u2019s \u201cDemonstration of the Being "
     "and Attributes of God,\u201d and of a Portion of the \u201cEthica Ordine Geometrico "
     "Demonstrata\u201d of Spinoza", "Clarke and Spinoza"),
    ("Example of the Analysis of a System of Equations by the Method of Reduction "
     "to a Single Equivalent Equation V = 0, Wherein V Satisfies the Condition "
     "V(1 \u2212 V) = 0", "Example of Analysis"),
    ("The Aristotelian Logic and Its Modern Extensions, Examined by the Method of "
     "This Treatise", "Of the Aristotelian Logic"),
]
# Boole's Contents, to assert the chapter list against (short titles)
CONTENTS = ["Nature and Design of this Work", "Signs and their Laws", "Derivation of the Laws",
            "Division of Propositions", "Principles of Symbolic Reasoning", "Of Interpretation",
            "Of Elimination", "Of Reduction", "Methods of Abbreviation",
            "Conditions of a Perfect Method", "Of Secondary Propositions",
            "Methods in Secondary Propositions", "Clarke and Spinoza", "Example of Analysis",
            "Of the Aristotelian Logic"]

MAX_PROSE = 7000          # split a chapter whose prose runs past this

# ---------------------------------------------------------------- fixes
# Raw-TeX replacements made before anything else, each (old, new, why).
# Every one must match exactly once.
# ---------------------------------------------------------------- the print
# BOOLE'S PRINTED NUMBERS ARE THE AUTHORITY, not the compile. Every tag in
# I-XV was compared, in order, with the 1854 print (Archive.org
# investigationofl00boolrich: its OCR, _src/scan/richtxt.txt, and the page
# images where the OCR loses a display). One chapter disagrees:
#   VII. 5 (p. 101): the print numbers "{f(1) - f(0)}x + f(0) = 0" as (1),
#   which the transcription leaves unnumbered, so every later number in
#   the chapter is one short -- and Boole's own prose ("Multiply (1) by x",
#   "with (1) and (3)", "substituted in (4)") cites the print's numbers.
RENUMBER = {"VII": lambda n: n + 1}
# Formula corrections made after the compile, each (chapter, old, new, why),
# each matching exactly once among that chapter's formulas.
FORMULA_FIXES = [
    ("VII", r"\text{or, } [f(1)-f(0)]x+f(0)=0. \therefore",
     r"\text{or, } [f(1)-f(0)]x+f(0)=0. \qquad (1) \\ \therefore",
     "p. 101 prints (1) here; the transcription has no number"),
]
PRINT_LOG = []


def print_numbers(held, start, where):
    """Apply RENUMBER and FORMULA_FIXES to one chapter's held formulas."""
    if where in RENUMBER:
        f = RENUMBER[where]
        for i in range(start, len(held)):
            kind, tex = held[i]
            new = re.sub(r"\\qquad \((\d+)\)", lambda m: rf"\qquad ({f(int(m.group(1)))})", tex)
            if new != tex:
                PRINT_LOG.append((where, re.findall(r"\\qquad \(([^)]*)\)", tex),
                                  re.findall(r"\\qquad \(([^)]*)\)", new)))
                held[i] = (kind, new)
    for w, old, new, why in FORMULA_FIXES:
        if w != where:
            continue
        hits = [i for i in range(start, len(held)) if old in held[i][1]]
        assert len(hits) == 1, (where, old, len(hits))
        kind, tex = held[hits[0]]
        held[hits[0]] = (kind, tex.replace(old, new))
        PRINT_LOG.append((where, old, why))


FIXES = [
    # --- the translators' SCAN QUEUE, each checked on the 1854 page ---
    # (A) transcription errors: the print reads as corrected
    ("yx - v(1 - z) - 0; \\\\", "yx - v(1 - z) = 0; \\\\", "VII. 11, p. 106: '= 0'"),
    (r"\textrm{whence } (x - 1 + z) yx = 0,", r"\textrm{whence } (yx - 1 + z) yx = 0,", "VII. 11, p. 106: (yx - 1 + z)"),
    ("(1 - sf) (1 - stp)w", "(1 - st) (1 - stp)w", "VII. 12, p. 107: (1 - st)"),
    ("xy - v (w(1 - z) +z (1 - w));", r"xy = v \{w(1 - z) +z (1 - w)\};", "VIII. 3, p. 118: '=' and braces"),
    ("yz = v (xw + (1 - x ) (1 - w));", r"yz = v \{xw + (1 - x ) (1 - w)\};", "VIII. 3, p. 118: braces"),
    (r"(c'\bar{y} - c'{z}) (1 - x) = 0;", r"(c'\bar{y} - c'\bar{z}) (1 - x) = 0;", "VIII. 3, p. 119: c' z-bar"),
    ("full development $V$, wherein", "full development $V_1$ wherein", "VIII. 2, p. 116: 'development V1'"),
    ("$V_{1}$ and $V_{2}$, are", "$V_{1}$ and $V_{0}$ are", "VIII. 6, p. 122: no comma (V0: see below)"),
    (r"Et + E \left(1-t\right)=0,", r"Et + E' \left(1-t\right)=0,", "IX. 4, p. 133: E'"),
    (r"+ \bar{y}z\bar{w} + \bar{y}\bar{z}w + \bar{y}\bar{z}\bar{x};",
     r"+ \bar{y}z\bar{w} + \bar{y}\bar{z}w + \bar{y}\bar{z}\bar{w};", "IX. Ex. 5, p. 148: last term y z w barred"),
    (r"\bar{x}z\bar{z}w &= 0;", r"\bar{x}\bar{z}w &= 0;", "IX. Ex. 5 (9), p. 148"),
    ("v + (1 - v)v' + (1 - v)(1 - v)v''", "v + (1 - v)v' + (1 - v)(1 - v')v''", "X. 3 (5), p. 153"),
    ("$E$ is equal to $B$, but in\nother cases $E$ vanishes", "$E'$ is equal to $B$, but in\nother cases $E'$ vanishes",
     "X. 7, p. 157: E' twice"),
    ("We shall term $x$; the", "We shall term $x$ the", "XI. 7, p. 165: no semicolon"),
    (r"&\textrm{1st }x(1 - y)", r"&\textrm{1st. }x(1 - y)", "XI. 12, p. 172: '1st.'"),
    (r"&\textrm{2nd.}x = v", r"&\textrm{2nd. }x = v", "XI. 12, p. 172: label spacing"),
    (r"&\textrm{3rd.}x (1 - y)", r"&\textrm{3rd. }x (1 - y)", "XI. 12, p. 172: label spacing"),
    ("t=0, y = 0, x(1-x) = 0, z = 0, x = 0;", "t=0, y = 0, x(1-z) = 0, z = 0, x = 0;", "XII, p. 184: x(1 - z)"),
    ("not born under the day star, and will die", "not born under the dogstar, and will die", "XII. 5, p. 180: 'dogstar'"),
    ("was born under the day star, and will not die", "was born under the dogstar, and will not die", "XII. 5, p. 180: 'dogstar'"),
    ("not born under the dogstar.}", "not born under the dog star.}", "XII. 5, p. 180: 'dog star', two words, as printed"),
    ("Chaldaeos casterosque divinos", "Chaldaeos caeterosque divinos", "XII. 5, p. 180: 'caeterosque'"),
    ("In what area\n", "In what are\n", "XIII. 2, p. 186: 'In what are regarded'"),
    ("every source\ndoubt", "every source of\ndoubt", "XIII. 2, p. 186"),
    ("the process\ninference", "the process of\ninference", "XIII. 2, p. 186"),
    ("might almost\ntermed", "might almost be\ntermed", "XIII. 2, p. 186"),
    ("proposition is prove\n", "proposition is proved\n", "XIII. 7, p. 192"),
    ("2nd. &$x=v[y(1-x)+z(1-y)]$;", r"2nd. &$x=v\{y(1-z)+z(1-y)\}$;", "XIII. 5, p. 190: y(1 - z), braces"),
    ("3rd. &$x=v[p(1-q)+q(1-p)]$;", r"3rd. &$x=v\{p(1-q)+q(1-p)\}$;", "XIII. 5, p. 190: braces as printed"),
    ("p(q-y)=0;", "p(1-y)=0;", "XIII. 5 (4), p. 190: p(1 - y)"),
    ("qz + (1-y)(1-q) = 0\\textrm{;}\n\\]\n\nwhence we find\n\n\\begin{equation}\nx(1-y) = 0",
     "qz + (1-y)(1-q) = 0\\textrm{;}\n\\]\n\nwhence we find\n\n\\begin{equation}\nz(1-y) = 0", "XIII. 6 (10), p. 191: z(1 - y)"),
    ("1-x = r(1-r),", "1-x = v(1-r),", "XIII. 9, p. 203: v(1 - r)"),
    (r"+ \bar{v}y\bar{xw} = 0.", r"+ \bar{v}y\bar{x}\bar{w} = 0.", "XIV. 2, p. 221: two bars"),
    ("+ v'(1-w)(1-w')\\}\\bigr]   \\\\", "+ v'(1-w)(1-w')\\}\\bigr]z   \\\\", "XV. 7 (IV.), p. 234: ']z'"),
    # house style: words inside a formula are \textrm, as for IV. 11
    (r"1 - x by \bar{x}, 1 - y by \bar{y}, \&c.,",
     r"1 - x \textrm{ by } \bar{x}, \quad 1 - y \textrm{ by } \bar{y}, \quad \textrm{\&c.},", "VIII. 3, p. 119: 'by' is a word"),
    ("x^2 = x, or, x (1 - x) = 0;", r"x^2 = x, \quad \textrm{or,} \quad x (1 - x) = 0;", "XI (3), p. 166: 'or' is a word"),
    # (B) the 1854 PRINT is wrong, unambiguously so from Boole's own working
    ("w(1-p)\n= \\frac{0}{0}wr", "1-p\n= \\frac{0}{0}wr",
     "PRINT, VII. 16, p. 112: prints w(1-p); the line above develops 1-p = 0/w(1-r), and the "
     "interpretation is of 'things not productive of pleasure'"),
    ("V_{1}V_{2}=0;", "V_{1}V_{0}=0;", "PRINT, VIII. 6, p. 122: V2 for V0 (the factors defined two lines up are V1, V0)"),
    ("product $V_{1}V_{2}$.", "product $V_{1}V_{0}$.", "PRINT, VIII. 6, p. 122"),
    ("equation $V_{1}V_{2}=0$ may", "equation $V_{1}V_{0}=0$ may", "PRINT, VIII. 6, p. 122"),
    ("$f$ which the interpretation", "of which the interpretation",
     "PRINT, IX. 6, p. 136: the print drops the 'o' of 'of' (a roman f)"),
    ("that the property A is present}", "that the property B is present}",
     "PRINT, IX. Ex. 5, p. 149: (7) on p. 148 makes y (B) present when x, z, w are absent; a reader "
     "pencilled B in the margin of this copy"),
    (r"w = v\left\{x(1-y)(1-q) + y(1-x)(1-z)", r"w = v\left\{x(1-y)(1-z) + y(1-x)(1-z)",
     "PRINT, XIII. 14, p. 207: (1 - q) for (1 - z); equation (1) below it has (1 - z)"),
    ("symbols but\n$z$, $p$, $q$, the result", "symbols but\n$t$, $p$, $q$, the result",
     "PRINT, XIII. 15, p. 208: the question's elements are absolute evils (t), p and q (p. 206)"),
    ("write $u = xy$, and then eliminate the symbols $x$ and $y$",
     "write $u = wz$, and then eliminate the symbols $w$ and $z$",
     "PRINT, XIV. 3, p. 223: u was defined as wz above, and the result gives u, then wz, in x and y"),
    ("in the case of like middle terms:", "in the case of unlike middle terms:",
     "PRINT, XV. 7, p. 235: the paragraph treats (IV.)-(VI.), the unlike case, as p. 236 says"),
    # --- checked against the 1854 page images (_src/scan/boole_bw.pdf) ---
    (r"\{x + (1-x)\}^2 &=& x+y(1-x).", r"\{x + y(1-x)\}^2 &=& x+y(1-x).",
     "IV. 6, p. 56: the print squares x + y(1-x); the transcription dropped the y"),
    ("v^2 = v, or v (1 - v) = 0.", r"v^2 = v, \quad \textrm{or} \quad v (1 - v) = 0.",
     "IV. 11, p. 61: 'or' is a word, set upright in the print"),
    (r"and $\left(1 - x\right)$, $\left(1 - y\right)$, multiplied",
     r"and $\left(1 - x\right)\left(1 - y\right)$, multiplied",
     "V. 11, p. 75: the fourth constituent; the PRINT has the stray comma too "
     "(a misprint: 'the four terms'), corrected"),
    (r"$t_1 t_2, = 0$", r"$t_1 t_2 = 0$", "V. Prop. IV, p. 79: stray comma, not in the print"),
    (r"a_1 \left(1 - a_1\right) t_1 = 0,\textrm{ whence } t_2 = 0.",
     r"a_1 \left(1 - a_1\right) t_1 = 0,\textrm{ whence } t_1 = 0.",
     "VI. 11, p. 91: the print reads 'whence t1 = 0'"),
    ("D = O,", "D = 0,", "VI. 12, p. 93: a zero, not the letter O (OCR and print)"),
    ("Chap. 11. that the operation", r"Chap. \textsc{ii}. that the operation",
     "VI. 10, p. 89: the print reads 'Chap. ii.' (small capitals)"),
    # II. 9: the transcriber italicised a word with $..$, which typesets it
    # as a product of eight variables
    ("is that of $absolute$ identity", "is that of \\emph{absolute} identity", "II.9 italic word set as math"),
    # The hypothetical syllogism (XV. 10) is a \tabbing whose prose lines
    # ("Let the argument---", "be put in the form---") sit between its
    # indented rows; set as two indented blocks with the prose between.
    (r"""\begin{tabbing}
Let the argument--- \= \\
                     \>If $A$ is $B$, $C$ is $D$,   \\
                     \>But $A$ is $B$,   \\
                     \>Therefore $C$ is $D$,   \\
be put in the form---   \\
\hfill If the proposition\ \>$X$ is true, $Y$ is true,   \\
                     \>But $X$ is true,   \\
                     \>Therefore $Y$ is true;
\end{tabbing}""",
     "Let the argument---\n\n\x10If $A$ is $B$, $C$ is $D$,\n\x10But $A$ is $B$,\n"
     "\x10Therefore $C$ is $D$,\n\nbe put in the form---\n\n"
     "\x10If the proposition $X$ is true, $Y$ is true,\n\x10But $X$ is true,\n"
     "\x10Therefore $Y$ is true;\n\n",
     "tabbing -> prose and two indented blocks"),
    # The development table (V. 12) sets its formulas in text mode, so
    # "x = 1" would print as words; made mathematics, ditto marks kept.
    (r"""\textrm{When } &x = 1 &\textrm{ and } &y = 1  &\textrm{ the given function }  &= 0.\\
             &x = 1  &"  &y = 0   &"  "  &= 0.\\
             &x = 0  &"  &y = 1   &"  "  &= 1.\\
             &x = 0  &"  &y = 0   &"  "  &= 1.""",
     r"""When &$x = 1$ &and &$y = 1$ &the given function &$= 0$.\\
             &$x = 1$  &"  &$y = 0$   &"  "  &$= 0$.\\
             &$x = 0$  &"  &$y = 1$   &"  "  &$= 1$.\\
             &$x = 0$  &"  &$y = 0$   &"  "  &$= 1$.""",
     "text-mode formulas in a tabular"),
    # three small-capital labels typed as capitals (VII. 8, VII. 18); the
    # rest of the book writes \textsc{Rule}, \textsc{Note}
    ("TO ELIMINATE ANY SYMBOL FROM A PROPOSED EQUATION.",
     "\\textsc{To Eliminate any Symbol from a Proposed Equation.}", "capitals -> small caps"),
    ("RULE.--\\textit{The terms", "\\textsc{Rule}.--\\textit{The terms", "capitals -> small caps"),
    ("18. NOTE.--The fundamental", "18. \\textsc{Note}.--The fundamental", "capitals -> small caps"),
    (r"\textit{Nov}. 30\textit{th}. 1853.", "Nov. 30th. 1853.",
     "the dateline's italic abbreviations set roman"),
    # Two Greek phrases from the Nicomachean Ethics (IX. 6 and its note):
    # the transcriber set the end of "hemas" in math mode, and in the note
    # typed accents where the breathings go. Corrected to the received text
    # (EN 1106b, 1145a), keeping the print's word forms (\u03ca, no comma).
    (r"pr`os >hm}$\tilde{\alpha}\varsigma$", r"pr`os <hm\~ac}", "\u1f21\u03bc\u1fb6\u03c2 typed half in math"),
    ("t`hn 'up`er\n`hm<'ac 'aret`hn `hrw\"ik'hn tina kai jeian}",
     "t`hn <up`er\n<hm\\~ac >aret`hn <hrw\"ik'hn tina ka`i je'ian}",
     "breathings typed as accents in EN 1145a"),
    # "Let" standing alone above the table of XIII. 4 would be set as a
    # heading; it becomes the table's first cell, as in "Let | x | stand for"
    ("Let \\\\\n\\begin{tabular}{c l l}\n&$x$ = &Something is.",
     "\\begin{tabular}{c l l}\nLet &$x$ = &Something is.", "lead-in into the table"),
    # The Greek of the Metaphysics footnote (III. 4): the transcriber typed
    # y (psi in LGR) for omega with iota subscript in "to auto", and a stray v.
    (r"\textgreek{t`o po>'n}", r"\textgreek{t`o po\~u}", "\u03c0\u03bf\u1fe6 (OCR n for upsilon)"),
    (r"a>i'wnia d'ikaia})", r"a>i'wnia d'ikaia}) ", "a comment ate the space before 'which'"),
    (r">'ama <up'arqein", r"<'ama <up'arqein", "\u1f05\u03bc\u03b1 takes the rough breathing"),
    (r">arx`h ka`i t\~wn >'allwn", r">arq`h ka`i t\~wn >'allwn", "LGR x is xi; \u1f00\u03c1\u03c7\u1f74"),
    (r">axewm'atwn", r">axiwm'atwn", "\u1f00\u03be\u03b9\u03c9\u03bc\u03ac\u03c4\u03c9\u03bd"),
    (r"d'oxan' f'usei", "d'oxan\u00b7 f'usei", "the colon (ano teleia) typed as an accent"),
    # Aristotle, De Caelo I. 1 (268a), in the note to XI. 14: the
    # transcription follows the print word for word but through an OCR
    # (n for upsilon, k for chi, breathings as quotation marks); set in
    # Unicode from the received text, keeping the print's word order.
    (r"""\textgreek{Meg'ejos d`e t`o m`en `ef "en, gramm'h t`o d' 'ep`i d'no 'ep'ipedon, t`o d'
`ep`i tr'ia sv<'wma' Ka'i par`a ta>'nta o'nk "esvtin "allo m'egejos, di`a t`o tri'a p'anta
e`inai ka`i t`o tr`is p'anth. K'ajaper g'ar fasvi ka`i o`i Pnjag'oreioi, t`o p>'an ka`i t`a
p'anta to>'is trisv`in "wrisvtai. Telent`h g`ar ka`i m'esvon ka`i 'ark`h t`on  `arijm`on
"ekei t`on to>'n pant'oc' ta>'nta d`e t`on t>'hs tri'ados. Di`o par`a t>'hs f'nsvews
e'ilhf'otes "wsvper n'omons 'eke'inhs, ka`i pr`os t`as `agisvte'ias kr'wmeja t>'wn
je>'wn t>'y 'arijm>'y to'nt>'y.}""",
     "\\textgreek{\u039c\u03ad\u03b3\u03b5\u03b8\u03bf\u03c2 \u03b4\u1f72 \u03c4\u1f78 \u03bc\u1f72\u03bd \u1f10\u03c6\u2019 \u1f13\u03bd, \u03b3\u03c1\u03b1\u03bc\u03bc\u03ae \u03c4\u1f78 \u03b4\u2019 \u1f10\u03c0\u1f76 \u03b4\u03cd\u03bf \u1f10\u03c0\u03af\u03c0\u03b5\u03b4\u03bf\u03bd, \u03c4\u1f78 \u03b4\u2019 \u1f10\u03c0\u1f76 \u03c4\u03c1\u03af\u03b1 \u03c3\u1ff6\u03bc\u03b1\u00b7 \u03ba\u03b1\u1f76 \u03c0\u03b1\u03c1\u1f70 \u03c4\u03b1\u1fe6\u03c4\u03b1 \u03bf\u1f50\u03ba \u1f14\u03c3\u03c4\u03b9\u03bd \u1f04\u03bb\u03bb\u03bf \u03bc\u03ad\u03b3\u03b5\u03b8\u03bf\u03c2, \u03b4\u03b9\u1f70 \u03c4\u1f78 \u03c4\u03c1\u03af\u03b1 \u03c0\u03ac\u03bd\u03c4\u03b1 \u03b5\u1f36\u03bd\u03b1\u03b9 \u03ba\u03b1\u1f76 \u03c4\u1f78 \u03c4\u03c1\u1f76\u03c2 \u03c0\u03ac\u03bd\u03c4\u1fc3. \u039a\u03b1\u03b8\u03ac\u03c0\u03b5\u03c1 \u03b3\u03ac\u03c1 \u03c6\u03b1\u03c3\u03b9 \u03ba\u03b1\u1f76 \u03bf\u1f31 \u03a0\u03c5\u03b8\u03b1\u03b3\u03cc\u03c1\u03b5\u03b9\u03bf\u03b9, \u03c4\u1f78 \u03c0\u1fb6\u03bd \u03ba\u03b1\u1f76 \u03c4\u1f70 \u03c0\u03ac\u03bd\u03c4\u03b1 \u03c4\u03bf\u1fd6\u03c2 \u03c4\u03c1\u03b9\u03c3\u1f76\u03bd \u1f65\u03c1\u03b9\u03c3\u03c4\u03b1\u03b9. \u03a4\u03b5\u03bb\u03b5\u03c5\u03c4\u1f74 \u03b3\u1f70\u03c1 \u03ba\u03b1\u1f76 \u03bc\u03ad\u03c3\u03bf\u03bd \u03ba\u03b1\u1f76 \u1f00\u03c1\u03c7\u1f74 \u03c4\u1f78\u03bd \u1f00\u03c1\u03b9\u03b8\u03bc\u1f78\u03bd \u1f14\u03c7\u03b5\u03b9 \u03c4\u1f78\u03bd \u03c4\u03bf\u1fe6 \u03c0\u03b1\u03bd\u03c4\u03cc\u03c2\u00b7 \u03c4\u03b1\u1fe6\u03c4\u03b1 \u03b4\u1f72 \u03c4\u1f78\u03bd \u03c4\u1fc6\u03c2 \u03c4\u03c1\u03b9\u03ac\u03b4\u03bf\u03c2. \u0394\u03b9\u1f78 \u03c0\u03b1\u03c1\u1f70 \u03c4\u1fc6\u03c2 \u03c6\u03cd\u03c3\u03b5\u03c9\u03c2 \u03b5\u1f30\u03bb\u03b7\u03c6\u03cc\u03c4\u03b5\u03c2 \u1f65\u03c3\u03c0\u03b5\u03c1 \u03bd\u03cc\u03bc\u03bf\u03c5\u03c2 \u1f10\u03ba\u03b5\u03af\u03bd\u03b7\u03c2, \u03ba\u03b1\u1f76 \u03c0\u03c1\u1f78\u03c2 \u03c4\u1f70\u03c2 \u1f01\u03b3\u03b9\u03c3\u03c4\u03b5\u03af\u03b1\u03c2 \u03c7\u03c1\u03ce\u03bc\u03b5\u03b8\u03b1 \u03c4\u1ff6\u03bd \u03b8\u03b5\u1ff6\u03bd \u03c4\u1ff7 \u1f00\u03c1\u03b9\u03b8\u03bc\u1ff7 \u03c4\u03bf\u03cd\u03c4\u1ff3.}",
     "De Caelo 268a, OCR-garbled LGR"),
    (r"t\~y a>ut\~y", r"t\~w| a>ut\~w|", "LGR y is psi; the dative is \u03c4\u1ff7 \u03b1\u1f50\u03c4\u1ff7"),
    (r"pasv\~wn", r"pas\~wn", "stray v in \u03c0\u03b1\u03c3\u1ff6\u03bd"),
]

# Transcriber notes (TeX comments) in the kept text, and what this prep did.
NOTES = [
    ("III. 4, Prop. III", "'i. e. originally NOT italicized' (the transcriber italicised the "
     "whole enunciation and says the print did not italicise 'i. e.')",
     "whole enunciation set roman (long-italic rule), so moot"),
    ("III", "first-round proofer's rough transliteration of the Metaphysics footnote",
     "ignored; the LGR \\textgreek above it is used"),
    ("III", "'Need to reset equation numbering here'", "numbers taken from the compile"),
    ("V. Prop. II", "'Need to reset equation numbering here for footnote only' (Taylor's theorem "
     "in a footnote is numbered (1), (2) of its own, then the text resumes at (2))",
     "numbers taken from the compile"),
    ("VIII", "'there is a typo in the equation below, unbalanced {' and 'restart equation "
     "numbering here'", "the braces are \\{ \\} and balance; checked by pandoc"),
    ("IX. 3", "'This equation restarts from 3 for no apparent reason'",
     "kept: (3), (4) as printed"),
    ("XII", "'Isn't there a special markup for non-bulleted lists?'", "none"),
    ("XIII", "'% (1)'..'% (6)' comments beside eqnarray rows that LaTeX numbers itself",
     "cross-check only; they agree with the compiled numbers"),
    ("XIII", "'Not exactly same alignment as in original'", "none"),
    ("XIII", "a commented-out eqnarray and '[2nd proofer: Alternate version:]'",
     "the uncommented aligned/gathered version is used"),
    ("XIII. 17", "'[2nd proofer: duplicate \" a \" removed.]'", "kept (a correction)"),
    ("XIV. 1", "'[2nd proofer: Misspelling corrected ... as probably a printer's error.]' "
     "(the word is not identified)", "kept (a correction)"),
    ("XV", "a commented-out \\tabbing version of the eight-forms table", "ignored"),
]

MERGED = []               # tabular continuation rows joined to the row above
L_FOR_ONE = []            # filled by fix_l(): (chapter, formula before)


# ---------------------------------------------------------------- lexing
def group(s, i):
    """s[i] == '{': (content, index after the closing brace)."""
    assert s[i] == "{", s[i:i + 40]
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced brace at " + s[i:i + 60])


def macro(s, name, nargs, fn, optional=False):
    """Replace every \\name[opt]{a}{b}.. by fn(opt, a, b, ..)."""
    pat = re.compile(r"\\" + name + r"(?![A-Za-z])\s*")
    out, i = [], 0
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:m.start()])
        j, opt = m.end(), None
        if optional and j < len(s) and s[j] == "[":
            k = s.index("]", j)
            opt, j = s[j + 1:k], k + 1
        args = []
        for _ in range(nargs):
            while s[j] in " \t\n":
                j += 1
            if s[j] == "{":
                a, j = group(s, j)
            else:
                a, j = s[j], j + 1
            args.append(a)
        out.append(fn(opt, *args))
        i = j


def blank_comments(s):
    """Comments -> spaces, keeping every offset (and so every line number);
    the % itself stays, to mark TeX's end-of-line join. Returns the text and
    the comments as (line, text)."""
    found = []
    out = []
    for n, line in enumerate(s.split("\n"), 1):
        m = re.search(r"(?<!\\)%", line)
        if m:
            found.append((n, line[m.start():]))
            line = line[:m.start()] + "%" + " " * (len(line) - m.start() - 1)
        out.append(line)
    return "\n".join(out), found


# ---------------------------------------------------------------- numbers
def eqtags():
    """{input line: [tag, ...]} for every equation number LaTeX prints."""
    if not TAGS.exists() or TAGS.stat().st_mtime < SRC.stat().st_mtime:
        src = SRC.read_text()
        patch = (r"\makeatletter\let\EQoldtagform\tagform@"
                 r"\def\tagform@#1{\immediate\write16{EQTAG:\the\inputlineno:#1:}\EQoldtagform{#1}}"
                 r"\makeatother\providecommand{\textgreek}[1]{G}")
        # same line count: the patch rides on the \begin{document} line, and
        # babel's greek option (not installed everywhere) is dropped
        src = src.replace(r"\usepackage[greek,english]{babel}", r"\usepackage[english]{babel}", 1)
        src = src.replace(r"\begin{document}", patch + r"\begin{document}", 1)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "b.tex").write_text(src)
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "b.tex"], cwd=d,
                               capture_output=True, text=True, timeout=600)
            log = (Path(d) / "b.log").read_text(errors="replace")
        log = log.replace("\n", "")
        found = re.findall(r"EQTAG:(\d+):([^:]{1,8}):", log)
        assert len(found) > 300, ("compile failed?", r.returncode, r.stdout[-500:])
        TAGS.write_text("".join(f"{a}\t{b}\n" for a, b in found))
    tags = {}
    for line in TAGS.read_text().splitlines():
        a, b = line.split("\t")
        tags.setdefault(int(a), []).append(b)
    return tags


# ---------------------------------------------------------------- math
MATH_ENVS = r"equation\*?|eqnarray\*?|align\*?|gather\*?|multline\*?"
MATH = re.compile(r"\\begin\{(" + MATH_ENVS + r")\}(.*?)\\end\{\1\}"
                  r"|\\\[(.*?)\\\]|\$\$(.*?)\$\$|(?<!\\)\$(.+?)(?<!\\)\$", re.S)


def split_top(s, sep):
    """Split on an unescaped separator at brace depth 0."""
    parts, depth, cur, i = [], 0, [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            if sep == "\\\\" and s.startswith("\\\\", i) and depth == 0:
                parts.append("".join(cur))
                cur = []
                i += 2
                continue
            cur.append(s[i:i + 2])
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if sep == "&" and c == "&" and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    parts.append("".join(cur))
    return parts


def mclean(tex):
    """Transcription macros -> what pandoc's TeX reader accepts."""
    tex = re.sub(r"(?<!\\)%\s*", " ", tex)
    tex = re.sub(r"\\setcounter\{[^}]*\}\{[^}]*\}", "", tex)
    tex = re.sub(r"\\(nonumber|notag|hfill)(?![A-Za-z])", "", tex)
    tex = re.sub(r"\\hspace\*?\{[^}]*\}", " ", tex)
    tex = macro(tex, "lefteqn", 1, lambda o, a: a)
    tex = macro(tex, "textrm", 1, lambda o, a: r"\text{" + a + "}")
    tex = macro(tex, "textsc", 1, smallcaps)     # "(Ax. \textsc{i}.)" in a \text
    tex = macro(tex, "textit", 1, lambda o, a: r"\textit{" + a + "}")
    tex = tex.replace("·", r"\cdot ")
    tex = tex.replace(r"\begin{split}", r"\begin{aligned}").replace(r"\end{split}", r"\end{aligned}")
    tex = re.sub(r"\s+", " ", tex).strip()
    new, changed = fix_braces(tex, None)
    if changed:
        BRACES.append((tex, new))
    return new


BRACES = []               # (chapter, formula) whose bare {..} became \{..\}


def fix_braces(tex, where):
    """A BARE BRACE GROUP HOLDING A SUM IS ONE OF BOOLE'S BRACKETS. The
    transcription types "vs {n(1-t) + t(1-n)}" where the print has braces;
    TeX swallows a bare group, so the formula prints (and pandoc reads) as
    vsn(1-t) + t(1-n), a different equation. A group that is a command's
    argument, a script's base or argument, or holds no + or -, is left."""
    out, i, changed = [], 0, False
    while i < len(tex):
        c = tex[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+\*?|.)", tex[i:])
            out.append(m.group(0))
            i += len(m.group(0))
            # a command's brace arguments are copied whole
            name = m.group(1)
            nargs = {"frac": 2, "text": 1, "bar": 1, "begin": 1, "end": 1, "sqrt": 1,
                     "textit": 1, "mathrm": 1, "acute": 1, "tilde": 1, "dfrac": 2,
                     "tfrac": 2, "hat": 1, "underline": 1, "overline": 1}.get(name, 0)
            for _ in range(nargs):
                while i < len(tex) and tex[i] == " ":
                    out.append(" ")
                    i += 1
                if i < len(tex) and tex[i] == "{":
                    g, j = group(tex, i)
                    out.append("{" + (fix_braces(g, where)[0] if name in ("frac", "dfrac", "tfrac", "sqrt") else g) + "}")
                    i = j
            continue
        if c == "{":
            g, j = group(tex, i)
            before = "".join(out).rstrip()
            after = tex[j:].lstrip()
            if (re.search(r"[+-]", g) and not before.endswith(("^", "_"))
                    and not after.startswith(("^", "_"))):
                inner, _ = fix_braces(g, where)
                out.append(r"\{" + inner + r"\}")
                changed = True
            else:
                out.append("{" + g + "}")
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), changed


def fix_l(tex, where):
    """The OCR's letter l for the digit 1, inside a formula."""
    bare = re.sub(r"\\text\{[^}]*\}", "", tex)
    if re.search(r"(?<![A-Za-z\\])l(?![A-Za-z])", bare):
        new = re.sub(r"(?<![A-Za-z\\])l(?![A-Za-z])",
                     "1", tex)
        # never inside \text{..}
        assert re.sub(r"\\text\{[^}]*\}", "", new) != bare
        L_FOR_ONE.append((where, tex, new))
        return new
    return tex


class Math:
    def __init__(self, tags):
        self.held = []           # (kind, payload)
        self.tags = tags
        self.where = "?"
        self.envs = []           # for the report: env names seen
        self.used = set()
        self.align_like = False
        self.in_note = False
        self.notes = []          # (start, end) offsets of every footnote
        self.note_end_line = None

    def numbers(self, start, end, expected):
        """The next `expected` numbers LaTeX printed on lines start..end.
        Numbers are CONSUMED, since two displays inside one footnote share
        its closing line (TeX reads a footnote whole, so \\inputlineno is
        the line where the footnote ends)."""
        pool = [(ln, i, t) for ln in range(start, end + 1)
                for i, t in enumerate(self.tags.get(ln, [])) if (ln, i) not in self.used]
        got = [t for ln, i, t in pool]
        take = expected
        if expected and len(got) >= 2 * expected and got[:expected] == got[expected:2 * expected] \
                and self.align_like:
            take = 2 * expected          # align's measuring pass logs twice
        if expected == 0:
            assert not got or self.in_note, (self.where, start, end, got)
            return []
        assert len(got) >= expected, (self.where, start, end, expected, got)
        if not self.in_note:
            assert len(got) == take, (self.where, start, end, expected, got)
        for ln, i, t in pool[:take]:
            self.used.add((ln, i))
        return got[:expected]

    def display(self, env, body, start, end):
        """One displayed environment -> list of ('D', tex) / ('T', text)."""
        self.envs.append(env)
        star = env.endswith("*")
        base = env.rstrip("*")
        # \intertext splits the display in two around a line of prose
        pieces = re.split(r"\\intertext\s*", body)
        chunks = [pieces[0]]
        texts = []
        for p in pieces[1:]:
            t, j = group(p, p.index("{"))
            texts.append(t)
            chunks.append(p[j:])
        multi = base in ("eqnarray", "align", "gather", "multline")
        rowsets = []
        for c in chunks:
            rows = [r for r in split_top(c, "\\\\") if r.strip()] if multi else [c]
            rowsets.append(rows)

        def numbered(r):
            if re.search(r"\\tag\{", r):
                return True
            if star or base == "multline":
                return False
            if base in ("eqnarray", "align", "gather", "equation"):
                return not re.search(r"\\(nonumber|notag)(?![A-Za-z])", r)
            return False
        flags = [[numbered(r) for r in rows] for rows in rowsets]
        if base == "multline" and any(any(f) for f in flags):
            flags = [[False] * len(rows) for rows in rowsets]
            flags[-1][-1] = True
        nums = iter(self.numbers(start, end, sum(sum(f) for f in flags)))
        out = []
        for k, (rows, fl) in enumerate(zip(rowsets, flags)):
            done = []
            for r, f in zip(rows, fl):
                r = re.sub(r"\\tag\*?\{[^}]*\}", "", r)
                if base == "eqnarray":
                    cells = split_top(r, "&") + ["", ""]
                    a, b, c = cells[0], cells[1], "".join(cells[2:])
                    r = f"{a} &{b} {c}" if (b.strip() or c.strip()) else a
                r = mclean(r)
                if f:
                    r += rf" \qquad ({next(nums)})"
                done.append(r)
            if len(done) == 1:
                tex = re.sub(r"(?<!\\)&", "", done[0]) if base in ("eqnarray", "align") else done[0]
            elif any("&" in split_top(d, "&")[0] or len(split_top(d, "&")) > 1 for d in done):
                tex = r"\begin{aligned} " + r" \\ ".join(done) + r" \end{aligned}"
            else:
                tex = r"\begin{gathered} " + r" \\ ".join(done) + r" \end{gathered}"
            tex = tex.replace(r"\begin{split}", r"\begin{aligned}").replace(r"\end{split}", r"\end{aligned}")
            out.append(("D", fix_l(tex, self.where)))
            if k < len(texts):
                out.append(("T", texts[k]))
        return out

    def sub(self, s, base_offset, line_at):
        """Hold every formula in s; s[0] sits at source offset base_offset."""
        def one(m):
            off = base_offset + m.start()
            start = line_at(off)
            end = line_at(base_offset + m.end())
            note = [e for a, e in self.notes if a <= off < e]
            self.in_note = bool(note)
            if note:
                start = end = line_at(note[0])
            self.align_like = bool(m.group(1)) and m.group(1).rstrip("*") in ("align", "gather", "multline")
            if m.group(1):
                parts = self.display(m.group(1), m.group(2), start, end)
            elif m.group(3) is not None or m.group(4) is not None:
                body = m.group(3) if m.group(3) is not None else m.group(4)
                self.envs.append("\\[")
                tagm = re.search(r"\\tag\{([^}]*)\}", body)
                tex = mclean(re.sub(r"\\tag\{[^}]*\}", "", body))
                if tagm:
                    tex += rf" \qquad ({self.numbers(start, end, 1)[0]})"
                else:
                    self.numbers(start, end, 0)
                parts = [("D", fix_l(tex, self.where))]
            else:
                self.envs.append("$")
                parts = [("I", fix_l(mclean(m.group(5)), self.where))]
            out = []
            for kind, x in parts:
                if kind == "T":
                    out.append("\n\n" + self.sub(x, 0, lambda o: 0) + "\n\n")
                else:
                    self.held.append((kind, x))
                    out.append(f"\x00{len(self.held) - 1}\x00")
            return "".join(out)
        return MATH.sub(one, s)


# ---------------------------------------------------------------- text
GREEK = {"a": "α", "b": "β", "g": "γ", "d": "δ", "e": "ε", "z": "ζ", "h": "η",
         "j": "θ", "i": "ι", "k": "κ", "l": "λ", "m": "μ", "n": "ν", "x": "ξ",
         "o": "ο", "p": "π", "r": "ρ", "s": "σ", "c": "ς", "t": "τ", "u": "υ",
         "f": "φ", "q": "χ", "y": "ψ", "w": "ω", "v": ""}   # v: LGR's no-op
GMARK = {">": "\u0313", "<": "\u0314", "'": "\u0301", "`": "\u0300", "~": "\u0342",
         "|": "\u0345", '"': "\u0308"}


def lgr(s):
    """babel's LGR transliteration -> Unicode Greek. Accents and breathings
    precede their vowel; an iota subscript follows it."""
    s = s.replace("\\~", "~").replace("\\dots", "…")
    out, pending = [], []
    for ch in s:
        if pending and ch.lower() not in "aehiouwr" and ch not in GMARK:
            # marks reach only a vowel (or rho's breathing); a lone acute
            # before a space or consonant is an elision mark
            out.append("\u2019" if "\u0301" in pending else "")
            pending = []
        if ch in GMARK and ch != "|":
            pending.append(GMARK[ch])
        elif ch == "|":
            out.append(GMARK["|"])
        elif ch.lower() in GREEK:
            g = GREEK[ch.lower()]
            out.append((g.upper() if ch.isupper() else g) + "".join(pending))
            pending = []
        else:
            out.append(ch)
    t = unicodedata.normalize("NFC", "".join(out))
    # final sigma at a word's end
    t = re.sub(r"σ(?![\wͅ])", "ς", t)
    return t


ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303"}
ROMAN_RE = re.compile(r"(?i)^(?=[ivxlc])(c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$")


def is_roman(w):
    return bool(ROMAN_RE.match(w))


def smallcaps(o, a):
    """\\textsc: Roman numerals are capitals; a lower-case label is titled."""
    a = a.strip()

    def word(w):
        core = w.strip(".,;:")
        if core and is_roman(core):
            return w.upper()
        return w
    a = " ".join(word(w) for w in a.split())
    if a == a.lower():                       # "type", "premises": a label
        a = titlecase(a)
    return a


def titlecase(s):
    small = {"of", "and", "the", "for", "a", "an", "in", "to", "on", "by", "or"}
    ws = s.split()
    out = []
    for i, w in enumerate(ws):
        core = w.strip(".,;:")
        if is_roman(core):
            out.append(w.upper())
        elif i and w.lower() in small:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


ITALIC_MAX = 120          # a longer italic span is an enunciation: roman
italic_stats = {"kept": 0, "roman": 0, "math_only": 0, "whole_para": 0}


def italic(o, a):
    a2 = a.strip()
    if not a2:
        return a
    bare = re.sub(r"\x00\d+\x00", "", a2).strip(" .,;:")
    if not bare:
        italic_stats["math_only"] += 1
        return a
    if len(a2) > ITALIC_MAX or re.search(r"[.;:]\s+\S", a2.rstrip(".")):
        italic_stats["roman"] += 1
        return a
    italic_stats["kept"] += 1
    lead = a[:len(a) - len(a.lstrip())]
    trail = a[len(a.rstrip()):]
    # a trailing stop or comma goes outside the underscores
    m = re.match(r"(.*?)([.,;:]*)$", a2, re.S)
    return f"{lead}_{m.group(1)}_{m.group(2)}{trail}"


def text_chars(s):
    s = macro(s, "textgreek", 1, lambda o, a: lgr(a))
    s = re.sub(r"\{\\(ae|AE|oe)\}|\\(ae|AE|oe)(?![A-Za-z])(\{\})?",
               lambda m: {"ae": "æ", "AE": "Æ", "oe": "œ"}[m.group(1) or m.group(2)], s)
    s = re.sub(r"\\([`'^\"~])\{?([A-Za-z])\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    s = s.replace("``", "“").replace("''", "”")
    s = re.sub(r"\\lq\\lq|\\rq\\rq", lambda m: "“" if "l" in m.group(0) else "”", s)
    s = re.sub(r"(?<![\w\\])`", "‘", s)
    s = s.replace("'", "’")
    s = s.replace("---", "—").replace("--", "—")
    s = re.sub(r"\\dots(?![A-Za-z])\s?", "…", s)
    s = s.replace("\\&", "&").replace("\\ ", " ").replace("\\\n", " ").replace("~", " ")
    s = re.sub(r"\\[,;:]", "", s)
    return s


def unwrap(s):
    """Plain layout macros and environments with nothing to say."""
    for name in ("bigskip", "medskip", "smallskip", "noindent", "large", "Large", "Huge",
                 "normalsize", "small", "newpage", "clearpage", "mainmatter", "frontmatter",
                 "hfill", "par", "indent"):
        s = re.sub(r"\\" + name + r"(?![A-Za-z])\s*", " ", s)
    s = re.sub(r"\\(vspace|hspace)\*?\{[^}]*\}", " ", s)
    s = re.sub(r"\\setcounter\{[^}]*\}\{[^}]*\}", "", s)
    return s


def tab_line(cells):
    cells = [re.sub(r"\s+", " ", c).strip() for c in cells]
    return "\x10" + " | ".join(cells)


def tabular(o, spec, body):
    """\\begin{tabular} -> TAB-led rows, cells split on " | " (a pipe table;
    assemble sets it as <table class="math"> when it carries a formula)."""
    body = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}\{\{?(.*?)\}?\}(?=\s*(\\\\|&|$))", r"\1", body)
    rows = []
    for r in split_top(body, "\\\\"):
        if not r.strip():
            continue
        cells = [c.strip() for c in split_top(r, "&")]
        # a row whose only cell is the last continues the row above, unless
        # that row's cell is finished ("their \\ freedom of action")
        cont = (rows and all(not c for c in cells[:-1]) and len(cells) > 1
                and not rows[-1][-1].replace("}", "").rstrip().endswith((".", ",", ";", ":")))
        if cont:
            MERGED.append((rows[-1][-1], cells[-1]))
        cells = [re.sub(r"\\hspace\*?\{[^}]*\}", "", c).strip() for c in cells]
        if cont and rows:
            rows[-1][-1] = (rows[-1][-1] + " " + cells[-1]).strip()
            continue
        rows.append(cells)
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    # a column empty in every row is layout (the assumption lists' indent)
    keep = [j for j in range(width) if any(r[j] for r in rows)]
    rows = [[r[j] for j in keep] for r in rows]
    # a hyphen left at a cell's line end joins the word ("not- Y's")
    rows = [[re.sub(r"-\s+(?=\S)", "-", c) for c in r] for r in rows]
    # every row as wide as the widest: an empty LAST cell is written as the
    # explicit '""' (assemble's empty cell), since tab_clean drops trailing
    # empties and epubcheck refuses a row wider than the first (XV's table
    # of eight forms carries its equation number "(1)" on one row only)
    rows = [r[:-1] + ['""'] if len(r) > 1 and not r[-1] else r for r in rows]
    return "\n\n" + "\n".join(tab_line(r) for r in rows) + "\n\n"


def lines_block(o, body):
    ls = [l.strip() for l in split_top(body, "\\\\") for l in [l] if l.strip()]
    return "\n\n" + "\n".join("\x10" + re.sub(r"\s+", " ", l) for l in ls) + "\n\n"


def itemize(o, body):
    items = [i.strip() for i in re.split(r"\\item(?:\[[^\]]*\])?", body) if i.strip()]
    return "\n\n" + "\n".join("\x10" + re.sub(r"\s+", " ", i) for i in items) + "\n\n"


def center(o, body):
    """Classify a centred block: a label, a table, or displayed text."""
    b = body.strip()
    if "\\begin{tabular}" in b or "\x10" in b:
        return "\n\n" + b + "\n\n"
    labels = re.findall(r"\\textsc\s*\{([^}]*)\}", b)
    rest = re.sub(r"\\textsc\s*\{[^}]*\}\.?", "", b).strip()
    if labels and (not rest or rest.startswith("\\emph")):
        out = []
        for lab in labels:
            lab = titlecase(lab.strip().rstrip(".").lower() if lab.strip().lower() == lab.strip()
                            else lab.strip().rstrip("."))
            out.append(lab + ".")
        if rest:
            out.append(rest)
        return "\n\n" + "\n\n".join(out) + "\n\n"
    return "\n\n" + b + "\n\n"


def convert(s, notes):
    """Body TeX (math already held) -> paragraphs text with \x10 tab lines."""
    # TeX's comment join: "%" + newline + leading space is nothing
    s = re.sub(r"(?<!\\)%[ \t]*\n[ \t]*", "", s)
    s = unwrap(s)
    # footnotes held, their marks become \x02n\x02
    def fn(o, a):
        notes.append(a)
        return f"\x02{len(notes) - 1}\x02"
    s = macro(s, "footnote", 1, fn)
    assert "\\footnotemark" not in s and "\\footnotetext" not in s
    s = re.sub(r"\\begin\{tabular\}(\[[^\]]*\])?", r"\\TABULAR", s)
    s = s.replace("\\end{tabular}", "}")
    s = re.sub(r"\\TABULAR\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", lambda m: "\\TABULAR{" + m.group(1) + "}{", s)
    s = macro(s, "TABULAR", 2, lambda o, spec, body: tabular(o, spec, body))
    for env, fn2 in (("verse", lines_block), ("itemize", itemize)):
        s = re.sub(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}",
                   lambda m: fn2(None, m.group(1)), s, flags=re.S)
    s = re.sub(r"\\begin\{center\}(.*?)\\end\{center\}", lambda m: center(None, m.group(1)), s, flags=re.S)
    return s


def tab_clean(l):
    """One TAB-led line: cells joined by exactly " | ", an empty first cell
    kept (render_math_table splits on the spaced pipe after the tab)."""
    cells = [re.sub(r"\s+", " ", c).strip() for c in l[1:].split("|")]
    # ditto marks, typed '' or " in the source: one mark, the plain "
    cells = [re.sub(r"[\u201d\u201c]", '"', c) if re.fullmatch(r'[\s"\u201d\u201c]+', c) else c
             for c in cells]
    while len(cells) > 1 and not cells[-1]:
        cells.pop()
    return "\t" + " | ".join(cells)


def whole_italic(t):
    """A PARAGRAPH WHOLLY IN ITALICS IS AN ENUNCIATION, NOT EMPHASIS: the
    statement of a Proposition, a Rule, a definition set out on its own.
    The label beside it ("Proposition I.", "Rule.--") already marks it, so
    it is set roman, as the long ones already are; italics are kept for
    words and phrases inside running text."""
    t = re.sub(r"(?<=\w)_ _(?=\w)", " ", t)      # two italic spans side by side are one
    held = []
    m_ = re.sub(r"\\\(.*?\\\)|\x00\d+\x00", lambda m: (held.append(m.group(0)), f"\x0e{len(held) - 1}\x0e")[1], t)
    m = re.fullmatch(r"(\d+\. |[A-Z][a-z]+\.\u2014)?_([^_]+)_([.,;:]*)(\s*\x02\d+\x02)*", m_)
    if not m:
        return t
    italic_stats["whole_para"] += 1
    m_ = (m.group(1) or "") + m.group(2) + m.group(3) + m_[m.end(3):]
    return re.sub(r"\x0e(\d+)\x0e", lambda k: held[int(k.group(1))], m_)


def finish(s, notes, held):
    """Italics, small caps, characters; paragraphs; math back."""
    def inline_fmt(t):
        t = re.sub(r"\{\\it\s+([^{}]*)\}", r"\\textit{\1}", t)
        t = macro(t, "textit", 1, italic)
        t = macro(t, "emph", 1, italic)
        t = macro(t, "textsc", 1, smallcaps)
        t = macro(t, "text", 1, lambda o, a: a)
        t = macro(t, "textrm", 1, lambda o, a: a)
        t = text_chars(t)
        assert not re.search(r"\\[A-Za-z]+", t), re.findall(r".{30}\\[A-Za-z]+.{30}", t)[:3]
        t = t.replace("{", "").replace("}", "")
        return t

    def math_back(t, in_note=False):
        def one(m):
            kind, tex = held[int(m.group(1))]
            if kind == "I":
                return rf"\({tex}\)"
            # \x11 marks a break made by a display, inside a TeX paragraph
            return rf" \[{tex}\] " if in_note else f" \x11\\[{tex}\\]\x11 "
        return re.sub(r"\x00(\d+)\x00", one, t)

    notes_txt = []
    for n in notes:
        t = inline_fmt(n)
        t = math_back(t, in_note=True)
        notes_txt.append(re.sub(r"\s+", " ", t).strip())

    s = s.replace("\\\\", " ")          # a forced line break in prose
    s = inline_fmt(s)
    s = math_back(s)
    # TeX's comment join: "%" + newline + leading space is nothing
    s = re.sub(r"%[ \t]*\n[ \t]*", "", s)
    assert "%" not in s.replace("\\%", ""), s[s.index("%") - 60:s.index("%") + 20]
    paras = []
    for p in re.split(r"\n[ \t]*\n", s):
        if not p.strip():
            continue
        if "\x10" in p:
            # a block of tab lines (it may carry stray text around it)
            lines = [l for l in p.split("\n") if l.strip()]
            pre = [l for l in lines if not l.startswith("\x10")]
            assert not pre or all(l.startswith("\x10") for l in lines[len(pre):]), p[:200]
            if pre:
                paras.append(re.sub(r"\s+", " ", " ".join(pre)).strip())
            paras.append("\n".join(tab_clean(l) for l in lines if l.startswith("\x10")))
            continue
        # A DISPLAY STAYS INSIDE ITS PARAGRAPH, on a line of its own (a
        # single newline, no tab). Split into separate paragraphs, the
        # lead-in before a display ("Hence we have", "Therefore", "Let") is
        # a short line with no closing stop, and assemble.is_subheading set
        # fifteen of them as <h4> headings; a paragraph with a newline in
        # it never is one. Both renderers set the whole as one <p>, the
        # display as a block inside it, and the notes follow the paragraph.
        marks = [int(x) for x in re.findall(r"\x02(\d+)\x02", p)]
        lines = []
        for piece in p.split("\x11"):
            t = re.sub(r"\s*\x02\d+\x02", "", piece)
            t = whole_italic(re.sub(r"\s+", " ", t).strip())
            if t:
                lines.append(t)
        if lines:
            paras.append("\n".join(lines))
        for k in marks:
            paras.append("Footnote: " + notes_txt[k])
    # a short lead-in with no stop, then a display ("Thus the equation"):
    # one paragraph, for the same reason as above
    out = []
    for p in paras:
        if (out and p.startswith("\\[") and "\n" not in out[-1] and len(out[-1]) < 90
                and not out[-1].startswith(("\t", "Footnote:", "\\["))
                and out[-1][-1] not in ".;:,\u2014!?\u201d"):
            out[-1] += "\n" + p
        else:
            out.append(p)
    return out


# ---------------------------------------------------------------- the book
def main():
    raw = SRC.read_text().replace("\r\n", "\n")
    # A PAGE MARKER BEFORE AN ARTICLE IS A PARAGRAPH BREAK. The proofers'
    # "%---File: 018.png---" comment sits between the last line of one
    # article and "18. In Prop. v." with no blank line, so TeX (and this
    # prep) would run Boole's article 18 into article 17. Three in scope.
    raw, n = re.subn(r"^%-+File: \d+\.png-+[ \t]*$(?=\n\d+\. )", "", raw, flags=re.M)
    assert n == 9, n          # nine in the whole file, three in scope
    b, comments = blank_comments(raw)
    linestarts = [0] + [m.end() for m in re.finditer(r"\n", b)]
    shifts = []               # (offset in the fixed text, length change)
    for old, new, why in FIXES:
        assert raw.count(old) == 1, ("FIX does not match once", why)
        # the same edit in both copies, so offsets stay aligned between them
        i = raw.index(old)
        bi = b.index(old) if b.count(old) == 1 else None
        assert bi == i, why
        raw = raw[:i] + new + raw[i + len(old):]
        b = b[:i] + new + b[i + len(old):]
        shifts.append((i + len(new), len(new) - len(old)))


    def line_at(off):
        """Source line of an offset in the fixed text (fixes hold no numbers)."""
        off -= sum(d for at, d in shifts if off >= at)
        return bisect.bisect_right(linestarts, off)

    # cut points
    heads = [(m.start(), m.group(0)) for m in re.finditer(r"\\chapter\[[^\]]*\]", b)]
    pre = [o for o, h in heads if h == r"\chapter[PREFACE.]"][0]
    cont = [o for o, h in heads if h == r"\chapter[CONTENTS.]"][0]
    main_ = b.index("\\mainmatter")
    prob = [o for o, h in heads if h.startswith(r"\chapter[ON THE THEORY OF PROBABILITIES")][0]
    chap_offs = [o for o, h in heads if main_ < o < prob]
    assert len(chap_offs) == 15, len(chap_offs)

    # Boole's Contents, asserted
    toc = re.findall(r"\\textsc\{([^}]*),\}\\dotfill\s*(\d+)", b[cont:main_])
    assert [t for t, p in toc[:15]] == CONTENTS, toc[:15]
    assert len(toc) == 22
    pages = [int(p) for t, p in toc]

    # dedication: the centred block on the page before the Preface
    ded = b[b.rindex("TO\\\\", 0, pre):b.index("\\end{center}", b.rindex("TO\\\\", 0, pre))]
    ded_lines = [re.sub(r"\\(bigskip|large|normalsize)", "", l).strip().rstrip("\\").strip()
                 for l in ded.split("\n")]
    ded_lines = [l for l in ded_lines if l]

    tags = eqtags()
    sections = []
    # Preface body: after its centred heading block
    pre_body_start = b.index("\\bigskip", b.index("\\end{center}", pre)) + len("\\bigskip")
    spans = [("Preface", pre_body_start, cont)]
    for k, o in enumerate(chap_offs):
        # body starts after the \chapter[..]{..} heading's closing brace
        j = b.index("]", o) + 1
        while b[j] in " \t\n":
            j += 1
        assert b[j] == "{", b[o:o + 80]
        _, j = group(b, j)
        end = chap_offs[k + 1] if k + 1 < 15 else prob
        spans.append((k + 1, j, end))

    math = Math(tags)
    # footnote spans: TeX numbers a display inside one at the note's last line
    for m in re.finditer(r"\\footnote(?![A-Za-z])\s*", b):
        _, e = group(b, m.end())
        math.notes.append((m.start(), e - 1))
    for key, start, end in spans:
        math.where = "Preface" if key == "Preface" else ROMAN[key - 1]
        seg = b[start:end]
        seg = seg.replace("\\setcounter{chapter}{13}", "")
        held_from = len(math.held)
        seg = math.sub(seg, start, line_at)
        print_numbers(math.held, held_from, math.where)
        notes = []
        seg = convert(seg, notes)
        paras = finish(seg, notes, math.held)
        sections.append((key, paras))

    # the equation numbers LaTeX printed in scope must all have been used
    lo, hi = line_at(pre), line_at(prob)
    printed = sum(len(v) for ln, v in tags.items() if lo <= ln < hi)
    unused = sorted((ln, v[i]) for ln, v in tags.items() if lo <= ln < hi
                    for i in range(len(v)) if (ln, i) not in math.used)
    assert not unused, ("equation numbers LaTeX printed that no display carries", unused)
    print(f"equation numbers: {printed} logged in scope, every one placed")

    write(sections, ded_lines, pages)


def heading(k):
    full, short = TITLES[k - 1]
    return f"Chapter {k}: {short or full}"


def write(sections, ded_lines, pages):
    out = HERE / "chapters"
    out.mkdir(exist_ok=True)
    for f in out.glob("*.txt"):
        f.unlink()
    manifest = []
    n = 0
    for key, paras in sections:
        if key == "Preface":
            ded = "\n".join("\t" + titlecase_ded(l) for l in ded_lines)
            text = "Dedication\n\n" + ded + "\n\nPreface\n\n" + "\n\n".join(paras) + "\n"
            (out / "000.txt").write_text(text)
            manifest.append({"file": "000.txt", "title": "Preface", "part": 1, "of": 1,
                             "words": len(text.split()),
                             "split_headings": ["Dedication", "Preface"]})
            n = 1
            continue
        title = heading(key)
        parts = split_parts(paras)
        for p, chunk in enumerate(parts, 1):
            head = title + (f"\n(Part {p} of {len(parts)})" if len(parts) > 1 else "")
            text = head + "\n\n" + "\n\n".join(chunk) + "\n"
            fn = f"{n:03d}.txt"
            (out / fn).write_text(text)
            e = {"file": fn, "title": title, "part": p, "of": len(parts),
                 "words": len(text.split()), "number": key}
            full, short = TITLES[key - 1]
            if p == 1 and short:
                e["full_title"] = full
            if p == 1:
                e["source_page"] = pages[key - 1]
            manifest.append(e)
            n += 1
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {n} files")
    if L_FOR_ONE:
        print(f"l -> 1 in {len(L_FOR_ONE)} formulas")
    print("italics:", italic_stats)
    print("bare brace groups made brackets:", len(BRACES))
    if "--report" in sys.argv:
        for w, a, b in L_FOR_ONE:
            print(f"  l->1 [{w}] {a}")
        for x in PRINT_LOG:
            print("  print:", x)
        for a, b in BRACES:
            print(f"  braces: {a}\n      -> {b}")
        for a, b in MERGED:
            print(f"  merged row: {a!r} + {b!r}")


DEDICATION = ["To", "John Ryall, LL.D.", "Vice-President and Professor of Greek",
              "in Queen\u2019s College, Cork,", "this work is inscribed",
              "in testimony of friendship and esteem"]


def titlecase_ded(l):
    """The dedication's capitals, set as the house sets running text."""
    i = [x.upper().replace("\u2019", "'") for x in DEDICATION].index(l)
    return DEDICATION[i]


MATHSPAN = re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)


def prose_words(t):
    return len(MATHSPAN.sub(" ", t).split())


def split_parts(paras):
    """Split at article boundaries ("12. ...") when the prose runs long."""
    total = sum(prose_words(p) for p in paras)
    if total <= MAX_PROSE:
        return [paras]
    k = -(-total // MAX_PROSE)
    target = total / k
    parts, cur, acc, top = [], [], 0, 0
    for p in paras:
        # an ARTICLE is the next number up; Boole's numbered premises and
        # definitions restart at 1 inside an article and are not breaks
        m = re.match(r"(\d+)\. ", p)
        art = bool(m) and int(m.group(1)) == top + 1
        if art:
            top += 1
        if cur and art and acc >= target * (len(parts) + 1) and len(parts) < k - 1:
            parts.append(cur)
            cur = []
        cur.append(p)
        acc += prose_words(p)
    parts.append(cur)
    return parts


if __name__ == "__main__":
    main()
