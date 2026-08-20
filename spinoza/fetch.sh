#!/usr/bin/env bash
# Spinoza's Ethics, Elwes's 1883 translation, from Project Gutenberg.
# Standard Ebooks has no Spinoza (checked 2026-08-19), so Gutenberg is
# the source rather than the fallback.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p source
curl -fsS "https://www.gutenberg.org/cache/epub/3800/pg3800.txt" \
     -o source/ethics.txt
printf '%8d words  source/ethics.txt\n' "$(wc -w < source/ethics.txt)"
