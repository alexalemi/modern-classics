"""Lucretius, De Rerum Natura: the Latin, with Leonard's 1916 verse as crib.

Sources, both from Perseus' canonical-latinLit on GitHub (the odyssey/
aeschylus pattern):
    phi0550.phi001.perseus-lat1.xml   the Latin, 6 books, 7,432 lines
    phi0550.phi001.perseus-eng1.xml   William Ellery Leonard's blank verse

THE ALIGNMENT IS IN THE SOURCE. Perseus divides Leonard's translation into
"cards" -- <div subtype="card" n="50"> -- and the Latin carries the SAME
cards as <milestone unit="card" n="50"/> before the line that opens each.
So every crib file is cut at exactly the Latin lines its file holds, and
the card numbers are asserted equal per book before anything is written
(the grimm rule: two witnesses that share no code with each other).

THE FORM: PROSE, the ovid/ precedent and Alex's ruling for the Odyssey.
Latin hexameter has no English equivalent that is not padding, and this
is an ARGUMENT -- 7,400 lines of physics, with a reader who wants to
follow it. What the verse carried is kept instead: the invocations and
the set-pieces (the plague at Athens, the sacrifice of Iphigenia, the
cow searching for her calf) at full imaginative weight, and the argument
's joints visible. Say so in the front matter.

Files are cut at CARD boundaries, never inside one, aiming at MAX_LATIN
words; the card is Perseus' paragraph and it is where Leonard breaks
too, so a file always opens on an argument's first sentence.
"""
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TEI = "{http://www.tei-c.org/ns/1.0}"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
RAW = ("https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/"
       "master/data/phi0550/phi001/phi0550.phi001.perseus-%s.xml")

BOOKS = ["One", "Two", "Three", "Four", "Five", "Six"]
# Descriptive titles are NEW WRITING (the augustine/burke precedent): the
# poem has no titles, and a reader has to be able to find the plague.
TITLES = {
    1: "Matter and Void",
    2: "The Movements and Shapes of Atoms",
    3: "The Mind, the Soul, and the Fear of Death",
    4: "The Senses, Sight, and Love",
    5: "The World, Its Making, and the Rise of Mankind",
    6: "Storms, Earthquakes, Magnets, and the Plague at Athens",
}
MAX_LATIN = 3300

# DERIVED ON THE FIRST RUN AND PINNED (the purgatorio rule): the poem's
# own facts, asserted against a re-fetched source.
# non-empty lines: 8 <l> in book 1, 2 in 3, 3 in 4, 1 in 5 and 6 in 6 are
# <gap>s -- lines lost in transmission -- and carry no text
LINES = {1: 1110, 2: 1178, 3: 1094, 4: 1287, 5: 1457, 6: 1286}
LATIN_WORDS = {1: 7284, 2: 7670, 3: 7410, 4: 8637, 5: 9514, 6: 8521}
TOTAL_LATIN = 49036


def fetch(kind):
    p = os.path.join(HERE, f"_src_{kind}.xml")
    if not os.path.exists(p):
        with urllib.request.urlopen(
                urllib.request.Request(RAW % kind, headers=UA), timeout=180) as r:
            open(p, "wb").write(r.read())
    return ET.parse(p).getroot()


def text_of(el):
    if el.tag.replace(TEI, "") == "note":
        return ""
    out = [el.text or ""]
    for c in el:
        out.append(text_of(c))
        out.append(c.tail or "")
    return "".join(out)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def latin_cards(book):
    """[(card n, [(line n, text)])] for one Latin book, walking in order."""
    cards, cur = [], None
    for el in book:
        t = el.tag.replace(TEI, "")
        if t == "milestone" and el.get("unit") == "card":
            cur = (el.get("n"), [])
            cards.append(cur)
        elif t == "l":
            txt = norm(text_of(el))
            if txt and cur is not None:
                cur[1].append((el.get("n"), txt))
    return cards


def english_cards(book):
    out = []
    for c in book.findall(f".//{TEI}div[@subtype='card']"):
        lines = [norm(text_of(l)) for l in c.findall(f".//{TEI}l")]
        out.append((c.get("n"), [l for l in lines if l]))
    return out


