"""Turn the 1885 Archive.org scan of Euclid and His Modern Rivals into
chapters/ + manifest, with the Appendices as a crib in reference/.

    bash euclid-rivals/fetch.sh && python3 euclid-rivals/prep.py

Carroll's 1879 farce, revised 1885: Minos, a college examiner marking
papers at midnight, is visited by the ghost of Euclid and then by Herr
Niemand, the phantom of a German professor who speaks for each modern
geometry textbook in turn. Four Acts. It is very funny and almost nobody
has read it.

NOT ON GUTENBERG, so this is the thompson/ OCR path -- see
source_notes.txt for the full assessment, and abbyy.py and speakers.py for
the two modules this leans on.

WHY THIS WORKS FROM THE ABBYY XML AND NOT THE PLAIN TEXT

Archive also offers a djvu.txt, and it is a flat dump: no page boundaries,
no block types, and no record of which text was italic. This book is a
play, its stage directions and speaker tags are italic, and italic is what
the 1885 scan recognises worst ("a College dudy. Time, midvigJtf"). The
XML records italic per run, so the STRUCTURE survives even where the
CHARACTERS do not -- which is the only reason all 1,068 speaker tags could
be resolved (speakers.py).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from abbyy import pages, clean                            # noqa: E402
from speakers import resolve, looks_like_tag              # noqa: E402
from repair import repair_tokens, english_share           # noqa: E402
from replate import NOT_A_PLATE                           # noqa: E402

BOOK = Path(__file__).parent
SRC = BOOK / "source"
CHAPTERS = BOOK / "chapters"
REFERENCE = BOOK / "reference"
XML = SRC / "euclidhismodernr00carr_abbyy.gz"

MAX_WORDS = 7000

# Scan pages, not printed pages. The body opens on the ACT I title page and
# the Appendices begin at the first APPENDIX heading.
BODY_FIRST, APPENDIX_FIRST = 38, 265

# PAGE 38 AND PAGE 40 ARE THE SAME PRINTED PAGE. An erratum slip is pasted
# over the stage direction on 38, so the scan holds the opening of the play
# twice -- once destroyed. Concatenated naively the book opens with a line
# of pure noise and then repeats itself.
DUPLICATE_PAGES = {38, 39}

# Running heads sit at the top of the page in nine-point ("MINOS AND
# EUCLID. [Act I."); signature marks sit at the foot in seven- or
# eight-point ("'^ B"). Both are page furniture and both are INSIDE the
# text, which is the thompson/ trap: strip one and it leaves a blank line,
# a blank line is a paragraph break, and paragraphs then split at every
# page turn.
HEAD_ZONE, FOOT_ZONE = 0.12, 0.90
HEAD_MAX_CHARS = 60


def is_running_head(par, page):
    if par[0].top >= HEAD_ZONE * page.height:
        return False
    txt = clean(" ".join(l.text for l in par))
    if len(txt) > HEAD_MAX_CHARS:
        return False
    size = par[0].runs[0].size if par[0].runs else ""
    if size not in ("9.", "8."):
        return False
    letters = [c for c in txt if c.isalpha()]
    caps = sum(1 for c in letters if c.isupper())
    return (bool(re.search(r"\[\s*A[Cc][Tt]", txt))
            or re.fullmatch(r"[\d ivxl]+", txt.lower().strip())
            or (letters and caps / len(letters) > 0.6))


def is_signature(par, page):
    """Printer's gathering marks: "B", "C", "'^ B".

    Position alone will not do it. They usually sit at the foot, but the
    scan also puts some in a block of their own part-way down the page,
    where a foot-of-page test never sees them and a bare "C" then arrives
    as a paragraph of the play.
    """
    txt = clean(" ".join(l.text for l in par))
    size = par[0].runs[0].size if par[0].runs else ""
    if len(txt) <= 3 and size in ("6.", "7.", "8."):
        return True
    if par[0].top <= FOOT_ZONE * page.height:
        return False
    return len(txt) <= 6 or size in ("6.", "7.")


APPENDIX = re.compile(r"^APPENDIX\s*([IVXL]*)\.?$", re.I)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}

# THE ACT AND SCENE HEADINGS ARE THE SPINE OF THE BOOK AND THE SCAN MANGLES
# THEM. A pattern strict enough to be safe on prose misses six of the
# nineteen Act headings ("ACT 11.", "A-CT II.") and eight of the seventeen
# Scene headings ("SCE^^E II.", "Scene YI.", "Scene VL"). Every miss is
# silent: the heading falls through into the body as an all-caps paragraph,
# which assemble.py then renders as a spurious heading, AND the section it
# should have opened never opens, so two scenes are welded into one file
# with the wrong title. Nothing mechanical sees either half of that.
#
# So match loosely and verify by count instead: the word is whatever
# reduces to SCENE-ish once the scan's noise is dropped, and the numeral is
# read through a table of the substitutions this scan actually makes.
HEAD = re.compile(r"^(\S+)\s+([IVXLY1lJ]+)\.?(?:\s+(.*))?$")
NUMERAL = str.maketrans("1lLJY", "IIIIV")
ACT_WORDS = {"ACT"}                     # "A-CT" reduces to this
SCENE_WORDS = {"SCENE", "SCEE", "SCNE", "SCEXE"}


FULL_NAMES = {"minos": "Minos", "euclid": "Euclid", "niemand": "Niemand",
              "nostradamus": "Nostradamus", "rhadamanthus": "Rhadamanthus"}


def tag_speaker(lead):
    """resolve(), but a name spelled out in full is its own tag.

    speakers.NOT_SPEAKER holds the five full names so that "Minos reads."
    and "[Minos sleeping" cannot be promoted to speeches -- and that also
    refuses the three paragraphs in the book which carry the name in full
    as the tag: Niemand's opening line of Act Two, and Minos's aside beside
    it. looks_like_tag() already demands the trailing point or comma, which
    is exactly what the stage directions do not have.
    """
    key = re.sub(r"[^a-z]", "", lead.lower())
    if key in FULL_NAMES:
        return FULL_NAMES[key], 0.0
    return resolve(lead)


def _head(txt, words):
    """(roman number, trailing title) if txt is one of these headings."""
    m = HEAD.match(txt.strip())
    if not m:
        return None
    if re.sub(r"[^A-Za-z]", "", m.group(1)).upper() not in words:
        return None
    n = ROMAN.get(m.group(2).upper().translate(NUMERAL))
    return None if n is None else (n, (m.group(3) or "").strip())


# The scene titles are reader-facing, so they are taken from the book's own
# ARGUMENT OF DRAMA rather than from the scanned heading, whose descriptive
# line arrives as raw OCR ("Treatment of Parallels hy equidistances") and
# never passes through the cross-copy repair. Act One's two scenes keep the
# bare form they were translated under. Act Four has no Scene heading at all.
SCENE_TITLE = {
    (2, 1): "Introductory",
    (2, 2): "Legendre",
    (2, 3): "Cooley",
    (2, 4): "Cuthbertson",
    (2, 5): "Henrici",
    (2, 6): "Wilson, Pierce and Willock",
    (3, 1): "Chauvenet, Loomis, Morell, Reynolds and Wright",
    (3, 2): "The Syllabus, and Wilson's Syllabus-Manual",
}


def read_pages():
    """Every page as (number, [(kind, text)]), furniture already gone."""
    out = []
    for pg in pages(XML):
        if pg.number in DUPLICATE_PAGES or not pg.blocks:
            continue
        items = []
        for b in pg.blocks:
            if b.kind == "Picture":
                # a full-bleed Picture block is the scan of a whole leaf,
                # not a plate
                if (b.right - b.left) < pg.width * 0.95:
                    items.append(("picture", f"{pg.number}"))
                continue
            if b.kind == "Table":
                items.append(("table", f"{pg.number}"))
                continue
            for par in b.paragraphs:
                if is_running_head(par, pg) or is_signature(par, pg):
                    continue
                txt = clean(" ".join(l.text for l in par))
                if not txt:
                    continue
                tag = None
                r0 = par[0].runs[0] if par[0].runs else None
                if r0 and r0.italic and looks_like_tag(clean(r0.text)):
                    who, _ = resolve(clean(r0.text))
                    if who:
                        tag = who
                        txt = clean(txt[len(clean(r0.text)):])
                items.append(("speech" if tag else "par",
                              f"{tag}\t{txt}" if tag else txt))
        out.append((pg.number, items))
    return out


# RUNNING HEADS is_running_head() CANNOT SEE. It tests position, length and
# point size, and ABBYY merged these twelve into the body block, where they
# are none of the three. Four are welded onto the first words of a sentence
# --- "Sc. VI. § I.] ANGLES. 101 table, and each player tries..." --- so
# they are not even paragraphs of their own; the rest stand alone. Every one
# of them reads as text, passes the word ratio, and cuts a sentence in half
# at the page turn.
#
# Listed rather than matched. The twelve are not one shape (the scan reads
# "Sc. VI." as "Sc. YL" and a title as "SO-CALLED 'parallels: 14'"), and a
# pattern loose enough to take them all takes real text with it -- two
# paragraphs here legitimately open "0 and 0'" and "1 should be very sorry",
# the second being an "I" the scan read as a 1. The counts are asserted, so
# a changed source stops the build instead of quietly keeping the furniture.
# The two shapes are regular even where their contents are not: the verso
# head is "<page> <AUTHOR>. [Act II." and the recto "Sc. VI. § 1.] ANGLES.
# 101". Matched WHOLE-PARAGRAPH and short, which no body paragraph is, and
# the counts are asserted so a re-OCR cannot quietly change what is dropped.
VERSO_HEAD = re.compile(r"^\d{0,3}\s*■?\s*[A-Z][A-Za-z'’ ]*\.?\s*"
                        r"\[\s*A[Cc][Tt]\b[^\]]{0,30}$")
RECTO_HEAD = re.compile(r"^(?:A[Cc][Tt]\s+[IVXLY]+\.\s*)?"
                        r"Sc[.,]?\s*[IVXLYivxly]+\b.{0,44}\]?.{0,4}$")
HEAD_SHAPES = [("verso", VERSO_HEAD, 6), ("recto", RECTO_HEAD, 10)]
HEAD_LEAKS = [("75", 1),        # a page number left alone on the turn
              ("[Act I.", 1), ("[Act III.", 1)]   # heads torn in half


# A SPEECH ABBYY BURIED AT THE END OF ANOTHER PARAGRAPH. The tag is not at
# a paragraph start, so nothing structural can find it, and the speech reads
# as the last sentence of the speaker it interrupts -- Minos agreeing with
# Euclid inside Euclid's own paragraph. Found by the tag census, not by any
# check on the output.
# Each entry is (context, tag, speaker, count). MATCHED ON THE CONTEXT, cut
# at the tag: "Euc." on its own occurs on nearly every page of this book as
# a citation ("Euc. I. 46"), so the tag alone is far too little to go on.
# One paragraph here holds two of them -- Minos answers, Euclid exclaims and
# Minos replies, all inside a single block -- so the split has to repeat
# until the paragraph stops yielding.
EMBEDDED_TAGS = [
    ("^lin. Very well.", "^lin.", "Minos", 1),
    ("Euc. It is very like making a new Triangle", "Euc.", "Euclid", 1),
    ("Min. It is indeed.", "Min.", "Minos", 1),
]


def split_embedded(paras):
    """Cut a buried speech loose from the paragraph that swallowed it."""
    seen = {ctx: 0 for ctx, _, _, _ in EMBEDDED_TAGS}
    out = []
    for item in paras:
        kind, text = item
        while True:
            for ctx, tag, who, _ in EMBEDDED_TAGS:
                i = text.find(ctx)
                if i == -1:
                    continue
                seen[ctx] += 1
                head, text = text[:i].rstrip(), text[i + len(tag):].strip()
                if head.split("\t", 1)[-1].strip():
                    out.append((kind, head))
                kind = "speech"
                text = f"{who}\t{text}"
                break
            else:
                break
        # only a SPEECH can be emptied by the split; a scene heading with no
        # descriptive title has an empty tail and must not be dropped
        if kind == "speech" and not text.split("\t", 1)[-1].strip():
            continue
        out.append((kind, text))
    wrong = {c: (seen[c], n) for c, _, _, n in EMBEDDED_TAGS if seen[c] != n}
    if wrong:
        sys.exit(f"embedded tags changed (got, want): {wrong}")
    return out


def strip_head_leaks(paras):
    """Drop the running heads that reached the body.

    Must run BEFORE mend(). Each of these stands as its own paragraph here,
    and the sentence it interrupts resumes in the next one -- so mend, which
    joins a paragraph that opens in lower case to the one before it, welds
    the body onto the RUNNING HEAD instead of onto its own first half.
    """
    seen = {p: 0 for p, _ in HEAD_LEAKS}
    shapes = {name: 0 for name, _, _ in HEAD_SHAPES}
    out = []
    for kind, text in paras:
        stripped = text.strip()
        if kind == "par":
            if stripped in seen:
                seen[stripped] += 1
                continue
            hit = next((name for name, pat, _ in HEAD_SHAPES
                        if len(stripped) < 90 and pat.match(stripped)), None)
            if hit:
                shapes[hit] += 1
                continue
        out.append((kind, text))
    wrong = {p: (seen[p], n) for p, n in HEAD_LEAKS if seen[p] != n}
    wrong.update({name: (shapes[name], n) for name, _, n in HEAD_SHAPES
                  if shapes[name] != n})
    if wrong:
        sys.exit(f"running-head leaks changed (got, want): {wrong}")
    return out


def mend(paras):
    """Rejoin paragraphs split by a page turn.

    thompson/'s rule, and it is the one that matters most on a scan: no
    English paragraph begins in lower case. Stripping the running head
    leaves the two halves of a sentence as separate paragraphs, and
    nothing downstream can tell.
    """
    out = []
    for kind, text in paras:
        if (out and kind == "par" and out[-1][0] in ("par", "speech")
                and text[:1].islower()):
            k, prev = out[-1]
            joiner = "" if prev.endswith("-") else " "
            out[-1] = (k, prev.rstrip("-") + joiner + text)
        else:
            out.append((kind, text))
    return out


def corrector_body():
    """The 1879 scan's body text, for repair.py to correct against."""
    raw = (SRC / "euclidandhismode000469mbp_djvu.txt").read_text(
        errors="replace")
    raw = re.sub(r"[ \t]{2,}", " ", raw)
    # ANCHOR ON THE STAGE DIRECTION, NOT ON THE FIRST SPEECH. Anchored on
    # "So, my friend" the corrector began AFTER the opening stage
    # direction -- which is the single most damaged passage in the 1885
    # scan and the whole reason the 1879 is here. It went unrepaired and
    # nothing said so.
    i = raw.find("a College study")
    j = raw.find("APPENDIX", i)
    if i < 0:
        sys.exit("cannot find the start of the body in the 1879 scan")
    return raw[max(0, i - 120):j if j > 0 else len(raw)]


