"""Fetch Cardozo's The Nature of the Judicial Process from Wikisource.

    python3 nature-of-the-judicial-process/fetch.py

The Wikisource text is transcluded from a VALIDATED index (every page
proofread twice) of the Yale University Press edition (the scan is of the
eleventh printing, 1941, from the 1921 plates). The four lectures come as
rendered HTML through the MediaWiki parse API; the memorial leaf (pages
5-6) and the Contents (page 7) as page wikitext. All of it into
_src/cardozo.zip, which prep.py reads.
"""
import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
API = "https://en.wikisource.org/w/api.php"
UA = {"User-Agent": "modern-classics-ebooks/1.0 (contact: alexalemi@gmail.com)"}


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            time.sleep(5 * (i + 1))
    raise SystemExit("fetch failed: " + url)


def main():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for n in ("I", "II", "III", "IV"):
            d = get({"action": "parse", "page": f"The Nature of the Judicial Process/Lecture {n}",
                     "prop": "text", "format": "json", "disableeditsection": 1})
            z.writestr(f"lecture{n}.html", d["parse"]["text"]["*"])
            time.sleep(1)
        for p in (5, 6):
            url = ("https://en.wikisource.org/w/index.php?title=" +
                   urllib.parse.quote(f"Page:Cardozo-Nature-Of-The-Judicial-Process.pdf/{p}") + "&action=raw")
            z.writestr(f"page{p}.wiki", urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
            time.sleep(1)
        for p in (5, 6, 7):
            d = get({"action": "parse", "page": f"Page:Cardozo-Nature-Of-The-Judicial-Process.pdf/{p}",
                     "prop": "text", "format": "json", "disableeditsection": 1})
            z.writestr(f"page{p}.html", d["parse"]["text"]["*"])
            time.sleep(1)
    (HERE / "_src").mkdir(exist_ok=True)
    (HERE / "_src" / "cardozo.zip").write_bytes(out.getvalue())
    print("wrote _src/cardozo.zip")


if __name__ == "__main__":
    main()
