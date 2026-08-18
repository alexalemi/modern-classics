#!/bin/sh
# Boethius, The Consolation of Philosophy (H. R. James, 1897) from
# Standard Ebooks' proofread XHTML -- the same source pipeline as
# bunyan/, autobiography/, epictetus/ and hume/.
#
# NOT from standardebooks.org: that site runs a crawler honeypot which
# bans the IP for 24 hours. Always use raw.githubusercontent.com.
set -e
cd "$(dirname "$0")"
S=https://raw.githubusercontent.com/standardebooks/boethius_the-consolation-of-philosophy_h-r-james/master/src/epub/text
for b in 1 2 3 4 5; do
  curl -sfS "$S/book-$b.xhtml" -o "source/book-$b.xhtml"
done
# chapter counts per book, from the repo listing
for c in $(seq 1 6);  do curl -sfS "$S/chapter-1-$c.xhtml" -o "source/chapter-1-$c.xhtml"; done
for c in $(seq 1 8);  do curl -sfS "$S/chapter-2-$c.xhtml" -o "source/chapter-2-$c.xhtml"; done
for c in $(seq 1 12); do curl -sfS "$S/chapter-3-$c.xhtml" -o "source/chapter-3-$c.xhtml"; done
for c in $(seq 1 7);  do curl -sfS "$S/chapter-4-$c.xhtml" -o "source/chapter-4-$c.xhtml"; done
for c in $(seq 1 6);  do curl -sfS "$S/chapter-5-$c.xhtml" -o "source/chapter-5-$c.xhtml"; done
ls source | wc -l
