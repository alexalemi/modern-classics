# Roadmap — future retellings

Candidates chosen for the project's thesis: works meant for wide
audiences, in the public domain, trapped behind archaic English
translations. Pipelines proven so far: Gutenberg/SE plain text,
SE-XHTML, Wikisource-API, from-the-Latin, from-the-French.

## Recently shipped
### The Royal Institution lecture volumes (6-book run, COMPLETE)
- **C. V. Boys — Soap Bubbles and the Forces Which Mould Them**
  (1890; the project's FIRST ILLUSTRATED volume) — 13 files, ~32k
  words, all 69 plates + frontispiece. LIVE. The figure pipeline
  (`FIGURE_DIR` in env, `[Figure N: caption]` markers, verify check 6)
  is generic and unblocks illustrated works in general — Hooke's
  Micrographia, Vasari.
- **Michael Faraday — The Chemical History of a Candle** (1861) — 12
  files, ~42k words, 38 woodcuts, plus the Lecture on Platinum. LIVE.
- **Michael Faraday — On the Various Forces of Nature** (1860) — 15
  files, ~36k words, 50 plates carrying 59 figures (compound-plate ids),
  plus the Lighthouse Illumination address. LIVE.
- **J. A. Fleming — Waves and Ripples in Water, Air, and Aether**
  (1902) — 32 files, ~77k words, all 87 plates, plus the two-note
  appendix. LIVE. The largest of the five.
- **Sir Robert Ball — Star-land** (1889/1899) — 36 files, ~96k words,
  all 94 plates, plus the concluding chapter on finding the
  constellations. LIVE. The warmest of the five.
- **Silvanus P. Thompson — Light Visible and Invisible** (1897) — 30
  files, ~69k words, all 127 recovered plates, plus six appendices.
  LIVE. THE PROJECT'S FIRST OCR SOURCE (Archive.org
  `lightvisibleinvi00thomrich`; there is no Gutenberg edition). Given
  thirteen months after Röntgen; the sixth lecture is on X-rays and
  quotes the discoverer's own interview. See thompson/FIGURES.md for
  the plate recovery and CLAUDE.md for the OCR-source lessons.
