"""Standard Ebooks XHTML -> chapters/ + manifest.json for Wollstonecraft's
A Vindication of the Rights of Woman.

Adapted from subjection/prep.py, which is adapted from mill/prep.py, and
carrying forward the two rules that earned their keep there:

  - PARSE THE SOURCE AS XML, NOT WITH REGEX (the epictetus rule), then
    CHECK THE PARSE AGAINST A SECOND, INDEPENDENT READING of the raw
    file that shares no code with it. Two readings that agree are
    evidence; one reading is a hope. Compare CHARACTERS, not tokens.
  - DELETE NOTEREF ANCHORS AS ELEMENTS, giving each tail to the nearest
    preceding sibling THAT STILL EXISTS. On Liberty had three noterefs
    in one paragraph and the naive version handed note 8's tail to note
    7, which had itself just been removed; half a sentence vanished with
    every other word present and in order.

FOUR THINGS THIS BOOK HAS THAT NEITHER MILL VOLUME DID:

  1. THE CHAPTER TITLES ARE HERS, AND STANDARD EBOOKS DROPPED THEM.
     SE sets a bare Roman numeral in the <h2> and in its own ToC, but
     the 1792 printing titles every chapter ("ANIMADVERSIONS ON SOME OF
     THE WRITERS WHO HAVE RENDERED WOMEN OBJECTS OF PITY, BORDERING ON
     CONTEMPT"). So unlike subjection/, where the titles had to be NEW
     WRITING, here they are the author's and are MODERNISED like any
     other sentence of hers -- the ball/ rule for captions the source
     supplies. They were taken from Gutenberg #3420's contents list,
     not from memory (the epictetus rule); the originals are logged in
     running_notes.txt beside each modern rendering.
  2. TWO CHAPTERS ARE DIVIDED INTO NUMBERED SECTIONS, and the section
     headings are bare numbers with no title ("Section 5.4"), sitting
     in a <header> inside a z3998:subchapter. Chapter Five's five
     sections take one writer each, which is most of what a reader
     needs to navigate a 16,000-word chapter, so each gets a short
     descriptive tail. THAT TAIL IS NEW WRITING, and every one of them
     was written from the section's own opening sentence rather than
     from the book's reputation -- see SECTION_TITLES.
  3. WOLLSTONECRAFT QUOTES VERSE CONSTANTLY (eleven blockquotes:
     Milton, Pope, Shakespeare, Dryden). Verse stays verse, as one
     tab-indented block per quotation -- and it is kept VERBATIM, since
     it is the property of the language and half of it is what she is
     attacking. Quoted PROSE is a different case; see text_analysis.txt.
  4. ALL 37 ENDNOTES ARE HERS. They are inlined as "Footnote: ..."
     paragraphs after the citing paragraph (the candle pattern), in her
     own voice. Nothing goes to reference/.
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

MAXW = 7000                      # an agent must OUTPUT as much as it reads

# WORD-FORM NUMBERS, as in mill/ and subjection/. assemble.CHAP_LINE
# matches only "Chapter <digits>: Title" and nests those as h3 under a
# Part divider; this book has no Parts, so digits would leave thirteen
# chapters nested under nothing and make the Dedication look like a peer
# of the whole volume.
TITLES = {
    1: "Chapter One: The Rights of Human Beings, and the Duties That Come with Them",
    2: "Chapter Two: The Common Opinion That Each Sex Has a Character of Its Own",
    3: "Chapter Three: The Same Subject Continued",
    4: "Chapter Four: On the Degraded State to Which Various Causes Have Reduced Women",
    5: "Chapter Five: Criticisms of the Writers Who Have Made Women Objects of Pity, Bordering on Contempt",
    6: "Chapter Six: The Effect That Early Associations of Ideas Have on Character",
    7: "Chapter Seven: Modesty, Considered in Full, and Not as a Virtue Belonging to One Sex",
    8: "Chapter Eight: How Morality Is Undermined by Ideas About a Woman's Reputation",
    9: "Chapter Nine: The Harm Done by the Unnatural Distinctions Society Establishes",
    10: "Chapter Ten: Parental Affection",
    11: "Chapter Eleven: Duty to Parents",
    12: "Chapter Twelve: On National Education",
    13: "Chapter Thirteen: Examples of the Folly That Women's Ignorance Produces, with Closing Reflections on a Revolution in the Manners of Women",
}

# The numbered sections carry no title in the original. The tail after
# the colon is NEW WRITING, taken from each section's own first sentence.
# NO TERMINAL PERIOD and title case, or assemble.is_subheading refuses
# them and they render as a paragraph shouted in capitals (the ball trap).
SECTION_TITLES = {
    (5, 1): "Section One: Rousseau",
    (5, 2): "Section Two: Dr. Fordyce's Sermons",
    (5, 3): "Section Three: Dr. Gregory's Legacy to His Daughters",
    (5, 4): "Section Four: Against the Prerogative of Man",
    (5, 5): "Section Five: Lord Chesterfield's Letters",
    (13, 1): "Section One: Fortune-Tellers and Credulity",
    (13, 2): "Section Two: Sentiment and the Reading of Novels",
    (13, 3): "Section Three: Dress and Vanity",
    (13, 4): "Section Four: The Sensibility Women Are Supposed to Have",
    (13, 5): "Section Five: The Rearing of Children",
    (13, 6): "Section Six: Concluding Reflections",
}

FRONT = {
    "dedication": "To Monsieur Talleyrand-Perigord, Late Bishop of Autun",
    "introduction": "Introduction",
}


def clean(s):
    """NO-BREAK SPACES ARE INVISIBLE AND BREAK EVERY ANCHOR (bunyan).
    Standard Ebooks sets one inside abbreviations and around dashes.
    Spell them as escapes -- writing them literally is how 3,789 of them
    survived into symbolic-logic's chapters/."""
    return (s.replace(" ", " ").replace(" ", " ")
             .replace("⁠", "").replace("⁡", ""))


