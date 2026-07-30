# Roadmap — future retellings

Candidates chosen for the project's thesis: works meant for wide
audiences, in the public domain, trapped behind archaic English
translations. Pipelines proven so far: Gutenberg/SE plain text,
SE-XHTML, Wikisource-API, from-the-Latin, from-the-French.

## Recently shipped
### The Royal Institution Christmas Lectures (5-book run, 3 of 5 done)
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
- NEXT: **Sir Robert Ball — Star-land** (1889; Gutenberg #60318, ~106k
  words, 95 plates — plates ship in the `-h.zip`). Sourced, untranslated.
- THEN: **Silvanus P. Thompson — Light Visible and Invisible** (1897).
  Archive.org OCR only (`lightvisibleinvi00thomrich`, `…uoft`; ~77k
  words, 0.05% suspicious tokens). ~130 plates must be hand-cropped
  from the page scans — the user chose this path explicitly over
  prose-only.
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

## Further afield (needs stronger crib scaffolding — different
translation-risk class; caveat prominently in front matter)
- Tao Te Ching; Analects (Legge as crib)
- Sun Tzu — The Art of War (Giles as crib)
- 1001 Nights, selected (Burton/Lane as cribs)
- Bhagavad Gita