- **John Tyndall — Sound** (1867; third edition 1875) — 44 files,
  ~117k words, all 187 plates, plus Le Conte's 1858 paper on the
  sensitive flame and Tyndall's own note on acoustic reversibility.
  LIVE, and the largest of the set. Gutenberg #54969. Tyndall invented
  the lecture-demonstration style all the others descend from, so the
  set now reads as one shelf: Boys on surface tension, Faraday on
  candles and forces, Fleming on waves, Ball on the sky, Thompson on
  light, Tyndall on sound. Its seventh chapter — the South Foreland
  fog-signal researches, and the acoustic clouds that explain them —
  has no counterpart anywhere else in the collection.
  (Note: "Sound: Musical and Non-Musical" is not a Thompson title —
  his catalogue is electricity, dynamos, Faraday, Kelvin and Gilbert.
  The nearest match to that phrase is Sedley Taylor's "Sound and
  Music: A Non-Mathematical Treatise" (1873), Archive.org only.)
- **Galileo — Dialogue Concerning the Two Chief World Systems**
  (Italian, 1632; the from-the-Italian pipeline's debut) — 55 files,
  ~194k words, assembled to site/galileo.html and added to the index.
  Deploy still pending: build epub, regenerate feeds, commit + push.
- **Theophrastus — Characters** (Greek, c. 319 BC; thirty comic
  sketches of annoying personality types) — live at
  site/theophrastus.html, in both feeds and epub catalog.

## Founders' Library, Volume II
- Montesquieu — The Spirit of the Laws (from the French; the most-cited
  secular author of the founding era; ~250k words)
- Cicero — On Friendship; On Old Age (from the Latin; short; Adams
  reread De Senectute yearly)
- Tacitus — Annals (Church & Brodribb as crib; pairs with Roman Lives)
- Livy — History of Rome, Books I–X (the founders' Rome)
- Epictetus — Discourses (the full lectures behind our Enchiridion)
- Beccaria — On Crimes and Punishments (from the Italian; behind the
  Eighth Amendment; short)

## High-payoff singles
- Lucretius — On the Nature of Things (from the Latin; Jefferson owned
  five copies)
- Augustine — Confessions (the first autobiography; pairs with
  Franklin's)
- Cellini — Autobiography (from the Italian; gossipy Renaissance gold)
- Vasari — Lives of the Artists (from the Italian; the Plutarch
  treatment for painters)
- La Rochefoucauld — Maxims (from the French; ~500 epigrams; quoted in
  our Cato's Letters)
- Erasmus — Praise of Folly (from the Latin)
- Ovid — Metamorphoses — DONE (site/ovid.html; all 15 books complete,
  from the Latin with Riley's prose crib; the storybook of mythology)
- Pascal — Pensées (from the French)
- Bunyan — The Pilgrim's Progress — IN PROGRESS (bunyan/; both parts,
  108k words, 39 chapters). The unusual justification: it is not hard,
  it MISLEADS. Standard Ebooks scores it at reading ease 74 ("fairly
  easy"), so there are no periodic sentences to unstack — but
  "conversation" means conduct, "want" means lack, "prevent" means go
  before, and a reader sails through getting them backwards with nothing
  to signal the error.
- Cervantes — Don Quixote (from the SPANISH, with Ormsby 1885 as the
  per-file crib — the de-officiis/ovid pattern; Gutenberg #2000 is the
  Spanish, Standard Ebooks has Ormsby in clean XHTML). 390k words of
  Spanish, 430k of Ormsby: the project's second-largest after Plato's
  Dialogues, and larger than Wealth of Nations. THE STRONGEST COPYRIGHT
  ARGUMENT ON THIS LIST — every good modern translation (Grossman,
  Rutherford) is in copyright, so the free Don Quixote is Ormsby,
  Jarvis, Motteux or Shelton, and the book's reputation as a slog is
  very largely an artifact of that. 126 chapters (52 + 74) at ~3.4k
  words each, so most need no splitting; verify near the Verne bounds
  (Ormsby runs 1.10x the Spanish), not the Latin ones. Set policy up
  front for Sancho's proverb-avalanches, the interpolated novellas in
  Part One that abridgements always cut, and the chapter titles, which
  are themselves jokes and must stay jokes.

## The Verne recovery project
The Victorian translations cut 20–30% and botched the science; faithful
from-the-French retellings would recover lost books:
- Twenty Thousand Leagues Under the Sea — DONE (site/twenty-thousand-
  leagues.html; complete/unabridged, from the French; the from-the-
  French novel pipeline is now proven — see twenty-thousand-leagues/prep.py)
- Around the World in Eighty Days — DONE (site/eighty-days.html;
  complete, from the French; second Verne, the comic-adventure pipeline)
- Journey to the Center of the Earth — DONE (site/journey-center-earth.html;
  complete, from the French; third Verne, completes the from-the-French
  trilogy; the wonder-and-descent register)

## Carroll the mathematician (planned shelf, ~121k words + one OCR book)
Sits directly beside the Royal Institution volumes: same period, same
instinct — a specialist writing for delighted amateurs. Charles Dodgson
was a working Oxford mathematician, and it is the MATHEMATICAL Carroll
that this project can help, not the fantasist.

NOT Alice, and NOT the Snark. Both fail the test, and it is worth
writing down why, because it is the clearest statement of what the test
IS: the question is not "is it old and famous" but "is a modern reader
being silently blocked or misled?" Alice is among the most-read books in
English exactly as written, by children, today; there is no archaic layer
and there are no false friends. The Snark is 8,900 words of verse whose
metre and rhyme ARE the work, and whose difficulty is deliberate nonsense
whose removal would be vandalism. What both want is annotation — a
different book from the one we make.

- **A Tangled Tale** (1885) — Gutenberg #29042, 31k words, 11 Arthur B.
  Frost plates in the -h.zip, so the easy soap-bubbles illustrated path
  rather than the Thompson OCR one. Ten comic "Knots", each carrying a
  puzzle, then an Appendix and ten "Answers to Knot N" sections in which
  Carroll reviews readers' submitted solutions by pseudonym and
  cheerfully eviscerates the wrong ones. The Answers are half the book
  and the best of it — translate them whole (the soap-bubbles "Practical
  Hints is a third of the book" rule). START HERE: closest in size and
  register to what the shelf already knows how to do.
  TWO POLICY CALLS DECIDED IN ADVANCE. (1) KEEP the pounds/shillings/
  pence and gloss the currency once at the front — several answers work
  out BECAUSE of the 12-and-20 structure, so decimalizing would silently
  break the puzzles. It is Carroll's puzzle in Carroll's units, which is
  the Verne rule. (2) CHECK EVERY ANSWER THAT CLAIMS TO BE COMPUTED —
  Carroll has known disputed and ambiguous solutions, and a wrong answer
  that looks right is precisely the defect verify.py cannot see (the
  fleming table lesson).
- **Symbolic Logic, Part I** (1896) — Gutenberg #28696, 69k words, 319
  diagram images. The genuinely trapped one: Victorian notation, his own
  idiosyncratic biliteral/triliteral diagram method, and a terminology
  that later logic simply abandoned — so a modern reader WITH logic
  training is more confused, not less. The diagrams are ordinary plates
  and the existing figure pipeline takes them.
- **Pillow Problems** (Curiosa Mathematica Part II, 1893) — Gutenberg
  #79080, 21k words. Seventy-two problems he solved in his head, in bed,
  in the dark; the premise alone sells it.
  NEW PREP PROBLEM, NOT YET SOLVED ANYWHERE IN THIS PROJECT: there is no
  plain-text edition, and the mathematics is 2,436 separate SVG files
  pulled in by <img> mid-sentence — one per symbol or fragment, so
  "sin ∠OPN" is four images in a row. That is a different thing from a
  block plate and the figure-marker pipeline does not fit it. (Only ~64
  of the 2,501 images are real diagrams: i_pNN.jpg. Those the existing
  pipeline takes.)
  THE ALT TEXT IS MATHSPEAK, WHICH CHANGES THE PROBLEM. Every one of the
  2,436 carries alt text, and it is not a human's loose description but
  the standard verbal serialisation of MathML: "upper A", "StartFraction
  x Over y EndFraction", "StartRoot r squared minus x squared EndRoot",
  "Superscript 4 Baseline", "StartLayout 1st Row 1st Column … EndLayout".
  That is grammatical and machine-reversible, so the notation can be
  PARSED BACK rather than guessed at. Write the MathSpeak reader first
  and test it against all 1,279 distinct strings before writing prep.
  THE DISTRIBUTION IS BIMODAL and only the tail needs a decision: ~1,900
  are a single symbol or a short inline expression and go straight to
  Unicode; a few dozen are whole multi-line derivations (one runs to 15
  rows) that are genuinely two-dimensional. Those want the indented-block
  path — which now renders properly in BOTH renderers after
  symbolic-logic — or they stay as plates. Decide that, and:
  DECIDED (Alex, 2026-08-06): MODERNISE THE NOTATION, and render it in
  both formats rather than falling back to plates. So Carroll's Victorian
  factorial |n-with-an-underline — which MathSpeak renders "vertical bar
  ModifyingBelow 2 With quotation dash" — becomes 2!, and the multi-line
  derivations become indented Unicode blocks, which BOTH renderers now
  set properly after symbolic-logic. This is the opposite of the
  symbolic-logic ruling and deliberately so: there the words WERE the
  machine, here the notation is incidental to the argument and the
  argument is what the reader came for.
- **Euclid and His Modern Rivals** (1879) — the ghost of Euclid defends
  his own textbook against thirteen Victorian rivals, in dialogue, at
  midnight, before a college examiner who cannot sleep for marking.
  Genuinely funny and completely unread. STARTED 2026-08-06: sources
  fetched and assessed, nothing prepped yet. Full findings in
  `euclid-rivals/source_notes.txt`; the four that matter:
  (1) confirmed NOT on Gutenberg (with a control query, so the search
      really works). Archive.org only, so the thompson/ OCR path.
  (2) USE BOTH SCANS. `euclidhismodernr00carr` (1885, 2nd ed) is the copy
      text because Carroll revised it; `euclidandhismode000469mbp` (1879,
      1st ed) is the corrector. Their OCR errors are INDEPENDENT, which
      is the biggest lever available: the 1885 renders italics as debris
      ("a College dudy. Time, midvigJtf") where the 1879 is nearly clean,
      and yet in the same two sentences the 1885 has the digits right and
      the 1879 has them wrong. A difference is a question, not an answer.
  (3) THE SPEAKER TAGS ARE OCR-DAMAGED, which is the dangerous part: get
      one wrong and Carroll's argument changes hands. But the vocabulary
      is TINY AND CLOSED (Min, Euc, Nie, Nos), so nearest-match is safe,
      the two scans can vote, and prep must RAISE on anything it cannot
      resolve rather than guess. Title-Case tags, never ALL-CAPS (galileo).
  (4) 29 Picture and 19 Table blocks in the ABBYY XML, so the full
      thompson/ apparatus is needed — plates re-cut from the page scans,
      and every table checked against the page image.
  The five Appendices are dense tabular cross-reference matter and want a
  decision of their own before prep, as bunyan/'s commentator notes did.

## Folktales and stories from other cultures (Alex, 2026-08-06)

A new strand, and the project's first COLLECTIONS rather than single
works. Start with Joseph Jacobs. All are on Gutenberg, all are out of
copyright, and Jacobs is the right door: he collected in English, wrote
for children on purpose, and left a scholarly apparatus that says where
every tale came from.

  #7439   English Fairy Tales (1890)     65k words, 43 tales, NO plates
  #35862  Celtic Folk and Fairy Tales    79k words, 26 tales, 80 plates
          (= Celtic Fairy Tales, 1892, the Batten-illustrated setting;
           #7885 is the same book without the pictures)
  #14241  More English Fairy Tales (1894) 64k, 59 plates
  #34453  More Celtic Fairy Tales (1894)  69k, 70 plates
  #7128   Indian Fairy Tales (1892)       75k, 85 plates
  #26019  Europa's Fairy Book (1916)      62k, 52 plates

THE NEW EDITORIAL QUESTION, AND IT IS THE WHOLE JOB: **DIALECT IS NOT
ARCHAISM.** Jacobs prints the tales as they were told. Tom Tit Tot opens
"there was a woman, and she baked five pies... they were that overbaked
the crusts were too hard to eat... 'Noo, they ain't come again'" — thick
Suffolk, and it is not a defect to be repaired, it is the artifact. Every
rule this project has is about removing distance between reader and
author; here some of the distance IS the text. Nix Nought Nothing is
Scots, several of the Celtic tales are Irish-inflected, and a modern
ten-year-old will bounce off some of it. Decide ONCE, before any prep, on
a scale: what is silently modernised (spelling that only represents
pronunciation), what is kept (rhythm, syntax, the tags and refrains), and
what gets a light hand (a genuinely opaque word). Nearest precedent is
bunyan/ — where the case for the book was that it MISLEADS rather than
that it is hard — but dialect is a class this project has not met.

SECOND DECISION: JACOBS' NOTES AND REFERENCES. 11,338 of English Fairy
Tales' 65k words are his own scholarly back matter — source, parallels,
bibliography, tale by tale. Unlike Offor's Victorian devotional
commentary in bunyan/ (dropped to a crib), these are the collector's own
and they are genuinely interesting: they are what makes it a book about
folklore and not just a book of stories. Probably keep, probably in his
register, possibly abridged.

THIRD: PLATES. Batten's illustrations are famous and good, and the Celtic
volumes have them on Gutenberg. English Fairy Tales does NOT — #7439 is
plain text and #26460 is an AUDIOBOOK, not an illustrated edition. So
either ship the English volume unillustrated or take the two-source route
(text from Gutenberg, plates from Archive.org) proven in candle/.

STANDARD EBOOKS HAS A REAL FOLKTALE SHELF — checked and SAMPLED
2026-08-06. SE editions are proofread, use semantic markup and modern
typography, and prep already handles SE XHTML (bunyan/, autobiography/),
with the traps known: no-break spaces inside abbreviations, and noteref
anchors that must be killed as ELEMENTS.

THE TEST ALEX SET: take the ones written in a stuffy or literary
register that a retelling would unlock. If a book is already good and
modern, LEAVE IT ALONE. Measured on the real text — average sentence
length, proportion of sentences over 35 words, and reading the prose:

  WORTH DOING (the register genuinely obstructs the material)
  - Hindu Tales from the Sanskrit — S. M. Mitra, 1919.  40k.
    30.4w average sentence, 29% over 35 words, and Edwardian
    explanatory syntax that keeps stopping to reassure you: "taking a
    certain pleasure in being entirely his own master; which a king can
    never really be, because he has to consider so many other people and
    to keep so many rules." Best ratio of good material to bad prose in
    the set. START HERE.
  - The Kalevala — Lönnrot, tr. Crawford 1888.  53w "sentences",
    50% over 35, and the whole thing is in Hiawatha metre: "O'er this
    cold and cruel country". A huge unlock, but it is a national EPIC in
    Victorian verse, so it is an Ovid-shaped job, not a folktale job.
    Size it separately.

  MARGINAL
  - Russian Folktales — Afanasyev, tr. Magnus 1915.  102k.  25.3w.
    I EXPECTED THIS TO BE THE STUFFY ONE AND IT IS NOT: the tales
    themselves keep a decent oral voice ("You know that there are all
    sorts in this world, good and bad, people who do not fear God").
    The scholarly apparatus is stiff; the stories are not. Great
    material, smaller unlock than it looks.
  - Indian Fairy Tales — Joseph Jacobs, 1892.  71k.  26.9w but reads
    young on purpose: "a wee wee Lambikin, who frolicked about on his
    little tottery legs".
  - Legends of Vancouver — E. Pauline Johnson, 1911.  29k.  Longest
    words in the set (4.27 chars) and a deliberately grand cadence
    ("the humane, sympathetic, charitable, loving people"). Literary by
    choice, not by stuffiness.

  LEAVE ALONE (already modern — the test says skip)
  - Old Indian Legends / American Indian Stories — Zitkala-Ša, 1901.
    13.9w average sentence and ONE PER CENT over 35 words: by a wide
    margin the cleanest prose in the set, and she is a Dakota writer
    telling Dakota stories. Nothing to unlock. Recommend as reading,
    do not retell.
  - Irish Fairy Tales — James Stephens, 1920. Mannered, but mannered
    ON PURPOSE — Irish Revival high style, aphoristic and beautiful
    ("or the spirit faints and wisdom herself grows bitter").
    Modernising it would be like modernising Yeats.
  - Fables — Aesop, tr. Vernon Jones 1912. Already brisk and clean.

NOT ACTUALLY AVAILABLE: Andersen's Fairy Tales and Dayrell's Folk
Stories from Southern Nigeria have SE pages but are IN PRODUCTION, not
published — "We don't have this ebook in our catalog yet." Both would be
strong candidates when they land (the Victorian Andersen translations
are notoriously stiff and bowdlerised, which is exactly the target).
Re-check before planning either.

THE GAP: SE has Jacobs' INDIAN Fairy Tales but NOT his English or
Celtic, so the two Alex first named still come from Gutenberg (#7439,
#35862). Nor does SE have Grimm, Lang, Ozaki's Japanese or the Arabian
Nights.

WHERE TO LOOK NEXT, given the test — the unlock is biggest where a
Victorian translator archaised deliberately, which is a Gutenberg
hunt rather than an SE one: Margaret Hunt's Grimm (1884), Ralston's
Russian Folk-Tales (1873), and above all Burton's Arabian Nights, whose
whole method was to write mock-Elizabethan. Prefer collectors who
worked from the source language over Lang, which is translations of
translations. SAMPLE THE PROSE BEFORE COMMITTING — the Afanasyev
result is the warning: the stuffy-looking one was fine.

## Further afield (needs stronger crib scaffolding — different
translation-risk class; caveat prominently in front matter)
- Tao Te Ching; Analects (Legge as crib)
- Sun Tzu — The Art of War (Giles as crib)
- 1001 Nights, selected (Burton/Lane as cribs)
- Bhagavad Gita
