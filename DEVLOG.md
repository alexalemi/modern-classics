# DEVLOG

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
