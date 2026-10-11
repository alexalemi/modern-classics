"""Fetch La Princesse de Clèves and La Princesse de Montpensier from French
Wikisource: both from the SAME validated transcription ("Textes validés"),
Lepetit's 1820 Œuvres complètes de Mesdames de La Fayette, de Tencin et de
Fontaines, tome 2 (index: "La Fayette, Tencin, Fontaines - Œuvres complètes,
Lepetit, 1820, tome 2.djvu"). Why this edition and not Gutenberg #20262:
see prep.py.

Writes _src/wikisource/<name>.html (rendered parse output). Idempotent.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BOOK = Path(__file__).parent
OUT = BOOK / "_src" / "wikisource"
API = "https://fr.wikisource.org/w/api.php"
UA = "modern-classics-prep/1.0 (public-domain text fetch; python-urllib)"
CL = "La Princesse de Clèves, édition Lepetit, 1820"
PAGES = {
    "cleves-1": f"{CL}/Première partie",
    "cleves-2": f"{CL}/Seconde partie",
    "cleves-3": f"{CL}/Troisième partie",
    "cleves-4": f"{CL}/Quatrième partie",
    "montpensier": "La Princesse de Montpensier",
    # Barbin's "Le libraire au lecteur" (file 000): Lepetit omits it; this
    # is the 1689 Barbin printing (TextQuality 50%, the 100 words read by
    # hand against the 1678 wording quoted in Perry's preface)
    "avertissement-1689": "La Princesse de Clèves (édition originale)/Avertissement",
}


def fetch(page, prop="text"):
    q = urllib.parse.urlencode({"action": "parse", "page": page,
                                "prop": prop, "format": "json"})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    for wait in (10, 30, 60, 120):          # Wikisource answers 429 freely
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["parse"][prop]["*"]
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    raise RuntimeError(f"rate-limited fetching {page}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, page in PAGES.items():
        f = OUT / f"{name}.html"
        if f.exists():
            continue
        f.write_text(fetch(page), encoding="utf-8")
        print("fetched", f.name)
        time.sleep(5)


if __name__ == "__main__":
    main()
