"""Prepare Zur Genealogie der Moral: German source + English crib, per file.

    python3 books/genealogy/prep.py            # writes chapters/, reference/, manifest.json
    python3 books/genealogy/prep.py --survey   # print the section table only

SOURCES (in _src/, fetched by fetch.sh):
  ekgwb_GM.html  Nietzsche Source eKGWB/GM, the Colli-Montinari text, which
                 keeps the first edition's spelling (Thier, giebt, nöthig,
                 Erkenntniss) and marks Sperrdruck as <span class="bold">.
                 THE SOURCE.
  zeno/          Schlechta 1954 via zeno.org: a second witness, used only by
                 check.py, and the source of ONE line eKGWB lacks: the
                 title-page note "Dem letztveröffentlichten ...".
  se/            Standard Ebooks, Horace B. Samuel's translation (1913).
                 THE CRIB ONLY.

STRUCTURE IS NIETZSCHE'S: a Preface of 8 numbered sections and three
Essays (Abhandlungen) of 17, 25 and 28. Four logical chapters. The three
Essays are split into parts at section boundaries only (GROUPS below), so
no file ever opens mid-section; each part is a later "(Part n of k)" of its
Essay. The Essays are top-level sections (no part_before): Nietzsche's own
contents list is exactly Preface + three Essays, and "Essay One: ..." can
never match assemble.PART_LINE.

CONVERSIONS
  - Sperrdruck <span class="bold"> -> *x* (assemble renders it as <em>);
    check.py asserts the same count of spans in the English.
  - section numbers "7." -> a lone roman numeral line "VII" (assemble sets
    a lone roman numeral as an h4, a lone "7" as a bare paragraph; the
    zarathustra precedent). The manifest records them in "sections".
  - Greek: ϑ (U+03D1, eKGWB's theta) -> θ; the one Latin "u" inside a
    Greek word (ῥαϑuμία) -> υ. Agents transliterate anyway.
  - verse: only the three Homer hexameters in II 23 (Odyssey 1.32-34),
    one tab-indented block of three lines (assemble renders it as <pre>).
    The Essay III motto is a prose sentence from Zarathustra: one
    paragraph, then "Also sprach Zarathustra." as its own paragraph.
  - "Anmerkung" (the note after I 17) and the Preface dateline are kept as
    ordinary paragraphs at the end of their sections.
"""

import json
import re
import sys
from html import unescape
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src"

TITLES = {
    "V": ("Preface", "Vorrede"),
    "I": ('Essay One: "Good and Evil," "Good and Bad"',
          "Erste Abhandlung: „Gut und Böse“, „Gut und Schlecht“"),
    "II": ('Essay Two: "Guilt," "Bad Conscience," and the Like',
           "Zweite Abhandlung: „Schuld“, „schlechtes Gewissen“ und Verwandtes"),
    "III": ("Essay Three: What Is the Meaning of Ascetic Ideals?",
            "Dritte Abhandlung: was bedeuten asketische Ideale?"),
}
EXPECTED = {"V": 8, "I": 17, "II": 25, "III": 28}

# Files: (essay, first section, last section). Cut only at section
# boundaries; each group <= ~4k German words (~5k English at 1.2).
GROUPS = [
    ("V", 1, 8),
    ("I", 1, 9), ("I", 10, 13), ("I", 14, 17),
    ("II", 1, 6), ("II", 7, 11), ("II", 12, 17), ("II", 18, 25),
    ("III", 1, 7), ("III", 8, 11), ("III", 12, 16), ("III", 17, 20),
    ("III", 21, 24), ("III", 25, 28),
]

# The title-page verso of the 1887 edition, which eKGWB does not carry
# (zeno's front page does). It opens the Preface file.
FRONT_NOTE = ("*Dem letztveröffentlichten „Jenseits von Gut und Böse“ "
              "zur Ergänzung und Verdeutlichung beigegeben.*")


def roman(n):
    out = ""
    for v, s in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out, n = out + s, n - v
    return out


