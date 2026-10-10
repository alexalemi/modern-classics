"""Prepare Also sprach Zarathustra: German source + English crib, per file.

    python3 zarathustra/prep.py            # writes chapters/, reference/, manifest.json
    python3 zarathustra/prep.py --survey   # print the section table only

SOURCES (both in _src/, fetched by fetch.sh):
  de_7205.txt  Project Gutenberg #7205, the German text (old orthography:
               Theil, Räthsel, gieng), Sperrdruck emphasis as _x_.
  se/          Standard Ebooks' Thus Spake Zarathustra, Thomas Common's
               translation (1909), unzipped epub. THE CRIB ONLY.

THE STRUCTURE IS NIETZSCHE'S OWN CONTENTS LIST, read from the Gutenberg
file's Inhaltsverzeichnis and asserted against the body: the Prologue plus
80 discourses (Part One 22, Part Two 22, Part Three 16, Part Four 20), and
the mottoes that open Parts Two, Three and Four. Every heading must be
found exactly once and in order, or prep refuses to write anything.

ONE DISCOURSE PER FILE (81 sections + 3 mottoes). The discourses are the
book's units and its contents list; one file each gives every one its own
heading, anchor and TOC entry with "chapter": true under its Part, which a
multi-discourse file with split_headings cannot (split sections are set
top-level, beside the Parts). Agents take several files each.

A discourse over SPLIT_AT German words is cut into parts at its own
numbered sub-sections (never mid-section), so a part never opens on a
mechanical cut.

CONVERSIONS, applied to German and crib alike so the two can be compared:
  - emphasis  _x_ (German) and <em>/<i>/<strong> (SE) -> *x*
  - numbered sub-sections  "3." (German) and SE's <h4>III</h4> -> a line
    reading "III" (assemble sets a lone roman numeral as an h4)
  - prose paragraphs are unwrapped to one line each (the crib's shape)
  - verse  -> every line tab-indented (assemble renders it as <pre>).
    German verse is short unindented lines; a paragraph is verse when it
    has 2+ lines and every line but the last is under VERSE_MAX chars
    (prose is hard-wrapped near 72). The SE crib marks verse explicitly.
"""

import json
import re
import sys
from html import unescape
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src"
SPLIT_AT = 5000          # German words; ~1.2 English per German -> <= ~6k out
VERSE_MAX = 50

WORD_NUM = {1: "One", 2: "Two", 3: "Three", 4: "Four"}

