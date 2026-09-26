# Restored Editions

Books that need an edition, not a retelling. Moved verbatim from CLAUDE.md §7.

Alex's ruling of 2026-09-17, after A. M. Worthington's A Study of Splashes
screened cleaner than any book the project had modernised (arch 0.00,
calq 25.4, against Jacobs struck at 0.90): "books we just give some TLC
and put into standard books quality, original prose but improved markup
and a nice ebook edition and web edition." They live on their own page,
site/restored.html, built by build_restored.py from env and never from a
hand-kept list.

THE PROSE IS THE AUTHOR'S, UNCHANGED. What a restored edition adds is the
apparatus: a caption and alt text for every plate, proper markup, an
editor's introduction, a real epub. Two shapes:
  COMPANION  a retelling's `--original` page (ORIGINAL_TEXT=yes): the seven
             Royal Institution volumes. Their 653 captions ALREADY EXISTED
             in modern_chapters/, and assemble.caption_map / fill_captions
             lift them onto the source's bare markers. Fill where empty,
             never overwrite: Ball captioned 93 of his 94 plates himself and
             those are his text.
  NATIVE     no retelling at all (EDITION=restored): worthington/, aesop/,
             irish-fairy-tales/, old-indian-legends/, american-indian-stories/,
             calculus-made-easy/. The page says "restored edition"; the epub
             drops "retold" and the `trl` role.

