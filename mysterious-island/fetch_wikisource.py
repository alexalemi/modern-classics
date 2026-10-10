"""Fetch the 62 chapters of L'Île mystérieuse from French Wikisource.

Why a second French witness: the Gutenberg French (#14287) has the body
text but NOT Verne's chapter summaries (the "sommaires" Hetzel printed
under every chapter number: "L'ouragan de 1865. — Cris dans les airs.
— ..."). Wikisource's transcription is proofread ("Textes validés")
against the scan of the Hetzel 1875 in-octavo, and carries them. prep.py
takes the summaries from here and the body from Gutenberg, and
check.py compares the two bodies word for word as a completeness check.

Writes _src/wikisource/P-CC.html (the rendered parse output) for
P in 1..3. Re-run is idempotent: existing files are kept.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BOOK = Path(__file__).parent
OUT = BOOK / "_src" / "wikisource"
API = "https://fr.wikisource.org/w/api.php"
UA = "modern-classics-prep/1.0 (public-domain text fetch; python-urllib)"
COUNTS = {1: 22, 2: 20, 3: 20}


def fetch(page):
    q = urllib.parse.urlencode({"action": "parse", "page": page,
                                "prop": "text", "format": "json"})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["parse"]["text"]["*"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p, n in COUNTS.items():
        for c in range(1, n + 1):
            f = OUT / f"{p}-{c:02d}.html"
            if f.exists():
                continue
            page = f"L’Île mystérieuse/Partie {p}/Chapitre {c}"
            f.write_text(fetch(page), encoding="utf-8")
            print("fetched", f.name)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