# German title -> locked English heading. THESE ARE THE HEADINGS EVERY AGENT
# WRITES, verbatim. See text_analysis.txt section 6 for the rules.
TITLES = [
    # Part One
    ("Zarathustra’s Vorrede", "Zarathustra’s Prologue"),
    ("Von den drei Verwandlungen", "On the Three Metamorphoses"),
    ("Von den Lehrstühlen der Tugend", "On the Professors of Virtue"),
    ("Von den Hinterweltlern", "On the Believers in Worlds Behind"),
    ("Von den Verächtern des Leibes", "On the Despisers of the Body"),
    ("Von den Freuden- und Leidenschaften", "On Joys and Passions"),
    ("Vom bleichen Verbrecher", "On the Pale Criminal"),
    ("Vom Lesen und Schreiben", "On Reading and Writing"),
    ("Vom Baum am Berge", "On the Tree on the Mountainside"),
    ("Von den Predigern des Todes", "On the Preachers of Death"),
    ("Vom Krieg und Kriegsvolke", "On War and Warriors"),
    ("Vom neuen Götzen", "On the New Idol"),
    ("Von den Fliegen des Marktes", "On the Flies of the Marketplace"),
    ("Von der Keuschheit", "On Chastity"),
    ("Vom Freunde", "On the Friend"),
    ("Von tausend und Einem Ziele", "On the Thousand and One Goals"),
    ("Von der Nächstenliebe", "On Love of the Neighbor"),
    ("Vom Wege des Schaffenden", "On the Way of the Creator"),
    ("Von alten und jungen Weiblein", "On Little Old and Young Women"),
    ("Vom Biss der Natter", "On the Adder’s Bite"),
    ("Von Kind und Ehe", "On Child and Marriage"),
    ("Vom freien Tode", "On Free Death"),
    ("Von der schenkenden Tugend", "On the Gift-Giving Virtue"),
    # Part Two
    ("Das Kind mit dem Spiegel", "The Child with the Mirror"),
    ("Auf den glückseligen Inseln", "On the Blessed Isles"),
    ("Von den Mitleidigen", "On the Pitying"),
    ("Von den Priestern", "On Priests"),
    ("Von den Tugendhaften", "On the Virtuous"),
    ("Vom Gesindel", "On the Rabble"),
    ("Von den Taranteln", "On the Tarantulas"),
    ("Von den berühmten Weisen", "On the Famous Wise Men"),
    ("Das Nachtlied", "The Night Song"),
    ("Das Tanzlied", "The Dance Song"),
    ("Das Grablied", "The Grave Song"),
    ("Von der Selbst-Überwindung", "On Self-Overcoming"),
    ("Von den Erhabenen", "On the Sublime Ones"),
    ("Vom Lande der Bildung", "On the Land of Culture"),
    ("Von der unbefleckten Erkenntniss", "On Immaculate Perception"),
    ("Von den Gelehrten", "On Scholars"),
    ("Von den Dichtern", "On Poets"),
    ("Von grossen Ereignissen", "On Great Events"),
    ("Der Wahrsager", "The Soothsayer"),
    ("Von der Erlösung", "On Redemption"),
    ("Von der Menschen-Klugheit", "On Human Prudence"),
    ("Die stillste Stunde", "The Stillest Hour"),
    # Part Three
    ("Der Wanderer", "The Wanderer"),
    ("Vom Gesicht und Räthsel", "On the Vision and the Riddle"),
    ("Von der Seligkeit wider Willen", "On Involuntary Bliss"),
    ("Vor Sonnen-Aufgang", "Before Sunrise"),
    ("Von der verkleinernden Tugend", "On the Virtue That Makes Small"),
    ("Auf dem Ölberge", "On the Mount of Olives"),
    ("Vom Vorübergehen", "On Passing By"),
    ("Von den Abtrünnigen", "On the Apostates"),
    ("Die Heimkehr", "The Homecoming"),
    ("Von den drei Bösen", "On the Three Evils"),
    ("Vom Geist der Schwere", "On the Spirit of Gravity"),
    ("Von alten und neuen Tafeln", "On Old and New Tablets"),
    ("Der Genesende", "The Convalescent"),
    ("Von der grossen Sehnsucht", "On the Great Longing"),
    ("Das andere Tanzlied", "The Other Dance Song"),
    ("Die sieben Siegel", "The Seven Seals (Or: The Yes-and-Amen Song)"),
    # Part Four
    ("Das Honig-Opfer", "The Honey Sacrifice"),
    ("Der Nothschrei", "The Cry of Distress"),
    ("Gespräch mit den Königen", "Conversation with the Kings"),
    ("Der Blutegel", "The Leech"),
    ("Der Zauberer", "The Magician"),
    ("Ausser Dienst", "Retired"),
    ("Der hässlichste Mensch", "The Ugliest Man"),
    ("Der freiwillige Bettler", "The Voluntary Beggar"),
    ("Der Schatten", "The Shadow"),
    ("Mittags", "At Noon"),
    ("Die Begrüssung", "The Welcome"),
    ("Das Abendmahl", "The Last Supper"),
    ("Vom höheren Menschen", "On the Higher Man"),
    ("Das Lied der Schwermuth", "The Song of Melancholy"),
    ("Von der Wissenschaft", "On Science"),
    ("Unter Töchtern der Wüste", "Among Daughters of the Desert"),
    ("Die Erweckung", "The Awakening"),
    ("Das Eselsfest", "The Donkey Festival"),
    ("Das Nachtwandler-Lied", "The Sleepwalker’s Song"),
    ("Das Zeichen", "The Sign"),
]
PART_SIZES = [23, 22, 16, 20]          # Part One counts the Prologue
PART_HEADS = ["Erster Theil", "Zweiter Theil", "Dritter Theil",
              "Vierter und letzter Theil"]
