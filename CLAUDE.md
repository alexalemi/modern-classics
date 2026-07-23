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
