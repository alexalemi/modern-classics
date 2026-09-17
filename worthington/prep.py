"""Worthington's splash books: the collection's FIRST RESTORED EDITION.

    python3 worthington/prep.py

TWO WORKS IN ONE VOLUME, both from Project Gutenberg's HTML editions,
which carry the plates the plain text drops:

    #39831  A Study of Splashes (1908)          18,874 words, 218 plates
    #27125  The Splash of a Drop (1894/95)       9,846 words,  29 plates

The 1908 book is the full scientific account. The Splash of a Drop is the
popular version: a Friday Evening Discourse given at the ROYAL
INSTITUTION on 18 May 1894 and printed in 1895 in the SPCK's "Romance of
Science" series -- which makes this the ninth Royal Institution volume in
the collection, after soap-bubbles, candle, forces, fleming, ball,
thompson and tyndall. Dover printed the two together in 1963 and that is
the precedent for pairing them here.

THIS IS A RESTORED EDITION, NOT A RETELLING. Worthington's prose is
already clear -- screened at arch 0.00, calq 25.4, cleaner than any book
this project has modernised and cleaner than books struck from the
roadmap for being too clean. So chapters/ and modern_chapters/ carry THE
SAME PROSE, and the edition's contribution is the apparatus: a caption
and alt text for all 218 plates (the source has a serial number and an
elapsed time, and an EMPTY alt attribute, on every one of them), an
editor's introduction, and a real epub. See ROADMAP.md, "A second strand:
restored editions".

That equality is what makes the pipeline safe: verify.py's word ratio,
the loosest check in the project, becomes an EQUALITY TEST at 1.00. A
restored file that drifts has been edited when it should not have been.
verify.FIGURE strips a marker and its caption from the counts, so the new
captions do not disturb it.

THE FILENAME DOES NOT TELL YOU WHAT THE PLATE IS, and this book proves it
three ways -- every one found by opening the image, never by the name:
  - `fig-a` and `fig-b` are PHOTOGRAPHS (a cavity beside a millimetre
    scale), not figures;
  - `plate-i` is a LINE DIAGRAM of the apparatus, sitting among the
    photographic plates, while `plate-ii` is a photograph;
  - `fig-15a`/`fig-15b` are diagrams stored as JPEG, which is why the PNG
    figures run 1-14 and 16-20 with a hole where 15 should be.
So PLATE_KIND below is a hand-checked table, not a rule over filenames.

FOUR TRAPS, each with a ruling already earned elsewhere in this repo:
  1. EVERY PHOTOGRAPH EXISTS TWICE. The HTML displays `-t` (thumbnail)
     and links `-f` (full). Only the `-f` is extracted. Shipping both is
     how thompson's epub doubled to 51 MB with every plate in it twice.
  2. FIGURES 15a AND 15b APPEAR IN REVERSED ORDER in the source (15b
     first), the symbolic-logic floated-diagram trap: read in document
     order their captions would swap. FLIPPED below, with an assertion.
  3. 197 MID-HEIGHT DECIMAL POINTS (0·002 sec.), and here every one is a
     MEASURED VALUE -- pillow-problems' rule. U+00B7 is preserved
     exactly; it is never "corrected" to a full stop.
  4. 22 PNGs will trip `se lint` f-019 where they have no transparency.
     candle's fix is to convert those to JPEG; build_ebook resolves the
     extension either way.

IDS. assemble.figure_label builds "Figure N" out of an id's digits, and
this book has no single figure sequence: Figs. 1-20 are line diagrams
while the photographs run in SERIES with a per-series number and an
elapsed time. The documented behaviour used here is that AN ID WITH NO
DIGITS GETS NO LABEL AND ITS CAPTION STANDS ALONE. So diagrams keep
numeric ids ("15a" renders "Figure 15a" correctly) and every photograph
takes a DIGIT-FREE id, with its real label inside the caption ("Series
II, 3 -- 0·002 sec. ..."), which is what a reader wants to read anyway.

THE ID MAP IS PINNED (PLATE_IDS, written on the first run and asserted on
every later one). Ids are assigned in document order, so without the pin
a later prep re-run could silently renumber 218 plates out from under 218
hand-written captions -- and nothing downstream would notice, because
every marker would still resolve to a file.
"""
import json
import os
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).parent
ROOT = HERE.parent
IMAGES = ROOT / "site" / "images" / "worthington"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}

