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
  `site/template.html` → `site/{book}.html`
- `legacy/` — the original API-based batch translator and prompt templates,
  plus old book-specific assemblers. Reference only; see `legacy/README.md`
  (note: their `max_tokens` settings truncate full chapters).

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
Cover: Blaikley's painting of Faraday's own 1855 Christmas Lecture,
Commons "Professor Faraday lecturing at the Royal Institution, 27th
December, 1855 RIIC 0006 20110213 BAL EP.jpg", crop "1847x2771+1500+86"
(a 2:3 slice out of a landscape painting, centred on Faraday at the
bench).
