#!/bin/bash
# Fetch the Gutenberg HTML edition of Symbolic Logic Part I (#28696),
# which carries the 314 diagrams the plain-text edition cannot.
set -e
mkdir -p source
[ -s source/h.zip ] || curl -sL --max-time 180 -o source/h.zip \
  "https://www.gutenberg.org/cache/epub/28696/pg28696-h.zip"
cd source && unzip -o -q h.zip
echo "fetched $(ls images | wc -l) diagrams"
