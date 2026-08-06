"""Turn Gutenberg #28696 (Symbolic Logic, Part I) into chapters/ + manifest.

    bash symbolic-logic/fetch.sh && python3 symbolic-logic/prep.py

Carroll's logic textbook of 1896, and the genuinely trapped book of the
Carroll shelf: the notation is Victorian, the diagram method is his own
invention and nobody else's, and the terminology was abandoned by the
logic that came after — so a modern reader WITH training is more lost
than one without, not less.

FOUR THINGS THIS SOURCE NEEDS THAT THE EASIER BOOKS DID NOT.

1. 509 PRINT-PAGE CROSS-REFERENCES. Carroll refers the reader backwards
   and forwards constantly — "as explained at p. 12" — and in a
   reflowable edition there is no page 12. Dropping them silently would
   break his argument, which is cumulative and leans on them. So prep
   builds a map from every pgNNN anchor to the section it falls in, and
   rewrites each reference to name that section instead. This is the
   star-land rule (decide print-page references IN ADVANCE and log
   them) applied at a scale that has to be mechanical.

2. 314 DIAGRAMS, WHICH ARE THE NOTATION AND NOT DECORATION. Every one
   carries descriptive alt text in the source ("Diagram representing all
   x are y"), so the caption seed is Carroll's own and rides through to
   be modernised, as in ball/. A reader who loses these loses the book:
   the whole method is a square divided into compartments with counters
   on it, and the prose says "this we can represent by placing a Red
   Counter on the partition which divides it" and then shows you.

3. 108 TABLES. A CELL IS NOT A PARAGRAPH — the lesson thompson/ paid
   for, where normalise() ate three rows out of a table and moved the
   word ratio by nothing. They are emitted as indented blocks, which
   assemble.py sets as <pre>, with cells joined by spaced pipes.

4. 130 BLOCKQUOTED ASIDES. Carroll's habit is to follow a definition
   with a bracketed gloss in smaller type — "[Note that the full meaning
   of this Proposition is ...]" — and these are a real part of how he
   teaches. They are kept, marked as bracketed paragraphs so the
   translation can keep them distinct from the running argument.
"""

import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
SITE_IMG = BOOK.parent / "site/images/symbolic-logic"

MAX_WORDS = 7000
WORDNUM = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
           "Nine", "Ten"]


# Two forms, and the underscore ones need NO lookahead: a roman-numeral
# marker can be followed by a lower-case letter ("have pg_xiiifound them"),
# so a rule demanding a capital or a space after it leaves exactly those
# behind. "pg_"/"px_" are unambiguous on their own; bare "pg" is only
# stripped when digits follow.
#
# The trailing [½¼¾] is not decoration: Carroll's fourth edition inserts
# whole pages numbered 1½, 2½, 3½ and 4½, so the marker for one of them is
# "pg002½" and a pattern anchored on \d+ leaves the fraction behind, welded
# to the first word of the paragraph ("½Hence, any single Thing...").
#
# The digit run is FIXED at three, not "\d+". The marker sits in a <span> of
# its own and the body text resumes immediately after it, so once the tags
# are stripped the two run together -- and a greedy \d+ then eats the first
# digit of the text: "pg007" + "4. Define “Men.”" leaves ". Define
# “Men.”", a numbered example that has lost its number. Every
# numeric marker in this edition is zero-padded to exactly three digits
# (pg001-pg168), so the count is asserted rather than guessed.
PAGEMARK = re.compile(r"(?:pg_|px_)(?:[ivxlc]+|\d+)|pg\d{3}[½¼¾]?")

# Combining low line and combining double low line, for the eliminated
# letters of the Method of Underscoring.
COMBINING = {"under1": "\u0332", "under2": "\u0333"}


def clean(s):
    s = re.sub(r"<[^>]*>", "", s)
    s = html.unescape(s)
    # NO-BREAK AND THIN SPACES, spelled out. The source sets them
    # inside expressions ("a\u00a0=\u00a0in the kitchen") and around
    # subscripts, and a literal " " in the replace list is impossible
    # to see in a diff and easy to lose in an edit -- which is how
    # 3,789 of them survived into chapters/, where every one is a
    # character that looks exactly like a space and matches nothing.
    # (Same trap as Standard Ebooks' "Mrs.\u00a0Timorous" in bunyan/.)
    s = re.sub("[\u00a0\u2007\u202f\u2009\u2002\u2003]", " ", s)
    # The marginal page numbers are INSIDE the running text, not only in
    # the headings: "before taking the trouble to read Vol. I. pg_xiiThis,
    # I say, is just permissible". Stripping them only from headings left
    # them welded to the following word all through the body — the same
    # shape as Bunyan's noteref digits, and just as invisible to every
    # mechanical check.
    s = PAGEMARK.sub("", s)
    return re.sub(r"[ \t]+", " ", s).strip()


