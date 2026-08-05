#!/bin/bash
# Fetch the Gutenberg HTML edition of A Tangled Tale (#29042), which
# carries the ten plates the plain-text edition drops.
set -e
mkdir -p source
[ -s source/h.zip ] || curl -sL --max-time 120 -o source/h.zip \
  "https://www.gutenberg.org/cache/epub/29042/pg29042-h.zip"
cd source && unzip -o -q h.zip
echo "fetched $(ls images | wc -l) images"
