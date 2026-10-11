#!/bin/bash
# Fetch the sources for Zur Genealogie der Moral into _src/. Run from genealogy/.
#
# THERE IS NO GERMAN GENEALOGIE ON PROJECT GUTENBERG (confirmed 2026-10-10
# by listing every Nietzsche title under gutenberg.org/ebooks/author/779:
# the German texts are #7202 Ecce homo, #7203 Götzen-Dämmerung, #7204
# Jenseits, #7205 Zarathustra, #7206 Geburt der Tragödie, #7207
# Menschliches, #60360 Wille zur Macht, #19793 Der tolle Mensch). Nor is
# it on German Wikisource or in the Deutsches Textarchiv.
#
#   ekgwb_GM.html  Nietzsche Source, eKGWB/GM: the digital Colli-Montinari
#                  critical text (KGW VI.2), which follows the first
#                  edition (Leipzig: C. G. Naumann, 1887) in its spelling
#                  (Thier, giebt, nöthig, Erkenntniss) and marks
#                  Nietzsche's letter-spacing. THE SOURCE.
#                  http://www.nietzschesource.org/#eKGWB/GM
#   zeno/          zeno.org, Schlechta's Werke in drei Bänden (1954), vol.
#                  2, "Gemeinfrei" (zeno's licence line). Modernised
#                  spelling. A SECOND WITNESS for witness.py only; never
#                  published. Ten pages (Vorrede + 3 per Abhandlung).
#   se.epub, se/   Standard Ebooks, The Genealogy of Morals, tr. Horace B.
#                  Samuel (1913, in Levy's Complete Works) -- the CRIB.
#                  https://standardebooks.org/ebooks/friedrich-nietzsche/
#                  the-genealogy-of-morals/horace-b-samuel
#   en_52319.txt   Project Gutenberg #52319, the same Samuel translation
#                  (kept for the record; SE's text is used).
set -e
mkdir -p _src && cd _src
[ -s ekgwb_GM.html ] || curl -sL -o ekgwb_GM.html \
  "http://www.nietzschesource.org/resources/scripts/static_html_include.php?book=%23eKGWB%2FGM"
[ -s en_52319.txt ] || curl -sL -o en_52319.txt https://www.gutenberg.org/cache/epub/52319/pg52319.txt
if [ ! -d se ]; then
  curl -sL -o se.epub "https://standardebooks.org/ebooks/friedrich-nietzsche/the-genealogy-of-morals/horace-b-samuel/downloads/friedrich-nietzsche_the-genealogy-of-morals_horace-b-samuel.epub?source=download"
  mkdir -p se && (cd se && unzip -oq ../se.epub)
fi
mkdir -p zeno
Z="http://www.zeno.org/Philosophie/M/Nietzsche,+Friedrich/Zur+Genealogie+der+Moral"
E1="Erste+Abhandlung%3A+%C2%BBGut+und+B%C3%B6se%C2%AB,+%C2%BBGut+und+Schlecht%C2%AB"
E2="Zweite+Abhandlung%3A+%C2%BBSchuld%C2%AB,+%C2%BBSchlechtes+Gewissen%C2%AB+und+Verwandtes"
E3="Dritte+Abhandlung%3A+Was+bedeuten+asketische+Ideale"
while read name path; do
  [ -s "zeno/$name.html" ] || { curl -sL -A "Mozilla/5.0" -o "zeno/$name.html" "$Z/$path"; sleep 0.5; }
done <<EOF
V Vorrede
I-01 $E1/1-10
I-11 $E1/11-17
II-01 $E2/1-10
II-11 $E2/11-20
II-21 $E2/21-25
III-01 $E3/1-10
III-11 $E3/11-20
III-21 $E3/21-28
EOF
echo "sources in $(pwd)"