def split_cards(cards, limit=MAX_LATIN):
    """Group cards into parts of about `limit` Latin words, greedily: a
    new part starts when adding the next card would carry the running
    total past the next multiple of the target."""
    words = [sum(len(t.split()) for _, t in ls) for _, ls in cards]
    total = sum(words)
    n = max(1, round(total / limit))
    target = total / n
    parts, cur, run = [], [], 0
    for c, w in zip(cards, words):
        if cur and len(parts) < n - 1 and run + w / 2 > target * (len(parts) + 1):
            parts.append(cur)
            cur = []
        cur.append(c)
        run += w
    if cur:
        parts.append(cur)
    return parts


def render_latin(head, cards):
    body = [head, ""]
    for n, ls in cards:
        for ln, t in ls:
            body.append("\t" + t)
        body.append("")
    return "\n".join(body).rstrip() + "\n"


def render_english(head, cards):
    body = [head, ""]
    for n, ls in cards:
        body.append(f"[card {n}]")
        for t in ls:
            body.append("\t" + t)
        body.append("")
    return "\n".join(body).rstrip() + "\n"


def main():
    chap = os.path.join(HERE, "chapters")
    ref = os.path.join(HERE, "reference")
    for d in (chap, ref):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
    lat = fetch("lat1").find(f".//{TEI}body").findall(
        f".//{TEI}div[@subtype='book']")
    eng = fetch("eng1").find(f".//{TEI}body").findall(
        f".//{TEI}div[@subtype='book']")
    assert len(lat) == len(eng) == 6

    manifest, idx, total, derived = [], 0, 0, {}
    for b in range(6):
        k = b + 1
        lc = latin_cards(lat[b])
        ec = dict(english_cards(eng[b]))
        if [n for n, _ in lc] != list(ec):
            raise SystemExit(f"book {k}: card numbers differ between Latin "
                             f"and Leonard: {[n for n, _ in lc]} vs {list(ec)}")
        nl = sum(len(ls) for _, ls in lc)
        if nl != LINES[k]:
            raise SystemExit(f"book {k}: {nl} lines, pinned {LINES[k]}")
        lw = sum(len(t.split()) for _, ls in lc for _, t in ls)
        derived[k] = lw
        if LATIN_WORDS and lw != LATIN_WORDS[k]:
            raise SystemExit(f"book {k}: {lw} Latin words, pinned "
                             f"{LATIN_WORDS[k]}")
        total += lw
        parts = split_cards(lc)
        title = f"Book {BOOKS[b]}: {TITLES[k]}"
        for p, cards in enumerate(parts):
            head = title if len(parts) == 1 else \
                f"{title} (Part {p+1} of {len(parts)})"
            open(os.path.join(chap, f"{idx:03d}.txt"), "w").write(
                render_latin(head, cards))
            open(os.path.join(ref, f"{idx:03d}.txt"), "w").write(
                render_english(head + " -- Leonard's verse, crib only",
                               [(n, ec[n]) for n, _ in cards]))
            manifest.append({
                "file": f"{idx:03d}.txt", "title": title,
                "part": p + 1, "of": len(parts), "chapter": True,
                "first_line": cards[0][1][0][0],
                "last_line": cards[-1][1][-1][0],
            })
            idx += 1
    if not LATIN_WORDS:
        print("DERIVED -- pin LATIN_WORDS and TOTAL_LATIN, then re-run:",
              derived, total)
        raise SystemExit(1)
    if total != TOTAL_LATIN:
        raise SystemExit(f"total {total} Latin words, pinned {TOTAL_LATIN}")
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"),
              indent=1)
    print(f"{idx} files, {total:,} Latin words, 6 books")
    for m in manifest:
        w = len(open(os.path.join(chap, m["file"])).read().split())
        print(f"  {m['file']}  {w:>6,}  {m['title']} ({m['part']}/{m['of']}) "
              f"lines {m['first_line']}-{m['last_line']}")


if __name__ == "__main__":
    main()
