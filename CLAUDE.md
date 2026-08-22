# Modern Classics

Modernize classic public domain texts into engaging, accessible contemporary English
using Claude as both the orchestrator and the translator.

## Project Goal

Take old public domain books with archaic language and retell them in a modern,
conversational voice — faithful to the original meaning but genuinely fun to read.
Target reading level: eighth grade to high school.

## How a Translation Works

Each book goes through these phases:

### 1. Setup — Prepare the source text

- Obtain a plain text version of the book (standardebooks.org is the best source,
  Project Gutenberg is the secondary source)
- Place the source text in a new directory: `{book}/`
- Create a `{book}/env` file with metadata:
  ```
  ORIGINAL_WORK=Title of the Work
  AUTHOR=Author Name
  DATE=Year
  SUBTITLE=optional subtitle shown under the title
  SOURCE_NAME=Project Gutenberg          # optional attribution link
  SOURCE_URL=https://www.gutenberg.org/ebooks/NNNN
  MODERN_YEAR=2026
  ```
- Split the source into chapter files with `splitter.py`:
  ```
  python3 splitter.py {book}/source.txt --headings '^CHAPTER [IVXL]+\..*$'
  ```
  It strips the Gutenberg wrapper, auto-splits chapters over ~7k words into
  parts at paragraph boundaries (a translation agent must *output* as much
  text as it reads, so output limits — not input context — are the binding
  constraint), writes `chapters/NNN.txt`, and emits `manifest.json`, which is
  the single source of truth for file → chapter mapping from here on.
  Text before the first heading lands in `preamble.txt` — decide explicitly
  whether to fold it into chapter 000 (dedications belong in the book) or
  drop it (tables of contents do not).
- Hand-edit `manifest.json` to add `"part_before"` dividers (e.g.
  `"Part II: Of Commonwealth"`) and, for a front-matter file holding several
  sections, `"split_headings"`.

### 2. Text Analysis — Develop a translation strategy

Before translating any chapters, analyze the full work and write
`{book}/text_analysis.txt` covering:

- Style, tone, and key themes of the original
- Challenges specific to this text (archaic vocabulary, cultural references, etc.)
- Consistent vocabulary mappings (archaic → modern equivalents)
- How to preserve the author's distinctive voice in modern English
- **Famous passages** that must survive near-verbatim — also list these in
  `{book}/must_contain.txt` so `verify.py` checks them mechanically
- Any content that needs careful handling, with explicit guidance

**Sensitive historical content:** canonical works discuss war, rebellion,
punishment, and religious conflict. Frame every subagent prompt as scholarly
modernization of a canonical historical text, and put the handling guidance
(measured register, render the author's argument as *his* argument, never
sensationalize or bowdlerize) in the analysis doc. This framing is what got
Leviathan through cleanly after an earlier attempt tripped safety filters.

### 3. Chapter-by-chapter Translation — shared-ledger pattern

Don't translate strictly sequentially with chapter-to-chapter notes passing;
use the shared-ledger pattern (proven on Leviathan, ~5x faster with no
consistency loss):

- Write `{book}/agent_instructions.txt` once: the standing prompt every
  translation subagent reads (persona, required reading, translation rules,
  heading conventions, multi-part file rules, output format). Subagent
  prompts then shrink to a few lines: file number, chapter title, anything
  chapter-specific.
- Maintain `{book}/running_notes.txt`: the accumulated consistency ledger —
  locked vocabulary ("caps spent, no re-gloss"), tone calibration, forward
  references to honor. Every agent reads it; the orchestrator (not the
  agents) updates it between batches from the agents' returned notes.
- Translate the first file **alone** to establish the voice, then run
  parallel batches of 4–6 subagents, updating the ledger between batches.
- Each agent writes `modern_chapters/NNN.txt` and returns (a) a short
  summary and (b) consistency notes for the ledger.
- **Specify exact heading strings in the prompts** ("Chapter 42: Of
  Ecclesiastical Power") rather than letting parallel agents invent them —
  independent reasonable choices are where seam bugs come from.
- Multi-part chapters: heading line, then `(Part n of k)`, then the
  translation; parts 2+ never re-introduce the chapter, non-final parts
  never conclude it.

### 4. Verify — before assembly

```
python3 verify.py {book}
```

Checks every chapter has a modern counterpart, per-file word ratios are
within 0.6–1.6 (catches silent summarization — the project's worst failure
mode), part markers haven't leaked into the body, no part divider appears
twice (the classic seam bug between parallel agents), and every phrase in
`must_contain.txt` survived. Fix failures before assembling.

### 5. Assembly — Combine into a readable book

```
python3 assemble.py {book}        # writes site/{book}.html
```

Generic and data-driven: page shell from `site/template.html`, metadata from
`{book}/env`, structure from `manifest.json` (multi-part chapters are
stitched back into single chapters; `part_before` entries become part
dividers in the TOC and body). Subheadings, indented outlines, and paragraph
rendering are handled by convention — see the docstring.

Then add the book to `site/index.html`.

## Translation Philosophy

The translator persona is: an expert scholar who has studied this work their
entire life, who is also a gifted storyteller, retelling the story for a modern
audience.

Key principles:
- **Faithful but not literal** — preserve meaning, tone, and narrative arc
- **Conversational and engaging** — modern turns of phrase, natural rhythm
- **Complete** — translate the entire text, don't summarize or truncate
- **Consistent** — maintain vocabulary choices and voice across chapters
- **Respectful** — handle dated cultural content thoughtfully

What to modernize:
- Archaic vocabulary → modern equivalents
- Complex/nested sentence structures → clearer modern syntax
- Outdated references → brief contextual explanations where needed
- Punctuation and formatting → modern conventions

What to preserve:
- The author's distinctive voice and style
- Famous passages and quotations
- Narrative structure and pacing
- Literary devices and imagery

## Directory Structure

```
{book}/                    # One directory per book
  env                      # Metadata (see Setup above)
  {source}.txt             # Original full text
  chapters/                # Split chapter files (000.txt, 001.txt, ...)
  manifest.json            # File -> chapter map; drives translation + assembly
  text_analysis.txt        # Translation strategy document
  agent_instructions.txt   # Standing prompt for translation subagents
  running_notes.txt        # Shared consistency ledger, updated between batches
  must_contain.txt         # Famous passages verify.py checks for
  modern_chapters/         # Translated chapters (000.txt, 001.txt, ...)
```

## Tooling

- `splitter.py` — source text → `chapters/` + `manifest.json` (heading-regex
  or legacy splits-file mode; Gutenberg stripping; oversize auto-split)
- `verify.py` — mechanical completeness/consistency checks before assembly
- `assemble.py` — `modern_chapters/` + `manifest.json` + `env` +
  `site/template.html` → `site/{book}.html`.
  `--original` assembles `chapters/` instead → `site/{book}-original.html`:
  the source text as published, for readers who want to see what the
  modernization is a modernization of. Headings come from the manifest
  (a source file opens on the chapter's contents summary, not a heading)
  and plates keep only the number the original printed under them, since
  the captions in this collection are new writing. Set `ORIGINAL_TEXT=yes`
  in `env` to cross-link the two pages. Live for the seven Royal
  Institution lecture volumes.
- `build_ebook.py {book} --original` — the same companion edition as an
  epub, into `{author}_{work}-the-original-text.epub`. Three things beyond
  the page build: the uid gets `#original-text` so the two editions are
  distinct works to a reader's library (and so `assemble.find_epub` can
  tell them apart); `dc:title` gains `: The Original Text`, which is what
  makes `se create-draft` name the build directory distinctly and what the
  cover and titlepage then render; and the imprint and colophon say the
  text is reproduced unmodernized rather than retold. The long description
  keeps the book's own first paragraph — it describes the book, not the
  retelling — and replaces the rest.
- The originals are deliberately NOT in the RSS or OPDS feeds: they are the
  same book, not a new one. They are reachable from the index and from each
  book page.
  TWO TRAPS. (1) `assemble.find_epub` must match on `dc:identifier`, NOT
  `dc:source` — both editions cite the same repo directory in dc:source, so
  matching that hands every modern page the original-text epub. (2) `se
  typogrify` unescapes `&lt;`, `&#x3C;` and `&#60;` alike into a bare `<`.
  The modern build refuses to proceed and asks for a rewording; the original
  build cannot reword its author, so it re-escapes after typogrify.
- `legacy/` — the original API-based batch translator and prompt templates,
  plus old book-specific assemblers. Reference only; see `legacy/README.md`
  (note: their `max_tokens` settings truncate full chapters).

EVERY BOOK NEEDS A REAL manifest.json, and the fallback is not a safe
default. With no manifest, `assemble.load_manifest` gives every file its
own section and `strip_front` takes the FIRST LINE as the heading. That
is right when the line is a heading and silent data loss when it is not,
and it is invisible to every check in the toolchain: verify.py compares
`chapters/` with `modern_chapters/`, and the damage happens downstream of
both, at render time. Six books were repaired in August 2026 (dialogues,
democracy, democracy2, descartes, wealth-of-nations, two-treatises) and
the same three defects ran through all of them.
  1. A MECHANICAL MID-CHAPTER CUT OPENS ON A SENTENCE, and that sentence
     was being set as a contents entry instead of as text — 5 in
     democracy, 9 in wealth-of-nations, 2 in democracy2. Group the file
     as a later part of the chapter it continues, so its prose survives.
     The signal is free: a SOURCE file that also opens on prose is a
     mechanical cut, and a source that labels its own pieces ("Chapter
     VIII: The Federal Constitution—Part IV") makes the whole grouping
     derivable. Read the source heading as the first PARAGRAPH, not the
     first line — four parts of one Tocqueville chapter wrap onto a
     second line and all four came back as "part 1 of 4".
  2. A "Part <Roman>:" LINE IN A FILE'S FRONT MATTER IS DELETED.
     strip_front skips anything matching PART_LINE (`^Part [IVXLC0-9]+:
     \S`) before the heading AND after it, since a translation may write
     its own divider on either side. Descartes lost all four Parts of the
     Principles of Philosophy that way — "Of the Principles of Human
     Knowledge" appeared nowhere on the shipped page — and Smith lost two.
     WORD FORM ("Part One: ...") does not match the pattern and is the
     house style for cross-references anyway. Sweep for it after any
     illustrated or multi-part book: every page, every file's first six
     lines.
  3. A REPEATED HEADING IS A REPEATED ANCHOR. Six "CHAPTER I." in
     democracy2, nine "MEDITATIONS ON THE FIRST PHILOSOPHY" in descartes
     — every one of them a link to the first of its kind.
Titles the batches disagree about are the visible symptom, and worth
normalising while you are there: the five Books of the Wealth of Nations
used five conventions, and Tocqueville's four tomes alternate ALL CAPS
with sentence case. Arabic "Chapter N: Title" is what `assemble.CHAP_LINE`
recognises, which is what sets a chapter as an `<h3>` inside its Book
rather than as a top-level section. Each repair lives in `{book}/retitle.py`,
kept alongside `prep.py` so the work is repeatable.

Claude Code does the translation work directly — reading chapters,
orchestrating translation subagents, and writing the output files. The API
scripts are not part of the current workflow.

## Books Completed

See `site/index.html` for the live list. As of June 2026: The Decameron,
Plato's Dialogues, The Prince, Candide, Meditations, Flatland, Common Sense,
The Federalist Papers, Democracy in America (two passes — English and from
the French), Progress and Poverty, The Wealth of Nations, Essay on the
Principle of Population, Descartes' Philosophical Works, Commentaries on the
Gallic War, On the Origin of Species, Herodotus' Histories, History of the
Peloponnesian War, Two Treatises of Government, Leviathan, The Social
Contract, Lucian's True History, More's Utopia, and Montaigne's Selected
Essays (23 essays + preface; the Apology for Raymond Sebond, Upon Some
Verses of Virgil, Of Vanity, Of Physiognomy, and Of Presumption remain
untranslated — candidates for a second volume), the Enchiridion,
The Way to Wealth, Xenophon's Memorabilia, Cicero's On Duties
(translated from the Latin; see de-officiis/ for the Latin-source
pipeline pattern — chapters/ holds the original, reference/ a
public-domain English crib, and verify runs with ratio bounds 1.0–1.8),
Franklin's Autobiography (see autobiography/prep.py for the
Standard-Ebooks-XHTML source pattern), the Tusculan Disputations
(from the Latin, tusculan/ — The Latin Library as source), and the
Nicomachean Ethics (ethics/ — locked-glossary pattern for
terminology-heavy works).

The "Founders' Library" push (July 2026) is COMPLETE: all 13 works of
the founding generation's shared bookshelf (see the 2026-07-22 DEVLOG
entry), including Seneca's complete Moral Letters, Plutarch's Roman
Lives (5 lives), and Cato's Letters (18 selected) — the last three
sourced from Wikisource via seneca/prep.py's MediaWiki-API pattern.

Also complete: Theophrastus' Characters (theophrastus/ — thirty comic
sketches, from the Greek) and Galileo's Dialogue Concerning the Two
Chief World Systems (galileo/ — the project's first from-the-Italian
volume; see prep.py's Wikisource-HTML pattern and its five source-
cleanup passes. NOTE: dialogue speaker tags must be Title-Case, not
ALL-CAPS — assemble.py reserves all-caps lines for section headings).

The project's first NOVEL and first from-the-French volume: Verne's
Twenty Thousand Leagues Under the Sea (twenty-thousand-leagues/ —
complete, unabridged, from the Gutenberg French #5097; 49 chapter
files, 2 split chapters, "Part Two" divider; see prep.py for the
two-line-heading + dual-TOC + chapter-restart pattern). Kicks off the
"Verne recovery project" (recovering the books the Victorian
translations cut ~20% and botched). Note: FR->EN narrative prose runs
near 1:1, so verify with --min-ratio 0.9 --max-ratio 1.5 and tell
agents NOT to pad; keep Verne's science/dates as written (no silent
corrections); Conseil addresses Aronnax as "Master", everyone else
"Professor".

Second Verne / second from-the-French novel: Around the World in Eighty
Days (eighty-days/ — 37 chapters, ~71k English words; the comic-
adventure register). Drop Verne's franc-conversion parentheticals of
sterling amounts (English readers don't need them); keep standalone
franc/dollar figures that are real detail. Reconcile Verne's internal
self-contradictions (a date given two ways for the same event) but keep
his one-off date-slips.

Third Verne / third from-the-French novel, completing the from-the-
French Verne trilogy: A Journey to the Center of the Earth (journey-
center-earth/ — 45 chapters, ~72k English words; the wonder-and-descent
register). Complete/unabridged from Gutenberg French #4791. The
SIMPLEST prep pattern yet: Verne titles chapters by lone Roman numeral
only (no descriptive titles), so prep.py's HEADING regex is just
`^[ \t]*([IVXLC]+)[ \t]*$` and manifest titles are generated "Chapter
N" (1–45); no oversize splits. Verify --min-ratio 0.9 --max-ratio 1.5
(landed 1.07). Voice locks: Professor (Otto) Lidenbrock (crackling/
imperious), Axel (narrator, wry/fearful-growing-braver), Hans (silent
Icelandic guide, tags kept+glossed as Verne glosses), Graüben (keep
Verne's ü). English honorifics (German setting) EXCEPT "Monsieur"
retained for French naming of real historical figures in scientific
asides (Humboldt, Milne-Edwards). Keep the runic cryptogram + Latin
solution verbatim (must_contain checks them). toise->"fathom". Place/
coinage locks emerged mid-book and were normalized: "the Lidenbrock
Sea," "Port Graüben" (not Port-Graüben), "Axel Islet" (not Island),
"Cape Saknussemm," "Hansbach," "surtarbrandur/fossil wood," "guncotton"
(fulmi-coton). TYPOGRAPHIC DEVICES preserved through assembly: Verne's
dot-row elisions (whispering-gallery lag ch 28; storm's fractured diary
ch 35) render as literal dot-paragraphs; the runic-initial facsimile
`* ᛐ * ᚼ *` does NOT trip assemble.py's HR_LINE regex (glyphs between
the asterisks), so it survives as a paragraph. Cover: Riou's 1867
granite-wave engraving (Commons "Voyage au centre de la Terre 1867
(140965384).jpg", crop "1231x1981+494+701" — the numbered 1867 scans
are full book-PAGES with in-text engravings, so a crop is required to
isolate the plate from the surrounding French text).

Ovid's Metamorphoses (ovid/ — the 40th book; the from-the-Latin
mythology anthology). All 15 books, ~131k English words, from the
LATIN (The Latin Library) with Henry Riley's 1851 prose as a per-file
crib under reference/ (the de-officiis Latin+crib pattern). prep.py's
key trick: Riley tags every segment with its Latin line-range ("FABLE
I. [I.5-31]"), so it slices the Latin by those ranges and pairs each
episode's crib to the same verses; handles compound "FABLES I. AND II."
headings, cuts parts at episode boundaries before overshooting, and
line-splits indivisibly-huge episodes. Verify --min-ratio 1.4
--max-ratio 2.4 (landed 1.68; Latin verse is very compressed, so this
runs much higher than the FR/IT prose books — do NOT reuse the 0.9–1.5
Verne bounds). VOICE: vivid modern PROSE that MATCHES OVID'S REGISTER
PER TALE (cosmic grandeur / tender pathos / real horror / sly comedy) —
never flatten the poem; render transformations with full physical
precision; handle the sexual violence with gravity, never sensationalize.
KEY CONVENTION (locked in running_notes): a LONG embedded tale/song
(Orpheus's song, the Muses' contest, Pythagoras's ~400-line discourse,
Aeneas's nested wanderings) renders as PRIMARY NARRATION — no enclosing
quotes around the whole tale; reserve quotes for framing remarks and
character dialogue, single quotes for dialogue nested inside. Names use
the familiar forms; resolve Ovid's cult-title periphrasis to plain names.
Epitaphs/inscriptions and the hyacinth's "AI, AI" stay mixed-case (never
all-caps — assemble.py reads an all-caps line as a heading). Cover:
Waterhouse's "Apollo and Daphne" (1908), Commons "Apollo and Daphne
waterhouse.jpg", crop "860x1219+38+0" (light width-crop to cut aspect
stretch without clipping the figures). NOTE: files 013–029 were
translated directly by the orchestrator after hitting the 200-subagent
session cap mid-book — the shared-ledger pattern kept the voice identical
across the subagent/direct boundary. For a multi-book push, raise
CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION at the start.

C. V. Boys' Soap Bubbles and the Forces Which Mould Them
(soap-bubbles/ — the 41st book; THE PROJECT'S FIRST ILLUSTRATED
VOLUME and its first work of popular-science lecturing). Three 1889–90
Christmas lectures on surface tension given to an audience of children;
~29k words, from Gutenberg #33370. Verify --min-ratio 0.85 --max-ratio
1.3 (landed 1.01 — EN→EN modernization runs ~1:1, since unstacking
Victorian periodic sentences costs about what cutting the
throat-clearing saves).

THE ILLUSTRATED-BOOK PIPELINE (new, reusable — Vasari, Darwin's
diagrams, any plate book):
- Gutenberg's HTML edition carries the plates that the plain text drops;
  they were copied wholesale to `site/images/{book}/figNN.jpg`.
- Figures ride through the pipeline as PLAIN-TEXT MARKERS, so
  chapters/ and modern_chapters/ stay text files: prep.py emits
  `[Figure 22]`, the translation writes `[Figure 22: caption]`.
- `env` gains `FIGURE_DIR=images/soap-bubbles`. assemble.py renders a
  marker paragraph as `<figure><img><figcaption>`, reading intrinsic
  width/height out of the JPEG (so a 66px-wide plate is not stretched
  and the page does not reflow while loading). build_ebook.py does the
  same into the SE draft and copies the plates to src/epub/images/,
  where `se build-manifest` finds them by itself.
- verify.py check 6: the set of figure markers in a modern file must
  match its source file exactly, and markers are excluded from the word
  counts so captions don't inflate the ratio. A silently dropped plate
  is the illustrated analogue of silent summarization.
