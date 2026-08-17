#!/usr/bin/env python3
"""Epictetus' Discourses (George Long, 1877) -> chapters/ + manifest.json

    ./fetch.sh && python3 epictetus/prep.py

Source: Standard Ebooks' epictetus_discourses_george-long, which is the
complete four books -- 95 chapters, ~119k words. Gutenberg has only a
SELECTION (#10661), which is why this book comes from SE.

ONE FILE PER CHAPTER, deliberately, against the grimm/ precedent of
grouping short pieces. The mean chapter is 1,254 words and grouping
would halve the file count, but assemble.build_sections sets
is_chapter=False for every section it carves out of a grouped file, so
all 95 chapters would render as top-level h2 and the four Books would
stop nesting anything. A chapter of the Discourses IS a chapter; three
of them are long enough to need parts and the rest are one file each.

THE SOURCE IS XML, SO PARSE IT AS XML. Two defects in this project's
history came from regex-walking HTML: tyndall's nested containers
emitted the Spenser stanza four times, and bunyan's noteref anchors
welded their digits onto the preceding word ("the Slough of Despond,41
his labourers"), which reads as a number in the text and passes every
mechanical check here. SE XHTML is well-formed, so ElementTree gives
document order for free and noterefs are removed as ELEMENTS before any
text is taken. Long's titles show why it matters: they arrive as
"Against the Academics37" and "That Logic Is Necessary427".

THE TITLES ARE DECIDED HERE AND NOWHERE ELSE (the quixote rule).
Long's Victorian titles are a large part of what makes the book look
forbidding -- "Of Precognitions", "About Cynism", "In What a Man Ought
to Be Exercised Who Has Made Proficiency" -- and they are also the only
map a reader has. Modernising them one at a time while translating is
how a book ends up with five conventions in it, so all 95 are settled
in advance, in one place, and carried in the manifest.

Three chapters repeat a title in Long ("Of Providence" twice, three
lots of "Certain Miscellaneous Matters", "That Logic Is Necessary"
twice). A repeated heading is a repeated anchor -- assemble.unique_ids
will silently suffix the second -- so each is distinguished by what it
is actually about.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"
REF = BOOK / "reference"

NS = {"x": "http://www.w3.org/1999/xhtml",
      "epub": "http://www.idpf.org/2007/ops"}
EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"

TARGET, MAX = 3600, 4300      # words per file; a chapter over MAX splits

BOOK_NAMES = ["Book One", "Book Two", "Book Three", "Book Four"]

# (book, chapter) -> the title this edition uses. Long's own title is
# kept in the manifest as "source_title" so the two can be compared.
TITLES = {
    (1, 1): "What Is Up to Us and What Is Not",
    (1, 2): "How to Keep Your Own Character in Every Situation",
    (1, 3): "What Follows from God Being the Father of All",
    (1, 4): "On Making Progress",
    (1, 5): "Against the Academics",
    (1, 6): "On Providence",
    (1, 7): "On the Use of Trick Arguments and Hypotheticals",
    (1, 8): "Why Logical Skill Is Not Safe in the Untrained",
    (1, 9): "What Follows from Our Kinship with God",
    (1, 10): "Against Those Chasing Promotion in Rome",
    (1, 11): "On Family Affection",
    (1, 12): "On Being Content",
    (1, 13): "How to Do Everything in a Way That Pleases the Gods",
    (1, 14): "That God Watches Everything",
    (1, 15): "What Philosophy Promises",
    (1, 16): "On Providence in the Smallest Things",
    (1, 17): "Why Logic Is Necessary",
    (1, 18): "Why We Should Not Be Angry at Other People's Mistakes",
    (1, 19): "How to Behave Toward Tyrants",
    (1, 20): "On Reason, and How It Examines Itself",
    (1, 21): "Against Those Who Want to Be Admired",
    (1, 22): "On Preconceptions",
    (1, 23): "Against Epicurus",
    (1, 24): "How to Wrestle with Circumstances",
    (1, 25): "On the Same Subject",
    (1, 26): "What the Rule of Life Is",
    (1, 27): "The Ways Impressions Come at Us, and What Defenses We Have",
    (1, 28): "Why We Should Not Be Angry at People; and What Counts as "
             "Small and Great",
    (1, 29): "On Steadiness",
    (1, 30): "What to Have Ready When Things Get Hard",

    (2, 1): "Why Confidence and Caution Are Not Opposites",
    (2, 2): "On Peace of Mind",
    (2, 3): "To Those Who Send People to Philosophers with a Recommendation",
    (2, 4): "Against a Man Caught in Adultery",
    (2, 5): "How Greatness of Spirit Goes with Taking Care",
    (2, 6): "On Things That Are Neither Good nor Bad",
    (2, 7): "How to Use Divination",
    (2, 8): "What the Nature of the Good Is",
    (2, 9): "How We Claim the Title of Philosopher Because We Cannot Live "
            "Up to Being Human",
    (2, 10): "How to Work Out Your Duties from the Names You Bear",
    (2, 11): "Where Philosophy Begins",
    (2, 12): "On Argument and Discussion",
    (2, 13): "On Anxiety",
    (2, 14): "To Naso",
    (2, 15): "Against Those Who Stubbornly Stick to What They Have Decided",
    (2, 16): "That We Do Not Practice Applying Our Judgments About Good "
             "and Evil",
    (2, 17): "How to Fit Preconceptions to Particular Cases",
    (2, 18): "How to Fight Against Impressions",
    (2, 19): "Against Those Who Take Up Philosophy Only in Words",
    (2, 20): "Against the Epicureans and the Academics",
    (2, 21): "On Inconsistency",
    (2, 22): "On Friendship",
    (2, 23): "On the Power of Speaking",
    (2, 24): "To a Man Epictetus Did Not Think Much Of",
    (2, 25): "That Logic Cannot Be Skipped",
    (2, 26): "What Is Really Going On in a Mistake",

    (3, 1): "On Personal Beauty and Finery",
    (3, 2): "What a Student Making Progress Should Train In, and What We "
            "Neglect",
    (3, 3): "What a Good Person Should Work On, and What We Should "
            "Practice Most",
    (3, 4): "Against a Man Who Cheered Too Loudly in the Theater",
    (3, 5): "Against Those Who Go Home Because They Are Ill",
    (3, 6): "Miscellaneous Remarks",
    (3, 7): "To the Governor of the Free Cities, Who Was an Epicurean",
    (3, 8): "How to Train Yourself Against Impressions",
    (3, 9): "To a Lawyer Going Up to Rome for a Lawsuit",
    (3, 10): "How to Bear Being Ill",
    (3, 11): "More Miscellaneous Remarks",
    (3, 12): "On Training",
    (3, 13): "What Loneliness Is, and What Kind of Person Is Truly Alone",
    (3, 14): "Further Miscellaneous Remarks",
    (3, 15): "Why We Should Think Before We Start Anything",
    (3, 16): "Why We Should Be Careful About the Company We Keep",
    (3, 17): "On Providence and Why the Wicked Prosper",
    (3, 18): "Why No News Should Disturb You",
    (3, 19): "The Difference Between an Ordinary Person and a Philosopher",
    (3, 20): "How Everything External Can Be Turned to Advantage",
    (3, 21): "Against Those Who Rush to Set Up as Teachers",
    (3, 22): "On the Cynic Life",
    (3, 23): "To Those Who Read and Lecture to Show Off",
    (3, 24): "Why We Should Not Be Moved by Longing for What Is Not Up to Us",
    (3, 25): "To Those Who Give Up",
    (3, 26): "To Those Who Are Afraid of Being Poor",

    (4, 1): "On Freedom",
    (4, 2): "On Close Friendships",
    (4, 3): "What We Should Trade for What",
    (4, 4): "To Those Who Want a Quiet Life",
    (4, 5): "Against the Quarrelsome and the Aggressive",
    (4, 6): "Against Those Who Complain of Being Pitied",
    (4, 7): "On Being Free from Fear",
    (4, 8): "Against Those Who Rush to Put On the Philosopher's Cloak",
    (4, 9): "To a Man Who Had Turned Shameless",
    (4, 10): "What We Should Despise and What We Should Value",
    (4, 11): "On Cleanliness",
    (4, 12): "On Attention",
    (4, 13): "Against Those Who Too Readily Tell Their Own Business",
}


def clean(t):
    """Normalise the spaces Standard Ebooks sets inside abbreviations.

    SE writes "Mrs.\\u00a0Timorous" with a no-break space, and every
    anchor written with an ordinary space then matches nothing. This cost
    bunyan/ a whole chapter division before it was found."""
    # SPELLED AS ESCAPES, NOT AS LITERALS. symbolic-logic/ wrote its
    # replace list with the characters themselves and 3,789 no-break
    # spaces rode straight through into chapters/, because an invisible
    # character in source code is invisible to the person editing it too.
    for a, b in [("\u00a0", " "), ("\u202f", " "),
                 ("\ufeff", ""), ("\u2060", "")]:
        t = t.replace(a, b)
    return t


def load(name):
    root = ET.fromstring(clean((SRC / f"{name}.xhtml").read_text()))
    body = root.find("x:body", NS)
    # KILL NOTEREFS AS ELEMENTS. Stripping tags instead welds the note
    # number onto the preceding word, which then reads as part of the
    # text and passes the word ratio, must_contain and every other check.
    #
    # THE TAIL GOES TO THE ANCHOR'S OWN PREDECESSOR, and getting that
    # wrong is worse than the bug it fixes. A first attempt appended it
    # to the parent's LAST child, which in any paragraph carrying more
    # than one note moved a clause to the end: II.23 came out reading
    # "what prevents you, if you can resolve syllogisms like Chrysippus,
    # and putting our hopes in them. If a man by this teaching does harm
    # ... from being wretched, from sorrowing". Every word is present,
    # the ratio does not move by one, and it reads almost plausibly.
    A = "{http://www.w3.org/1999/xhtml}a"
    for parent in body.iter():
        i = 0
        while i < len(parent):
            el = parent[i]
            if el.tag == A and el.get(EPUB_TYPE) == "noteref":
                tail = el.tail or ""
                del parent[i]
                if i > 0:
                    parent[i - 1].tail = (parent[i - 1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
            else:
                i += 1
    return body


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def render(el):
    """One source element -> zero or more output paragraphs."""
    tag = el.tag.split("}")[-1]
    kind = el.get(EPUB_TYPE) or ""
    if tag == "p":
        t = text_of(el)
        return [t] if t else []
    if tag == "blockquote":
        # every blockquote in this book is verse: one <p> of <span> lines
        # separated by <br/>, sometimes followed by a <cite> naming the
        # poem. Tab-indented, which is the project's only verse
        # convention, with the attribution as its last line.
        #
        # TAKE THE VERSE LINES AS CHILDREN OF THE <p>, NOT AS
        # DESCENDANTS OF THE BLOCKQUOTE. A <cite> contains a <span> of
        # its own for the book number, so el.iter() collected "i" out of
        # "Iliad, i 526" and set it as a line of the poem -- while the
        # word "Iliad" itself was dropped, since only spans were read.
        # A BLOCKQUOTE IS NOT ALWAYS VERSE. One of them (II.22, the
        # quarrel of Polynices and Eteocles) wraps a drama table, and a
        # branch that only knew about <p> and <cite> dropped the whole
        # quotation -- eight lines of Euripides, gone, with the sentence
        # that introduces them ("see what they say:") left pointing at
        # nothing.
        out, lines = [], []
        for child in el:
            ctag = child.tag.split("}")[-1]
            if ctag == "p":
                for sp in child:
                    if sp.tag.split("}")[-1] == "span":
                        t = text_of(sp)
                        if t:
                            lines.append("\t" + t)
            elif ctag == "cite":
                lines.append("\t— " + text_of(child).lstrip("—- ").strip())
            else:
                if lines:
                    out.append("\n".join(lines))
                    lines = []
                out.extend(render(child))
        if lines:
            out.append("\n".join(lines))
        return out
    if tag == "table":
        # the one drama quotation (Euripides' Phoenissae). Speaker tags
        # are TITLE CASE, never all-caps: assemble.py reads an all-caps
        # line as a section heading (the galileo lesson).
        rows = []
        for tr in el.iter():
            if tr.tag.split("}")[-1] != "tr":
                continue
            cells = [text_of(td) for td in tr
                     if td.tag.split("}")[-1] == "td"]
            if len(cells) == 2:
                rows.append(f"\t{cells[0]}: {cells[1]}")
        return ["\n".join(rows)] if rows else []
    if tag in ("hgroup", "h2", "h3", "section"):
        return []
    raise SystemExit(f"unhandled element <{tag}> epub:type={kind!r}")


WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def raw_words(name):
    """The source's words, per chapter, reached by a different route.

    The parsed output is checked against this. It is deliberately the
    crudest possible reading of the file -- delete the noteref anchors
    from the RAW XML with a regex, delete every remaining tag, take the
    words -- so that it shares no code with the ElementTree path and
    cannot go wrong in the same way. A reordering bug inside a paragraph
    changes no word and no count, so a set comparison would not see it;
    the SEQUENCE is what is compared.
    """
    t = clean((SRC / f"{name}.xhtml").read_text())
    t = re.sub(r'<a [^>]*epub:type="noteref"[^>]*>.*?</a>', "", t, flags=re.S)
    t = re.sub(r"<hgroup>.*?</hgroup>", "", t, flags=re.S)   # heading, not body
    out = []
    for m in re.finditer(r'<section id="chapter-\d+-\d+">(.*?)'
                         r'(?=<section id="chapter-|</section>\s*</body>)',
                         t, re.S):
        body = re.sub(r"<[^>]+>", " ", m.group(1))
        out.append(WORD.findall(body))
    return out


def chapters():
    """[(book, chapter, long_title, [paragraphs])] in document order."""
    out = []
    for bn in range(1, 5):
        body = load(f"book-{bn}")
        booksec = body.find("x:section", NS)
        for sec in booksec.findall("x:section", NS):
            hg = sec.find("x:hgroup", NS)
            title = text_of(hg.find("x:p[@epub:type='title']", NS))
            num = int(sec.get("id").rsplit("-", 1)[1])
            pars = []
            for el in sec:
                pars.extend(render(el))
            out.append((bn, num, title, pars))
    return out


def front():
    """Long's introduction and Arrian's dedicatory letter."""
    out = []
    for name, title in [("introduction", "Introduction"),
                        ("preface", "Arrian's Letter to Lucius Gellius")]:
        body = load(name)
        sec = body.find("x:section", NS)
        pars = []
        for el in sec:
            pars.extend(render(el))
        out.append((title, pars))
    return out


def wc(pars):
    return sum(len(p.split()) for p in pars)


def split_oversize(pars, n):
    total, out, cur, run = wc(pars), [], [], 0
    for p in pars:
        cur.append(p)
        run += len(p.split())
        if run >= total / n and len(out) < n - 1:
            out.append(cur)
            cur, run = [], 0
    if cur:
        out.append(cur)
    return out


def write_notes():
    """Long's 795 endnotes, as a crib -- NOT as part of the book.

    The bunyan/Offor precedent. They are a Victorian translator's
    apparatus: citations to Schweighauser, Greek textual argument, and
    a good many admissions of the form "I am not sure that I have
    understood rightly." They are about the TRANSLATION, not about
    Epictetus, and at 39,772 words they are a third of the book again.
    Kept where the translation can consult them, drawn on only where a
    modern reader genuinely cannot follow (the soap-bubbles rule)."""
    REF.mkdir(exist_ok=True)
    body = load("endnotes")
    lines = []
    for li in body.iter():
        if li.tag.split("}")[-1] != "li" or not li.get("id", "").startswith(
                "note-"):
            continue
        lines.append(f"[{li.get('id')[5:]}] {text_of(li).rstrip(' ↩')}")
    (REF / "notes.txt").write_text("\n\n".join(lines) + "\n")
    return len(lines)


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    chaps = chapters()
    assert len(chaps) == 95, f"expected 95 chapters, got {len(chaps)}"

    # EVERY WORD, IN ORDER, BY TWO INDEPENDENT ROUTES.
    want = [w for bn in range(1, 5) for w in raw_words(f"book-{bn}")]
    assert len(want) == len(chaps), f"{len(want)} raw vs {len(chaps)} parsed"
    for (bn, cn, _, pars), expect in zip(chaps, want):
        got = WORD.findall(" ".join(pars))
        if got != expect:
            bad = next(i for i, (a, b) in enumerate(zip(got + [None], expect))
                       if a != b)
            raise SystemExit(
                f"{bn}.{cn}: text differs from the source at word {bad}\n"
                f"  parsed: ...{' '.join(got[max(0, bad - 8):bad + 8])}...\n"
                f"  source: ...{' '.join(expect[max(0, bad - 8):bad + 8])}...")

    missing = [(b, c) for b, c, _, _ in chaps if (b, c) not in TITLES]
    assert not missing, f"no modern title for {missing}"
    extra = set(TITLES) - {(b, c) for b, c, _, _ in chaps}
    assert not extra, f"modern title for a chapter that does not exist: {extra}"
    # A REPEATED HEADING IS A REPEATED ANCHOR, and unique_ids will hide it.
    dupes = {t for t in TITLES.values()
             if list(TITLES.values()).count(t) > 1}
    assert not dupes, f"title used twice: {dupes}"

    manifest, idx = [], 0

    def emit(title, pars, part=1, of=1, source_title=None, divider=None):
        nonlocal idx
        name = f"{idx:03d}.txt"
        head = [title] + ([f"(Part {part} of {of})"] if of > 1 else [])
        (OUT / name).write_text("\n\n".join(head + pars) + "\n")
        entry = {"file": name, "title": title, "part": part, "of": of,
                 "words": wc(pars)}
        if source_title:
            entry["source_title"] = source_title
        if divider:
            entry["part_before"] = divider
        manifest.append(entry)
        idx += 1

    for title, pars in front():
        emit(title, pars)

    seen_books = set()
    for bn, cn, long_title, pars in chaps:
        title = f"Chapter {cn}: {TITLES[(bn, cn)]}"
        divider = None
        if bn not in seen_books:
            seen_books.add(bn)
            divider = BOOK_NAMES[bn - 1]
        n = wc(pars)
        if n > MAX:
            k = -(-n // TARGET)
            for i, chunk in enumerate(split_oversize(pars, k), 1):
                emit(title, chunk, i, k, long_title,
                     divider if i == 1 else None)
        else:
            emit(title, pars, source_title=long_title, divider=divider)

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    notes = write_notes()
    words = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {len(chaps)} chapters, {words:,} words")
    print(f"largest file: {max(m['words'] for m in manifest):,} words")
    print(f"reference/notes.txt: {notes} endnotes kept as a crib")


if __name__ == "__main__":
    main()
