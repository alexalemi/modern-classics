#!/usr/bin/env bash
# Pull the Standard Ebooks source for Mill's The Subjection of Women.
#
# ALWAYS FROM raw.githubusercontent.com, NEVER standardebooks.org: the
# site runs a crawler honeypot that bans the IP for 24 hours.
set -euo pipefail
cd "$(dirname "$0")"

REPO=https://raw.githubusercontent.com/standardebooks/john-stuart-mill_the-subjection-of-women/master/src/epub/text
mkdir -p source

for f in chapter-1 chapter-2 chapter-3 chapter-4 endnotes; do
    curl -fsS "$REPO/$f.xhtml" -o "source/$f.xhtml"
    printf '%8d  %s\n' "$(wc -c < "source/$f.xhtml")" "$f.xhtml"
done
