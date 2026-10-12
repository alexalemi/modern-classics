#!/bin/bash
# Fetch the Standard Ebooks source for Le Morte d'Arthur. Run from malory/.
# source/ is not kept in the repo.
#
#   https://standardebooks.org/ebooks/thomas-malory/le-morte-darthur
#   git: github.com/standardebooks/thomas-malory_le-morte-darthur
#
# SE follows the Gutenberg #1251/#1252 transcription (Sir Edward Strachey's
# 1868 Globe edition, Caxton's 1485 text in modernized spelling), and keeps
# Caxton's 21 Books, his chapter rubrics as chapter titles, the Caxton
# preface and an SE glossary of obsolete words.
set -e
mkdir -p source
B=https://raw.githubusercontent.com/standardebooks/thomas-malory_le-morte-darthur/master/src/epub
files=$(curl -sL --max-time 60 https://api.github.com/repos/standardebooks/thomas-malory_le-morte-darthur/contents/src/epub/text \
  | python3 -c "import json,sys; print(' '.join(x['name'] for x in json.load(sys.stdin)))")
for f in $files; do
  [ -s "source/$f" ] || curl -sL --max-time 90 -o "source/$f" "$B/text/$f"
done
for f in content.opf toc.xhtml; do
  [ -s "source/$f" ] || curl -sL --max-time 90 -o "source/$f" "$B/$f"
done
echo "fetched $(ls source | wc -l) source files"

# Second witness: Gutenberg #1251/#1252 (the same Pollard text, two volumes).
# check.py counts its Contents list against SE's chapter files.
mkdir -p source/gutenberg
for id in 1251 1252; do
  [ -s "source/gutenberg/pg$id.txt" ] || curl -sL --max-time 300 -A "modern-classics/1.0" \
    -o "source/gutenberg/pg$id.txt" "https://www.gutenberg.org/cache/epub/$id/pg$id.txt"
done
