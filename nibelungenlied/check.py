"""Book-specific checks for nibelungenlied/ (run from the repo root).

    python3 nibelungenlied/check.py                 source checks only
    python3 nibelungenlied/check.py NNN [NNN ...]   + check those DRAFTS and,
                                                    if clean, write modern_chapters/
    python3 nibelungenlied/check.py --drafts        + every draft that exists
    python3 nibelungenlied/check.py --modern        + every modern file (read only)

THE DRAFT IS THE FILE OF RECORD (the gita pattern). An agent writes
nibelungenlied/drafts/NNN.txt: the English with a strophe marker {N}
(Bartsch's number) at the point where each strophe begins, or {N-M} where
one English sentence must carry several strophes. This script checks the
draft and, ONLY WHEN IT IS CLEAN, writes modern_chapters/NNN.txt with the
markers removed. Never edit modern_chapters/ by hand: --modern fails any
modern file that is not exactly its stripped draft.

What verify.py cannot see, and this checks:

SOURCE (prep.py's output)
  1. Structure against witnesses prep.py did not produce: 39 Aventiuren,
     2,379 strophes (Bartsch's published total), Shumway's and Armour's 39
     Adventures, and -- the real boundary check -- Reichert's diplomatic
     transcription of manuscript B, divided into Aventiuren by a different
     editor: the opening of each B Aventiure must match the opening
     strophe of ours (or the next one in the two places, B_OPENS_LATER,
     where Bartsch's division differs from the manuscript's).
  2. Manifest: "Chapter N: Title" headings 1..39 (assemble.CHAP_LINE), two
     word-form part_before dividers that assemble.PART_LINE cannot match,
     no split files, every strophe exactly four tab-indented lines.

DRAFTS / MODERN
  3. A DROPPED STROPHE. A strophe is ~35 English words; losing one moves a
     file's ratio by about one percent. Every strophe of the Aventiure must
     be marked once, in order; a range covers at most four strophes.
  4. Heading exact (line 1), line 2 blank; prose only (no tab or indented
     lines); no "(Part" marker or "Part ...:" line; no square brackets,
     asterisks, underscores, "#", or "--"; no line ending in a hyphen; no
     paragraph assemble.is_subheading would set as a heading; straight
     quotes (the collection's convention, and must_contain's).
  5. The crib's costume: Shumway made his English "to some extent archaic,
     especially in dialogue" (his preface). With him open all day the
     drift is into his English; the sweep has no exemptions -- if a
     correct sentence fires, add an EXACT PHRASE to ALLOW with the reason.
  6. NAMES (the fleming numeral rule for a text whose numbers are words):
     every name in a file's MHG must appear in the English in its LOCKED
     form (WARNINGS); and none of the unlocked forms (Kriemhilt, "Attila"
     for Etzel, Rudeger, Folker, Troneg, Bechelaren ...) may appear
     (FAILURES).
  7. Ratio: English words / MHG words (tabbed lines only, so the [N]
     lines do not count). PROVISIONAL band; re-derive after file 000.
"""
import difflib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT))
from assemble import CHAP_LINE, PART_LINE, is_subheading  # noqa: E402

AUG = BOOK / "_src" / "augustana"
N_STROPHES = 2379
# Aventiuren where manuscript B does not open on Bartsch's first strophe,
# each read against the pages on 2026-10-10:
#   1: strophe 1 ("Uns ist in alten maeren") is not in B at all; Bartsch
#      prints it from A/C. B opens on 2 ("Ez wuohs in Burgonden").
#   6: B closes Aventiure 5 with 325 ("Iteniuwe maere sich huoben über
#      Rin"); Bartsch moves it to open 6. B's Aventiure 6 opens on 326.
B_OPENS_LATER = {1: 2, 6: 326}

# PROVISIONAL (the dogen rule: derive the band from finished files, never
# from a guess). Shumway's literal prose runs 1.01-1.16 per Aventiure (1.05
# overall). A readable retelling that resolves the formulas and fills in
# what a reader needs runs above a crib. Re-derive from file 000.
MIN_RATIO, MAX_RATIO = 1.0, 1.6