SMALL = {"a","an","and","as","at","but","by","for","in","of","on","or",
         "the","to","with","from","into","terms"}


def smallcaps(s):
    """SHOUTING CAPITALS -> Title Case, leaving Carroll's single-letter
    variables (x, y, m) and roman numerals alone."""
    out = []
    for i, w in enumerate(s.split()):
        if re.fullmatch(r"[IVXL]+[.,:]?", w) or len(w.strip(".,:")) == 1:
            out.append(w)
        elif w.isupper() or w.istitle():
            low = w.lower()
            out.append(w.capitalize() if (i == 0 or low.strip(".,:") not in SMALL)
                       else low)
        else:
            out.append(w)
    return " ".join(out)


def strip_pagenum(s):
    """Headings carry their print page as a prefix: 'pg043CHAPTER II.'"""
    # A heading can carry MORE THAN ONE page marker ("pg_xxxiipg001BOOK I."
    # is the start of Book I on the page after the roman-numbered front
    # matter), so strip repeatedly rather than once — a single pass leaves
    # "pg001BOOK I.", which then fails to match as a Book heading at all.
    while True:
        s2 = re.sub(r"^(?:pg|px_|pg_)[\divxlc]+", "", s)
        if s2 == s:
            break
        s = s2
    return re.sub(r"^[\s½¼¾\d]+(?=[A-Z§])", "", s).strip()


