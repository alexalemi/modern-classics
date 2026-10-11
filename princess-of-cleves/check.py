"""Book-specific checks for princess-of-cleves/ (run from the repo root).

    python3 princess-of-cleves/check.py            # source checks only
    python3 princess-of-cleves/check.py --modern   # + translated files

What verify.py cannot see here (memory notes: silent defect classes;
checks that cannot see a missing section; manifest-less books lose text):

SOURCE (prep.py's output)
  1. THE BOOK'S OWN STRUCTURE, read from the raw Wikisource pages, not from
     prep.py: Lepetit closes each work with a "fin de la ..." line -- four
     for Clèves ("première", "seconde", "troisième", "quatrième et
     dernière") and one for Montpensier. All five, in that order. The
     second witness agrees: Gutenberg #20262 has four PARTIE headings.
  2. Manifest: 15 files; sections in order [The Publisher to the Reader,
     Part One..Four, The Princess of Montpensier]; part n of k contiguous
     and complete in every group; one part_before ("The Princess of
     Cleves", on 000) and nothing matching assemble.PART_LINE; titles in
     WORD form; "chapter": true on the first file of each Part.
  3. COMPLETENESS AGAINST THE RAW PAGES: the files of each Part, joined,
     are letter for letter the text of that Wikisource page minus
     Lepetit's title and "fin" lines (read here from the HTML with a
     parser independent of prep.py's), and Montpensier likewise.
  4. SECOND WITNESS: Gutenberg #20262 (Sledd & Gorrell 1896) is a school
     abridgement, so the check is ONE-WAY: every Gutenberg word must
     sit in some 6-word run that also occurs in ours (spelling normalised: accents,
     oi/ai, hyphens). A Gutenberg run absent from ours FAILS (a loss in
     our text); the passages ours has and Gutenberg lacks are its cuts
     and are only counted.
  5. Size: every file <= 6,000 French words (one agent's output).
  6. Cribs: reference/001-014 exist; crib/French ratios printed.

MODERN (modern_chapters/, once they exist)
  7. Line 1 is exactly the manifest title. In a split group EVERY file
     opens on the title line and then "(Part n of k)" (the
     twenty-thousand-leagues convention): assemble.strip_front drops the
     first line of every file of a group, so a part that opens on prose
     loses that sentence. Single files carry no marker.
  8. No divider lines ("The Princess of Cleves", "Part ...:"), no
     marker after line 3, no paragraph assemble.is_subheading would set
     as a heading (the book has none: a hit is a leaked short line --
     a letter's salutation or signature must sit in an indented block),
     no curly quotes, no guillemets.
  9. Locked names: none of the BANNED forms (the cribs' renderings).
 10. Numerals and regnal numbers present in the French but absent from
     the English: WARNINGS for a human to read.
"""

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

BOOK = Path(__file__).parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BOOK))
from assemble import PART_LINE, PART_MARK, is_subheading  # noqa: E402

SECTIONS = ["The Publisher to the Reader", "Part One", "Part Two",
            "Part Three", "Part Four", "The Princess of Montpensier"]
GROUP_SIZES = [1, 3, 3, 3, 3, 2]
FINS = ["fin de la première partie.", "fin de la seconde partie.",
        "fin de la troisième partie.", "fin de la quatrième et dernière partie",
        "fin de la princesse de montpensier."]
MAX_WORDS = 6000
SHINGLE = 6
LIMIT = 4         # uncovered Gutenberg words tolerated in one run
DIVIDERS = ["The Princess of Cleves"]
# Uncovered Gutenberg runs read against Lepetit by hand (2026-10-10) and
# found to be the school editors' patches where they spliced across a cut,
# or plain variants between the 1678-based and the 1820 text -- never a
# loss in ours. Matched against the normalised uncovered words.
KNOWN = [
    "bientot apres",              # Lepetit: "son père, qui arriva alors"
    "grand respect et qui",       # Lepetit: "un si grand respect ... si éloigné ..., que"
    "continua le vidame",         # school splice; Lepetit has the speech later
    "dit m de nemours et",        # Lepetit: "Je vous ai déja dit, reprit ..."
    "elaigne et plus altere",     # Lepetit: plural agreement, then more text
    "et adore de ses peuples",    # school cut of "et aimé d'une maîtresse ..."
    "elle trouva madame de cleves",  # Lepetit: "Madame de Martigues vint à Coulommiers"
]

