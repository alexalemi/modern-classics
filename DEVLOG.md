# DEVLOG

## 2026-08-01 (Thompson's Light Visible and Invisible — the RI set complete, and the first OCR source)

Silvanus P. Thompson's Light Visible and Invisible: 30 files, ~69k
modern words, ratio 0.96, all 127 recovered plates, epub built, `se
lint` clean. The five-book Royal Institution Christmas Lecture push is
finished — Boys, Faraday twice, Fleming, Ball, Thompson.

**This is the project's first book taken from a scan rather than from a
proofread text.** There is no Gutenberg or Standard Ebooks edition; the
source is the Archive.org OCR of a University of California copy of the
1897 Macmillan printing. That single fact reshaped the whole job. About
a fifth of the session went into the translation and four fifths into
making a source worth translating.

### The defect classes an OCR source has and a proofread one does not

1. **The page furniture is inside the text stream.** Every page carries
   a running head, and stripping it leaves a blank line where the prose
   ran on — so ~330 of Thompson's paragraphs were cut in half at the
   point where the page turned. The mend rule is that no English
   paragraph begins in lower case, plus a dangling-word list ("of",
   "the", "and", a trailing comma) for the halves that resume on a
   proper noun. Run it to a fixed point: one mend exposes another.

2. **A cell is not a paragraph.** `normalise()` drops paragraphs under
   three words, which is right for prose and fatal for tables. The
   luminescence table lost *three whole rows* that way — tribo-
   luminescence, lyo-luminescence, and the single substance under
   crystallo-luminescence — and the word ratio barely moved. Five
   tables were rebuilt from the page images (Tables I-V plus the
   wave-length appendix). **Check every table against the scan.**

3. **Every fraction is a measured value and not one of them survives.**
   5½ seconds, 6¾ millionths of an inch, 1/800 inch, 1/10000 of the
   air, 2⅞ inches, 1⅝ inch, 8¼ by 5 inches. Thirty-odd of them, each
   read back off the page image. I guessed 1/1000000 for the sixth
   Crookes tube and the page said 1/10000; I guessed 1½ and ¾ for the
   polariscope and the page said 1⅝ and ⅝. **Do not infer a fraction
   from context.**

