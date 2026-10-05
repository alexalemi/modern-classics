"""Vannevar Bush, Science, the Endless Frontier (Government Printing Office,
July 1945) -> chapters/ and modern_chapters/ (a RESTORED EDITION).

    python3 endless/prep.py [--report]

A US government work, public domain. No clean transcription exists, so the
words are voted from three OCRs:

A  ABBYY layout of the 1945 GPO printing (Archive.org scienceendlessfr00unit_0;
   endless/abbyy.py): the base, and the only source of structure -- headings
   by type size, paragraphs by first-line indent, italics.
B  djvu text of the National Science Foundation's 1960 reprint
   (scienceendlessfr00unit), a separate setting of the same words.
C  djvu text of a second scan of the 1945 printing (Digital Library of
   India, in.ernet.dli.2015.212068), noisy; a tie-breaker.

A token of A is replaced when B and C agree against it, or when A's word is
not a word and B's is (a lone 1960 reading never overrides a real 1945
word). What is left is listed by --report and settled in FIXES from the
1945 page images (_src/scan_jp2.zip).

Kept: the letter of transmittal, Roosevelt's letter, the summary, the six
chapters, the organisation chart, and Appendix 1 (the committees consulted).
Omitted: Appendices 2-5, the four committee reports (some 65,000 words of
supporting evidence, with tables), as the introduction says.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import abbyy  # noqa: E402
from scan_diff import opcodes  # noqa: E402

FIRST, LAST = 7, 51            # leaves of the main report and Appendix 1
EPIGRAPH = 11                  # the half-title with Roosevelt's sentence
CHART = 42                     # the organisation chart
SECTIONS = [  # (opening heading as printed, file title)
    ("LETTER OF TRANSMITTAL", "Letter of Transmittal"),
    ("PRESIDENT ROOSEVELT’S LETTER", "President Roosevelt’s Letter"),
    ("SUMMARY OF THE REPORT", "Summary of the Report"),
    ("INTRODUCTION", "Chapter 1: Introduction"),
    ("THE WAR AGAINST DISEASE", "Chapter 2: The War Against Disease"),
    ("SCIENCE AND THE PUBLIC WELFARE", "Chapter 3: Science and the Public Welfare"),
    ("RENEWAL OF OUR SCIENTIFIC TALENT", "Chapter 4: Renewal of Our Scientific Talent"),
    ("A PROBLEM OF SCIENTIFIC RECONVERSION", "Chapter 5: A Problem of Scientific Reconversion"),
    ("THE MEANS TO THE END", "Chapter 6: The Means to the End"),
    ("COMMITTEES CONSULTED", "Appendix 1: Committees Consulted"),
]
# readings settled on the 1945 page images: (old, new), each must match once
FIXES = [
    # letterheads: one line each, as in Sabotage's memorandum
    ("Office of Scientific Research and Development\n\n1530 P Street, NW.\n\nWashington 25, D. C.\n\nJuly 5, 1945.",
     "Office of Scientific Research and Development · 1530 P Street, NW. · Washington 25, D. C. · July 5, 1945."),
    ("The White House *Washington D. C.*\n\n*November 17, 1944*", "The White House · Washington, D. C. · November 17, 1944."),
    ("(s) V. Bush, *Director.*", "(s) V. Bush, *Director*."),
    ("your considered * judgment", "your considered judgment"), ("with our* allies", "with our allies"),
    ("on a level i comparable", "on a level comparable"),
    ("and new' industries", "and new industries"),       # scan specks, not print
    ("a human one.'We shall", "a human one. We shall"),
    ("benefit of the general public.’", "benefit of the general public."),
    ("pioneered | with", "pioneered with"), ("with | your", "with your"),
    ("research'in", "research in"),
    ("employment and a 1 fuller and more fruitful life. 1", "employment and a fuller and more fruitful life."),
    ("as a nation in the modern world\n", "as a nation in the modern world.\n"),
    ("fuller and more fruitful life.”—\n", "fuller and more fruitful life.”\n"),
    ("battlefronts aU over", "battlefronts all over"),
    ("ForO ur National Security", "For Our National Security"),
    ("would has^e received", "would have received"),
    ("more than one^third", "more than one-third"),
    ("by its own^ clearly", "by its own, clearly"),
    ("applied research—^have", "applied research—have"),
    ("(5) ^While", "(5) While"),
    ("and {h) from", "and (b) from"),
    ("and (6) by strengthening", "and (b) by strengthening"),
    ("to|fight|successfully", "to fight successfully"),
    ("Relation to National Security ^", "Relation to National Security"),
    ("during the war. ^", "during the war."),
    ("must be responsibile to", "must be responsible to"),   # the printer's misprint (RESTORED.md)
    ("Industry is ordy", "Industry is only"), ("source of fimds", "source of funds"),
    ("year shoidd not", "year should not"),
    ("President Conant s statement", "President Conant’s statement"),
    ("militarily possi-1)1 e,", "militarily possible,"),
    ("war-time Ofl&ce", "war-time Office"), ("of the Ofilce of", "of the Office of"),
    ("of the OjQfice of", "of the Office of"),
    ("Action by Consress\n\nTJie National", "Action by Congress\n\nThe National"),
    ("professional Divi-\n\n. sions to be", "professional Divisions to be"),
    ("1. *Purposes*.—", "I. *Purposes*.—"),
    ("\n\nа. To formulate", "\n\na. To formulate"), ("\n\nб. To establish", "\n\nb. To establish"),
    ("*h. Division of Natural Sciences.*", "*b. Division of Natural Sciences.*"),
    ("\n\nh. Recommendation regarding", "\n\nb. Recommendation regarding"),
    ("\n\n/. To review", "\n\nf. To review"), ("\n\n/. Presentation", "\n\nf. Presentation"),
    ("\n\n0. To devise", "\n\no. To devise"),
    ("*The Divisions should he responsible", "*The Divisions should be responsible"),
    ("during the stress of the present war * *", "during the stress of the present war * * *."),
    ("statement that:\n\n* * in every section", "statement that:\n\n“* * * in every section"),
    ("Id planning the release", "In planning the release"),
    ("fighting the war in,the", "fighting the war in the"), ("against time, - the", "against time, the"),
    ("authorization so , that", "authorization so that"), ("healthy manner , from", "healthy manner from"),
    ("functions, -powers, and", "functions, powers, and"),
    ("of the military (‘establishment", "of the military establishment"),
    ("our future as a nation;\n\nAppendices\n", "our future as a nation.\n"),
    ("chairman of the • National", "chairman of the National"),
    # the budget table (printed page 33), typed from the image
    ("reached a fairly stable level:\n\nAction by Congress",
     "reached a fairly stable level:\n\n"
     "\tActivity | First year (millions of dollars) | Fifth year (millions of dollars)\n"
     "\tDivision of Medical Research | $5.0 | $20.0\n"
     "\tDivision of Natural Sciences | 10.0 | 50.0\n"
     "\tDivision of National Defense | 10.0 | 20.0\n"
     "\tDivision of Scientific Personnel and Education | 7.0 | 29.0\n"
     "\tDivision of Publications and Scientific Collaboration | .5 | 1.0\n"
     "\tAdministration | 1.0 | 2.5\n"
     "\tTotal | 33.5 | 122.5\n\nAction by Congress"),
    # Appendix 1: the questions open and close on double quotation marks
    ("^^With particular reference", "“With particular reference"),
    ("related sciences?’^", "related sciences?”"),
    ("carefully considered.’^", "carefully considered.”"),
    ("‘^Can an effective", "“Can an effective"),
    ("^^What can be done, consistent", "“What can be done, consistent"),
    ("scientific knowledge?'^", "scientific knowledge?”"),
]
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}
FURNITURE = re.compile(r"^[\dIVXLCivxlc\s,.|'’-]*$|^\d{6}—45$")


def key(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def is_word(k):
    return k.isdigit() or k in DICT or k.rstrip("s") in DICT or (k.endswith("ed") and k[:-2] in DICT) \
        or (k.endswith("ing") and k[:-3] in DICT) or (k.endswith("ly") and k[:-2] in DICT)


# ---------------------------------------------------------------- A: structure
def layout():
    """[(kind, text)] for the leaves of the report: H (heading), P, CHAPNUM."""
    out, leaves = [], {}
    for leaf, ps in abbyy.pages():
        if FIRST <= leaf <= LAST:
            leaves[leaf] = ps
        if leaf > LAST:
            break
    for leaf in range(FIRST, LAST + 1):
        first_body = True
        for p in leaves[leaf]:
            t = p["text"].strip()
            if not re.search(r"[A-Za-z]{2}", t) or FURNITURE.match(t) or p["size"] < 9:
                continue
            if leaf == CHART and t.startswith("PROPOSED ORGANIZATION"):
                out.append(("CHART", t))
                continue
            if leaf == EPIGRAPH:
                out.append(("EPI", t))
                continue
            plain = t.replace("*", "")
            if re.fullmatch(r"(Chapter|Appendix) \d+", plain):
                out.append(("NUM", plain))
                continue
            short = len(plain.split()) <= 10 and plain[-1] not in ".,:;—"
            known = re.sub(r"[^a-z]", "", plain.lower()) in {re.sub(r"[^a-z]", "", h.lower()) for h, _ in SECTIONS}
            if p["size"] >= 15 and (known or (p["indent"] <= 0 and short and p["left"] < 5000)):
                out.append(("H", plain))
                first_body = False
                continue
            if p["bold"] >= 0.99:
                t = "**" + t.replace("**", "") + "**"
            elif p["bold"] > 0:
                print(f"leaf {leaf}: partly bold ({p['bold']:.2f}): {t[:70]}", file=sys.stderr)
            # a page that opens on an unindented line continues the paragraph
            # (a page that opens unindented), or a last line the OCR set
            # apart as a paragraph of its own (unindented, lower case)
            if out and out[-1][0] == "P" and p["indent"] <= 0 and (
                    (first_body and not re.search(r"[.:?!”\"]$", out[-1][1])) or
                    (t[0].islower() and not re.search(r"[.:?!”\"]\**$", out[-1][1]))):
                prev = out[-1][1]
                if prev.endswith("**") and t.startswith("**"):
                    prev, t = prev[:-2], t[2:]
                out[-1] = ("P", prev[:-1] + "\u00ad" + t if re.search(r"[a-z]-$", prev) else prev + " " + t)
            else:
                out.append(("P", t))
            first_body = False
    return [(k, soft_hyphens(t)) for k, t in out]


def soft_hyphens(t):
    """Settle each line-end join: a word closes up ("possi-ble"); two words
    keep the hyphen ("civilian-controlled", "well-being")."""
    def one(m):
        x, y = m.group(1), m.group(2)
        if is_word((x + y).lower()) or not (is_word(x.lower()) and is_word(y.lower())):
            return x + y
        return x + "-" + y
    t = re.sub(r"([A-Za-z]+)\u00ad([A-Za-z]+)", one, t)
    return t.replace("\u00ad", "-")


# ---------------------------------------------------------------- B, C: witnesses
def witness(name):
    s = (HERE / "_src" / name).read_text(errors="replace")
    s = re.sub(r"(\w)[¬-]\s*\n\s*(\w)", r"\1\2", s)
    return [m.group(0).lower() for m in re.finditer(r"[A-Za-z0-9]+", s)]


def aligned(ak, bk):
    m = {}
    for tag, i1, i2, j1, j2 in opcodes(ak, bk):
        if tag == "equal":
            for d in range(i2 - i1):
                m[i1 + d] = j1 + d
    return m


def reading(m, i1, i2, w):
    """The witness's keys for A's [i1, i2), if both ends anchor."""
    if (i1 - 1) not in m or i2 not in m:
        return None
    return w[m[i1 - 1] + 1:m[i2]]


VOTED = ("P", "H", "EPI")
BRITISH = {"endeavour", "labour", "honour", "favour", "colour", "behaviour"}


def vote(blocks, report):
    """Vote A's letter runs (keys) against B and C. A key is a run of
    letters or digits inside a block; a change rewrites only those letters,
    so A's punctuation, dashes and italic stars stand."""
    keys = []                      # (block, start, end, key)
    for bi, (kind, text) in enumerate(blocks):
        if kind in VOTED:
            for m in re.finditer(r"[A-Za-z0-9]+", text):
                keys.append((bi, m.start(), m.end(), m.group(0).lower()))
    ak = [k[3] for k in keys]
    bk, ck = witness("scienceendlessfr00unit_djvu.txt"), witness("dli_djvu.txt")
    mc = aligned(ak, ck)
    changes, conflicts = [], []
    for tag, i1, i2, j1, j2 in opcodes(ak, bk):
        if tag == "equal" or i2 == i1 or j2 == j1:
            continue                   # B adds or lacks words: A is the base
        if len({keys[i][0] for i in range(i1, i2)}) > 1:
            conflicts.append((i1, i2, bk[j1:j2], None))
            continue
        a_rd, b_rd = ak[i1:i2], bk[j1:j2]
        c_rd = reading(mc, i1, i2, ck)
        if c_rd == a_rd or (all(is_word(x) for x in a_rd) and not all(is_word(y) for y in b_rd)):
            continue                   # the two 1945 copies agree, or B is the misreading
        if c_rd == b_rd:
            why = "B=C"
        elif "".join(a_rd) == "".join(b_rd) and len(b_rd) < len(a_rd) and is_word("".join(b_rd)) \
                and "-" not in blocks[keys[i1][0]][1][keys[i1][1]:keys[i2 - 1][2]]:
            why = "join"
        elif len(a_rd) == len(b_rd) and all(not is_word(x) and is_word(y) and x not in BRITISH for x, y in zip(a_rd, b_rd)):
            why = "nonword"
        else:
            conflicts.append((i1, i2, b_rd, c_rd))
            continue
        changes.append((i1, i2, b_rd, why))
    for i1, i2, b_rd, why in sorted(changes, reverse=True):
        bi, start, end = keys[i1][0], keys[i1][1], keys[i2 - 1][2]
        text = blocks[bi][1]
        old = text[start:end]
        new = " ".join(b_rd)
        # B's case is lost to the key; take A's capitalisation pattern
        if old[:1].isupper():
            new = new[:1].upper() + new[1:]
        if old.isupper() and len(old) > 1:
            new = new.upper()
        blocks[bi] = (blocks[bi][0], text[:start] + new + text[end:])
        if report == "changes":
            print(f"{why:8} {old!r} -> {new!r}")
    if report == "conflicts":
        for i1, i2, b, c in conflicts:
            ctx = " ".join(ak[max(0, i1 - 5):i1])
            print(f"A={' '.join(ak[i1:i2])!r:28} B={' '.join(b)!r:28} C={' '.join(c) if c is not None else None!r:24} | {ctx}")
    return blocks, len(changes), len(conflicts)