- CAPTIONS ARE NEW WRITING. The 1890 original captions every plate
  "Fig. 22." and nothing more; the modern edition writes a descriptive
  one-liner for each from the adjacent prose. This is the single
  biggest improvement over the original. Look at the plate before
  captioning it — fig6 turned out to have two toy passengers and a sail
  (Boys built Lear's Jumblies for real), and `fig39b` is not a figure at
  all but the SCALE BAR belonging to Fig. 39, so it is emitted
  caption-less right after it.
- Boys' fold-out Fig. 35 (the thaumatrope) lived at the END of the 1890
  book behind a marginal note; prep.py moves it inline to where it is
  discussed, and the cross-references were rewritten to point at the
  Practical Hints section instead of at page numbers.

VOICE: live demonstration in the continuous present ("I am now dipping
it in the water") — never convert his demonstrations into textbook
statements; keep every "I want you to notice" and "you can try this at
home". Keep "elastic skin" as the governing metaphor (introduce
"surface tension" exactly once, in 001) and keep every number and ratio
exactly (4½ diameters, 3 1/7 diameters, 3¼ grains to the inch). Keep
the dated claims as HIS claims — the Rayleigh account of why
thunderstorm raindrops are large is not the modern one, and gets no
correction. Quoted verse (Lear's Jumblies, the Simple Simon couplet)
and Proverbs 23:31 KJV stay verbatim.
THE APPENDIX: "Practical Hints" is a third of the book — translate it
whole; it is the DIY invitation the lectures existed for. Boys' recipes
stay as written, with sparing `[Modern note: ...]` annotations (nine in
all) for obsolete materials, his genuinely hazardous reagents (carbon
disulfide, ether, mercury, molten wax — nobody flagged these in 1890),
and a working modern bubble mixture. Its `_Italic Subheadings._` become
plain title-case lines, which assemble.py renders as h4, and part
splits are forced onto those boundaries so no recipe is cut in half.
GOTCHA FIXED IN SHARED CODE: assemble.py's `strip_front` used to
`.strip()` the body, which ate the leading indentation of a chapter's
FIRST paragraph — so a file opening on verse or an outline lost its
`<pre>`. Now trims blank lines only. This also made two chapter-summary
blocks in democracy2 and the cast lists in dialogues render
consistently with their siblings.
ANOTHER GOTCHA: a bracketed aside like "(Note: For particulars see the
Philosophical Magazine, September 1890.)" is read as a SUBHEADING —
short, majority-capitalised, no terminal period after the bracket. End
such notes with a plain period ("Note: ... 1890.").

Faraday's The Chemical History of a Candle (candle/ — the 42nd book;
the six Christmas 1860–61 lectures at the Royal Institution, plus the
separate Lecture on Platinum this edition appends). ~41k words from
Gutenberg #14474. Verify --min-ratio 0.85 --max-ratio 1.3 (landed
0.99). The second book in the Royal Institution Christmas Lecture
tradition after soap-bubbles/ — read that text_analysis first, the
register carries over almost entirely.

TWO-SOURCE PREP (new pattern): Gutenberg's transcription of the Candle
keeps all 38 illustration CAPTIONS but none of the woodcuts —
pg14474-h.zip contains exactly one image, the cover. The plates live on
Wikisource/Commons instead, so prep pulls TEXT from Gutenberg and
FIGURES from Commons, matched by number. Watch the Commons naming: figs
1–35 are "Chemical History of a Candle Figure01" (zero-padded, no
space) but 36–38 are "Figure 36" (space, no padding), because the
Platinum lecture is a separate Wikisource page. Always check every
prospective book's `-h.zip` for image files BEFORE planning it.
PNG PLATES forced a toolchain generalization: assemble.py and
build_ebook.py now resolve a plate's extension (jpg/png/gif) instead of
assuming .jpg, and image_size() reads PNG's IHDR as well as JPEG's SOF.
NOTE: `se lint` rejects a PNG with no transparency (f-019) — convert
those plates to JPEG; the extension resolver picks them up with no
other change. Four of the 38 needed it.
EDITOR'S NOTES: Crookes's 19 notes sat at the back behind print-page
headings ("Page 186."). prep.py cuts them loose and inlines each as an
"Editor's note: ..." paragraph after the paragraph that cites it.
Translate them in CROOKES'S register — dry, third-person, technical —
never the lecturer's voice. Faraday writes "glycerin", Crookes writes
"glycerine": do NOT harmonize, the spelling marks the seam.
SOURCE DEFECT FOUND: Lecture V anchors note 16 as "[14]", so note 14
was inlined twice and note 16 (which names the unnamed oxygen test gas)
never appeared. prep.py's SOURCE_FIXES corrects it and raises SystemExit
if the misprint ever vanishes from the source. Mechanical checks CANNOT
catch this class of bug — a correctly-formatted note on the wrong
sentence passes ratio and figure-parity. Read the notes in context.
VOICE: warmer than Boys — "my boys and girls", "I claim the privilege
of speaking to young people as a young person myself", constant
self-interruption to admire something. Keep the stage directions in
square brackets where they fall. NOMENCLATURE IS LOAD-BEARING: he
reasons with "carbonic acid" and "carbonic oxide", so keep his term
primary and gloss the modern name exactly once (carbon dioxide, carbon
monoxide, aqua regia, hydrochloric, ethanol). Keep every number as
printed; two garbled ASCII tables (the 1:8 water diagram, the
atmosphere's bulk/weight analysis) were rebuilt as indented blocks, and
the water diagram MOVED UP to the sentence that references it.
Faraday's On the Various Forces of Nature (forces/ — the 43rd book;
the Christmas 1859–60 course, the year BEFORE the Candle, plus the
appended "Light-house Illumination" address of 9 March 1860). 15 files,
~35k words from Gutenberg #52293 (NOT 61k — that count includes the
publisher's advertisements bound in at the back, dropped at "THE END.").
Ratio 0.98. Crookes edits and annotates this one too.
COMPOUND PLATES (new, generic): Victorian printers put several numbered
figures on ONE woodblock, so 50 plates carry 59 figures. Markers and
filenames now take hyphenated ids — [Figure 15-16-17] / fig15-16-17.jpg
— and assemble.figure_label() renders "Figures 15, 16 and 17". A
compound caption MUST cover every figure on the block, in order, saying
which is which (left/right/above/below): the prose refers to them
separately and the reader has only one image to find them in. LOOK at
the plate first.
CRITICAL: the text's illustration grouping does NOT match the plates'
grouping, so prep.py drives markers from the FILES, not from the
"[Illustration: ...]" lines. fig15-16-17 is one plate but two text
markers (emit once, drop the second, or the image appears twice);
figures 18 and 19 are two plates under one marker (emit both); and
fig29 has no marker at all — it is referenced only in lower-case prose
as "(fig. 29)", and its position was confirmed against the Gutenberg
HTML edition.
SAME TRAP AS THE CANDLE: lecture headings appear THREE times — in the
contents, in the body, and again as section headers inside the NOTES.
Anchor on the LAST occurrence before "NOTES." (find_last_line).
Also: a note runs until the next note OR the next "LECTURE" header, or
the per-lecture header gets swallowed onto the end of a note.
VOICE: as candle/, but Lecture One opens with Faraday apologising that
illness twice postponed the course and that he may manage "only a few
words" — render plainly, no softening. Lecture Six closes on As You
Like It ("tongues in trees, books in the running brooks"), set as verse
and pinned by must_contain. The LIGHTHOUSE ADDRESS is a separate adult
occasion — a Trinity House report, plainer and more official; do not
import Christmas-lecture warmth into it.
Cover: Church's "Aurora Borealis" (1865), Commons "Aurora Borealis by
Frederic Edwin Church.jpg", crop "1802x2704+1099+0" — magnetism written
across the sky, which is the last lecture's thesis. (Balke's aurora was
the runner-up but reads too dark at thumbnail size.)

Cover: Blaikley's painting of Faraday's own 1855 Christmas Lecture,
Commons "Professor Faraday lecturing at the Royal Institution, 27th
December, 1855 RIIC 0006 20110213 BAL EP.jpg", crop "1847x2771+1500+86"
(a 2:3 slice out of a landscape painting, centred on Faraday at the
bench).

Fleming's Waves and Ripples in Water, Air, and Aether (fleming/ — the
44th book; the Christmas 1901 course at the Royal Institution, the
FOURTH RI Christmas Lecture volume after soap-bubbles/, candle/ and
forces/). 32 files, ~77k words from Gutenberg #71757, ALL 87 PLATES.
Ratio 0.95 — verify with --min-ratio 0.85 --max-ratio 1.3.
Fleming was about to invent the vacuum tube and was already the leading
authority on wireless; chapter six reports Marconi's Atlantic aerial as
current news.
THE VERNE RULE IS THE WHOLE BOOK: the aether is asserted as established
fact ("suns and stars float in an illimitable ocean of aether"). Render
it as HIS claim, unhedged, with no editorial wink. By contrast archaic
GAS NAMES are just vocabulary — carbonic acid -> carbon dioxide,
carbonic oxide -> carbon monoxide, silently. Distinguish dated claims
(keep) from dated words (modernize).
FOUR DEFECTS THE MECHANICAL CHECKS CANNOT SEE — every one found by
reading, not by verify.py:
  1. An UNNUMBERED plate breaks id assignment twice over. The middle-C
     clef is a BARE "[Illustration]" with no colon, so a regex demanding
     the colon skipped it AND left its "music" id free for the next
     unnumbered block to claim — which put a treble clef where chapter
     six's line of Morse code belonged. ILLUS now makes the caption
     optional; a captioned plate with no number is DROPPED rather than
     allowed to take a spare id.
  2. A cross-reference to a plate that carries no number of its own goes
     astray: the gamut-of-aether-waves chart is cited as "(see Fig. 77)",
     which is the paraffin prism. Redirected to Figure 80.
  3. Arithmetic in tables. 495x3 is printed 1475 (corrected to 1485);
     the ice prism's refractive index is 1.83 in the body and 1.88 in
     its own footnote (harmonized to 1.83, which is what the formula
     gives). CHECK EVERY TABLE THAT CLAIMS TO BE COMPUTED.
  4. Numbers spelled as words ("thirty-six hours" for "36 hours") pass
     the word-ratio, the figure parity and must_contain alike. Add a
     numeric-token check per file — see the recipe in
     fleming/running_notes.txt. It is cheap and it is the only guard
     against silent loss of a measured value. USE IT ON EVERY BOOK.
     COUNT, DO NOT USE A SET (the hume lesson): a set cannot see a
     dropped duplicate, because the surviving occurrence covers for the
     lost one. Counter subtraction is the whole fix. And never test
     `token not in modern_text` — that is a substring search, so "5"
     counts as present because some "1500" contains it.
     BUT MEASURE WHAT IT CAN ACTUALLY SEE BEFORE COUNTING IT AS
     PROTECTION (2026-08-22). THE CHECK ONLY HAS PURCHASE WHERE THE
     SOURCE USES DIGITS. Burton's Nights contains NOT ONE DIGIT in 72
     source files — he spells every number out — so nights/check.py had
     been reporting "numerals clean" since the day it was written while
     testing precisely nothing. Grimm has six numeral tokens in all,
     across 3 of 85 files, one of them already-exempted page furniture.
     Both now say so in place. A check that cannot fire is worse than no
     check, because it is counted as coverage. What actually guards
     numbers in the Nights is its night-number SEQUENCE check, which
     parses the spelled-out ordinals into integers — and that one has
     caught real defects ("the Five Hundred ante Seventy-fifth Night").
     Where a source spells its numbers out, that is the shape to build.
THE APPENDIX TRAP (generic): back matter with no CHAPTER heading gets
swept into the last chapter's final part, where it ships with no TOC
entry — while body notes still cite it by name. prep.py peels it off
AFTER the chapter split, never before: splitting the chapter without
its 1420 words changes nparts 6 -> 5 and moves every boundary, which
would invalidate translations already done. Its print-page references
("NOTE A (see p. 21)") are meaningless in a reflowable edition and were
replaced with descriptive titles.
INDENTED RUNS MUST STAY ONE BLOCK: normalise() emitted one paragraph
per indented line, so assemble.py opened a separate <pre> per line and
its 2em bottom margin strewed the 26-letter Morse alphabet down half a
page and pulled two-line equations apart. Group consecutive indented
lines. DEDENT such blocks, never strip per line — the Morse for "How
are you?" sets its letters under their own groups of dashes, and
stripping slides the rows out of register. (Worth auditing the other
illustrated books for the same thing.)
VOICE: a working engineer talking to teenagers — everything is a thing
on a table, and he says "you see" because they can. Keep the
demonstrator's present tense. Fleming's own notes are first person;
where the body drops into "The author had an instance of this before
him", restore first person — same man, same lecture.
Cover: Hokusai's "The Great Wave off Kanagawa" (1831), Commons "File:
Great Wave off Kanagawa2.jpg", focus_x 0.43 — a 2:3 slice of a
landscape print keeping the crest, the claw and Fuji. Not period-apt
and deliberately so: the book's thesis is that one wave is every wave.

Sir Robert Ball's Star-land (ball/ — the 45th book; the FIFTH and last
Royal Institution Christmas Lecture volume, after soap-bubbles/,
candle/, forces/ and fleming/). The Christmas courses of 1881 and 1887
worked up into a book: six lectures from the sun out to the nebulae
plus a closing chapter teaching the constellations. 36 files, ~96k
words, 94 plates, from Gutenberg #60318. Ratio 0.95 (--min-ratio 0.85
--max-ratio 1.3).
IT IS THE 1899 REVISED EDITION, not the 1889 first — caught only
because file 004 mentions the great sunspot of September 1898. Ball
updated throughout (Saturn's ninth satellite, "(1899)" as the present
year, a confident forecast of the 1899 Leonid shower). env DATE is
1889/1899.
THE CLEANEST SOURCE OF THE FIVE: no footnotes at all, and body
headings sit at column 0 while the contents indents them, so a
column-anchored regex separates them — none of the find_last_line
contortions candle/ and forces/ needed. prep.py REFUSES TO RUN unless
every plate on disk is placed exactly once; that assertion is what
turned fleming/'s two figure traps into non-events here (the
frontispiece is a bare uncaptioned "[Illustration]", and figures 35
and 64 print their number AFTER the plate's own sub-labels, "Partial.
Annular. FIG. 35."). Figures 29 and 30 share one plate — compound id
from forces/.
CAPTIONS COME FROM THE SOURCE for the first time. Ball captioned his
own plates and the captions are frequently the joke ("Two Eyes are
better than One", "This is what we wanted the Cards for"), so they
ride through into chapters/ as [Figure N: caption] to be MODERNIZED,
not replaced. Keep his phrasing as the first clause and extend with a
short descriptive one — the caption is also the epub's alt text.
INDENT THRESHOLD: normalise() now preserves a run of lines indented by
TWO spaces, not four. The concluding chapter's six astronomical tables
are indented by two, and at the old threshold every one of them was
collapsed into running prose ("Mercury | 35.9 | 87.969 | 2,992 |
Uncertain. Venus | 67.0 | ..."). Worth checking on any book with
tables. Lowering it also fixed the postal-address block and the two
verse quatrains. Verified against the manifest: no boundary drift.
PROCESS RULE, learned on file 016: READ THE WHOLE SOURCE FILE, never a
line range. Two sed ranges stopped at line 40 and a figure marker, a
section heading and a closing paragraph were simply absent from the
translation. Figure parity caught it — but nothing would have, had the
dropped tail been ordinary prose with no figure and no number in it.
Eight print-page references were all decided IN ADVANCE and logged,
including the one that must NOT be touched: "page 123" in Lecture Five
is not a reference to this book but the telegraph-code story, where
astronomers cabled "123 degrees 45 minutes" as the 45th word on page
123 of Worcester's Dictionary — the single word "constituent". There
the page number IS the message.
VOICE: Ball talks TO children and never down to them; he is the
funniest of the five and needs LIGHT work (ratio 0.95), not rebuilding.
Everything is a demonstration, and the jokes are load-bearing. 68
in-lecture section headings render as TITLE CASE WITH NO TERMINAL
PERIOD — assemble.is_subheading() rejects anything ending in ".;:,—",
so the period alone is the difference between an <h4> and a paragraph
shouted in capitals.
VERNE RULE: 1889/99 astronomy throughout, kept unhedged — volcanic
lunar craters, Lowell's canals, Venus keeping one face to the sun, the
1899 Leonid prediction (which disappointed; no note is added). Ball is
scrupulous about marking what is known versus guessed: keep that
grading exactly where he puts it.
SENSITIVE PASSAGE: Lecture Five quotes an 1833 eyewitness account of
the great Leonid shower from a South Carolina plantation — an enslaver
describing the terror of the people he held enslaved, "the negroes"
throughout. The astronomy is genuinely valuable and is why Ball quotes
it. Rendered "the enslaved people": MORE explicit, not less, since a
modern young reader would not otherwise know. Quoted in full, nothing
cut, the fear not softened.
Cover: Trouvelot's "The November Meteors" (1868), Commons "File:
Trouvelot - The November Meteors.jpg", crop "2533x3800+733+721" (the
plate only, out of a full lithograph sheet with wide margins and a
printed caption). Doubly apt: it is the shower Lecture Five is about,
and Trouvelot's drawings are reproduced inside the book as figures 18
and 20.
NOTE: `se lint` raises two [Manual Review] titlecase items wanting
"Star-Land"; the book's title is "Star-land" and they are correctly
ignored.

Silvanus P. Thompson's Light Visible and Invisible (thompson/ — the
45th book; the Royal Institution Christmas course of 1896, and the
FIFTH and last of the RI Christmas Lecture set after soap-bubbles/,
candle/, forces/, fleming/ and ball/). 30 files, ~69k words, 127
plates, ratio 0.96 (verify --min-ratio 0.85 --max-ratio 1.3). Given
thirteen months after Röntgen announced the X-ray; Lecture Six is
about nothing else and quotes the discoverer's own interview.

THE PROJECT'S FIRST OCR SOURCE — no Gutenberg, no Standard Ebooks.
Archive.org's `lightvisibleinvi00thomrich` (text + plates; `…uoft` as
a second copy for blotted cells). Four fifths of the work was making a
source worth translating. The reusable lessons, all of them invisible
to verify.py:
- PAGE FURNITURE IS INSIDE THE TEXT. Stripping a running head leaves a
  blank line, and a blank line is a paragraph break — ~330 paragraphs
  were cut in half at the page turn. Mend rule: no English paragraph
  starts in lower case, plus a dangling-word list for halves that
  resume on a proper noun. Iterate to a fixed point.
- A CELL IS NOT A PARAGRAPH. normalise()'s "drop paragraphs under three
  words" ate three whole rows out of the luminescence table and moved
  the word ratio by nothing. FIVE tables were rebuilt from page images.
  CHECK EVERY TABLE AGAINST THE SCAN.
- EVERY FRACTION IS A MEASURED VALUE AND NONE SURVIVE. ~30 of them, all
  read off the page. My contextual guesses were wrong twice (1/10000
  not 1/1000000; 1⅝ and ⅝ not 1½ and ¾). DO NOT INFER A FRACTION.
- FORMULAS AND GREEK FLATTEN TO DEBRIS, and some vanish outright,
  leaving "the formula becomes" followed by nothing. Restored via
  thompson/appendix_fixes.py — a separate module of (garbled, correct)
  pairs, each of which must still match or prep stops. REUSE THIS.
- FOOTNOTES THAT RUN OVER A PAGE BREAK SWALLOW BODY SENTENCES; seven
  here, six reassembled by hand.
- A CAPTION LINE AND A SENTENCE OPENING ARE THE SAME REGEX. "Fig. 115
  gives a front view…" lost its subject. The tail decides: upper case
  = caption, lower case = sentence. Fixed generically in normalise().
- "Fig. 118" split by a page break reads as a caption for FIG. 1 — the
  ripple-tank plate landed in Lecture Five and the reference died.
  Mend split figure numbers BEFORE the caption pass.
- A SUB-FIGURE LETTER IS NOT A MISPRINT. "Fig. 121b" scanned as
  "121^"; I "corrected" it to 122 and was wrong — two paragraphs later
  the text uses 122 for something else. A conflict between references
  is the signal; LOOK AT THE PLATE.
ONE REAL ERROR IN THOMPSON'S PRINTING: the wave-length table gives the
A line as 29.28 millionths of an inch where 75.94/2.54 = 29.90. All 55
rows checked against both relations the table asserts about itself;
only that one fails, and the frequency cell says which figure is wrong.
Corrected with an editor's note.
VOICE: the REFORMER of the five lecturers. He says outright that the
orthodox teaching of optics is "fundamentally wrong" and that hard
WORDS, not hard ideas, are what make science look difficult — a
sentence that is this project's thesis in his own 1897 words. Wave-
fronts, never rays. The ether is real and unhedged (the Verne rule);
kathode -> cathode and reflexion -> reflection are silent vocabulary.
TOOLCHAIN, both fixed in shared code:
- `se typogrify` UNESCAPES `&lt;` into a bare `<` and breaks the XHTML
  for every later step; build_ebook.py now refuses an escaped `<` and
  says why.