4. **Formulas and Greek flatten to debris.** Appendix I's eighteen
   numbered formulas came through as "2 * r "" and ") i ( ^"; several
   vanished outright, leaving the prose to say "the formula becomes"
   and then say nothing. Restored from the page images into
   `thompson/appendix_fixes.py`, which is the pattern to reuse: a
   separate module of (garbled, correct) pairs, every one of which must
   still match or prep stops.

5. **Footnotes that run over a page break swallow the body.** Seven of
   them here. A footnote's tail lands in the middle of whatever
   sentence was running past it at the time, and the sentence's own
   halves end up separated by the whole note. Six pieces of prose were
   reassembled by hand this way, including the University of London
   aside and the Bose apparatus description.

### Three traps that would have shipped silently

- **A caption line and a sentence opening look identical to a regex.**
  "Fig. 115 gives a front view of the oscillator" was being read as a
  caption for plate 115 and losing its subject. The tail tells them
  apart: a caption continues in upper case or not at all, a sentence
  continues in lower case. Fixed generically in `normalise()`.

- **"Fig. 118" broken across a page break reads as a caption for Fig.
  1** — so the ripple-tank photograph of Lecture One was emitted into
  the middle of the Hertz-wave discussion in Lecture Five, and the
  cross-reference itself was destroyed. Mend split figure numbers
  *before* the caption pass ever sees them.

- **A sub-figure letter is not a misprint.** "Fig. 121b" scanned as
  "Fig. 121^", and I "corrected" it to Fig. 122 on the strength of the
  plate captions — which was wrong. Two paragraphs later the text says
  "Fig. 122 depicts one of the simplest ways of detecting such electric
  waves", which is the electroscope, not the cylinder. Looking at the
  plate settled it: Fig. 121 is one block lettered a and b. **A
  conflict between two references is the signal; the plate is the
  arbiter.**

The Fechner footnote is the one I would have missed without the numeric
check: the natural logarithm of 16 printed as "277". A number a hundred
times too large, in a footnote, passing the word ratio, the figure
parity and must_contain alike. Its neighbour, ln 100 = 4.6, kept its
decimal point and pinned the pattern.

### One real error in Thompson's own printing

The wave-length table gives the A line as 29.28 millionths of an inch,
where 75.94 micro-centimetres divided by 2.54 is 29.90. All 55 rows
were checked against both relations the table asserts about itself
(inches = micro-cm / 2.54, frequency = 30000 / micro-cm); every other
row agrees within a rounding step, and the frequency cell confirms
which of the two figures is the misprint. Corrected, with an editor's
note. The second Archive.org copy was used to settle four cells the
first has an ink blot over — and to make the point that two copies of
one setting can confirm what was *printed*, never that it was right.

### Toolchain

- `se typogrify` **unescapes `&lt;` into a bare `<`**, which makes the
  XHTML unparseable for every step after it, and the error you get is a
  raw "invalid element name" pages from the cause. `build_ebook.py` now
  refuses to ship an escaped `<` and says why. (Reworded to "h₁ is less
  than h₂", which reads better anyway.)
- `epubcheck` in this environment reports PKG-021 "Corrupted image
  file" for **every** image, including the cover and title page `se`
  generates itself, and including books already published from this
  repo — Star-land fails identically. It is a local Java image-reader
  fault, not a broken book. `build_ebook.py` now tolerates that single
  code, verifies every image itself with PIL, and builds without
  `--check`; anything else still fails the build.

Figure 63, the refractive-index chart, was recovered late from a page
image and brought the plate count from 126 to 127. Twenty figures still
have no plate — mostly small line cuts set into the text — and the
translation describes those instead of pointing at them.

Cover: Joseph Wright of Derby's "An Experiment on a Bird in an Air
Pump" (1768), crop `1919x2878+922+0`. A demonstrator, a glass receiver,
an air pump and an audience of frightened children — which is this book
exactly, and the air pump is what Lecture Six turns on.

## 2026-07-31 (Ball's Star-land — book 4 of five, and the RI set complete bar one)

Sir Robert Ball's Star-land: 36 files, ~96k modern words, ratio 0.95,
all 94 plates, epub built. The Royal Institution Christmas courses of
1881 and 1887 worked up into a book, and the warmest of the five
Christmas-lecture volumes by a distance.

The book turned out to be the **1899 revised edition, not the 1889
first** — and I only caught it because file 004 mentions "the great
spot of September 1898", which is impossible in an 1889 book. The
title page confirms it, and Ball updated throughout: Saturn's ninth
satellite (August 1898), "(1899)" as the present year, and a confident
forecast of a great Leonid shower in 1899. The Verne rule keeps that
prediction exactly as he made it, with no note that it disappointed.
`env` now says 1889/1899. prep had also dropped the **dedication**
with the copyright page; CLAUDE.md is explicit that dedications belong
in the book and contents pages do not, so it is restored.

This was the first prep that **refuses to run unless the plates
reconcile** — it asserts every image on disk is placed exactly once and
raises SystemExit otherwise. That assertion is why both of fleming's
figure traps were non-events here rather than discoveries: the
frontispiece is a bare uncaptioned `[Illustration]`, and figures 35 and
64 print their number *after* the plate's own sub-labels ("Partial.
Annular. FIG. 35."). Both were designed for from the start.

It is also the first book where **the captions come from the source**.
With Boys the 1890 original captioned every plate "Fig. 22." and
nothing else, so captions were new writing; Ball captions his own, and
they are frequently the joke — "Two Eyes are better than One", "This
is what we wanted the Cards for". Those get modernized and then
extended with a short descriptive clause, since the caption doubles as
the epub's alt text and a bare punchline tells a screen-reader user
nothing.

Three things worth carrying forward:

- **The indent threshold was wrong.** `normalise()` preserved runs of
  lines indented by four spaces; the concluding chapter's six
  astronomical tables are indented by *two*, and every one of them had
  been collapsed into running prose — "Mercury | 35.9 | 87.969 | 2,992
  | Uncertain. Venus | 67.0 | ...". Lowering the threshold to two
  spaces restored all six byte-identical, and incidentally fixed the
  interplanetary postal address and both verse quatrains. Verified
  against the manifest first: no boundary drift. Worth checking on any
  book with tables.
- **Read the whole source file, never a line range.** On file 016 I
  read with two `sed` ranges that stopped at line 40, and lines 41–45 —
  a figure marker, a section heading and a closing paragraph — were
  simply absent from the translation. Figure parity caught it in
  seconds. But the lesson is what it revealed about the checks' limits:
  had that tail been ordinary prose with no figure and no number in it,
  *nothing* would have caught it. Losing 150 words from a 2,750-word
  file moves the ratio from 0.94 to 0.89 — still inside the bound.
- **Decide the print-page references up front.** All eight were
  resolved and logged before translating, which turned up the one that
  must *not* be touched: "page 123" in Lecture Five is not a reference
  to this book at all but Ball's account of how astronomers telegraphed
  comet positions cheaply, encoding "123 degrees 45 minutes" as the
  45th word on page 123 of Worcester's Dictionary — the single word
  *constituent*. There the page number is the message.

Sensitive content: Lecture Five quotes an 1833 eyewitness account of
the great Leonid storm from a South Carolina plantation — a white
enslaver describing the terror of the people he held enslaved, called
"the negroes" throughout. The astronomy is genuinely valuable; it is
one of the best surviving descriptions of that night, and it is why
Ball quotes it. Rendered as "the enslaved people": more explicit about
what was happening, not less, since a modern young reader would not
otherwise know these were enslaved people at all. Quoted in full,
nothing cut, no commentary added, the fear not softened.

Cover: Trouvelot's *The November Meteors* — doubly apt, since that is
the shower Lecture Five is about and Trouvelot's drawings are
reproduced inside the book as figures 18 and 20.

Also this session: **the OPDS catalog was broken on an e-ink reader and
is now fixed.** The feed itself was fine — 44 entries, well-formed,
every href resolving. The problem was the header: GitHub Pages derives
Content-Type from the file extension and cannot be given custom
headers, so `opds.xml` went out as `application/xml`, which strict OPDS
clients reject before parsing a byte. The same bytes at **opds.atom**
serve as `application/atom+xml`; verified live. `opds.xml` still works
for anyone already subscribed. Entries also gained a bare
`rel=".../acquisition"` link alongside the `open-access` one (minimal
readers often look only for the bare rel) and a `<content>` mirroring
`<summary>`.

## 2026-07-30 (Fleming's Waves and Ripples — book 3 of five)

Third of the five Royal Institution Christmas Lecture volumes, and the
biggest: 32 files, ~77k modern words, ratio 0.95, all 87 plates, epub
lint clean. Fleming gave this course at Christmas 1901, months before he
invented the vacuum tube, and chapter six reports Marconi's Cornwall
aerial as current news.

The through-line is that a ripple on a pond, the wake of a liner, a note
sung into a tube, the colour of a geranium and a wireless signal are one
thing in different media — so the aether is not a digression in this
book, it is the destination. The Verne rule therefore governs the whole
back half: Fleming asserts the aether as established fact, and it is
rendered as his claim, unhedged. Archaic *gas names* got the opposite
treatment — carbonic acid became carbon dioxide silently, because that
is vocabulary, not a claim. Dated claim, keep; dated word, modernize.

**Every real defect this book had was invisible to verify.py.** That is
now the headline lesson of the whole illustrated-books run, and it is
worth stating plainly: the mechanical checks catch omission and
truncation. They cannot catch *wrong*.

- **An unnumbered plate broke figure assignment twice over.** The
  middle-C clef in chapter four is a bare `[Illustration]` with no colon
  and no caption — the only such marker in the book. A regex demanding
  the colon walked straight past it, leaving a raw marker in the text
  *and* leaving the `music` id unclaimed, so the next unnumbered block
  took it. That block is chapter six's line of Morse code spelling "How
  are you?", which would have shipped as a picture of a treble clef.
  Fixed at the root: the caption is optional, and a *captioned* plate
  with no number is now dropped rather than allowed to take a spare id.
- **A cross-reference to that same class of plate had also gone astray.**
  The gamut-of-aether-waves chart — printed unnumbered between figures 79
  and 81 — is cited in the text as "(see Fig. 77)", which is the paraffin
  prism. Almost certainly it went wrong *because* the plate has no number
  of its own.
- **Two arithmetic faults in tables.** The harmonic table prints 495 × 3
  as 1475; every other cell in both columns is exact, so it is a
  one-digit slip and 1485 was restored. The ice prism's electric
  refractive index is 1·83 in the body and 1·88 in its own footnote —
  the formula Fleming gives yields 1·813, so the footnote is the outlier
  and was harmonized to his stated 1·83. Check every table that claims to
  be computed; both of these are invisible to a word-count.
- **Numbers written as words survive every existing check.** Chasing the
  ratio drift to 0.94 turned up six measured quantities I had rendered
  as "thirty-six hours" for "36 hours". Word ratio can't see it, figure
  parity can't see it, must_contain can't see it. A set-difference on
  numeric tokens catches it instantly, and it now runs per file. It is
  cheap and it should run on every book from here on — the recipe is in
  `fleming/running_notes.txt`.
- The ratio drift itself was benign: modern paragraph counts run *higher*
  than source (Fleming's long expository paragraphs got split), and the
  missing words were his Victorian connective scaffolding.
- **The appendix trap, which is generic.** Fleming's two-note appendix
  carries no CHAPTER heading, so the splitter swept it into chapter six's
  last part — where it would have shipped buried, with no TOC entry,
  while two body notes still cited it by name. The fix that matters is
  the ordering: peel it off *after* the chapter split, never before.
  Splitting chapter six without its 1420 words changes nparts from 6 to 5
  and moves every boundary in the chapter, which would have invalidated
  five finished translations. Peeled afterwards, files 000–029 came out
  byte-identical. Its print-page references ("NOTE A (see p. 21)") are
  meaningless in a reflowable edition and became descriptive titles.
- **Indented runs must stay one block.** `normalise()` emitted one
  paragraph per indented line, so assemble.py opened a separate `<pre>`
  for each — and each carries a 2em bottom margin, which strewed the
  26-letter Morse alphabet down half a page and pulled two-line equations
  apart. 94 `<pre>` blocks became 40. And such blocks must be *dedented*,
  not stripped line by line: the Morse for "How are you?" sets its
  letters underneath their own groups of dashes, and stripping each line
  independently slides the rows out of register so the labels stop
  pointing at anything. Worth auditing the other illustrated books.
- Voice: a working engineer talking to teenagers, where everything is a
  thing on a table and he says "you see" because they can. Where the body
  drops into "The author had an instance of this before him" — the
  Victorian way of telling a story about yourself — first person was
  restored; it is the same man in the same lecture.
- Cover: Hokusai's *Great Wave* (1831). Not period-apt, deliberately: the
  book's whole argument is that one wave is every wave.
- Fleming quotes C. V. Boys's soap-solution recipe by name in chapter
  three — out of the book that opened this run.

## 2026-07-30 (Faraday's Forces of Nature — book 2 of five)

Second of the five Royal Institution Christmas Lecture volumes.

- `forces/` — 15 files, ~35k modern words, ratio 0.98, epub lint clean.
  Crookes's preface, the six Christmas 1859–60 lectures, and the
  "Light-house Illumination" address of 9 March 1860 that the edition
  appends. Note the word count: the raw Gutenberg file is 61k words, but
  a third of that is the publisher's advertisements bound in at the back.
- **Compound plates**, and the generic support for them. Victorian
  printers put several numbered figures on one woodblock, so this book's
  50 plates carry 59 figures. Markers and filenames now take hyphenated
  ids (`[Figure 15-16-17]`, `fig15-16-17.jpg`) and
  `assemble.figure_label()` renders "Figures 15, 16 and 17". Verified the
  Candle and Boys pages come out byte-identical after the change.
- The awkward part was that **the text's grouping and the plates'
  grouping disagree**. `fig15-16-17` is a single plate that the text
  marks as two illustrations — follow the text and the image prints
  twice. Figures 18 and 19 are two separate plates under one text marker.
  And `fig29` has no illustration marker anywhere; it is referenced only
  in running prose as lower-case "(fig. 29)", which a case-sensitive
  grep missed entirely. Its position was confirmed against the Gutenberg
  HTML edition rather than guessed. prep.py therefore drives markers from
  the FILES and reconciles the text to them.
- Two traps repeated from the Candle, now recorded as rules: lecture
  headings appear three times (contents, body, notes), so anchor on the
  last before `NOTES.`; and a note runs until the next note *or* the next
  per-lecture header, or the header is swallowed onto the end of a note
  ("...could be solidified. LECTURE II.").
- Three more mangled ASCII tables rebuilt as indented blocks — the 8:1
  water diagram, the cubic-inches-to-grains table, and the relative
  weights of hydrogen, air, water and platinum.
- The book opens with Faraday apologising that illness had twice
  postponed the course, saying he may manage "only a few words", and
  then claiming as always the right to speak to the young "as a young
  person myself". Kept unsoftened. It closes on As You Like It.
- Cover: Church's *Aurora Borealis* (1865) — magnetism written across the
  sky, which is precisely the thesis of the final lecture.


## 2026-07-30 (Faraday's Candle — book 1 of the Christmas Lectures five)

Alex asked for five Royal Institution Christmas Lecture volumes:
Faraday's *Chemical History of a Candle* and *On the Various Forces of
Nature*, Fleming's *Waves and Ripples*, Ball's *Star-land*, and
Thompson's *Light Visible and Invisible*. ~360k words in all. Deploying
one complete book at a time; this is the first.

- `candle/` — 15 files, ~41k modern words, ratio 0.99, epub lint clean.
  Crookes's preface, the six lectures, and the Lecture on Platinum that
  the 1861 edition appends.
- **Sourcing was scouted for all five up front**, which was worth doing:
  Gutenberg's Candle transcription keeps all 38 illustration *captions*
  and none of the woodcuts — its `-h.zip` holds one image, the cover.
  The plates turned out to be on Wikisource/Commons, so the Candle uses
  a two-source prep: text from Gutenberg, figures from Commons. Their
  naming is inconsistent in a way that would have silently dropped three
  plates (`Figure01` vs `Figure 36`, because Platinum is a separate
  Wikisource page). Forces of Nature, Fleming and Ball all ship their
  plates inside the Gutenberg zip; Thompson has no extracted plates
  anywhere and needs ~130 crops off page scans — Alex chose to do them.
- Commons served the plates as **PNG line art**, so the figure pipeline
  built for Boys needed generalizing: both renderers now resolve a
  plate's extension rather than assuming `.jpg`, and `image_size()`
  reads PNG's IHDR alongside JPEG's SOF. Confirmed byte-identical output
  for soap-bubbles afterwards. `se lint` then rejected four PNGs for
  having no transparency (f-019); converting just those to JPEG fixed it
  with no other change, which is exactly what the extension resolver was
  for.
- **Crookes's 19 notes.** I first concluded they had no anchors in the
  body and could be dropped — that was wrong, from a byte-range bug in
  my own check, and would have shipped 19 dangling `[n]` markers. They
  are anchored 18 times. Each note is now cut loose from its meaningless
  "Page 186." heading and inlined as an `Editor's note:` paragraph after
  the paragraph citing it. Better than either original option, and no
  footnote machinery needed.
- **A real defect in the source**: Lecture V anchors note 16 as `[14]`,
  so note 14 was inlined a second time in a passage about testing for
  oxygen, and note 16 never appeared at all — the note that identifies
  the "test gas" Faraday demonstrates but never names. `prep.py` carries
  a `SOURCE_FIXES` entry that raises if the misprint ever disappears.
  Worth recording that ratio and figure-parity checks were green
  throughout: a correctly-formatted note attached to the wrong sentence
  is invisible to them.
- Also fixed, in shared code: `build_ebook.py` wrote `alt` text without
  escaping quotes, so a caption naming the "philosopher's candle"
  produced unparseable XHTML. Any illustrated book would have hit it.
- Two garbled ASCII tables (the 1:8 water diagram, the atmosphere's
  bulk/weight analysis) rebuilt as indented blocks; the water diagram
  moved up to the sentence that says "represented for us in the
  following diagram", where the original typesetting had stranded it two
  paragraphs later.
- Cover: Blaikley's painting of Faraday's own 1855 Christmas Lecture — a
  2:3 slice out of a landscape canvas, centred on Faraday at the bench
  with the packed theatre behind him.

## 2026-07-30 (Boys' Soap Bubbles — the first illustrated book)

C. V. Boys' *Soap Bubbles and the Forces Which Mould Them* — the 41st
book, the first illustrated one, and the first popular-science lecturing
in the collection. Three Christmas lectures on surface tension given to
a hall full of children over the New Year of 1889–90.

- `soap-bubbles/` from Gutenberg #33370. 13 files, ~32k modern words,
  ratio 1.01. Front matter + three lectures + the "Practical Hints"
  appendix, which is a third of the book and got translated whole.
- The interesting problem was not the prose, it was the **69 figures**.
  The text makes ~150 references to them ("the apparatus in Fig. 22")
  and is unreadable without them, but the plain-text edition drops
  every plate. Gutenberg's HTML edition still has them, so all 70
  images (69 + frontispiece) were pulled into
  `site/images/soap-bubbles/`.
- New generic capability across three tools: figures travel as
  plain-text markers (`[Figure 22]` in, `[Figure 22: caption]` out) so
  chapters/ stays text; `env` gains `FIGURE_DIR`; assemble.py renders
  `<figure>` and reads intrinsic dimensions from the JPEG so narrow
  plates aren't stretched; build_ebook.py does the same into the SE
  draft; verify.py gained check 6, figure-set equality per file, with
  markers excluded from the word counts.
- **The captions are new writing.** Boys captioned every plate "Fig. 22."
  and nothing else, so the modern edition writes a descriptive line for
  each. Worth actually looking at the images first: fig6 turned out to
  show two toy passengers and a sail on a tobacco-pipe mast — Boys had
  built Lear's Jumblies for real — and `fig39b`, which has empty alt
  text and no caption in the source, is not a figure at all but the
  *scale bar* for Fig. 39's photomicrograph of spider-web beads. It is
  now emitted caption-less directly beneath it.
- Boys' fold-out Fig. 35 (43 photographs of a falling drop, to be cut
  out and spun as a thaumatrope) sat at the very end of the 1890 book
  behind a marginal note. prep.py moves it inline to where it's
  discussed, and his "see page 149" cross-references were rewritten to
  point at the Practical Hints.
- Two bugs found by rendering the page and looking at it:
  (1) `assemble.py`'s `strip_front` called `.strip()` on the body, which
  ate the leading indentation of a chapter's *first* paragraph — so a
  file opening on verse silently lost its `<pre>` and Lear came out as
  one run-on line. Fixed to trim blank lines only; checked against all
  39 other books, where it changes exactly two (democracy2's chapter
  summaries and dialogues' cast lists, both now consistent with their
  own siblings).
  (2) A parenthetical footnote, "(Note: For particulars see the
  Philosophical Magazine, September 1890.)", was rendered as an `<h4>` —
  short, majority-capitalised, and no terminal period *outside* the
  bracket. Such notes now end in a plain period.
- The appendix has children handling ether, carbon disulfide, mercury
  and molten wax, none of it flagged in 1890. Boys' recipes are kept
  verbatim with nine sparing `[Modern note: ...]` annotations — obsolete
  materials, real hazards, and a bubble mixture that works today.
- Still to do: epub (wants a cover — Millais' *Bubbles*, which Boys
  himself name-checks in Lecture One, is the obvious choice), feeds,
  commit and push.

## 2026-07-21 (Theophrastus; Galileo prepped)

Theophrastus' Characters — the 35th book, and the first past the
Founders' Library. Also the first book finished without subagents:
the session hit the 200-subagent limit mid-Galileo, so sketches
11–30 were translated inline by the orchestrator itself.

- `theophrastus/` — 30 comic character sketches + the Epistle
  Dedicatory (Bennett & Hammond 1902, Gutenberg #58242). Three files
  of ten sketches, ratio 0.97. The voice agent locked all 30 modern
  titles up front (The Phony, The Chatterbox, The Cheapskate, The
  Trash-Talker, The Sleaze...) plus the formula "[Vice] is, in
  essence, [definition]. The [title] is the sort of man who..." —
  the catalogue engine is the comedy, so the formula is the lock.
- Prep bug: the Gutenberg end-marker matched the license header deep
  in the file, leaking license text into 002.txt — end marker
  tightened to "*** END OF THE PROJECT GUTENBERG".
- Two ebook toolchain fixes: non-numeric cover years ("the 2nd
  century AD") no longer go inside `<time>` (vnu rejects them), and
  `prepare_cover` now steps JPEG quality down until the cover fits
  se lint's 1.5MB cap (the masks mosaic blew past it at q90).
- Cover: the Hadrian's Villa theatrical-masks mosaic.
- Galileo's Dialogue is fully prepped (it.wikisource source, speaker
  tags, docs, front matter translated — 55 dialogue files remain)
  but blocked on the session subagent limit; see ROADMAP.md for it
  and the full future queue.

## 2026-07-21 (Founders' Library complete)

Seneca's Moral Letters + Cato's Letters — THE FOUNDERS' LIBRARY IS
COMPLETE. All 13 works from Alex's Pursuit-of-Happiness list are now
translated, built, and deployed.

- Seneca: `seneca/` — all 124 letters (~209k words, the project's
  largest book) from Wikisource's Gummere (SE unpublished, Gutenberg
  lacks the work entirely; downloaded via the MediaWiki parse API
  with polite backoff). 55 files, ratio 0.93, zero lint errors.
  Ledger discipline at scale: the daily-wage Epicurus ritual tracked
  until Seneca himself ends it at Letter 33 (later agents barred from
  resuming it); the Cleanthes hymn rendered to match our Enchiridion
  volume exactly; Cato's death kept consistent across five letters
  AND with the Roman Lives volume; a Letter 71→75 self-quotation
  harmonized at merge. Known source gaps documented in text_analysis
  (Wikisource lacks Letter 64 §§1–4; a one-line bridge in Letter 84's
  bee passage was restored from Gummere's known text — the only
  restoration, flagged). Two source typos fixed in chapters+modern
  together ("Tlme", "in of the"). One orchestrator-caused defect
  caught before deploy: the Farewell-normalization regex left single
  newlines that merged 39 letter headings into the previous
  paragraph — fixed volume-wide, epub rebuilt.
- Second spend-limit incident: 4 agents "failed" but all had written
  complete verified files (the Ethics lesson held — check outputs
  before re-running; zero re-runs needed).
- Cato's Letters (committed previous push): the closing-formula
  variance across agents normalized to "I am, etc." + initial.
- Cover: Domínguez Sánchez's The Suicide of Seneca (1871).

THE FOUNDERS' LIBRARY (13/13): Plato (Apology/Crito/Republic in
Dialogues), Aristotle's Nicomachean Ethics, Xenophon's Memorabilia,
Plutarch's Roman Lives, Cicero's On Duties + Tusculan Disputations
(both from the Latin), Seneca's Moral Letters, Epictetus' Enchiridion,
Marcus Aurelius' Meditations, Franklin's Autobiography + Way to
Wealth, and Trenchard & Gordon's Cato's Letters (selected).