def text_of(el):
    """All text under el, with <em>/<i> carried through as *emphasis*."""
    out = []
    tag = el.tag.split("}")[-1]
    emph = tag in ("em", "i")
    if emph:
        out.append("*")
    out.append(el.text or "")
    for kid in el:
        out.append(text_of(kid))
    if emph:
        # the marker may not enclose a space or assemble.EMPH refuses it
        inner = "".join(out[1:]).strip()
        out = ["*" + inner + "*"] if inner else [""]
    out.append(el.tail or "")
    return "".join(out)


def flat(el):
    return re.sub(r"\s+", " ", clean(text_of(el))).strip()


def kill_noterefs(root):
    """Delete noteref anchors AS ELEMENTS, tail to the SURVIVING
    predecessor. See the module docstring for what the other version
    costs."""
    seen = []
    for parent in list(root.iter()):
        prev = None
        for kid in list(parent):
            if kid.tag == f"{X}a" and "noteref" in (kid.get(EPUB) or ""):
                n = int(re.search(r"\d+", kid.get("href") or
                                  kid.get("id") or "0").group())
                seen.append((parent, n))
                tail = kid.tail or ""
                if prev is None:
                    parent.text = (parent.text or "") + tail
                else:
                    prev.tail = (prev.tail or "") + tail
                parent.remove(kid)
            else:
                prev = kid
    return seen


def verse_block(bq):
    """A z3998:verse blockquote -> ONE tab-indented block. Consecutive
    indented lines must stay ONE block (the fleming rule): one paragraph
    per line makes each its own <pre> with a 2em margin, which strews a
    five-line quotation down half a page."""
    lines = []
    for p in bq.iter(f"{X}p"):
        for span in p.findall(f"{X}span"):
            s = flat(span)
            if s:
                lines.append("\t" + s)
        if not p.findall(f"{X}span"):
            s = flat(p)
            if s:
                lines.append("\t" + s)
    # THE ATTRIBUTION IS PART OF THE QUOTATION and lives in a <cite>
    # INSIDE the blockquote. Collecting only spans drops it silently --
    # "—Dryden" simply vanished, and the cross-check is the only thing
    # that noticed.
    for c in bq.iter(f"{X}cite"):
        s = flat(c)
        if s:
            lines.append("\t" + s)
    return "\n".join(lines)


def paragraphs(path, chapter=None):
    """[(text, note_numbers)] for one source file, in document order.

    Walks the body itself rather than iter()ing every <p>, because a
    verse blockquote's <p> must NOT be emitted a second time on its own
    -- the tyndall bug, where nested containers each emitted their whole
    contents and the Spenser stanza appeared four times.
    """
    root = ET.parse(path).getroot()
    owner = {}
    for parent, n in kill_noterefs(root):
        owner.setdefault(id(parent), []).append(n)

    out = []

    def walk(el, sec=None):
        for kid in el:
            tag = kid.tag.split("}")[-1]
            if tag == "section":
                m = re.match(r"chapter-\d+-(\d+)$", kid.get("id") or "")
                walk(kid, int(m.group(1)) if m else sec)
            elif tag == "header":
                # the chapter's own <h2> is a bare Roman numeral we
                # replace; a subchapter's <p> is a bare "Section 5.4"
                if sec is not None and chapter is not None:
                    title = SECTION_TITLES.get((chapter, sec))
                    assert title, f"no title for section {chapter}.{sec}"
                    out.append((title, []))
            elif tag == "blockquote":
                if "verse" in (kid.get(EPUB) or ""):
                    b = verse_block(kid)
                    if b:
                        out.append((b, owner.get(id(kid), [])))
                else:
                    walk(kid, sec)
            elif tag == "hr":
                out.append(("* * *", []))
            elif tag in ("p", "cite"):
                s = flat(kid)
                if s:
                    out.append((s, owner.get(id(kid), [])))
            else:
                walk(kid, sec)

    walk(root.find(f"{X}body"))
    return out