REDEN = "Die Reden Zarathustra’s"
DISCOURSES_LINE = "Zarathustra’s Discourses"
# Two subtitles printed as a second heading line under the title
SUBTITLE_DE = {"Die sieben Siegel": "(Oder: das Ja- und Amen-Lied)"}
SUBTITLE_EN = {}   # the Seven Seals subtitle rides in its heading

# Transcription errors in Gutenberg #7205, each checked against the crib and
# the sense. Pinned by line AND content so a re-fetched file cannot move them.
FIXES = [
    # EVERY "9." in the file was transcribed as "8." (four sections that
    # number 1-8, 8, 10): Prologue, Old and New Tablets, Of the Higher Man,
    # the Sleepwalker's Song. A systematic misreading, not four misprints.
    (686, "8.", "9."),
    (8232, "8.", "9."),
    (11780, "8.", "9."),
    (13076, "8.", "9."),
    (13271, "verfuhren", "verführen"),  # "verführen und versuchen"
    (9567, "in der Weit stiftete", "in der Welt stiftete"),  # Part Four motto
    # --- found by witness.py (zeno.org / Schlechta as second witness),
    # each read against the crib. The OCR's habits: a lost umlaut, l read
    # as I, n as m, h as b, and "gieng" read as the REAL WORD "gierig"
    # ("greedy") seven times -- the dangerous kind, since it parses.
    (482, "Es kommt die Weit des", "Es kommt die Zeit des"),   # the last man
    (435, "freien Herzes", "freien Herzens"),
    (549, "einer kleiner Thür", "einer kleinen Thür"),
    (1129, "reinere Simme", "reinere Stimme"),
    (1202, "liebsten wilI", "liebsten will"),
    (1672, "sagen dich Andern", "sagen die Andern"),
    (2076, "ein Stuck Fleisch", "ein Stück Fleisch"),
    (2101, "wir zur ihr", "wir zu ihr"),
    (2204, "VieIe Länder", "Viele Länder"),
    (2473, "selber fuhrt dein", "selber führt dein"),
    (2750, "vielen kurzer Thorheiten", "vielen kurzen Thorheiten"),
    (2927, "in euren Seele", "in eure Seele"),
    (3331, "und Göttem", "und Göttern"),
    (5826, "zum Obermenschen", "zum Übermenschen"),
    (6196, "windet sieh", "windet sich"),
    (6258, "Düster gierig ich", "Düster gieng ich"),
    (6517, "dass ich gierig;", "dass ich gieng;"),
    (6539, "brach ihm Gräber", "brach ihre Gräber"),
    (7136, "gierig Zarathustra", "gieng Zarathustra"),
    (7784, "so beisst sie", "so heisst sie"),
    (7841, "Kehle weide", "Kehle weich"),
    (10443, "und gierig lachend", "und gieng lachend"),
    (10450, "den er gierig,", "den er gieng,"),
    (10550, "mein Wille gierig allem", "mein Wille gieng allem"),
    (11147, "sie gemessen ihre", "sie geniessen ihre"),
    (11244, "Augen-Blidk", "Augen-Blick"),
    (11861, "Tugend gierig!", "Tugend gieng!"),
] + [(n, "Ring de Wiederkunft", "Ring der Wiederkunft")
     for n in (9422, 9445, 9467, 9489, 9511, 9533, 9556)] + [
]

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX",
         "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII",
         "XXVIII", "XXIX", "XXX"]
ROMAN_LINE = re.compile(r"^(?:X{0,3})(?:IX|IV|V?I{0,3})$")


def words(t):
    return len(re.findall(r"\w+", t.replace("*", "")))


# ---------------------------------------------------------------- German