## 2026-07-21 (later still)

Plutarch's Roman Lives — the five-lives volume.

- New book: `roman-lives/` from Gutenberg #674 (Dryden-Clough). Five
  lives — Caesar, Cato the Younger, Cicero, Brutus, Antony — chosen as
  the fall-of-the-Republic arc the founders studied; 28 files, ratio
  0.96 (113k → 109k).
- The volume's central craft problem: the five lives retell the SAME
  events (Catiline, the Rubicon, the Ides, Philippi, Actium, Cicero's
  death). The ledger accumulated fixed renderings per event at first
  occurrence, and later agents echoed them — while PRESERVING
  Plutarch's own cross-life contradictions as source-faithful
  divergences (who detained Antony at the door: Decimus in Caesar,
  Trebonius in Brutus, unnamed in Antony; the prison-march silence;
  "hands" vs "right hand" on the Rostra; 200 vs 300 proscribed).
  Both fidelity rules held simultaneously.
- Names policy: this volume deliberately uses "Pompey"/"Octavian"
  (narrative familiarity) unlike the Cicero volumes' Latin-form rule;
  Sulla/Gaius normalized from Dryden's Sylla/Caius; Dryden's corrupt
  Gallic names repaired (Vergentorix→Vercingetorix).
- One must_contain lock removed at verify: Cato's "destroy the state
  sober" quip is Suetonius, NOT Plutarch — a prep-stage error; lesson:
  verify famous quotes against the actual source text before locking
  (the locks that were source-verified all passed).