- `epubcheck` here reports PKG-021 "Corrupted image file" for EVERY
  image including se's own cover, and for books already published from
  this repo (star-land fails identically) — a local Java image-reader
  fault. build_ebook.py tolerates that one code, verifies images with
  PIL, and builds without --check; anything else still fails.
Cover: Joseph Wright of Derby's "An Experiment on a Bird in an Air
Pump" (1768), Commons "An Experiment on a Bird in an Air Pump by
Joseph Wright of Derby, 1768.jpg", crop "1919x2878+922+0" — a
demonstrator, a glass receiver, an air pump and an audience of
frightened children.
PLATES RE-CUT AND CLEANED (thompson/replate.py, and the pattern to
reuse on any book whose plates come off a page scan):
- ABBYY's Picture box fits the ENGRAVING, not the drawing, so plates
  arrive CLIPPED — fig 3 lost the entire barrier-and-slit its
  wavefronts diffract through. Do not re-cut with a fixed margin; GROW
  EACH SIDE UNTIL IT REACHES WHITESPACE (scan outward, stop at the
  first run of blank lines, back off by a pad). Self-limiting on a
  plate that was never clipped. Seven needed a hand-set cap where the
  search walks into body text; a negative cap moves an edge inward,
  for boxes that took in a running head to begin with.
- SCANNED PAPER IS DIRT ON A WHITE PAGE — 127 patches of cream, each
  with its own cast. Map DARKNESS TO ALPHA over pure black: the ink
  survives, anti-aliased as the scan had it, and the paper goes.
- READ "PAPER" AT THE 99TH PERCENTILE, NOT THE MODE. A fifth of these
  plates are printed white on black, where the mode IS the ink; at the
  mode the black ground lands at 0.9 alpha and the text on the back of
  the leaf shows through it as a legible ghost. At the 99th the one
  mapping handles both polarities with no special case.
- ALPHA, NOT A THRESHOLD: a bilevel threshold destroys the halftones
  (the Röntgen plates, the ripple tank).
- QUANTISE THE ALPHA (16 levels line art, 48 halftone). The scan's
  noise gives every stroke a fringe of unique values PNG cannot
  compress; rounding halves the files and is invisible.
- build_ebook.py gives a book with transparent plates
  `figure img{background:#fff}` in local.css — black ink on nothing is
  invisible in a reader set to a dark theme.
- THE SE DRAFT IS REUSED BETWEEN RUNS and copy_figures used to copy
  only INWARD, so changing 127 JPEGs to PNGs left both in the draft and
  `se build-manifest` listed all 254: the epub doubled to 51 MB with
  every plate in it twice. It now sweeps whatever is not in the source
  directory. GENERAL SHAPE: any build step that writes a SET of files
  without owning the set will eventually ship something stale — the
  same bug left figfront.jpg in Tyndall's epub and 044.txt in its
  chapters/.

John Bunyan's The Pilgrim's Progress (bunyan/ — the 46th book, and the
project's first from Standard Ebooks XHTML since autobiography/). Both
parts complete: Christian's road (20 files) and Christiana's (18), 39
files, 108k words in and 112k out, ratio 1.03. Verify with
--min-ratio 0.85 --max-ratio 1.3.

THE JUSTIFICATION IS UNUSUAL AND WORTH KEEPING IN MIND FOR OTHER
CANDIDATES: this book is not hard, it MISLEADS. Standard Ebooks scores
it at reading ease 74 ("fairly easy") — Bunyan was a tinker writing
deliberately plain English for people like himself and his sentences
are short, so there is nothing to unstack. But "conversation" means
CONDUCT (11x in Part One), "want" means lack, "prevent" means go
before, "conceit" means opinion, "let" means hinder, "crazy" means
decrepit, "professor" means one who professes faith. A reader trips on
"hath" and knows it; they read "his conversation gives his profession
the lie" and walk away confidently wrong. Difficulty you can feel is
the weaker case for a retelling than difficulty you cannot.

STRUCTURE: Bunyan wrote one continuous dream with NO chapters, and SE
preserves that — part-1.xhtml is a single section of 924 paragraphs.
The division is imposed on his own scene-transition formula ("Now I saw
in my dream, that...", "I beheld, then, that..."), which is a chapter
break in seventeenth-century dress. prep.py pins each boundary to a
distinctive substring and ASSERTS it matches exactly one paragraph.
No file exceeds 7k words, so no oversize splits at all.

THREE SILENT TRAPS, none visible to verify.py:
- SE SETS A NO-BREAK SPACE INSIDE ABBREVIATIONS ("Mrs.\u00a0Timorous").
  Every chapter anchor written with an ordinary space matched nothing
  and the division came out empty. Normalise \u00a0 and \u202f in
  clean(). Applies to ANY Standard Ebooks source.
- "Christ." IS CHRISTIANA, 56 times in Part Two. Read as Jesus it
  produces fluent, confident, entirely wrong dialogue. The distribution
  is clean and can be relied on: "Chr." = Christian, Part One only;
  "Christ." = Christiana, Part Two only. Matt./James./Sam./Joseph. are
  her four sons, not books of the Bible.
- KILL NOTEREF ANCHORS AS ELEMENTS, NOT TAGS. Strip tags naively and
  `<a>41</a>` welds a bare 41 onto the preceding word — "the Slough of
  Despond,41 his labourers" — which reads as a number in the text and
  passes every mechanical check this project has.

OFFOR'S 1,010 COMMENTATOR NOTES ARE NOT TRANSLATED. At 500 KB the
endnotes file is larger than either part of the book, and they are
Victorian devotional commentary by men who are not Bunyan. They go to
reference/notes.txt as a crib, drawn on only where a modern reader
genuinely cannot follow (the soap-bubbles annotation rule). Exactly one
bracketed note in the whole volume: that the "den" of the first
sentence is Bedford jail.

SHARED FIX — assemble.is_subheading(). It read 45 short spoken
questions as section headings, because a speaker tag supplies one of
the capitals that make a line count as majority-capitalised and "?" was
not a disqualifying terminator. THE OBVIOUS FIX REGRESSES TWO BOOKS:
adding "?"/"!" outright demoted real section titles in Leviathan
("Could Church Councils Make Scripture Law?") and The Social Contract.
The rule is therefore narrow — a "?"/"!" line is disqualified only if
it ALSO carries a speaker tag or runs to more than one sentence.
Dialogue does one or the other; a heading does neither. Re-tested
across all 29 assembled books: only bunyan changes, plus
journey-center-earth, where "Climb, obviously! Always climb!" stops
being a heading. ALWAYS RE-ASSEMBLE EVERY BOOK AND DIFF BEFORE
CHANGING is_subheading OR normalise.

MANIFEST SHAPE: one entry per FILE with REQUIRED "part"/"of" keys, not
one per chapter with a files list. assemble.py indexes m["part"]
directly. Checksum chapters/ before and after any prep re-run to prove
no boundary moved.

STALE SE DRAFT — GENERIC, AND IT BIT HERE. rebrand.py installs the
long description by substituting the LONG_DESCRIPTION placeholder that
`se create-draft` writes. build_ebook.py only creates the draft `if not
dest.exists()`, so on the SECOND build the placeholder is already gone,
the substitution matches nothing, and THE EPUB SHIPS THE OLD METADATA
WITH NO WARNING. Editing ebook_meta.json and rebuilding is not enough:
rm -rf build/ebooks/{slug} first. Same family as the stale-image bug in
copy_figures.

VOICE: far more colloquial than the book's reputation. Pliable whines,
Worldly-Wiseman patronises, Talkative is unbearable, Giant Despair
takes his wife's advice, and the comedy is load-bearing — play it
straight. TWO REGISTERS, and do not flatten them together: Part One is
a man alone with his fingers in his ears; Part Two has a guide, four
sons, two weddings and a great many meals, and its whole argument is
that the weak all get across. Mr. Feeble-mind's "to run when I can, to
walk when I cannot run, and to crawl when I cannot walk" only lands if
Part Two is not pitched at Part One's terror.
THE ALLEGORICAL NAMES ARE LOCKED and pinned in must_contain — Slough of
Despond, Vanity Fair, Giant Despair, Mr. Worldly-Wiseman, Great-heart,
the Delectable Mountains. They are the book's gift to the language.
THE VERNE RULE, hard: Ignorance walks the whole road and is bound hand
and foot at the very gate and carried to hell, and the vision ends "a
way to hell, even from the gates of Heaven". Giant Pope, the anti-Roman
aside at Vanity Fair and the beast of Revelation 17 all stand as his.
No softening, no wink.
TWO RACE-ADJACENT PASSAGES, DECIDED DIFFERENTLY AND BOTH RECORDED IN
running_notes.txt. The Flatterer is "a man, black of flesh, but covered
with a very light robe", identified two paragraphs later as a fiend
transformed into an angel of light: rendered "black of body" / "the
black figure", NOT "a black man", because in modern English that names
a person's race and would misidentify the character. The Ethiopian on
Mount Charity is KEPT verbatim: it is the classical proverb for
attempting the impossible, glossed on the spot as being about the vile
person, and its whole mechanism is the man's origin — no rendering
keeps the emblem while removing it, so cutting would be bowdlerising
and a note would be the wink the Verne rule forbids.
Cover: Thomas Cole's "The Voyage of Life: Manhood" (1842), Commons
"File:Thomas Cole - The Voyage of Life Manhood, 1842 (National Gallery
of Art).jpg", crop "1684x2526+219+0" — a lone figure carried down a
dark river with hands clasped, demons in the storm and a break of light
ahead. NOTE the crop is in the coordinates of the 3840x2526 rendition
Commons actually serves, not the 5272x3468 original.
`se lint` raises s-023 wanting "Mr. Stand-Fast"; the name is
"Stand-fast", as with Great-heart and Feeble-mind, and it is correctly
ignored (compare star-land's "Star-land").

John Tyndall's Sound (tyndall/ — the 44th book, and the EIGHTH Royal
Institution volume after soap-bubbles/, candle/, forces/, fleming/,
ball/ and thompson/. Chronologically it is the FIRST: 1867, six years
after Faraday's Candle, and the book every later lecturer in the set
is imitating). 44 files, ~117k words, 187 plates, from Gutenberg
#54969 — the Collier reprint of the THIRD edition of 1875, which is
why the South Foreland fog-signal chapter is in it. Ratio 0.97
(--min-ratio 0.85 --max-ratio 1.3). Read thompson/ and candle/ first;
the register is theirs, one generation earlier.
The translation is the easy part here. EVERY defect found was of the
one class verify.py structurally cannot see: CONTENT PRESENT, IN
ORDER, AND WRONG.
FIGURE-ID COLLISIONS, TWO KINDS, BOTH SILENT (the important lesson):
  - A TRAILING LETTER IS PART OF THE NUMBER. "Fig. 94a" (Helmholtz's
    resonator) read as 94 overwrote the sonorous bell and then shipped
    twice.
  - A BOOK MAY RESTART ITS FIGURE NUMBERING. Appendix II has its own
    Figs. 1-4 and overwrote chapter one's solitaire balls, row of
    boys, Cottrell's spring model and bell-in-a-vacuum — so the first
    plates a reader sees came from the back of the book. Fixed with a
    NAMESPACED id: "app_1", which assemble.figure_label now strips
    back to "Figure 1" (a "_"-terminated prefix picks the file, the
    digits after it are what the reader sees). verify.py and
    assemble.py accept "_" in marker ids. prep.py RAISES if any id is
    ever claimed by two different plates — copy that assertion.
  FIGURE PARITY CANNOT SEE EITHER OF THESE: every marker exists and
  every marker is placed. Only looking at the plate finds them.
NESTED CONTAINERS DUPLICATE TEXT (generic to any HTML source): walk()
  visited every wrapping <div>/<blockquote> as well as its children,
  so a wrapper emitted its whole contents once per level of nesting —
  the Spenser stanza (poetry-container > poetry > stanza > line)
  FOUR times, two blockquoted letters twice each, 1,281 words in all.
  Skip a div/blockquote that contains a block-level descendant. The
  word ratio gets WORSE, not better, the more faithful the
  translation is, so nothing flags it.
FRONTISPIECE FILENAME: assemble.figure_name special-cases the id
  "front" and looks for front.jpg, so a prep that writes fig{id}.jpg
  for every id produces figfront.jpg and a broken image on the page
  AND a missing resource in the epub (epubcheck RSC-007, at the very
  end of the build). Worth sweeping every assembled page for missing
  image references after any illustrated book.
SIX MISPRINTS IN TYNDALL'S OWN TEXT, each caught by reading a sentence
  against the figure or the arithmetic it describes: the third law
  names the wrong fork; a free-free rod's tone series printed
  "1, 3, 4" for 1, 2, 3; an open pipe's reciprocals printed backwards
  as 3:2:1; the resultant-tone table labelling the ratio 2:3 "Octave"
  (it is the fifth); the major third located at c' instead of e' on
  Helmholtz's own curve; and Fig. 165 cited for the parabola of
  Fig. 177. Plus "Mr. Philip Harry's Sensitive Flame", where the
  paragraph under the heading and the index both say Barry.
QUOTED MATTER IS VERBATIM, as in the other lecture books — EXCEPT
  where the quotation's source is itself reprinted in this volume. Le
  Conte's 1858 paper is Appendix One and is also quoted in chapter
  six; the two must agree, and the modernized form governs. Every
  other quotation (Hooke, Herschel, Robison, Chladni, Abel, Arrow,
  Atkins, Kean, Arago's French, Helmholtz's German) stays as printed.
THE DEDICATION to Richard Dawes stands before the first heading in a
  box of its own, six centred all-caps lines. It falls outside every
  section (so it is dropped) and is all-caps (so a general rule would
  render it as a heading). Set as an indented block, with a source
  check so it cannot vanish unnoticed.
A CUT AFTER A SECTION HEADING IS HARMLESS — assemble.py stitches a
  chapter's parts back together before rendering, so the heading and
  its section end up adjacent again. A cut after a PLATE is not: its
  caption is written in the modern file. Do not add the heading rule;
  it moves boundaries of finished files for nothing.
CROSS-REFERENCES go to WORD FORM ("Chapter Seven", "Summary of Chapter
  One"), not the source's Roman, because the manifest heads every
  chapter that way and the reader has only the assembled page.
VOICE: the ancestor of all the others — five boys in a row standing in
  for a line of air particles, a glass tube rubbed until it shivers
  into rings, a flame that ducks at the letter S and ignores the same
  sound aimed half an inch higher. Chapter seven is unlike anything
  else in the set: months on a steamer off the South Foreland, results
  that contradict each other flatly day by day, and the ACOUSTIC
  CLOUDS that resolve them — optically clear air that stops sound
  dead, while dense fog is the best carrier of all. Keep his
  scrupulousness about what is inference and what is measurement.
Cover: Turner's "Snow Storm: Steam-Boat off a Harbour's Mouth" (1842),
Commons "File:Joseph Mallord William Turner - Snow Storm - Steam-Boat
off a Harbour's Mouth - WGA23178.jpg", crop "1252x1879+754+0" — a
steamer signalling in fog off a harbour mouth, which is chapter seven.

Lewis Carroll's Symbolic Logic, Part I (symbolic-logic/ — the 48th
book, and the third of the Carroll shelf after bunyan/ and
tangled-tale/). 41 files, ~57k words, 308 diagrams, from Gutenberg
#28696. Ratio 1.00 (--min-ratio 0.85 --max-ratio 1.3).
THE ONE BOOK WHERE THE FLEMING RULE DOES NOT REACH. Elsewhere dated
CLAIMS stand as the author's and dated WORDS are modernised silently.
Here THE WORDS ARE THE MACHINE: "Retinend" and "Eliminand" are not old
names for something logic now calls something else, they are parts
Carroll built. KEEP ALL OF HIS TERMINOLOGY and his capitalisation of
it — Premiss/Premisses (his spelling), Univ., Sorites/Soriteses,
Entity/Nullity, and the compass geography (North, South, Inner, Outer),
which are COORDINATES, not description. All the work is syntax and
signposting. The book is not hard, it MISLEADS: Victorian notation, a
diagram method that is his and nobody else's, and a vocabulary later
logic abandoned — so a reader WITH training is more lost than one
without.
THE CAPTIONS ARE THE BOOK. Every diagram carries alt text and every one
is useless ("Diagram representing all x are y" repeats the sentence
above it). A caption must say WHICH CELL HOLDS WHICH COUNTER. All 308
were opened before captioning, because the drawing convention exists
NOWHERE in the text: a Red Counter is a circle with a dot, a Grey
Counter a plain circle, and from Book Four Chapter III — where Carroll
tells the reader to switch to digits — the plates switch with him and
draw the Red Counter as the letter I.
A CAPTION ON AN EXERCISE MUST NOT PRINT ITS ANSWER. Book Eight § 3 sets
twenty marked diagrams "to be interpreted" and the source's alt text on
each IS the interpretation. Captioned by their marks instead, each
checked against the printed Answer.
FLOATED DIAGRAMS PRECEDE THE PARAGRAPH THEY BELONG TO. Figs 111/112
show the right and wrong order of laying counters; read in text order
they come out swapped and the caption then calls the tidy diagram the
mistake.
FIVE DEFECTS NO MECHANICAL CHECK CAN SEE, all in prep:
  1. A GREEDY PAGE-MARKER REGEX EATS THE TEXT'S OWN DIGITS. The marker
     is a span and the body resumes right after it, so pg\d+ swallowed
     the "4" of "4. Define Men." — 21 numbers over seven files,
     including two table cells that were answers. Anchor the digit run
     (pg\d{3}), do not use \d+. Carroll's half-pages need a trailing
     [½] too.
  2. THE NOTATION LIVED IN THE CSS. The Method of Underscoring carries
     as class="under1"/"under2"; strip tags and all 642 marks vanish,
     leaving the section that TEACHES it printing its example twice in
     identical letters. Carried through as U+0332/U+0333.
  3. THE SECTION NAME ALONE IS NOT AN ADDRESS. Eight Books means four
     "Chapter II"s. Qualify every chapter target with its Book; collapse
     two page numbers landing in one section; say "above" for a
     reference into its own section.
  4. EVERY ROW OF THE INDEX OF TABLES POINTS AT PAGE 25 (visible
     numbers right, all nine hrefs wrong), and A PAGE ANCHOR MARKS THE
     TOP OF A PAGE, NOT THE PLACE — "'Name'" indexed a chapter early.
     Resolve an index row through its own TERM anchor.
  5. 3,789 NO-BREAK SPACES survived into chapters/ because clean()'s
     replace list wrote them literally. Spell them as escapes.
TWO MISPRINTS IN CARROLL, both c-for-e, found by WORKING the Sorites:
"No a are e′" for ac′0, "No c′ are b′" for e′b′0. He also promises
eight Problems and sets nine.
FIVE EXERCISES CHANGE THEIR TERMS (racial and antisemitic Classes in
§§ 5, 7 and 9). The logic is indifferent — subscripts, Answers and
Solutions all unchanged — which is why they can go, and this is a book
for children of twelve to fourteen who are invited to manipulate these
propositions as their own. NOT the Verne rule: that protects a dated
CLAIM the author makes as part of his subject, and none of this is
Carroll's subject. The Bunyan-Flatterer precedent governs. All listed
in running_notes.txt with the four neutral references that are KEPT.
SHARED CODE, three fixes:
  - verify.py's FIGURE was ANCHORED TO A WHOLE LINE. A marker can be one
    CELL of a table row; anchored, those stayed in the word counts and
    were invisible to figure parity. Also: files under 20 words skip the
    ratio check.
  - THERE ARE TWO BODY RENDERERS AND BOTH HAD THE SAME BUG. assemble.py
    set any indented block as <pre> and build_ebook.py set it as lined
    matter, so 248 of 308 plates printed as literal "[Figure 57: ...]"
    on the page AND in the epub, where they sat in the package
    referenced by nothing. An indented block CARRYING a marker now
    renders as a table in both (caption -> img alt); blocks without one
    are untouched, so no other book moves. NOTHING CATCHES THE EPUB
    HALF: `se build-manifest` lists what is on disk rather than what is
    used, `se lint` passes, and epubcheck has no opinion about an image
    nobody asked for. After any render change, unzip the built epub and
    compare images referenced against images present, BOTH directions.
  - assemble.is_subheading read 169 lines across seven books as titles.
    New: a QUOTED line is speech (92 dialogue lines across the Verne
    novels, journey-center-earth, memorabilia, tangled-tale), and
    SQUARE BRACKETS mark the author in a lower voice. TWO BLUNTER RULES
    WERE TRIED FIRST AND BOTH REGRESSED REAL BOOKS — a sentence-break
    rule killed theophrastus's "10. The Grouch" and tyndall's two-clause
    titles; a followed-by-indented-block rule killed ball's table
    captions and leviathan's numbered sections. Re-assemble all 60 pages
    and diff after EVERY is_subheading change.
Cover: Sofonisba Anguissola's "The Chess Game" (1555), Commons "File:
The Chess Game (Sofonisba Anguissola) 1555 (4096x3236px).jpg", crop
"2157x3236+350+0" — two sisters over a squared board of counters.
Carroll names chess in the passage where he argues his own game is
better, because a finished game of chess leaves you nothing to show.

Lewis Carroll's Pillow Problems (pillow-problems/ — the 49th book, and
the fourth of the Carroll shelf after bunyan/, tangled-tale/ and
symbolic-logic/). Curiosa Mathematica Part II, 1893. 9 files, ~24.4k
words, 64 plates, 2,436 FORMULAS, from Gutenberg #79080. Ratio 1.00
(--min-ratio 0.85 --max-ratio 1.3). Seventy-two problems he solved in
his head, in bed, in the dark.
THE SOURCE IS UNLIKE ANY OTHER HERE: there is NO plain-text edition,
because the mathematics is not text. It is 2,436 separate SVG files
pulled in by <img>, one per SYMBOL, so "sin OP · PN" is four images in
a row — the figure-marker pipeline does not fit it at all. BUT EVERY
IMAGE CARRIES data-tex WITH ITS LATEX, and across all 2,436 there are
only 55 distinct commands and 3 environments. Encoded, not lost.
tex.py converts it; reuse that module for any book whose mathematics
comes as images. (The alt text is MathSpeak and is also reversible,
but it is a READING of the formula; data-tex is the formula. It does
settle arguments — see the decimal point.)
ALEX'S RULING: MODERNISE THE NOTATION, and render in both formats.
DELIBERATELY THE OPPOSITE OF symbolic-logic/ and for a stated reason —
there the words WERE the machine, here the notation is incidental to
the argument. So the Victorian factorial (a vertical bar with the
number underlined) -> "3!", "&c." -> "etc.", mid-height decimal point
-> full stop.
SIX CONVERTER TRAPS, EVERY ONE PRODUCING READABLE, WRONG ARITHMETIC:
  1. THE DECIMAL POINT IS AT MID HEIGHT. "18 \cdot 65°" is 18.65°;
     "a \cdot b" is a times b. Getting it backwards turned 1.5430806
     into "1· 5430806". The MathSpeak settles it (41 cases, all
     "dot 65 degree").
  2. A LITERAL "." BETWEEN ATOMS IS HIS MULTIPLICATION SIGN
     ("1/2.c/2" is not a number) — but the decimal point and the dots
     in \text{i. e.} must survive that pass, so both ride sentinels.
  3. THE VINCULUM IS A BRACKET: "2×10 - \overline{x-1}" is
     2×10-(x-1); dropping the bar flips the sign of the 1 silently.
     Over bare letters it is a line SEGMENT. Content decides.
  4. "\\&c." IS A ROW BREAK FOLLOWED BY CONTENT. Protecting "\&"
     before splitting rows eats the break and welds two lines.
  5. AN EXPONENT MUST SWALLOW ITS COMMAND'S ARGUMENTS.
     "2^\tfrac{3}{4}" read as the command name alone gives "2^/34" —
     19 formulas, including the one the Introduction narrates.
  6. "A. P." / "A. M." are not products. Only a list can tell them
     from one.
