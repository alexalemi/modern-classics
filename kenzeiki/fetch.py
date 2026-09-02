"""Fetch the Teiho Kenzeiki zue page images from the National Archives.

訂補建撕記図会 -- Kenzei's fifteenth-century life of Dogen in Menzan
Zuiho's annotated recension, illustrated by Daiken, published 1806.
Two volumes, held in the 内閣文庫 and digitised by the NATIONAL ARCHIVES
OF JAPAN (not NDL, which is why it took a lead from Alex to find).

    search    https://www.digital.archives.go.jp/api/search?title=...
    manifest  https://www.digital.archives.go.jp/api/iiif/{aip}/manifest.json

THE SEARCH API HAS A TRAP WORTH KEEPING: it accepts `keyword`,
`freeWord`, `searchWord` and `anyWord` and silently returns the ENTIRE
ARCHIVE for each -- 4.29 million hits, which looks like a working query
and is not. Only `title` and `q` filter.

EACH IMAGE IS AN OPENING, not a page: two facing half-leaves of a
folded woodblock book, printed kanji-katakana. They are cut apart here
and fetched separately, because a half-leaf at 2200px is comfortably
legible where a whole opening at the same width is not, and the text
has to be read off the image -- there is no transcription of this book
anywhere, and no English translation that is not in copyright.
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
MANIFEST = "https://www.digital.archives.go.jp/api/iiif/%s/manifest.json"
VOLS = [("4982930", 1, 62), ("4982931", 2, 57)]
PAGES = os.path.join(HERE, "pages")

# A SECOND IMPRESSION, AND IT IS THE ONLY CHECK THIS BOOK CAN HAVE.
# There is no transcription of the Kenzeiki anywhere free and no
# English translation out of copyright, so the transcription made here
# has no crib behind it -- and a misread character in a biography is a
# wrong date or a wrong name, which is the one defect class that reads
# perfectly. What exists instead is a DIFFERENT PRINTING: the National
# Institute of Japanese Literature holds the 文化14 (1817) impression by
# Ogawa Tazaemon, against the National Archives' 文化3 (1806), and it
# runs to exactly the same 119 openings. Where the ink or the
# bleed-through fouls a character in one copy, the other settles it.
#   https://kokusho.nijl.ac.jp/biblio/100265060  (DOI 10.20730/100265060)
NIJL = ("https://kokusho.nijl.ac.jp/api/iiif/100265060/v4/ORMK/"
        "ORMK-00310/ORMK-00310-%05d.tif")
NIJL_PAGES = os.path.join(HERE, "pages_nijl")
NIJL_N = 119


def canvases(aip, expect):
    with urllib.request.urlopen(
            urllib.request.Request(MANIFEST % aip, headers=UA),
            timeout=180) as r:
        d = json.load(r)
    cs = d["sequences"][0]["canvases"]
    if len(cs) != expect:
        raise SystemExit(f"{aip}: {len(cs)} canvases, expected {expect} -- "
                         f"the archive's item changed")
    return [c["images"][0]["resource"]["service"]["@id"] for c in cs]


def get(url, path, tries=4):
    """Fetch one half-leaf, resumably and with retries.

    The archive truncates a long response often enough to matter
    (http.client.IncompleteRead partway through a 1 MB JPEG), so a
    single-shot download of 238 images will not finish. Each file is
    written only once complete, and a short file is treated as absent
    on the next run, which makes the whole fetch restartable.
    """
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return False
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA),
                    timeout=240) as r:
                data = r.read()
            if len(data) < 20000:
                raise IOError(f"short read, {len(data)} bytes")
            open(path, "wb").write(data)
            return True
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    print(f"  FAILED {os.path.basename(path)}: {type(last).__name__}",
          file=sys.stderr)
    return False


def nijl():
    """The 1817 impression, as half-leaves.

    THIS IS THE READING COPY, and the 1806 Archives scan is the check --
    the reverse of what was planned. The 1817 impression is printed on
    unbrowned paper with no show-through, and the difference is not
    cosmetic: in the 1806 copy the first word of the editorial preface
    reads 糞 and in the 1817 it is plainly 冀, "I hope that". Dung
    against hope, from one character fouled by the reverse leaf.
    """
    os.makedirs(NIJL_PAGES, exist_ok=True)
    got = 0
    for i in range(1, NIJL_N + 1):
        for side, region in (("r", "pct:50,0,50,100"),
                             ("l", "pct:0,0,50,100")):
            p = os.path.join(NIJL_PAGES, f"n{i:03d}{side}.jpg")
            if get(f"{NIJL % i}/{region}/2200,/0/default.jpg", p):
                got += 1
    print(f"NIJL 1817 impression: {got} new, "
          f"{len(os.listdir(NIJL_PAGES))} files in pages_nijl/")


def main():
    if "--nijl" in sys.argv:
        return nijl()
    os.makedirs(PAGES, exist_ok=True)
    got = 0
    for aip, vol, expect in VOLS:
        svcs = canvases(aip, expect)
        for i, svc in enumerate(svcs, 1):
            # left and right half-leaves of the opening, separately
            for side, region in (("r", "pct:50,0,50,100"),
                                 ("l", "pct:0,0,50,100")):
                p = os.path.join(PAGES, f"v{vol}_{i:03d}{side}.jpg")
                if get(f"{svc}/{region}/2200,/0/default.jpg", p):
                    got += 1
        print(f"volume {vol}: {expect} openings")
    print(f"{got} new half-leaves; {len(os.listdir(PAGES))} files in pages/")


if __name__ == "__main__":
    main()
