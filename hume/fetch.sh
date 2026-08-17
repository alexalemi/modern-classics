#!/bin/bash
# Fetch the Standard Ebooks source for Hume's Enquiry.
# Run from hume/. source/ is not kept in the repo.
set -e
mkdir -p source
B=https://raw.githubusercontent.com/standardebooks/david-hume_an-enquiry-concerning-human-understanding/master/src/epub
for f in $(seq 1 12); do
  [ -s "source/chapter-$f.xhtml" ] || curl -sL --max-time 90 -o "source/chapter-$f.xhtml" "$B/text/chapter-$f.xhtml"
done
[ -s source/content.opf ] || curl -sL --max-time 90 -o source/content.opf "$B/content.opf"
echo "fetched $(ls source | wc -l) source files"
