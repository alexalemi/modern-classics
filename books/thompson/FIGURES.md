# Thompson — recovering 158 plates from page scans

The problem this book poses, and how far it is solved.

## The source

There is **no Gutenberg edition** of *Light Visible and Invisible*
(checked: Gutenberg has eight Silvanus Thompson titles, not this one).
The only sources are two Archive.org scans:

| | pages | page size | OCR odd-char rate | ABBYY picture blocks |
|---|---|---|---|---|
| `lightvisibleinvi00thomrich` | 350 | 1956×3086 | **0.40 %** | **170** |
| `lightvisibleinvi00thomuoft` | 344 | 1970×3042 | 0.72 % | 126 |

`…rich` wins on every count and is the source for **both** text and
plates. `source.txt` is its `_djvu.txt`.

## The key discovery: the crops are already computed

The user's instruction was to crop ~130 plates by hand from page scans.
That is not necessary. Archive.org ships an **ABBYY FineReader XML**
(`_abbyy.gz`, 6 MB) in which every illustration is already marked:

```xml
<block blockType="Picture" l="884" t="576" r="1764" b="1476">
```

170 such blocks, with exact pixel boxes. Two facts make them directly
usable:

- **The coordinates need no scaling.** 344 of the 350 ABBYY pages are
  1956×3086, which is exactly what
  `archive.org/download/{id}/page/n{N}.jpg` serves. Only the six cover
  pages differ. Coordinates map 1:1.
- **Only the pages carrying figures need downloading** — 132 pages,
  101 MB, instead of the 172 MB `jp2.zip`.

## Numbering them is the actual problem

A plate is worthless if it ships under the wrong number: the text says
"see Fig. 84" and the reader is shown Fig. 85. This is exactly the bug
that put a treble clef where fleming/ needed a line of Morse code.

Three independent sources of evidence were combined, none sufficient
alone:

1. **ABBYY line text** — lines whose text contains `FIG. n`. Finds 140
   distinct numbers, but merges captions into body text and often
   places the caption *inside* the picture block rather than below it.
2. **Targeted tesseract on the caption band** — crop from 78 % down the
   block to 230 px below it, greyscale, 3×, threshold 62 %. Finds 106
   distinct numbers, and is the best single source.
3. **Full-page tesseract TSV** — word boxes for all 132 pages. Only 84
   distinct: the small-caps "FIG." defeats default tesseract.

Union: **124 of 158 numbers** carry direct evidence.

## Two systematic traps

- **The library stamps.** "REESE LIBRARY OF THE UNIVERSITY OF
  CALIFORNIA" is stamped across many pages and ABBYY marks each one as
  a Picture block. There are **15** of them, and because they sit in
  the reading order between real figures, a sequential numbering pass
  silently shifts every subsequent figure by one. They are detected by
  OCR-ing the block itself and matching
  `REESE|LIBRARY|UNIVERSITY|CALIFORNIA`. Dropping them removes the
  drift.
- **Compound plates.** ABBYY groups figures printed side by side into
  one Picture block — figs 75+76 on one block, 77+78+79 on another,
  121+122 on another. These take the hyphenated compound ids
  (`[Figure 75-76]`) that forces/ introduced, and their captions must
  name every figure on the block, in order, saying which is which.

## Method that works

1. Drop the 15 stamp blocks → **137 real blocks** for 158 figures.
2. Take the longest strictly-increasing subsequence of the evidence as
   trusted anchors (figures are printed in order, so any anchor that
   breaks monotonicity is an OCR misread).
3. Fill each run between consecutive anchors: if the run has as many
   blocks as numbers, assign in order; surplus numbers mean a compound
   plate; surplus blocks mean an artifact.
4. **Verify the residue by eye.** Crop each uncertain block with 300 px
   of margin below — the printed "FIG. n." then falls *inside* the
   crop — annotate it with its index, and montage 10 to a sheet. The
   printed caption is legible and settles the case immediately.

Step 4 is what caught every remaining error: fig 29's block wrongly
merged as [29,30,31], the 75/76 and 77/78/79 blocks, the 121/122 block,
and fig 74's block scored as an artifact.

## State

- `ev_all.json` — 137 real blocks with page, box and all evidence
- `stamps.json` — the 15 library-stamp block indices
- `caps_tsv.json` — caption positions from full-page OCR

