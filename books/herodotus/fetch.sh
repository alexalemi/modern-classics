#!/bin/bash
# Fetch the Standard Ebooks source for Herodotus, The Histories (Macaulay).
# Run from herodotus/. _src/ is not kept in the repo.
#
#   https://standardebooks.org/ebooks/herodotus/histories/g-c-macaulay
#   git: github.com/standardebooks/herodotus_histories_g-c-macaulay
#   pinned at commit 838070e17b16ade8c926064b23dcd16e64d5a46c (2026-09-04)
#
# SE's own sources: Gutenberg #2707 and #2456 (Macaulay, 1890, two volumes)
# checked against archive.org scans. herodotus.txt in this directory is the
# old Gutenberg-derived text (notes stripped, but the note-reference numbers
# left in the prose, some fused with their neighbours: "4601", "13701"); it
# is kept as the second witness that check.py counts against.
set -e
SHA=838070e17b16ade8c926064b23dcd16e64d5a46c
B=https://raw.githubusercontent.com/standardebooks/herodotus_histories_g-c-macaulay/$SHA/src/epub
mkdir -p _src/se
for f in book-1 book-2 book-3 book-4 book-5 book-6 book-7 book-8 book-9 endnotes preface; do
  [ -s "_src/se/$f.xhtml" ] || curl -sL --max-time 90 -o "_src/se/$f.xhtml" "$B/text/$f.xhtml"
done
[ -s _src/se/content.opf ] || curl -sL --max-time 90 -o _src/se/content.opf "$B/content.opf"
echo "fetched $(ls _src/se | wc -l) source files"
