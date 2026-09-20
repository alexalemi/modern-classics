#!/bin/sh
# Byrne capture: typeset the recreation with the capture hooks, then split
# the picture pages out as SVG. Run from anywhere; writes byrne/_src/build/.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
B="$HERE/../_src/build"
cd "$B"
cp "$HERE/capture.lua" "$HERE/hooks.tex" .
cp ../byrne-euclid/byrnebook.cls .
sed 's/^\\begin{document}$/\\begin{document}\n\\input{hooks.tex}/' ../byrne-euclid/byrne-en-latex.tex > cap.tex
export TEXMFHOME="$B/../texmf" TEXMFVAR="$B/../texmf-var"
lualatex -interaction=nonstopmode cap.tex > cap.run 2>&1 || true
grep -q "Output written on cap.pdf" cap.log
python3 - <<'PY'
import subprocess, re
out = subprocess.run(['pdfinfo', '-f', '1', '-l', '99999', 'cap.pdf'], capture_output=True, text=True).stdout
sizes = re.findall(r'Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+)', out)
main = {int(p) for p, w, h in sizes if abs(float(w) - 419.528) < 0.1 and abs(float(h) - 595.276) < 0.1}
pics = [int(p) for p, w, h in sizes if int(p) not in main]
n = sum(1 for _ in open('pictures.tsv'))
assert len(pics) == n, (len(pics), n)
open('picpages.txt', 'w').write("\n".join(map(str, pics)))
print(len(main), "text pages,", len(pics), "pictures")
PY
rm -rf svg && mkdir svg
mutool draw -q -F svg -o svg/p%d.svg cap.pdf "$(tr '\n' ',' < picpages.txt | sed 's/,$//')" 2>/dev/null
ls svg | wc -l