def repaired(items):
    """Run the whole body through repair.py in one alignment, keeping the
    paragraph boundaries of the copy text exactly.

    One alignment and not one per paragraph: the two editions differ in
    content here and there, and a per-paragraph search would happily match
    a paragraph to the wrong neighbour and then 'correct' it into it.
    """
    tokens, spans = [], []
    for kind, text in items:
        body = text.split("\t", 1)[1] if kind == "speech" else text
        start = len(tokens)
        tokens.extend(body.split())
        spans.append((kind, text, start, len(tokens)))
    log = []
    fixed = repair_tokens(tokens, corrector_body().split(), log)
    out = []
    for kind, text, a, b in spans:
        body = " ".join(x for x in fixed[a:b] if x)
        if kind == "speech":
            out.append((kind, text.split("\t", 1)[0] + "\t" + body))
        else:
            out.append((kind, body))
    return out, log


def read_body_and_appendix():
    """(body items, appendix text). Headings carry their point size, which
    is how a display heading is told from a line of prose: the Acts are set
    in 19- or 20-point and the Scenes in 11- or 12-point, while the body is
    10-point. Pattern alone cannot do it -- "ACT III" also appears in the
    running heads and in the contents."""
    body, appendix = [], []
    zone = False        # inside the run of display lines that opens a section
    for pg in pages(XML):
        if pg.number in DUPLICATE_PAGES or not pg.blocks:
            continue
        where = body if pg.number < APPENDIX_FIRST else appendix
        if pg.number < BODY_FIRST:
            continue
        for b in pg.blocks:
            if (b.kind == "Picture" and pg.number not in NOT_A_PLATE
                    and (b.right - b.left) < pg.width * 0.95):
                where.append(("picture", str(pg.number)))
                continue
            if b.kind == "Table":
                where.append(("table", str(pg.number)))
                continue
            if b.kind != "Text":
                continue
            for par in b.paragraphs:
                if is_running_head(par, pg) or is_signature(par, pg):
                    continue
                txt = clean(" ".join(l.text for l in par))
                if not txt:
                    continue
                r0 = par[0].runs[0] if par[0].runs else None
                size = float((r0.size or "0.").rstrip(".") or 0) if r0 else 0
                kind, payload = "par", txt
                act_h = _head(txt, ACT_WORDS) if size >= 15 else None
                scene_h = _head(txt, SCENE_WORDS) if 10.5 <= size < 15 else None
                if act_h:
                    kind, payload, zone = "act", str(act_h[0]), True
                elif scene_h:
                    kind, zone = "scene", True
                    payload = f"{scene_h[0]}\t{scene_h[1]}"
                elif zone and size >= 10.5:
                    # The descriptive line under an Act or Scene heading, set
                    # at heading size. It is furniture, not the first
                    # paragraph of the section -- and being all-caps or
                    # title-case it would render as a heading if kept.
                    continue
                elif r0 and r0.italic:
                    # "Nie. (innocently)" -- A TAG AND THE STAGE DIRECTION IT
                    # INTRODUCES ARE ONE ITALIC RUN, so the tag test sees the
                    # whole thing and fails. Forty-odd speeches lose their
                    # speaker that way, and each then reads as a continuation
                    # of the previous speech -- Niemand's evasions delivered
                    # in Minos's voice. Split at the parenthesis, and require
                    # an exact resolve on the part before it so that an
                    # italic aside can never be promoted to a speaker.
                    head = clean(r0.text)
                    lead, aside = head, ""
                    if not looks_like_tag(head) and "(" in head:
                        before, after = head.split("(", 1)
                        lead, aside = before.strip(), "(" + after
                    exact_only = bool(aside)
                    if not looks_like_tag(lead):
                        # THE TERMINAL POINT IS PART OF THE TAG AND THE SCAN
                        # DROPS IT -- "Mhu", "Nie»", and "Euc. '" where the
                        # opening quote of the speech was pulled into the
                        # italic run. Retry on the letters alone, demanding
                        # an exact resolve, which is what stops a one-word
                        # italic emphasis from becoming a speaker.
                        bare = re.sub(r"[^A-Za-z0-9'^`]+$", "", lead).strip()
                        if bare and looks_like_tag(bare + "."):
                            lead, exact_only = bare + ".", True
                    if looks_like_tag(lead):
                        who, dist = tag_speaker(lead)
                        if who and (not exact_only or dist == 0.0):
                            kind = "speech"
                            rest = clean(txt[len(head):]).strip()
                            payload = f"{who}\t{(aside + ' ' + rest).strip()}"
                if kind == "par":
                    # A TAG THE SCAN NEVER MARKED ITALIC AT ALL. The italic
                    # test is what tells a speaker from a numbered Table
                    # item, so give it up only for an EXACT resolve: "Sc."
                    # scores 1.5 to Euclid and "Props." 2.5 to Nostradamus,
                    # and a looser rule turns both into speeches.
                    lead = txt.split(" ", 1)[0]
                    if looks_like_tag(lead) and re.search(r"[A-Za-z]{2}", lead):
                        who, dist = tag_speaker(lead)
                        if who and dist == 0.0:
                            kind = "speech"
                            payload = f"{who}\t{txt[len(lead):].strip()}"
                if kind == "speech" and not payload.split("\t", 1)[1].strip():
                    # A TAG WITH NOTHING AFTER IT. The scan sets Rhadamanthus'
                    # "Rhad." on a line of its own, above the stage direction
                    # "Reads." that introduces the quotation he then reads.
                    # Emitted as a speech it becomes a speaker who says
                    # nothing, and the speech that follows loses its own tag.
                    continue
                if kind in ("par", "speech") and size < 10.5:
                    zone = False
                where.append((kind, payload))
                if kind == "scene" and scene_h[1].startswith("§"):
                    # Four of Act Three's § headings are printed on the same
                    # line as the Scene heading that repeats above them.
                    # Swallowing them with the heading would leave that scene
                    # showing §§ 3 and 4 and not §§ 1, 2, 5 and 6.
                    where.append(("par", scene_h[1]))
    return body, appendix


