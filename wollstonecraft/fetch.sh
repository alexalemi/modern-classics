#!/usr/bin/env bash
# Pull the Standard Ebooks source for Wollstonecraft's A Vindication of
# the Rights of Woman.
#
# ALWAYS FROM raw.githubusercontent.com, NEVER standardebooks.org: the
# site runs a crawler honeypot that bans the IP for 24 hours.
set -euo pipefail
cd "$(dirname "$0")"

REPO=https://raw.githubusercontent.com/standardebooks/mary-wollstonecraft_a-vindication-of-the-rights-of-woman/master/src/epub/text
mkdir -p source

FILES=(dedication introduction endnotes)
for n in $(seq 1 13); do FILES+=("chapter-$n"); done

for f in "${FILES[@]}"; do
    curl -fsS "$REPO/$f.xhtml" -o "source/$f.xhtml"
    printf '%8d  %s\n' "$(wc -c < "source/$f.xhtml")" "$f.xhtml"
done
