"""Build chapters/ + manifest.json for Silvanus P. Thompson's Light Visible
and Invisible from the Archive.org OCR of the 1897 Macmillan edition.

The Royal Institution Christmas lectures of 1896 — the SIXTH RI Christmas
Lecture volume in the collection, and the only one with no Gutenberg
edition behind it. Delivered within a year of Rontgen's announcement, with
a whole lecture on X-rays; Thompson dates the first lecture in the text
itself to "29th December 1896, 3 o'clock".

SOURCE. Two Archive.org scans exist. `lightvisibleinvi00thomrich` beats
`…uoft` on every measure — 0.40% vs 0.72% odd-character OCR rate, larger
pages, 170 vs 126 marked illustrations — and is the source for both the
text (its _djvu.txt, kept as source.txt) and the plates. See FIGURES.md
for the plate recovery, which is a study in itself.

THIS IS THE FIRST OCR SOURCE IN THE PROJECT. Everything else has come
from a proofread Gutenberg or Standard Ebooks text. Raw OCR needs four
classes of repair that a proofread source never does:

  1. RUNNING HEADS. Every page carries one, and they land mid-sentence in
     the text stream: "2 LIGHT LECT.", "160 THE INVISIBLE SPECTRUM iv",
     "APP. ELECTROMAGNETIC THEORY 231". 130-odd of them. Unstripped they
     would read as sentence fragments dropped into the prose.
  2. END-OF-LINE HYPHENATION. The scan preserves the printed line breaks,
     so "per- haps" and "Inver- sion" are two tokens. Rejoining them is
     safe ONLY when the fragment before the hyphen is lower-case and the
     line actually ended there; real compounds ("light-waves") must not
     be touched.
  3. SIGNATURE MARKS AND PAGE NUMBERS on their own lines — a stray "B",
     "12", "L 2".
  4. CHARACTER-LEVEL MISREADS. Collected in SOURCE_FIXES below. The
     dangerous ones are numerals: "5^ seconds" is 5-1/2 seconds and
     "i6,666f hours" is 16,666-2/3 hours. A misread number passes every
     mechanical check we have — see fleming/ — so they are corrected here
     at the source rather than left for the translator to trip over.

FIGURES. The OCR keeps every "FIG. n." caption line at the point where the
plate sat, so those lines become the [Figure n] markers. A marker is
emitted ONLY for a figure we actually recovered a plate for; the 21
figures with no plate (see plate_inventory.json) get no marker, and the
translation must describe rather than cross-reference them.

Dropped: the scan's front matter, the contents, the index, the library
stamps' OCR debris.

Ratio note for verify: English -> English modernization of spoken lecture
prose, as the other five. Run verify.py with --min-ratio 0.85
--max-ratio 1.3.
"""

import difflib
import json
import re
from pathlib import Path

from appendix_fixes import APPENDIX_FIXES

import sys
sys.path.insert(0, str(Path(__file__).parent))

BOOK = Path(__file__).parent
TARGET = 2800
MAX = 3500

SECTION = re.compile(r"^\s*(LECTURE\s+[IVX]+|APPENDIX\s+TO\s+LECTURE\s+[IVX]+)\s*$")

TITLES = [
    ("LECTURE I", "Lecture One: Lights and Shadows"),
    ("APPENDIX TO LECTURE I", "Appendix to Lecture One: The General Method of Geometrical Optics"),
    ("LECTURE II", "Lecture Two: The Visible Spectrum and the Eye"),
    ("APPENDIX TO LECTURE II", "Appendix to Lecture Two: Anomalous Refraction and Dispersion"),
    ("LECTURE III", "Lecture Three: The Polarisation of Light"),
    ("APPENDIX TO LECTURE III", "Appendix to Lecture Three: The Elastic-Solid Theory of Light"),
    ("LECTURE IV", "Lecture Four: The Invisible Spectrum — the Ultra-Violet Part"),
    ("APPENDIX TO LECTURE IV", "Appendix to Lecture Four: Table of Wave-Lengths and Frequencies"),
    ("LECTURE V", "Lecture Five: The Invisible Spectrum — the Infra-Red Part"),
    ("APPENDIX TO LECTURE V", "Appendix to Lecture Five: The Electromagnetic Theory of Light"),
    ("LECTURE VI", "Lecture Six: Röntgen Light"),
    ("APPENDIX TO LECTURE VI", "Appendix to Lecture Six: Other Kinds of Invisible Light"),
]