THREE THINGS PREP'S ASSERTIONS CAUGHT: the FRONTISPIECE falls outside
every kept section and would have been dropped (it is Solution 67's
diagram with the labels off — id "front", NOT "figfront", the tyndall
trap); A STRAY UNRENDERED LATEX FRAGMENT SITS IN THE BODY TEXT,
invisible to a converter that only reads attributes; and a STALE PLATE
from an earlier run, so prep now clears the image directory first.
VOICE, THREE REGISTERS KEPT APART. The Introduction is the reason to
publish the book and needs real work; NO CLINICAL VOCABULARY near the
passage on sceptical, blasphemous and unholy thoughts — he is
describing a night, not a diagnosis. The Questions are terse (money
into words where it is puzzle data: "2/6" -> half a crown). The
Answers and Solutions get a LIGHT touch on purpose — working, not
exposition — and HIS DROPPED ARTICLES STAY ("If remaining bag be A"),
because that telegraphic style is how he thought.
THE CHECK THAT MATTERS IS NOT THE RATIO but the numeric-token diff per
file: verify.py cannot see arithmetic, and 2,436 formulas came through
a converter.
Cover: Whistler's "Nocturne: Blue and Gold — Old Battersea Bridge"
(1872), Commons "File:James McNeill Whistler - Nocturne en bleu et
or.jpg", crop "1723x2584+120+0" — night, one small figure, and a
composition of pure geometry that looks like one of his own diagrams
floating in the black.

Lewis Carroll's Euclid and His Modern Rivals (euclid-rivals/ — the 50th
book, and the third Carroll after symbolic-logic/ and pillow-problems/).
The 1879 farce in four acts, revised 1885: Minos, a college examiner,
falls asleep over his marking and is visited by the ghost of Euclid and
then by Herr Niemand, who appears as counsel for thirteen rival geometry
manuals and loses every case. 14 files, 54,126 -> 53,015 words, ratio
0.98 (verify --min-ratio 0.85 --max-ratio 1.3). The SECOND OCR source
after thompson/, from the same Archive.org path, and see source_notes.txt
plus abbyy.py / speakers.py / repair.py.

THE TRANSLATION WAS THE EASY PART. Every defect found was in the class
verify.py structurally cannot see, and check.py (new, per-book, KEEP THIS
PATTERN) is what found them: it compares the SPEAKER SEQUENCE of each
modern file against its source name for name, plus marker parity, heading
renderability, and fleming/'s numeral diff. 1,163 speeches, all matching.

A MISATTRIBUTED SPEECH IS THE WORST DEFECT AN OCR PLAY CAN HAVE — it
reads perfectly and argues the opposite. ~50 tags were lost in FIVE
distinct ways, none visible in the output:
  - A TAG AND ITS ITALIC STAGE DIRECTION ARE ONE RUN ("Nie.
    (innocently)"), so the tag test sees the whole thing and fails. This
    was forty of the fifty.
  - Some tags are never marked italic at all. Fall back on the paragraph's
    first token, but ONLY for an exact resolve: "Sc." scores 1.5 to Euclid
    and "Props." 2.5 to Nostradamus, and a looser rule promotes both.
  - THE TERMINAL POINT IS PART OF THE TAG and the scan drops it ("Mhu",
    "Nie»", "Euc. '" with the speech's opening quote pulled in). Retry on
    the letters alone.
  - Tags BURIED MID-PARAGRAPH, one paragraph hiding two. Match on a
    distinctive CONTEXT string and cut at the tag: "Euc." alone occurs on
    nearly every page as a citation.
  - The tag pattern must admit the punctuation the scan INVENTS inside a
    tag — "3Ii?i.", "311)1.", 'A?"^.' — or it is refused before scoring.
Every guard on the fallback should be justified by what it actually
excludes, and tested by re-running over the whole book: relaxing the
"needs two letters" rule to one letter, and then to none, each added
exactly one more speech, and each was the right one.

THE ACT AND SCENE HEADINGS ARE THE SPINE AND THE SCAN MANGLES THEM.
"ACT 11." for ACT II., "SCE^^E II.", "Scene YI.", "Scene VL" — six of
nineteen Act headings and eight of seventeen Scene headings missed. EVERY
MISS IS SILENT TWICE: the heading falls into the body as an all-caps
paragraph that assemble.py renders as a spurious heading, AND the section
it should open never opens, so two scenes weld into one file under the
wrong title. Act II Scene II vanished into Scene I this way, while six
REPEATED page headings invented sections the book does not have. Match
loosely, then ASSERT THE WHOLE STRUCTURE against the book's own ARGUMENT
OF DRAMA (eleven sections). Scene titles come from that front matter too,
not from the scanned heading, which arrives as raw OCR.

SIXTEEN RUNNING HEADS REACHED THE BODY in three shapes, four of them
welded into the middle of a sentence. Strip them BEFORE mend(), or mend
joins the body to the running head instead of to its own first half. A
list of them is not enough — "58 LEGENDRE. [AcT II." and "Sc. v.]"
escaped a first pass on capitalisation alone. Match the SHAPE
whole-paragraph and short, and assert the counts.

ABBYY'S BLOCK TYPES LIE, AND THE LIE IS INVISIBLE. Three cases here:
  - A "Table" that is text: the fifth entry of Table III (R. Simpson's
    Axiom), boxed because it is set in short measure beside its heading.
    Table III shipped with four of its five Propositions.
  - A "Table" that is a diagram: the labelled square of the II. 4 proof,
    boxed because its point-letters sit in a grid.
  - A "Picture" that is neither: page 227 is the Syllabus's rearranged
    list of Propositions, and shipping it as a plate would have put plain
    content behind an image.
In each case the marker is present and placed once, and the word ratio
barely moves. LOOK AT EVERY PLATE BEFORE CAPTIONING IT — that is what
found all three, and it also found that page 65 is ONE diagram ABBYY
boxed twice (cut in two it became two half-figures, each missing the
labels that give it meaning) and that page 116 carries THREE of Niemand's
case-diagrams where ABBYY found two — the missing one being the case the
text names three times.
PLATE IDS MUST BE SEQUENTIAL, NOT PAGE NUMBERS: three pages carry two
plates each, and both would resolve to the same file.

NO CRIB FOR THE 1885 ADDITIONS. repair.py corrects the 1885 scan against
the 1879, but Henrici's book appeared in 1879 and Morell's in 1875, so
those scenes are new in the revision and have nothing to correct against
— which is why they are the most damaged, and why their geometry had to
be rebuilt from the figures instead. Both reconstructions were confirmed
afterwards by the plates themselves, letter for letter.

CONVENTIONS (all three checked mechanically, see running_notes.txt):
asides take Carroll's own form, "Minos. (thoughtfully) Well, ..." and not
the modern playscript "Minos (thoughtfully)."; consecutive speeches by one
speaker STAY TWO SPEECHES because that is what he printed; and section
headings take no terminal period and are title case (ball/'s trap — 14 of
them were written wrong).
CROSS-REFERENCES to Carroll's own pages (there are ~50) go to Act and
Scene, or to "§ 1 above"; two point forward into Act Four. References to
OTHER authors' books are kept as printed — the numeral check earned its
keep by catching a dropped "(see pp. 222, 241)".
Cover: Goya's "The Sleep of Reason Produces Monsters" (Los Caprichos 43,
1799), Commons "File:Francisco de Goya, El sueño de la razon produce
monstruos (The Sleep of Reason Produces Monsters), published 1799, NGA
7502.jpg", crop "2188x3282+312+278" — the plate only, out of a full sheet
with wide margins and the printed number 43. A man asleep at his desk with
his head on his arms while phantoms crowd in behind him is the book's
opening stage direction almost word for word.

Miguel de Cervantes' Don Quixote (quixote/ — the 51st book, and by a wide
margin the LONGEST in the collection: 134 files, 379,021 Spanish words ->
426,371 English, ratio 1.12, verify --min-ratio 0.95 --max-ratio 1.35).
Both parts complete and unabridged — Part One of 1605 (52 chapters) and Part
Two of 1615 (74) — from the Spanish, Gutenberg #2000, with every interpolated
tale that abridgements cut (Reckless Curiosity, the Captive's story, Cardenio
and Dorotea, Leandra, the Camacho wedding, Ricote and Ana Félix).

THE SINGLE MOST DANGEROUS BUG, and it is INVISIBLE TO verify.py. Three
chapters are split across two files (035+036 = I.33, 037+038 = I.34,
045+046 = I.41). I titled 036 and 037 as chapters in their own right — 036
headed "Chapter 34" when it is chapter 33's second half. NOTHING would have
caught it: assemble.strip_front() drops the first non-blank line of EVERY
file in a group and takes the heading from part 1 only, so the bad line in
036 vanishes silently, and chapter 34 would have shipped titled "Chapter 34
(Part 2): ... Is Carried Further". verify.py check 3 only asserts that a part
marker, IF PRESENT, sits in the first three lines; a MISSING marker and a
WRONG heading are both invisible, and neither the ratio nor must_contain
moves. CHECK THE MANIFEST FOR "of" > 1 BEFORE WRITING ANY FILE. The correct
shape is: heading line, "(Part n of k)", blank, body — parts 2+ never
re-introduce the chapter and non-final parts never conclude it.

THE PIPELINE IS MARKUP-FREE AND IT IS EASY TO FORGET IT. I wrote
*Tablante de Ricamonte* in file 018 and four italicised book titles in 081;
both renderers would have shipped literal asterisks. Book titles go in plain
text. Structure comes ONLY from convention: tab indent = verse or table,
ALL CAPS = heading (so NEVER write an all-caps line), and nothing else.

SANCHO IS THE TRANSLATION PROBLEM. Two editorial calls, both approved up
front and both worth reusing:
- PROVERBS ARE TRANSLATED FOR FUNCTION, not word for word. Where a real
  English equivalent exists, use it; where none does, INVENT an
  English-sounding proverb. Keep the avalanches at full length (they are the
  joke) and let the misfires misfire — Don Quixote's complaint that Sancho
  drags them in "by the hair" only lands if some of them genuinely do not fit.
- EVERY MALAPROPISM IS REBUILT ON THE ENGLISH WORD, never carried over.
  fiscal/friscal -> prosecutor/PERSECUTOR (a letter's difference, and Sancho
  does feel persecuted); Ptolomeo's dirty syllables -> "a Toll-and-Lousy,
  with 'pee' tacked on"; scitas/"cita, cita" -> "Scythians"/"sic 'em, sic 'em";
  bárbaros -> "barbarians"/"barbers"; pacto expreso -> "packet expressed";
  teologías -> "'ologies"; abernuncio kept as the Latin he mangles. The full
  locked list is in running_notes.txt. Sancho's malapropisms are the one place
  where a literal rendering is guaranteed to be wrong.
- THE VERSOS DE CABO ROTO in the prologue verses (Cervantes chops the last
  syllable off every line) are reproduced by chopping the last syllable in
  ENGLISH, with one bracketed note. `se lint` flags all thirty-odd of them as
  broken words; they are correct and the warnings are ignored.

THE INCONSISTENCY RULE, and it has two halves. RECONCILE a slip a reader
could only read as OURS: the Yangüesan/Galician muleteers, Alifanfarón's
shifting name, "Teodora" for Dorotea, Vicente de la Roca/de la Rosa, don
Pedro/don Gaspar Gregorio, Osiris for Busiris, Curambro for Curiambro, and
II.45's back-reference to a purse case that has not happened yet (dropped the
specific reference; the whole chapter otherwise stands). KEEP the famous ones
Cervantes answers for himself: Sancho's wife's shifting name, the vanishing
and reappearing saddlebags, and the stolen ass — he apologises for the last
two in II.3-4 and the apology is funnier than the fix. Every reconciliation is
logged in running_notes.txt.

EPITHET CHANGE: from II.17 Don Quixote renames himself the KNIGHT OF THE
LIONS and the narrative follows him. "The Knight of the Sorrowful Countenance"
stays pinned in must_contain because it is Part One's, but do not use it as
the running epithet after file 076.

TWO SENSITIVE PASSAGES, both the Verne rule, both translated in full with no
softening and no wink: Ricote the Morisco endorsing the 1609 expulsion of his
own people as "divine inspiration" while weeping for Spain (II.54), and his
praise of its executor Don Bernardino de Velasco for using "the cautery that
burns rather than the ointment that softens" (II.65). The reader has just
watched his daughter nearly hanged; the contradiction is what Cervantes leaves
standing, and a note would be the wink the rule forbids. Sancho on the slave
trade (II.1) and his "mortal enemy of the Jews" are handled the same way.
Dorotea's seduction and the attempted rape are at full length, with gravity
and without titillation.

RATIO: Spanish -> English narrative prose runs about 1.12 here — HIGHER than
the 0.9-1.5 FR/IT novels because Cervantes' periodic sentences unstack, and
far below the 1.4-2.4 of Latin verse. Target 1.06-1.20 per file; under 1.00
means summarising.
Cover: Gustave Doré's 1863 frontispiece, Commons "File:Gustave Doré - Miguel
de Cervantes - Don Quixote - Part 1 - Chapter 1 - Plate 1 \"A world of
disorderly notions, picked out of his books, crowded into his imagination\"
.jpg", crop "3067x4600+338+100" — the plate only, out of a book page with
white margins and a printed caption line. THE CROP IS IN THE COORDINATES OF
THE 3840x4968 RENDITION COMMONS SERVES, not the 6456x8352 original (the
bunyan trap: build_ebook caches the 4000px thumb and crops THAT).

The Thousand Nights and a Night (nights/ — the 52nd book, and the first
ANTHOLOGY assembled by selection rather than translated whole). Shahrazad's
frame plus eighteen of the great tales, from Burton's 1885-88 translation
(Gutenberg #3435/3440/3444/3447): the Fisherman and the Jinni, the Porter
and the Three Ladies, the entire Hunchback cycle, Sindbad's seven voyages
AND the Calcutta variant seventh, the City of Brass, Aladdin, Ali Baba.
72 files, 217,720 -> 225,804 words, ratio 1.04 (verify --min-ratio 0.85
--max-ratio 1.25).

THE JUSTIFICATION IS THE SAME SHAPE AS bunyan/, and stronger. Burton's
archaism is the densest on the roadmap (19.83 archaic tokens per 1000) and
NONE OF IT IS IN THE ARABIC — he invented an antique English that was
already artificial in 1885. Elsewhere we remove the centuries between the
reader and the author; here we remove a costume the translator put on. That
distinction is worth stating in the book's own front matter, and it is why
the ratio lands at 1.04 rather than the 0.95 of the EN->EN lecture books:
unstacking Burton costs about what cutting his throat-clearing saves.

FOUR SOURCE VOLUMES, THREE SETS OF FRAME FORMULAS. This is the structural
lesson and it generalises to any anthology drawn from several volumes:
  - the main Nights: "perceived the dawn of day" / "O auspicious King";
  - Aladdin (supplemental): "surprised by the dawn" / "O King of the Age",
    plus a nightly exchange with Dunyazad the others lack;
  - Ali Baba: "the morn began to dawn", and the header comes AFTER the
    break naming the night that has just CLOSED, where everywhere else it
    precedes the break and names the night about to OPEN.
ALL THREE ARE NORMALISED to one form, which makes every Ali Baba header the
source number PLUS ONE. THE SHIFT IS ENCODED, NOT TRUSTED: check.py parses
spelled-out ordinals to integers ("Six Hundred and Thirty-fourth" -> 634),
reads both source header forms, applies the +1 to Ali Baba's, and compares
numerically. Validated by re-running over the 68 files already finished and
reproducing every one unchanged — that, not the new file passing, is the
evidence a normaliser is right.
Aladdin's numbering also RESTARTS at 515 after the City of Brass ended at
578, because the selection order is ours; see the editor's notes below.

check.py (the euclid-rivals per-book pattern) CAUGHT TWO REAL DEFECTS that
verify.py structurally cannot see, both in night headers: "the Five Hundred
ante Seventy-fifth Night" and "the Six Hundred ante Thirty-fourth Night" —
"ante" for "and", in two different Gutenberg volumes, which makes it the
transcription's habit and not a one-off. The header is otherwise well
formed, the night-break COUNT is right, must_contain does not move and the
ratio does not move. Only reading the numbers AS A SEQUENCE finds it. Both
in prep.py's SOURCE_FIXES with assertions.
WHEN A CHECK FIRES ON CORRECT OUTPUT, FIX THE CHECK. The resumption lock
flagged the Queen greeting her husband as "O King of the Age", which is
good dialogue and in the source; the variants are now anchored to
"reached me," so the lock guards the FORMULA and not the honorific. The
tempting fix — rewording the Queen — would have let a blunt check quietly
distort the prose.

THREE EDITOR'S NOTES, the most in any book here, and each is a fact about
the BOOK'S CONSTRUCTION rather than a claim of the author's (which is what
the Verne rule protects): that the Calcutta seventh voyage is a different
tale and not a variant reading, so the reader does not think the edition
has repeated itself; and that Aladdin and Ali Baba are the two most famous
stories in the Nights and the two that are not in it — no Arabic manuscript
older than the eighteenth century has either, Galland took them down in
Paris in 1709 from Hanna Diyab, and they were written back into Arabic
afterwards — which is also what explains the night numbering restarting.

THE SENSITIVE-CONTENT DECISIONS, and the volume answers the same question
two ways ON PURPOSE. The test throughout: does the reader LOSE information,
or GAIN a false one?
  - File 026, the Jewish physician of the Hunchback cycle: KEPT ENTIRE,
    panic-idiom and all, because a Muslim, a Jew and a Christian are made
    ridiculous in exactly equal measure and the symmetry IS the joke.
  - File 058, Aladdin's dealer (ALEX'S RULING, asked before writing):
    KEEP THE CHARACTER, CUT THE LIBEL. He stays a Jewish dealer and stays
    dishonest — real social history, and his cheating brings the honest
    goldsmith on — but the narrator's slur-epithets go, and the goldsmith's
    claim about all Jews becomes a claim about this dealer. No plot moves.
    There is no symmetry here to protect, which is what separates it.
  - "blackamoor" goes wherever the people have ALREADY been named (Indians
    and Abyssinians, in the same clause) — the noun then carries nothing
    but contempt. But "the country of the blacks" is KEPT as "the Land of
    the Blacks": bilad al-sudan is a real region on a medieval map, and
    deleting it loses geography. Likewise Zanj, Abyssinia and Nubia, and
    likewise the descent of the people of al-Karkar from Ham, which they
    state themselves and which the tale gives to the only people in it who
    help anybody.
  - Sindbad's burial cavern (046) is the darkest passage in the book — he
    escapes by beating to death every living person lowered into the pit
    and robbing the corpses, then comes home and gives alms to the widow
    and the orphan. Rendered flat and in full, unremarked, exactly as the
    Arabic leaves it. A modern reader will notice; that noticing is the
    reading experience and must not be done for them.

