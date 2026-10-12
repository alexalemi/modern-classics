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
- Place the source text in a new directory: `books/{book}/`. Every book
  lives under `books/` (moved there 2026-10-12); below, `{book}/...` is short
  for `books/{book}/...`. The tools take a bare name (`python3 assemble.py
  flatland`) and resolve it through `paths.book_dir()`.
- Create a `{book}/env` file with metadata:
  ```
  ORIGINAL_WORK=Title of the Work
  AUTHOR=Author Name
  DATE=Year
  SUBTITLE=optional subtitle shown under the title
  SOURCE_NAME=Project Gutenberg          # optional attribution link
  SOURCE_URL=https://www.gutenberg.org/ebooks/NNNN
  MODERN_YEAR=2026
  MODEL=Claude Opus 5.5                 # the model that did the translation
  MODEL_EVIDENCE=how MODEL is known
  ```
  MODEL is recorded so books can be revisited as models improve. Write the
  model that translated `modern_chapters/` (subagents included). If a
  subagent model was overridden, say so in MODEL_EVIDENCE. The fields for
  books before 2026-10-09 were backfilled from the Co-Authored-By trailer on
  the commit that first added `modern_chapters/`. `MODEL=unknown` marks the
  22 early books whose commits carry no trailer.
- Split the source into chapter files with `splitter.py`:
  ```
  python3 splitter.py books/{book}/source.txt --headings '^CHAPTER [IVXL]+\..*$'
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

Then put the book on the front page: add `SHELF=` to its `env` (one of
`build_index.SHELVES`) and a one-line blurb to `build_index.BLURBS`, then
`python3 build_feeds.py` (makes the cover thumbnail) and
`python3 build_index.py`. `site/index.html` is generated — never edit it
by hand. The build refuses a book with a shelf but no blurb, or no cover.
The cover (ebook_meta.json `cover`, a public-domain artwork on Commons) must
not show nudity; see "COVERS: NO NUDITY" in BOOKS.md for the line.

### 6. Editor's Introduction — context for a modern reader

Every book carries `{book}/introduction.txt`: 300-500 words of NEW
WRITING telling the reader who wrote this, when, what was happening, what
the book was for, what convention would otherwise read as strange, and
what this edition did. `assemble.py` renders it on the page above the
Contents and `build_ebook.py` makes it the epub's first frontmatter
section. See `INTRODUCTIONS.md` for the full specification and
`check_introductions.py` for the checks.

Load-bearing details (root not `modern_chapters/`; heading is "Editor's
Introduction"; modern page only, never `--original`; a well-written wrong
fact is the one defect no check can see) are in `INTRODUCTIONS.md`.

### 7. Restored Editions — books that need an edition, not a retelling

The author's prose unchanged, plus apparatus: captions and alt text for
every plate, proper markup, an editor's introduction, a real epub. Two
shapes: COMPANION (a retelling's `--original` page, ORIGINAL_TEXT=yes) and
NATIVE (no retelling, EDITION=restored). Listed on site/restored.html,
built by build_restored.py from env. Full notes — composed
modern_chapters/, pinned plate ids, scan-vote witnesses, math typesetting,
Helmholtz locators — are in `RESTORED.md`; captioning spec in `CAPTIONS.md`.

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
books/{book}/              # One directory per book
  env                      # Metadata (see Setup above)
  {source}.txt             # Original full text
  chapters/                # Split chapter files (000.txt, 001.txt, ...)
  manifest.json            # File -> chapter map; drives translation + assembly
  text_analysis.txt        # Translation strategy document
  agent_instructions.txt   # Standing prompt for translation subagents
  running_notes.txt        # Shared consistency ledger, updated between batches
  must_contain.txt         # Famous passages verify.py checks for
  introduction.txt         # Editor's introduction (NEW WRITING, see below)
  modern_chapters/         # Translated chapters (000.txt, 001.txt, ...)
```

## Tooling

