#!/usr/bin/env bash
# Pillow Problems (Curiosa Mathematica, Part II), Lewis Carroll, 1893.
# Gutenberg #79080 — the illustrated HTML edition. There is no plain-text
# edition: the mathematics is 2,436 separate SVG files pulled in by <img>.
set -euo pipefail
cd "$(dirname "$0")/source"
curl -sSL -A "modern-classics/1.0" \
  -o pg79080-images.html "https://www.gutenberg.org/cache/epub/79080/pg79080-images.html"
curl -sSL -A "modern-classics/1.0" -o pg79080-h.zip \
  "https://www.gutenberg.org/cache/epub/79080/pg79080-h.zip" || true
ls -la
