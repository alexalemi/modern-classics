#!/bin/bash
# Fetch both sources for Don Quixote. Run from quixote/. source/ is not
# kept in the repo.
#
#   SPANISH (the source text)  Project Gutenberg #2000, Cervantes' own
#                              1605/1615 text, ~390k words.
#   ENGLISH (the crib only)    John Ormsby's 1885 translation, from the
#                              Standard Ebooks repository, one XHTML file
#                              per chapter — which is what makes it usable
#                              as a PER-CHAPTER crib without any alignment
#                              work at all. 126 chapters, 52 + 74.
#
# Ormsby is never the source. He is the de-officiis/ovid crib: consulted
# for who-does-what and for the hard idiom, never translated from.
set -e
mkdir -p source
SE=https://raw.githubusercontent.com/standardebooks/miguel-de-cervantes-saavedra_don-quixote_john-ormsby/master/src/epub

[ -s source/quixote_es.txt ] || curl -sL --max-time 300 -A "modern-classics/1.0" \
  -o source/quixote_es.txt "https://www.gutenberg.org/cache/epub/2000/pg2000.txt"

[ -s source/content.opf ] || curl -sL --max-time 90 -o source/content.opf "$SE/content.opf"

mkdir -p source/ormsby
for f in translators-preface dedication-1 preface-1 epigraph \
         dedication-2 preface-2 endnotes; do
  [ -s "source/ormsby/$f.xhtml" ] || \
    curl -sL --max-time 90 -o "source/ormsby/$f.xhtml" "$SE/text/$f.xhtml" || true
done
for part in 1 2; do
  last=52; [ "$part" = 2 ] && last=74
  for n in $(seq 1 $last); do
    f="chapter-$part-$n.xhtml"
    [ -s "source/ormsby/$f" ] || curl -sL --max-time 90 -o "source/ormsby/$f" "$SE/text/$f"
  done
done
echo "spanish: $(wc -w < source/quixote_es.txt) words"
echo "ormsby:  $(ls source/ormsby | wc -l) files"
