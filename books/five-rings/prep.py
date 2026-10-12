"""Miyamoto Musashi, Gorin no Sho (五輪書, 1645) -> chapters/000-004.txt.

    python3 books/five-rings/prep.py

SOURCE: 宮本武蔵遺蹟顕彰会 編『宮本武蔵』(金港堂書籍, 明治42 = 1909),
NDL Digital Collections pid 992019, Access Restriction PDM, chapter 9
(五輪書), frames 97-141. The book prints the text from the copy then held
by the Maeda family of Tamana, Higo; every scroll ends on the transmission
colophon Musashi -> Terao Magonojō (1645) -> Terao Yumeyo Katsunobu ->
Yamamoto Gensuke (1667).

TEXT LAYER: the NDL Lab full-text OCR of the same scan
(lab.ndl.go.jp/dl/api/book/fulltext-json/992019, saved in source/),
proved against the page images: frame 103 right page agreed character for
character, frame 117 likewise in every column read. Its only systematic
defect is 〓 for glyphs the OCR font lacks: a PAIR is the two-column
kunoji repeat mark (〳〵), a single is almost always 敎 (教); the others
are fixed by name in SINGLE_FIX below after reading the image.

Layout: running heads and the side titles sit above y=650 or are
single-character blocks, page numbers are bare kanji numerals; both are
dropped. A frame is a two-page spread, right page first, columns right to
left. An article head (一 ...) is its own short block at the top of a
column and becomes its own paragraph.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
FT = json.loads((HERE / "source/ndl_992019_fulltext.json").read_text())["list"]
PAGES = {x["page"]: x for x in FT}
FIRST, LAST = 97, 141
MID = 1850                          # x splitting the right page from the left
NUMERAL = re.compile(r"^[一二三四五六七八九〇十]{1,4}$")
TITLES = {"地の卷": 0, "水の卷": 1, "火の卷": 2, "風之卷": 3, "空の卷": 4}

# Single 〓 that are not 敎, each read off the page image.
SINGLE_FIX = [
    ("水に碧潭の色有り、〓き所", "水に碧潭の色有り、清き所"),   # f102
    ("刀のきれざる時な〓", "刀のきれざる時など"),            # f117, image
    ("おさへ ん\n〓とする", "おさへんおさへんとする"),         # f123: repeat mark split over a column
]

# Article heads the OCR misread, fused into the running text or dropped;
# each checked against the page image (or, where the head survives in
# the text, by its own wording). (text to find, head it starts)
HEAD_FIX = [
    ("師ははり、弟子は糸と成て、たえず稽古有るべき事也、一兵法の道大工にたとへたる事",
     "一兵法の道大工にたとへたる事"),                         # f100: head fused into text
    ("一ををささるると云事", "一枕をおさふると云事"),             # f122 image
    ("吟味有べし、多敵の位と云ふは", "一多敵の位の事"),           # f118 image: head block dropped
    ("一兵法に武具の利を知ると云事", "一兵法に武具の利を知ると云事"),
    ("おもての第二の次第の事", "一おもての第二の次第の事"),
    ("ナかげをおさふると云事", "一かげをおさふると云事"),
    ("吟味有べき也、おびやかすと云事", "一おびやかすと云事"),
    ("一さんかいのかわりと云事、", "一さんかいのかわりと云事"),
    ("一他流に於てつよみの太刀と云事", "一他流に於てつよみの太刀と云事"),
]


def blocks(p):
    bl = json.loads(PAGES[p]["coordjson"])
    keep, seen = [], set()
    for b in bl:
        t = b["contenttext"].strip()
        key = (t, round(b["xmin"] / 50), round(b["ymin"] / 50))
        if key in seen:                 # the OCR emits some colophon blocks twice
            continue
        seen.add(key)
        # single characters below the running head are kept: Musashi's
        # signature is set letter-spaced (新 免 武 藏) and 口傳 is set small
        if b["ymin"] < 650 or t in ("-", "") or NUMERAL.match(t):
            continue
        keep.append(b)
    # cluster into columns by centre x (a head and the body that follows
    # it in the same column differ by a few px, enough to split a rounding
    # bucket), then read columns right to left, each top to bottom
    cols = []
    for b in sorted(keep, key=lambda b: -(b["xmin"] + b["xmax"])):
        c = (b["xmin"] + b["xmax"]) / 2
        if cols and abs(cols[-1][0] - c) < 50:
            cols[-1][1].append(b)
        else:
            cols.append([c, [b]])
    cols.sort(key=lambda c: (0 if c[0] > MID else 1, -c[0]))
    return [b for _, bs in cols for b in sorted(bs, key=lambda b: b["ymin"])]


lines = []
for p in range(FIRST, LAST + 1):
    for b in blocks(p):
        t = b["contenttext"].strip().replace(" ", "")
        if t in TITLES:
            lines.append(("TITLE", t))
        elif t.startswith("一") and b["ymax"] < 1700 and len(t) < 30:
            lines.append(("HEAD", t))
        else:
            lines.append(("TEXT", t))

# paragraphs: text runs broken at heads and titles
paras, cur = [], ""
for kind, t in lines:
    if kind == "TEXT":
        cur += t
        continue
    if cur:
        paras.append(("TEXT", cur))
        cur = ""
    paras.append((kind, t))
if cur:
    paras.append(("TEXT", cur))

text = "\n".join(f"@{k}@{t}" for k, t in paras)
for a, b in SINGLE_FIX:
    a2 = a.replace(" ", "").replace("\n", "")
    assert a2 in text or a in text, a
    text = text.replace(a2, b).replace(a, b)
text = text.replace("〓〓", "〳〵").replace("〓", "敎")
for find, head in HEAD_FIX:
    assert text.count(find) == 1, find
    if find.startswith("一") and ("\n@HEAD@" + find) in text:
        text = text.replace("\n@HEAD@" + find, "\n@HEAD@" + head)
        continue
    if find.endswith(head) and not find.startswith("一"):
        text = text.replace(find, find[:-len(head)] + "\n@HEAD@" + head + "\n@TEXT@")
        continue
    pre = find[:find.index(head[1:3])] if not find.startswith("一") and head[1:3] in find else ""
    rest = find[len(pre):]
    if rest.startswith("ナ") or rest.startswith("一ををさ"):
        rest = rest[1:] if rest.startswith("ナ") else ""
    body = rest
    if body.startswith(head):
        body = body[len(head):]
    elif body.startswith(head[1:]):
        body = body[len(head) - 1:]
    text = text.replace(find, pre + "\n@HEAD@" + head + "\n@TEXT@" + body)

# debris the head repairs leave: a stray kana before one head, a comma after another
text = text.replace("能々吟味有べし、ナ\n", "能々吟味有べし、\n")
text = text.replace("\n@TEXT@、山海の心", "\n@TEXT@山海の心")

# drop the 1909 editors' introduction: Musashi begins at 兵法の道
start = text.index("兵法の道二天一流と號し")
head = text[:start].rsplit("\n", 1)[0]
text = "@TEXT@" + text[start:]

files = {0: []}
cur = 0
for line in text.split("\n"):
    k, t = line[1:].split("@", 1)
    if k == "TITLE":
        cur = TITLES[t]
        files.setdefault(cur, [])
        if cur == 0:
            files[0].append("◇地の卷")      # the preface ends, the Earth scroll proper begins
        continue
    # 1909 prints the head, then the body opens by repeating it; keep both
    files[cur].append(t if k != "HEAD" else "◆" + t)

NAMES = ["The Earth Scroll", "The Water Scroll", "The Fire Scroll",
         "The Wind Scroll", "The Void Scroll"]
(HERE / "chapters").mkdir(exist_ok=True)
manifest = []
reading = []
for i in range(5):
    paras_i = [p for p in files[i] if p]
    reading.append(NAMES[i] + "\n\n" + "\n\n".join(paras_i))
    # chapters/ holds each scroll as ONE unbroken line, the way the
    # manuscript runs: an article opens on its head in 【】, there is no
    # whitespace anywhere. verify.py counts len(text.split()), which on
    # Japanese is a count of paragraphs, not words; with no whitespace
    # its ratio is honestly "not checked" rather than a false number.
    # The real ratio (source characters -> English words) is check.py's.
    body = "".join(("【" + p[1:] + "】") if p.startswith(("◆", "◇")) else p
                   for p in paras_i)
    assert not re.search(r"\s", body)
    fn = f"{i:03d}.txt"
    (HERE / "chapters" / fn).write_text(body + "\n")
    n = len(re.findall(r"[㐀-鿿぀-ヿ]", body))
    manifest.append({"file": fn, "title": NAMES[i], "part": 1, "of": 1,
                     "chars": n})
    print(fn, NAMES[i], n, "chars,", body.count("【一"), "articles")
(HERE / "source/gorin_paragraphed.txt").write_text("\n\n\n".join(reading) + "\n")
(HERE / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