def inline(h):
    """HTML fragment -> plain text with *emphasis*."""
    h = re.sub(r"<br\s*/?>", "\n", h)
    # bolditalic is Sperrdruck too (III 27, the planned Wille zur Macht
    # title, half in each class); adjacent spans merge below
    h = re.sub(r'<span class="(?:bold|bolditalic)">(.*?)</span>',
               lambda m: "*" + m.group(1).strip() + "*" if m.group(1).strip() else m.group(1),
               h, flags=re.S)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("**", "")
    h = unescape(h)
    h = h.replace("ϑ", "θ").replace("ῥαθuμία", "ῥαθυμία")
    h = re.sub(r"[ \t\r]+", " ", h)
    return h.strip()


def german():
    """{essay: {n: [paragraphs]}} plus the Essay III motto, from eKGWB."""
    t = (SRC / "ekgwb_GM.html").read_text(encoding="utf-8")
    # blocks in document order
    tok = re.compile(
        r'<h2>(?P<h2>.*?)</h2>'
        r'|<h3>(?P<h3>.*?)</h3>'
        r'|<p class="motto">(?P<motto>.*?)</p>'
        r'|<p class="motto-right">(?P<mottor>.*?)</p>'
        r'|<div class="l">(?P<verse>.*?)</div>'
        r'|<blockquote>(?P<bq>.*?)</blockquote>'
        r'|<p(?: class="(?P<pc>[^"]*)")?>(?P<p>.*?)</p>', re.S)
    order = ["V", "I", "II", "III"]
    essay, sec = None, None
    out = {e: {} for e in order}
    motto = []
    h2_seen = 0
    for m in tok.finditer(t):
        if m.group("h2") is not None:
            txt = inline(m.group("h2"))
            if txt.startswith("Zur Genealogie"):
                continue
            essay = order[h2_seen]
            h2_seen += 1
            sec = None
            continue
        if m.group("h3") is not None:
            n = int(inline(m.group("h3")).rstrip("."))
            sec = n
            out[essay][n] = []
            continue
        if essay is None:
            continue
        if m.group("motto") is not None:
            # set in short lines on the page, but it is a prose sentence
            # from Zarathustra ("On Reading and Writing"): one paragraph
            motto.append(" ".join(inline(m.group("motto")).split()))
            continue
        if m.group("mottor") is not None:
            # the attribution is spaced type on the title, not emphasis:
            # "*Thus spoke Zarathustra.*" would end on "*" and be set as
            # a heading by assemble.is_subheading
            motto.append(inline(m.group("mottor")).strip("*"))
            continue
        if sec is None:
            continue
        paras = out[essay][sec]
        if m.group("verse") is not None:
            # one eKGWB div = one hexameter; its <br> is only the page's
            # wrap of a long line, so the line is rejoined
            paras.append("\t" + " ".join(inline(m.group("verse")).split()))
        elif m.group("bq") is not None:
            paras.append(inline(m.group("bq")))
        else:
            if m.group("pc") in ("Zentriert", "Untertitel"):
                continue
            txt = inline(m.group("p")).replace("\n", " ")
            if txt:
                paras.append(txt)
    # the dateline is two "paragraphs" in eKGWB; it is one line
    v8 = out["V"][8]
    if v8[-2:] == ["*Sils-Maria*, Oberengadin,", "im Juli 1887."]:
        v8[-2:] = ["*Sils-Maria*, Oberengadin, im Juli 1887."]
    else:
        sys.exit(f"Preface dateline not found: {v8[-2:]}")
    # the Homer verse in II 23: three eKGWB divs are one stanza of
    # three couplet-lines; keep them as ONE tabbed block
    for e in out:
        for n, paras in out[e].items():
            merged = []
            for p in paras:
                if p.startswith("\t") and merged and merged[-1].startswith("\t"):
                    merged[-1] += "\n" + p
                else:
                    merged.append(p)
            out[e][n] = merged
    return out, motto