# Character-level OCR repairs. Each entry must appear at least once or the
# script stops: a fix that has silently stopped matching is worse than no
# fix, because it looks like the text was checked when it was not.
SOURCE_FIXES = [
    # The two numerals matter most. Thompson's opening image is that light
    # covers a million miles while you count to ten — "just over 5½
    # seconds" — and that an express train would need 16,666⅔ hours to do
    # the same. Both fractions were scanned as junk, and a wrong number
    # passes every mechanical check we have.
    ("5^  seconds", "5½ seconds"),
    ("i6,666f  hours", "16,666⅔ hours"),
    (".ripples", "ripples"),
    # The umlaut defeats the scanner twice in the sixth lecture. 152 of the
    # 155 occurrences come through clean; these do not.
    ("Rb'ntgen", "Röntgen"),
    ("Rdntgen", "Röntgen"),
    # single-character corruptions, unambiguous in context
    ("wa^ve-front", "wave-front"),
    ("this^phere", "this sphere"),
    ("primary  r^d", "primary  red"),
    ("b^.id  and  pulley", "band  and  pulley"),
    ("It  must  r~^essarily", "It  must  necessarily"),
    ("Profes^r  E.  Wiedemann", "Professor  E.  Wiedemann"),
    ("to  ^mit  not  only", "to  emit  not  only"),
    ('"^Reserving  for', '"Reserving  for'),
    ("ur^  yl  nitrate", "uranyl  nitrate"),
    ("BM  =  ^.AM,", "BM  =  h.AM,"),
    ("the  curvature  F^  imprinted", "the  curvature  F₁  imprinted"),
    ("curvature  F^  due", "curvature  F₂  due"),
    ("plates,  qi  and  q^", "plates,  q₁  and  q₂"),
    ("bits  marked  b  and  ^,", "bits  marked  b  and  c,"),
    # THE FECHNER FOOTNOTE. Its raised decimal points vanish outright
    # rather than turning into another character, so the natural logarithm
    # of 16 reads "277" where it should read 2.77 — a number 100 times too
    # large that passes every mechanical check there is. The neighbouring
    # value, ln 100 = 4.6, survived with its point and pins the pattern.
    ("logarithm  of  16  is  277", "logarithm  of  16  is  2.77"),
    ("tion 277  times  as  great.", "tion 2.77  times  as  great."),
    ("is  1 6  times  as  bright", "is  16  times  as  bright"),
    # The scanner reads the numeral 1 as a capital I wherever it stands
    # before a unit. Only where a unit follows, so the pronoun is safe.
    ("as  bright  as  I  candle", "as  bright  as  1  candle"),
    ("that  of  I  candle.", "that  of  1  candle."),
    ("light  be  I  metre", "light  be  1  metre"),
    ("read  I  at  I  metre", "read  1  at  1  metre"),
    ("would  travel  I \nfoot", "would  travel  1 \nfoot"),
    ("fell  on  i  square", "fell  on  1  square"),
    ("in  the  ratio  of  I  to  h.", "in  the  ratio  of  1  to  h."),
    ("in  the  ratio  of  i  to  h,", "in  the  ratio  of  1  to  h,"),
    ("Figs.  1 3  and  1 4 \n", "Figs.  13  and  14\n"),
    ("Now  AM  =  £/,  and  BM  =  V.", "Now  AM  =  U,  and  BM  =  V."),
    ("having  velocity-constant  //,  and  so  curved",
     "having  velocity-constant  h,  and  so  curved"),
    # Fig. 157 is set INTO the text like Fig. 107, so the marks drawn inside
    # the diagram land in the middle of the sentence running past it.
    ("will  generate  a  wave, \n/-^^  s  which,", "will  generate  a  wave, \nwhich,"),
    ("\\J  or  even  higher  than,", "or  even  higher  than,"),
    (",£16,500", "£16,500"),
    ('^"16,280', "£16,280"),
    # "Fig. 121b" — the italic b of a lettered sub-figure, scanned as a
    # caret. It is NOT a misprint for 122: the plate shows Fig. 121 as one
    # block lettered a and b (the ball oscillator and the cylinder), with
    # Fig. 122, the electroscope detector, beside it. Two sentences later
    # the text says "Fig. 122 depicts one of the simplest ways of detecting
    # such electric waves", which is the electroscope and confirms it.
    ("The  other  form,  Fig.  121^,", "The  other  form,  Fig.  121b,"),
    ("oscillator,  like  Fig.  121^:,", "oscillator,  like  Fig.  121b,"),
    ("the  second  q^  being", "the  second  q₂  being"),
    # The scanner's own accession number, stamped on the title page. STRAY
    # stops at three digits on purpose — appendix four's table is full of
    # four- and five-digit wave-lengths that are real data.
    ("\n39631 \n", "\n"),
    # A stacked fraction defeats both scans ("awcou", "^lowmm"). Read off
    # the page image (printed p. 21): one two-hundred-thousandth of an inch.
    ("finer  than \n\nawcou  of  an  incn- \n",
     "finer  than  1/200000  of  an  inch. \n"),
    # STACKED FRACTIONS AND THE MID-DOT DECIMAL. Every one of these is a
    # MEASURED VALUE, and every one of them passes the word-count, the
    # figure parity and must_contain alike — the fleming lesson. Each was
    # read off the page image and checked against the physics where the
    # physics constrains it: red waves are 27 millionths of an inch, so the
    # first-order ring stands at a quarter of that, 6-3/4.
    ("7^  inches", "7½ inches"),
    ("about  ^9^00  of  an  inch", "about  1/39000  of  an  inch"),
    ("2§  inches", "2⅞ inches"),
    ("5!  millionths", "5½ millionths"),
    # "i6|" must be repaired BEFORE "6|", or the shorter rule fires inside
    # the longer string and 16-1/2 silently becomes "i6-3/4".
    ("i6|  millionths", "16½ millionths"),
    ("6|  millionths", "6¾ millionths"),

    ("5^  millionths", "5½ millionths"),
    ("8J  by  5  inches", "8¼ by 5 inches"),
    ("9!  inches", "9¾ inches"),
    # Two decimal points that vanished outright rather than turning into
    # another character: the velocity-constant of water (0.75, printed
    # between 0.65 for crown glass and 0.61 for flint, so the value is
    # pinned by its neighbours) and the upper refractive index of flint
    # glass, which the same sentence brackets with 1.5 and 2.6.
    ("water  is  about  075", "water  is  about  0.75"),
    ("flint  glass  from  o-6i \n", "flint  glass  from  0.61\n"),
    ("between  1-5  and  17,", "between  1.5  and  1.7,"),
    # The same 1-1/2 glyph three times in the Rontgen and Hertz lectures,
    # scanned two different ways. Confirmed on the page image at printed
    # p. 224 ("after about 1-1/2 or 2 complete oscillations").
    ("about  i|-  or  2", "about  1½  or  2"),
    ("about  i|-  times", "about  1½  times"),
    ("about  i^  periods", "about  1½  periods"),
    # Five more stacked fractions, buried in ordinary prose rather than in a
    # formula, and every one of them a measured quantity. Read off the page
    # images at printed pp. 137, 248, 252, 262 and 279.
    ("mica  ^hr  inch", "mica  1/800  inch"),
    ("consists  of  but \ni$  ripples", "consists  of  but\n1½  ripples"),
    # The Weber-Kohlrausch ratio of the units — the number that told Maxwell
    # light was an electromagnetic wave. 3.19 x 10^10 cm/s.
    ("to  be  3'i9x  io10 \n", "to  be  3.19 x 10¹⁰\n"),
    ("to  about  —  1 80° \n", "to  about  −180°\n"),
    ("Die  Lehre  von  der  Elektricitdt", "Die  Lehre  von  der  Elektricität"),
    ("8  inches  down  to \ni  inch", "8  inches  down  to\n1  inch"),
    ("emits  waves  about  J  inch  long", "emits  waves  about  ½  inch  long"),
    ("Royal  Institution,  1 7th  May", "Royal  Institution,  17th  May"),
    # Two figure numbers read as words: "Fig. no" is Fig. 110, the
    # radiometer, and "Fig. in" is Fig. 111, the differential thermometer.
    # A cross-reference that points nowhere is the same defect as one that
    # points at the wrong plate.
    ("the  radiometer  (Fig.  no).", "the  radiometer  (Fig. 110)."),
    ("radiometers  (Fig.  no,  p.  199).", "radiometers  (Fig. 110,  p. 199)."),
    ("thermometer  (Fig.  in), \n", "thermometer  (Fig. 111),\n"),
    # Lecture Four's transparency limits. All three are cut-off wave-lengths
    # for real materials and all three lose their point or their digit.
    ("15  millionths  to  n  millionths", "15  millionths  to  11  millionths"),
    ("wave-length  of  13 '3 \n", "wave-length  of  13.3\n"),
    ("down  to  about  8'i  millionths", "down  to  about  8.1  millionths"),
    # The build-it-yourself polariscope of Lecture Three. Every dimension
    # is a workshop measurement and every fraction in them is lost.
    ("and  at  if  inch  from  its", "and  at  1⅝  inch  from  its"),
    ("by \ni  inch  broad,", "by\n1  inch  broad,"),
    ("each  about  ij  inch  long  and  f  inch  wide",
     "each  about  1½  inch  long  and  ⅝  inch  wide"),
    ("about \nTTRRT  inch.", "about  1/1000\ninch."),
    ("the  film  is  5  J  millionths", "the  film  is  5½  millionths"),
    ("(p.  1 1 9),", "(p. 119),"),
    # "Fig. 118" broken across the page break reads as a caption line for
    # Fig. 1 — so the ripple-tank photograph of Lecture One was emitted
    # into the middle of the Hertz-wave discussion in Lecture Five, and the
    # cross-reference itself was destroyed. Mend the number before the
    # caption pass ever sees it.
    ("the  lower  curve  in \nFig.  1 1 8.", "the  lower  curve  in\nFig. 118."),
    ("above  (Fig.  1 14, \n", "above  (Fig. 114,\n"),
    ("1 1  millionths", "11  millionths"),
    ("about  6-oooQ  of  an  inch", "about  1/60000  of  an  inch"),
    # Lecture One's refraction argument turns on two fractions: light goes
    # two-thirds as fast in glass, so the virtual focus is one and a half
    # times as far away. Both glyphs are lost; both are pinned by the
    # sentences around them.
    ("a  point  i  J  times  as  far", "a  point  1½  times  as  far"),
    ("MA  being  drawn  ij  times", "MA  being  drawn  1½  times"),
    ("(if  MB  =  §  MA)", "(if  MB  =  ⅔  MA)"),
    ("a  refractivity  of  ij)", "a  refractivity  of  1½)"),
    ("conscious  of  th e  impressions", "conscious  of  the  impressions"),
    # This one was dropped by the scanner altogether, leaving "less than
    # about inch". Printed p. 20: one two-hundred-thousandth, the same
    # figure as the polishing powder two sentences later.
    ("less  than  about \ninch)", "less  than  about  1/200000\ninch)"),
    ("haps ^J-g-  part", "haps  1/300  part"),
    # The rest of Lecture Six's vacuum series, read off printed p. 251:
    # 1/5, 1/20 (19/20 removed), 1/40 or 1/50, 1/500, 1/10000, 1/50000.
    ("only  about  -J-  of  the  original", "only  about  1/5  of  the  original"),
    ("exhausted  to  about  -fa  part", "exhausted  to  about  1/20  part"),
    ("that  is  to  say,  J-jj-  of  the  air", "that  is  to  say,  19/20  of  the  air"),
    ("carried  to  about  -g-J-Q,", "carried  to  about  1/500,"),
    ("about  -^Q^-Q-Q  part", "about  1/50000  part"),
    ("foil  YO^O  inc^", "foil  1/10000  inch"),
    ("T^nth  sec.", "1/100th  sec."),
    ("residual  air  is  reduced  to  ^  or  -g1^ \npart;",
     "residual  air  is  reduced  to  1/40  or  1/50\npart;"),
    ("sixth  tube  to  about  T -Q^-Q-Q  :",
     "sixth  tube  to  about  1/10000  :"),
    # Fig. 107 is set INTO the text, so the scanner reads the labels printed
    # inside the diagram as if they were words of the sentence running past
    # it. Cut the labels out and the sentence closes up.
    ("\\x  /WHITE\\  /B'LUE  ^   overlap  at  the  centre  they \nPM  L- rin^T  I  give  us  white.",
     "overlap  at  the  centre  they  give  us  white."),
    # 30,000,000,000 / 100,000,000 = 300, and the sentence itself says the
    # answer is about ten feet.
    ('we  get  ft?  the  •wav?-lQngtb..  3^"  centi- \nmetres',
     "we  get  the  wave-length  300  centi-\nmetres"),
]

