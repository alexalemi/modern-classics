#!/bin/bash
# Rebuild every epub and every page, e.g. after a branding change
# (rebrand.VERSION bump). Logs to build/rebuild_all/. Usage:
#   ./rebuild_all.sh [JOBS]      # default 3 books at a time
set -u
cd "$(dirname "$0")"
export SE_CACHE_PATH="$PWD/build/selenium"   # MathML books: se renders formulas through Firefox (RESTORED.md)
JOBS=${1:-3}
LOG=build/rebuild_all; mkdir -p "$LOG"

books=$(python3 -c "import json;print('\n'.join(json.load(open('ebook_meta.json'))))")

one() {   # one book: its epub(s), then its page(s)
  b=$1; L=build/rebuild_all/$b.log
  { python3 build_ebook.py "$b" && echo "EPUB OK $b" || echo "EPUB FAIL $b"
    if grep -q '^ORIGINAL_TEXT=yes' "$b/env" 2>/dev/null; then
      python3 build_ebook.py "$b" --original && echo "EPUB-ORIG OK $b" || echo "EPUB-ORIG FAIL $b"
      python3 assemble.py "$b" --original >/dev/null && echo "PAGE-ORIG OK $b" || echo "PAGE-ORIG FAIL $b"
    fi
    python3 assemble.py "$b" >/dev/null && echo "PAGE OK $b" || echo "PAGE FAIL $b"
  } > "$L" 2>&1
  grep -E '^(EPUB|PAGE)' "$L"
}
export -f one
echo "$books" | xargs -P "$JOBS" -I{} bash -c 'one {}' | tee "$LOG/summary.txt"

python3 build_index.py; python3 build_restored.py; python3 build_about.py; python3 build_feeds.py
echo "FAILURES:"; grep FAIL "$LOG/summary.txt" || echo "none"