MARK = re.compile(r"\{(\d+)(?:-(\d+))?\}")

ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|ye|unto|ere|"
    r"whilst|amongst|betwixt|methinks|forsooth|yonder|nay|verily|behold|"
    r"wherefore|whence|whither|hither|thither|perchance|o'er|ne'er|'tis|"
    r"'twas|aught|naught|hark|lo|spake|quoth|fain|wot|wist|hight|an'|"
    r"anon|ween|eke|erst|sooth|liege|liegemen|lording|lordings|twain|"
    r"passing (?:bold|fair|good|rich|strong)|full many|many a one|"
    r"gramercy|prithee|mayhap|withal|sithen|thereto|whereof|wherein|"
    r"thereof|herein|morrow|"
    r"wouldst|couldst|shouldst|canst|didst|mayst|mightst|wert|"
    r"knowest|sayest|seest|hearest|art thou|[a-z]+eth)\b", re.I)
# modern words ending in -eth
MODERN_ETH = {"teeth", "death", "breath", "beneath", "seth", "beth",
              "kenneth", "meth", "twentieth", "thirtieth", "fortieth",
              "fiftieth", "sixtieth", "seventieth", "eightieth",
              "ninetieth"}
ALLOW = [
    # exact phrases, each with its reason
]

# LOCKED NAMES: regex on the lowercased MHG (the OTA spelling varies:
# chriemhilt / criemhilt / krimhilt, ezel / ecel) -> the English form. A
# name found in the Aventiure's MHG must appear in the English.
NAMES = {
    r"\bsi[vf]ri[dt]|\bsivride|\bsifride": "Siegfried",
    r"\b(ch|c|k)ri?e?mhil": "Kriemhild",
    r"\bgv(e)?nther|\bgv(e)?ntehern": "Gunther",
    r"\bgernot": "Gernot",
    r"\bgiselher|\bgiseher": "Giselher",
    r"\bhagene": "Hagen",
    r"\bdan(ch|c|k)wart": "Dankwart",
    r"\bo?e?rtewin": "Ortwin",
    r"\bvolker": "Volker",
    r"\b(p|b)rv(n|nn)hil": "Brunhild",
    r"\be[cz]el": "Etzel",
    r"\brv(e|o)?d(e|i)?ger": "Rüdiger",
    r"\bdiet(e)?ri(ch|c)": "Dietrich",
    r"\bhildebran": "Hildebrand",
    r"\bsigemvn": "Siegmund",
    r"\bsigelin": "Sieglinde",
    r"\balbri|\balberi": "Alberich",
    r"\bs(c)?hilbv": "Schilbung",
    r"\bbalmv": "Balmung",
    r"\bgotelin": "Gotelind",
    r"\birin(ch|c|g)\b|\biringe": "Iring",
    r"\birnfri": "Irnfried",
    r"\bhawart": "Hawart",
    r"\bbloedel": "Blödel",
    r"\bwolfhart": "Wolfhart",
    r"\bwerbel": "Werbel",
    r"\bswemmel": "Swemmel",
    r"\bortlie": "Ortlieb",
    r"\bpilgerin|\bpilgrim": "Pilgrim",
    r"\be(ck|kk|k)ewart": "Eckewart",
    r"\brv(o)?molt": "Rumold",
    r"\bliv?deger": "Liudeger",
    r"\bliv?degast": "Liudegast",
    r"\bgel(p)?fr[a]t": "Gelfrat",
    r"\bsindolt": "Sindold",
    r"\bvoten?\b|\bvote\b": "Ute",
    r"\bdan(ch|c|k)rat": "Dankrat",
    r"\bhv(o)?nolt": "Hunold",
    r"\bwormez|\bwormze|\bwormeze": "Worms",
    r"\bsanten\b": "Xanten",
    r"\bisenlant|\bislant": "Isenland",
    r"\bbechelaren": "Pöchlarn",
    r"\bwienne": "Vienna",
    r"\bpazzo?we": "Passau",
    r"\b(von|uon|ze|ce) berne?\b": "Bern",
    r"\bnibelvng": "Nibelung",
}
# Unlocked forms that must not appear (other translators' spellings).
BANNED = [
    r"\bKriemhilt\b", r"\bChriemhild\b", r"\bSigfrid\b", r"\bSiegfrid\b",
    r"\bSivrit\b", r"\bBrünhild\b", r"\bBrunhilda\b", r"\bBrunhilde\b",
    r"\bAttila\b", r"\bRudeger\b", r"\bRudiger\b", r"\bRüdeger\b",
    r"\bFolker\b", r"\bTroneg\b", r"\bTroneck\b", r"\bTronege\b",
    r"\bBechlaren\b", r"\bBechelaren\b", r"\bGiselher the youth\b",
    r"\bUta\b", r"\bDancrat\b", r"\bBloedel\b",
    r"\bBloedelin\b", r"\bIceland\b", r"\bNibelungs' hoard\b",
    r"\btarnkappe\b", r"\bTarnkappe\b", r"\bhightide\b", r"\bhigh tide\b",
]

fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("æ", "ae").replace("œ", "oe")
    s = re.sub(r"[uw]", "v", s)
    s = re.sub(r"ch|c|k", "k", s)
    s = re.sub(r"[^a-z ]", "", s)
    return " ".join(s.split())


def load_source():
    manifest = json.loads((BOOK / "manifest.json").read_text(encoding="utf-8"))
    strophes = {}
    for e in manifest:
        txt = (BOOK / "chapters" / e["file"]).read_text(encoding="utf-8")
        for blk in txt.strip().split("\n\n"):
            head, *lines = blk.split("\n")
            n = int(head.strip("[]"))
            strophes[n] = (e["file"], lines)
    return manifest, strophes


def b_openings():
    """First strophe of each Aventiure in Reichert's diplomatic B."""
    out = []
    for i in range(1, 40):
        t = (AUG / f"nib_b_{i:02d}.html").read_text(encoding="utf-8")
        t = t[t.index("Aventiure"):]
        lines = re.findall(r"<h3[^>]*>(.*?)</h3>", t, re.S)
        lines = [" ".join(html.unescape(re.sub(r"<[^>]+>", "", l)).split())
                 for l in lines]
        out.append(" ".join(lines[:2]))
    return out


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b), autojunk=False).ratio()


def check_source(manifest, strophes):
    # counts
    if len(manifest) != 39:
        fail(f"{len(manifest)} files, expected 39 Aventiuren")
    if sorted(strophes) != list(range(1, N_STROPHES + 1)):
        fail("strophes are not exactly 1..2379")
    for n, (f, lines) in strophes.items():
        if len(lines) != 4 or not all(l.startswith("\t") for l in lines):
            fail(f"{f}: strophe {n} is not four tab-indented lines")
    # Shumway / Armour: 39 each (prep slices them; recount here from scratch)
    shum = (BOOK / "_src" / "pg1151.txt").read_text(encoding="utf-8")
    n_shum = len(re.findall(r"^ADVENTURE [IVXL]+\b", shum, re.M))
    arm = (BOOK / "_src" / "pg3636.txt").read_text(encoding="utf-8")
    n_arm = len(re.findall(r"^\w+(?:-\w+)? Adventure\s*$", arm, re.M))
    print(f"witness counts: Shumway {n_shum} Adventures, Armour {n_arm} Adventures")
    if n_shum != 39 or n_arm != 39:
        fail("a crib does not have 39 Adventures")
    # B boundaries
    bo = b_openings()
    worst = 1.0
    for e, b in zip(manifest, bo):
        i = e["aventiure"]
        first = e["strophes"][0]
        want = B_OPENS_LATER.get(i, first)
        cands = {n: similarity(b, " ".join(strophes[n][1][:2]))
                 for n in range(max(1, first - 2), min(N_STROPHES, first + 3) + 1)}
        best = max(cands, key=cands.get)
        worst = min(worst, cands[want])
        if best != want:
            fail(f"Aventiure {i}: B opens like strophe {best} "
                 f"({cands[best]:.2f}), expected {want} ({cands[want]:.2f})")
    print(f"B witness: 39 Aventiure openings agree "
          f"(lowest similarity {worst:.2f})" if not fails else "")
    # manifest headings and dividers
    dividers = [e for e in manifest if e.get("part_before")]
    if [d["file"] for d in dividers] != ["000.txt", "019.txt"]:
        fail("part dividers must sit before 000 and 019")
    for d in dividers:
        if PART_LINE.match(d["part_before"]) or not re.match(
                r"^Part (One|Two): ", d["part_before"]):
            fail(f"divider {d['part_before']!r} not in word form")
    for k, e in enumerate(manifest, 1):
        m = CHAP_LINE.match(e["title"])
        if not m or int(m.group(1)) != k:
            fail(f"{e['file']}: title {e['title']!r} is not 'Chapter {k}: ...'")
        if (e["part"], e["of"]) != (1, 1):
            fail(f"{e['file']}: unexpected split")