def se_sections():
    """{essay: {n: [paragraphs]}} from Samuel's SE text."""
    files = {"V": "preface.xhtml", "I": "chapter-1.xhtml",
             "II": "chapter-2.xhtml", "III": "chapter-3.xhtml"}
    out = {}
    for e, f in files.items():
        t = (SRC / "se" / "epub" / "text" / f).read_text(encoding="utf-8")
        t = re.sub(r'<a href="endnotes[^"]*"[^>]*>.*?</a>', "", t, flags=re.S)
        parts = re.split(r'<section id="(?:chapter-\d|preface)-(\d+)"[^>]*>', t)
        out[e] = {}
        head = parts[0]
        for k in range(1, len(parts), 2):
            n = int(parts[k])
            body = parts[k + 1]
            paras = []
            for m in re.finditer(r"<(p|blockquote|h3)[^>]*>(.*?)</\1>", body, re.S):
                if m.group(1) == "h3":
                    continue
                s = m.group(2)
                s = re.sub(r"<br\s*/?>", "\n", s)
                s = re.sub(r"</?(?:i|em|strong|b)(?: [^>]*)?>", "*", s)
                s = re.sub(r"<[^>]+>", "", s)
                s = unescape(s)
                s = re.sub(r"\*\s*\*", "", s)
                s = "\n".join(re.sub(r"\s+", " ", l).strip() for l in s.split("\n"))
                if s.strip():
                    paras.append(s.strip())
            out[e][n] = paras
        out[e]["_head"] = head
    return out


def words(paras):
    return sum(len(p.split()) for p in paras)


def build(survey=False):
    de, motto = german()
    en = se_sections()
    for e, n in EXPECTED.items():
        if sorted(de[e]) != list(range(1, n + 1)):
            sys.exit(f"eKGWB {e}: sections {sorted(de[e])} != 1..{n}")
        got = sorted(k for k in en[e] if k != "_head")
        if got != list(range(1, n + 1)):
            sys.exit(f"SE crib {e}: sections {got} != 1..{n}")
    if len(motto) != 2:
        sys.exit(f"Essay III motto: {motto}")
    # every section belongs to exactly one group
    cover = [(e, n) for e, a, b in GROUPS for n in range(a, b + 1)]
    want = [(e, n) for e in ["V", "I", "II", "III"] for n in range(1, EXPECTED[e] + 1)]
    if cover != want:
        sys.exit("GROUPS do not cover every section exactly once, in order")

    nparts = {e: sum(1 for g in GROUPS if g[0] == e) for e in EXPECTED}
    seen = {e: 0 for e in EXPECTED}
    manifest = []
    if not survey:
        for d in ("chapters", "reference"):
            (BOOK / d).mkdir(exist_ok=True)
            for p in (BOOK / d).glob("*.txt"):
                p.unlink()
    for i, (e, a, b) in enumerate(GROUPS):
        seen[e] += 1
        part, of = seen[e], nparts[e]
        fname = f"{i:03d}.txt"
        title, de_title = TITLES[e]
        de_paras, en_paras, secs = [], [], []
        if e == "V":
            de_paras.append(FRONT_NOTE)
        if e == "III" and a == 1:
            de_paras += motto
        for n in range(a, b + 1):
            r = roman(n)
            secs.append(r)
            de_paras += [r] + de[e][n]
            en_paras += [r] + en[e][n]
        dw, ew = words(de_paras), words(en_paras)
        entry = {"file": fname, "title": title, "part": part, "of": of,
                 "de_title": de_title, "essay": e,
                 "first": a, "last": b, "sections": secs,
                 "words": dw, "crib_words": ew}
        manifest.append(entry)
        if survey:
            print(f"{fname} {e:>3} {a:>2}-{b:<2} de {dw:5d}  crib {ew:5d}  "
                  f"ratio {ew / dw:.2f}  {title} ({part}/{of})")
            continue
        (BOOK / "chapters" / fname).write_text("\n\n".join(de_paras) + "\n",
                                               encoding="utf-8")
        mark = f" (Part {part} of {of})" if of > 1 else ""
        banner = (f"{title}{mark}, sections {a}-{b} -- Horace B. Samuel's "
                  f"English (1913), CRIB ONLY")
        (BOOK / "reference" / fname).write_text(
            banner + "\n\n" + "\n\n".join(en_paras) + "\n", encoding="utf-8")
    tot_de = sum(m["words"] for m in manifest)
    tot_en = sum(m["crib_words"] for m in manifest)
    print(f"{len(manifest)} files; German {tot_de} words, crib {tot_en} "
          f"({tot_en / tot_de:.2f})")
    if not survey:
        (BOOK / "manifest.json").write_text(
            json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8")


if __name__ == "__main__":
    build(survey="--survey" in sys.argv)