def notes():
    root = ET.parse(SRC / "endnotes.xhtml").getroot()
    out = {}
    for li in root.iter(f"{X}li"):
        m = re.search(r"\d+", li.get("id") or "")
        if not m:
            continue
        for a in list(li.iter(f"{X}a")):
            if "backlink" in (a.get(EPUB) or ""):
                for p in li.iter():
                    if a in list(p):
                        p.remove(a)
                        break
        s = flat(li).rstrip("↩").strip()
        out[int(m.group())] = s
    return out


def split_parts(pars, maxw):
    """Cut a chapter into <= maxw-word parts at paragraph boundaries,
    PREFERRING a section boundary when one is near (the soap-bubbles
    rule that no recipe is cut in half)."""
    total = sum(len(p.split()) for p in pars)
    k = max(1, -(-total // maxw))
    if k == 1:
        return [pars]
    target = total / k
    heads = {i for i, p in enumerate(pars) if p in SECTION_TITLES.values()}
    parts, cur, run = [], [], 0
    for i, p in enumerate(pars):
        w = len(p.split())
        near = heads and any(abs(i - h) <= 2 for h in heads)
        want = run + w / 2 > target
        if cur and len(parts) < k - 1 and (
                (i in heads and run > target * 0.6) or (want and not near)):
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    parts.append(cur)
    return parts


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    note = notes()
    assert set(note) == set(range(1, 38)), sorted(note)

    manifest, idx = [], 0

    def emit(title, body, part, of):
        nonlocal idx
        name = f"{idx:03d}.txt"
        (OUT / name).write_text(title + "\n\n" + body.rstrip() + "\n")
        manifest.append({"file": name, "title": title, "part": part,
                         "of": of, "words": len(body.split())})
        idx += 1

    def gather(path, chapter=None):
        pars, used = [], []
        for text, ns in paragraphs(path, chapter):
            pars.append(text)
            for n in sorted(ns):
                used.append(n)
                pars.append("Footnote: " + note[n])
        return pars, used

    used = []
    order = [(SRC / "dedication.xhtml", FRONT["dedication"], None),
             (SRC / "introduction.xhtml", FRONT["introduction"], None)]
    order += [(SRC / f"chapter-{c}.xhtml", TITLES[c], c) for c in range(1, 14)]

    for path, title, chapter in order:
        pars, u = gather(path, chapter)
        used += u
        parts = split_parts(pars, MAXW)
        for i, part in enumerate(parts, 1):
            emit(title, "\n\n".join(part), i, len(parts))

    assert sorted(used) == sorted(note), \
        f"missing {sorted(set(note) - set(used))}, dup {sorted(n for n in set(used) if used.count(n) > 1)}"
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # -- SECOND, INDEPENDENT READING. Shares no code with the parser.
    # Footnotes are compared separately, because the raw reading has them
    # at the back where the source keeps them and the parser has moved
    # them inline. <header> goes for both the chapter's bare numeral and
    # the subchapters' bare "Section 5.4", neither of which survives.
    want = []
    for path, _, _ in order:
        raw = path.read_text()
        raw = re.sub(r"<head>.*?</head>", " ", raw, flags=re.S)
        raw = re.sub(r"<header>.*?</header>", " ", raw, flags=re.S)
        # the dedication sets its <h2> BARE, outside any <header>, so
        # stripping headers alone leaves the title in the raw reading
        # while the parser has dropped it
        raw = re.sub(r"<h2[^>]*>.*?</h2>", " ", raw, flags=re.S)
        raw = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>.*?</a>', " ", raw,
                     flags=re.S)
        want += re.sub(r"\s+", " ", clean(re.sub(r"<[^>]+>", " ", raw))).split()
    got = []
    for m in manifest:
        body = "\n".join((OUT / m["file"]).read_text().split("\n")[1:])
        keep = [p for p in re.split(r"\n\s*\n", body)
                if not p.strip().startswith("Footnote: ")
                and p.strip() not in SECTION_TITLES.values()]
        got += " ".join(keep).split()
    for n in sorted(note):
        hits = sum((OUT / m["file"]).read_text().count("Footnote: " + note[n])
                   for m in manifest)
        assert hits == 1, f"note {n} appears {hits} times inline"

    squash = lambda ws: re.sub(r"\s+", "", " ".join(ws)).replace("*", "")
    a, b = squash(want), squash(got)
    if a != b:
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                 min(len(a), len(b)))
        raise SystemExit(f"diverges at char {i} (source {len(a)}, out {len(b)}):\n"
                         f"  source ...{a[max(0, i-70):i+70]}\n"
                         f"  output ...{b[max(0, i-70):i+70]}")
    print(f"cross-check: {len(a):,} characters match, in order")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words; "
          f"largest {max(m['words'] for m in manifest):,}")
    print(f"{sum(1 for m in manifest if m['of'] > 1)} files are chapter parts")


if __name__ == "__main__":
    main()