Numbers still lacking direct evidence, to be settled by eye:
1, 3, 8, 13, 17, 35, 36, 63, 64, 65, 69, 70, 71, 72, 85, 96, 101, 103,
108, 123, 129, 131, 134, 135, 147–158.

The 147–158 run is Lecture VI, the Röntgen photographs — full-page
plates whose captions are set differently from the line cuts.

## Result

**127 plate files covering 138 of the 158 figures**, in
`site/images/thompson/figN.jpg`. (Figure 63, the refractive-index
chart of appendix two, was rescued late by cropping it straight out of
the page image for printed p. 104 — ABBYY had marked no block for it.) Eight are compound plates under
hyphenated ids (`fig41-42`, `fig88-89-90`, `fig141-142`, …).

Every number was checked against the printed caption. The verification
pass settled twenty-one blocks the automation had scored as compound;
only seven of those were genuinely compound, and the rule that decided
each was simply *how many captions are printed under the block*.

Two further corrections came out of it:

- **The stamp filter had a false positive.** Page 26 carries both the
  ripple-tank photograph (Fig. 1) and a library stamp, so OCR-ing the
  block found "LIBRARY" and threw the figure away. Stamps are ~620×340;
  requiring area < 300,000 px keeps all thirteen real stamps and
  restores Fig. 1 and the large plate on p299.
- Eighteen plates had their own printed "FIG. n." caption inside the
  ABBYY box and were re-cropped above it.

Figures with no plate recovered — ABBYY marked no separate block for
them, mostly small line cuts set into the text:

    8, 13, 22, 36, 64, 65, 73, 96, 103, 108, 123, 131,
    134, 135, 150, 151, 152, 153, 156, 157

The translation must not emit a `[Figure n]` marker for these, and
should describe rather than cross-reference where the text says "see
Fig. 8".

## Re-cutting them (2026-08-04)

The plates as first cut had two faults that only show when you read the
assembled page, and `replate.py` fixes both. It works from
`plates.json` (fig, page, box) and the page scans, so
`bash fetch.sh` has to be run first.

**They were clipped.** ABBYY's Picture block fits the *engraving*, not
the drawing: arrowheads, outer labels and the last ray of a pencil fall
outside it. Worst case, fig 3 lost the entire barrier-and-slit the
wavefronts are diffracting through and shipped as three arcs and an
arrow; fig 17 lost the whole lantern and kept the chimney; fig 10 was
cut through the words "Light No. 2". A fixed margin is a guess in both
directions, so each side is instead **grown outward until it reaches
whitespace** — scan away from the box a line at a time, stop at the
first run of blank lines, back off by a small pad. That recovers
whatever was clipped, stops in the gutter before the running text, and
does nothing at all to a plate that was never clipped. Seven plates
where the search runs into body text anyway carry a hand-set cap in
`CAPS`; a negative cap moves the edge inward, for the two boxes that
took in page furniture to begin with.

**The paper was in the picture.** Each plate carried its own patch of
scanned cream with its own cast, and 127 slightly different creams down
a white page read as dirt. The darkness of a pixel now becomes its
ALPHA over pure black, so what survives is the ink, anti-aliased as the
scan had it, on a transparent ground.

Three details that matter:

- **PAPER_PCT has to be near the top of the histogram, not at its
  mode.** A fifth of these plates are printed white on black (a lantern
  beam crossing a darkened room), where the mode IS the ink. At the
  mode, the black ground came out at 0.9 alpha instead of 1.0 — enough
  for the text on the back of the leaf to show through as a legible
  ghost. Read at the 99th percentile the same mapping handles both
  polarities with no special case: black ground opaque, white lines
  transparent, so over a white page it looks exactly as printed.
- **Alpha, not a threshold.** A fifth of the plates are halftones — the
  Röntgen photographs, the ripple tank, the mirror scans — and a
  bilevel threshold destroys them.
- **Quantise the alpha.** The scan's noise gives every stroke a fringe
  of unique values that PNG cannot compress. Rounding to 16 levels for
  line art and 48 for halftones halves the files and is invisible.

Two corrections to the inventory came out of it: `plates.json` still
carried fig 108, whose box is a running head and a library stamp (it
was right to be dropped from the shipped set), and lacked fig 63, the
refractive-index chart rescued by hand. 63's box was recovered by
matching the shipped crop against the page by row and column profile —
[310, 1120, 1300, 685] on the file for printed p. 104 — and the page
added to `fetch.sh`, which had never included it.
