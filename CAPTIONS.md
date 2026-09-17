# Captions for Restored Editions

A restored edition keeps the author's prose unchanged. What it adds is an
apparatus the original never had, and the heart of it is the **caption and
alt text for every plate**. The source Gutenberg editions ship these plates
with an empty `alt` attribute or a filename, so a reader who cannot see
them gets nothing.

Captions are written into `{book}/captions/NNN.txt`, one plate per line:

    <plate id><TAB><description>

`prep.py` composes `modern_chapters/` from `chapters/` plus these files.
Nobody edits `modern_chapters/` by hand, and nobody retypes the prose.
Rerun `python3 {book}/prep.py` after writing captions, then
`python3 verify.py {book} --min-ratio 0.999 --max-ratio 1.001`.

## What the page shows

The rendered caption is **the printed label, then an em dash, then your
description**. The printed label comes from `plates.json` and is the
author's. Do not repeat it. So for a plate printed `3 0·002 sec.` in
Series II, write only what is in the photograph:

    fc	The drop has just touched the surface and a thin ring of liquid is rising around its base.

and the page will show "3 0·002 sec. — The drop has just touched…".

A plate with no printed label (a headpiece, a silhouette, a composite)
gets a description that stands alone.

The same text is the epub's `alt` attribute, so it has to work read aloud
to someone who will never see the image.

## How to write one

1. **LOOK AT THE PLATE.** Open the image before writing a word. This
   collection's standing rule, earned repeatedly: `fig-a` in Worthington
   is a photograph despite its name; a "figure" can be a scale bar; a
   printer's float can put two plates in the wrong order. The file on
   disk is `site/images/{book}/fig{id}.jpg` (Aesop's title page is
   `front.jpg`).
2. **READ WHERE IT SITS.** Find `[Figure id]` in `chapters/` and read the
   paragraphs around it. The author usually says what the plate is for.
3. **Describe what is drawn or photographed, concretely.** Shapes, stage,
   which way things are moving, who is doing what. One or two sentences,
   usually 12–35 words.
4. **Use the author's vocabulary for the author's things.** Worthington's
   crater, sheath, basket, column, crown, rim; Rackham's figures by the
   names the story gives them. Where the prose names a character, use the
   name.
5. **Do not interpret beyond the book.** Say what is there, and where the
   prose says what it means, you may say that. Never add science, history
   or a judgement the author did not make. A caption is not a place for
   the edition's opinions.
6. **Never contradict the printed label.** If the photograph looks wrong
   against its label, REPORT it rather than "correct" it.

## Mechanics

- Plain text only. No square brackets (they close the marker), no
  asterisks, no tabs inside the description, no line breaks.
- Real em dashes with spaces (` — `), never `--`.
- End with a full stop.
- Every plate in the batch you were given, and only those. prep refuses a
  plate captioned twice.

## Tone

Plain, exact, and a little warm where the picture is: the kind of sentence
a good museum label has. No "stunning", "exquisite", "beautifully
captures" — the INTRODUCTIONS.md banned list applies here too.