MODERN_CHAPTERS/ IS COMPOSED, NEVER TYPED. prep.py writes chapters/ with
bare markers and modern_chapters/ as the same files with each marker
filled from plates.json (the label the book printed) and captions/*.txt
(what this edition writes, see CAPTIONS.md). Nobody retypes the prose, so
verify.py's word ratio -- the loosest check in the project -- becomes an
EQUALITY TEST that holds at 1.00 by construction.

AND THEREFORE THE RATIO CAN SEE NOTHING THAT PREP GOT WRONG, because both
directories come from the same prep. Aesop's first prep dropped 357 words
of "The Miller, His Son, and Their Ass" (loose text inside Gutenberg's
pg_body_wrapper divs) and verified at 1.00. The only defence is a SECOND
READING THAT SHARES NO CODE WITH THE WALKER (the epictetus rule): aesop/
prep.py now counts the raw HTML's words against what it emitted.

PLATE IDS ARE PINNED AND THE PIN IS AUTHORITATIVE. Captions are keyed by
id; ids were first assigned in document order; so an ORDER_FIX must move a
plate without renumbering it, or every caption after the move describes
its neighbour. Once plates.json exists, an id follows its source plate.
Unnumbered plates get digit-free ids ('aa', 'ab') so assemble.figure_label
cannot print "Figure 12" over a photograph the book calls "Series II, 3".

THE CAPTION PASS IS THE BEST PLATE AUDIT THIS PROJECT HAS. Every batch
agent opened every plate and reported what did not match, and between them
they found: Worthington labels given the whole row of a table ("1 2 T = 0 3
0·002 sec. ..."); a page-reference link stripped out of a label; 21 Aesop
plates one fable too late (the <hr> is the fable boundary, not "has text
been emitted yet"); Aesop's lost Miller text; Fig. 5 a photograph, not a
diagram; the lecture's "photographs" mostly engravings and drawings; the
page-55 order 1, 2a, 3, 2. REPORT, DON'T FIX is the standing instruction,
and every one of these was fixed in prep, not in a caption.

WHEN TWO WITNESSES DISAGREE, GO TO THE PAGE. Irish Fairy Tales' captions
came from an OCR list and were checked against Stephens' own prose, which
caught "Guillen" for Cuillen and a welded "con-tinuous" in the source. But
one printed caption genuinely departs from the sentence it quotes ("all
the worlds"), and only the scanned page image settled it. Worthington's
two out-of-sequence times (0·014, 0·285) were likewise checked on the scan
and are his own misprints, so they stand.

A LONE ASTERISK THAT IS CONTENT IS DELETED BY emph_safe, and nothing
notices (2026-09-20). Russell's Introduction to Mathematical Philosophy
cites Principia by its star numbers ("vol. II. *110") and all fifteen had
become "vol. II.  110"; Hoffmann's card rows ("1, 0, *, *, *, *") had
become bare commas. Each prep now converts them before walking (✱ for
Principia's star, ⁎ for an indifferent card). Grep any new source for a
bare "*" beside a digit or a comma before prepping. The same walker also
dropped verse lines classed "iq" (a hanging opening quote); restore_lib
now takes i\d*q? spans.

EMPHASIS IS ASKED OF THE RENDERER. emph_safe() keeps exactly the spans
assemble.EMPH will render and removes every other asterisk. The first
Worthington page shipped 16 literal asterisks from italic letters glued to
numbers ("Figs. 20*a*").

COMPARE THE TRANSCRIPTION WITH A SCAN, WORD BY WORD, AND WITH A SECOND
COPY WHERE THEY DISAGREE (Zitkala-Ša, 2026-09-17). A word diff of Gutenberg
against the Archive.org OCR, after dropping running heads and line-end
splits, leaves a short list worth reading. It found four kinds of thing,
and they are decided differently:
  - WHOLE MATTER GUTENBERG LEFT OUT: Old Indian Legends' preface (only its
    signature survived, as a garbled heading), all fourteen plates and
    their captions; American Indian Stories' epigraph and Acknowledgments.
    Restored, typed from the page images and checked LETTER FOR LETTER
    against the OCR, which shares no keystrokes with prep.py.
  - GUTENBERG NORMALISING PERIOD SPELLING ("Dumfounded", "hand's-breadth",
    "intrust", "gayly"): reversed in SOURCE_FIXES, but ONLY where two copies
    agree on the printed reading.
  - THE PRINTER'S PLAIN MISPRINTS ("langauge", "warrier", "gilt" for
    guilt), which Gutenberg corrected: left corrected. They are errors,
    not the author's words.
  - TWO STATES OF ONE PRINTING. The BYU copy of American Indian Stories
    prints two sentences and an ending that the BPL copy and Gutenberg do
    not. Neither is "the" 1921 text; the edition follows the two witnesses
    that agree and the introduction says what the other copy prints. One
    scan, taken as the book, would have silently swapped the text.
  AND THE VOTE WAS BLIND TO A DROPPED WORD until 2026-09-20: it compared
  only words the edition HAS and the print lacks, never the reverse, so
  "the law always approaching" (for "the law is always approaching") and
  Russell's later-state omissions of "Mr." and "until very lately" passed
  six books. It now reports short insertions both scans agree on, minus
  running heads, and `--json` writes them for a prep to apply (see
  common-law/prep.py restore_dropped: 58 words in Holmes).
  AND A DIFF CAN LIE ABOUT THE TRANSCRIPTION: its biggest hit, 300 words
  "missing" from Iya, the Camp-Eater, was a page the Archive.org copy
  scanned twice.

A PRINTED CAPTION MAY MISQUOTE ITS OWN SENTENCE. De Cora's plates quote
the story ("A little boy stopped his play among the grasses") where the
story says "a little wild boy ... among the tall grasses". prep places each
plate after the one paragraph containing its caption and asserts it; the
two that depart are in PRINTED_DIFFERS with the prose anchor beside them,
and the caption stands as printed. A frontispiece whose caption says "(See
page 89)" is placed at page 89's paragraph, not at the front.

PLATES CUT FROM A PAGE SCAN BY THEIR OWN EDGES (old-indian-legends/
plate_box): average brightness across a central band, take the LONGEST run
darker than the paper, then the same across the plate's rows. A halftone's
lightest passages stay well under the paper; the gutter shading and a
library's perforated stamp only make short runs. Asserted against a size
band. Note the leaf index: Archive.org's _jp2.zip is one ahead of the
ABBYY page index for this scan, and the first fetch was fourteen text
pages.

MATHEMATICS IS TYPESET, NOT PICTURED (calculus-made-easy/, 2026-09-20).
Gutenberg sets each formula as an image carrying `data-tex`; a restored
edition keeps the LaTeX in chapters/ as \(...\) and \[...\] and both
renderers typeset it (mathml.py: pandoc, cached in build/). assemble.inline
HOLDS formulas aside before emphasis, since LaTeX is full of _ and *. The
page gets plain <math>; the epub needs MORE, all found by building:
  - `se clean` hoists a default MathML xmlns onto <html>, replacing XHTML's,
    so every chapter failed to parse. Emit <m:math> and declare xmlns:m on
    the root (mathml.prefixed/declare); `se build-manifest` only sets the
    `mathml` property when that root declaration exists.
  - `se lint` wants alttext on every formula (s-089): prep writes
    {book}/mathalt.json from Gutenberg's MathSpeak alts. It rejects
    pandoc's inline style (x-012) and empty <mtd>/<mrow> (s-010; <mspace/>
    is the exempt filler).
  - `se build` renders MathML to PNG for the compatible epub through
    Selenium/Firefox: export SE_CACHE_PATH to a writable directory, and
    mathml.se_safe dodges its "cannot add ancestor as sibling" crash on
    nested groups in a superscript.
The witnesses that mattered: a FORMULA-SEQUENCE diff against data-tex
(caught six displayed formulas lost in wrapper divs the word count could
not see), and a scan diff that found Gutenberg's "trillionth" for the
printed "billionth" and "sixpence" for "saxpence". Beware: Archive.org's
`calculusmadeeasy_202001`, catalogued as the 1914 book, is Gutenberg's own
typeset PDF -- not a witness. Three figure pairs (12/13, 38/39, 44/45)
carried each other's numbers and were relabelled by Thompson's text.

HELMHOLTZ, ON THE SENSATIONS OF TONE (helmholtz/, 2026-09-21), Ellis's
1885 translation: the largest page-read edition, 560 leaves proofed from the
1895 reprint's scan (fixes/ against the OCR draft, apply_fixes.py -> proof/),
56 sections, 385,000 words, 2,205 formulas, 625 notes, 181 cuts.
  THE APPARATUS IS KEPT, AS LINKS. Ellis cites his own pages by page and
  QUARTER ("see p. 77c") and the quarters are his marginal pilcrows, three a
  page (554 of 564 carry exactly three; a chapter opening prints two, the
  first falling in the heading space). Each page start and pilcrow is a
  locator token {¶77c}, each LETTERED reference a link {@77c|77c'}, rendered
  by assemble.locators() in both renderers; build_ebook.resolve_locators
  points each link at the right chapter file and stops on a link to nothing.
  ONLY LETTERED REFERENCES LINK: a bare page number cites another book as
  often as this one ("Hopkins, p. 113", "vol. lx. p. 449"), and a wrong link
  is worse than none. Primes (second column) go to the unprimed quarter.
  THE SECOND READING PAID AT ONCE (crosscheck.py, the epictetus rule): 11,966
  words of notes continued from the page before were silently lost, because
  the join went into a list already copied into the stream. Word ratio,
  verify and every per-leaf count agreed with the loss.
  A NOTE FOLLOWS THE PARAGRAPH THAT CITES IT, unless that paragraph runs on
  overleaf; the first version set every note at the page's end, up to six
  paragraphs from its mark.
  A PROOF CHUNK MAY HOLD A PROSE LINE AND ITS TABLE ROWS WITH NO BLANK LINE,
  and prose resuming after a table must not be joined into its last cell.
  TWO SHARED FIXES: a TAB block whose every line carries " | " is now a table
  in both renderers (eight books had shown literal pipes in <pre>), and the
  epub's subheads go through esct(), because escaped-only subheads shipped
  literal asterisks in twelve epubs (Gray's How Plants Grow: 118).
  THE VOTE ON A BOOK THIS SIZE needs scan_diff.opcodes' chunked alignment
  (one SequenceMatcher over 370k words did not finish in 15 minutes; chunked
  it takes 3.5); of 1,473 agreeing readings a dictionary filter left four,
  all Google-OCR artefacts ("Lectures on Sounds" is an italic comma).

Covers come from the books' own plates where Commons has nothing large
enough (build/covers/{book}.jpg with a placeholder `commons` name and a
cover_note -- the kenzeiki precedent).