- Cover: Gérôme's The Death of Caesar (1867). Lint: zero errors.
- Meanwhile: Seneca (55 files, Wikisource Gummere — SE unpublished,
  Gutenberg lacks it entirely) and Cato's Letters (18 selected
  letters, Wikisource) are prepped and translating; both fully
  documented in their text_analysis files.

## 2026-07-21 (night)

Nicomachean Ethics — the glossary-driven book.

- New book: `ethics/` from SE's Peters translation (single-page XHTML,
  the autobiography prep pattern; 784 endnote refs stripped). 116
  chapters/10 books in 25 files; Peters' thematic part titles kept as
  subheadings. Ratio 0.95 (91.6k → 86.6k), all locks intact.
- The distinctive move for this book: a LOCKED GLOSSARY in
  text_analysis.txt treated as law (happiness, habit, the mean,
  practical wisdom, self-restraint vs. weakness of will — banning
  Peters' "continence/incontinence" — the noble, activity, function,
  generosity, friendship…), extended between batches as agents
  flagged new territory (choice/prohairesis, the Book V justice
  framework, the VI satellite faculties, VII's endurance/brutishness,
  VIII–IX friendship terms). Seam fixes at merge were tiny and caught
  by the ledger discipline: foolhardy/reckless, a duplicate hexis
  gloss, hardiness→endurance, one mikropsychia collision.
