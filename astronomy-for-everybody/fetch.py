"""Fetch Newcomb's Astronomy for Everybody (1902) from Wikisource.

    python3 astronomy-for-everybody/fetch.py

Wikisource's text is transcluded from a VALIDATED index (every page
proofread twice) of the McClure, Phillips first edition of 1902. Every
page (front matter, six Part pages, thirty-three chapters) as rendered HTML
through the MediaWiki parse API, and every plate as its ORIGINAL file, not
the thumbnail the page shows. Into _src/newcomb.zip.
"""
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
API = "https://en.wikisource.org/w/api.php"
UA = {"User-Agent": "modern-classics-ebooks/1.0 (contact: alexalemi@gmail.com)"}
CHAPTERS = {1: 5, 2: 5, 3: 6, 4: 11, 5: 2, 6: 6}


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            time.sleep(10 * (i + 1))
    raise SystemExit("fetch failed: " + url)


def main():
    pages = ["Astronomy for Everybody"]
    for p, n in CHAPTERS.items():
        pages.append(f"Astronomy for Everybody/Part {p}")
        pages += [f"Astronomy for Everybody/Part {p}/Chapter {c}" for c in range(1, n + 1)]
    out = io.BytesIO()
    files = []
    with zipfile.ZipFile(out, "w") as z:
        for k, page in enumerate(pages):
            d = get({"action": "parse", "page": page, "prop": "text|images", "format": "json", "disableeditsection": 1})
            z.writestr(f"{k:02d}.html", d["parse"]["text"]["*"])
            files += [f for f in d["parse"]["images"] if f not in files]
            time.sleep(1)
        z.writestr("pages.json", json.dumps(pages))
        for f in files:
            d = get({"action": "query", "titles": "File:" + f, "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
            ii = list(d["query"]["pages"].values())[0]["imageinfo"][0]
            if ii["url"].endswith(".svg"):
                continue                     # Wikisource's own furniture (icons)
            data = urllib.request.urlopen(urllib.request.Request(ii["url"], headers=UA), timeout=120).read()
            z.writestr("images/" + f, data)
            print(f, ii["width"], ii["height"])
            time.sleep(3)
    (HERE / "_src").mkdir(exist_ok=True)
    (HERE / "_src" / "newcomb.zip").write_bytes(out.getvalue())
    print(len(pages), "pages")


if __name__ == "__main__":
    main()