def cut_chart():
    """The organisation chart (printed page 30), from the 1945 page image,
    with the verso's show-through cleared by a levels curve (the chart is
    black line art on white)."""
    from PIL import Image
    out = HERE.parent / "site/images/endless/figchart.jpg"
    if out.exists():
        return
    import zipfile, io
    with zipfile.ZipFile(HERE / "_src/scan_jp2.zip") as z:
        im = Image.open(io.BytesIO(z.read(f"scienceendlessfr00unit_0_jp2/scienceendlessfr00unit_0_{CHART:04d}.jp2")))
    c = im.convert("L").crop((400, 1230, 2600, 4010))
    c = c.point(lambda v: 255 if v > 150 else max(0, int((v - 40) * 255 / 110)))
    out.parent.mkdir(parents=True, exist_ok=True)
    c.save(out, quality=88)


def titlecase(s):
    small = {"a", "an", "the", "of", "to", "in", "on", "and", "for", "at", "by"}
    if s.upper() != s:
        return s
    ws = s.lower().split()
    out = [w if (w in small and 0 < i < len(ws) - 1) else w.capitalize() for i, w in enumerate(ws)]
    return " ".join(out).replace("’S", "’s")


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def sections(blocks):
    heads = {norm(h): t for h, t in SECTIONS}
    out, cur = [], None
    epi = []
    for kind, text in blocks:
        if kind == "H" and norm(text) in heads and (cur is None or cur[0] != heads[norm(text)]):
            cur = (heads[norm(text)], [])
            out.append(cur)
            if cur[0] == "Summary of the Report" and epi:
                cur[1].extend(epi)
            continue
        if kind == "EPI":
            plain = text.replace("*", "")
            if norm(plain) == "sciencetheendlessfrontier":
                continue
            if plain.startswith("“"):
                epi.append(text)
            elif "Roosevelt" in plain:
                epi.append("—Franklin D. Roosevelt, November 17, 1944.")
            continue
        if kind == "NUM":
            continue
        if kind == "CHART":
            cur[1].append("[Figure chart]")
            continue
        if kind == "H":
            cur[1].append(titlecase(text))
            continue
        if cur[0].startswith("Appendix"):
            # one member per paragraph: the OCR runs some entries together
            # and reads the commas inside an entry as full stops ("professor
            # of medicine. Harvard University"): the page images print commas
            for e in re.split(r"(?<=\.) (?=(?:Dr|Mr|Rev|Col|Gen|Adm)\. [A-Z])", text):
                m = re.match(r"(Dr|Mr|Rev|Col)\. ", e)
                if m:
                    e = m.group(0) + re.sub(r"(?<=[a-z]{2})\. (?=[A-Z])", ", ", e[m.end():])
                cur[1].append(e)
            continue
        cur[1].append(text)
    return out