# Running heads, matched against the book's actual head titles rather than
# by shape. Shape alone is not enough: page numbers come through the scan
# as "i8" and "l6l", the head may lead with "LECT." or "APP.", and it may
# carry no number at all. A line is a running head if, once the furniture
# is stripped off, nothing but one of these titles remains.
HEAD_TITLES = [
    "LIGHT", "LIGHTS AND SHADOWS", "VISIBLE SPECTRUM AND THE EYE",
    "THE VISIBLE SPECTRUM AND THE EYE", "POLARISATION OF LIGHT",
    "THE INVISIBLE SPECTRUM", "RONTGEN LIGHT", "INTRODUCTION", "CONTENTS",
    "REFLEXION FORMULA", "REFRACTION AND DISPERSION",
    "ELASTIC-SOLID THEORY OF LIGHT", "ELASTIC-SOLID THEORY",
    "ELECTROMAGNETIC THEORY", "ELECTROMAGNETIC THEORY OF LIGHT",
    "OTHER KINDS OF INVISIBLE LIGHT", "TABLE OF WAVE-LENGTHS",
    "GEOMETRICAL OPTICS", "THE GENERAL METHOD OF GEOMETRICAL OPTICS",
    "RECKONING CURVATURE", "METHOD OF RECKONING CURVATURE",
    "REFRACTION FORMULA", "REFLEXION FORMULA",
    "LENS FORMULAE", "WAVE MODEL", "A HERTZ-WAVE MODEL", "HERTZ-WAVE MODEL", "VISIBLE SPECTRUM", "THIN FILMS",
    "COMPLEMENTARY TINTS", "SPECTRUM",
]
FURNITURE = re.compile(
    # the LECT/APP variants must keep their full stop, or "LIG" of "LIGHT"
    # matches the pattern and the head stops being recognisable
    r"^[\s.,|]*(?:[LI][EI]C?[TG]\.|AP[PR]\.?)?[\s.,]*(?:[ivxlcIVXLCnm\dioOlIsS]+(?=[\s.,|]|$)[\s.,]*)*"
    r"(?:[LI][EI]C?[TG]\.|AP[PR]\.?)?[\s.,]*")