def sections(items):
    """Split the body at each Act/Scene heading that opens new material.

    THE HEADINGS REPEAT. The printer sets "ACT II. / Scene VI." again at the
    head of every page where a new section of that scene begins (§ 2.
    Pierce, § 3. Willock), so cutting at each Scene heading invents six
    sections the book does not have. Cutting only at Scene headings misses
    Act Four, which carries no Scene heading at all. Cut when the (act,
    scene) PAIR changes, and let an Act heading clear the scene so that
    Act Four still opens one.
    """
    out, cur, act, scene, key = [], [], 1, None, None
    for kind, text in items:
        if kind == "act":
            act, scene = int(text), None
            continue
        if kind == "scene":
            scene = int(text.split("\t", 1)[0])
            continue
        if (act, scene) != key:
            if cur:
                out.append(key + (cur,))
                cur = []
            key = (act, scene)
        cur.append((kind, text))
    if cur:
        out.append(key + (cur,))
    return [s for s in out if any(k != "picture" for k, _ in s[2])]


# The eleven sections the ARGUMENT OF DRAMA lists, in order. Asserted rather
# than trusted: every defect in this book's structure was a heading the scan
# had damaged past recognition, and the damage is silent in both directions
# -- a missed heading welds two scenes together, a spurious one splits one.
EXPECTED_SECTIONS = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
                     (2, 6), (3, 1), (3, 2), (4, None)]