STUDY, DROP = "39831", "27125"
SOURCES = {STUDY: "A Study of Splashes", DROP: "The Splash of a Drop"}

# The 1908 book's own title page claims "WITH 197 ILLUSTRATIONS FROM
# INSTANTANEOUS PHOTOGRAPHS"; by the taxonomy below the source carries
# 194 photographs. There is NO list of illustrations in the book to
# arbitrate -- the front matter has a chapter contents and nothing else.
# Recorded rather than silently reconciled (the grimm rule: the book's
# own count is the one witness the pipeline did not produce). Settle it
# against Archive.org's `studyofsplashes00wortrich` before publishing.
CLAIMED_PHOTOGRAPHS = 197

# Plates whose kind cannot be read off the filename. Everything not named
# here follows the prefix: photo-* is a photograph, fig-*/plate-* a
# diagram. Each entry was checked by OPENING the image.
PLATE_KIND = {
    "fig-a": "photo",      # a cavity photographed beside a millimetre scale
    "fig-b": "photo",      # its companion
    "plate-i": "diagram",  # the apparatus: laboratory and dark room
    "plate-ii": "photo",
    "fig-15a": "diagram",  # diagrams of a breaking wave, stored as JPEG
    "fig-15b": "diagram",
}

# Source order is 15b then 15a, because the printer floated them. The
# text discusses 15a first ("a long, smooth, horizontal cylindrical
# edge (see Fig. 15 a)") and 15b second.
FLIPPED = [("fig-15b", "fig-15a")]


def fetch(book_id):
    """The Gutenberg HTML edition, cached beside this file."""
    path = HERE / f"pg{book_id}-h.zip"
    if not path.exists():
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-h.zip"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=300) as r:
            path.write_bytes(r.read())
    return zipfile.ZipFile(path)


def stem_of(name):
    """'images/photo-p012-01-f.jpg' -> 'photo-p012-01'."""
    base = name.split("/")[-1]
    base = re.sub(r"\.(jpg|jpeg|png|gif)$", "", base, flags=re.I)
    return re.sub(r"-[ft]$", "", base)


def kind_of(stem):
    if stem in PLATE_KIND:
        return PLATE_KIND[stem]
    return "photo" if stem.startswith("photo-") else "diagram"


LETTERS = "abcdefghijklmnopqrstuvwxyz"


def photo_id(n):
    """Digit-free, unique, stable: 0 -> 'aa', 1 -> 'ab', ... 675 -> 'zz'.

    Digit-free BY CONSTRUCTION, because assemble.figure_label would
    otherwise print "Figure 12" over a photograph the book calls
    "Series II, 3". check.py asserts the property rather than trusting
    this function to keep it.
    """
    return LETTERS[n // 26] + LETTERS[n % 26]


def diagram_id(stem):
    """'fig-01' -> '1'; 'fig-15a' -> '15a'; 'plate-i' -> 'plate-one'.

    A numbered figure keeps its number so the page says "Figure 15a".
    Everything else gets a digit-free id and carries its own label in
    its caption.
    """
    m = re.fullmatch(r"fig-0*(\d+[a-z]?)", stem)
    if m:
        return m.group(1)
    return {"plate-i": "plate-one", "plate-ii": "plate-two",
            "fig-p033-water": "water-drop", "fig-p033-turp": "turpentine-drop",
            }.get(stem, stem.replace("_", "-"))