class Extract(HTMLParser):
    """Section HTML -> paragraphs, figure markers, indented tables.

    A parser, not a pattern: the source nests blockquote > div > p and
    table > tbody > tr > td, and a non-greedy close tag lands in the wrong
    place every time (see tyndall's Spenser stanza, which came out four
    times over).
    """

    def __init__(self, figmap):
        super().__init__(convert_charrefs=True)
        self.figmap = figmap
        self.out, self.buf = [], []
        self.p = 0
        self.quote = 0
        self.table = None
        self.row = None
        self.cell = None
        self.head = 0
        self.under = []
        self.overs = []
        self.skip = 0
        self.skips = []

    def flush(self):
        s = clean("".join(self.buf))
        if s:
            self.out.append(f"[{s}]" if self.quote and not s.startswith("[")
                            else s)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            src = a.get("src", "")
            name = Path(src).stem
            if name not in self.figmap:
                return
            cap = clean(a.get("alt", ""))
            n = self.figmap[name]
            marker = f"[Figure {n}: {cap}]" if cap else f"[Figure {n}]"
            # A DIAGRAM CAN LIVE INSIDE A TABLE CELL. Carroll tabulates
            # diagrams against their readings, and emitting the marker
            # straight to self.out let the figure escape the table and left
            # the row as "Interpretation of | " with nothing in it. Buffer
            # it into the cell it belongs to.
            if self.cell is not None:
                self.cell.append(marker)
            else:
                self.out.append(marker)
        elif tag == "table":
            self.flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "blockquote":
            self.flush()
            self.quote += 1
        elif tag in ("h5", "h6"):
            self.flush()
            self.head += 1
        elif tag == "p":
            self.p += 1
        elif tag == "br":
            self.buf.append(" ")
        if tag == "span":
            # THE UNDERSCORING IS THE NOTATION, AND IT LIVES IN THE CSS.
            # Book Seven's "Method of Underscoring" -- Carroll's own
            # preferred way of working a Sorites -- marks an eliminated
            # letter with one rule under it and its partner with two, and
            # the source carries that as class="under1"/"under2" on a
            # <span>. Strip the tags and 642 marks vanish, leaving the
            # section that TEACHES the method printing its worked example
            # twice over in identical unmarked letters, and most of the
            # Solutions book as rows of symbols with nothing to show what
            # was cancelled against what. Nothing mechanical can see this:
            # every word is present and in order. Carried through as the
            # combining low line and double low line.
            cls = a.get("class", "").split()
            mark = next((COMBINING[c] for c in cls if c in COMBINING), "")
            # THE PREMISS NUMERAL IS PRINTED ABOVE ITS EXPRESSION
            # (class="over1"), which in running text becomes a prefix --
            # and "1k1l'0" then reads as if the 1 belonged to the k. Set
            # it in parentheses, which is what the position was doing.
            over = "over1" in cls
            # THE MARGINAL SPANS ARE PRINT FURNITURE. Two hundred of them
            # are page numbers, which PAGEMARK already strips; the other
            # twenty-nine are the EX1/AN1/SL1 reference tags that let a
            # reader of the paper book jump between an Example, its Answer
            # and its Solution. Set in the margin they are navigation; run
            # into the text they weld onto the section heading ("EX1§ 1")
            # and read as part of the notation, which in a book of
            # subscripted letters is exactly the wrong thing to look like.
            self.skips.append("marginal" in cls)
            self.skip += self.skips[-1]
            self.under.append(mark)
            self.overs.append(over)
            if over:
                self.emit("(")

    def handle_endtag(self, tag):
        if tag == "span" and self.under:
            self.skip -= self.skips.pop()
            self.under.pop()
            if self.overs.pop():
                self.emit(")")
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(clean("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row):
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            rows = ["\t" + " | ".join(c for c in r) for r in self.table]
            if rows:
                self.out.append("\n".join(rows))
            self.table = None
        elif tag == "blockquote" and self.quote:
            self.flush()
            self.quote -= 1
        elif tag in ("h5", "h6") and self.head:
            self.head -= 1
            s = strip_pagenum(clean("".join(self.buf)))
            self.buf = []
            # assemble.is_subheading() rejects anything ending in ".;:,—",
            # so a heading that keeps its printed full stop is set as a
            # shouted paragraph instead of a heading.
            s = s.rstrip(".").strip()
            if s:
                self.out.append(s)
        elif tag == "p" and self.p:
            self.p -= 1
            self.flush()

    def emit(self, d):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(d)
        elif self.table is not None:
            pass                       # stray text between cells
        elif self.p or self.quote or self.head:
            self.buf.append(d)

    def handle_data(self, d):
        if self.under and self.under[-1]:
            mark = self.under[-1]
            d = "".join(c + mark if c.strip() else c for c in d)
        self.emit(d)

    def close(self):
        super().close()
        self.flush()
        return [x for x in self.out
                if x.strip() and x.strip() not in {">", "|", "\t>"}]


def main():
    page = SRC / "pg28696-images.html"
    if not page.exists():
        sys.exit("no symbolic-logic/source — run `bash symbolic-logic/fetch.sh`")
    t = page.read_text(encoding="utf-8", errors="replace")

    start = t.find("ADVERTISEMENT")
    end = t.find("WORKS BY LEWIS CARROLL")
    if start < 0 or end < 0:
        sys.exit("could not find the body bounds")
    body = t[t.rfind("<h2", 0, start):end]

    # ---- excise the table of contents -----------------------------------
    # It is a <table> like any other to the parser, and its rows are section
    # names against page numbers — which the cross-reference rewriter then
    # helpfully turns into "Interpretation of | [Figure 1]". It is furniture,
    # not text, and the six index*.png thumbnails in it are miniatures of
    # diagrams that appear properly later, so they are not plates either.
    before = len(body)
    toc = re.search(r"tocchap", body)
    if toc:
        a = body.rfind("<table", 0, toc.start())
        depth, i = 0, a
        while i < len(body):                 # walk to the matching close
            m2 = re.compile(r"</?table\b").search(body, i)
            if not m2:
                break
            depth += 1 if m2.group(0) == "<table" else -1
            i = m2.end()
            if depth == 0:
                break
        body = body[:a] + body[i:]
    body = re.sub(r"<tr[^>]*class=\"toc[^\"]*\".*?</tr>", "", body, flags=re.S)
    body = re.sub(r"<tr[^>]*class=\"middled\".*?</tr>", "", body, flags=re.S)
    if len(body) == before:
        sys.exit("the contents table was not found — check the source markup")

    # ---- sections -------------------------------------------------------
    # h2 for the front matter, h3 for the BOOKs and the back matter, h4 for
    # the chapters inside them. Cut on h3/h4 and on the front-matter h2s.
    SKIP = {"BY LEWIS CARROLL", "LEWIS CARROLL", "PART I",
            "MACMILLAN AND CO., LTD., LONDON.", "TRANSCRIBER'S NOTE",
            "THE END."}
    cuts = []
    for m in re.finditer(r"<h([234])[^>]*>(.*?)</h\1>", body, re.S):
        name = strip_pagenum(clean(m.group(2)))
        if not name or name.upper().rstrip(".") in {
                s.upper().rstrip(".") for s in SKIP}:
            continue
        cuts.append((m.start(), m.end(), name, int(m.group(1))))

    # ---- a source defect, corrected before anything reads the links ----
    # EVERY ROW OF THE INDEX OF TABLES POINTS AT PAGE 25. The transcription
    # gives each of the nine Tables its correct printed page number as the
    # visible text -- 25, 34, 35, 42, 46, 47, 48, 49, 78 -- and then hangs
    # all nine off href="#pg025". Following the href, as the rewriter must,
    # sends the reader to Book Three, Chapter I for every one of them,
    # including the three Triliteral tables and the table of Formulae that
    # belong to Books Four and Six. A correctly formatted reference on the
    # wrong target: ratio, figure parity and must_contain are all blind to
    # it (the same shape as candle/'s note 16).
    #
    # The rule is general and self-correcting: a link whose visible text IS
    # a page number should point at that page. It is a no-op wherever the
    # two already agree.
    def _retarget(m):
        return m.group(0).replace(f'#pg{m.group(1)}', f'#pg{int(m.group(2)):03d}')
    body, n_fixed = re.subn(
        r'<a href="#pg(\d+)"[^>]*>\s*(?:pp?\.\s*)?(\d+)\s*</a>',
        lambda m: _retarget(m) if int(m.group(1)) != int(m.group(2)) else m.group(0),
        body)
    n_fixed = sum(1 for m in re.finditer(
        r'<a href="#pg(\d+)"[^>]*>\s*(?:pp?\.\s*)?(\d+)\s*</a>', body)
        if int(m.group(1)) != int(m.group(2)))
    if n_fixed:
        sys.exit(f"{n_fixed} page links still disagree with their own text")

    # A PAGE ANCHOR MARKS THE TOP OF A PAGE, NOT THE PLACE ITSELF. Each
    # Index row carries two links: the term, anchored exactly where it is
    # defined, and the page number, anchored at the head of the page that
    # definition happens to fall on. Where a chapter opens part-way down a
    # page the two disagree, and following the page link sends the reader
    # to the chapter before -- "'Name'" is defined in Book One, Chapter IV
    # and was being indexed under Chapter III. Point each row's page link
    # at the row's own term anchor.
    _ix = body.rfind("Words &c. explained")
    if _ix < 0:
        _ix = body.rfind("Words &amp;c. explained")
    if _ix > 0:
        head, tail = body[:_ix], body[_ix:]
        tail = re.sub(
            r'(<a href="#(?!pg)([\w]+)"[^>]*>[^<]*</a>\s*</td>\s*'
            r'<td[^>]*>\s*<a )href="#pg[\w]+"',
            lambda m: m.group(1) + 'href="#pg!' + m.group(2) + '"', tail)
        body = head + tail

    # ---- the print-page map ---------------------------------------------
    # Every pgNNN anchor, mapped to the name of the section it sits in, so
    # that "p. 12" can be rewritten as the place a reader can actually go.
    #
    # THE SECTION NAME ALONE IS NOT AN ADDRESS. Carroll's chapter headings
    # are "CHAPTER I", "CHAPTER II", "CHAPTER III" -- and there are eight
    # Books, so the book contains four separate Chapter IIs and the reader
    # is sent to whichever he likes. Worse, "Review Tables VII, VIII
    # (p. 46, p. 47)" came out as "(Chapter II, Chapter II)", which reads
    # as a misprint rather than a reference. Every chapter target is
    # qualified with its Book, exactly as the manifest titles are.
    booked, bk, n = [], "", 0
    for a, b_, name, lvl in cuts:
        if lvl == 3 and re.match(r"BOOK [IVX]+", name.upper()):
            n += 1
            bk = f"Book {WORDNUM[n - 1]}"
        booked.append(bk)

    def address(i):
        # A BOOK HEADING IS NOT A PLACE TO SEND ANYONE. Five of the eight
        # carry no text of their own, so a page that falls on one (the
        # Index sends "Adjuncts" and "Attributes" to page 1, which is the
        # page BOOK I is printed on) resolved to a bare "Book One". Step
        # forward to the chapter that actually holds the definition.
        while (i + 1 < len(cuts)
               and not re.match(r"CHAPTER [IVXL]+", cuts[i][2].upper())
               and cuts[i + 1][3] != 3):
            i += 1
        where = cuts[i][2].rstrip(".,;:").strip()
        # .title() turns "CHAPTER III" into "Chapter Iii"; smallcaps
        # leaves roman numerals and single-letter variables alone.
        where = smallcaps(where)
        if booked[i] and re.fullmatch(r"Chapter [IVXL]+", where):
            return f"{booked[i]}, {where}"
        return where

    pagemap, ci = {}, 0
    # The half-pages Carroll inserts in the fourth edition anchor as
    # "pg001x", not "pg001"; a pattern of \d+ alone leaves four Index
    # entries reading "'Class' | 1½" -- a page number, in the one edition
    # that has no pages.
    for m in re.finditer(r'id="([\w]+)"', body):
        while ci + 1 < len(cuts) and cuts[ci + 1][0] < m.start():
            ci += 1
        key = m.group(1)
        pagemap[key] = pagemap["pg!" + key] = (
            (address(ci), ci) if cuts else ("", -1))

    def fix_xrefs(chunk, here=-1):
        def repl(m):
            tgt, text = m.group(1), m.group(2)
            where, sec = pagemap.get(tgt, ("", -1))
            if not where:
                return text
            # A REFERENCE INTO THE SECTION IT IS WRITTEN IN reads as
            # nonsense once the page number is gone: the four worked
            # examples of Book Five are recapitulated at the end of their
            # own chapter as "(1) [see Chapter II]", which is the chapter
            # the reader is standing in. Say "above" instead.
            if sec == here:
                return "\x01above\x02"
            return f"\x01{where}\x02"
        chunk = re.sub(r'<a[^>]*href="#(pg[\w!]+)"[^>]*>(.*?)</a>', repl,
                       chunk, flags=re.S)
        # TWO PAGE NUMBERS CAN LAND IN ONE SECTION, and then the reference
        # says the same thing twice: "Review Tables VII, VIII (p. 46, p. 47)"
        # became "(Book Four, Chapter II, Book Four, Chapter II)", and
        # "Tables V-VIII (pp. 34, 47)" became a range from a section to
        # itself. The rewrites are fenced so a repeat can be collapsed
        # without a regex having to guess where a section name ends -- the
        # names contain commas themselves.
        while True:
            c2 = re.sub("\x01([^\x02]*)\x02(\\s*(?:[,;]|and|–|—|-)\\s*)*"
                        "\x01\\1\x02", "\x01\\1\x02", chunk)
            if c2 == chunk:
                break
            chunk = c2
        # "described at p. 63" -> "described at above" reads as a slip.
        chunk = re.sub("\\b(?:at|on|in) (above)", "\\1", chunk)
        chunk = chunk.replace("\x01", "").replace("\x02", "")
        # Carroll cites his own Books in roman ("Work Examples § 1, 17-21
        # (Book VIII)"), while every heading and every rewritten reference
        # in this edition names them in words. Harmonise, or the reader has
        # to hold two numbering systems at once.
        return re.sub(r"\bBook ([IVX]+)\b",
                      lambda m: "Book " + WORDNUM[
                          ["I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                           "IX", "X"].index(m.group(1))], chunk)

    # ---- figures --------------------------------------------------------
    names = [Path(m).stem for m in
             re.findall(r'<img[^>]*src="images/([^"]+)"', body)]
    seen, figmap = set(), {}
    for n in names:
        if n not in seen:
            seen.add(n)
            figmap[n] = len(figmap) + 1

    # ---- build ----------------------------------------------------------
    sections = []
    for i, (a, b_, name, lvl) in enumerate(cuts):
        stop = cuts[i + 1][0] if i + 1 < len(cuts) else len(body)
        e = Extract(figmap)
        e.feed(fix_xrefs(body[b_:stop], here=i))
        sections.append((name, lvl, e.close()))

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()
    manifest, divider, book, bookname = [], None, 0, ""
    oversize = []
    idx = 0
    for name, lvl, paras in sections:
        # THE BOOK CHECK MUST COME FIRST. Five of the eight Book headings
        # carry no body text of their own, so an "if not paras: continue"
        # placed ahead of this skipped them entirely and no divider was ever
        # set — the book silently lost its whole top-level structure.
        if lvl == 3 and re.match(r"BOOK [IVX]+", name.upper()):
            book += 1
            bookname = f"Book {WORDNUM[book - 1]}"
            # A Book's own subject line ("The Biliteral Diagram") is an h5
            # inside it, so it arrives as this section's first paragraph.
            sub = paras[0] if paras and len(paras[0]) < 60 else ""
            divider = f"{bookname}: {sub.rstrip('.')}" if sub else bookname
            continue
        if not paras:
            continue
        sub = ""
        # A NOTE LABEL IS NOT A SUBTITLE. The back matter opens on
        # "(A) [See p. 80]", which is the first note's own number and
        # back-reference, and taking it as the section subtitle gave
        # the contents an entry reading "Notes: (a) [see Chapter Iii]".
        if (paras and len(paras[0]) < 90
                and not paras[0].startswith(("[", "\t", "(", "§"))):
            sub = paras[0]
        title = name.rstrip(".")
        m2 = re.fullmatch(r"CHAPTER ([IVXL]+)", title.upper())
        if m2 and bookname:
            title = f"{bookname}, Chapter {m2.group(1)}"
        if sub:
            title = f"{title}: {sub.rstrip('.')}"
            paras = paras[1:]
        title = " ".join(title.split())      # headings can wrap onto 2 lines
        title = smallcaps(title)
        # A title that overruns is REPORTED, not silently cut with an
        # ellipsis. Carroll's chapter subject lines run to eighty and ninety
        # characters ("REPRESENTATION OF TWO PROPOSITIONS OF RELATION, ONE IN
        # TERMS OF x AND m, AND THE OTHER IN TERMS OF y AND m") and a
        # mechanical cut leaves "...in terms of x and m, ..." in the table of
        # contents, where the reader has no way to recover the rest. These are
        # shortened by hand in the manifest; the warning is what makes a new
        # one impossible to miss.
        if len(title) > 78:
            oversize.append((f"{idx:03d}.txt", title))
        for k, chunk in enumerate(split_oversize(paras)):
            e = {"file": f"{idx:03d}.txt", "title": title,
                 "part": k + 1, "of": 1,
                 "words": sum(len(p.split()) for p in chunk)}
            if divider:
                e["part_before"] = divider
                divider = None
            (CHAPTERS / f"{idx:03d}.txt").write_text("\n\n".join(chunk) + "\n")
            manifest.append(e)
            idx += 1
    fill_of(manifest)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    SITE_IMG.mkdir(parents=True, exist_ok=True)
    for f in SITE_IMG.glob("fig*"):
        f.unlink()
    for name, n in figmap.items():
        src = SRC / "images" / f"{name}.png"
        if not src.exists():
            sys.exit(f"missing plate {src}")
        shutil.copy(src, SITE_IMG / f"fig{n}.png")

    placed = sorted(int(m) for f in CHAPTERS.glob("*.txt")
                    for m in re.findall(r"\[Figure (\d+)", f.read_text()))
    if sorted(set(placed)) != list(range(1, len(figmap) + 1)):
        missing = set(range(1, len(figmap) + 1)) - set(placed)
        sys.exit(f"{len(missing)} figures never placed: {sorted(missing)[:10]}")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words, {len(figmap)} diagrams")
    for m in manifest[:8]:
        if m.get("part_before"):
            print(f"  -- {m['part_before']} --")
        print(f"  {m['file']}  {m['words']:6,}w  {m['title'][:56]}")
    print(f"  ... ({len(manifest)} in all)")
    for f, t in oversize:
        print(f"  WARNING {f}: title is {len(t)} chars and will not fit "
              f"the contents -- shorten it by hand in manifest.json\n            {t}")


def split_oversize(paras):
    total = sum(len(p.split()) for p in paras)
    if total <= MAX_WORDS:
        return [paras]
    n = -(-total // MAX_WORDS)
    target = total / n
    parts, cur, run = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and run + w / 2 > target and len(parts) < n - 1:
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    if cur:
        parts.append(cur)
    return parts


def fill_of(manifest):
    run = []
    for m in manifest + [{"part": 1}]:
        if m["part"] == 1 and run:
            for r in run:
                r["of"] = len(run)
            run = []
        if "file" in m:
            run.append(m)
    for r in run:
        r["of"] = len(run)


if __name__ == "__main__":
    main()