def german():
    raw = (SRC / "de_7205.txt").read_text(encoding="utf-8").replace("\r", "")
    L = raw.split("\n")
    for ln, old, new in FIXES:          # 1-based line numbers in de_7205.txt
        assert old in L[ln - 1], (ln, L[ln - 1])
        L[ln - 1] = L[ln - 1].replace(old, new)
    end = next(i for i, l in enumerate(L) if l.startswith("*** END OF"))
    # the body opens on the second "Erster Theil" (the first is the TOC)
    starts = [i for i, l in enumerate(L) if l.strip() == "Erster Theil"]
    assert len(starts) == 2, starts
    toc = [l.strip() for l in L[starts[0]:starts[1]] if l.strip()]
    toc_titles = [t for t in toc if t not in PART_HEADS and t != REDEN]
    toc_titles = [re.sub(r" \(Oder:.*\)$", "", t) for t in toc_titles]
    want = [d for d, _ in TITLES]
    assert toc_titles == want, (
        "TITLES does not match Nietzsche's contents list",
        [(a, b) for a, b in zip(toc_titles, want) if a != b],
        len(toc_titles), len(want))
    body = L[starts[1]:end]

    # locate every structural line, in order, exactly once
    marks = []           # (line index, kind, payload)
    queue = [("part", p) for p in PART_HEADS[:1]]
    k = 0
    seq = []
    for pi, n in enumerate(PART_SIZES):
        seq.append(("part", PART_HEADS[pi]))
        for _ in range(n):
            seq.append(("sec", TITLES[k][0]))
            if k == 0:
                seq.append(("reden", REDEN))
            k += 1
    j = 0
    for i, l in enumerate(body):
        if j >= len(seq):
            break
        kind, t = seq[j]
        s = l.strip()
        if s == t or s == t + ".":
            assert not body[i - 1].strip() if i else True, (i, l)
            marks.append((i, kind, t))
            j += 1
    assert j == len(seq), f"found {j} of {len(seq)} structural lines; next {seq[j]}"
    for kind, t in seq:            # each exactly once in the body
        n = sum(1 for l in body if l.strip() in (t, t + "."))
        assert n == 1, (t, n)

    secs, mottos = [], {}
    marks.append((len(body), "end", None))
    part = 0
    for (i, kind, t), (i2, _, _) in zip(marks, marks[1:]):
        chunk = body[i + 1:i2]
        if kind == "part":
            part += 1
            txt = "\n".join(chunk).strip()
            if txt:
                mottos[part] = txt
        elif kind == "sec":
            secs.append({"de": t, "part": part, "text": "\n".join(chunk)})
        elif kind == "reden":
            assert not "\n".join(chunk).strip()
    assert len(secs) == 81 and sorted(mottos) == [2, 3, 4], (len(secs), mottos.keys())
    return secs, mottos