def strip_markers(text):
    text = re.sub(r"\{\d+(?:-\d+)?\} ?", "", text)
    return "\n".join(l.rstrip() for l in text.split("\n"))


def mhg_words(src):
    return sum(len(l.split()) for l in src.split("\n") if l.startswith("\t"))


def check_text(e, text, say, draft=False):
    """Checks 4-6 on a draft (markers present) or a modern file."""
    lines = text.split("\n")
    if lines[0] != e["title"]:
        say.append(f"line 1 is {lines[0]!r}; the manifest says {e['title']!r}")
    if len(lines) < 3 or lines[1].strip():
        say.append("line 2 must be blank (no part marker: one file per Aventiure)")
    body = "\n".join(lines[2:])
    for i, ln in enumerate(lines, 1):
        if ln.startswith("\t") or ln.startswith("    "):
            say.append(f"indented line {i}: the edition is prose")
            break
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if re.match(r"^\(Part \d", s) or re.match(r"^Part \w+:", s):
            say.append(f"line {i}: stray part line {s[:40]!r}")
        if s.endswith("-") and not s.endswith("--"):
            say.append(f"line {i} ends in a hyphen: the renderers join it as 'x- y'")
    if "--" in text:
        say.append("double hyphen: use a real em dash ( — )")
    if re.search(r"[\[\]*_<>#]", text):
        say.append("markup character ([ ] * _ < > #): the edition is plain prose")
    if re.search("[‘’“”]", text):
        say.append("curly quotes: the collection uses straight ' and \"")
    if not draft and MARK.search(text):
        say.append("strophe marker left in a modern file")
    plain = MARK.sub("", body)
    paras = [" ".join(p.split()) for p in plain.split("\n\n") if p.strip()]
    for par in paras:
        if len(par) > 3 and par == par.upper() and any(c.isalpha() for c in par):
            say.append(f"all-caps paragraph renders as a heading: {par[:50]}")
        elif is_subheading(par):
            say.append(f"paragraph renders as a subheading: {par[:60]}")
    flat = " ¶ ".join(paras)
    for m in ARCHAIC.finditer(flat):
        w = m.group(0).lower()
        if w in MODERN_ETH:
            continue
        ctx = flat[max(0, m.start() - 60):m.end() + 60]
        if any(ok in ctx for ok in ALLOW):
            continue
        say.append(f"archaism {m.group(0)!r}: ...{flat[max(0, m.start()-30):m.end()+30]}...")
    for pat in BANNED:
        for m in re.finditer(pat, flat):
            say.append(f"unlocked form {m.group(0)!r}: ...{flat[max(0, m.start()-30):m.end()+30]}...")


def names_warnings(e, src, text):
    verse = " ".join(l for l in src.lower().split("\n") if l.startswith("\t"))
    return [eng for pat, eng in NAMES.items()
            if re.search(pat, verse) and eng not in text]