- Mid-book incident: the monthly spend limit killed a whole batch of
  6 agents — but 4 of the 6 had already written complete, verified
  files before dying (the failure notices only meant the *return
  message* was lost). Lesson: after agent failures, check the output
  files before re-running anything; only 2 files actually needed
  relaunching.
- Cover: Raphael's School of Athens. Lint: 10 manual-review rows,
  zero errors.
- Founders' Library: 10 of 13. Roman Lives (5-life fall-of-the-
  Republic volume: Caesar, Cato, Cicero, Brutus, Antony — 28 files)
  is prepped and starting; then Seneca, then selected Cato's Letters.

## 2026-07-21 (later)

Tusculan Disputations — second from-the-Latin volume. Standing goal
set by Alex: work through the whole Founders' Library.

- New book: `tusculan/` — Latin from The Latin Library (first
  non-Gutenberg/SE source), Yonge's English (PG #14988, minus the
  bundled De Natura Deorum) as per-book cribs since the two sources
  divide the text differently (§§ vs. chapters). prep.py fought:
  nav-link rows of numerals, two garbled section numbers in Book I
  (renumbered by position), mid-line § numerals glued to punctuation,
  two anchor variants, dangling chapter numerals (stripped at 2+
  letters only — single letters are praenomens).
- Translation: 16 files, ratio 1.50 (48.5k Latin → 72.8k English),
  all six locks intact (preparation for death; cultivation of the
  mind; philosophy, guide of life; Damocles + single horsehair;
  Archimedes). The Latin has no M./A. speaker tags (they're Yonge's),
  so the dialogue is rendered as embedded quoted speech.
- Orchestrator seam-fixes at merge: harmonized the grief-species list
  (III.83 vs. IV.16–21), the gestiens family ("exultant"), Pompey→
  Pompeius (cross-volume consistency with On Duties), and two
  quote-punctuation slips lint caught (a lowercase re-opened quote,
  a missing re-opening quote in a Plato quotation spanning sections).
- Agents caught genuine Yonge errors (Aristus/Aristo confusion,
  lyre-not-flute, inverted fear definition) and repaired Latin
  Library typos against the standard text, flagging real cruxes
  (Theombrotus, Anticlea, Nicocreon).
- Cover: Westall's The Sword of Damocles (1812). Lint: manual-review
  rows only.

## 2026-07-21

Franklin's Autobiography — first Standard-Ebooks-HTML-sourced book.

