"""H. W. Fowler, A Dictionary of Modern English Usage (Oxford, Clarendon
Press, 1926): a RESTORED EDITION.

    python3 fowler/prep.py

THE TEXT IS PAGE-READ. No transcription exists; the OCR drafts were a
convenience only. Two scans were read, leaf by leaf, into proof files
(apply_fixes.py writes proof*/NNN.txt from preproof*/ and fixes*/):
  proof/      Google's scan (dictionaryofmode0000hwfo), front matter and
              pp. 1-64, plus pp. 374-375, which the second scan skips;
  proof_kv/   the cleaner bwb_KV scan, p. 65 to the end.
Where both scans were read (p. 117, p. 386, pp. 380-381 twice in KV) the
readings agreed on every word and were settled on the KV image, so the KV
leaf is taken. correction_instructions.txt is the standing instruction the
leaves were read under; proof_notes.txt records every reading kept as
printed and every PREP item this file discharges.

Conventions the proof files carry, resolved here:
  "page: N"      the printed folio (p. 284 misprints "234": asserted).
  "+ "           continues the paragraph before it, across a column or a
                 page; "+ <TAB>" continues a set-out (TAB) block.
  **x**          bold (headwords, article titles, section numerals).
  ^^X^^          small capitals: cross-references, above all.
  *x*            italic; ***x*** italic inside bold.
  a TAB line     a set-out line (lists, tables with " | " cells, verse).
  ∗              Fowler's printed asterisk (ruling 18), never markup.

WHAT THIS EDITION ADDS: every headword is an anchor, and every small-caps
cross-reference that names a headword or a general article is a link to it
(a reference to nothing stays plain text; the count is printed). The
small capitals are re-cased the way Fowler printed them -- sentence case
for a general article, taken from his own List of General Articles
(pp. v-viii), lower case for an ordinary word -- because the proofs write
them in capitals and the renderer sets them with font-variant small-caps.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

ROMAN = ["iii", "iv", "v", "vi", "vii", "viii"]
MISPRINTED_FOLIO = {("proof_kv", 296): ("234", "284")}   # ruling 23
DUPLICATE_LEAVES = {392, 393}          # the scan's second shot of pp. 380-381


def leaf_order():
    out = [("proof", n) for n in range(9, 79)]            # pp. iii-viii, 1-64
    kv = sorted(int(p.stem) for p in (HERE / "proof_kv").glob("*.txt"))
    assert kv[0] == 77, kv[:3]
    for i, n in enumerate(kv):
        if n in DUPLICATE_LEAVES:
            continue
        if "--partial" in sys.argv and i and n != kv[i - 1] + 1:
            break                                           # proofing in progress
        out.append(("proof_kv", n))
        if n == 385:                                        # p. 373; KV skips 374-375
            out += [("proof", 388), ("proof", 389)]
    return out


def load():
    """[(page, [paragraph, ...])] in reading order, pages asserted
    consecutive from iii to the last page read."""
    pages = []
    for d, n in leaf_order():
        text = (HERE / d / f"{n:03d}.txt").read_text()
        head, _, body = text.partition("\n")
        m = re.fullmatch(r"page: (\S+)", head.strip())
        assert m, (d, n, head)
        page = m.group(1)
        if (d, n) in MISPRINTED_FOLIO:
            printed, true = MISPRINTED_FOLIO[(d, n)]
            assert page == printed, (d, n, page)
            page = true
        pars = [p for p in re.split(r"\n[ \t]*\n", body.strip("\n")) if p.strip()]
        pages.append((page, pars, f"{d}/{n:03d}"))
    want = ROMAN + [str(i) for i in range(1, len(pages) - len(ROMAN) + 1)]
    got = [p for p, _, _ in pages]
    assert got == want, next((w, g, s) for w, g, (_, _, s) in zip(want, got, pages) if w != g)
    return pages


# ---------------------------------------------------------------- joining

SPANS = ("***", "**", "^^", "*")


def join_spans(a, b):
    """ruling 14: a span closed at the end of a column and reopened after
    the '+ ' is one span. Joining 'x*' + '*y' always renders the same as the
    two spans with a space between, so the merge is safe for any marker."""
    for mk in SPANS:
        if a.endswith(mk) and b.startswith(mk) and not b.startswith(mk + "*"):
            if mk == "*" and (a.endswith("**") or b.startswith("**")):
                continue
            return a[: -len(mk)], b[len(mk):], True
    return a, b, False


WORDS = None


def dictionary():
    global WORDS
    if WORDS is None:
        WORDS = set()
        for f in ("/usr/share/dict/british-english", "/usr/share/dict/american-english"):
            if Path(f).exists():
                WORDS |= {w.strip().lower() for w in open(f)}
    return WORDS


# a word broken at a column or page end: decided by hand where the
# dictionary cannot (proof_notes.txt, "PREP MUST join a WORD BROKEN AT A
# COLUMN OR LEAF END"). True keeps the hyphen (a real compound).
SEAM_HYPHEN = {
    # line-end breaks the dictionary does not know: rare words, Fowler's
    # cited forms, suffixed forms. Each read in context (2026-09-28).
    **{k: False for k in (
        "cas-tratable", "in-alterable", "unEng-lish", "constrain-edly",
        "allure-ments", "ponderous-ness", "phage-daena", "indiffer-ency",
        "amor-celments", "neces-sitarian", "hypo-thecate", "at-taque",
        "sensi-tivize")},
    # real compounds: out-of-the-way, ill-temper, case-endings,
    # anti-Saxonist, Leave-not-a-rack-behind, foul-mouthed, self-conscious
    # (the dictionary keeps these already; listed so the decision is
    # visible). sea-|sickness is a line end in a quotation; Fowler lists
    # "seasick" as one word, so it is closed up.
    **{k: True for k in (
        "of-the", "ill-temper", "case-endings", "anti-Saxonist", "a-rack",
        "foul-mouthed", "the-way", "self-conscious")},
}
SEAMS = []


def bare(s):
    return re.sub(r"[*^]", "", s)


def join(a, b):
    """Join continuation b onto paragraph a."""
    if b.startswith("\t") or re.match(r"[ \t]", b):
        return a.rstrip("\n") + "\n" + b                   # a set-out block runs on
    a2, b2, _ = join_spans(a.rstrip(), b.lstrip())
    m = re.search(r"([A-Za-zÀ-ɏ̀-ͯ]+)-$", bare(a2))
    if m:
        left = m.group(1)
        right = re.match(r"[A-Za-zÀ-ɏ̀-ͯ]+", bare(b2))
        right = right.group(0) if right else ""
        key = f"{left}-{right}"
        keep = SEAM_HYPHEN.get(key)
        if keep is None:
            whole = unicodedata.normalize("NFD", left + right).lower()
            whole = "".join(c for c in whole if not unicodedata.combining(c))
            keep = whole not in dictionary()
        SEAMS.append((key, keep))
        return (a2 if keep else a2[:-1]) + b2
    return a2 + " " + b2


def stream(pages):
    """Paragraphs in reading order with every '+ ' joined, each tagged
    with the page it opens on."""
    out = []
    for page, pars, src in pages:
        for p in pars:
            if p.startswith("+ **") and not p.startswith("+ ***") \
                    and not out[-1][1].rstrip().endswith("**"):
                p = p[2:]           # a headword at a column top, flush like all headwords
            if p.startswith("+ ") or p.startswith("+\t"):
                assert out, (src, p[:60])
                cont = p[2:] if p.startswith("+ ") else p[1:]
                out[-1][1] = join(out[-1][1], cont)
            else:
                out.append([page, p])
    return out


# --------------------------------------------------------- normalisation

NORMALISE = [
    # carons are breves in this book (ruling 17)
    ("ǎ", "ă"), ("ě", "ĕ"), ("ǐ", "ĭ"), ("ǒ", "ŏ"), ("ǔ", "ŭ"),
    # the long oo is one bar over both letters (ruling 10)
    ("ōō", "o͞o"), ("ō͞o", "o͞o"),
]


def normalise(p):
    for a, b in NORMALISE:
        p = p.replace(a, b)
    # the printer's thin space in "e. g.", "i. e." -- the proofs mix both
    p = re.sub(r"\b(e|i)\.(g|e)\.", r"\1. \2.", p)
    # quote spacing: Fowler's compositor spaces inside single quotes; close up
    p = re.sub(r"‘ +", "‘", p)
    p = re.sub(r" +’", "’", p)
    p = re.sub(r"(?<![\w’])' (?=\w)", "'", p)
    p = re.sub(r"(?<=[\w.,;:!?*)]) '(?=[\s,.;:)—]|$)", "'", p)
    # a letter-spaced hyphen set out to justify a line ("British - Columbia")
    p = re.sub(r"(?<=[A-Za-z]) - (?=[A-Za-z])", "-", p)
    # two letter references joined by '&' are one (PREP item, 519-523):
    # "^^-ER^^ & ^^-EST^^" is the article -ER & -EST
    p = re.sub(r"\^\^(-[A-Z()]+-?)\^\^ & \^\^(-[A-Z()]+-?)\^\^", r"^^\1 & \2^^", p)
    # "&c." after a small-caps reference renders alike inside or out
    p = p.replace(" &c.^^", "^^ &c.")
    # 'x* *y' italic seams: one span
    p = re.sub(r"(?<=[^*\s])\* \*(?=[^*\s])", " ", p)
    return p


# ----------------------------------------------------------- headwords

HEADWORD = re.compile(r"^\*\*(?!\d)(.+?)\*\*(?!\*)")


def plain(s):
    for a, b in (("Æ", "AE"), ("æ", "ae"), ("Œ", "OE"), ("œ", "oe")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[*^'’ʹ]", "", s)
    return s


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", plain(s).lower()).strip("-")


# a part-of-speech label after a headword ("affix, n.", "stave, vb",
# "that, adj. & adv.") is not a form of the word
POS = re.compile(r"(?:(?:n|nn|v|vb|vv|adj|adjj|adv|prep|pref|conj|pron|rel|pl|sing|"
                 r"p\.p|intr|trans|&|and|or|\s)+\.?\s*)+")


def keys(title):
    """The lookup keys a headword answers to: the whole title, each of its
    comma-, ')('- or '&'-separated forms ("sceptre, -ter" answers to
    "sceptre"; "simpleness)(simplicity" to both), without a trailing
    parenthesis, with optional letters dropped and kept ("moral(e)" is
    "moral" and "morale"), and closed up ("every one" is "everyone")."""
    t = refkey(title)
    out = {t, t.strip("()")}
    for part in re.split(r"\)\s*\(|,|\s&\s", t):
        part = part.strip(" .,;:")
        # "platen, -tt-": "-tt-" is platen's own inflexion, not a headword;
        # a suffix part counts only in a title that is all suffixes
        if part and (not part.startswith("-") or t.startswith("-")) \
                and not POS.fullmatch(part):
            out.add(part)
    for k in list(out):
        out.add(re.sub(r"\s*\([^)]*\)$", "", k))
    for k in list(out):
        if re.search(r"\w\(\w+\)", k):
            out.add(re.sub(r"\((\w+)\)", "", k))
            out.add(re.sub(r"\((\w+)\)", r"\1", k))
    for k in list(out):
        if " " in k and not k.startswith("-"):
            out.add(k.replace(" ", ""))
    return {k.strip() for k in out if k.strip()}


def refkey(text):
    k = re.sub(r"\s+", " ", plain(text).lower()).strip(" .,;:")
    k = re.sub(r"\)\s*\(", ")(", k)                 # "-ise) (-ize"
    return re.sub(r"(?<=\b\w)\.\s+(?=\w\b)", ".", k)    # "p. p." = "p.p."


# ------------------------------------------------------------ sections

FRONT = [("iii", "Dedication"), ("iv", "Acknowledgements"),
         (None, "Key to Pronunciation"), ("v", "List of General Articles")]
# a heading inside the front matter that opens a section of its own
FRONT_HEADS = {"**ACKNOWLEDGEMENTS**": "Acknowledgements",
               "**KEY TO PRONUNCIATION**": "Key to Pronunciation",
               "**LIST OF GENERAL ARTICLES**": "List of General Articles"}


def first_letter(title):
    m = re.search(r"[a-z]", plain(title).lower())
    return m.group(0).upper()


def sections(paras):
    """Front matter by page, then one section per letter, split at the
    first headword of each new initial. The proofs carry the letter
    headings Fowler printed as bare capitals (a few were not written: A
    has none in print, the half-title stands before it; Q was missed): each
    one present must agree with the split, and is dropped."""
    front = {t: [] for _, t in FRONT}
    letters = []
    cur = None
    roman = set(ROMAN)
    fp = dict(FRONT)
    ftitle, last_page = None, None
    for i, (page, p) in enumerate(paras):
        if page in roman:
            if page != last_page:
                ftitle, last_page = fp.get(page, ftitle), page
            if p.strip() in FRONT_HEADS:
                ftitle = FRONT_HEADS[p.strip()]
                continue
            front[ftitle].append(p)
            continue
        s = p.strip()
        if re.fullmatch(r"[A-Z]", s):
            nxt = paras[i + 1][1] if i + 1 < len(paras) else ""
            m = HEADWORD.match(nxt)
            if m and first_letter(m.group(1)) == s:
                assert cur is None or cur["title"] != s, s
                letters.append({"title": s, "stream": []})
                cur = letters[-1]
                continue
        m = HEADWORD.match(s)
        if m and not s.startswith("**" + "^^"):
            L = first_letter(m.group(1))
            nxt_letter = "A" if cur is None else chr(ord(cur["title"]) + 1)
            if L == nxt_letter:
                letters.append({"title": L, "stream": []})
                cur = letters[-1]
        cur["stream"].append(p)
    out = [{"title": t, "stream": front[t]} for _, t in FRONT]
    order = [s["title"] for s in letters]
    assert order == sorted(order) and len(order) == len(set(order)), order
    return out + letters


def is_article_title(t):
    letters = [c for c in plain(t) if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


# ------------------------------------------------- anchors and references

GENERAL = {}          # refkey -> Fowler's casing, from pp. v-viii


def general_articles(front_list):
    for p in front_list:
        for line in p.split("\n"):
            s = line.strip()
            m = re.fullmatch(r"\*\*\(?(.+?)\)?\*\*", s)
            if m:
                GENERAL[refkey(m.group(1))] = m.group(1)


def headwords(secs):
    """slug for every headword paragraph; key -> slug."""
    index, seen = {}, {}
    for s in secs[len(FRONT):]:
        for j, p in enumerate(s["stream"]):
            m = HEADWORD.match(p)
            if not m:
                continue
            title = re.sub(r"\.\s*\d+\.?$", "", m.group(1)).rstrip(" .,")
            sl = "w-" + slug(title)
            n = seen.get(sl, 0) + 1
            seen[sl] = n
            if n > 1:
                sl = f"{sl}-{n}"
            s["stream"][j] = f"\u27e6#{sl}\u27e7" + p
            for k in keys(title):
                index.setdefault(k, sl)
    return index


def lookup(index, k):
    """A reference names a headword exactly, or by a form of it: singular
    for plural ("GALLICISM", "SUPERFLUOUS WORD"), without "&c.", or by the
    unambiguous start of a long general-article title ("-EN VERBS" for
    "-EN VERBS FROM ADJECTIVES")."""
    k = re.sub(r"\s*&c\.?$", "", k).strip(" ,")
    cands = [k, "s " + k,              # "'s INCONGRUOUS" prints its 's roman k + "s", k[:-1] if k.endswith("s") else None,
             k + "es", re.sub(r"\s*\(.*\)$", "", k),
             k[:-1] + "ies" if k.endswith("y") else None,
             re.sub(r"(?<=[a-z])-(?=[a-z])", " ", k)]
    for c in cands:
        if c and c in index:
            return index[c]
    pre = {v for key, v in index.items() if key.startswith(k + " ")}
    if len(pre) == 1:
        return pre.pop()
    for part in re.split(r",|\s&\s", k):
        part = part.strip()
        if part and part in index:
            return index[part]
    return None


SC = re.compile(r"\^\^(.+?)\^\^")


def recase(text, target_general):
    """Small capitals as Fowler set them: sentence case for a general
    article (his own casing, from the List), lower case otherwise."""
    k = refkey(text)
    if k in GENERAL:
        return GENERAL[k]
    if target_general:
        low = text.lower()
        return low[:1].upper() + low[1:]
    return text.lower()


def link_refs(secs, index):
    """Every ^^X^^ that names a headword becomes a link token around it."""
    general_slugs = set()
    for s in secs[len(FRONT):]:
        for p in s["stream"]:
            m = re.match(r"\u27e6#([^\u27e7]+)\u27e7\*\*(.+?)\*\*", p)
            if m and is_article_title(m.group(2)):
                general_slugs.add(m.group(1))
    stats = {"linked": 0, "plain": 0}
    missed = {}

    def one(m):
        text = m.group(1)
        k = refkey(text)
        sl = lookup(index, k)
        shown = recase(text, sl in general_slugs)
        if sl is None:
            stats["plain"] += 1
            missed[k] = missed.get(k, 0) + 1
            return f"^^{shown}^^"
        stats["linked"] += 1
        return f"\u27e6@{sl}|^^{shown}^^\u27e7"

    for s in secs[len(FRONT):]:
        s["stream"] = [SC.sub(one, p) for p in s["stream"]]
    for s in secs[:len(FRONT)]:     # front matter: plain small capitals,
        s["stream"] = [SC.sub(lambda m: "^^" + (m.group(1).capitalize()   # "Cantab."
                       if " " not in m.group(1) else m.group(1).lower()) + "^^", p)
                       for p in s["stream"]]
    return stats, missed


def link_list(sec, index):
    """The List of General Articles is Fowler's own index of them: each
    line links to its article. A bracketed title is a cross-reference
    entry and links to it all the same."""
    miss = []
    out = []
    for par in sec["stream"]:
        lines = []
        for line in par.split("\n"):
            body = line.strip()
            if line.startswith("\t") and body:
                k = refkey(body)
                if k.startswith("(") and k.endswith(")"):
                    k = k[1:-1]                  # a bracketed (cross-reference) title
                k = re.sub(r"\)\s*\(", ")(", k)
                k = re.split(r" (?:prep|vb|n|adj|conj|rel)\b", k)[0].strip(" ,")
                sl = lookup(index, k)
                if sl:
                    line = "\t\u27e6@" + sl + "|" + body + "\u27e7"
                else:
                    miss.append(body)
            lines.append(line)
        out.append("\n".join(lines))
    sec["stream"] = out
    return miss


# ---------------------------------------------------------------- output

def write(secs):
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for i, s in enumerate(secs):
        body = s["title"] + "\n\n" + "\n\n".join(s["stream"]).rstrip() + "\n"
        (HERE / "modern_chapters" / f"{i:03d}.txt").write_text(body)
        # chapters/ is the text as printed, without the edition's anchors
        # and links: what verify.py and scan_diff.py compare
        bare_text = re.sub("\u27e6#[^\u27e7]*\u27e7", "", body)
        bare_text = re.sub("\u27e6@[^|\u27e7]*\\|([^\u27e7]*)\u27e7", r"\1", bare_text)
        assert "\u27e6" not in bare_text
        (HERE / "chapters" / f"{i:03d}.txt").write_text(bare_text)
        e = {"file": f"{i:03d}.txt", "title": s["title"], "part": 1, "of": 1}
        if i == len(FRONT):
            e["part_before"] = "The Dictionary"
        manifest.append(e)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")


def main():
    pages = load()
    paras = [(pg, normalise(p)) for pg, p in stream(pages)]
    secs = sections(paras)
    general_articles(secs[len(FRONT) - 1]["stream"])
    index = headwords(secs)
    stats, missed = link_refs(secs, index)
    list_miss = link_list(secs[len(FRONT) - 1], index)
    write(secs)
    n = sum(len(s["stream"]) for s in secs)
    print(f"{len(pages)} pages, {n} paragraphs, {len(index)} headword keys, "
          f"{len(GENERAL)} general articles listed")
    print(f"seams: {len(SEAMS)} ({sum(k for _, k in SEAMS)} hyphens kept)")
    print(f"cross-references: {stats['linked']} linked, {stats['plain']} to nothing")
    for k, c in sorted(missed.items(), key=lambda x: -x[1])[:40]:
        print(f"   {c:3d}  {k}")
    print(f"List of General Articles: {len(list_miss)} lines unlinked:",
          "; ".join(list_miss[:60]))
    print("sections:", " ".join(s["title"][:12] for s in secs))


if __name__ == "__main__":
    main()
