"""Dogen: the practice writings, from the original kanbun.

SOURCE. Japanese Wikisource, which transcribes and proofreads (to 100%)
two of Dogen's works from EIHEIJI'S OWN COLLECTED EDITION:

    承陽大師聖教全集 (Joyo Daishi Shogyo Zenshu), Eiheiji, 1909
    NDL Digital Collections pid 823139 (vol 1), 823141 (vol 3)
    Access Restriction: PDM -- public domain mark, no restriction

    普勸坐禪儀  Fukanzazengi        vol 1, ~1,000 characters
    學道用心集  Gakudo Yojinshu     vol 3, ~4,500 characters, 10 sections

THERE IS NO PUBLIC-DOMAIN ENGLISH DOGEN, AND THAT IS THE CENTRAL FACT
ABOUT THIS BOOK. Every other from-the-original volume in this collection
carries a crib -- Murray for Homer, Riley for Ovid, Longfellow for
Dante, Jebb for Sophocles, Symonds for Cellini -- and that crib is the
SECOND WITNESS the whole method depends on. Every English Dogen
(Nishijima & Cross, Tanahashi, Waddell & Abe, Cleary, Kim) is in
copyright, and searches of Gutenberg, Archive.org and Wikisource return
nothing. So reference/ is empty by necessity, not by oversight, and the
front matter says so.
What partly replaces it: the source is short enough to work phrase by
phrase, and its famous cruxes (身心脱落, 非思量, 只管打坐, 本來面目)
have settled English renderings to check against.

THE TEXT IS KANBUN -- classical Chinese written by a Japanese author --
not Japanese. 「原夫。道本圓通、爭假修證。」 is Chinese syntax. This is
the first from-the-Chinese volume in the collection; sun-tzu/ modernises
Giles's English precisely because it is not one.

A WORD RATIO CANNOT FIRE ON THIS BOOK, and an inert check that looks
like coverage is worse than no check at all (the nights lesson). CJK
text has no spaces, so `len(text.split())` returns approximately 1 for a
whole chapter and verify.py's ratio -- the one mechanical guard against
silent summarising -- would be meaningless. check.py therefore measures
CHARACTERS of source against WORDS of translation, and verify.py is run
with bounds wide enough to be honest about being uninformative.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
API = "https://ja.wikisource.org/w/api.php"

WORKS = [
    ("普勸坐禪儀", "Fukanzazengi",
     "Universal Recommendation for Zazen", "1227",
     "vol 1, NDL pid 823139"),
    ("學道用心集", "Gakudo Yojinshu",
     "Points to Watch in Studying the Way", "1234",
     "vol 3, NDL pid 823141"),
]

# Characters per work, DERIVED THEN PINNED as a regression guard. The
# load-bearing witness is not this table but the 1909 page images, which
# are served by NDL under PDM and were read against the transcription
# for the Gakudo Yojinshu's opening sections: they agree character for
# character, which is what makes the Wikisource text trustworthy here.
CHARS = {"普勸坐禪儀": 894, "學道用心集": 4342}

SECTION = re.compile(r"^\s*第[一二三四五六七八九十]+\s")


def parse(title):
    u = API + "?" + urllib.parse.urlencode(
        {"action": "parse", "prop": "text", "format": "json", "page": title})
    with urllib.request.urlopen(
            urllib.request.Request(u, headers=UA), timeout=120) as r:
        d = json.load(r)
    return d["parse"]["text"]["*"]


def clean(html):
    """Wikisource's rendered page down to the text of the work itself.

    The page is a transclusion wrapper: a {{header}} table naming the
    1909 底本, then the transcluded Page: namespace content. Both the
    header and the category/navigation furniture have to go, and they
    are removed as ELEMENTS -- a naive tag strip welds the bibliographic
    note onto the first line of the work (the bunyan noteref trap).
    """
    html = re.sub(r"<table.*?</table>", "", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", html, flags=re.S)
    html = re.sub(r'<div class="[^"]*(?:navigation|catlinks|printfooter)'
                  r'[^"]*">.*?</div>', "", html, flags=re.S)
    html = re.sub(r"<[^>]+>", "\n", html)
    txt = re.sub(r"&#160;|&nbsp;", " ", html)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"&#\d+;|&[a-z]+;", "", txt)
    lines = [l.strip() for l in txt.split("\n")]
    out = []
    for l in lines:
        if not l:
            continue
        if l.startswith(("書誌情報", "底本", "この著作物は", "作者：")):
            continue
        if re.match(r"^(カテゴリ|Category|原文|関連|脚注)", l):
            continue
        out.append(l)
    return out


def body(title):
    """The work's own lines, with the title line and colophon dropped."""
    lines = clean(parse(title))
    # CUT ON THE BIBLIOGRAPHIC ANCHOR, NOT ON LINE SHAPES. The rendered
    # page opens with a {{header}} block -- title, author, 底本, and the
    # NDL persistent identifier -- and the work begins after it. Slicing
    # on the identifier is exact and it FAILS LOUDLY if Wikisource ever
    # restructures the page, where a shape-based filter would silently
    # leave a line of catalogue furniture at the head of the text (or,
    # worse, eat Dogen's first line).
    anchor = [i for i, l in enumerate(lines) if "info:ndljp" in l]
    if len(anchor) != 1:
        raise SystemExit(f"{title}: expected exactly one NDL identifier "
                         f"line in the header, found {len(anchor)}")
    lines = lines[anchor[0] + 1:]
    while lines and (lines[0] == title or lines[0] == "道元"
                     or lines[0] in (":", "-", "*")):
        lines.pop(0)
    while lines and (lines[-1] in ("終",) or lines[-1].endswith("終")
                     or re.match(r"^\[?\d+\]?$", lines[-1])):
        lines.pop()
    return lines


def chars(lines):
    return sum(1 for l in lines for c in l if not c.isspace())


def main():
    chap = os.path.join(HERE, "chapters")
    os.makedirs(chap, exist_ok=True)
    for f in os.listdir(chap):
        os.remove(os.path.join(chap, f))

    manifest, idx = [], 0
    for title, roman, english, date, where in WORKS:
        lines = body(title)
        n = chars(lines)
        if n != CHARS[title]:
            raise SystemExit(
                f"{title}: {n} characters, pinned {CHARS[title]} -- the "
                f"Wikisource transcription changed; re-read it against the "
                f"1909 scan ({where}) before adjusting the pin")
        text = "\n\n".join([roman] + lines) + "\n"
        open(os.path.join(chap, f"{idx:03d}.txt"), "w").write(text)
        manifest.append({
            "file": f"{idx:03d}.txt",
            "title": roman,
            "part": 1, "of": 1, "chapter": True,
            "part_before": f"{roman} — {english} ({date})",
        })
        idx += 1
        print(f"  {idx-1:03d}.txt  {n:>6,} chars  {roman} ({english})")

    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"{idx} files, {sum(CHARS.values()):,} characters of kanbun")


if __name__ == "__main__":
    main()