- New book: `autobiography/` from SE's single-page XHTML (Pine's 1916
  chapter arrangement, 19 chapters, one file each). `prep.py` grew an
  HTMLParser-based converter: SE endnote refs stripped (editorial, not
  Franklin), lists/tables (the 13 virtues, the tracking chart, the
  daily schedule, Braddock's supply list) become two-space-indented
  blocks that assemble.py renders as <pre>. A pattern for future
  SE-sourced books (Nicomachean Ethics, Seneca next).
- Translation: 19 agents in three batches + voice file; overall ratio
  a remarkable 1.00 (61,623 → 61,625 words). All nine locked passages
  intact ("Dear Son", puffy rolls, the cod moral, "bold and arduous
  project", "Eat not to dullness", "Imitate Jesus and Socrates",
  "a speckled ax was best", errata). "errata" glossed once at its true
  first use (ch. 2) and used plain thereafter — coordinated across
  parallel agents via the ledger.
- Editorial calls worth recording: ch. 8's Memo referenced the Abel
  James/Vaughan letters, which the SE/Pine edition itself omits (they
  live in an endnote) — the Memo line was smoothed to "the advice of
  friends who had written urging me to continue". The book ends on the
  source's "[Unfinished]", nothing added. "empty sack" (ch. 10) vs.
  our Way to Wealth's "empty bag" is NOT a seam: Franklin's own two
  texts differ.
- Cover: Benjamin West's "Benjamin Franklin Drawing Electricity from
  the Sky" (as planned when Way to Wealth took the Duplessis
  portrait). Lint: 10 manual-review abbreviation rows in quoted
  period documents, zero errors. (se lint's --plain mode crashes on
  messages containing literal [/xhtml] — use table mode when that
  happens.)

## 2026-07-20 (night)

On Duties (Cicero) — the first from-the-Latin volume — plus feed fixes.

- New book: `de-officiis/` from Gutenberg #47001, the 1913 Loeb
  PARALLEL edition: Cicero's Latin + Walter Miller's English
  alternating chapter by chapter. Translated FROM THE LATIN (the
  democracy2 move); Miller kept per-file under `reference/` as a
  comprehension crib with an explicit don't-echo-Miller rule. 103
  chapters (45/25/33) in 12 files; verify runs with
  `--min-ratio 1.0 --max-ratio 1.8` since English expands Latin
  (final ratio 1.47: 34.6k Latin → 50.9k English).
- prep.py battles worth remembering for Tusculan Disputations later:
  Roman praenomen abbreviations ("L. Manlio…") masquerade as chapter
  numerals (fixed by accepting only next-expected numerals in the
  Latin-leads-English alternation); Latin sometimes runs two chapters
  ahead of its English; and in ONE spot the Loeb alternates by page —
  Book II ch. XIII resumes via a "*44* (XIII.)" marker the parser
  misses. That stranded Latin was recovered by the translation agent
  and then moved back into chapters/006.txt by hand (see prep.py's
  header note before rerunning it).
- The agents' Latin-first discipline caught real Miller issues:
  Loeb editorial glosses presented as text, added addressees in the
  Pyrrhus verse, Caesar/Pompey named where Cicero pointedly leaves
  them unnamed ("this tyrant of ours" — policy: follow the Latin).
- Epub: Maccari's "Cicero Denounces Catiline" fresco (focus_x 0.18 to
  crop onto Cicero); the Commons file is a PNG, which `se` rejects
  when cached as cover.jpg — converted the cache to real JPEG.
  Note: my long_description fix no-opped once because I searched for
  a typogrify-curled apostrophe in the raw JSON; edit ebook_meta with
  straight quotes.
- Feeds: base URL corrected to https://www.alexalemi.com (bare
  alexalemi.com is Squarespace and 301s via plain http, which
  e-reader OPDS clients refuse — this was the Xteink X3 "Failed to
  fetch"). Feeds also need the site DEPLOYED to exist at all.

## 2026-07-20 (evening)

The Memorabilia (Xenophon), plus site feeds and an About-page scaffold.

- New book: `memorabilia/` from Gutenberg #1177 (Dakyns). `prep.py`
  strips Dakyns' footnote apparatus and Greek transliterations,
  auto-patches Book III's mislabeled fourteenth chapter (a second
  "XII"), and groups 39 chapters into 18 part-files — a new structure:
  one *section* per Book stitched from parts (like Herodotus), with
  "Chapter N" h4 subheadings inside preserving Book+chapter citations.
  Translated via shared ledger: 1 voice file + batches of 5 and 6;
  overall ratio 0.86, all locked passages intact (indictment, divine
  sign, Choice of Heracles "two roads", closing "best and the happiest
  of men" — the finale intentionally reorders the source's last two
  sentences so the eulogy line closes the book).
  Two source corruptions found and cleanly folded out by agents (a
  leaked flush-left syllogism schema in IV.6, a garbled voluntary-liar
  line in IV.2) — prep.py's indent-based footnote filter can't catch
  flush-left apparatus; worth a manual scan on future Dakyns texts.
  Epub lints completely clean (zero rows); cover is Carracci's Choice
  of Hercules (1596) — the fable in II.1, and the image John Adams
  proposed for the Great Seal.
- RSS + OPDS: new `build_feeds.py` → site/feed.xml (RSS 2.0, epub
  enclosures) and site/opds.xml (OPDS 1.2 acquisition catalog), covers
  copied to site/covers/. Publication dates = first git commit of each
  site page (uncommitted pages fall back to 2026-01-01 and sort oldest,
  so commit new books before deploying; `make deploy` now regenerates
  feeds first). Autodiscovery links in index + template; PAGE_OVERRIDES
  maps dirs whose page names differ (malthus→population,
  descartes→philosophical-works). Base URL:
  https://alexalemi.com/modern-classics
- About page: Alex writes prose in `about.md` (placeholders only for
  now); `make about` renders site/about.html via build_about.py, which
  borrows the <style> block from site/index.html at build time.

## 2026-07-20 (later)

The Way to Wealth (Franklin) — second Founders' Library book of the day.

- New book: `way-to-wealth/` from Gutenberg #43855, an 1810 Darton
  chapbook printing; `prep.py` extracts Franklin's 1758 essay only
  (publisher ads, illustration captions, and Darton's added
  Roman-numeral paragraph markers stripped). Single 2,946-word chapter,
  single translation agent; ratio 1.01, all 22 "as Poor Richard says"
  refrains and every locked proverb intact.
- Cover: Duplessis' 1785 Franklin portrait (the Benjamin West kite
  painting is reserved for the Autobiography later).
- Lint at parity: two benign manual-review rows — the y-003
  "paragraph ends in '; but'" is faithful to the source, which breaks
  mid-sentence into the "age and want" couplet.

## 2026-07-20

The Enchiridion (Epictetus), and the start of the Founders' Library.

- New book: `enchiridion/` from Gutenberg #45109 (Higginson's translation;
  the 1948 Liberal Arts Press introduction is stripped by `prep.py` — it
  is separately copyrighted and we only want Higginson's 1865 text). This
  edition has 51 sections (standard numbering through §43; Higginson
  merges the usual 50–53 at the tail). Sections are tiny, so `prep.py`
  groups them into 4 ~1.7k-word files with "Section N" subheadings rather
  than using splitter.py — a pattern for future aphoristic texts.
  Translated with the shared-ledger pattern (1 voice-setting agent + 3
  parallel); verify ratio 0.96, all 7 locked famous passages intact.
  Site page, index entry, and epub built (lints at parity: one t-064
  manual-review row on the colophon painting title, matching Leviathan's
  precedent of benign manual-review rows).