def is_running_head(line):
    s = re.sub(r"\s+", " ", line).strip()
    if not s or len(s) > 60:
        return False
    # The scan sprays junk into the heads ("2*7" for 297, "AlS^SEEsBYE"
    # for "AND THE EYE"), so no whitelist of characters survives contact.
    # What a running head never has is a real lower-case word: reject on
    # that instead, and let the title match below do the real work.
    if re.search(r"\b[a-z]{3,}\b", s):
        return False
    # A page break sometimes sets the head on three lines — "68", "LIGHT",
    # "LECT." — and the last of those strips to nothing. It is still a head.
    # The test must name the LECT/APP token explicitly: a bare number also
    # strips to nothing, and appendix four's wave-length table is bare
    # numbers from top to bottom.
    if re.fullmatch(r"[\s.,|]*(?:[LI][EI]C?[TG]\.|AP[PR]\.?)[\s.,|ivxlcIVXLC\d]*", s):
        return True
    s = FURNITURE.sub("", s)
    s = re.sub(r"[\s.,|]*(?:[LI][EI]C?[TG]\.|AP[PR]\.?)?[\s.,]*(?:[ivxlcIVXLCnm\dioOlIsS]+(?=[\s.,|]|$)[\s.,|]*)*$",
               "", s).strip().upper()
    if not s:
        return False
    if s in HEAD_TITLES:
        return True
    # The scan mangles the heads themselves — LECT becomes IECT, RONTGEN
    # becomes RCNTGEN, and "AND THE EYE" once came through as
    # "AlS^SEEsBYE" — so compare the HEAD of the line, word for word,
    # against each title rather than demanding the whole line match.
    # Match a PREFIX of the line against the titles and allow a short junk
    # tail, because the page number is often glued to the head as unreadable
    # characters. The tail must stay short: "THE INVISIBLE SPECTRUM
    # (INFRA-RED PART)" is a real lecture heading, not a running head, and
    # its sixteen-character tail is what tells the two apart.
    words = s.split()
    for k in range(len(words), 0, -1):
        if len(" ".join(words[k:])) > 14:
            continue
        head = " ".join(words[:k])
        if any(head == t or difflib.SequenceMatcher(None, head, t).ratio() > 0.82
               for t in HEAD_TITLES):
            return True
    return False


FIGCAP = re.compile(r"^\s*F\s*[IilL1]\s*[GC]\s*[.,\-]?\s*(\d{1,3})\s*[.,\-]?\s*(.*)$", re.I)
# Where the printed caption never made it into the OCR at all — it was set
# inside the engraving and read as part of the picture — the plate is
# placed after the first paragraph that refers to it. This is a normal
# editorial placement and it is how the page reads anyway.
FIGREF = re.compile(r"\bF[ilI1]G[.,]?\s*(\d{1,3})", re.I)
STRAY = re.compile(r"^\s*(?:[A-Z]|[A-Z]\s*\d|\d{1,3}|[ivxlc]{1,5})\s*$")
STAMP = re.compile(r"REESE|LIBRARY OF THE|UNIVERSITY OF|CALIFORNIA", re.I)