WORDNUM = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
           "Nine", "Ten", "Eleven", "Twelve"]


# A NUMBERED TABLE ITEM CAN LOOK EXACTLY LIKE A SPEAKER TAG. Item 7 of
# Table II opens "7." in italic, which the scan reads as "^7." -- and
# "^7." at page 73 IS a genuine tag of Minos's, resolved by context. The
# tag alone cannot tell them apart; only the fact that the paragraph
# before this one is item 6 can. One case in the whole book, so it is
# corrected by name rather than by loosening the resolver, and prep stops
# if it ever stops matching.
LIST_ITEM_NOT_SPEAKER = [
    ("Minos\tA Pair of Lines, of which one has two points on the same "
     "side of, and not equidistant from, the other, are intersectional.",
     "7. A Pair of Lines, of which one has two points on the same side of, "
     "and not equidistant from, the other, are intersectional."),
]


def unmask_list_items(items):
    out, hits = [], 0
    for kind, text in items:
        for wrong, right in LIST_ITEM_NOT_SPEAKER:
            if kind == "speech" and text == wrong:
                kind, text, hits = "par", right, hits + 1
        out.append((kind, text))
    return out, hits


def render(items):
    out = []
    for kind, text in items:
        if kind == "speech":
            who, body = text.split("\t", 1)
            out.append(f"{who}. {body}")
        elif kind == "picture":
            out.append(f"[Figure p{text}]")
        elif kind == "table":
            out.append(f"[Table p{text}]")
        else:
            out.append(text)
    return out