LOCK THE FORMULAS EARLY AND ENCODE THE WRONG ANSWERS. "the Destroyer of
Delights and the Sunderer of Companies" was locked in file 049 with its
near-misses registered ("Sunderer of Societies", lower-case "Destroyer of
delights", "Caterer for Cemeteries"); Burton then varied it four more times
and every one was rendered correctly without my noticing. This is the same
mechanism that caught "Prince of the Faithful" in 033 and, chasing it,
"Prince of True Believers" eleven files earlier.
FAMOUS PHRASES GOVERN over Burton's wording: "Open, Sesame!" (his "Open, O
Simsim!"), "New lamps for old", "the Slave of the Ring", "the Old Man of
the Sea". All pinned in must_contain. Kasim still dies of forgetting the
word, because he shouts every other grain instead.
CROSS-SELECTION REFERENCES MUST BE RECONCILED, and there were two: file 040
pointed forward to a tale not chosen, and the Conclusion opened "when she
had made an end of the story of Ma'aruf" while file 070 handed off to it.
Fixed without a note — 070's last night now closes the frame ("and so
Shahrazad went on telling the King her tales... until the thousand nights
and a night were fulfilled") and 071 opens "when she had made an end of her
tales". No absent tale is named and the night count stays honest.

TWO SHARED-CODE FIXES, both generic, both found here:
  - build_ebook.commons_url TAKES THE RENDERED JPEG WHEN THE ORIGINAL IS
    NOT ONE. Anderson's "Scheherazade" is a TIFF that ImageMagick cannot
    read at all ("Can not read TIFF directory count"), so the build died at
    the cover step with a bare TIFF error and no hint of the cause. THE
    CROP IS THEN IN THE RENDITION'S COORDINATES: Commons caps TIFF
    thumbnails at 1920px, so unlike the bunyan/quixote case the rendition
    is SMALLER than the original (2528x3204 -> 1920x2433).
  - rebrand._colophon ANCHORS ON THE PHRASE, NOT ON WHAT FOLLOWS IT.
    `se create-draft` writes "was published in <time>YEAR</time> by
    <author>" for a named author but "...<time>YEAR</time>." for an
    anonymous one, so matching the trailing " by" left the placeholder in
    place and the build died much later in `se build --check`, with vnu
    objecting that YEAR is not a datetime. Any anonymous work would have
    hit this.
VOICE: eighteen tales and no single register. The frame is a woman talking
for her life; the Hunchback cycle is farce played dead straight; Sindbad is
an adventure serial whose hero is a merchant, not a hero; the City of Brass
is an hour of tomb inscriptions and is the most beautiful thing in the
book; Aladdin and Ali Baba are folk tales with the shape of pantomime.
Morgiana counts thirty-seven jars, answers each robber in the captain's own
voice, boils them one at a time and then dances with the dagger — she is
the best character in the collection and needs no help at all.
Cover: Sophie Gengembre Anderson's "Scheherazade" (c. 1870), Commons "File:
Scheherazade.tif", crop "1622x2433+140+0" — the storyteller herself, calm
and looking straight out at the reader, which is the whole book.

Grimm's Household Tales (grimm/ — the 53rd book, and the largest tale
collection in the project: 211 tales in 85 files, 282,941 source words ->
280,899, ratio 0.99, verify --min-ratio 0.85 --max-ratio 1.2). All two
hundred numbered tales and all ten children's legends, from Margaret
Hunt's 1884 translation (Gutenberg #5314) — the FIRST complete English
Grimm and still the only complete one out of copyright.

THE JUSTIFICATION IS THE BUNYAN ONE, SHARPENED: this book is not hard, it
MISLEADS, and the misleading is 99% inside dialogue. Hunt's thou-family
runs to 3,729 instances and is the visible half; the invisible half is
her ordinary-looking vocabulary — "conversation" for conduct, "want" for
lack, "prevent" for go before, "presently" for at once. A reader trips on
"hath" and knows to look it up; the same reader walks past "prevent" and
comes away confidently wrong. The DELIVERABLE, though, is completeness:
every other modern Grimm in print is a selection of thirty or forty.

THE WORST DEFECT OF THE BOOK WAS A MISSING TALE, AND EVERY MECHANICAL
CHECK PASSED WHILE IT WAS MISSING. The Grimms number their tales 1-200
but print 201 of them, because "The Twelve Idle Servants" is 151* — an
extra hung on 151, "The Three Sluggards". prep.py's heading regex was
\d{1,3}, the star did not match, and the heading was never recognised.
Its text still rode through the entire pipeline inside its neighbour's
file, so:
  - verify.py's word ratio did not move by a hair (the words are all
    there, in order);
  - check.py's title, order and first-line rules passed, because they
    compare the manifest against the FILES and a heading missing from
    both agrees with itself;
  - the page simply had one untitled paragraph in the middle of another
    tale and one missing TOC entry, out of 211.
THE ONLY WITNESS IS THE SOURCE'S OWN CONTENTS LIST — the one description
of the book that the pipeline did not produce. check.py now counts it and
requires the manifest to match. GENERALISE THIS: any book that prints its
own table of contents can be checked against it, and nothing else in this
toolchain can see a section that was never a section. (Found by sweeping
the assembled HTML for heading counts, not by any check.)

SHARED FIX — assemble.is_subheading READ NARRATION-PLUS-SPEECH AS A
TITLE. The existing rule rejects a line that BEGINS with a quotation
mark; it cannot see 'Hans answered, "To Gretel."', where the terminal
stop is inside the quotes. Eleven lines of Clever Hans were section
headings in the middle of their own conversation. THE BLUNT FIX (any line
ending in a closing quote) REGRESSES LEVIATHAN, whose real section titles
quote a term — 'The Names "Sacerdotes" and "Sacrifices"'. The rule
therefore keys on what INTRODUCES the quote: a comma or full stop means
reported speech, a bare space means a quoted term. All 65 pages
re-assembled and diffed, as this file requires: the only changes are
dialogue and answer lines losing heading status in grimm, nights,
euclid-rivals, symbolic-logic, tangled-tale and tyndall-original.

SHARED FIX — A THIRD FORM OF THE NON-JPEG COVER. commons_url already
takes the rendered thumbnail when the Commons original is not a JPEG (the
nights TIFF), but it asks for a 4000px rendition, and WHEN THE ORIGINAL IS
SMALLER THAN THAT COMMONS RETURNS THE ORIGINAL UNTOUCHED. So a PNG
arrived named .jpg and `se build-images` stopped on "Invalid JPEG file"
several minutes in. Commons will not render a PNG as a JPEG at any size,
so prepare_cover now converts on the magic number. Expect this on any
illustrator's plate — they are usually PNGs.

