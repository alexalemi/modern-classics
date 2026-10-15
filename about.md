<!-- ABOUT PAGE PROSE — written by Alex. Everything in this file is the
     page body; edit freely and run `make about` to render it into
     site/about.html. Standard Markdown: paragraphs, ## headings,
     [links](https://…), *emphasis*, lists.

     The placeholder below just sketches one possible shape — replace
     every word of it with your own prose. -->

Modern Classics retells classic public-domain books in contemporary English.

## Why

When I was young, I read [Flatland](flatland.html) and loved it. In many ways I think it was the book that first got me interested in science. If you're unfamiliar, its a story written by a square. He lives in a purely two-dimensional world and explains how they get on in that place. One day, he's visited by a Sphere, and has his mind opened up to the possibilities of higher spatial dimensions. The book is a ruse, its meant to get you, a feeble three-dimensional being to start to ponder what a four-dimensional world would be like. Anywho, its a great book. 

I suggested my son read it, and he immediately bounced off of it. When I went back and tried to reread it myself, I realized its because the book was written in 1884 and so the style of prose is hard for a modern reader. I think this is a real shame, as the book was meant to be for a popular audience.  This got me wondering what it would look like to *translate* the book to contemporary English.  AI tools like [Claude](https://claude.ai) have come a long way, and I thought they could be up for this kind of task. 

I was pleased with the result, and it got me thinking about other books that were lost to modern audiences. In particular there are tons of old works that were meant to be for a popular lay audience in other languages, but because of an accident of history the available english translations date from the 19th century. This means the works, which were meant to be widely accessible, have been *lost* to modern audiences.

## How it's made

Here I use [Claude](https://claude.ai) to translate the original books into contemporary English. I use the [standardebooks.org](https://standardebooks.org) project for a bunch of wonderful guidelines for producing high quality epub ebooks.

Each book gets more care than a single "please modernize this" prompt. The process looks like this:

1. **Source.** I start from a public-domain text, usually from [Standard Ebooks](https://standardebooks.org) or [Project Gutenberg](https://www.gutenberg.org) (each book's page links its source). The text is split into chapter-sized pieces, and stray artifacts of old editions — translator footnotes, publisher ads, printers' errors — are stripped or fixed, with the changes logged.

2. **A translation strategy.** Before any translating happens, Claude studies the whole work and writes an analysis: the author's voice and how to keep it, archaic vocabulary and what it should consistently become, content that needs careful historical handling, and — importantly — a list of famous passages that must survive recognizably. Nobody wants a Meditations that's lost "the best revenge is not becoming like the person who wronged you," or an Enchiridion without "Some things are up to us, and some things are not."

3. **Translation.** The persona is a scholar who has studied the work their whole life and happens to be a gifted storyteller, retelling it for a modern reader — faithful to the meaning, complete (never summarized), but genuinely fun to read. Chapters are translated a few at a time, and the translators share a running ledger of decisions — locked vocabulary, tone calibrations, forward references — so chapter 40 uses the same words as chapter 2.

4. **Verification.** Software checks every chapter mechanically: nothing missing, no chapter silently shortened (word-count ratios catch a translator that summarizes instead of translating — the failure mode I worry about most), and every one of those famous passages present, word for word.

5. **Assembly.** The chapters become the web pages here and epubs built with the Standard Ebooks toolchain, with covers from public-domain paintings.

An honest caveat: these are AI retellings, and despite the checks, a turn of phrase may occasionally drift from the original's nuance. Treat these as a friendly first encounter, not a scholarly edition — and if a book grabs you, go read a real translation of the original. Every page links to the source text for exactly that reason. If you spot something off, [tell me](mailto:contact@emend.press).

## Restored editions

Not every old book needs retelling. Some are already clear and simply deserve a better edition than they have: the plates scanned properly, every illustration captioned and described for readers who can't see it, the mathematics typeset, and an ebook that works on a real device. Those are the [restored editions](./#restored). The words are the author's, unchanged; what's new is the apparatus around them. A few of the retellings also have their original text here as a companion, so you can read the two side by side.

## Emend Press

Modern Classics is published by Emend Press. *To emend* is to correct a text, which is what an editor does. Every book here is free to read online and to download, and the work done on them is dedicated to the public domain (CC0), except where a book's colophon says otherwise. Corrections, suggestions and requests are welcome at [contact@emend.press](mailto:contact@emend.press).

## Following along

New retellings appear here as they're finished. Two ways to subscribe:

**RSS** — point any feed reader (Feedly, NetNewsWire, Miniflux, …) at:

    https://emend.press/feed.xml

Each new book shows up as an entry with a link to read it here and the epub attached.

**OPDS** — if you read on an e-reader, the whole library is an [OPDS catalog](https://en.wikipedia.org/wiki/Open_Publication_Distribution_System), which most reading apps can browse directly. Add this catalog URL in KOReader (Search → OPDS catalog), Moon+ Reader (Net Library), Thorium, Aldiko, or any other OPDS-aware app:

    https://emend.press/opds.xml

You'll get the full shelf with covers, and can download any book straight to your device — no computer required.

## Symbols on e-readers

A few of the books use signs that ordinary text fonts don't have: the logic in *Gödel's Proof* and Boole's *Laws of Thought* (∃, ∨, ⊃, ∼, ∴), the mathematics in *Calculus Made Easy* and Carroll's *Pillow Problems* (∫, ≠, ∠), the planet signs in Euler's letters, the runes in *Journey to the Center of the Earth*. Phones, tablets, computers and most reading apps borrow a missing sign from another font, so these show up without your doing anything. Some small e-ink readers can't, and print a box instead.

For readers running CrossPoint, such as the Xteink X3, there is a font with every character in these books: [**Emend Serif**](downloads/EmendSerif-crosspoint.zip) (3 MB). Unzip it, copy the `EmendSerif` folder into the `fonts` folder on the reader's SD card (make one if it isn't there), and choose Emend Serif as the reading font in the reader's settings. It is [Literata](https://github.com/googlefonts/literata) for the text, with Google's [Noto](https://notofonts.github.io) fonts filling in the symbols, and like them it is free under the [SIL Open Font License](https://openfontlicense.org).
