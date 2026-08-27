#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare Homer's Odyssey from the Greek.

SOURCE, and it is a better arrangement than the Divine Comedy had.  Both
the Greek and the crib come from Perseus' `canonical-greekLit` on GitHub,
in the SAME TEI markup, so ONE parser reads both:

    tlg0012.tlg002.perseus-grc2.xml   the Greek of the 1919 Loeb (Allen)
    tlg0012.tlg002.perseus-eng3.xml   A. T. Murray's 1919 Loeb English

Murray's prose carries <milestone unit="line"> anchors throughout -- 2,434
of them, about one every five verses -- so the crib SELF-ALIGNS to the
Greek line numbers.  That is what `reference/` is built out of, and it is
why no Butler (Gutenberg #1727) is needed: Butler's prose has no anchors
at all and would have to be aligned by eye.

LICENCE.  Murray's 1919 text is public domain by age; Perseus' MARKUP is
CC BY-SA 4.0 and Tufts asserts copyright over the digital library.  The
retelling is new writing and is unaffected, but this book therefore ships
NO "original text" companion page -- unlike the Royal Institution volumes
and like the three cantiche of the Comedy.  Do not add one.

THE LINE COUNT DOES NOT MATCH THE CANONICAL ONE AND THAT IS NOT A BUG.
Allen's text gives 12,107 lines where the figure usually quoted is 12,110.
The difference is athetized lines that this edition does not print.  It is
asserted below against the per-book table so that a FUTURE change in the
source cannot pass silently -- the point of the grimm rule is that a
source compared only against itself agrees with itself, so the table is
the second witness, and the crib is the third.

THE POEM IS BEING RETOLD AS PROSE (Alex's ruling), which costs the check
that mattered most in the Comedy: exact line parity.  What replaces it is
in check.py and comes free out of this same markup -- Perseus tags all
674 speeches as <q>, so speech parity per book is exact and mechanical.
prep.py therefore writes a speeches.json alongside the chapters, which is
the only thing check.py trusts.  See check.py's docstring for why the
fleming numeric diff is NOT among the checks: the Greek body contains
ZERO digit tokens, so it could never fire.
"""

import collections
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TEI = "{http://www.tei-c.org/ns/1.0}"

RAW = ("https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/"
       "master/data/tlg0012/tlg002/tlg0012.tlg002.perseus-%s.xml")
GRC = os.path.join(HERE, "_perseus_grc2.xml")
ENG = os.path.join(HERE, "_perseus_eng3.xml")

# Lines per book in Allen's text.  Written out so the parse has a witness
# that shares no code with it.
LINES = [444, 434, 497, 847, 493, 331, 347, 586, 566, 573, 640, 453,
         440, 533, 557, 480, 606, 428, 604, 394, 434, 501, 371, 548]
TOTAL_LINES = 12107
BOOKS = 24

# Speeches per book, tagged <q> by Perseus.  Same role as LINES: a second
# witness, and the thing check.py holds the translation to.
SPEECHES = [20, 21, 20, 50, 20, 12, 15, 33, 20, 30, 31, 16,
            24, 20, 38, 34, 52, 33, 37, 28, 26, 37, 23, 34]
TOTAL_SPEECHES = 674

# An English file over ~7k words is more than a translation agent can
# emit in one go, and English runs about 1.5x the Greek here (Murray:
# 133,145 English words against 87,181 Greek).  So cut a book whose Greek
# exceeds this, at a SPEECH BOUNDARY -- never inside a speech, because a
# speech split across two files is exactly the seam the check exists to
# catch.
MAX_GREEK_WORDS = 4500

# THREE TRANSCRIPTION SLIPS IN PERSEUS' ENGLISH, none of which touches the
# Greek.  They matter because a wrong anchor sends a translator to the
# wrong place in the crib, and a crib silently off by one reads perfectly
# -- the defect cellini/ hit when Symonds ran two chapters together.
#
# Keyed by (book, position of the anchor in that book's sequence) rather
# than by value, because book 6's bad anchor is a DUPLICATE and a value
# key could not say which of the two to correct.  Each is asserted, so a
# corrected source will stop the build rather than pass silently.
#
#   (book, index): (wrong, right, why)
ANCHOR_FIXES = {
    (6, 65): (320, 325, "duplicate: the run is 315, 320, 320, 330"),
    (16, 56): (580, 280, "digit slip: sits between 275 and 285"),
}
# Book 4 skips from 140 to 150 -- an anchor simply absent rather than
# wrong.  Harmless (it points nowhere false), and recorded here so that
# nobody 'fixes' it later by inventing a 145 the source does not have.
KNOWN_GAPS = {(4, 145)}

WORD = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen "
        "Twenty Twenty-One Twenty-Two Twenty-Three Twenty-Four").split()


def fetch():
    for kind, path in (("grc2", GRC), ("eng3", ENG)):
        if os.path.exists(path):
            continue
        sys.stderr.write("fetching %s\n" % kind)
        with urllib.request.urlopen(RAW % kind) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)


def books_of(root, subtype="book"):
    """The 24 book divs.

    NO FALLBACK ON PURPOSE.  An earlier version matched subtype "Book"
    (capitalised, which is wrong -- both files use "book") and fell back
    to type="textpart" when that found nothing.  It returned the right
    divs here by luck; in the ENGLISH file the same fallback would have
    returned 312, because Perseus also divides that text into 288
    "card" divs of the same type.  A fallback that can silently pick a
    different level of the tree is how a parser agrees with itself and
    with nothing else.
    """
    body = root.find(".//%sbody" % TEI)
    out = [d for d in body.iter(TEI + "div") if d.get("subtype") == subtype]
    assert len(out) == BOOKS, (
        "expected %d divs with subtype=%r, found %d -- the source's "
        "structure has changed; look at it rather than loosening this"
        % (BOOKS, subtype, len(out)))
    return out


def flat(el):
    return re.sub(r"\s+", " ", " ".join(el.itertext())).strip()


def greek_books():
    """[(book_no, [(line_no, text, speech_id_or_None, depth), ...]), ...]

    Perseus tags every speech <q>, and they nest exactly one level: 570
    speeches at the top and 104 inside another (Odysseus quoting Circe
    inside his own tale to the Phaeacians, and so on).  Depth is recorded
    per line because it decides the QUOTE MARK the translation uses --
    double for a speech, single for a speech inside one -- and therefore
    what check.py can count.
    """
    root = ET.parse(GRC).getroot()
    out = []
    for bk in books_of(root):
        owner, depth_of = {}, {}
        seq = [0]

        def walk(el, d):
            for ch in el:
                if ch.tag == TEI + "q":
                    sid = seq[0]
                    seq[0] += 1
                    for l in ch.findall(".//%sl" % TEI):
                        # innermost speech wins: a line inside a nested
                        # speech belongs to that one, not to its container
                        if id(l) not in owner or d + 1 > depth_of[id(l)]:
                            owner[id(l)] = sid
                            depth_of[id(l)] = d + 1
                    walk(ch, d + 1)
                else:
                    walk(ch, d)

        walk(bk, 0)
        lines = []
        for l in bk.findall(".//%sl" % TEI):
            lines.append((l.get("n"), flat(l),
                          owner.get(id(l)), depth_of.get(id(l), 0)))
        out.append((int(bk.get("n")), lines))
    return out


def murray_books():
    """{book_no: prose with [line N] anchors}, anchors repaired."""
    root = ET.parse(ENG).getroot()
    out = {}
    for bk in books_of(root):
        bno = int(bk.get("n"))
        seen = [0]                     # anchor counter, for ANCHOR_FIXES
        chunks = []
        for p in bk.iter(TEI + "p"):
            buf = []
            if p.text:
                buf.append(p.text)
            for child in p:
                tag = child.tag.replace(TEI, "")
                if tag == "milestone" and child.get("unit") == "line":
                    n = int(child.get("n"))
                    fix = ANCHOR_FIXES.get((bno, seen[0]))
                    if fix:
                        wrong, right, _why = fix
                        assert n == wrong, (
                            "book %d anchor %d: expected the known bad value "
                            "%d, found %d -- the source has changed, so "
                            "re-derive the fix rather than moving it"
                            % (bno, seen[0], wrong, n))
                        n = right
                    buf.append(" [line %d] " % n)
                    seen[0] += 1
                elif tag == "note":
                    pass                       # editor's notes are not Homer
                else:
                    buf.append(" ".join(child.itertext()))
                if child.tail:
                    buf.append(child.tail)
            chunks.append(re.sub(r"\s+", " ", "".join(buf)).strip())
        out[bno] = "\n\n".join(c for c in chunks if c)
    return out


def cut_points(lines, budget):
    """Indices at which to start a new part, never inside a speech."""
    cuts, run = [], 0
    for i, (_, text, spk, _d) in enumerate(lines):
        n = len(text.split())
        if run + n > budget and spk is None and i:
            cuts.append(i)
            run = 0
        run += n
    return cuts


def speech_shape(chunk):
    """(outer, inner) speech counts for a run of lines."""
    seen = {}
    for _n, _t, sid, d in chunk:
        if sid is not None:
            seen[sid] = d
    return (sum(1 for d in seen.values() if d == 1),
            sum(1 for d in seen.values() if d == 2))


def main():
    fetch()

    grc = greek_books()
    assert len(grc) == BOOKS, len(grc)
    counts = [len(l) for _, l in grc]
    assert counts == LINES, (
        "line table disagrees with the source: %r" % (counts,))
    assert sum(counts) == TOTAL_LINES, sum(counts)

    eng = murray_books()
    assert sorted(eng) == list(range(1, BOOKS + 1)), sorted(eng)
    # the crib is the third witness: every book it carries must be one the
    # Greek also has, and its last line anchor must fall inside the book.
    gaps = set()
    for n, prose in eng.items():
        anchors = [int(m) for m in re.findall(r"\[line (\d+)\]", prose)]
        assert anchors, "book %d: crib carries no line anchors" % n
        assert anchors[0] == 1, (n, anchors[0])
        assert anchors == sorted(set(anchors)), (
            "book %d: crib anchors are not strictly increasing -- %r"
            % (n, [(i, anchors[i - 1], anchors[i])
                   for i in range(1, len(anchors))
                   if anchors[i] <= anchors[i - 1]]))
        assert all(a % 5 == 0 for a in anchors[1:]), n
        assert max(anchors) <= LINES[n - 1], (
            "book %d: crib anchors line %d but the book has %d"
            % (n, max(anchors), LINES[n - 1]))
        # anchors run 1, 5, 10, 15, ... so the opening step is 4 by design
        for i in range(2, len(anchors)):
            if anchors[i] - anchors[i - 1] != 5:
                gaps.add((n, anchors[i - 1] + 5))
    assert gaps == KNOWN_GAPS, (
        "crib anchor gaps changed: %r (expected %r)" % (gaps, KNOWN_GAPS))

    for d in ("chapters", "reference", "modern_chapters"):
        p = os.path.join(HERE, d)
        if not os.path.isdir(p):
            os.makedirs(p)

    manifest, idx, speeches_out = [], 0, {}
    spoken_total = 0
    for bno, lines in grc:
        nspeech = len(set(s for _, _, s, _d in lines if s is not None))
        assert nspeech == SPEECHES[bno - 1], (
            "book %d: %d speeches, table says %d"
            % (bno, nspeech, SPEECHES[bno - 1]))
        spoken_total += nspeech

        cuts = cut_points(lines, MAX_GREEK_WORDS)
        bounds = [0] + cuts + [len(lines)]
        nparts = len(bounds) - 1
        for part in range(nparts):
            lo, hi = bounds[part], bounds[part + 1]
            chunk = lines[lo:hi]
            name = "%03d.txt" % idx
            title = "Book %s" % WORD[bno - 1]
            head = title if nparts == 1 else "%s (Part %d of %d)" % (
                title, part + 1, nparts)
            body = "\n".join(t for _, t, _s, _d in chunk)
            with open(os.path.join(HERE, "chapters", name), "w") as f:
                f.write(head + "\n\n" + body + "\n")
            outer, inner = speech_shape(chunk)
            manifest.append({
                "file": name,
                "title": title,
                "part": part + 1,
                "of": nparts,
                "chapter": True,
                "words": sum(len(t.split()) for _, t, _s, _d in chunk),
                "book": bno,
                "lines": [chunk[0][0], chunk[-1][0]],
                "speeches": outer + inner,
            })
            speeches_out[name] = {"outer": outer, "inner": inner}
            idx += 1

        with open(os.path.join(HERE, "reference", "%02d.txt" % bno),
                  "w") as f:
            f.write("Book %s -- A. T. Murray, Loeb 1919 (crib only)\n\n"
                    % WORD[bno - 1])
            f.write(eng[bno] + "\n")

    assert spoken_total == TOTAL_SPEECHES, spoken_total

    with open(os.path.join(HERE, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(HERE, "speeches.json"), "w") as f:
        json.dump(speeches_out, f, indent=1)
        f.write("\n")

    gw = sum(m["words"] for m in manifest)
    multi = [m for m in manifest if m["of"] > 1]
    outer = sum(v["outer"] for v in speeches_out.values())
    inner = sum(v["inner"] for v in speeches_out.values())
    assert (outer, inner) == (570, 104), (outer, inner)
    print("%d books -> %d files, %d Greek words, %d speeches "
          "(%d spoken, %d quoted inside another)"
          % (BOOKS, len(manifest), gw, spoken_total, outer, inner))
    print("largest file: %d Greek words (~%d English)"
          % (max(m["words"] for m in manifest),
             int(max(m["words"] for m in manifest) * 1.53)))
    print("split books: %s" % (sorted(set(m["book"] for m in multi)) or "none"))


if __name__ == "__main__":
    main()