BANNED = [
    r"\b[Dd]auphiness\b", r"\b[Cc]rown [Pp]rincess\b", r"\bMadam\b",
    r"\bDutchess\b", r"\bDiana\b", r"\bVidame of Chartres\b",
    r"\bClèves\b", r"\bMercœur\b", r"\bDuke of Alva\b",
    r"\bQueen-[Dd]owager\b", r"\bChabanes\b", r"\bChampigni\b",
    r"\bMézière\b", r"\bChambort\b", r"\bÉlisabeth\b",
    r"\binclination\b",                 # a false friend: see text_analysis
    r"(?<!de )(?<!of )\bCleves\b",      # the husband is never bare "Cleves"
]
# "Monsieur de Cleves" is right in dialogue and wrong in narration, which a
# regex cannot see: that one is the orchestrator's read, not a check.

fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def raw_text(name):
    """Visible text of a Wikisource page, tags stripped -- deliberately
    NOT prep.ws_paras, so the count is independent of prep's parser."""
    t = (BOOK / "_src" / "wikisource" / f"{name}.html").read_text(
        encoding="utf-8")
    t = t[t.index("</style>", t.index("headertemplate-journal")) + 8:]
    t = t[:t.find("<!--")]
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace(" ", " ")
    return " ".join(t.split())


def norm_words(s):
    s = s.replace("’", "'").replace("œ", "oe").replace("æ", "ae")
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\[\d+\]", " ", s)
    s = s.replace("oi", "ai").replace("-", " ")
    s = re.sub(r"\bmonsieur\b", "m", s)       # Lepetit abbreviates
    s = re.sub(r"\bmadame la dauphine\b", "madame la dauphine", s)
    s = s.replace("colomiers", "coulommiers").replace("longtemps",
                                                      "long temps")
    return re.findall(r"[a-z]+", s)


def gutenberg_body():
    g = (BOOK / "_src" / "pg20262.txt").read_text(encoding="utf-8")
    g = g.replace("\r\n", "\n")
    g = g[g.index("PREMIÈRE PARTIE."):g.index("\nNOTES.\n")]
    heads = re.findall(r"^(PREMIÈRE|SECONDE|TROISIÈME|QUATRIÈME) PARTIE\.$",
                       g, re.M)
    g = re.sub(r"\[Page \d+\]", "", g)
    g = re.sub(r"[ \t]{2,}\d+[ \t]*$", "", g, flags=re.M)   # line numbers
    g = re.sub(r"(\w)-\n(\w)", r"\1\2", g)
    g = re.sub(r"^(PREMIÈRE|SECONDE|TROISIÈME|QUATRIÈME) PARTIE\.$", "", g,
               flags=re.M)
    return heads, g


def groups(manifest):
    out = []
    for m in manifest:
        if m["part"] == 1:
            out.append([])
        out[-1].append(m)
    return out


