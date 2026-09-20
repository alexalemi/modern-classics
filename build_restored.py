#!/usr/bin/env python3
"""Build site/restored.html, the Restored Editions page.

    python3 build_restored.py

A RESTORED EDITION IS NOT A RETELLING. The prose is the author's, word
for word; what this collection adds is the apparatus — a caption and alt
text for every plate, proper markup, a real epub, a readable page and an
editor's introduction. Alex asked for the strand on 2026-09-17, after
Worthington's A Study of Splashes screened cleaner than any book the
project has modernised: "books we just give some TLC and put into
standard books quality, original prose but improved markup and a nice
ebook edition and web edition."

TWO SHAPES, and the page lists both:

  COMPANION  a book whose modern retelling is the primary edition and
             whose original text is also published — the seven Royal
             Institution volumes. `ORIGINAL_TEXT=yes` in env. Its
             captions already existed (assemble.caption_map lifts them
             out of modern_chapters/), so these cost almost nothing.

  NATIVE     a book with no retelling at all, because it does not need
             one. `EDITION=restored` in env. Worthington is the first.

THE LIST IS DERIVED FROM env, NEVER KEPT HERE. A hand-maintained list
would be a second copy of "which books are restored", and this repo has
scars from a fact held in two places drifting apart — the descartes
repair that reached no reader because only build_feeds.py knew the
published filename. The only per-book text stored below is the blurb,
which exists nowhere else.
"""
import html
import sys
from pathlib import Path

import assemble

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# One line per restored edition, and the ONLY thing hard-coded here:
# a blurb has no other home. Keyed by book directory.
# A blurb has no other home, so it lives here -- but it must NOT repeat
# anything that is derivable. The plate count is appended by main() from
# plate_count(), and an earlier draft of this file wrote "thirteen months
# after Röntgen" into the thompson blurb, which is the very error the
# fact-check pass had just removed from that book's introduction. A fact
# copied into a second place comes back wrong.
BLURBS = {
    "tyndall": "Eighteen sixty-seven, and the book every later Royal "
               "Institution lecturer is imitating.",
    "thompson": "The Christmas course given twelve months after Röntgen "
                "announced the X-ray, with one lecture on nothing else. "
                "The plates were recut and cleaned from the page scans.",
    "ball": "Six lectures from the sun out to the nebulae, by the funniest "
            "of the lecturers; Ball’s own captions are frequently the joke.",
    "fleming": "Christmas 1901, weeks after Marconi pushed a signal across "
               "the Atlantic, reported here as current news.",
    "soap-bubbles": "Three Christmas lectures on why a bubble is round, "
                    "with the recipes for doing every experiment yourself.",
    "forces": "The Christmas course of 1859, the winter before the Candle, "
              "driving at the idea that the forces of nature are one.",
    "candle": "Faraday’s last Christmas course, and the most famous "
              "science lectures ever given.",
    "worthington": "The splash of a drop, photographed by electric spark in "
                   "hundredths of a second — with Worthington’s 1894 Royal "
                   "Institution discourse on the same subject.",
    "aesop": "All 284 fables in Vernon Jones’s 1912 translation, with "
             "Chesterton’s introduction and every Rackham plate and "
             "silhouette.",
    "old-indian-legends": "Fourteen Dakota legends of Iktomi the trickster and "
                          "his neighbours, with the preface and Angel De "
                          "Cora’s plates that Gutenberg dropped.",
    "american-indian-stories": "Her childhood on the Yankton reservation, her "
                               "schooldays in the East, her stories, and her "
                               "1921 case against the Indian Bureau.",
    "short-history-of-the-world": "From the nebulae to the peace of 1922 in "
                                  "sixty-seven chapters, with all 208 plates "
                                  "and the preface restored.",
    "problems-of-philosophy": "A table, its colour and its shape, and what if "
                              "anything we know about it. The 1912 text.",
    "calculus-made-easy": "“What one fool can do, another can.” The 1914 "
                          "edition, with every formula typeset rather than "
                          "pictured.",
    "irish-fairy-tales": "Ten stories of Fionn, the Fianna and the Shi’, with "
                         "Rackham’s colour plates and drawings, and the "
                         "captions Gutenberg dropped.",
}

