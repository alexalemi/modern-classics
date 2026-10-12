#!/bin/bash
# Fetch the Standard Ebooks source for The Pilgrim's Progress.
# Run from bunyan/. source/ is not kept in the repo.
set -e
mkdir -p source
B=https://raw.githubusercontent.com/standardebooks/john-bunyan_the-pilgrims-progress/master/src/epub
for f in foreword preface-1 part-1 preface-2 part-2 endnotes; do
  [ -s "source/$f.xhtml" ] || curl -sL --max-time 90 -o "source/$f.xhtml" "$B/text/$f.xhtml"
done
[ -s source/content.opf ] || curl -sL --max-time 90 -o source/content.opf "$B/content.opf"
echo "fetched $(ls source | wc -l) source files"
