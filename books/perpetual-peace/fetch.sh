#!/bin/sh
# Fetch the sources for perpetual-peace into _src/ (see prep.py).
set -e
cd "$(dirname "$0")"
mkdir -p _src/aa08
# The German, 1795 first edition (Nicolovius), PGDP transcription.
curl -sL -o _src/pg46873.txt https://www.gutenberg.org/cache/epub/46873/pg46873.txt
# The crib: M. Campbell Smith's English (1903), for sense only.
curl -sL -o _src/pg50922_smith.txt https://www.gutenberg.org/cache/epub/50922/pg50922.txt
# Akademie-Ausgabe VIII 341-386 (Kant im Kontext / korpora.org), which
# prints the 1796 second edition: the source of the Second Supplement.
# (https on this host fails through the proxy; http works.)
for p in $(seq 341 386); do
  curl -s -o _src/aa08/$p.html "http://www.korpora.org/kant/aa08/$p.html"
done