def check_source(manifest):
    # 1. the book's own structure
    found = []
    for name in ["cleves-1", "cleves-2", "cleves-3", "cleves-4",
                 "montpensier"]:
        t = raw_text(name)
        found += re.findall(r"fin de la [^.]*?(?:partie\.?|montpensier\.)", t)
    if found != FINS:
        fail(f"'fin' lines {found} != {FINS}")
    heads, gtext = gutenberg_body()
    if len(heads) != 4:
        fail(f"Gutenberg #20262 has {len(heads)} PARTIE headings, not 4")

    # 2. manifest shape
    if len(manifest) != 15:
        fail(f"manifest has {len(manifest)} files, expected 15")
    gs = groups(manifest)
    if [g[0]["title"] for g in gs] != SECTIONS:
        fail(f"sections {[g[0]['title'] for g in gs]}")
    if [len(g) for g in gs] != GROUP_SIZES:
        fail(f"group sizes {[len(g) for g in gs]} != {GROUP_SIZES}")
    for g in gs:
        for n, m in enumerate(g, 1):
            if (m["part"], m["of"], m["title"]) != (n, len(g), g[0]["title"]):
                fail(f"{m['file']}: part {m['part']}/{m['of']} "
                     f"{m['title']!r} out of sequence")
        is_part = g[0]["title"].startswith("Part ")
        if is_part != bool(g[0].get("chapter")):
            fail(f"{g[0]['file']}: 'chapter' flag wrong")
    pbs = [(m["file"], m["part_before"]) for m in manifest
           if m.get("part_before")]
    if pbs != [("000.txt", DIVIDERS[0])]:
        fail(f"part_before entries {pbs}")
    for m in manifest:
        if PART_LINE.match(m["title"]) or re.search(r"\b[IVX]+\b", m["title"]):
            fail(f"{m['file']}: title {m['title']!r} not in word form")

    # 3. completeness against the raw pages
    drop = re.compile(r"LA PRINCESSE|DE CLÈVES\.|DE MONTPENSIER\.|"
                      r"(SECONDE|TROISIÈME|QUATRIÈME) PARTIE\.|"
                      r"fin de la [^.]*?(partie\.?|montpensier\.)")
    # compare with ALL whitespace removed: tag boundaries split tokens in
    # the raw text ("I er", "II .") but cannot change a single letter
    squash = lambda s: re.sub(r"\s+", "", s)
    body = {m["file"]: (BOOK / "chapters" / m["file"]).read_text(
        encoding="utf-8") for m in manifest}
    words = {f: len(t.split()) for f, t in body.items()}
    pages = [(f"cleves-{k}", g) for k, g in enumerate(gs[1:5], 1)]
    pages.append(("montpensier", gs[5]))
    for name, g in pages:
        want = squash(drop.sub(" ", raw_text(name)))
        have = squash("".join(body[m["file"]] for m in g))
        if want != have:
            i = next((i for i, (x, y) in enumerate(zip(want, have))
                      if x != y), min(len(want), len(have)))
            fail(f"{name}: files differ from the page at char {i}: "
                 f"page {want[i - 30:i + 30]!r} files {have[i - 30:i + 30]!r}")
    for m in manifest:
        if words[m["file"]] != m["words"]:
            fail(f"{m['file']}: manifest words {m['words']} != "
                 f"{words[m['file']]}")

    # 4. second witness, one way
    ours = norm_words(" ".join((BOOK / "chapters" / m["file"]).read_text(
        encoding="utf-8") for m in manifest if m["source"].startswith("Cl")))
    g = norm_words(gtext)
    have = {tuple(ours[i:i + SHINGLE]) for i in range(len(ours) - SHINGLE)}
    gset = {tuple(g[i:i + SHINGLE]) for i in range(len(g) - SHINGLE)}
    # a Gutenberg word is COVERED when some shingle containing it occurs in
    # ours. Where the school editors spliced across a cut and patched the
    # join ("il résolut" -> "M. de Nemours résolut") only the patched
    # words go uncovered; a real loss leaves a long uncovered run.
    covered = [False] * len(g)
    for i in range(len(g) - SHINGLE + 1):
        if tuple(g[i:i + SHINGLE]) in have:
            for j in range(i, i + SHINGLE):
                covered[j] = True
    runs, i = [], 0
    while i < len(g):
        if covered[i]:
            i += 1
            continue
        j = i
        while j < len(g) and not covered[j]:
            j += 1
        runs.append((i, j))
        i = j
    real = [(a, b) for a, b in runs if b - a > LIMIT
            and not any(k in " ".join(g[a:b]) for k in KNOWN)]
    for a, b in runs:
        if b - a > LIMIT and (a, b) not in real:
            print(f"  known variant: {' '.join(g[a:b])!r}")
    for a, b in real:
        fail(f"Gutenberg text absent from ours: {' '.join(g[a:b])!r} "
             f"(in: ...{' '.join(g[max(0, a - 5):b + 5])[:140]}...)")
    cut = sum(1 for i in range(len(ours) - SHINGLE)
              if tuple(ours[i:i + SHINGLE]) not in gset)
    print(f"second witness: Gutenberg {len(g)} words, ours {len(ours)}; "
          f"{len(runs)} short variants (spelling, patched splices), "
          f"{len(real)} real gaps; "
          f"~{cut} of our words are in passages the school edition cut")

    # 5. size, 6. cribs
    for m in manifest:
        if m["words"] > MAX_WORDS:
            fail(f"{m['file']}: {m['words']} French words > {MAX_WORDS}")
    ratios = []
    for m in manifest[1:]:
        ref = BOOK / "reference" / m["file"]
        if not ref.exists():
            fail(f"reference/{m['file']} missing")
            continue
        w = len(ref.read_text().split("\n\n", 1)[1].split())
        ratios.append(f"{m['file'][:3]} {w / m['words']:.2f}")
    print("crib/French:", ", ".join(ratios))


