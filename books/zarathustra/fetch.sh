#!/bin/bash
# Fetch the sources for Also sprach Zarathustra into _src/. Run from zarathustra/.
#   de_7205.txt  Project Gutenberg #7205 (German; the SOURCE)
#                https://www.gutenberg.org/ebooks/7205
#   se.epub, se/ Standard Ebooks, Thus Spake Zarathustra, tr. Thomas Common
#                (1909) -- the CRIB. https://standardebooks.org/ebooks/
#                friedrich-nietzsche/thus-spake-zarathustra/thomas-common
#   en_1998.txt  Project Gutenberg #1998, Common's English with
#                Förster-Nietzsche's introduction and Ludovici's notes
#                (not used: SE's text is the same translation, cleaner)
#   zeno/        zeno.org pages (Schlechta, Werke in drei Bänden, 1954),
#                a SECOND WITNESS for witness.py only. Never published.
set -e
mkdir -p _src && cd _src
[ -s de_7205.txt ] || curl -sL -o de_7205.txt https://www.gutenberg.org/cache/epub/7205/pg7205.txt
[ -s en_1998.txt ] || curl -sL -o en_1998.txt https://www.gutenberg.org/cache/epub/1998/pg1998.txt
if [ ! -d se ]; then
  curl -sL -o se.epub "https://standardebooks.org/ebooks/friedrich-nietzsche/thus-spake-zarathustra/thomas-common/downloads/friedrich-nietzsche_thus-spake-zarathustra_thomas-common.epub?source=download"
  mkdir -p se && (cd se && unzip -oq ../se.epub)
fi
# zeno: the 85 page URLs are listed in zeno/index.txt (file -> path)
if [ -f zeno/index.txt ]; then
  while read f path; do
    [ -s "zeno/$f.html" ] || { curl -sL -o "zeno/$f.html" "http://www.zeno.org$path"; sleep 0.5; }
  done < zeno/index.txt
fi
echo "sources in $(pwd)"