CONVENTIONS, all checked mechanically by grimm/check.py:
 - Every tale title appears in its modern file on its own line, spelled
   EXACTLY and in manifest order. 15 of the 212 titles carry U+2019, and
   a straight apostrophe loses the section silently; grimm/fixtitles.py
   repairs ONLY that, and is deliberately too weak to mask a real drift.
 - No thou-family word survives anywhere ("Our Father, which art in
   Heaven" is exempted by exact phrase, not by loosening the sweep).
 - Verse parity counts BLOCKS, not lines: a rhyme dissolved into prose is
   this book's silent summarisation, but re-setting a four-line unrhymed
   rendering as a rhymed couplet is a legitimate choice and must not be
   punished by the tool.
 - The fleming numeric diff, with a FILE-SCOPED exemption for the one
   stray catalogue number in the body. Never loosen NUM itself.
EVERY CHECK THAT FIRED IN THIS BOOK FIRED ON CORRECT PROSE EXCEPT ONE
("hop hither and thither", a real archaism hiding inside a nonsense
jingle, where the ear stops auditing). Six of seven fixes went into the
tool, not the sentence.

TRANSLATION DECISIONS worth reusing (all in running_notes.txt):
 - DUMMLING = SIMPLETON always. Hunt renders one German name two ways in
   adjacent files; that is the TRANSLATOR's inconsistency, not the
   Grimms', and is reconciled. The Verne rule protects an author's own
   claim, not a transmission artefact.
 - Coinage kept (thaler, groschen, kreuzer, farthing); it is doing real
   work as a quantity and no modern equivalent survives conversion.
 - Nonsense jingles are REBUILT ON THE ENGLISH WORD, like Sancho's
   malapropisms — the chain-rhyme in "Domestic Servants" (Cham/name,
   Hippodadle/cradle) rhymes in English or it is not the joke.
 - THE THREE ANTISEMITIC TALES (7, 110, 115) are translated IN FULL AND
   UNSOFTENED, with exactly ONE editor's note, at 110, saying what the
   edition did and why and making no comment on the tale. Alex's ruling,
   taken before any of the three was written.
 - COLOUR AS ENCHANTMENT, twice, decided differently from each other and
   both logged. In "The King's Son Who Feared Nothing" the princess's
   blackness is the spell's progress meter and is rendered as a
   CONDITION, never an identity ("black from head to foot", thereafter
   "the girl") — the Bunyan-Flatterer precedent. "The White Bride and the
   Black One" cannot be handled that way: there blackness is a punishment
   God inflicts and is half the title, so it stands as printed.
 - THE NOTE COVERS BOTH CLASSES (Alex, 2026-08-16: broaden it). Still
   exactly ONE note, still at 110, now naming the caricatures of Jews AND
   the tales that turn on skin colour, with "The White Bride and the
   Black One" as the sharpest of the second. It stays inside the Verne
   rule by remaining a statement about what the EDITION did, and says so
   in as many words: "It makes no further comment on them. They stand as
   the Grimms printed them." NOTE THE COUPLING nobody would look for: the
   note states the collection's size, so recovering the missing 151*
   turned it into a miscount ("two hundred and ten") until it was fixed
   in the same pass. Any change to what the edition contains has to reach
   that sentence.
Cover: Arthur Rackham's Little Red-Cap from his 1909 Grimm, Commons
"File:Grimm-Rackham-reconstruction_0173.1.png", crop "1890x2835+538+482"
— the plate only, cropped out of a page scan with wide paper margins (the
Trouvelot/Goya method: find the plate box by darkness profile, then take
the 2:3 rectangle inside it). One small red figure at the foot of a huge
bare wood, meeting the wolf: legible at thumbnail size, and the emblem of
the whole collection.

Epictetus' Discourses (epictetus/ — the 54th book, and the completion
of something the collection already half-had: our Enchiridion is an
abridgement of THIS, compiled by Arrian out of these same lectures).
All four surviving books, 95 chapters, 120,290 -> 115,318 words, ratio
0.96 (verify --min-ratio 0.85 --max-ratio 1.3). From Standard Ebooks'
George Long; GUTENBERG HAS ONLY A SELECTION (#10661), so check SE when
Gutenberg looks thin.

A THIRD JUSTIFICATION CLASS, and the most useful thing this book
teaches. Measured first, as the folktales strand requires, and the
measurement says DON'T DO IT:
    Bunyan (source)               13.11 archaisms per 1,000 words
    Hunt's Grimm                  12.34
    Long's Discourses              1.00
    Jacobs' English Fairy Tales    0.90  <- STRUCK as too clean
22.8-word mean sentence, 19% over 35. By every number this project has
used to choose a book, Long should be left alone.
He should not be. He translates word by word, and the words he picks
are ordinary modern English meaning something else: phantasia ->
"appearance", prohairesis -> "will", dogma -> "opinion", prolepsis ->
"precognition", ataraxia -> "perturbation", dunamis -> "faculty".
Those run to 4.99 per 1,000 words, FIVE TIMES his archaism rate. A
reader trips on "thou hast" and looks it up; he meets "the right use of
appearances" and sails past having understood the opposite.
So the three classes are: (1) HARD — Burton, Leviathan, archaism you
can feel; (2) FALSE FRIENDS — Bunyan, Grimm, ordinary words that have
moved; (3) TECHNICAL CALQUE — this book, where a translator renders a
foreign TERM with a transparent-looking English word and then uses it
for 119,000 words. CLASS 3 IS INVISIBLE TO THE ARCHAISM MEASURE BY
CONSTRUCTION. Do not conclude from a low score that a philosophical
translation is safe; measure the technical vocabulary separately.

ONE FILE PER CHAPTER, DELIBERATELY, against the grimm/ precedent of
grouping short pieces. The mean chapter is 1,254 words and grouping
would halve the file count — but assemble.build_sections sets
is_chapter=False for every section it carves out of a grouped file, so
all 95 chapters would have rendered as top-level h2 and the four Books
would have nested nothing. 101 files, three chapters split into parts.

THE SOURCE IS XML, SO PARSE IT AS XML (ElementTree, not regex — that is
where tyndall's four-fold Spenser stanza and bunyan's welded noteref
digits came from). Then add the check that actually paid: EVERY
CHAPTER'S WORD SEQUENCE COMPARED AGAINST A SECOND READING OF THE RAW
XML THAT SHARES NO CODE WITH THE PARSER. It caught three bugs in ten
minutes, none of which would have moved the word ratio:
  1. MY OWN NOTEREF REMOVAL appended a deleted anchor's tail to the
     parent's LAST child instead of the anchor's PREDECESSOR, relocating
     a clause to the end of any paragraph carrying two notes. II.23 read
     "...syllogisms like Chrysippus, and putting our hopes in them. If a
     man by this teaching does harm ... from being wretched" — every
     word present, and it reads almost plausibly.
  2. The verse renderer took spans as DESCENDANTS of the blockquote, so
     a <cite>'s inner span became a line of the poem ("i") while the
     word "Iliad" vanished.
  3. A BLOCKQUOTE THAT IS NOT VERSE wrapped the one drama table
     (Euripides), silently dropping eight lines and leaving "see what
     they say:" pointing at nothing.
REUSE THIS CROSS-CHECK ON ANY STRUCTURED SOURCE. Two independent
readings agreeing is evidence; one reading is a hope.

check.py (the euclid-rivals per-book pattern), and TWO LESSONS ABOUT
CHECKERS THAT GENERALISE:
  - IT MUST EXIT NONZERO. It printed findings and returned success for
    48 files, so a real defect rode straight through a `check && commit`
    chain. A checker that cannot fail a build will eventually be ignored.
  - IT MUST MIRROR THE RENDERER, NOT APPROXIMATE IT. It stripped every
    line and asked is_subheading about each, so a citation INSIDE a
    tab-indented verse block came back as a spurious heading — the
    renderer never asks, because an indented paragraph takes the <pre>
    branch several tests earlier. Walk paragraphs exactly as
    render_body does. Every disagreement between a check and the
    renderer costs an edit to correct prose.

THE BARE-QUESTION RULE, and the shared fix that was COSTED AND
REJECTED. The dialogue convention here is that the objector is quoted
and Epictetus answers unquoted — which is most of what makes Long
readable, since he runs both sides into one paragraph and the reader
cannot tell who is speaking. But it fills Epictetus' side with short
bare questions, and is_subheading's last test is caps >= len(words)//2,
which a two-word question passes on its opening capital alone ("How
so?"). Write them at four words or more with no proper noun, or quote
them. The shared fix does not exist: a strict majority fixes "How so?"
and "How does Medea put it?" but not "How so, Diogenes?" (2 of 3);
excluding the first word from the count fixes those two and keeps every
real title, but still leaves "How so, Diogenes?". No one-line change to
is_subheading covers the class, and any of them costs a re-assembly and
diff of all 56 books.

A FORMULA LOCKED ACROSS TWO BOOKS. The Cleanthes prayer appears FIVE
times and Long renders it FOUR ways, including "necessity" for
"destiny" at IV.4 where Epictetus quotes it with anagke. All five are
set as the Enchiridion's stanza ("Lead me, Zeus, and you too, Destiny,
/ wherever you have fixed my post"), verified by grepping both books
rather than by memory. This is the nights/ rule about frame formulas
applied to a QUOTATION: a reader who owns both books meets the same
lines five times and must recognise them every time.

SENSITIVE CONTENT, AND THE DISTINCTION IS THE POINT. Epictetus uses
kinaidoi four times (I.5, II.10, II.20, IV.2) as an incidental term of
abuse inside sentences about something else; all four are rendered by
what the word MEANS in the argument ("men who have lost all shame about
sex"), because the class is not his subject and the reader loses no
information and gains no false one — the Bunyan-Flatterer test. At
II.10 the SYMMETRY is what has to survive: he condemns both parties and
says the second man "loses being a man no less than the other".
BUT III.1 IS THE VERNE RULE AND GOES THE OTHER WAY. Two thousand words
arguing that a man who plucks his body hair is trying to stop being a
man, with the gods sending Hermes to tell him to let a man be a man and
a woman a woman. There the claim IS the chapter, and softening it would
replace his argument with one he never made. Translate in full,
unhedged, no note.
Also: "the Galileans" (IV.7) kept as written with no note — it is one
of the earliest pagan references to Christians and whether he means
Christians or Jewish zealots is a live dispute, so identifying them
would put a claim in his mouth. Same reasoning as II.9's "dipped".
The suicide material (I.9, I.24, I.25, II.15, III.13) is translated in
full with NO modern note and no helpline: that would be the wink the
Verne rule forbids and would recast a philosophical position as a
symptom. KEEP BOTH HALVES — II.15, where Epictetus talks a student out
of starving himself ("not to all our decisions, to the right ones"), is
the same doctrine as "the door is open", and is the half every popular
account leaves out.

A must_contain PIN MUST BE WRITTEN FROM THE TEXT, NOT FROM MEMORY. The
one that failed pinned the Cynic as "a scout sent from God to men";
Epictetus uses two words there and Long keeps them apart — MESSENGER
(angelos) from Zeus, and SPY (kataskopos) on what is good and bad. The
pin merged them into a phrase in neither the Greek nor Long, so it
could only have been satisfied by a translation that was wrong.
VOICE: it is SPEECH — the Greek diatribe, a man talking out loud,
starting again, answering a heckler, losing patience. Long flattens it
to level Victorian prose and restoring it is most of the job. Resolve
his parenthetical double-shots ("confidence (courage)") to one word and
drop his parenthetical Greek. Keep the diminutives ("this little body
of yours"), keep the plainness about the body that Long is prim about,
and keep the comedy, which is load-bearing.
Cover: Gérôme's "Diogenes" (1860), Commons "File:Jean-Léon Gérôme -
Diogenes - Walters 37131.jpg", crop "881x1322+400+0" — the whole jar
with the lamp centred and one dog entering at the edge. Diogenes is
whom Epictetus points to whenever he has to show what a free man looks
like. NOTE the original is 1800x1322, SMALLER than the 4000px rendition
build_ebook requests, so Commons returns it untouched and the crop is
in the original's own coordinates — the opposite of the bunyan/quixote
trap.

TWO BUGS OF ONE SHAPE, both found on 2026-08-17, and the shape is worth
naming: A FACT DUPLICATED ACROSS TWO TOOLS WILL EVENTUALLY DISAGREE, AND
THE DISAGREEMENT IS INVISIBLE WHILE EACH TOOL IS INDIVIDUALLY CORRECT.
  1. THE PUBLISHED FILENAME. Two early books ship under the name of the
     WORK, not the directory: descartes/ as philosophical-works.html and
     malthus/ as population.html. Only build_feeds.py knew, in a dict of
     its own, so assemble.py wrote site/descartes.html, nothing linked to
     it, and the site served a stale page. A repair to descartes/ the day
     before -- nineteen duplicate contents entries, four Part titles
     restored that strip_front had deleted -- was committed, verified,
     swept, pushed, and REACHED NO READER. Now `PAGE=` in the book's env,
     read by assemble.py, sweep.py and build_feeds.py alike. sweep found
     the staleness seconds after being taught the right filename.
  2. INLINE MARKUP. assemble.py and build_ebook.py each did their own
     escaping-plus-markup. Now assemble.inline() is the only one and
     build_ebook.esct() calls it, so page and epub cannot drift.
When you add a per-book fact, ask which tools need it before deciding
where it lives.

EMPHASIS IS THE ONE EXCEPTION TO THE MARKUP-FREE RULE (Alex, 2026-08-17):
_x_ and *x* render as <em> in both renderers. Everything else still comes
from convention alone. THE PATTERN MUST STAY NARROW, because a bare
asterisk means at least five other things here: "* * *" is a scene
separator (291 of them in progress-and-poverty, 52 in democracy2);
Carroll writes "* * *" for an unexpressed substantive and marks proposed
axioms with a leading "*"; Paine and Smith use it as a footnote mark;
Verne's runic facsimile "* ᛐ * ᚼ *" must survive. So the delimiters may
not enclose whitespace and are anchored against word characters (which
also protects the figure id "app_1" and pillow-problems' "S_n"). A span
MAY cross a line break -- the Decameron wraps each multi-line rubric in
one pair of asterisks -- capped at 400 characters. Re-assemble all books
AND the -original pages and diff after any change here; the books that
carry only separators must not move, and that is the test that the guard
works.

A DECLARED OMISSION IS STILL AN OMISSION, AND NO CHECK CAN SEE IT.
wealth-of-nations/023 verified at 0.44 from the day it shipped. The
prose was complete; what was missing was 342 rows of Smith's wheat-price
tables, and in their place sat a bracketed note saying the original
"includes extensive historical wheat price tables" followed by a
120-word summary of what they showed. verify.py could measure the ratio
but had no way to know the missing words were DATA; the note itself was
the evidence, in plain English, and only reading the file found it.
Recovered from Standard Ebooks' XHTML, which keeps the tables as real
tables -- our source was SE, not Gutenberg, and checking the provenance
rather than assuming it is what made the fix possible. See
wealth-of-nations/tables.py: classify() raises on a row shape it does
not know, each table asserts every non-header row survived, and the
digit runs were compared as multisets between source and output.

David Hume's An Enquiry Concerning Human Understanding (hume/ — the
55th book; the 1748 rewrite of Book One of the Treatise, from Standard
Ebooks). 20 files, 12 sections, 48,082 -> 45,632 words, ratio 0.95
(verify --min-ratio 0.85 --max-ratio 1.3).

THE PUREST CASE YET OF THE CLASS epictetus/ NAMED, and worth reusing as
the justification template. Archaism 0.47 per 1,000 words — BELOW books
struck from the roadmap for being too clean (Jacobs, Ralston) — against
the highest abstraction score measured anywhere in the screening pass
(49.1). Nothing in it sounds old. It is blocked entirely by
eighteenth-century philosophical vocabulary used with total
consistency, and "matter of fact" read as the modern idiom ("prosaic")
silently destroys the distinction the whole book is built on. A reader
who trips on "hath" knows to look it up; this reader does not know
anything happened. DIFFICULTY YOU CANNOT FEEL IS A STRONGER CASE FOR A
RETELLING THAN DIFFICULTY YOU CAN.

AND THE MEASURE OVERSTATES IT, WHICH THE TRANSLATION HAS TO KNOW. Hume
is a great stylist and his famous sentences are already modern
("Custom, then, is the great guide of human life"; "A wise man
proportions his belief to the evidence"). The obstruction is the
apparatus AROUND the argument — section-opening throat-clearing,
periodic set-up sentences — not the argument. THE GOVERNING RULE IS THE
REVERSE OF THIS PROJECT'S USUAL ONE: IF A SENTENCE IS ALREADY CLEAR,
LEAVE IT ALONE. A file in which every sentence has been rewritten has
been damaged, however defensible each rewrite is. Several must_contain
pins are therefore pinned UNCHANGED, which is what stops a translator
improving a sentence that needs no improving.

THE FIRST BOOK THAT DEPENDS ON THE EMPHASIS RENDERING (assemble.inline,
added 2026-08-17), and it leans on it hard: 202 spans, because Hume
italicises the terms he is DEFINING at the moment of defining them, the
propositions under examination ("*that the sun will not rise
tomorrow*"), and both definitions of cause. All 202 render as <em> on
the page and in the epub. MARKER PARITY AGAINST THE SOURCE, per file,
caught three drifts nothing else could see: two spans I invented, and
one moved off Hume's word onto its neighbour (*may* possibly, for may
*possibly*). DO NOT ADD emphasis the author did not have — in the one
book where the markers mean something, inflating them makes them mean
less. Malformed markers FAIL OPEN (assemble.EMPH deliberately refuses
to match across a leading or trailing space), so a bad marker ships as
literal asterisks and is visible only in a check.

SHARED LESSON — THE fleming NUMERIC DIFF IS A SET DIFFERENCE, AND A SET
CANNOT SEE A DROPPED DUPLICATE. Hume dates two parallel suppositions to
the same first of January 1600; spelling one of them out passes a set
difference untouched because the other survives. hume/check.py counts
instead (Counter subtraction), which caught it with ZERO false
positives across all twenty files. Worth adopting wherever the set form
is in use. Also: NUM's character class r"\d[\d,./]*" lets a figure
swallow the SENTENCE comma after it, so "1600," and "1600" are
different tokens and every number ending a clause fires a false
positive — separators must be required to be followed by a digit.

PART-DIVIDER PARITY, per file, counted against the source. This is the
descartes trap in its cheapest possible form: strip_front deletes a
line matching PART_LINE from a file's front matter, which is how the
Principles lost all four of its Parts off the published page. WORD form
("Part One") dodges the pattern, but only COUNTING them proves it —
and proves equally that a divider was not dropped in translation.
Section Eleven is undivided; do not assume every split section has one.

THREE SOURCE DEFECTS FOUND BY READING, none visible to any check
because each reads perfectly aloud and says the wrong thing: "necessary
and evitable" for inevitable, which reverses the very argument it
concludes; a question mark on "Is it thence we become acquainted",
where every neighbouring sentence is a question-and-answer pair and
this is the answer; and a full stop closing a plain question. All three
are transmission errors, not claims, so the Verne rule does not protect
them.

THE VERNE RULE, unhedged, no notes anywhere in the book: Section Ten
entire, including the remarks on ignorant and barbarous nations — which
are LOAD-BEARING in the argument about testimony, and that is exactly
why they cannot be quietly dropped — and its closing irony that the
Christian religion cannot be believed by any reasonable person without
a miracle. Section Eleven keeps Hume's frame of a friend arguing in
Epicurus' person; he built the deniability in on purpose. Section
Eight's compatibilism including the passages tracing a criminal's sins
back to the Creator.
BUT ONE PASSAGE IS NOT THE VERNE RULE, and the ledger says why at
length, because the distinction is the whole editorial method: "A
Laplander or Negro has no notion of the relish of wine" keeps the
example entire and drops the noun. The Verne rule protects a dated
CLAIM that is part of the author's subject. Hume's subject here is the
origin of ideas and his claim is about an absent EXPERIENCE; the noun
carries no part of the argument, so the reader loses no information and
gains no false one. Same class as "the vulgar" -> "ordinary people".
(Hume's notorious footnote on race is in "Of National Characters", a
different essay, and is NOT in this book. Do not import it.)
Cover: Chardin's "The House of Cards" (1737), Commons "File:Jean Siméon
Chardin, The House of Cards, probably 1737, NGA 97.jpg", crop
"2667x4000+0+0" — the trim comes off the RIGHT because the card house
sits hard against the left edge and is the reason for the choice.
Painted eleven years before the Enquiry: a fragile structure built by
careful habit, which is Hume's account of what knowledge rests on.

Augustine's Confessions (augustine/ — the 56th book; Pusey's 1838
translation from Gutenberg #3296). 36 files, 13 books, 112,160 ->
117,672 words, ratio 1.05 (verify --min-ratio 0.85 --max-ratio 1.3).
Written c. 397-400: the first autobiography in the Western tradition,
and the book that invented most of what we mean by an inner life.

THE HIGHEST ARCHAISM DENSITY IN THE COLLECTION (35.9 per 1,000 words,
above Burton's Nights and far above Bunyan) — AND THE MEASURE IS
MISLEADING IN A NEW WAY, worth keeping in mind for any translated
source. Nearly all of it is ONE grammatical feature, the second person
singular, and removing it is nearly mechanical. What is NOT mechanical
is everything the Thou was carrying.

THE CENTRAL DECISION: RENDER IT "you", and the argument is the nights/
argument sharpened. Latin "tu" is the INTIMATE singular — the pronoun
for a friend, a child, a lover — so Pusey's "Thou" is a Victorian
addition that makes the book considerably MORE formal than Augustine
wrote it. As with Burton, we are removing a costume the TRANSLATOR put
on, not centuries between reader and author. Take the reverence out of
the pronoun and put it back in the rhythm.
CAPITALISE THE DIVINE PRONOUNS, and NOT for piety — for
disambiguation, and the need is frequent. Augustine breaks off from
addressing God to address his readers directly as "you", sometimes in
the same paragraph (Book Ten opens that way). The capital is the
cheapest possible signal and costs the prose nothing. God is "You",
the reader is "you".

THE DECISION IS MECHANICALLY CHECKABLE, which is unusual and is why
augustine/check.py exists: NO thou-family word survives anywhere,
INCLUDING inside quoted Scripture — because the point is that the book
has ONE voice, and re-archaising the quotations would put a frame
round them that Augustine did not. It fired twice on my own prose,
both times on "Behold" inside a Scripture quotation, which is exactly
the archaism the rule removes. Exemptions are by EXACT PHRASE, never
by loosening the sweep (the grimm rule).
IT ALSO FIRED ONCE ON CORRECT PROSE — "the art itself, by which I
wrote" — and there the CHECK was fixed, not the sentence, with the
reason recorded in the file: as a verb "art" is second person singular
and CANNOT occur without "thou", which the sweep already catches, so
dropping it loses nothing; as a noun it is ordinary modern English.
Fix a check by an argument about what the rule can actually miss, not
by whatever silences it.

THE CHAPTER DIVISIONS ARE NOT IN THE SOURCE AND ARE NOT INVENTED.
Augustine is cited by book, chapter and section (Conf. VIII.12.29) and
every scholarly edition prints all three; this transcription prints
thirteen BOOK headings and then continuous prose. That was CHECKED and
not assumed — in the .txt AND in Gutenberg's HTML, which elsewhere in
this project has carried structure the .txt drops. Recovering them
from the Latin (#33849) was considered and rejected: 971 Latin
sections against 461 English paragraphs, so there is no 1:1 map, and A
WRONG CHAPTER NUMBER IS WORSE THAN NONE, because a reader would trust
it. Each book instead gets a DESCRIPTIVE title as new writing, on the
soap-bubbles precedent ("Book Eight: The Garden at Milan").

KEEP THE RHETORICAL FIGURES — this reverses the project's usual
instruction and is the easiest way to lose 10% of the word count
without noticing. Augustine was a professor of rhetoric who is ashamed
of having been one, and the piled antitheses ("most hidden, yet most
present") are professional equipment, not padding.
SCRIPTURE IS WOVEN IN UNMARKED, half-clause by half-clause, because
the Psalms are the language he thinks in. Render a quoted phrase in
the SAME modern register as the prose around it, so the seam stays
where he put it: invisible. Lifting them into King James English would
make the book look like a book of proofs rather than a man whose
sentences have the Psalms in them the way ours have song lyrics.

THE VERNE RULE, in full and with no note anywhere in the volume:
infant sin argued as guilt; the Manichees as he tells them; his
condemnation of the men of Sodom; his praise of his mother for
enduring a violent husband; woman as subject to man in Book Thirteen;
the allegorical Genesis of Books Twelve and Thirteen, where he keeps
his own modesty about other readings and that modesty is kept too.
THE WOMAN HE DISMISSED (Book Six) is the sharpest case and is handled
as nights/'s Sindbad: she is never named in thirteen books, he records
that his heart was "torn and wounded and bleeding" and then that he
took another mistress because he could not wait two years. Rendered
flat, in full, unremarked. THE ONE THING TO GET RIGHT IN THE
TRANSLATION is that his grief is entirely about his own pain — no
sympathetic phrase may slip in on her behalf that he did not write. A
modern reader will notice what Augustine does not notice, and doing
that noticing for them destroys it.
NOT the Verne rule, and logged as such: Pusey's dismissive rendering
of MULIERCULIS is KEPT, because the diminutive is dismissive in the
Latin too and so is the author's, not the translator's addition. The
test each time is whether the archaism is HIS or PUSEY'S.

BOOKS TEN TO THIRTEEN ARE KEPT ENTIRE. Most modern editions cut them
or append them, which turns the Confessions into a conversion memoir —
a genre it invented and then refused. Book Eleven is the greatest
sustained writing about time in the language and is handled like
hume/: clear the apparatus, keep the joints visible, and do NOT import
the memoir's warmth, or let it go cold either, since he prays in the
middle of the argument and that is the point.
Cover: Ary Scheffer's "Saints Augustine and Monica" (1846), Commons
"File:Scheffer, Ary - Saint Augustin et Sainte Monique - 88.45 - Musée
de la Vie romantique.jpg", crop "2888x4332+250+93" — cropped INSIDE
the painted gold frame, which runs round all four edges. It is the
vision at Ostia itself, Book Nine: mother and son at a window looking
up together, the sea beyond on the right.
NOTE ON THE CROP COORDINATES, a refinement of the bunyan/quixote trap:
commons_url gates on WIDTH > 4200, not on the larger dimension. This
painting is 3520x4500, so despite exceeding 4000 in HEIGHT it is
served as the original, and the crop is in the ORIGINAL's coordinates.
Check which dimension the gate actually tests before assuming.

Boethius' The Consolation of Philosophy (boethius/ — the 57th book;
H. R. James's 1897 translation from Standard Ebooks, GUTENBERG HAS NO
USABLE EDITION). Written in 524 in a cell at Pavia by a consul
condemned without a hearing, and finished shortly before he was
clubbed to death. All five books, 39 chapters and ALL THIRTY-NINE
POEMS, 39,364 -> 40,579 words, ratio 1.03 (verify --min-ratio 0.9
--max-ratio 1.25). It was the most-read book in Europe after the
Bible; Alfred, Chaucer and Elizabeth I each translated it, and there
is not one Christian doctrine in it.

THE POEMS ARE HALF THE BOOK AND ARE WHAT ABRIDGEMENTS CUT. Boethius
alternates prose argument with verse (the Menippean satire form), in
some twenty-eight different classical quantitative metres, and
UNRHYMED. THE RHYME IS JAMES'S VICTORIAN ADDITION — so it goes, on
the nights/ reasoning: we remove the costume the TRANSLATOR put on,
not the centuries between reader and author. Verse STAYS VERSE, in
clear modern English with an audible rhythm. Turning a poem into a
paragraph is this book's silent summarisation. The one metrum James
himself set unrhymed is Song IX, the "O qui perpetua" hymn, and there
the work was only unstacking his inversions.

check.py's DECISIVE CHECK IS VERSE INTEGRITY, and it is exact on all
three of blocks, line count and per-line indent depth — because the
depth carries James's stanza structure (a stanza opens at depth 2, its
body sits at depth 1) and nothing else in the toolchain can see it.
Every song also has to carry its own number, in order. Plus the
augustine THOU sweep, emphasis parity, a markup sweep and the fleming
numeric diff. IT FIRED ON MY OWN PROSE TWICE, both times on "behold",
which is exactly the archaism the rule exists to remove.

A CHECK MUST MIRROR THE RENDERER, NOT APPROXIMATE IT (the epictetus
lesson, re-learned). marker_report tested an emphasis span only for an
internal space, which is ONE of the three ways assemble.EMPH refuses a
marker — it also requires the opening delimiter not to follow a word
character, the guard that protects "app_1" and "S_n". So "can*not*" is
not emphasis at all, and file 028 was written that way and passed
clean: markers balanced, no internal space, count correct against the
source. It would have shipped literal asterisks. Now the check
substitutes with assemble.EMPH and requires that no asterisk survives.
Reintroduce a defect and watch the check fail before believing it.

SHARED, ADDITIVE — A MANIFEST GROUP MAY SAY `"chapter": true`.
assemble.build_sections nests a section under its Part divider only
when the heading reads "Chapter N: Title", and some sections belong
inside a Part without being able to say so that way: Book One opens on
Song I, a peer of that Book's six chapters and not of the five Books,
and it rendered as a top-level section level with "Book One" itself.
Both renderers go through build_sections, so page and epub agree. No
book without the key moves — re-assembled all 46 and diffed.

TWO GENERIC COLOPHON BUGS, both first hit here and both in shipped
epubs (rebrand.py):
  1. HTML's year format is FOUR OR MORE DIGITS, so "<time>524</time>"
     is invalid and vnu rejects it — killing `se build --check`
     minutes in, with nothing pointing at the cause. This is the
     collection's first pre-1000 date. A short year now keeps its
     semantics through a zero-padded datetime attribute.
  2. "a oil painting" — the se template hardcodes "a painting
     completed in" and every medium goes straight into it. Five books
     say "a oil painting", seven "a engraving", plus "a etching" and
     "a illustration". Sixteen epubs carry it until rebuilt.
ALSO: ASSEMBLE THE PAGE **AFTER** BUILDING THE EPUB. assemble.find_epub
looks for the file on disk, so a page built first ships with no epub
link and nothing complains. hume.html and augustine.html were both
shipped that way and were repaired here.

MEASURED AND REJECTED, so it is not re-tried blind:
build_ebook.classify_block calls an indented block verse only when
EVERY line is under 65 characters, so the four songs James set as
fourteeners ship as generic lined matter — `blockquote class="lines"`,
which has no hanging indent, exactly what a long wrapped line needs.
Two wider rules were measured over every book. Allowing 120 characters
moved 1,508 blocks, pillow-problems' formulas and symbolic-logic's
tables among them. Requiring 4+ lines, no column gap, no "|", no list
marker and almost no digits moved 98 — nearly all real poetry (72 in
Burton's Nights, Bunyan's Apology, Seneca's and Cicero's quoted verse)
but still wrong on Franklin's thirteen virtues and the dialogues' cast
lists. The same shape as the is_subheading precedents: successive
blunter rules, each regressing a real book. Left alone; the PAGE is
correct either way, since <pre> keeps the indentation the epub drops.

VOICE: it opens as self-pity and Philosophy throws the Muses out for
making the sickness worse, and the book is a cure administered in
stages — "gentler remedies" first, then the hard ones. Keep the two
speakers distinct: Boethius complains, argues back, and concedes; she
is affectionate, brisk and occasionally sarcastic, and never a
lecturer. The Socratic step-by-step in Books Three and Four is the
spine and its joints must stay visible (the hume rule: where a
sentence is already clear, leave it). Book Two's Fortune speaks in her
own person and is the great set-piece.
must_contain pins the definition of eternity in the form the
translation is REQUIRED to use — "the complete and perfect possession
of endless life all at once", which is what Aquinas takes over whole —
plus "every fortune is good fortune", the wheel, and Orpheus and
Eurydice by name. Note what the eternity pin does NOT say: not
"everlasting", not "for ever". All at once.
Cover: Burne-Jones' "The Wheel of Fortune" (1883), Commons "File:
Edward Burne-Jones - The Wheel of Fortune - Google Art Project.jpg",
crop "2967x4450+0+0" — Fortune with her hand on the wheel and the
slave, the crowned king and the laurelled poet bound to it. The canvas
is 1:2, so the 2:3 rectangle comes off the top; at 2967 wide it is
under commons_url's 4200 gate and the crop is in the ORIGINAL's own
coordinates. Boethius is the reason that wheel is in every medieval
manuscript.

John Stuart Mill's On Liberty (mill/ — the 58th book; 1859, from
Standard Ebooks). 12 files, 5 chapters, 47,974 -> 47,385 words, ratio
0.99 (verify --min-ratio 0.85 --max-ratio 1.15).

THE JUSTIFICATION IS THE hume CASE ALMOST EXACTLY, and the wrong
diagnosis produces the wrong translation. Archaism 0.6 per 1,000 words
— below books struck from the roadmap as too clean — against calque
34.6 and 44% of sentences over 35 words. Nothing in it sounds old.
What blocks it is (1) Victorian periodic sentence architecture, and
(2) a technical vocabulary used with total consistency: "utility" is
Bentham's standard and not usefulness, "sentiment" is settled feeling
and not sentimentality, "self-regarding" is Mill's own coinage and the
hinge of the book. Plus the bunyan false friends, of which there are
more than expected — "suffer" for allow ("mankind gain more by letting
each other live as seems good to themselves" turns on it), "vulgarly"
for commonly, "peculiar" for specific, "obtain" for hold good.
AND THE MEASURE OVERSTATES IT, so the hume rule governs: IF A SENTENCE
IS ALREADY CLEAR, LEAVE IT ALONE. Mill's famous sentences are already
perfect. Four of the nine must_contain pins are pinned UNCHANGED for
that reason, and two more encode a punctuation decision (his comma
after "the case" in "He who knows only his own side of the case, knows
little of that" goes, and the pin is written without it so the choice
cannot drift).

THE SECOND READING OF THE SOURCE EARNED ITS KEEP IN THE FIRST MINUTE
(the epictetus rule: parse as XML, then compare against an independent
regex reading that shares no code with the parser). It caught
kill_noterefs giving a removed anchor's tail to THE PREVIOUS ANCHOR
rather than to the previous SURVIVING element. Notes 7, 8 and 9 sit in
one paragraph — the Old Bailey jurymen — so note 8's tail was attached
to detached note 7 and half a sentence vanished. Every other word
present and in order; the ratio would not have moved enough to notice.
GENERALISE: when deleting elements, the destination for a tail is the
nearest preceding sibling THAT STILL EXISTS.
The same check taught its own lesson: COMPARE CHARACTERS, NOT TOKENS.
A raw reading replaces each tag with a space, so "<i>odium
theologicum</i>," tokenises differently from the parsed form — a
difference in the check, not in the text.

WHAT IS IN THE BOOK AND WHAT IS NOT, decided explicitly. The
dedication to Harriet Taylor and the Humboldt epigraph are Mill's and
stay (CLAUDE.md's rule that a dedication belongs in the book).
introduction.xhtml is a later editor's biographical essay and goes to
reference/ as a crib, on the bunyan/Offor precedent. THE ENDNOTES
SPLIT CLEANLY WITH IT: notes 1-5 are that editor's citations to his own
essay; notes 6-14 are MILL'S OWN and are inlined as "Footnote: ..."
paragraphs after the citing paragraph (the candle pattern), in Mill's
voice and not an editor's. Note 6 is the 1858 Press Prosecutions
footnote he added rather than change a word of his text, and says so.

WORD-FORM CHAPTER NUMBERS, DELIBERATELY. assemble.CHAP_LINE matches
only "Chapter <digits>: Title" and nests those as h3 under a Part
divider; this book has no Parts, so digits would have left the five
chapters nested under nothing and the Epigraph and Dedication looking
more important than they are. "Chapter One: ..." keeps everything at
one level and the contents flat, as hume/ does with "Section One".
NINE OF THE TWELVE FILES ARE CHAPTER PARTS, so the quixote trap is
live: heading, "(Part n of k)", blank, body, and part 2+ never
re-introduces the chapter. check.py compares later parts against part
1's MODERN heading, not the manifest title, because that is what the
renderer uses.

check.py also carries the hume COUNTED numeric diff (a set cannot see
a dropped duplicate), and asks assemble.EMPH ITSELF whether every
emphasis marker renders rather than approximating the test. THE
EMPHASIS PARITY CAUGHT A REAL DEFECT: I rendered "a clever nisi prius
advocate" as "a clever courtroom advocate", dropping one of Mill's 52
italic spans. The prose read perfectly and nothing else would have
seen it. Its archaism sweep exempts exactly ONE phrase, by exact
phrase (the grimm rule): Chapter Two's account of Christian morality
turns on the grammatical form of the commandments, '"thou shalt not"
predominates unduly over "thou shalt"', so modernising it there would
delete the observation.

SENSITIVE CONTENT — THE VERNE RULE IN FULL, NO NOTE ANYWHERE, AND ONE
EXCEPTION. Kept entire and unhedged: the despotism-and-barbarians
exception and "backward states of society ... in its nonage" (Chapter
One), which is the most discussed passage in the book's modern
reception and is Mill's own limitation on his own principle; the
attack on the Calvinistic theory; the whole China and "despotism of
Custom over the whole East" argument; the Mormon passage, including
his judgment that polygamy is a direct infraction of the principle of
liberty, his account of why a woman might still choose it, and his
refusal all the same to allow a "civilizade"; the critique of
Christian morality, with the Old Testament "intended only for a
barbarous people" and Paul's apparent sanction of slavery; and all of
Chapter Five, including the view that a man who cannot support
children should not be permitted to have them.
THE ONE EXCEPTION, and the reasoning is the hume "Laplander or Negro"
precedent exactly: in Chapter One's list of moralities made by an
ascendant class, "between planters and negroes" is rendered "between
planters and the people they enslaved". The Verne rule protects a
dated CLAIM that is part of the author's subject; Mill's subject there
is the morality that power produces, and the claim survives entire
when the noun is replaced by the relationship. MORE explicit, not less
— the ball/ Leonid precedent. "roturiers" becomes commoners in the
same list and nothing else moves.
A DATED WORD IS NOT A DATED CLAIM: Mahomedans and Mussulmans become
Muslims silently (he uses both interchangeably in one paragraph). But
inside the Sepoy footnote, where Mill QUOTES an Undersecretary of
State calling the faith of a hundred million British subjects "the
superstition which they called religion", the quotation is verbatim,
because exhibiting it is the argument.

VOICE: Mill is arguing with one reader in mind — an educated, decent,
liberal Englishman who agrees with him about religious toleration and
has never once thought about why. Courteous to the point of
self-effacement, concedes early and often, then does not budge. And
more ANGRY than his reputation suggests: the 1857 prosecutions, the
"moral police", the Sabbatarian legislation and the Maine Law are
written with his temper on a short leash, and that has to survive, as
do the two or three moments of open contempt ("the pinched and
hidebound type of human character", "the deep slumber of a decided
opinion") and the elegiac tone of Chapter Three, which is the most
beautiful writing in the book and is really about Harriet Taylor.
Cover: Friedrich's "Wanderer above the Sea of Fog" (1818), Commons
"File:Caspar David Friedrich - Wanderer above the sea of fog.jpg",
crop "1986x2980+170+0" — the canvas is 1:1.28, so the 2:3 rectangle is
centred, keeping the whole figure and the rock he stands on. At 2327
wide it is under commons_url's 4200 gate and the crop is in the
ORIGINAL's coordinates.

Edmund Burke's Reflections on the Revolution in France (burke/ — the
60th book; 1790, from Gutenberg #15679, the Works vol. III). 22 files,
13 sections, 97,846 -> 99,967 words, ratio 1.02 (verify --min-ratio
0.85 --max-ratio 1.3).

THE JUSTIFICATION IS THE hume/mill CASE, class 3 (technical calque):
archaism 0.25 per 1,000 words — the LOWEST of any book taken on, below
several struck from the roadmap as too clean — against calque 39.7.
Nothing in it sounds old. What blocks it is 200-word periodic sentences
and a vocabulary used with total consistency: "prejudice" is inherited
judgement and not bigotry, "prescription" is title by long possession,
"speculation" is theorising, "manners" is the whole moral texture of a
society. The hume rule governs and hard — HIS FAMOUS SENTENCES ARE
ALREADY MODERN, and most must_contain pins are pinned UNCHANGED.

STRUCTURE FROM THE AUTHOR, NOT FROM US. Burke wrote one continuous
letter with no chapters, but he PUNCTUATED it with twelve `* * * * *`
breaks of his own. prep.py cuts on those, giving 13 sections; the
titles are new writing (the soap-bubbles/augustine precedent). Four
sections needed oversize splits, so 22 files.

THE REAL WORK WAS THE SOURCE, AND THE LESSON GENERALISES TO ANY SCAN.
The translation itself was ordinary; every defect found was of the class
verify.py structurally cannot see, and most were OCR damage that is
INDISTINGUISHABLE FROM CONTENT because the result is a real English word
in a plausible place:
    "They TOLL the people"  (tell)      "he must HE sensible"   (be)
    "WORE endowed with"     (were)      "the conquest AXE"      (are)
    "persons are to MATE good"(make)    "to LENDER them"        (render)
    "for WHOSO present relief"(whose)   "ministers in PRANCE"   (France)
    "this new RELIGIONS persecution"    "IFS judicial authority"(its)
    "HO spent the income"   (He)        "PROM the general style"(From)
    "those who US TEN"      (listen)
NONE of these moves the word ratio, the emphasis parity, must_contain or
the numeric diff. burke/ocr_sweep.py (NEW, REUSE IT) turns each one
found into one that cannot recur; it REPORTS and never fixes, and it is
deliberately noisy — two of its findings were CORRECT as printed
("protect all religions" is the plural noun; "ut bis jam vidimus" is
Latin for twice), and being made to look is the whole mechanism. IT IS
NOT A GUARANTEE: three errors in file 017 got past it because its F/P
pattern had been written around the single word that first produced it.

A COMPUTED TABLE THAT DOES NOT COMPUTE (the fleming rule, again).
Burke's footnote on the Assembly's charity spending gives every item in
livres AND sterling with a total for both. Every sterling row is its
livres figure over exactly 24 except the grain premiums, printed
235,329 9s 2d where 5,671,907/24 = 236,329 9s 2d — and only with the
correction does the column reach its own printed total, which as printed
it misses by exactly £1,000. TWO INDEPENDENT RELATIONS AGREE ON WHICH
CELL IS WRONG, which is what makes it a correction and not a guess.

FOREIGN QUOTATIONS: KEEP VERBATIM, THEN GLOSS. Burke quotes at length in
French and Latin because his correspondent read both; his modern reader
does not, and an untranslated block is a hole in the argument rather
than a piece of scholarship. The original stands (it is a document, and
his italics inside it are part of what he is pointing at) and a plain
English rendering follows, CARRYING NO EMPHASIS MARKERS so parity is
undisturbed. This is why files 008 and 014 run at 1.15 and 1.08 against
the book's 1.02 — the extra words ARE the gloss. Scan errors inside a
quotation are still scan errors and are repaired ("qui OUT déterminé",
"ON plutôt", "à RÉCRÉER" for recréer, which inverts the sense of the
sentence the whole footnote exists for): a quotation is protected from
us, not from its scanner.

check.py (the euclid-rivals per-book pattern) carries the augustine
thou-sweep, the hume COUNTED numeric diff, footnote parity, and
emphasis parity asked of assemble.EMPH itself. TWO SIGNED ALLOWANCE
TABLES, both with the reason written beside each entry, because an
allowance without one is just a loosened check: EMPH_DELTA (the printer
sets the pound sign as an italic "l." after the figure — typography, not
emphasis; and two words of small-capital contrast that become italics)
and NUM_DROPPED ("Cic. Off. 1. 2." is "l. 2", LIBER 2, with the ell
scanned as a one).
THE EMPHASIS PARITY EARNED ITS KEEP TWICE OVER: at file 017 it caught a
DROPPED TAIL. I read that source with two sed windows ending at line 60
and the file has 61 — the last being La Tour du Pin's speech to the
Assembly, which the whole army section is built on. It was simply
absent, and the ratio came in at 0.98, inside every band. It was caught
only because the missing paragraph happened to carry three italic spans.
THE ball/ RULE IS THE FIX: READ THE WHOLE SOURCE FILE, NEVER A LINE
RANGE.

SENSITIVE CONTENT — THE VERNE RULE THROUGHOUT, NO NOTE ANYWHERE IN THE
VOLUME, AND ONE EXCEPTION. Kept entire and unhedged: the Marie
Antoinette passage with its ten thousand swords, which even sympathetic
contemporaries thought absurd; "learning will be cast into the mire and
trodden down under the hooves of a swinish multitude", the phrase that
made him hated for a century and that he never retracted; the whole
jeering page on Lord George Gordon's conversion to Judaism, offering to
swap "our Protestant rabbi" for the Archbishop of Paris and pricing the
ransom in compound interest on the thirty pieces of silver — the ugliest
thing in the book, and Burke's own argument about who is applauding the
Revolution; the contempt for the Assembly as country attorneys; and the
defence of prejudice, prescription and hereditary rank.
THE ONE EXCEPTION is the mill/ "planters and negroes" precedent exactly:
"As the colonists rise on you, the negroes rise on them" becomes "the
people they hold enslaved rise against them". The Verne rule protects a
dated CLAIM that is part of the author's subject; Burke's subject there
is the logic of the rights of men running past the men who declared it,
and the claim survives ENTIRE when the noun is replaced by the
relationship — MORE explicit, not less (the ball/ Leonid precedent).
"massacre, torture, hanging! These are your rights of men!" stands.

VOICE: a working politician's prose, and much funnier and angrier than
its reputation — the Assembly's finance is "paper pills at thirty-four
millions sterling a dose", their politicians "do not understand their
trade, and so they sell their tools", and a chapter of constitutional
arithmetic ends with the three principles held together "like wild
beasts shut up in a cage to claw and bite each other". Keep the
periodic sentences' JOINTS visible while unstacking them; the argument
is cumulative and the subordinate clauses are the argument.
Cover: Hubert Robert's "The Bastille in the First Days of Its
Demolition" (1789), Commons "File:The Bastille in the first days of its
demolition, by Hubert Robert.jpg", crop "1695x2543+620+66" — a 2:3
slice of a 1.5:1 canvas, taken inside the painted frame and centred on
the great tower with the demolition crew silhouetted along its parapet.
Robert was a painter of ruins who was himself jailed in the Terror. The
crop is in the coordinates of the 4000px RENDITION (the original is
5162 wide, over commons_url's 4200 gate) — the bunyan/quixote trap.
NOTE the stale-draft trap bit again and cost a rebuild: `se create-draft`
keys the build directory on the SLUG, so it is
build/ebooks/edmund-burke_reflections-on-the-revolution-in-france and
NOT build/ebooks/burke. `rm -rf build/ebooks/<book-dir>` removes nothing
and the old metadata ships silently.

Mill's The Subjection of Women (subjection/ — the 59th book; written
1861, published 1869, from Standard Ebooks). 8 files, 4 chapters,
44,006 -> 43,483 words, ratio 0.99 (verify --min-ratio 0.85
--max-ratio 1.15). READ mill/ FIRST: same author, same decade, same
pipeline, and every rule there carries over.

EASIER THAN On Liberty IN THE TWO PLACES THAT COST WORK THERE. No
editorial introduction to separate out, and ALL THREE endnotes are
Mill's own, so all three inline as "Footnote: ..." with nothing going
to reference/. The cross-check passed on the FIRST run, because
prep.py was mill/prep.py with the surviving-predecessor noteref fix
already in it.

HARDER IN ONE: ALL EIGHT FILES ARE CHAPTER PARTS, so the quixote trap
is at maximum. And the 1869 printing heads each chapter with a bare
Roman numeral, so the four titles are NEW WRITING (the soap-bubbles
and augustine precedent) — which makes them the one place in the book
where a wrong word is invisible to every mechanical check. They were
written from each chapter's argument, verified by reading the first
and last paragraph of each.

THE JUSTIFICATION IS hume/mill CLASS 3 AGAIN, plus a second and
stronger one. "Disability" is the dangerous false friend and it is
everywhere: it means a LEGAL BAR, not an impairment. But the better
case is that this book is far less read than On Liberty and much more
startling — written fifty years before British women could vote, and
arguing that the nature of women is simply unknown because it has
never been observed out of chains. In Victorian prose a reader files
that as a period document, which is the misreading the retelling
exists to prevent.

VOCABULARY THAT MUST NOT BE SOFTENED: bondage, bondservant, slave,
master, despotism. Chapter Two is a point-by-point LEGAL comparison,
not a figure of speech, and Mill twice says wives are not in general
TREATED as slaves are — which is exactly what licenses him to insist
that in law they are worse placed, since a slave has hours off and an
acknowledged right to refuse his master the last familiarity. KEEP
BOTH HALVES. Dropping the qualification makes him cruder than he is;
softening the claim makes him tamer.

TWO DEFECTS I INTRODUCED AND CAUGHT BY READING, both in one file, and
both of the class no check in this project can see:
  1. A SILENT EMENDATION. The source says the lord was led to believe
     his vassals were really SUPERIOR to himself; I wrote "inferior"
     because it looked like a misprint. It is not: the two branches
     are a gradation — believing them actually superior, or merely as
     good as himself — and both are "no merit of his own". Restored.
     A source oddity is either KEPT or corrected WITH A LOGGED REASON;
     it is never quietly flipped.
  2. A DROPPED NEGATION. "values itself upon accidental advantages,
     NOT of its own achieving" came out without the "not", asserting
     the opposite. It reads perfectly.
MEASURED AND REJECTED, so it is not re-tried blind: a per-file
negation-count check. On known-good files the modern/source ratio runs
0.96-1.04, and the dropped "not" moved a 91-negation file to 88, ratio
0.97 — inside the noise, because rewording legitimately moves
negations about ("cannot" -> "is unable to"). The regex is noisy too:
an `un\w+` class counts "unfolded" as a negation. There is no
threshold that separates the defect from the noise. This class is
caught by reading and by nothing else.

Cover: Emily Mary Osborn's "The Governess" (1860), Commons "File:
Emily Mary Osborn - The Governess - Google Art Project.jpg", crop
"3268x4903+0+0" — the governess in plain black standing apart on the
left, hands clasped, while the mother in scarlet velvet and four
children occupy the right. The trim comes off the RIGHT because she
stands hard against the left edge and is the reason for the choice.
At 4051 wide it is under commons_url's 4200 gate, so the crop is in
the ORIGINAL's coordinates. Painted by a woman, one year before Mill
wrote the book, and it is the one occupation Chapter Three says was
open to an educated woman.

Baruch Spinoza's Ethics (spinoza/ — the 61st book; Elwes' 1883
translation from Standard Ebooks). All five Parts, 17 files, 91,300 ->
87,619 words, ratio 0.96 (verify --min-ratio 0.85 --max-ratio 1.15).
Published the year he died, and on the Index within four.

THE JUSTIFICATION IS hume/mill/burke CLASS 3 (technical calque):
archaism 0.29 per 1,000 words against calque 38.6. But the SENTENCES
are the shortest of any book taken on — mean 17.9 words, only 16% over
35 — so the hume rule governs harder here than anywhere: IF A SENTENCE
IS ALREADY CLEAR, LEAVE IT ALONE. A file in which every sentence has
been rewritten has been damaged. The blockers are a small locked
vocabulary used with total consistency (substance, attribute, mode,
affection, conatus/endeavour, adequate idea) and the false friends
around it — "affection" is a modification and not fondness, "passion"
is being acted on, "idea" is not a notion in a head, "perfection" is
reality.

THE REAL WORK WAS NEITHER VOCABULARY NOR SYNTAX BUT THE APPARATUS, and
this is a class of work no earlier book here has needed. The Ethics is
bound together by 1,084 cross-references and Elwes prints them as
Spinoza's contemporaries did — "(II. vii. Coroll.)", "(by the last
Prop.)", "(by the Coroll. of the preceding Prop.)" — IN A HUNDRED AND
THIRTY-SEVEN DISTINCT SHAPES. ALEX'S RULING: RESOLVE AND NORMALISE.
Every one is written out in full and in one canonical form, arabic,
with the scope always explicit ("Part 3, Proposition 9, Note";
"Proposition 22 of this Part, Corollary"). A reader can now follow a
proof without counting on their fingers, and it is the edition's one
real contribution. See spinoza/refs.py, and the toolkit around it
(triage/refcheck/gap/leftover/refused, plus test_refs.py).

FOUR LESSONS FROM THE RESOLVER, all of them general:
  1. A RELATIVE REFERENCE INSIDE A COROLLARY POINTS AT N, NOT N-1
     (Alex's ruling). A Corollary is drawn FROM the proposition it
     hangs on, and that proposition is what a reader looking up the
     page finds first. Same for a Note and an Explanation.
  2. I COUNTED THE REFERENCES WRONG FOUR TIMES — 430, then 598, then
     1,027, then 1,075, then +114 unparenthesised — AND EVERY COUNT
     AGREED WITH EVERY OTHER COUNT, because all of them derived from
     one blind regex. A number confirmed by the tool that produced it
     is not confirmed. What fixed it was asking DIFFERENT questions:
     what falls in the gaps between matches (gap.py), what tokens are
     left over (leftover.py), what the resolver REFUSED (refused.py),
     and reading the prepared text.
  3. WHITESPACE MAY CROSS A NEWLINE BUT NEVER A BLANK LINE. A `\s*`
     in a citation's tail ate the paragraph break and DELETED Part
     III Proposition 27's second Corollary. Two narrower fixes were
     wrong before the rule came out right:
     `_WS = r"(?:[ \t]|\n(?![ \t]*\n))*"`. Reuse it.
  4. `[ivxlc]+` WITHOUT WORD BOUNDARIES MATCHES THE "i" IN "is", which
     produced "This Proposition 1 of this Parts evident". Roman
     numerals always need `\b`.

check.py's DECISIVE CHECK IS CITATION PARITY: every citation in a
modern file, parsed back into its (part, kind, number) triple and
compared as a multiset against the prepared source. Nothing else can
see a citation quietly reworded, and I did it — plus moving a
parenthesis boundary and writing word-form Part numbers where the
source had digits. Plus proposition sequence, Q.E.D. parity, the
augustine thou-sweep, emphasis parity via assemble.EMPH itself, and
the hume COUNTED numeric diff (with the four enumerator forms stripped,
or every numbered list item fires).
A CHECK AND A CONVENTION MUST NOT PULL OPPOSITE WAYS. "whereof" inside
a citation was demanded by citation parity and forbidden by the
archaism sweep; the fix is to modernise it IN prep, so both sides agree
about what the source says (same precedent as cf. -> compare).

SHARED FIX — parse_heading MISSED THE THIRD ORDINAL FORM. It knew the
roman ("Part I: Of Man") and the bare word ("Part Two"), but not A WORD
ORDINAL FOLLOWED BY A COLON AND ITS OWN TITLE, which is what this
collection actually writes. So "Part One: Concerning God" came back
with NO ordinal, and build_ebook fell back on the sequence number:
every part divider in the epub read "Part 1" with the real name demoted
to a bridgehead reading "One: Concerning God". boethius, bunyan and
wealth-of-nations shipped that way and nothing had ever looked. The
same heading also fed a span typed z3998:roman an arabic digit, which
is the s-026 [Manual Review] item on every part file — now converted.
NOTHING IN THE TOOLCHAIN CHECKS EPUB PART HEADINGS; this was found by
reading the built XHTML, which is worth doing once per illustrated or
multi-part book.

THE MANIFEST TRAP THAT PRODUCED IT: "part"/"of" mean WHICH PIECE OF A
SPLIT CHAPTER, not which Part of the book. Writing "part": k, "of": 5
stitched each Part into one monolithic chapter — 17 sections collapsed
to 5, one of them 22,819 words — and the page and epub both agreed with
each other, so only the ToC's length gave it away. Each file is its own
section: "part": 1, "of": 1, "chapter": true, with "part_before" on the
first file of each Part.
AND EVERY FILE MUST OPEN WITH ITS HEADING LINE, because
assemble.strip_front takes the first non-blank line as the section
heading and drops it. The translations were written before prep wrote
headings into chapters/, so a retitle pass was needed (spinoza/
retitle.py, idempotent).

SECTION TITLES ARE NEW WRITING and are deliberately mechanical
("Propositions 18 to 36", "Definitions of the Emotions"), because the
Ethics has no chapters and any interpretive title would put a claim in
Spinoza's mouth about what a run of propositions is FOR. Same reasoning
as augustine, opposite decision, and the reason is the geometrical
form: the reader is meant to find Proposition 36, not a theme.

VOICE: the flattest prose in the collection, and that is the point —
forty-eight emotions are defined in order, hatred and jealousy and
ambition among them, with no more moralising than a geometer gives a
triangle. Do not warm it up. The exceptions are the four Prefaces and
the Appendix to Part One, where he drops the geometry and is suddenly
savage about final causes and the men who take refuge in "the will of
God, that sanctuary of ignorance"; those need real work and carry the
book's heat. THE PINS WERE WRITTEN FROM THE PREPARED TEXT, NOT FROM
MEMORY (the epictetus rule), and one of them is why that rule exists:
"God or Nature" was about to be pinned "God, or Nature", with a comma
Elwes does not use, and no correct translation could ever have
satisfied it. Also pinned: the parallelism doctrine, "a kingdom within
a kingdom", "Blessedness is not the reward of virtue, but virtue
itself", and the last sentence of the book.
THE VERNE RULE, no note anywhere in the volume: the identification of
God with Nature, the denial of free will and of final causes, the
reading of Genesis in Part 4 Proposition 68 as a story Moses used to
signify something else; "womanish pity" as the thing reason is set
against; the contempt for what "the vulgar" believe; and the jealousy
passage of Part 3, explicit about the body in a way Elwes is not prim
about and neither is this edition.
Cover: Vermeer's "The Astronomer" (1668), Commons "File:Johannes
Vermeer - The Astronomer - 1668.jpg", crop "2908x4363+240+0" — a man
alone at a table with his hand on a celestial globe, painted in the
Dutch Republic in the year Spinoza was writing. The Commons original
is over commons_url's 4200 gate, so what arrives is the 3840px
rendition and the crop is in ITS coordinates (the bunyan/quixote
trap); the cached build/covers/spinoza.jpg is 3840x4363, which is how
to tell which case you are in.

Mary Wollstonecraft's A Vindication of the Rights of Woman
(wollstonecraft/ — the 62nd book; 1792, from Standard Ebooks). All
thirteen chapters plus the Dedication to Talleyrand and her own
Introduction, 21 files, 84,590 -> 85,835 words, ratio 1.01 (verify
--min-ratio 0.85 --max-ratio 1.15). READ mill/ AND subjection/ FIRST:
same decade of English, same publisher, same pipeline, and Mill's book
is the sequel to this one.

THE JUSTIFICATION IS hume/mill CLASS 3 (technical calque): calque 35.0
with 42% of sentences over 35 words, against an archaism score low
enough that on that axis alone it would have been struck. Nothing in it
sounds old. What blocks it is periodic sentence architecture and a
technical vocabulary used with total consistency — and the FALSE FRIENDS
are unusually dangerous here. "SEXUAL CHARACTER" is the book's central
term and means a character proper to one's sex; the modern reading is
not merely wrong, it is obscene, and it is Chapter Two's entire subject.
Also sensibility (capacity for feeling), manners (the moral texture of a
society, as burke/), accomplishments (the finishing-school skills),
suffer (allow), want (lack).
AND THERE IS A SECOND JUSTIFICATION, which is the stronger one: this
book has a reputation that stands in for reading it. Its actual claim is
not "women are equal" but something harder — that the character women
have is an ARTEFACT of their education, and nobody knows what women are
like because nobody has ever let them find out. In 1792 prose a reader
files that as a period document, which is the misreading the retelling
exists to prevent.

THE CHAPTER TITLES ARE HERS, AND STANDARD EBOOKS DROPPED THEM. SE prints
a bare Roman numeral in the <h2> and in its own ToC; the 1792 printing
titles every chapter ("ANIMADVERSIONS ON SOME OF THE WRITERS WHO HAVE
RENDERED WOMEN OBJECTS OF PITY, BORDERING ON CONTEMPT"). So unlike
subjection/, where the titles had to be NEW WRITING, here they are the
author's and are MODERNISED like any other sentence of hers — the ball/
rule for a source that captions its own plates. Recovered from Gutenberg
#3420's contents list, CROSS-CHECKED AND NOT REMEMBERED. GENERALISE:
when a modern edition prints bare numerals, go and look at whether the
original had titles before deciding they are yours to invent.

THE ONE DEPARTURE FROM THE LECTURE-VOLUMES RULE, and it is deliberate:
QUOTED PROSE IS MODERNISED WITH HER OWN, quoted VERSE is verbatim.
Chapter Five is 16,000 words of Rousseau, Fordyce, Gregory and
Chesterfield quoted at length and then taken apart line by line. If the
quotations stay in 1762 English while her replies are modern, the reader
can follow the reply and not the charge — the exact failure the
retelling exists to prevent. Two further reasons it is safe: Rousseau's
Emile is quoted in an eighteenth-century ENGLISH TRANSLATION, so the
archaism there is the translator's costume and not the author's (the
nights/ reasoning), and she is usually quoting in order to ridicule,
which requires the reader to understand the words. NOTHING IS SOFTENED
INSIDE THE QUOTATIONS; they are the evidence. Verse (Milton, Dryden,
Pope, and "God is thy law, thou mine" pinned in must_contain) stays as
printed, attributions included.
SCRIPTURE COUNTS AS QUOTED PROSE and is modernised too — Job 38:11 and
the talents of Matthew 25 — on the augustine precedent that the book has
ONE voice. Contrast soap-bubbles, which kept Proverbs 23:31 in the King
James wording, where the verse is a set-piece and no argument depends on
the reader following it.

CHECK.PY, and the one lesson worth taking away from it: A STRUCTURAL
EXEMPTION CAN BEAT THE grimm EXACT-PHRASE RULE, WITH AN ARGUMENT. The
archaism sweep now skips tab-indented lines, because those blocks are
required to be verbatim Milton and Dryden, so an archaism inside one is
the poet's BY CONSTRUCTION — and check 3 independently pins every verse
block's line count, so the exempted region cannot quietly grow. The
exact-phrase version was tried first and was incomplete WITHIN ONE FILE:
it listed Eve's five lines and then fired on Adam's eleven-line reply
the moment chapter Two was written. A list that has to be extended every
time a poet is quoted is not an exemption list, it is a leak. Proved by
reintroducing "hath" into ordinary prose and watching the sweep fail
(the boethius rule). THOU_OK stays for PROSE, and stays empty.
The rest is the standard set: heading/part parity (ELEVEN of 21 files
are chapter parts, so the quixote trap is near maximum), section-heading
parity asked of assemble.is_subheading ITSELF, verse integrity (blocks
and line counts, the boethius check), emphasis parity via assemble.EMPH,
the hume COUNTED numeric diff, and footnote parity.

THE CROSS-CHECK EARNED ITS KEEP IN THE FIRST RUN, as it did in mill/ and
epictetus/. THE ATTRIBUTION IS PART OF THE QUOTATION and lives in a
<cite> INSIDE the blockquote, so collecting only the <span> lines
dropped "—Dryden" silently. Nothing else would have noticed: the word
ratio does not move for one word.

SENSITIVE CONTENT — THE VERNE RULE THROUGHOUT, NO NOTE ANYWHERE, AND TWO
EXCEPTIONS OF THE mill/burke CLASS. Kept entire and unhedged: the
PHYSICAL-INFERIORITY CONCESSION of the Introduction, which modern
readers find the most surprising thing in the book and which is
LOAD-BEARING (the whole structure is "grant that, and nothing else
follows"); her contempt for women as they are ("mere propagators of
fools"), without which the argument collapses, since her point is that
this is what the education PRODUCED; the two "Muhammadan" passages,
where the CLAIM is hers and part of her attack on Milton while the WORD
is modernised as mill/ does; "the Indians worship the devil"; her
Dissenting Christianity, which she means; and the slavery vocabulary,
which is deliberate and never softened.
THE TWO EXCEPTIONS are both racial nouns replaced by the relationship,
where the claim survives entire: "like the poor African slaves" ->
"like the enslaved Africans" (Chapter Nine), and "the savage desire of
admiration which the black heroes inherit from both their parents" ->
"that enslaved people inherit from both their parents alike" (Chapter
Thirteen), where the point is that a love of ornament is HUMAN and not
female, which is why "from both their parents" is the load-bearing
phrase. Her abolitionist passages stand entire: "Is sugar always to be
produced by human blood?" and the minister who rivets the chains "by
sanctioning the abominable trade".

VOICE: far funnier and angrier than her reputation. "A wild wish has
just flown from my heart to my head, and I will not stifle it though it
may excite a horse laugh." She wrote the book in six weeks and refused
to polish it, and SAYS SO — "I shall not waste my time in rounding
periods... I shall be employed about things, not words!", which is this
project's thesis in an author's own words and is pinned. So the hume
rule governs hard: IF A SENTENCE IS ALREADY CLEAR, LEAVE IT ALONE. Most
pins are pinned UNCHANGED. The work is unstacking the sentences where
the stack has collapsed, which happens mostly in Chapters Four and Five.
KEEP THE METAPHORS — the gilt cage, the rattle that must jingle in his
ears, the flowers planted in too rich a soil. They are compressed
argument, not ornament.
Cover: Adélaïde Labille-Guiard's "Self-Portrait with Two Pupils" (1785),
Commons "File:Adélaïde Labille-Guiard - Self-Portrait with Two Pupils -
The Metropolitan Museum of Art.jpg", crop "3820x5730+0+0" — a woman at
her easel with palette and brushes, looking straight out, with two young
women she is training behind her. The parallel to subjection/'s Osborn
is deliberate: a painting by a woman, from the book's own decade,
showing the thing the book argues for. The canvas is 4523x6479, over
commons_url's 4200 gate, so what arrives is the 4000px rendition at
4000x5730 and THE CROP IS IN THE RENDITION'S COORDINATES; it is taller
than 2:3, so the crop is height-limited and the 180px comes off the
RIGHT, because the easel at the left edge is the reason for the choice.
NOTE: `se lint` raises two [Manual Review] items wanting a `win` relator
and a frontmatter inflection on introduction.xhtml. The Introduction is
WOLLSTONECRAFT'S OWN, not an editor's, and carries four of the
must_contain pins; both are correctly ignored.

Sun Tzu's The Art of War (sun-tzu/ — the 63rd book; Lionel Giles's 1910
translation from Gutenberg #132). All thirteen chapters, verses AND
commentary, 14 files, 41,012 -> 40,290 words, ratio 0.98 (verify
--min-ratio 0.85 --max-ratio 1.3).

IT IS A CRIB MODERNISATION, NOT A TRANSLATION FROM THE ORIGINAL, and
that is said in the subtitle on the page and in the epub description.
Sun Tzu wrote about 6,000 Chinese characters; what is modernised here is
Giles's English. Every other from-the-original book here (ovid/,
galileo/, the Vernes) works from the source language with a crib
alongside; this one cannot, because nobody here reads classical Chinese.
Say so rather than implying otherwise.

THE COMMENTARY IS THE BOOK — 53% of the text, 416 bracketed blocks by
eleven Chinese generals and scholars over two thousand years. Most
modern editions print the verses alone, which is why this one is worth
having. Giles's own sixteen footnotes are kept too. THREE VOICES, and
the reader can tell them apart ONLY by the label, so check.py's decisive
check is VOICE PARITY: the sequence of "Commentary:" / "Footnote:" /
verse, per file, compared against the source. A label that vanishes
hands a commentator's gloss to Sun Tzu; one that is invented does the
reverse. BOTH READ PERFECTLY, and neither moves the ratio.

THE SOURCE DEFECT CLASS THIS BOOK IS MADE OF: GUTENBERG'S BRACKETS DO
NOT BALANCE, and every imbalance silently reassigns a voice. Eleven are
corrected in prep.py's SOURCE_FIXES, each asserted. The lesson that
generalises is that BRACKET ARITHMETIC IS THE WRONG TOOL — classify by
paragraph (first character opens, an unmatched closer ends) and then fix
the specific breakages by hand:
  - A MISSING OPENING BRACKET makes a gloss read as Sun Tzu's own text.
    Three of these, the largest being Giles's 500-word review of how
    badly the Nine Grounds hang together, which would have shipped as
    Sun Tzu criticising his own book.
  - A MISSING CLOSING BRACKET makes the block swallow the verse after
    it. Eight, and each needed READING to find where the note ends.
  - A FOOTNOTE MARKER'S BRACKET IS NOT A STRAY. Collapsing the "] ]"
    transcription noise ate the block's own closer wherever a note ended
    "[1] ]", and the casualty was "All warfare is based on deception" —
    the most quoted line in the book — shipping as somebody's commentary
    on itself. Ride the markers through on a sentinel.
  - NOR IS A NESTED CITATION'S BRACKET A STRAY. Four notes end on a
    bracketed source reference, so the run is "inner close + block
    close". Same sentinel, and NOT applied to the one that looks
    identical and is not (its citation has no opener either).
  - A TRAILING "]" IS NOT ALWAYS THE BLOCK'S. Decide by BALANCE, never
    by the last character, and strip EXACTLY ONE delimiter at each end:
    .strip("[] ") took a citation's closer along with the block's and
    left an opening bracket dangling in five of the fourteen files.
Every one of these is invisible to verify.py, and the two that reassign
a voice are invisible to a reader who does not have the source open.

GILES'S PAGE REFERENCES TO HIS OWN EDITION, five of them, are
meaningless in a reflowable page. Four RESOLVE and were rewritten to
chapter-and-verse; one points into his introduction, which this edition
does not carry, so the locator is dropped and the battle it refers to is
described in full in the same sentence. All five are in check.py's
NUM_DROPPED with the reason beside them — the hume COUNTED numeric diff
caught every one. References to OTHER authors' books ("Marshal Turenne,"
p. 311) are kept as printed, the euclid-rivals rule.

VOICE: three registers kept apart. Sun Tzu is aphoristic and already
modern — the hume rule governs and most must_contain pins are pinned
UNCHANGED, because his sentences are the reason the book is quoted. The
commentators are a two-thousand-year argument, by turns pedantic,
anecdotal and rude about each other. Giles is an Edwardian scholar who
is funny, opinionated ("But this is very weak") and given to comparing
everything to Napoleon, Cromwell and Turenne; the connective prose and
his apparatus are where the actual work is.
PINS MUST COME FROM THE PREPARED TEXT (the epictetus rule), and this
book punishes memory harder than most: "swift as the wind", "the
victorious warrior wins first and then goes to war" and the sheathed
sword are all famous Sun Tzu and NONE of them is in Giles. They belong
to later translations, so a pin written from memory could only be
satisfied by a translation that had drifted to somebody else's wording.
LOCKED: the Moral Law (his tao, and his own note says it is not
morality), *cheng* and *ch'i*, energy (shih), method and discipline
(fa), *li* and *picul*, and Wade-Giles spelling throughout. Giles's
editorial Latin (*I.e.*, *supra*, *infra*) is Englished and correctly
loses its italics with the Latin — exempted in check.py BY RULE, not by
a per-file allowance, so a dropped *li* or *cheng* still fails.
THE VERNE RULE, no note anywhere in the volume: Giles's aside that "a
strange lack of logical perception is shown in the Chinaman's
unquestioning acceptance of glaring cross-divisions" stands as HIS
judgement of the commentators' logic (the noun goes, on the mill
"planters and negroes" precedent, because it names the same people and
carries no part of the claim); "some of which would occur only to the
Oriental mind" is KEPT ENTIRE, because there the dated category IS the
claim. Swap a slur WORD for the neutral name of the same people; never
swap out the CLAIM. The "Northern barbarians" of the Hou Han Shu are
kept for the same reason — that is the Chinese state's political
category, not a slur standing in for a people already named.
Cover: Shang Xi's "Guan Yu Captures General Pang De" (c. 1430), Commons
"File:Shang Xi, Guan Yu Captures General Pang De.JPG", crop
"1241x1862+300+0" — the general seated under a pine with his officers,
taken out of a nearly square Ming hanging scroll; the crop deliberately
leaves the bound prisoner outside the frame, so what is left is a
commander deciding something, which is the book. At 2200 wide it is
under commons_url's 4200 gate and the crop is in the ORIGINAL's
coordinates. FOUR CANDIDATES WERE LOOKED AT AND REJECTED BY LOOKING:
the two best-named "bamboo slips of the Art of War" photographs turn out
to be a museum caption card and a 1996 gift-shop facsimile behind glass.
`se lint` raises t-057 in eleven chapters ("`<p>` starting with lowercase
letter") and y-003 in four; both are correct here, because a verse is
routinely interrupted by a commentary block and resumes in a new
paragraph.
