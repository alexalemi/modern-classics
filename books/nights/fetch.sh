#!/bin/bash
# Fetch the four Burton volumes this selection draws on. Run from nights/.
# source/ is not kept in the repo.
#
#   #3435  Vol 1        the frame story and the Baghdad cycle
#   #3440  Vol 6        Sindbad the Seaman, the City of Brass
#   #3444  Vol 10       the CONCLUSION — Shahrazad's release. Without it
#                       the book has no ending.
#   #3447  Suppl. v3    Aladdin and Ali Baba, the two "orphan" tales that
#                       are not in Burton's main Calcutta II text at all.
#
# NOTE: prefer these transcriptions over #51252 etc. These carry the
# [FN#nnn] footnote markers, which is what makes Burton's apparatus
# cleanly separable from the tales. The apparatus is NOT the book.
set -e
mkdir -p source
for id in 3435 3440 3444 3447; do
  [ -s "source/pg$id.txt" ] || curl -sL --max-time 300 -A "modern-classics/1.0" \
    -o "source/pg$id.txt" "https://www.gutenberg.org/cache/epub/$id/pg$id.txt"
done
wc -w source/*.txt