def de_clean(text, de_title):
    lines = text.split("\n")
    sub = SUBTITLE_DE.get(de_title)
    if sub:
        first = next(i for i, l in enumerate(lines) if l.strip())
        assert lines[first].strip() == sub, lines[first]
        lines = lines[first + 1:]
    out = []
    for l in lines:
        m = re.fullmatch(r"(\d+)\.", l.strip())
        out.append(ROMAN[int(m.group(1))] if m else l.rstrip())
    text = "\n".join(out).strip()
    text = re.sub(r"_([^_]+)_", r"*\1*", text)
    assert "_" not in text, de_title
    paras = re.split(r"\n\s*\n", text)
    res = []
    for p in paras:
        ls = p.split("\n")
        indented = all(re.match(r"^ {2,}\S", x) for x in ls)
        ls = [x for x in ls if x.strip()] or ls
        nf = ls[:-1]
        # prose is hard-wrapped at ~72, so its non-final lines are long; a
        # verse paragraph may carry the odd long line (079 has a 71)
        short = len(ls) >= 2 and sum(len(x) < VERSE_MAX for x in nf) >= 0.6 * len(nf)
        if indented or short:
            # keep relative indent: 4 spaces = one tab, plus the verse tab
            ls = ["\t" + "\t" * ((len(x) - len(x.lstrip(" "))) // 4) + x.strip()
                  for x in ls]
            res.append("\n".join(ls))
        else:
            # prose: one paragraph per line, as in the crib (and so an
            # emphasis span never crosses a line break)
            res.append(" ".join(x.strip() for x in ls))
    return "\n\n".join(res)


# ----------------------------------------------------------------- crib

def xhtml_paras(path):
    """SE xhtml -> list of paragraph strings in the house markup."""
    x = path.read_text(encoding="utf-8")
    x = x[x.index("<body"):]
    x = re.sub(r"<hgroup.*?</hgroup>", "", x, flags=re.S)
    x = re.sub(r"<h3[^>]*>.*?</h3>", "", x, flags=re.S)   # chapter titles
    x = re.sub(r"<h4[^>]*>([IVXL]+)</h4>", r"<p>\1</p>", x)
    x = re.sub(r"<header>.*?</header>", "", x, flags=re.S)
    x = re.sub(r"</?(em|i)\b[^>]*>", "*", x)
    x = re.sub(r"</?(strong|b)\b[^>]*>", "*", x)
    x = re.sub(r"<abbr[^>]*>(.*?)</abbr>", r"\1", x, flags=re.S)
    x = x.replace("⁠", "").replace("﻿", "").replace("‑", "-")
    out = []
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>|<blockquote[^>]*z3998:song[^>]*>(.*?)</blockquote>",
                         x, flags=re.S):
        if m.group(2) is not None:
            for st in re.findall(r"<p\b[^>]*>(.*?)</p>", m.group(2), flags=re.S):
                ls = [re.sub(r"<[^>]+>", "", s).strip()
                      for s in re.findall(r"<span[^>]*>(.*?)</span>", st, flags=re.S)]
                ls = [unescape(s) for s in ls if s]
                if not ls:      # a song paragraph written as prose
                    ls = [unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", st)).strip())]
                out.append("\n".join("\t" + s for s in ls))
            continue
        p = m.group(1)
        if "<span" in p and "<br" in p:            # verse outside a song block
            ls = [unescape(re.sub(r"<[^>]+>", "", s).strip())
                  for s in re.findall(r"<span[^>]*>(.*?)</span>", p, flags=re.S)]
            out.append("\n".join("\t" + s for s in ls if s))
            continue
        p = re.sub(r"<br\s*/?>", "\n", p)
        p = unescape(re.sub(r"<[^>]+>", "", p))
        p = re.sub(r"[ \t]+", " ", p).strip()
        if p:
            out.append(p)
    return out


def crib():
    T = SRC / "se" / "epub" / "text"
    secs = ["\n\n".join(xhtml_paras(T / "prologue.xhtml"))]
    for n in range(1, 81):
        secs.append("\n\n".join(xhtml_paras(T / f"chapter-{n}.xhtml")))
    mottos = {}
    for p in (2, 3, 4):
        x = (T / f"part-{p}.xhtml").read_text(encoding="utf-8")
        q = re.search(r"<blockquote[^>]*epigraph[^>]*>(.*?)</blockquote>", x, re.S).group(1)
        q = q.replace("\u2060", "").replace("\ufeff", "")
        q = re.sub(r"<cite>(.*?)</cite>", r"<p>\1</p>", q, flags=re.S)
        q = re.sub(r"</?i\b[^>]*>", "*", q)
        ps = [unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m)).strip())
              for m in re.findall(r"<p\b[^>]*>(.*?)</p>", q, flags=re.S)]
        mottos[p] = "\n\n".join(ps)
    return secs, mottos


# ------------------------------------------------------------- assemble

def roman_count(t):
    return [l.strip() for l in t.split("\n") if ROMAN_LINE.fullmatch(l.strip()) and l.strip()]