def split_oversize(paras):
    total = sum(len(p.split()) for p in paras)
    if total <= MAX_WORDS:
        return [paras]
    n = total // MAX_WORDS + 1
    target = total / n
    parts, cur, count = [], [], 0
    for p in paras:
        if cur and count >= target:
            parts.append(cur)
            cur, count = [], 0
        cur.append(p)
        count += len(p.split())
    if cur:
        parts.append(cur)
    return parts


def main():
    if not XML.exists():
        sys.exit("run fetch.sh first")
    body, appendix = read_body_and_appendix()

    # The Appendices are dense cross-reference tables -- lists of Euclid's
    # propositions against a dozen rival manuals -- and go to reference/ as
    # a crib rather than being translated (the bunyan/ ruling on Offor's
    # commentator notes).
    REFERENCE.mkdir(exist_ok=True)
    (REFERENCE / "appendices.txt").write_text(
        "APPENDICES (untranslated crib -- see text_analysis.txt)\n\n"
        + "\n\n".join(render(mend(appendix))) + "\n")

    secs = sections(mend(strip_head_leaks(split_embedded(body))))
    fixed, unmasked = [], 0
    for act, scene, items in secs:
        got, _ = repaired(items)
        got, n = unmask_list_items(got)
        unmasked += n
        fixed.append((act, scene, got))
    if unmasked != len(LIST_ITEM_NOT_SPEAKER):
        sys.exit(f"expected {len(LIST_ITEM_NOT_SPEAKER)} masked list "
                 f"items, matched {unmasked} -- the text has changed")

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()

    got = [(a, s) for a, s, _ in fixed]
    if got != EXPECTED_SECTIONS:
        sys.exit(f"section structure has changed:\n  want {EXPECTED_SECTIONS}"
                 f"\n  got  {got}")

    manifest, idx, opened = [], 0, set()
    for act, scene, items in fixed:
        title = f"Act {WORDNUM[act - 1]}"
        if scene is not None:
            title += f", Scene {WORDNUM[scene - 1]}"
            if (act, scene) in SCENE_TITLE:
                title += f": {SCENE_TITLE[(act, scene)]}"
        chunks = split_oversize(render(items))
        for k, chunk in enumerate(chunks):
            (CHAPTERS / f"{idx:03d}.txt").write_text("\n\n".join(chunk) + "\n")
            e = {"file": f"{idx:03d}.txt", "title": title,
                 "part": k + 1, "of": len(chunks),
                 "words": sum(len(p.split()) for p in chunk)}
            if act not in opened and k == 0:
                e["part_before"] = f"Act {WORDNUM[act - 1]}"
                opened.add(act)
            manifest.append(e)
            idx += 1

    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    total = sum(m["words"] for m in manifest)
    pics = sum(1 for k, _ in body + appendix if k == "picture")
    tabs = sum(1 for k, _ in body + appendix if k == "table")
    print(f"{len(manifest)} files, {total:,} words; "
          f"{pics} plates and {tabs} tables marked for hand work")
    for m in manifest:
        pre = f"  -- {m['part_before']} --\n" if m.get("part_before") else ""
        print(f"{pre}  {m['file']}  {m['words']:6,}w  {m['title']}"
              + (f"  ({m['part']}/{m['of']})" if m["of"] > 1 else ""))


if __name__ == "__main__":
    main()