- `paths.py` — ROOT, BOOKS, `book_dir(name_or_path)` and `all_books()`: the
  one place that knows books live in `books/`. A book is still NAMED by its
  directory name everywhere else (ebook_meta "dir", covers, the epub uid,
  which deliberately still reads `{REPO}/tree/main/{book}`).
- `splitter.py` — source text → `chapters/` + `manifest.json` (heading-regex
  or legacy splits-file mode; Gutenberg stripping; oversize auto-split)
- `verify.py` — mechanical completeness/consistency checks before assembly
- The site's look lives in four static files in site/: `fonts.css` (the
  self-hosted fonts, shared), `site.css` + `site.js` (the front pages and
  the filter box), `book.css` + `book.js` (every book page: the title band
  with cover and Download button, the floating Contents button, "continue
  reading" kept in the reader's own localStorage). Book pages set their
  running text in the reader's own best screen serif for legibility; the
  Emend fonts are for the title band, headings and controls only. Dark mode
  follows the system setting. fonts.css and book.css are INLINED into every
  book page by assemble.py (render-blocking otherwise), so a change to them,
  or to `site/template.html`, needs every book re-assembled; site.css,
  site.js and book.js are plain links. The front page lists
  BOTH collections (retellings, then restored editions via
  `build_restored.section()`); restored.html remains for old links.
- `seo.py` — search and link-preview plumbing. `seo.BASE`
  (https://emend.press) is the canonical host, the one place it is written
  (build_feeds reads it). Every page gets a description (the shelf blurb),
  a canonical link and Open Graph/Twitter tags; build_feeds makes the
  1200x630 share cards (site/covers/share/, cover + title + wordmark);
  build_index writes sitemap.xml and 404.html. site/robots.txt is static.
- `build_restored.py` — site/restored.html, the Restored Editions page,
  derived from env (ORIGINAL_TEXT companions, EDITION=restored natives).
- `CAPTIONS.md` — the captioning spec for restored editions.
- `check_introductions.py` — the editor's introductions: word band,
  banned-phrase list, markup conventions, agreement with the renderer
  (is_subheading and EMPH are asked themselves), and that the author is
  named and a date given. Exits nonzero. See `INTRODUCTIONS.md`.
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
- `build_print.py {book} [--isbn N --price 14.99 --spine W]` — 5x8 paperback
  files for IngramSpark from the built epub (Typst; EB Garamond 11pt):
  `{isbn}_txt.pdf` (grayscale) and `{isbn}_cov.pdf` (CMYK, our EAN-13+price
  barcode), both PDF/X-3:2002 via Ghostscript, plus report.txt and proof/
  contact sheets in build/print/{book}/. Specs and their source (Ingram's
  File Creation Guide, Aug 2026) are in the docstring. Pass --spine from
  Ingram's Cover Template Generator before uploading; the default is an
  estimate. Cover colours are Typst cmyk() and RGB SVGs go through
  -dUseFastColor so black stays pure K and total ink stays under 240%.
- `brand/` — the Emend Press logos (Emend Press publishes the Modern
  Classics series): `make_logo.py` outlines the type (Cormorant Garamond
  SemiBold + Montserrat Medium, fonts via `fetch_fonts.sh`) so the SVGs need
  no fonts; copies live in `site/brand/` (favicon, masthead, book pages).
  `rebrand.py` puts the mark in every epub's imprint and colophon and names
  Emend Press as publisher. BUMP `rebrand.VERSION` whenever rebrand's
  rewrites change: build_ebook reuses se drafts, and a draft rewritten by an
  older rebrand silently keeps the old wording; a stamp mismatch forces a
  fresh draft. `rebuild_all.sh` rebuilds every epub and page.
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

See `site/index.html` for the live list. **Per-book notes — sources, ratio
bands, prep traps, voice, sensitive-content rulings, covers — are in
`BOOKS.md`.** Before starting a book, read the entries for its nearest
precedents there (same source format, language, or genre); before touching
a finished book, read its own entry.