def split_parts(text):
    """Cut a long discourse at its numbered sub-sections into balanced parts."""
    w = words(text)
    k = -(-w // SPLIT_AT)
    if k == 1:
        return [text]
    lines = text.split("\n")
    cuts = [i for i, l in enumerate(lines) if ROMAN_LINE.fullmatch(l.strip()) and l.strip()]
    assert cuts, "long discourse with no sub-sections to cut at"
    target = w / k
    pieces, start, acc = [], 0, 0
    for c in cuts[1:]:
        seg = words("\n".join(lines[start:c]))
        if seg >= target and len(pieces) < k - 1:
            pieces.append("\n".join(lines[start:c]).strip())
            start = c
    pieces.append("\n".join(lines[start:]).strip())
    return pieces


def build():
    dsecs, dmottos = german()
    esecs, emottos = crib()
    assert len(esecs) == 81
    manifest, files = [], []
    n = 0
    part_of = []
    for p, size in enumerate(PART_SIZES, 1):
        part_of += [p] * size

    def emit(title, de, en, part_before=None, sub_en=None, **extra):
        nonlocal n
        de_parts = split_parts(de)
        k = len(de_parts)
        if k > 1:
            # cut the crib at the same sub-section numerals
            heads = [roman_count(x)[0] for x in de_parts[1:]]
            en_parts, rest = [], en
            for h in heads:
                m = re.search(rf"^{h}$", rest, flags=re.M)
                en_parts.append(rest[:m.start()].strip())
                rest = rest[m.start():]
            en_parts.append(rest.strip())
        else:
            en_parts = [en]
        for i, (d, e) in enumerate(zip(de_parts, en_parts), 1):
            f = f"{n:03d}.txt"
            entry = {"file": f, "title": title, "part": i, "of": k,
                     "chapter": True}
            if part_before and i == 1:
                entry["part_before"] = part_before
            if sub_en and i == 1:
                entry["subtitle"] = sub_en
            entry["de_title"] = extra.get("de_title")
            entry["words"] = words(d)
            entry["crib_words"] = words(e)
            entry["sections"] = roman_count(d)
            manifest.append(entry)
            files.append((f, title, i, k, d, e))
            n += 1

    for idx, (ds, es) in enumerate(zip(dsecs, esecs)):
        de_t, en_t = TITLES[idx]
        assert ds["de"] == de_t
        p = part_of[idx]
        first_in_part = idx == 0 or part_of[idx - 1] != p
        pb = f"Part {WORD_NUM[p]}" if first_in_part else None
        if first_in_part and p in dmottos:
            emit(f"Epigraph to Part {WORD_NUM[p]}", de_clean(dmottos[p], ""),
                 emottos[p], part_before=pb, de_title=f"Motto, {PART_HEADS[p-1]}")
            pb = None
        dt = de_clean(ds["text"], de_t)
        if idx == 0:
            # "Die Reden Zarathustra's" stands between the Prologue and the
            # first discourse. It is a heading with no text of its own, so
            # it closes the Prologue file as a subheading (h4) and sits just
            # above "On the Three Metamorphoses" on the page. See
            # text_analysis 6.
            dt += "\n\n" + REDEN
            es += "\n\n" + DISCOURSES_LINE
        # the German and the crib must have the same numbered sub-sections
        assert roman_count(dt) == roman_count(es), (de_t, roman_count(dt), roman_count(es))
        emit(en_t, dt, es, part_before=pb, sub_en=SUBTITLE_EN.get(en_t), de_title=de_t)
    return manifest, files


def main():
    manifest, files = build()
    tot = sum(m["words"] for m in manifest)
    ctot = sum(m["crib_words"] for m in manifest)
    if "--survey" in sys.argv:
        for m in manifest:
            print(f'{m["file"]} {m["words"]:5d} {m["crib_words"]:5d} '
                  f'{m["crib_words"]/m["words"]:.2f} {m["part"]}/{m["of"]} '
                  f'{m.get("part_before") or "":10s} {m["title"]}')
        print("files", len(manifest), "German words", tot, "crib words", ctot,
              f"crib ratio {ctot/tot:.2f}")
        return
    for d in ("chapters", "reference"):
        (BOOK / d).mkdir(exist_ok=True)
        for old in (BOOK / d).glob("*.txt"):
            old.unlink()
    for f, title, i, k, d, e in files:
        head = f"{title} (Part {i} of {k})" if k > 1 else title
        (BOOK / "chapters" / f).write_text(d.rstrip() + "\n", encoding="utf-8")
        (BOOK / "reference" / f).write_text(
            f"{head} -- Thomas Common's English (1909), CRIB ONLY\n\n"
            + e.rstrip() + "\n", encoding="utf-8")
    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(files)} files; German words {tot}; crib words {ctot}")


if __name__ == "__main__":
    main()