- `build_ebook.py` heading-regex fix: the label alternation now requires
  a word boundary, so a title like "Sections 1–15" no longer half-matches
  "Section" and emits "s 1–15" as the chapter heading. Would have bitten
  any plural label ("Letters …", "Essays …").
- Toolchain note: under Claude Code's sandbox, epubcheck reports valid
  cover images as "Corrupted image file encountered" (PKG-021) because
  Java can't write its ImageIO cache to /tmp. Harmless outside the
  sandbox; `-Djava.io.tmpdir` works around it when running epubcheck by
  hand (but JAVA_TOOL_OPTIONS breaks `se build`'s output parsing).
- Project direction: working through the Founders' Library (the shared
  bookshelf from *The Pursuit of Happiness*). Already covered: Meditations;
  Plato's Apology/Crito/Republic (in the dialogues volume); now the
  Enchiridion. Queued, sources scouted: The Way to Wealth (PG 43855),
  Xenophon's Memorabilia (PG 1177), Franklin's Autobiography (SE),
  Nicomachean Ethics (SE, Peters), Plutarch's Roman Lives (PG 674,
  Dryden/Clough — SE's Perrin edition was never produced), Seneca's
  Moral Letters (SE, Gummere). Decisions: both Cicero works (On Duties,
  Tusculan Disputations) will be translated from the original Latin
  (PG 47001 for De Officiis; no public-domain English De Officiis exists
  on PG/SE anyway) — same move as democracy2's from-the-French pass;
  Cato's Letters will be a selected-letters volume (full text is ~350k
  words and lives only on OLL/constitution.org/archive.org).

## 2026-07-08

Linked the epubs from the site and refreshed all the pages.

- `site/index.html`: every entry now has an epub link in its byline;
  each book page's header note links its epub too (new `{{EPUB_SENTENCE}}`
  in the template — `assemble.py` finds the right file by reading the
  dc:source out of each epub's OPF rather than keeping a mapping).
- Regenerating surfaced that the committed pages were stale: they'd been
  generated before the June "quality pass" rewrote the chapter text (and
  by an assemble.py variant that was never committed). Pages now match
  the current chapters — the same text the epubs are built from.
- Two renderer fixes applied to *both* the site and the epubs:
  dialogue speakers on their own line (Plato, ~9,700 blocks) no longer
  run into their text — site renders `<b>Socrates</b>: …`, epubs use
  `<b epub:type="z3998:persona">`; and `---` scene markers become
  thought breaks (`<hr>`) instead of literal dashes (the epubs had been
  typogrifying them into lone em-dash paragraphs). Scene breaks at
  section boundaries are dropped (lint s-012). Seven epubs rebuilt;
  all 24 still lint clean and pass epubcheck.
- `assemble.py`'s no-manifest fallback now ignores `NNN_notes.txt`
  (the hazard flagged yesterday).
- Note for deploys: `make deploy` rsyncs `site/` with `--delete`, so
  `site/ebooks/` (~55 MB) ships on the next deploy.

## 2026-07-07

Standard-Ebooks-quality epubs for the whole library. New `build_ebook.py`
(+ `rebrand.py`, `ebook_meta.json`) converts each book's `modern_chapters/`
into an SE-style source tree with the pipx `se` toolset, then lints and
builds to `site/ebooks/<author>_<title>.epub` (plus an `_advanced` build).
`make ebooks` rebuilds everything; build trees live in `build/ebooks/`
(gitignored).

- Reuses `assemble.py`'s section parsing so the site and the epubs agree;
  part grouping for pre-manifest books is reconstructed from "(Part n of k)"
  markers.
- SE semantics throughout: hgroup ordinals + titles, part files with
  `data-parent`, verse blockquotes, `<hr/>` scene breaks, era abbrs,
  half-title pages when a book has frontmatter.
- All Standard Ebooks trademarks are replaced (publisher = Modern Classics,
  imprint/colophon/uncopyright rewritten, identifier = repo URL); imprint
  states plainly that these are Claude-assisted retellings and not SE
  productions. Original PG translators are credited in the colophon.
- Covers: public-domain paintings from Wikimedia Commons, one per book,
  cropped to SE's 1400x2100 (choices + credits in `ebook_meta.json`).
- Gotchas: don't import `se` into the system python (a `regex` C-extension
  conflict produces heisenbugs — shell out to `se titlecase` instead);
  `se create-draft` prompts when a title collides with SE's catalog;
  `se build` names its output after the dc:identifier.
- Fixed a latent hazard in no-manifest books: `assemble.py`'s fallback
  globs `*.txt`, which now also matches `NNN_notes.txt` translation-notes
  files — the epub builder guards with `\d{3}.txt`. The site generator
  should get the same guard before any page is regenerated.
- Final sweep: all 24 books lint with zero errors and pass epubcheck.
  Late fixes: repeated matter sections get unique filenames (Democracy in
  America has a preface per volume — the collision only shows up as an
  epubcheck duplicate-itemref error); `EBOOK_WIKI_URL` placeholder is
  handled when create-draft can't find the title on Wikipedia
  ("Philosophical Works"); books without a `SOURCE_URL` in `env` no longer
  get the repo URL as a duplicated dc:source. Note `build_ebook.py` reuses
  an existing `build/ebooks/<slug>` tree — after changing `rebrand.py`,
  `rm -rf` the tree first, since placeholder-driven replacements no-op on
  a second pass.


## 2026-06-11 (night)

Two more books:

- Utopia (More, 1516, Burnet's 1684 translation, PG #2130). 14 files,
  ratio 0.91. The interpretive-tightrope rule (never resolve the satire)
  went in the analysis doc and held — Raphael stays a true believer,
  "More" stays politely skeptical, the closing "rather wish, than hope"
  lands intact.
- Selected Essays of Montaigne (Cotton/Hazlitt, PG #3600): 23 essays +
  the preface (~136k words of source), curated from 107 — the canon
  (Cannibals, Friendship, Education, Repentance, Experience...) plus the
  short gems. 34 files, ratio 0.90. New policy that earned its keep: all
  Latin verse quotations collapsed to one integrated English clause with
  mid-flow attribution — Cotton's double-rendering (Latin + bracket
  translation) would have been a third of the book. Extraction needed
  care: PG #3600 is stitched from volume files with per-volume "ETEXT
  EDITOR'S BOOKMARKS" blocks, the Apology hides under a mixed-case
  heading that the all-caps chapter regex missed (it silently inflated
  Of Cruelty to 82k words until caught), and the editorial --[...]--
  bracket notes had to be dropped wholesale. Remaining giants (Apology,
  Of Vanity, Upon Some Verses of Virgil, Of Physiognomy, Of Presumption)
  left for a possible second volume.

## 2026-06-11 (evening)

Added Lucian's True History (c. 175 AD, via Francis Hickes' 1634
translation, PG #45858 — Whibley introduction and Hickes' marginal
footnotes dropped). The first science fiction story, from the DEVLOG
wishlist. ~16k words, 4 files, one voice-setting agent then 3 parallel;
ratio 0.92, all checks pass. The comic compounds got locked in file 000
(Vulture Cavalry, Salad-Wings, Pumpkin-Pirates...) and the "that I lie"
confession lands as the punchline it is. One workflow note: verify.py
flagged a must_contain phrase that I had copied in Hickes' archaic
wording while text_analysis §7 itself mandated the modern rendering —
the check was wrong, the translation right; must_contain phrases should
be drawn from the strategy's target phrasing, not the source's.

