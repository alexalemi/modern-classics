#!/bin/bash
# Fetch the Standard Ebooks source for Epictetus' Discourses (George Long).
# Run from epictetus/. source/ is not kept in the repo.
set -e
mkdir -p source
B=https://raw.githubusercontent.com/standardebooks/epictetus_discourses_george-long/master/src/epub
for f in introduction preface book-1 book-2 book-3 book-4 endnotes; do
  [ -s "source/$f.xhtml" ] || curl -sL --max-time 90 -o "source/$f.xhtml" "$B/text/$f.xhtml"
done
[ -s source/content.opf ] || curl -sL --max-time 90 -o source/content.opf "$B/content.opf"
echo "fetched $(ls source | wc -l) source files"