HEAD = """<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>Restored Editions &mdash; Modern Classics</title>
<style>
html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
  font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
}

body { color: #1d1d1d; }

h1 { margin-top: 1em; text-align: center; }

h2 {
  font-size: 0.95em;
  font-weight: normal;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #888;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.4em;
  margin: 3em 0 1em;
}

p, ul, ol { margin-bottom: 2em; }

.subtitle {
  text-align: center;
  font-style: italic;
  margin-top: -1em;
  margin-bottom: 3em;
}

.book-list { list-style: none; padding: 0; }
.book-list li { margin-bottom: 1.75em; }
.book-list a { font-size: 1.15em; text-decoration: none; color: #333; }
.book-list a:hover { color: #000; text-decoration: underline; }

.author { display: block; font-size: 0.8em; color: #666; margin-top: 0.2em; }
.blurb { display: block; font-size: 0.9em; color: #444;
         font-style: italic; margin-top: 0.2em; }

.note {
  font-size: 0.9em;
  color: #444;
  border-left: 3px solid #ddd;
  padding-left: 1em;
  margin-bottom: 3em;
}
</style>
</head>

<body>

<h1>Restored Editions</h1>
<p class="subtitle">The author&rsquo;s own words, properly presented</p>
<p class="subtitle" style="font-size: 0.8em;"><a href="index.html">The
retellings</a> &middot; <a href="about.html">About</a></p>

<p class="note">Not every old book needs retelling. Some are already
clear and simply deserve a better edition than they have. In these
volumes <strong>the prose is the author&rsquo;s, unchanged</strong>;
what has been added is the apparatus &mdash; a caption and descriptive
alt text for every plate, modern typesetting, and an ebook worth
reading on a real device. Where a book captioned its own illustrations,
those captions are the author&rsquo;s and stand as printed.</p>
"""

FOOT = "\n</body>\n</html>\n"


def entry(title, author, date, page, epub, blurb, plates=None):
    bits = [f'{html.escape(author)} ({html.escape(date)})']
    if epub:
        bits.append(f'<a href="ebooks/{epub}">epub</a>')
    line = " &middot; ".join(bits)
    out = [f'  <li>\n    <a href="{page}">{html.escape(title)}</a>',
           f'    <span class="author">{line}</span>']
    if blurb:
        out.append(f'    <span class="blurb">{blurb}</span>')
    out.append("  </li>")
    return "\n".join(out)


def plate_count(d):
    """How many plates the book actually carries, counted from the files.

    Derived, never stored: the blurbs quote these numbers and a stored
    count would drift the moment a prep re-run changed one.
    """
    import re
    n = 0
    src = d / "chapters"
    if not src.is_dir():
        src = d / "modern_chapters"
    for f in sorted(src.glob("*.txt")):
        if not re.fullmatch(r"\d{3}\.txt", f.name):
            continue
        n += len(assemble.FIGURE_INLINE.findall(f.read_text()))
    return n


def books():
    """(kind, book_dir, env) for every restored edition, from env alone."""
    for d in sorted(ROOT.iterdir()):
        envp = d / "env"
        if not envp.is_file():
            continue
        env = assemble.read_env(envp)
        if env.get("EDITION", "").lower() == "restored":
            yield "native", d, env
        elif env.get("ORIGINAL_TEXT"):
            yield "companion", d, env


def main():
    native, companion = [], []
    for kind, d, env in books():
        page_stem = env.get("PAGE", d.name)
        if kind == "companion":
            page = f"{page_stem}-original.html"
            epub = assemble.find_epub(d, ROOT, original=True)
        else:
            page = f"{page_stem}.html"
            epub = assemble.find_epub(d, ROOT)
        if not (SITE / page).exists():
            print(f"  ! {d.name}: {page} not built yet, skipped")
            continue
        n = plate_count(d)
        blurb = BLURBS.get(d.name, "")
        if n:
            blurb = (blurb + " " if blurb else "") + f"{n} plates."
        row = entry(env["ORIGINAL_WORK"], env["AUTHOR"], env["DATE"],
                    page, epub, blurb)
        (native if kind == "native" else companion).append(
            (n, d.name, row))

    out = [HEAD]
    if native:
        out.append("<h2>Editions</h2>\n<ul class=\"book-list\">")
        out += [r for _, _, r in sorted(native, reverse=True)]
        out.append("</ul>")
    if companion:
        out.append("<h2>The Royal Institution lectures</h2>\n"
                   "<ul class=\"book-list\">")
        # by plate count, which is the reason to come to this page
        out += [r for _, _, r in sorted(companion, reverse=True)]
        out.append("</ul>")
        out.append('<p class="note">Each of these is also published as a '
                   'retelling in contemporary English; the link on every '
                   'book page goes to it, and back.</p>')
    (SITE / "restored.html").write_text("\n".join(out) + FOOT)
    print(f"wrote site/restored.html "
          f"({len(native)} edition(s), {len(companion)} companion(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
