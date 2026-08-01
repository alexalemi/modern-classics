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
