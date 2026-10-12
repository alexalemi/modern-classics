#!/usr/bin/env bash
# Euclid and His Modern Rivals, Lewis Carroll, 1879; 2nd ed. 1885.
#
# NOT ON GUTENBERG in any edition -- checked 2026-08-06, and the search
# does work (the control query finds Pillow Problems at #79080). So this is
# the thompson/ OCR path, and the source has to be built before it can be
# translated.
#
# TWO SCANS, AND BOTH ARE NEEDED. They are different editions, so they
# differ in content as well as in OCR, but their OCR errors are
# INDEPENDENT -- which makes each the corrector of the other, and is the
# single biggest lever on a source this damaged. See source_notes.txt.
set -euo pipefail
cd "$(dirname "$0")/source"
A=euclidhismodernr00carr      # 1885, 2nd ed, scribe2 scan -- COPY TEXT
B=euclidandhismode000469mbp   # 1879, 1st ed, Million Books scan -- CORRECTOR

for id in "$A" "$B"; do
  curl -sSL -m 300 -A "modern-classics/1.0" \
    -o "${id}_djvu.txt" "https://archive.org/download/$id/${id}_djvu.txt"
done
# ABBYY XML for the 1885: word coordinates, and the Picture/Table blocks
# that say where the 29 diagrams and 19 tables are on the page.
curl -sSL -m 600 -A "modern-classics/1.0" \
  -o "${A}_abbyy.gz" "https://archive.org/download/$A/${A}_abbyy.gz"
curl -sSL -m 300 -A "modern-classics/1.0" \
  -o "${A}_metadata.json" "https://archive.org/metadata/$A"
ls -la
