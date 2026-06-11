# DEVLOG

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