def plates():
    """Figure ids we actually have a plate for, as {number: id}. A compound
    plate answers for every number printed on it."""
    d = BOOK.parent / "site" / "images" / "thompson"
    out = {}
    for p in sorted(d.glob("fig*.jpg")):
        fid = p.stem[3:]
        for part in fid.split("-"):
            if part.isdigit():
                out[int(part)] = fid
    return out


def dehyphenate(text):
    """Rejoin words the printer broke across a line. Only when the tail
    begins lower-case: "per-\\nhaps" joins, "light-\\nWaves" does not, and
    a hyphen with text after it on the same line is a real compound."""
    return re.sub(r"([a-z])-\s*\n\s*([a-z])", r"\1\2", text)


def rejoin_over_heads(text):
    """A word broken across a PAGE break has the running head sitting
    between its halves, so the first dehyphenation pass — which runs before
    the heads are stripped — cannot see it. Run again once they are gone,
    now allowing the blank line the removed head left behind. Ten words in
    this book are broken this way; every one of them joins without a
    hyphen, "semicircle" included (that is how Thompson spells it in the
    two places the word survives intact)."""
    return re.sub(r"([a-z]{2,})-[ \t]*\n\s*\n[ \t]*([a-z]{2,})", r"\1\2", text)


# The printer's raised decimal point comes through the scanner three ways:
# as an asterisk, as a hyphen, and as nothing at all. The hyphen case has to
# be told apart from a genuine page range, and the test that separates them
# is digit counts: "0-625" and "45-4" are numbers, "69-73" and "113-117" are
# ranges, and no decimal in this book has two digits on the left AND two on
# the right.
MIDDOT = re.compile(r"(?<=\d)\*(?=\d)")
HYPHDOT = re.compile(r"\b(\d)-(\d+)\b|\b(\d{2,})-(\d)\b")
# a pound sign, every time
POUNDS = re.compile(r"\^(?=\d{1,3},\d{3})")


def fix_decimals(text):
    text = MIDDOT.sub(".", text)
    text = HYPHDOT.sub(lambda m: (f"{m[1]}.{m[2]}" if m[1] else f"{m[3]}.{m[4]}"), text)
    return POUNDS.sub("£", text)


def apply_fixes(text):
    """Applied ONCE to the whole scan, before anything is split off. Each
    entry must still match, or the script stops: a fix that has silently
    stopped matching is worse than no fix, because the text then looks
    checked when it is not."""
    for a, b in SOURCE_FIXES:
        if a not in text:
            raise SystemExit(f"SOURCE_FIXES no longer matches: {a!r}")
        text = text.replace(a, b)
    # The printer sets a raised dot for the decimal point and the scanner
    # reads it as an asterisk. Only between two digits, so the footnote
    # asterisks and the multiplication signs are left alone.
    return fix_decimals(text)


def clean_body(text):
    text = dehyphenate(text)
    keep = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        if is_running_head(line) or STAMP.search(line):
            keep.append("")
            continue
        if STRAY.match(line):
            keep.append("")
            continue
        keep.append(line)
    return rejoin_over_heads("\n".join(keep))


FOOTNOTE = re.compile(r"^([1-9])\s+(?=[A-Z\"“(])(.+)$", re.S)
# A footnote marker is a superscript digit, and the scan sets it as an
# ordinary digit welded to the word it followed: "wave-length.1", "then2".
# Strip it only after two lower-case letters, so the book's own symbols
# survive — D1 and D2 are spectrum lines, b1 is a line, L2 is a lens.
MARKER = re.compile(r"(?<=[a-z]{2})[1-9](?=\s)|(?<=[a-z][.,;:\"”)])[1-9](?=\s)"
                    r"|(?<=[a-z]{3})\^(?=[\s.,;:])")


def lift_footnotes(paras):
    """Thompson's 78 footnotes are set at the foot of the page, so the scan
    drops each one into the text stream at whatever point the page happened
    to break — usually straight through the middle of a sentence. Lift each
    note out, mend the paragraph it interrupted, and set it down again as
    its own "Footnote:" paragraph immediately after. The notes are the
    author's own and belong in the book; what does not belong is a bare "1"
    starting a paragraph in the middle of an argument."""
    out, i = [], 0
    while i < len(paras):
        m = FOOTNOTE.match(paras[i])
        if not m or not out or out[-1].startswith("[Figure"):
            out.append(paras[i]); i += 1
            continue
        notes = []
        while i < len(paras):
            m = FOOTNOTE.match(paras[i])
            if not m:
                break
            notes.append(m.group(2).strip()); i += 1
        # the note split a sentence if what came before does not end one and
        # what comes after resumes in lower case
        if (i < len(paras) and re.match(r"[a-z]", paras[i])
                and not re.search(r"[.!?:;][\'\"”]?$", out[-1])):
            out[-1] = out[-1].rstrip() + " " + paras[i]
            i += 1
        out.extend("Footnote: " + n for n in notes)
    return out