def check_draft(e, write):
    f = e["file"]
    src = (BOOK / "chapters" / f).read_text(encoding="utf-8")
    draft = (BOOK / "drafts" / f).read_text(encoding="utf-8")
    say = []
    check_text(e, draft, say, draft=True)
    body = "\n".join(draft.split("\n")[2:])
    a0, a1 = e["strophes"]
    seq = []
    for m in MARK.finditer(body):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if b < a or b - a > 3:
            say.append(f"odd range marker {m.group(0)} (at most four strophes)")
        seq.extend(range(a, b + 1))
    want = list(range(a0, a1 + 1))
    if seq != want:
        missing = sorted(set(want) - set(seq))
        dup = sorted({x for x in seq if seq.count(x) > 1})
        extra = sorted(set(seq) - set(want))
        order = [f"{x}>{y}" for x, y in zip(seq, seq[1:]) if y != x + 1][:5]
        say.append(f"strophe markers: missing {missing[:12]}, repeated {dup[:12]}, "
                   f"outside this Aventiure {extra[:12]}, out of order at {order}")
    for m in MARK.finditer(body):
        before = body[m.start() - 1] if m.start() else "\n"
        after = body[m.end()] if m.end() < len(body) else ""
        if not before.isspace() or after != " ":
            say.append(f"marker {m.group(0)} needs whitespace before it and one space after")
    if re.search(r"[{}]", MARK.sub("", body)):
        say.append("a brace that is not a well-formed marker {N} or {N-M}")
    clean = strip_markers(draft)
    text = "\n".join(clean.split("\n")[2:])
    r = len(text.split()) / max(1, mhg_words(src))
    if not MIN_RATIO <= r <= MAX_RATIO:
        say.append(f"ratio {r:.2f} outside {MIN_RATIO}-{MAX_RATIO} "
                   f"({len(text.split())} English / {mhg_words(src)} MHG words; "
                   f"Shumway {e['shumway_words'] / e['mhg_words']:.2f})")
    warn = names_warnings(e, src, clean)
    mp = BOOK / "modern_chapters" / f
    if not say and write:
        mp.parent.mkdir(exist_ok=True)
        mp.write_text(clean, encoding="utf-8")
    if mp.exists() and mp.read_text(encoding="utf-8") != clean:
        say.append("modern_chapters file differs from the stripped draft: edit the "
                   "DRAFT and rerun, never modern_chapters/")
    return say, r, warn


def check_modern(manifest):
    for e in manifest:
        f = e["file"]
        mp = BOOK / "modern_chapters" / f
        if not mp.exists():
            continue
        say = []
        text = mp.read_text(encoding="utf-8")
        check_text(e, text, say)
        dp = BOOK / "drafts" / f
        if not dp.exists():
            say.append("modern file with no draft behind it")
        elif strip_markers(dp.read_text(encoding="utf-8")) != text:
            say.append("differs from its stripped draft (hand edit?)")
        src = (BOOK / "chapters" / f).read_text(encoding="utf-8")
        for s in say:
            fail(f"{f}: {s}")
        w = names_warnings(e, src, text)
        if w:
            print(f"  WARN {f}: names in the MHG absent from the English: {w}")


def main(argv):
    manifest, strophes = load_source()
    check_source(manifest, strophes)
    by_num = {e["file"][:3]: e for e in manifest}
    want = [a for a in argv[1:] if not a.startswith("--")]
    if want or "--drafts" in argv:
        files = want or sorted(p.name[:3] for p in (BOOK / "drafts").glob("*.txt"))
        for k in files:
            e = by_num[k]
            if not (BOOK / "drafts" / e["file"]).exists():
                fail(f"{e['file']}: no draft at nibelungenlied/drafts/{e['file']}")
                continue
            say, r, warn = check_draft(e, write=True)
            for s in say:
                fail(f"{e['file']}: {s}")
            if not say:
                print(f"{e['file']}: ok (ratio {r:.2f}); modern_chapters/{e['file']} written")
            if warn:
                print(f"  WARN {e['file']}: names in the MHG absent from the English: {warn}")
    if "--modern" in argv:
        check_modern(manifest)
    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
