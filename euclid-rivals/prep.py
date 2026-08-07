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


ACT = re.compile(r"^ACT\s*([IVXL]+)\.?$", re.I)
SCENE = re.compile(r"^Scene\s*([IVXL]+)\.?$", re.I)
APPENDIX = re.compile(r"^APPENDIX\s*([IVXL]*)\.?$", re.I)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "L": 1}          # the scan reads "ACT I." as "ACT L." twice


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
    for pg in pages(XML):
        if pg.number in DUPLICATE_PAGES or not pg.blocks:
            continue
        where = body if pg.number < APPENDIX_FIRST else appendix
        if pg.number < BODY_FIRST:
            continue
        for b in pg.blocks:
            if b.kind == "Picture" and (b.right - b.left) < pg.width * 0.95:
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
                if size >= 15 and ACT.match(txt.strip()):
                    kind, payload = "act", ACT.match(txt.strip()).group(1)
                elif 10.5 <= size < 15 and SCENE.match(txt.strip()):
                    kind, payload = "scene", SCENE.match(txt.strip()).group(1)
                elif r0 and r0.italic and looks_like_tag(clean(r0.text)):
                    who, _ = resolve(clean(r0.text))
                    if who:
                        kind = "speech"
                        payload = f"{who}\t{clean(txt[len(clean(r0.text)):])}"
                where.append((kind, payload))
    return body, appendix


def sections(items):
    """Split the body at each Act/Scene heading that opens new material."""
    out, cur, act, scene = [], [], None, None
    for kind, text in items:
        if kind == "act":
            act = text
            continue
        if kind == "scene":
            # A repeated Act heading with no new Scene is a divider page,
            # not a new section.
            if cur:
                out.append((act, scene, cur))
            cur, scene = [], text
            continue
        cur.append((kind, text))
    if cur:
        out.append((act, scene, cur))
    return [s for s in out if any(k != "picture" for k, _ in s[2])]


WORDNUM = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
           "Nine", "Ten", "Eleven", "Twelve"]


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

    secs = sections(mend(body))
    fixed = []
    for act, scene, items in secs:
        got, _ = repaired(items)
        fixed.append((act, scene, got))

    CHAPTERS.mkdir(exist_ok=True)
    for f in CHAPTERS.glob("*.txt"):
        f.unlink()

    manifest, idx, seen = [], 0, {}
    for act, scene, items in fixed:
        a = ROMAN.get((act or "I").upper(), 1)
        seen[a] = seen.get(a, 0) + 1
        title = f"Act {WORDNUM[a - 1]}, Scene {WORDNUM[seen[a] - 1]}"
        chunks = split_oversize(render(items))
        for k, chunk in enumerate(chunks):
            (CHAPTERS / f"{idx:03d}.txt").write_text("\n\n".join(chunk) + "\n")
            e = {"file": f"{idx:03d}.txt", "title": title,
                 "part": k + 1, "of": len(chunks),
                 "words": sum(len(p.split()) for p in chunk)}
            if seen[a] == 1 and k == 0:
                e["part_before"] = f"Act {WORDNUM[a - 1]}"
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