def mend_pages(paras):
    """The scan sets a running head at the top of every page, so removing it
    leaves a blank line — and a blank line is a paragraph break. Roughly 290
    of Thompson's paragraphs are therefore cut in half at the point where
    the page turned. A new paragraph never begins in lower case, so a
    paragraph that does not end a sentence followed by one that begins in
    lower case is one paragraph, and is rejoined here.

    Plates and footnotes may sit between the halves — the plate was set at
    the top of the next page, the note at the foot of the last one. Step
    over them and let them follow the mended paragraph rather than splitting
    it. Repeat until nothing more joins, because one mend can expose
    another.

    The lower-case test alone leaves the halves that resume on a proper noun
    ("...the precision-photometer of" / "Brodhun and Lummer, which..."). For
    those, look at the word the first half ENDS on: no English sentence
    stops on "of"."""
    DANGLING = re.compile(
        r"(?:\b(?:of|the|a|an|and|or|but|to|in|on|at|by|for|with|from|as|"
        r"that|which|is|are|was|were|be|been|its|his|their|this|these|"
        r"than|when|if|into|upon|about|through|over|under)\s*|[,—–])$", re.I)
    for _ in range(4):
        out, i, moved = [], 0, 0
        while i < len(paras):
            out.append(paras[i]); i += 1
            cur = out[-1]
            if (not cur or cur.startswith(("[Figure", "Footnote:", "    "))
                    or re.search(r"""[.!?:;'\"”)\]]$""", cur)):
                continue
            j, skipped = i, []
            while j < len(paras) and paras[j].startswith(("[Figure", "Footnote:")):
                skipped.append(paras[j]); j += 1
            if j >= len(paras):
                continue
            nxt = paras[j]
            if not (re.match(r"[a-z(]", nxt) or DANGLING.search(cur)):
                continue
            if nxt.startswith("    "):
                continue
            out[-1] = cur + " " + nxt
            out.extend(skipped)
            moved += 1
            i = j + 1
        mend_pages.count += moved
        paras = out
        if not moved:
            break
    return paras


mend_pages.count = 0


def normalise(block, have):
    """One paragraph per line; FIG. n. caption lines become [Figure n]
    markers, but only for figures we hold a plate for."""
    paras, cur = [], []
    for raw in block.split("\n"):
        line = raw.strip()
        m = FIGCAP.match(line)
        if m:
            n = int(m.group(1)); tail = m.group(2).strip()
            if cur:
                paras.append(" ".join(cur)); cur = []
            # A SENTENCE may begin "Fig. 115 gives a front view of the
            # oscillator" — and a caption line and a sentence opening look
            # identical to a regex. The tail tells them apart: a caption
            # continues in upper case or not at all, a sentence continues in
            # lower case. Keep the reference in the prose when it is prose.
            if tail and tail[:1].islower():
                if n in have:
                    paras.append(f"[Figure {have[n]}]")
                cur.append(f"Fig. {n} {tail}")
                continue
            if n in have:
                paras.append(f"[Figure {have[n]}]")
            if tail:
                cur.append(tail)
            continue
        if line:
            cur.append(line)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))

    # A caption line can fall between the halves of a word broken over the
    # page break — "The sender con-" / "FIG. 124." / "sists of an
    # oscillator". The text pass cannot rejoin those, because the caption
    # between them is real content. Rejoin the word here and let the marker
    # follow the mended paragraph.
    i = 0
    while i + 2 < len(paras):
        if (re.search(r"[a-z]{2,}-$", paras[i])
                and paras[i + 1].startswith("[Figure")
                and re.match(r"[a-z]{2,}", paras[i + 2])):
            joined = paras[i][:-1] + paras[i + 2]
            paras[i:i + 3] = [joined, paras[i + 1]]
        i += 1

    out, seen = [], set()
    for p in paras:
        if p.startswith("[Figure"):
            if p in seen:            # the same plate captioned twice
                continue
            seen.add(p); out.append(p)
            continue
        p = re.sub(r"\s+", " ", p).strip()
        p = p.replace("Rontgen", "Röntgen").replace("RONTGEN", "RÖNTGEN")
        p = MARKER.sub("", p)
        # an orphaned marker caret — but not the one standing in for the
        # fraction one-half in the sagitta footnote, which repair_formulae
        # replaces by name
        p = re.sub(r"(?<!factor)\s\^(?=\s)", "", p)
        if len(p.split()) >= 3:
            out.append(p)
    return mend_pages(lift_footnotes(out))