## 2026-06-11 (later)

Two additions:

1. Redesigned site/index.html: books grouped by theme (Political
   Philosophy / Economics / The Ancient World / Philosophy & Science /
   Fiction & Ideas) with one-line blurbs and reading-time estimates.

2. Added Rousseau's The Social Contract (1762, Cole translation, PG
   #46333 trimmed to the Social Contract proper) — completes the
   social-contract trilogy with Leviathan and Two Treatises. First full
   run of the new harness on a fresh book: splitter (book-level regex,
   9 files), text_analysis + agent_instructions + running_notes ledger,
   Book I solo then 8 parallel agents, verify.py (ratio 1.00, all famous
   passages present), generic assemble.py with split_headings for the
   Foreword. The agents handled the Gutenberg footnote-displacement
   quirks (notes physically located across part boundaries from their
   anchors) by coordinating through their returned notes. ~45k words,
   roughly two hours wall-clock end to end.

## 2026-06-11

Quality pass over all 19 earlier books (made by older models). Findings and
fixes:

- federalist, progress-and-poverty, wealth-of-nations: modern_chapters
  files were raw model responses (`<modernized_text>` wrappers +
  explanation/notes sections). Extracted clean text, moved the extras to
  `NNN_notes.txt`. Site pages were unaffected (built from extracted text).
- wealth-of-nations: Book IV ch. VI "Of Treaties of Commerce" had never
  been translated — the grain-trade digression had spilled across files
  042/043 and the site page had the Treaties heading sitting on Colonies
  content. Translated the missing chapter (~4.6k words), rebalanced the
  files (042 = full digression, 043 = Treaties), and fixed the site page.
- dialogues: the book had been interrupted — site only published through
  Republic X; files 024-058 were translated but unpublished, and
  Theaetetus (both halves) + Timaeus Part 2 (~46k words) were never
  translated. Translated the three missing chapters (9 subagents) and
  extended site/dialogues.html with five new groups: Shorter Socratic
  Dialogues, Language and Knowledge, The Late Dialogues, Cosmology and
  Myth, and The Laws (25 new TOC entries; page now the complete Jowett
  Plato).
- Verified-acceptable flags (no action): herodotus 018 (0.59 ratio =
  stylistic compression, subagent confirmed all content present);
  wealth-of-nations 023 (Smith's wheat-price tables replaced by a
  transparent editorial note summarizing them); democracy 039 (omitted
  tail is footnote material); gallic-war (0.78 = Latin syntax tightening,
  names/numbers verified intact).

## 2026-06-10

Completed Leviathan (Hobbes, 1651). A previous attempt had stalled after
downloading the source (safety filter trip, likely on the political-violence
material read out of context); this pass framed every chapter prompt as
scholarly modernization of a canonical political-philosophy text and had no
filter issues at all — all 47 chapters plus the Epistle Dedicatory,
Introduction, and Review & Conclusion translated complete (~213k words in,
~217k out, ratio 1.02).

Process notes: split into 57 files (chapter 42, "Of Power Ecclesiastical,"
is 29.5k words and became 5 parts; chapters 26, 44, 45, 46 also split).
Instead of strictly sequential chapter-notes passing, used a shared
`agent_instructions.txt` + `running_notes.txt` ledger updated between
parallel batches of 4-6 subagents — kept vocabulary locked ("commonwealth,"
"covenant," counsel vs. command, the personation machinery) across ~50
agents while cutting wall-clock time roughly 5x. `manifest.json` +
`assemble.py` rebuild `site/leviathan.html` from the modern chapters.

Harness overhaul (same day): rewrote `splitter.py` (heading-regex mode,
Gutenberg stripping, oversize auto-split, manifest output), added
`verify.py` (ratio/seam/famous-passage checks — the ratio bound catches
silent summarization), replaced the per-book assemblers with a generic
`assemble.py` + `site/template.html`, moved the old API scripts to
`legacy/`, and rewrote CLAUDE.md to document the shared-ledger parallel
translation pattern. Regenerated leviathan.html via the generic assembler:
byte-identical body, only two internal anchor slugs changed.

## 2026-02-23

Got interrupted with the rest of Dialogues by Plato and the Decameron.

Decided I should try to do 

Demoracy in America from the original French: https://www.gutenberg.org/ebooks/30513

and

An Essay Concerning Human Population by Malthus: https://www.gutenberg.org/ebooks/4239

Other suggestions are Erewhon.

True History (Lucian)
The Night Land (Hodgson)
The Coming Race (Bulwer-Lytton)
Looking Backward (Bellamy)
News From Nowhere (Morris)
The Iron Heel (London)
Walden (Thoreau)
A Voyage to Arcuturus (Lindsay)
Phantastes (MacDonald)

An Investigation of the Laws of Thought (Boole)
A Sceptical Chymist (Boyle)
Opticks (Newton)
The Education of Henry Adams
A Budget of Paradoxes (De Morgan)
Mutual Aid (Kropotkin)

The Travels of Sir John Mandeville



## 2026-02-22

Asked Claude for some tests to consider, suggested:

 * The Pilgrim's Progress
 * Candide
 * The Odyssey
 * Don Quixote
 * Meditations
 * Julius Caesar's diary
 * The Iliad
 * Herodetus' histories
 * Plutarch's Lives
 * Dante's Divine Comedy
 * The Thousand and One Nights
 * Discourses
 * Enchiridion
 * The Prince
 * Utopia
 * Bacon's Essays
 * Montaigne's Essays
 * Moby Dick
 * Wealth of Nations
 * Origin of Species
 * The Federalist Papers
 * Gulliver's Travels
 * Scarlet Letter
 * Frankenstein
 * Paine's Common Sense

I think the best are Smith, Darwin, the Federalist Papers, Paine's Common Sense
For Colin, Democracy in America by de Tocqueville

## 2024-09-09

Tried out Gemini, might be the best for this.  The [ai
studio](https://aistudio.google.com/app/prompts/1V-Xf_6BQQ1WX3sGIlZNsuXURfOM_wKEU)
let's you customize a prompt and can accept up to 1 million token inputs.
