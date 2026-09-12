# Editor's Introductions

Every book in the collection opens with a short editor's introduction:
`{book}/introduction.txt`, rendered by `assemble.py` onto the page above
the Contents and by `build_ebook.py` as the epub's first frontmatter
section. It is NEW WRITING and lives at the book root, never in
`modern_chapters/`, because everything in that directory is measured
against `chapters/` by `verify.py` and by the book's own `check.py`.

## What it is for

A reader arriving at a 2,400-year-old play, or a Japanese meditation
manual, or a Victorian lecture on soap films, is missing the things the
first readers had for free: who this person was, what year it was, what
had just happened, what the book was for, and what the conventions of it
are. Supply exactly that, and then get out of the way.

The model is a good anthology headnote, not a scholarly preface. It is
read once, before the book, by somebody who has not decided yet whether
to keep reading.

## Length and shape

300 to 500 words. Three to five paragraphs. The check allows 200-650.

Cover these, in whatever order the particular book wants:

1. **Who, when, where.** The author, the date, the place, and the one or
   two facts about their situation that change how the book reads.
   Boethius wrote his in a cell awaiting execution; Wollstonecraft wrote
   hers in six weeks; Cellini dictated his to a boy of thirteen while he
   went on working.
2. **What was going on around it.** Only what bears on the book. The
   Peloponnesian War, the 1857 prosecutions, the sack of Rome. Not a
   survey of the century.
3. **What the book is and what it was for.** What the author was trying
   to do, and to whom. A manual, a defence, a letter to a friend, a
   speech, a court entertainment, thirteen Christmas lectures for
   children.
4. **What a modern reader needs in order not to be lost.** The genre
   convention that will otherwise read as strange; the assumption the
   author never states because everyone knew it. A Greek tragedy's
   chorus. That a Stoic "passion" is not an emotion. That Sun Tzu's
   commentary is eleven men arguing across two thousand years.
5. **What this edition did.** One or two sentences, only where a real
   choice was made: translated from the original rather than from an
   English version; verse set as prose and why; the whole thing, where
   most editions abridge; offensive material kept as the author wrote
   it. The facts are in `CLAUDE.md` under the book's entry and in
   `ebook_meta.json`'s `long_description`. Do not repeat the page
   header, which already says the book is an AI modernization.

Optionally end on the thing most worth staying for — the actual best
passage in the book, named plainly, without overselling it.

## Voice

Plain, concrete, direct. Short declarative sentences. Facts and dates
and names. The register of a well-informed friend telling you what you
are about to read, who assumes you are intelligent and does not assume
you know anything in particular.

The single hardest rule, and the one Alex asked for by name:

> **NO MANNERED PROSE.**

That means, concretely:

- **No literary-blurb vocabulary.** Not timeless, immortal, seminal,
  masterpiece, magisterial, towering, profound, luminous, unflinching,
  haunting, searing, tour de force, testament, meditation on.
- **No claims about the book's importance in place of information.** "One
  of the most influential books ever written" tells the reader nothing.
  Say what it did: who read it, what changed, what came after.
- **No relevance-mongering.** Not "as relevant today as ever", "speaks to
  us across the centuries", "resonates with modern readers", "what it
  means to be human". If it is still worth reading, show why with a
  fact, and let the reader decide.
- **No "not just X but Y"**, no "at its core", no "in many ways", no
  "invites us to", "reminds us that", "sheds light on", "serves as",
  "stands as", "grapples with", "delves into", "a rich tapestry".
- **No address to the reader as "dear reader"**, no rhetorical questions
  aimed at them, no "let us now", no "we shall see", no telling them
  what they will feel.
- **No throat-clearing first sentence.** Start with the fact.

## Spoilers

Say what happens in the setup; do not give away a turn the book works to
conceal. Oedipus' parentage is the subject of the play and every Athenian
knew it walking in — that is not a spoiler. The identity of the murderer
in a Verne chapter, or the trap Penelope sets for her husband, is. Where
a famous scene is the reason to read the book, name it without saying how
it comes out.

## Mechanics

Same markup-free conventions as `modern_chapters/`:

- Paragraphs separated by blank lines. **No heading line** — the renderer
  supplies "Editor's Introduction".
- No ALL-CAPS lines (`assemble.py` reads one as a heading), no tab or
  space indentation (it becomes a `<pre>` block), no Markdown.
- Em dashes are real em dashes with spaces around them, never `--`:
  `assemble.py` does not convert a double hyphen while `se typogrify`
  silently does, so it would ship literally on the page and correctly in
  the epub.
- `_x_` or `*x*` render as italics; use them only for a title or a
  foreign term, and the delimiters may not enclose a space.
- Nothing that `assemble.is_subheading()` would read as a section title:
  a short line with no terminal punctuation, in title case, on its own.
  `check_introductions.py` asks the renderer itself.

## Checking

    python3 check_introductions.py            # all books
    python3 check_introductions.py odyssey    # one

It fails nonzero (the epictetus rule: a checker that cannot fail a build
is eventually ignored). It enforces the word band, the banned-phrase
list, the markup rules, the renderer agreement, and that the author is
actually named and a date actually given — which is the cheap guard
against an introduction written about the wrong book, a defect nothing
else here can see.

## Where it is rendered, and where it is not

On the MODERN page, above the Contents, and as the epub's first
frontmatter section. NOT on the `--original` companion page: the last
paragraph describes what this edition did, and those sentences are false
of the source text. `se lint` m-030 wants to know who wrote an
`introduction` semantic, so `rebrand.py` adds the `win` relator (writer
of introduction) to the producer, beside the `trl` it already carries for
the retelling — keyed off the epub spine, so there is no second copy of
"does this book have an introduction" to fall out of step.

## The fact-check pass

Writing them is half the work. Every introduction was then checked by
somebody who did not write it, against the web for biography and
publication history and against the repo for claims about the edition.
That pass caught real errors, and it is the only defence there is: a
well-written wrong fact renders perfectly, passes every mechanical check,
and misinforms every reader of the page. Re-run it whenever a book is
added.
