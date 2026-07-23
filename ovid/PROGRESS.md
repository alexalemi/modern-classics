# Ovid Metamorphoses — build progress / RESUME HERE

Book #40 of the Modern Classics project. First of a five-book push
(Ovid → Cellini → Dante Inferno → Homer Odyssey → Sun Tzu). Paused only
because the session hit the 200-subagent cap; raise
`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` (e.g. 1000) and restart, then
resume the parallel pipeline from file 013.

## Method (proven, DO NOT re-run prep)
From the LATIN (chapters/) with Riley's prose crib (reference/) as a
comprehension aid only. Shared-ledger pattern: every translation agent
reads agent_instructions.txt + text_analysis.txt + running_notes.txt,
then its Latin file + crib. Orchestrator updates running_notes.txt
between batches. 30 files, 15 books = chapters "Book I".."Book XV".
Ratio Latin→English ≈ 1.4–2.4; verify with `--min-ratio 1.4 --max-ratio 2.4`.
DO NOT re-run prep.py (it would repack part boundaries under the
already-translated files). chapters/ were hand-cleaned of stray
line-numbers/footers after prep; prep.py is fixed for any future run.

## TRANSLATION COMPLETE — all 30 files (Books I–XV) done & verified.
verify.py ovid --min-ratio 1.4 --max-ratio 2.4: 30 files, 78,141 Latin ->
131,076 English words, ratio 1.68, ALL checks passed (all must_contain
names present). Files 013–029 were translated DIRECTLY by the orchestrator
after the 200-subagent session cap was hit (000–012 by subagents); voice
and ledger consistent throughout, ratios 1.51–1.90. ASSEMBLED to
site/ovid.html (15 sections; proem + epilogue verified; no inscription
mis-rendered as a heading).

## REMAINING TO PUBLISH (needs network / a publish decision):
1. COVER — not yet scouted. Ovid has rich PD art on Wikimedia Commons
   (Waterhouse, Bernini's Apollo & Daphne, Rubens, Poussin, engravings).
   Pick a striking public-domain painting; set ebook_meta.json "cover"
   (commons file + optional crop). Add the full ebook_meta.json entry
   (see eighty-days/journey pattern: dir, fiction, genre="Fiction",
   subjects, description, long_description, author_wiki, work_wiki, cover).
2. `python3 build_ebook.py ovid` (network; sandbox off for Commons).
3. Add to site/index.html — a NEW section "Myth & Epic" (or Fiction &
   Ideas). Ovid 1st-century-BCE/CE Latin; ~11-hour read (~131k words);
   epub link ebooks/ovid_metamorphoses.epub.
4. `python3 build_feeds.py` AFTER committing the book (dates from the
   adding-commit). Two-commit deploy: commit book, regen feeds, commit
   feeds, push. Update CLAUDE.md / ROADMAP.md / memory.

## Then books 2–5 of the push (fresh prep each — raise the subagent cap
## first!): Cellini (Italian), Dante Inferno (Italian+crib), Homer Odyssey
## (Greek+crib), Sun Tzu Art of War (crib).
Voice locked from 000. running_notes.txt holds all conventions:
name/periphrasis resolutions, "follow the Latin over Riley where they
diverge", bracketed-variant + ++OCR++ handling, epitaphs-not-all-caps,
and the EMBEDDED-TALES convention (long tale-within-tale as primary
narration, no enclosing quotes — critical for Book X Orpheus).

## REMAINING: files 013–029 (17 files). Launch as batches of ~6:
- Batch 3 — 013 (Bk VII p2: Cephalus & Procris), 014 (Bk VIII p1:
  Scylla, Minotaur, DAEDALUS & ICARUS), 015 (Bk VIII p2: Meleager,
  BAUCIS & PHILEMON, Erysichthon), 016 (Bk IX p1: death of Hercules),
  017 (Bk IX p2: Byblis; Iphis & Ianthe), 018 (Bk X p1: ORPHEUS &
  EURYDICE + Orpheus's song incl. PYGMALION — use embedded-tale rule).
- Batch 4 — 019 (Bk X p2: Orpheus's song cont. — Myrrha, Venus & Adonis,
  Atalanta), 020 (Bk XI p1: death of Orpheus, MIDAS), 021 (Bk XI p2:
  Ceyx & Alcyone, the House of Sleep), 022 (Bk XII p1: Troy, Cycnus),
  023 (Bk XII p2: the Lapiths & Centaurs battle, death of Achilles),
  024 (Bk XIII p1: the debate of Ajax & Ulysses over the arms).
- Batch 5 — 025 (Bk XIII p2: fall of Troy, Hecuba, Polyxena; Acis &
  Galatea), 026 (Bk XIV p1: Scylla & Glaucus, the Sibyl, Circe), 027
  (Bk XIV p2: more Circe, Picus; Aeneas deified; Vertumnus & Pomona),
  028 (Bk XV p1: Pythagoras's great speech on flux/vegetarianism —
  NB has the 22a/23b transposed-line passage, already cleaned), 029
  (Bk XV p2: Numa, Hippolytus, the apotheosis of Caesar, and Ovid's
  proud EPILOGUE "iamque opus exegi" — make the closing sing).

Use LEAN briefs: heading + exact part marker + "follow your crib's
episode labels" + note the marquee tale + the seam. The crib labels the
episodes authoritatively, so don't over-brief plot (it drifts).

## After all 30 files:
1. `python3 verify.py ovid --min-ratio 1.4 --max-ratio 2.4` — fix any
   flags; check must_contain names all present.
2. Read the 018/019 seam (Orpheus's song spans it) and any book-part
   seams for quote-level / double-beat issues (see the 008/009 fix).
3. `python3 assemble.py ovid` → site/ovid.html; add to site/index.html
   (Fiction & Ideas or a new "Myth & Epic"? — decide; near the classics).
4. COVER: not yet scouted. Ovid has rich art on Wikimedia Commons
   (Waterhouse, Bernini's Apollo & Daphne, Rubens). Pick a striking
   public-domain painting; set ebook_meta.json "cover" (commons + crop).
   Add the full ebook_meta.json entry (see eighty-days/journey pattern).
5. `python3 build_ebook.py ovid` (network; sandbox off for Commons).
6. `python3 build_feeds.py` AFTER committing the book (dates come from
   the adding-commit). Two-commit deploy: commit book, regen feeds,
   commit feeds, push. Update CLAUDE.md / ROADMAP.md / memory.

## Then books 2–5 of the push (fresh prep each; see ROADMAP + my plan):
Cellini Autobiography (Italian; Symonds crib), Dante Inferno (Italian +
Longfellow/Cary crib; Doré covers on Commons), Homer Odyssey (Greek +
Butler/Butcher-Lang crib), Sun Tzu Art of War (Giles crib — flag the
crib-modernization caveat in front matter).
