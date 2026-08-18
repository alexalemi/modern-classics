#!/usr/bin/env python3
"""Boethius, The Consolation of Philosophy -> chapters/ + manifest.json

    ./fetch.sh && python3 boethius/prep.py

Source: Standard Ebooks' H. R. James (1897), the same proofread-XHTML
pipeline as bunyan/, autobiography/, epictetus/ and hume/.

WHY THIS BOOK. It is the only candidate in the 2026-08-17 screening
that scores high on BOTH axes: archaism 23.7 AND calque 22.9. Every
other candidate is a one-axis case. Written in 524 while Boethius was
in prison awaiting execution for treason, it was the scholar's familiar
book for a thousand years and was translated into English by Alfred the
Great, Chaucer and Elizabeth I.

THE STRUCTURE IS A PROSIMETRUM, and that is new to this project. Prose
argument alternates with thirty-nine verse metra, and every prose
chapter but the last carries one. Book Five chapter VI ends the work on
prose: the great argument that God's foreseeing is a seeing, and that
it imposes no necessity. Elsewhere verse has been an occasional
indented block; here it is half the architecture.

FOUR THINGS THE STRUCTURE HIDES, all of them found by looking rather
than by assuming, and all of them of the class verify.py cannot see:

  1 SONG I IS NOT IN A CHAPTER FILE. It is Boethius' opening lament,
    and it lives in book-1.xhtml, after that book's argument, wrapped
    in a <blockquote> where every other song uses a bare <p>. A prep
    that walked chapter-*.xhtml only -- the obvious thing to write --
    would have dropped the first poem of the work silently, and the
    word ratio would not have moved enough to notice. THE BOOK'S OWN
    ARGUMENT NAMES IT, which is how it was caught.

  2 EACH BOOK CARRIES AN ARGUMENT (an se:bridgehead) summarising every
    chapter and naming every song. This is the independent description
    of the book that the pipeline did not produce -- the grimm witness.
    It is NOT published: it is chapter-by-chapter plot summary of a
    philosophical dialogue, which is a spoiler and a crutch, and it is
    James's writing and not Boethius'. It is used instead to CHECK the
    census, and to write the chapter titles from.

  3 THE SONGS ARE NUMBERED INDEPENDENTLY OF THE PROSE, and offset from
    it: Book One chapter I carries Song II. Both numbers are kept.

  4 A NOTEREF IS AN ELEMENT, NOT A TAG. Strip tags naively and the
    anchor's digit welds onto the preceding word -- the source's own
    song title comes out as "A Psychological Fallacy34", and the
    argument ends "the whole universe tends.11". That is the bunyan
    trap, and it passes every mechanical check this project has.

CHAPTER TITLES ARE NEW WRITING, on the augustine and soap-bubbles
precedent: the source heads each chapter with a lone Roman numeral.
They are written from each book's own argument, so they describe what
the chapter actually does rather than guessing.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"

X = "{http://www.w3.org/1999/xhtml}"
EPUB = "{http://www.idpf.org/2007/ops}type"

# chapters per book, asserted against the files on disk
COUNTS = {1: 6, 2: 8, 3: 12, 4: 7, 5: 6}

BOOK_TITLES = {
    1: "The Sorrows of Boethius",
    2: "The Vanity of Fortune's Gifts",
    3: "True Happiness and False",
    4: "Good and Ill Fortune",
    5: "Free Will and God's Foreknowledge",
}

# Written from each book's own argument. One per prose chapter, in order.
TITLES = {
    1: ["Philosophy Appears and Drives Out the Muses",
        "Boethius Struck Dumb",
        "Boethius Recognises Philosophy",
        "The Story of His Ruin",
        "The Sickness Is in His Mind, Not His Fortune",
        "The Three Things He Has Forgotten"],
    2: ["Fortune's Nature Is Caprice",
        "Fortune Speaks in Her Own Defence",
        "How Brilliant His Fortunes Once Were",
        "Happiness Is Not Anywhere Outside You",
        "Riches Bring Anxiety, Not Contentment",
        "High Office Without Virtue",
        "Fame Against the Size of the Universe",
        "The One Service Bad Fortune Does"],
    3: ["The Promise to Lead Him to True Happiness",
        "The Five Things People Mistake for Happiness",
        "Riches Only Add to What You Want",
        "High Position Cannot Command Respect",
        "Sovereignty Cannot Even Buy Safety",
        "Fame, and the Splendour That Is Somebody Else's",
        "Pleasure Begins in Restlessness and Ends in Regret",
        "All Five Fail, and Each Brings Its Own Harm",
        "The Error Is Breaking the One Good into Pieces",
        "That Happiness Exists, and That It Is God",
        "Everything Alive Wants to Stay One, and Unity Is Good",
        "Goodness Governs the World, and the Paradox of Evil"],
    4: ["Why the Wicked Prosper",
        "The Good Alone Have Power",
        "Reward and Punishment Are Never Absent",
        "The Wicked Are Unhappier When They Succeed",
        "Why the Distribution Looks Like Chance",
        "Fate and Providence",
        "All Fortune Is Good Fortune"],
    5: ["Is There Any Such Thing as Chance?",
        "Whether a Human Being Is Free",
        "The Problem: Foreknowledge Seems to Destroy Freedom",
        "Knowledge Depends on the Knower, Not the Thing Known",
        "Rising from Reason to a Higher Standpoint",
        "Eternity, and Why Foreseeing Does Not Compel"],
}


def clean(t):
    for a, b in [(" ", " "), (" ", " "), ("﻿", ""),
                 ("⁠", "")]:
        t = t.replace(a, b)
    return t


def strip_noterefs(root):
    """Remove noteref anchors as ELEMENTS, each tail going to its own
    PREDECESSOR. Appending to the parent's last child instead relocates
    text, which is how a clause moved in epictetus/; and stripping the
    tag rather than the element welds the digit onto the previous word,
    which is how bunyan/ got "the Slough of Despond,41 his labourers"."""
    for parent in root.iter():
        i = 0
        while i < len(parent):
            el = parent[i]
            if el.tag == X + "a" and el.get(EPUB) == "noteref":
                tail = el.tail or ""
                del parent[i]
                if i:
                    parent[i - 1].tail = (parent[i - 1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
            else:
                i += 1


def load(name):
    root = ET.fromstring(clean((SRC / name).read_text()))
    strip_noterefs(root)
    return root.find(f"{X}body")


def text_of(el):
    """Element text with <em> carried through as *markers* (hume/)."""
    out = [el.text or ""]
    for child in el:
        inner = text_of(child)
        if child.tag == X + "em" and inner.strip():
            out.append(f"*{inner.strip()}*")
        else:
            out.append(inner)
        out.append(child.tail or "")
    return "".join(out)


def para(el):
    return re.sub(r"\s+", " ", text_of(el)).strip()


def find(el, path):
    return el.find(path, {"epub": "http://www.idpf.org/2007/ops"})


def song_of(sec):
    """(label, title, [lines]) for a song section, or None.

    THE LINES ARE ONE BLOCK. Every line gets a leading tab so the whole
    run renders as a single <pre>; the source's class="i1" lines, which
    mark the shorter line of each couplet, get one further level so the
    metre survives. The fleming rule: group the run, and never strip
    per line, or the rows slide out of register.

    A SONG IS IDENTIFIED BY ITS LABEL, NOT BY ITS SHAPE AND NOT BY ITS
    TYPE, and both of the obvious rules are wrong:

      BY SHAPE — with no test at all, the function happily renders a
      PROSE body as verse, every paragraph becoming a tab-indented
      line. The word-sequence cross-check CANNOT SEE THIS, because the
      words are the same words in the same order either way. Only the
      structural census (39 songs) catches it. A second reading of the
      source proves CONTENT; it does not prove STRUCTURE, and structure
      needs its own assertion.

      BY TYPE — only 35 of the 39 songs sit in a section typed
      z3998:song. Four do not: Song I of Book One (which is also the
      one in a <blockquote>, and the one outside any chapter file),
      Song II, Song V — Boethius' prayer — and Song IX of Book Three,
      the "O qui perpetua" hymn, which is the most famous poem in the
      work. Trusting the type drops those four silently. Same shape as
      euclid-rivals, where ABBYY's block types lied in three different
      directions, and as fleming's unnumbered plate.

    The se:label is present in all 39 and is what is trusted here."""
    hg = find(sec, f"{X}hgroup")
    if hg is None:
        return None
    if not any((s.get(EPUB) or "") == "se:label" and (s.text or "").strip() == "Song"
               for h in hg for s in h):
        return None
    label = title = ""
    if hg is not None:
        h = hg.find(f"{X}h4") if hg.find(f"{X}h4") is not None else hg.find(f"{X}h3")
        if h is not None:
            ords = [para(s) for s in h if s.get(EPUB, "").startswith("z3998:ordinal")]
            label = ords[0] if ords else ""
        t = find(hg, f"{X}p[@epub:type='title']")
        if t is not None:
            title = para(t)
    lines = []
    for p in sec.iter(X + "p"):
        if p.get(EPUB) == "title":
            continue
        spans = [c for c in p if c.tag == X + "span"]
        if not spans:
            txt = para(p)
            if txt:
                lines.append("\t" + txt)
            continue
        for s in spans:
            txt = re.sub(r"\s+", " ", text_of(s)).strip()
            if txt:
                lines.append("\t\t" + txt if "i1" in (s.get("class") or "")
                             else "\t" + txt)
    return (label, title, lines) if lines else None


def sections_of(body):
    """Direct child <section>s of the outer chapter/part section."""
    outer = body.find(f"{X}section")
    return outer, [s for s in outer if s.tag == X + "section"]


WORDRE = re.compile(r"[^\W\d_]+")


def raw_words(name, drop_bridgehead=False):
    """The file's words by a second route: regexes over the raw XML,
    sharing no code with the ElementTree path. Two independent readings
    agreeing is evidence; one reading is a hope (epictetus/)."""
    t = clean((SRC / name).read_text())
    t = re.sub(r'<a [^>]*epub:type="noteref"[^>]*>.*?</a>', "", t, flags=re.S)
    t = t[t.find("<body"):]
    if drop_bridgehead:
        t = re.sub(r'<p epub:type="se:bridgehead">.*?</p>', "", t, flags=re.S)
        t = re.sub(r"<header>.*?</header>", "", t, flags=re.S)
    t = re.sub(r"<hgroup>.*?</hgroup>", "", t, flags=re.S)
    # The chapter heading is a bare Roman numeral which this edition
    # REPLACES with a written title, so it is excluded on both sides.
    # Normalising an intended transformation is the honest fix; dropping
    # the check because it fired is not.
    t = re.sub(r"<h3[^>]*>.*?</h3>", "", t, flags=re.S)
    return WORDRE.findall(re.sub(r"<[^>]+>", " ", t))


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    manifest, idx, arguments, songs_seen = [], 0, {}, 0

    for b in range(1, 6):
        body = load(f"book-{b}.xhtml")
        outer, subs = sections_of(body)

        hdr = outer.find(f"{X}header")
        t = find(hdr, f"{X}hgroup/{X}p[@epub:type='title']") if hdr is not None else None
        # APOSTROPHES: Standard Ebooks sets U+2019 throughout, and a
        # straight apostrophe in the comparison loses the match silently
        # -- the grimm trap, where 15 of 212 tale titles carry it. Compare
        # with them normalised, and take the published title from the
        # SOURCE so the page keeps SE's typography.
        assert t is not None and para(t).replace("\u2019", "'") == BOOK_TITLES[b], \
            f"book {b} title is {para(t) if t is not None else None!r}"
        BOOK_TITLES[b] = para(t)
        arg = find(hdr, f"{X}p[@epub:type='se:bridgehead']")
        arguments[b] = para(arg) if arg is not None else ""

        divider = f"Book {['One','Two','Three','Four','Five'][b-1]}: {BOOK_TITLES[b]}"
        pending = divider

        # SONG I OF BOOK ONE LIVES HERE, not in a chapter file.
        for sec in subs:
            s = song_of(sec)
            if s:
                songs_seen += 1
                label, title, lines = s
                head = f"Song {label}: {title}" if title else f"Song {label}"
                name = f"{idx:03d}.txt"
                (OUT / name).write_text(head + "\n\n" + "\n".join(lines) + "\n")
                # "chapter": it is a peer of Book One's CHAPTERS, not of
                # the five Books. assemble.py nests a section under its
                # Part divider when the heading reads "Chapter N: ...",
                # which this one cannot say; without the flag it renders
                # as a top-level section level with "Book One" itself.
                manifest.append({"file": name, "title": head, "part": 1,
                                 "of": 1, "words": sum(len(l.split()) for l in lines),
                                 "part_before": pending, "kind": "song",
                                 "chapter": True})
                pending, idx = None, idx + 1

        want = COUNTS[b]
        assert not (SRC / f"chapter-{b}-{want+1}.xhtml").exists(), \
            f"book {b} has more than {want} chapters on disk"
        for c in range(1, want + 1):
            cbody = load(f"chapter-{b}-{c}.xhtml")
            couter, csubs = sections_of(cbody)
            title = TITLES[b][c - 1]
            head = f"Chapter {c}: {title}"
            lines = [head, ""]
            for sec in csubs:
                s = song_of(sec)
                if s:
                    songs_seen += 1
                    label, stitle, slines = s
                    lines.append(f"Song {label}: {stitle}" if stitle
                                 else f"Song {label}")
                    lines.append("")
                    lines.extend(slines)
                    lines.append("")
                else:
                    for p in sec.iter(X + "p"):
                        txt = para(p)
                        if txt:
                            lines.append(txt)
                            lines.append("")
            name = f"{idx:03d}.txt"
            (OUT / name).write_text("\n".join(lines).rstrip("\n") + "\n")
            entry = {"file": name, "title": head, "part": 1, "of": 1,
                     "words": sum(len(l.split()) for l in lines),
                     "source_title": f"Book {b}, Chapter {c}"}
            if pending:
                entry["part_before"] = pending
                pending = None
            manifest.append(entry)
            idx += 1

    # WORD-SEQUENCE CROSS-CHECK, per source file, against a second
    # reading that shares no code with the parser.
    for b in range(1, 6):
        for name, drop in [(f"book-{b}.xhtml", True)] + \
                [(f"chapter-{b}-{c}.xhtml", False) for c in range(1, COUNTS[b] + 1)]:
            want = raw_words(name, drop)
            got = []
            body = load(name)
            outer, subs = sections_of(body)
            for sec in subs:
                s = song_of(sec)
                if s:
                    got += WORDRE.findall(" ".join(s[2]).replace("*", " "))
                else:
                    for p in sec.iter(X + "p"):
                        if p.get(EPUB) != "title":
                            got += WORDRE.findall(para(p).replace("*", " "))
            if got != want:
                bad = next((k for k, (a, c) in enumerate(zip(got + [None], want))
                            if a != c), min(len(got), len(want)))
                raise SystemExit(
                    f"{name}: text differs from source at word {bad}\n"
                    f"  parsed: ...{' '.join(got[max(0,bad-8):bad+8])}...\n"
                    f"  source: ...{' '.join(want[max(0,bad-8):bad+8])}...")

    assert songs_seen == 39, f"expected 39 songs, found {songs_seen}"
    assert sum(1 for m in manifest if m.get("kind") != "song") == 39

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (BOOK / "arguments.txt").write_text(
        "# Each book's own argument, from the source's se:bridgehead.\n"
        "# NOT PUBLISHED -- it is chapter-by-chapter plot summary of a\n"
        "# philosophical dialogue, and it is James's writing, not\n"
        "# Boethius'. Kept as the independent census witness (the grimm\n"
        "# rule) and as the material the chapter titles were written from.\n\n"
        + "\n\n".join(f"BOOK {b}\n{arguments[b]}" for b in range(1, 6)) + "\n")

    words = sum(m["words"] for m in manifest)
    nsong = sum(1 for m in manifest if m.get("kind") == "song")
    print(f"{len(manifest)} files = 39 prose chapters + {nsong} standalone "
          f"song(s); {songs_seen} songs in all, {words:,} words")
    print(f"largest file: {max(m['words'] for m in manifest):,} words")
    for m in manifest:
        if m.get("part_before"):
            print(f"  -- {m['part_before']}")


if __name__ == "__main__":
    main()