# ---------------------------------------------------------------------------
# APPENDIX TO LECTURE IV is nothing but a table, and the OCR destroys a table
# completely: the column structure is gone and the digits are unreliable
# ("- B -04 09-865", "1 2 '2O6"). It is therefore TRANSCRIBED BY HAND from the
# page images -- printed pages 190-191, scan leaves n213-n214 -- and checked,
# cell by cell, against the two things the table asserts about itself:
# millionths of an inch = micro-centimetres / 2.54, and frequency in billions
# per second = 30000 / micro-centimetres.
#
# Every one of the 55 rows agrees on both counts to within a rounding step
# (the inch column is off by at most 0.05, the frequency by at most 0.15%)
# EXCEPT the A line, printed "29.28" where 75.94 / 2.54 = 29.90. The 1897
# typesetting is wrong there; the frequency cell (395.2, which implies 75.94)
# confirms which of the two is the misprint. Corrected here, and flagged.
#
# The second Archive.org copy (...uoft) settled four cells the ...rich copy
# has an ink blot over: X1 is 84.97, Z is 82.264, Y is 89.904 -- and the A
# line really is printed 29.28 in both, which is a reminder that two copies
# of one setting can confirm what was printed, never that it was right.
WAVE_TABLE = """    Line               Element   Micro-cm   Millionths   Frequency
                                            of inch
    ------------------------------------------------------------
    Rubens and Nichols'
      longest waves       —         2400         944       12.5
    Langley's
      longest waves       —         1500         592         20
    Paschen's
      longest waves       —          945         370       31.7
    Ψ₂, Ψ₁               ...         270      106.24        111
    Φ₂                   ...         124       48.73        242
    Φ₁                   ...         120       47.25        250
    Y                    ...      89.904       35.36      333.7
                         ...      89.865       35.35      334.0
    X₄                   ...      88.061       34.64      340.8
    X₃                   ...      86.614        34.1      346.2
    X₂                   ...      85.418       33.63      351.3
    X₁                   ...       84.97       33.44      353.3
    Z                    ...      82.264       32.34      364.5
    A                     O        75.94       29.90      395.2
    B                     O       68.674       27.03      436.5
    C                     H       65.630       25.83      457.2
    D₁                   N₂       58.961       23.21      508.8
    D₂                   N₂       58.902       23.18      509.1
    D₃                   He       58.760       23.13      510.5
    E₁                   Fe       52.705       20.78      569.2
                         Ca       52.704       20.78      569.2
    E₂                   Fe       52.697       20.74      569.3
    b₁                   Mg       51.838       20.40      578.9
    b₂                   Mg       51.729       20.36      580.0
    b₃                   Fe       51.692      20.351      580.4
                         Fe       51.691      20.350      580.4
    b₄                   Fe       51.677      20.306      580.5
                         Mg       51.675      20.305      580.5
    F                     H       48.615       19.14      617.1
    G                    Fe       43.081       16.96      696.3
                         Ca       43.079       16.95      696.4
    h                     H       41.018       16.17      731.3
    H                    Ca       39.686       15.63      756.0
    K                    Ca       39.338       15.48      762.7
    L                    Fe       38.206       15.04      785.1
    M                    Fe       37.278      14.676      804.6
                         Fe       37.271      14.673      804.9
    N                    Fe       35.813       14.09      837.7
    O                    Fe       34.411       13.55      871.8
    P                    Fe       33.613       13.23      892.6
    Q                    Fe       32.869       12.94      912.6
    R                    Ca       31.814       12.52      942.9
                         Ca       31.794       12.51      943.5
    r                    Fe       31.446       12.38      954.1
    S₁                   Fe       31.008      12.207      967.4
    S₂                   Fe       31.004      12.206      967.6
                         Fe       31.001      12.205      967.7
    s                    Fe       30.477       11.99      984.5
    T                    Fe       30.212      11.894      993.0
                         Fe       30.207      11.892      993.3
    t                    Fe       29.945       11.79     1002.0
    U                    Fe       29.480       11.60     1017.6
    Miller's limit
      (photographic)      —         20.2        7.95     1485.1
    Stokes' limit
      (fluorescent)       —         18.5        7.28     1621.6
    Schumann's highest
      frequency           —           10        3.93       3000"""


def repair_formulae(paras):
    """Splice the transcribed formulas back into the appendices. Each fix is
    applied to the joined text so that a replacement may introduce paragraph
    breaks, which is what turns a run-together sentence into prose, display,
    prose again.

    A fix belongs to exactly one appendix, so a miss here is not an error;
    check_formulae() below verifies at the end of the run that every one of
    them landed somewhere."""
    text = "\n\n".join(paras)
    for i, (a, b) in enumerate(APPENDIX_FIXES):
        if a in text:
            text = text.replace(a, b, 1)
            repair_formulae.hit.add(i)
    return text.split("\n\n")


repair_formulae.hit = set()


def check_formulae():
    missed = [a for i, (a, _) in enumerate(APPENDIX_FIXES)
              if i not in repair_formulae.hit]
    if missed:
        raise SystemExit("APPENDIX_FIXES no longer match:\n  "
                         + "\n  ".join(repr(a[:70]) for a in missed))



# A plate whose number is never cited in the prose falls to the numerical-
# order fallback, which puts it after the nearest lower plate — and that is
# wrong when the nearest lower plate is in a different section. Fig. 38 is
# the sagitta construction of Appendix I, but Fig. 37 is the last plate of
# Lecture One, so the fallback strands it at the end of the lecture. Pin it
# to the sentence that describes it instead.
FIGURE_PINS = {
    # Fig. 38 is the sagitta construction of Appendix I, but Fig. 37 is the
    # last plate of Lecture One, so the numerical fallback strands it at
    # the end of the lecture. Pin it to the sentence that describes it.
    "38": "Consider a circular arc AP",
    # Fig. 1 — the lecturer at the ripple-tank, dipping a finger into the
    # water while the lamp underneath throws the circles onto the sloping
    # screen — lost its caption line entirely in the scan, and the only
    # "Fig. 1" left in the text is the first half of a broken "Fig. 114".
    "1": "shallow tank l of water",
}


def place_unused(sections, have):
    """Every plate must appear somewhere. Any not carried in by its own
    caption line is inserted after the first paragraph that mentions it."""
    placed = {fid for sec in sections for p in sec
              if p.startswith("[Figure ") for fid in [p[8:-1]]}
    want = [(n, fid) for n, fid in sorted(have.items()) if fid not in placed]
    done = set()
    for n, fid in want:
        if fid in done or fid in placed:
            continue
        for sec in sections:
            for i, p in enumerate(sec):
                if p.startswith("[Figure"):
                    continue
                if any(int(x) == n for x in FIGREF.findall(p)):
                    sec.insert(i + 1, f"[Figure {fid}]")
                    done.add(fid)
                    break
            if fid in done:
                break
    # Last resort: a dozen figures are never named anywhere the OCR can be
    # trusted — neither caption nor reference survived. They are printed in
    # numerical order, so each goes immediately after the nearest lower
    # plate already placed.
    byfid = {}
    for si, sec in enumerate(sections):
        for i, p in enumerate(sec):
            if p.startswith("[Figure "):
                byfid[p[8:-1]] = (si, i)
    for fid, anchor in FIGURE_PINS.items():
        if fid in placed or fid in done:
            continue
        for sec in sections:
            for i, par in enumerate(sec):
                if anchor in par:
                    sec.insert(i + 1, f"[Figure {fid}]")
                    done.add(fid)
                    break
            if fid in done:
                break
    strays = 0
    for n, fid in want:
        if fid in done or fid in placed:
            continue
        prev = [m for m, f in sorted(have.items()) if m < n and f in byfid]
        if not prev:
            continue
        si, i = byfid[have[prev[-1]]]
        sections[si].insert(i + 1, f"[Figure {fid}]")
        done.add(fid); strays += 1
        byfid = {}
        for sj, sec in enumerate(sections):
            for j, p in enumerate(sec):
                if p.startswith("[Figure "):
                    byfid[p[8:-1]] = (sj, j)
    if strays:
        print(f"plates placed by numerical order alone: {strays}")
    return len(done)


