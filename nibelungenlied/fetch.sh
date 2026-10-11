#!/bin/bash
# Fetch the sources for the Nibelungenlied into _src/. Run from nibelungenlied/.
#   augustana/nib_n_NN.html  THE SOURCE. Bibliotheca Augustana (Ulrich Harsch),
#        "Der Nibelunge nôt": Karl Bartsch's text of the B version (Leipzig:
#        Brockhaus, 1870-80) in the raw form of Oxford Text Archive text 0202,
#        with gaps supplied in italics by Harsch. 39 pages, 2,379 strophes.
#        https://www.tha.de/~harsch/germanica/Chronologie/12Jh/Nibelungen/nib_n_00.html
#        (www.hs-augsburg.de/~harsch/... redirects there)
#   augustana/nib_b_NN.html  SECOND WITNESS, never translated: Hermann
#        Reichert's diplomatic transcription of manuscript B (St. Gallen,
#        Cod. Sang. 857), same site.
#   pg1151.txt   THE CRIB: Daniel B. Shumway, The Nibelungenlied (1909),
#        literal prose of Bartsch's B text. https://www.gutenberg.org/ebooks/1151
#   pg3636.txt   Margaret Armour, The Fall of the Nibelungs (1897), prose.
#        Measured, not used. https://www.gutenberg.org/ebooks/3636
#   pg59831.txt  Alice Horton, The Lay of the Nibelung Men (1898), verse.
#        Measured, not used. https://www.gutenberg.org/ebooks/59831
#   pg7321.txt   George H. Needler (1904), verse. Not used.
#   pg38468.txt  W. N. Lettsom (1850), verse, Lachmann's A. Not used.
#   pg14915.txt  Karl Simrock, Das Nibelungenlied (New High German verse,
#        C version) -- NOT the Middle High German the ROADMAP took it for.
#        Consulted once (LINE_FIXES 524). https://www.gutenberg.org/ebooks/14915
set -e
mkdir -p _src/augustana && cd _src
for n in 1151 3636 59831 7321 38468 14915; do
  [ -s pg$n.txt ] || curl -sL -o pg$n.txt https://www.gutenberg.org/cache/epub/$n/pg$n.txt
done
B=https://www.tha.de/~harsch/germanica/Chronologie/12Jh/Nibelungen
cd augustana
for f in nib_intr nib_text nib_quel nib_n_00 nib_b_00; do
  [ -s $f.html ] || curl -sL -o $f.html $B/$f.html
done
for i in $(seq -w 1 39); do
  for p in n b; do
    [ -s nib_${p}_$i.html ] || { curl -sL -o nib_${p}_$i.html $B/nib_${p}_$i.html; sleep 0.3; }
  done
done
echo "sources in $(pwd)/.."