def suspects(secs):
    seen = {}
    for title, paras in secs:
        for p in paras:
            for w in re.findall(r"[A-Za-z][A-Za-z’']*", p):
                k = w.lower().strip("’'")
                k = re.sub(r"[’']s$", "", k)
                if not is_word(k) and not w[0].isupper():
                    seen.setdefault(w, p[max(0, p.find(w) - 30):p.find(w) + 30])
                elif w[0].isupper() and not is_word(k) and len(w) > 1:
                    seen.setdefault(w, p[max(0, p.find(w) - 30):p.find(w) + 30])
    return seen


def main():
    report = sys.argv[1].lstrip("-") if len(sys.argv) > 1 else None
    blocks, nch, ncf = vote(layout(), report)
    print(len(blocks), "blocks;", nch, "votes taken;", ncf, "conflicts left", file=sys.stderr)
    secs = sections(blocks)
    assert [t for t, _ in secs] == [t for _, t in SECTIONS], [t for t, _ in secs]
    used = set()
    texts = []
    for title, paras in secs:
        text = title + "\n\n" + "\n\n".join(paras) + "\n"
        for old, new in FIXES:
            n = text.count(old)
            if n:
                assert n == 1, (old, n)
                text = text.replace(old, new)
                used.add(old)
        texts.append((title, text))
    unused = [o for o, _ in FIXES if o not in used]
    assert not unused, unused
    if report == "suspects":
        for w, ctx in sorted(suspects([(t, x.split("\n\n")) for t, x in texts]).items()):
            print(f"{w:20} | {ctx}")
        return
    cut_chart()
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for i, (title, text) in enumerate(texts):
        (HERE / f"chapters/{i:03d}.txt").write_text(text)
        (HERE / f"modern_chapters/{i:03d}.txt").write_text(text.replace("[Figure chart]", "[Figure chart: " + CHART_CAPTION + "]"))
        manifest.append({"file": f"{i:03d}.txt", "title": title, "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(len(texts), "sections,", sum(len(t.split()) for _, t in texts), "words")


CHART_CAPTION = ("Proposed Organization of National Research Foundation — An organization chart. At the top, "
                 "the National Research Foundation and its Members; below them a Director, with Staff Offices "
                 "(general counsel, finance officer, administrative planning, personnel) to one side. Under the "
                 "Director stand five Divisions, each with its own members and an executive officer: Medical "
                 "Research, Natural Sciences, National Defense, Scientific Personnel and Education, and "
                 "Publications and Scientific Collaboration.")


if __name__ == "__main__":
    main()