def split_body(body):
    paras = body.split("\n\n")
    words = [len(p.split()) for p in paras]
    total = sum(words)
    if total <= MAX:
        return [body]
    nparts = max(2, round(total / TARGET))
    per = total / nparts
    cum = [0]
    for w in words:
        cum.append(cum[-1] + w)
    cuts, lo = [], 1
    for k in range(1, nparts):
        target = k * per
        best, best_d = None, None
        for i in range(lo, len(paras)):
            if paras[i - 1].startswith("[Figure"):
                continue
            d = abs(cum[i] - target)
            if best_d is None or d < best_d:
                best, best_d = i, d
        cuts.append(best)
        lo = best + 1
    edges = [0] + cuts + [len(paras)]
    return ["\n\n".join(paras[a:b]) for a, b in zip(edges, edges[1:])]


def body_words(text):
    return len(re.sub(r"^\[Figure[^\]]*\]$", "", text, flags=re.M).split())


def main():
    raw = apply_fixes((BOOK / "source.txt")
                      .read_text(encoding="utf-8", errors="replace"))
    have = plates()
    print(f"plates on disk cover {len(have)} figure numbers")

    lines = raw.split("\n")
    # the body begins at the SECOND "LECTURE I" (the first is the contents)
    heads = [i for i, l in enumerate(lines) if SECTION.match(l)]
    body_start = next(i for i in heads
                      if re.match(r"^\s*LECTURE\s+I\s*$", lines[i])
                      and i > 200)
    index_at = next(i for i, l in enumerate(lines)
                    if l.strip() == "INDEX" and i > body_start)
    # Thompson calls his preface an INTRODUCTION, and it is the best short
    # statement of what a Christmas lecture is for that the five volumes
    # contain — two things are expected of the lecturer, experiments and
    # a note of modernity.
    pre_at = next(i for i, l in enumerate(lines) if l.strip() == "INTRODUCTION")
    con_at = next(i for i, l in enumerate(lines) if l.strip() == "CONTENTS")
    preface = clean_body("\n".join(lines[pre_at + 1:con_at]))

    body = clean_body("\n".join(lines[body_start:index_at]))
    blines = body.split("\n")
    bh = [i for i, l in enumerate(blines) if SECTION.match(l)]
    if len(bh) != 12:
        raise SystemExit(f"expected 12 body sections, found {len(bh)}")
    bounds = bh + [len(blines)]

    (BOOK / "chapters").mkdir(exist_ok=True)
    front = "\n\n".join(["Front Matter", "Introduction"] + normalise(preface, have))
    (BOOK / "chapters" / "000.txt").write_text(front + "\n")
    manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
                 "words": body_words(front), "split_headings": ["Introduction"]}]

    # build all twelve sections first, so a plate whose caption never made
    # it into the OCR can still be placed from a reference anywhere in the
    # book before anything is split into files
    sections = []
    for k in range(12):
        want, _ = TITLES[k]
        got = re.sub(r"\s+", " ", blines[bounds[k]]).strip()
        if got != want:
            raise SystemExit(f"section {k}: expected {want!r}, found {got!r}")
        chunk = blines[bounds[k] + 1:bounds[k + 1]]
        j = 0
        while j < len(chunk) and (not chunk[j].strip()
                                  or chunk[j].strip().isupper()):
            j += 1
        if k == 7:                       # the wave-length table appendix
            sections.append([WAVE_TABLE])
            continue
        # APPENDIX_FIXES are keyed on their own text, not on a section
        # number, so they can be run over everything; check_formulae() then
        # confirms that each one landed exactly once.
        sections.append(repair_formulae(normalise("\n".join(chunk[j:]), have)))
    added = place_unused(sections, have)
    check_formulae()
    print(f"plates placed from an inline reference: {added}")
    print(f"paragraphs mended across a page break: {mend_pages.count}")

    n = 1
    for k in range(12):
        title = TITLES[k][1]
        parts = split_body("\n\n".join(sections[k]))
        for i, part in enumerate(parts, 1):
            fname = f"{n:03d}.txt"
            (BOOK / "chapters" / fname).write_text(part + "\n")
            manifest.append({"file": fname, "title": title,
                             "part": i, "of": len(parts),
                             "words": body_words(part)})
            n += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    used = set()
    for f in (BOOK / "chapters").glob("*.txt"):
        used |= set(re.findall(r"^\[Figure ([\w-]+)\]$", f.read_text(), re.M))
    disk = {p.stem[3:] for p in (BOOK.parent / "site/images/thompson").glob("fig*.jpg")}
    if disk - used:
        print(f"  WARNING: plates on disk never placed: {sorted(disk - used)}")

    for m in manifest:
        print(f"  {m['file']}  {m['words']:>5}  {m['title'][:52]} ({m['part']}/{m['of']})")
    print(f"{len(manifest)} files, {sum(m['words'] for m in manifest)} words, "
          f"{len(used)} plates placed")


if __name__ == "__main__":
    main()