def check_modern(manifest):
    mod = BOOK / "modern_chapters"
    for m in manifest:
        f = mod / m["file"]
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        lines = text.split("\n")
        if lines[0].strip() != m["title"]:
            fail(f"{m['file']}: line 1 {lines[0][:60]!r} != {m['title']!r}")
        head = [ln.strip() for ln in lines[1:4] if ln.strip()]
        want = f"(Part {m['part']} of {m['of']})"
        if m["of"] > 1:
            if not head or head[0] != want:
                fail(f"{m['file']}: missing {want!r} after the title")
        elif head and PART_MARK.match(head[0]):
            fail(f"{m['file']}: part marker on a single file")
        for n, ln in enumerate(lines[1:], 2):
            s = ln.strip()
            if PART_MARK.match(s) and n > 4:
                fail(f"{m['file']}:{n}: part marker in the body")
            if PART_LINE.match(s) or re.match(r"^Part \w+:", s):
                fail(f"{m['file']}:{n}: divider line {s[:50]!r}")
            if s in DIVIDERS or (s in SECTIONS and n > 1):
                fail(f"{m['file']}:{n}: heading/divider repeated: {s!r}")
        paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        for par in paras[1:]:
            st = par.strip()
            if PART_MARK.match(st) or par.startswith(" "):
                continue
            if is_subheading(st):
                fail(f"{m['file']}: would render as a heading: {st[:50]!r}")
        if re.search("[‘’“”]", text):
            fail(f"{m['file']}: curly quotes (collection uses straight)")
        if re.search("[«»]", text):
            fail(f"{m['file']}: guillemets left in the English")
        flat = " ".join(text.split())      # a hard wrap must not trip a lookbehind
        for pat in BANNED:
            for hit in re.finditer(pat, flat):
                fail(f"{m['file']}: banned form {hit.group(0)!r}")
        # 10. numerals and regnal numbers (warnings)
        src = (BOOK / "chapters" / m["file"]).read_text(encoding="utf-8")
        src = re.sub(r"\bIer\b", "I", src)
        nums = lambda s: set(re.findall(r"\b(?:\d+|[IVX]+)\b", s))
        missing = nums(src) - nums(text)
        if missing:
            print(f"  WARN {m['file']}: French numerals absent in English: "
                  f"{sorted(missing)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modern", action="store_true")
    args = ap.parse_args()
    manifest = json.loads((BOOK / "manifest.json").read_text())
    check_source(manifest)
    if args.modern:
        check_modern(manifest)
    print(f"\n{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
