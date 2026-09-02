"""Fetch pages of NDL volume 3 of the 1909 Eiheiji collected Dogen.

承陽大師聖教全集 第三巻, NDL Digital Collections pid 823141, Access
Restriction PDM, 306 openings. The volume carries, after the Gakudo
Yojinshu already published in this book:

    寶慶記      Hokyoki      -- Dogen's record of what he asked Rujing
                               in China and what Rujing answered
    傘松道詠    Sansho Doei  -- his waka
    正法眼藏隨聞記 Zuimonki   -- 142 pages, too large for an extension
    光明藏三昧, 曹洞教會修證義

THE HOKYOKI IS THE RIGHT EXTENSION and not merely the convenient one.
The volume as published is two sets of instructions -- how to sit and
how to study -- and the Hokyoki is the record of Dogen being taught
both, question by question, by the teacher he crossed the sea to find.
It also supplies what dogen/ conspicuously lacks: Rujing's own voice.

Legibility of this exact volume was proved when the Gakudo Yojinshu was
published: a page image was read directly against the Wikisource
transcription and they agreed character for character.
"""
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
SVC = "https://dl.ndl.go.jp/api/iiif/823141/R%07d"
PAGES = os.path.join(HERE, "pages_v3")


def get(url, path, tries=4):
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return False
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA),
                    timeout=240) as r:
                data = r.read()
            if len(data) < 20000:
                raise IOError(f"short read {len(data)}")
            open(path, "wb").write(data)
            return True
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    print(f"  FAILED {os.path.basename(path)}: {last}", file=sys.stderr)
    return False


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    os.makedirs(PAGES, exist_ok=True)
    n = 0
    for i in range(lo, hi + 1):
        # each opening is two half-leaves; the 1909 book is printed
        # western-style two columns per image, so take it whole
        p = os.path.join(PAGES, f"p{i:03d}.jpg")
        if get(f"{SVC % i}/full/2000,/0/default.jpg", p):
            n += 1
    print(f"{n} new; {len(os.listdir(PAGES))} files in pages_v3/")


if __name__ == "__main__":
    main()
