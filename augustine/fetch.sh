#!/bin/bash
# Fetch the source for Augustine's Confessions (Pusey, 1838).
# Run from augustine/. source/ is not kept in the repo.
set -e
mkdir -p source
[ -s source/pg3296.txt ] || curl -sL --max-time 120 -o source/pg3296.txt \
  "https://www.gutenberg.org/cache/epub/3296/pg3296.txt"
echo "fetched $(wc -w < source/pg3296.txt) words"
