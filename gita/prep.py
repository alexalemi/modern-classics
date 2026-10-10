"""Prepare the Bhagavad Gita: Sanskrit source files, verse-aligned crib, manifest.

    python3 gita/prep.py            # writes chapters/, reference/, manifest.json,
                                    # variants.txt, and prints the measurements

SOURCES (all under gita/_src/, see env and text_analysis.txt section 1):
  bhgce__u.htm         GRETIL, "Bhagavadgita. Text based on the BORI edition
                       of the Mahabharata", entered by Muneo Tokunaga et al.,
                       revised by John Smith (Cambridge). IAST, one half-verse
                       a line, every line tagged Bhg_CC.VVVa/c, every speaker
                       line ("arjuna uvaca") tagged Bhg_CC.VVV with no pada.
                       THIS IS THE TEXT TRANSLATED.
  besant/discourse_N.html
                       Wikisource, "Bhagavad-Gita (Besant 4th)": Annie Besant's
                       translation, 4th edition, G. A. Natesan, Madras, 1922,
                       proofread, with the Devanagari of the vulgate printed
                       verse by verse beside it. THE CRIB (English) AND THE
                       SECOND SANSKRIT WITNESS (Devanagari, vulgate).
  telang_1898_djvu.txt Archive.org bhagavadgtwithsa0008unse: OCR of Telang,
                       SBE vol. 8, 2nd ed. 1898.
  telang_1882_djvu.txt Archive.org bhagavadgtwi00tela: OCR of the 1st ed. 1882. Orchestrator's
                       reference for cruxes only: the OCR mangles every
                       diacritic and interleaves footnotes, and the verse
                       numbers survive only in running heads, so it cannot
                       be sliced per verse. Not given to agents.
  arnold_pg2388.txt    Gutenberg #2388, Arnold's verse paraphrase. Not a crib.
  (not kept)           GRETIL's vulgate with four commentaries,
                       gretil/corpustei/sa_bhagavadgItA-4comm.xml, was fetched
                       and inspected as a second witness and dropped: CC
                       BY-NC-SA, and 50 root verses sit in <p> not <lg>.
                       Besant's Devanagari is the second witness instead.

ALIGNMENT. The critical edition has 700 verses. Besant's vulgate has 701:
her 13.1 is Arjuna's question ("prakrtim purusam caiva ...") which the
critical edition omits, so every Besant verse in chapter 13 is CE n-1. That
shift is applied here and ASSERTED (her 13.2 must transliterate to the CE's
13.1). Every other chapter must agree in count exactly, or prep stops.
"""

import difflib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src"

# Verse counts of the critical edition, chapter by chapter: the standard
# 700. Hard-coded so that a parse that loses or gains a verse cannot agree
# with itself (checks-that-cannot-see-a-missing-section).
COUNTS = [47, 72, 43, 42, 29, 47, 30, 28, 34, 42, 55, 20, 34, 27, 20, 24, 28, 78]

# Exact heading strings. The traditional chapter names come from the
# colophons of the vulgate ("iti srimadbhagavadgitasu ... arjunavisadayogo
# nama prathamo 'dhyayah"), which the critical edition does not print; the
# English is ours. See text_analysis.txt section 7.
TITLES = [
    "Arjuna's Despair",                       # arjuna-visada-yoga
    "Understanding and Action",               # sankhya-yoga
    "The Way of Action",                      # karma-yoga
    "Knowledge and the Giving Up of Action",  # jnana-karma-samnyasa-yoga
    "The Way of Renunciation",                # karma-samnyasa-yoga
    "The Way of Meditation",                  # dhyana-yoga / atma-samyama-yoga
    "Knowledge and Insight",                  # jnana-vijnana-yoga
    "The Imperishable",                       # aksara-brahma-yoga
    "The Royal Secret",                       # raja-vidya-raja-guhya-yoga
    "The Divine Glories",                     # vibhuti-yoga
    "The Vision of the Universal Form",       # visvarupa-darsana-yoga
    "The Way of Devotion",                    # bhakti-yoga
    "The Field and the Knower of the Field",  # ksetra-ksetrajna-vibhaga-yoga
    "The Three Gunas",                        # gunatraya-vibhaga-yoga
    "The Supreme Person",                     # purusottama-yoga
    "The Divine and the Demonic",             # daivasura-sampad-vibhaga-yoga
    "The Three Kinds of Faith",               # sraddhatraya-vibhaga-yoga
    "Freedom Through Renunciation",           # moksa-samnyasa-yoga
]

# English speaker tags, in the order the agents must write them. Locked
# (running_notes.txt). bhagavan is a title, "the Blessed One"; the plain name
# is what a fourteen-year-old can follow, and it is the name the frame uses.
SPEAKERS = {
    "dhṛtarāṣṭra uvāca": "Dhritarashtra said:",
    "saṃjaya uvāca": "Sanjaya said:",
    "arjuna uvāca": "Arjuna said:",
    "śrībhagavān uvāca": "Krishna said:",
}

VOWEL = re.compile(r"ai|au|[aāiīuūṛṝḷeo]")


def syllables(line):
    return len(VOWEL.findall(line.lower()))


def metre(lines):
    s = [syllables(l) for l in lines]
    if all(15 <= x <= 17 for x in s):
        return "sloka"
    if all(20 <= x <= 24 for x in s):
        return "tristubh"
    raise SystemExit(f"unclassifiable metre {s}: {lines}")


# ---------------------------------------------------------------- the CE

def parse_ce():
    raw = (SRC / "bhgce__u.htm").read_text()
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    verses, pending = {}, None
    for line in text.splitlines():
        m = re.match(r"^(.*?)\s+Bhg_(\d\d)\.(\d\d\d)([a-f]?)\s+\[=MBh_06,(\d\d\d)\.(\d\d\d)", line)
        if not m:
            continue
        body, c, v, pada = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
        if not pada:
            assert body in SPEAKERS, body
            pending = (c, v, body)
            continue
        e = verses.setdefault((c, v), {"speaker": None, "lines": [],
                                       "mbh": f"6.{int(m.group(5))}.{int(m.group(6))}"})
        if pending and pending[:2] == (c, v):
            e["speaker"] = pending[2]
            pending = None
        e["lines"].append(body)
    assert pending is None
    for c in range(1, 19):
        got = sorted(v for cc, v in verses if cc == c)
        assert got == list(range(1, COUNTS[c - 1] + 1)), (c, len(got))
    assert all(len(e["lines"]) == 2 for e in verses.values())
    for e in verses.values():
        e["metre"] = metre(e["lines"])
    return verses


# ------------------------------------------------------------ Devanagari

DV_CONS = dict(zip(
    "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह",
    "k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h".split()))
DV_VOW = dict(zip("अआइईउऊऋॠऌएऐओऔ", "a ā i ī u ū ṛ ṝ ḷ e ai o au".split()))
DV_SIGN = dict(zip("ािीुूृॄॢेैोौ", "ā i ī u ū ṛ ṝ ḷ e ai o au".split()))
VIRAMA, ANUSVARA, VISARGA, AVAGRAHA, CANDRA = "्", "ं", "ः", "ऽ", "ँ"


def translit(dev):
    out, i = [], 0
    while i < len(dev):
        ch = dev[i]
        if ch in DV_CONS:
            out.append(DV_CONS[ch])
            nxt = dev[i + 1] if i + 1 < len(dev) else ""
            if nxt == VIRAMA:
                i += 2
                continue
            if nxt in DV_SIGN:
                out.append(DV_SIGN[nxt])
                i += 2
                continue
            out.append("a")
        elif ch in DV_VOW:
            out.append(DV_VOW[ch])
        elif ch in (ANUSVARA, CANDRA):
            out.append("ṃ")
        elif ch == VISARGA:
            out.append("ḥ")
        elif ch == AVAGRAHA:
            out.append("'")
        elif ch in "​‌‍":
            pass
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def normal(s):
    """Spelling-blind comparison form: no spaces, hyphens, avagraha or
    punctuation; every nasal before a consonant written as anusvara; final
    m written as anusvara. What survives a difference here is a READING."""
    s = s.lower().replace("'", "").replace("’", "")
    s = re.sub(r"[^a-zāīūṛṝḷṃḥṅñṭḍṇśṣ]", "", s)
    s = re.sub(r"[ṅñṇnm](?=[kgcjṭḍtdpbśṣsh]|$)", "ṃ", s)
    # m/anusvara and visarga vary with the printer's sandhi at a word break
    # that the joined form can no longer see; neither is ever a reading here
    s = s.replace("ṃ", "m").replace("ḥ", "")
    return s


# ---------------------------------------------------------------- Besant

DEV_RE = re.compile(r"[\u0900-\u097F]")
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
SPEAKER_EN = re.compile(r"(The Blessed Lord|Arjuna|Sanjaya|Sañjaya|Dhritarâshtra|Dhritarashtra)\s+said:")
SPEAKER_DV = re.compile(r"^(?:अर्जुन उवाच|स(?:ञ्|ं)जय उवाच|धृतराष्ट्र उवाच|श्रीभगवानुवाच)\s*।?\s*")


class Paras(HTMLParser):
    """Wikisource's rendered page as a list of paragraphs, read by a real
    HTML parser: the page-number transclusions carry JSON with '>' inside
    quoted attributes, and a regex over <p>...</p> read those as text.

    Each paragraph: text (footnote calls kept as "[n]"), num (the text of
    the right-floated verse number, or Wikisource's [sic] correction of
    it), and the footnotes from the reference list."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras, self.notes = [], {}
        self.stack = []          # (tag, role)
        self.cur = None
        self.note = None

    def role(self):
        for _, r in reversed(self.stack):
            if r:
                return r
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag in ("link", "br", "img", "meta", "hr", "wbr"):
            return
        role = None
        if tag in ("style", "script"):
            role = "skip"
        elif tag == "p" and self.note is None:
            self.cur = {"text": [], "num": [], "sic": None}
        elif tag == "span" and "wst-floatright" in cls:
            role = "num"
        elif tag == "span" and "mw-cite-backlink" in cls:
            role = "skip"
        elif tag == "li" and a.get("data-mw-footnote-number"):
            self.note = (int(a["data-mw-footnote-number"]), [])
        if "wst-tooltip" in cls and (a.get("title") or "").startswith("[sic]"):
            if self.cur is not None and self.role() == "num":
                self.cur["sic"] = re.sub(r"^\[sic\]\s*'?|'$", "", a["title"])
        self.stack.append((tag, role))

    def handle_endtag(self, tag):
        if tag in ("link", "br", "img", "meta", "hr", "wbr"):
            return
        while self.stack:
            t, _ = self.stack.pop()
            if t == tag:
                break
        if tag == "p" and self.cur is not None and self.note is None:
            p = self.cur
            self.cur = None
            text = " ".join("".join(p["text"]).replace("\u200b", "").split())
            num = " ".join("".join(p["num"]).split())
            if p["sic"]:            # Wikisource's {{SIC}}: printed number defective
                num = p["sic"]
            if text or num:
                self.paras.append({"text": text, "num": num.strip("() ") or None})
        if tag == "li" and self.note is not None:
            k, buf = self.note
            self.notes[k] = " ".join("".join(buf).replace("\u200b", "").split())
            self.note = None

    def handle_data(self, data):
        r = self.role()
        if r == "skip":
            return
        if self.note is not None:
            self.note[1].append(data)
        elif self.cur is not None:
            (self.cur["num"] if r == "num" else self.cur["text"]).append(data)
        elif DEV_RE.search(data):
            # a Devanagari line set bare inside its div, outside any <p>
            # (chapter 13 does this for the first half of most verses)
            for line in data.splitlines():
                if line.strip():
                    self.paras.append({"text": " ".join(line.split()), "num": None})


# Misprinted verse numbers in Besant's English that Wikisource did not mark
# [sic]. Each is keyed by the opening words of the verse and must fire
# exactly once (asserted). The Devanagari beside it carries the right one.
NUM_FIXES = {
    (17, "That austerity done under a deluded understanding"): ("20", "19"),
    (18, "The body, the actor, the various organs"): ("15", "14"),
}


def parse_besant(n):
    raw = (SRC / "besant" / f"discourse_{n}.html").read_text()
    if "Wikimedia Error" in raw[:500]:
        raise SystemExit(f"besant/discourse_{n}.html is an error page; refetch it")
    P = Paras()
    P.feed(raw)
    eng, dev = {}, {}
    pending_eng, pending_dev, speaker = [], [], None
    started = False
    fired = []
    for p in P.paras:
        txt, num = p["text"], p["num"]
        if not started:            # skip the page furniture before the first verse
            if DEV_RE.search(txt) and "॥" in txt:
                started = True
            elif re.fullmatch(r"[A-Z]+ DISCOURSE\.", txt):
                pending_dev = []
                continue
            elif not DEV_RE.search(txt):
                continue
        if DEV_RE.search(txt):
            if txt.startswith("इति श्री"):
                break              # the Sanskrit colophon; it carries the CHAPTER number
            txt = SPEAKER_DV.sub("", txt.replace("ॐ", ""))
            txt = re.sub(r"[A-Za-z.]+", "", txt).strip()
            if not txt.strip(" ।"):
                continue
            m = re.search(r"॥\s*([०-९]+)\s*॥", txt)
            body = re.sub(r"॥\s*[०-९]+\s*॥", "", txt).replace("॥", "")
            pending_dev.extend(x.strip() for x in body.split("।") if x.strip())
            if m:
                dev[int(m.group(1).translate(DEV_DIGITS))] = pending_dev
                pending_dev = []
            continue
        if SPEAKER_EN.fullmatch(txt):
            speaker = txt
            continue
        if num is None:
            if txt.startswith("Thus in the glorious"):
                break              # the colophon; the critical edition has none
            if txt:
                pending_eng.append(txt)
            continue
        for (fc, start), (bad, good) in NUM_FIXES.items():
            if fc == n and txt.startswith(start):
                assert num == bad, (n, start, num)
                num = good
                fired.append(start)
        if not re.fullmatch(r"[\d\s,\-–&]+", num):
            raise SystemExit(f"discourse {n}: odd verse number {num!r}")
        vs = [int(x) for x in re.findall(r"\d+", num)]
        if re.search(r"[-–]", num):
            vs = list(range(vs[0], vs[-1] + 1))
        body = " ".join(pending_eng + [txt])
        pending_eng = []
        assert vs[0] not in eng, (n, "verse number twice", vs[0])
        eng[vs[0]] = {"verses": vs, "speaker": speaker, "text": body}
        speaker = None
    assert not pending_eng, (n, pending_eng)
    want = [k[1] for k in NUM_FIXES if k[0] == n]
    assert sorted(fired) == sorted(want), (n, "NUM_FIXES did not fire exactly once", fired)
    return eng, dev, P.notes


# ---------------------------------------------------------------- Telang

# Telang's literal prose for chapter 11 only. Besant sets 11.15-49 (the
# hymn, in the long tristubh metre) as her own BLANK VERSE, padded to the
# line, so for that stretch the verse-aligned crib is a paraphrase. Telang's
# 1898 OCR is too damaged to slice the whole book (headings for chapters
# II-VIII, XII, XVII and XVIII are not recognisable, and every diacritic is
# mangled: "Arguna", "Pazdavas"), but chapter 11 can be cut by hand between
# two anchors, which are asserted. Page heads and footnotes are dropped.
TELANG_11 = (5205, 5590, "CHAPTER XI.", "O son of Pazdu! comes to me.")


def telang_11():
    lines = (SRC / "telang_1898_djvu.txt").read_text().split("\n")
    a, b, first, last = TELANG_11
    seg = lines[a - 1:b]
    assert seg[0].strip() == first and seg[-1].strip() == last, (seg[0], seg[-1])
    out, in_note, blanks = [], False, 0
    for ln in seg:
        t = ln.strip()
        if not t:
            blanks += 1
            out.append("")
            continue
        head = re.match(r"^(\d+ )?BHAGAVADGITA\.?( \d+)?$|^CHAP\S* .*\d+\s*$|^\[\d+\]", t)
        if head:
            in_note, blanks = False, 0
            continue
        if blanks >= 2 and re.match(r"^([0-9*§†‡]|[1-9]\S?) ", t) and not re.match(r"^\d+ [A-Z][a-z]+ said", t):
            in_note = True
        blanks = 0
        if not in_note:
            out.append(t)
    text = "\n".join(out)
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


# --------------------------------------------------------------------- main

def main():
    ce = parse_ce()
    (BOOK / "chapters").mkdir(exist_ok=True)
    (BOOK / "reference").mkdir(exist_ok=True)
    manifest, variants, report = [], [], []
    tot_sa = tot_be = 0
    for c in range(1, 19):
        n = COUNTS[c - 1]
        eng, dev, notes = parse_besant(c)
        shift = 1 if c == 13 else 0
        extra = None
        if shift:
            assert normal(translit(" ".join(dev[2]))) == normal(" ".join(ce[(13, 1)]["lines"])), \
                "chapter 13 shift no longer holds"
            extra = (eng.pop(1), dev.pop(1))
            eng = {k - 1: dict(e, verses=[x - 1 for x in e["verses"]]) for k, e in eng.items()}
            dev = {k - 1: d for k, d in dev.items()}
        covered = sorted(x for e in eng.values() for x in e["verses"])
        assert covered == list(range(1, n + 1)), (c, "besant english", covered[-3:], n)
        assert sorted(dev) == list(range(1, n + 1)), (c, "besant devanagari", len(dev), n)

        title = f"Chapter {c}: {TITLES[c - 1]}"
        fname = f"{c - 1:03d}.txt"

        # --- chapters/NNN.txt: the Sanskrit, verse by verse
        out = [title, ""]
        for v in range(1, n + 1):
            e = ce[(c, v)]
            if e["speaker"]:
                out += [e["speaker"], ""]
            tag = f"[{c}.{v}]" + ("  (long metre)" if e["metre"] == "tristubh" else "")
            out += [tag] + ["\t" + l for l in e["lines"]] + [""]
        (BOOK / "chapters" / fname).write_text("\n".join(out).rstrip() + "\n")
        sa_words = sum(len(l.split()) for v in range(1, n + 1) for l in ce[(c, v)]["lines"])

        # --- reference/NNN.txt: Besant, verse by verse
        ref = [f"{title} -- Besant's 1922 English, crib only. Verse numbers are the",
               "critical edition's (the ones in chapters/NNN.txt)." if not shift else
               "critical edition's: Besant numbers this chapter one higher, and that is corrected here.",
               ""]
        if extra:
            e, d = extra
            ref += ["[13.0 -- VULGATE ONLY. Not in the critical edition and not in chapters/012.txt.",
                    " Do not translate unless running_notes.txt says the ruling is to include it.]",
                    f"{e['speaker'] or ''} {e['text']}".strip(), ""]
        be_words = 0
        for k in sorted(eng):
            e = eng[k]
            lab = f"{c}.{e['verses'][0]}" + (f"-{e['verses'][-1]}" if len(e["verses"]) > 1 else "")
            if e["speaker"]:
                ref.append(e["speaker"])
            ref += [f"[{lab}] {e['text']}", ""]
            be_words += len(e["text"].split())
        if notes:
            ref += ["", "Besant's footnotes (numbers as in the text above):", ""]
            ref += [f"[{k}] {notes[k]}" for k in sorted(notes)]
        (BOOK / "reference" / fname).write_text("\n".join(ref).rstrip() + "\n")

        # --- the second Sanskrit witness
        for v in range(1, n + 1):
            a = normal(" ".join(ce[(c, v)]["lines"]))
            b = normal(translit(" ".join(dev[v])))
            if a != b:
                r = difflib.SequenceMatcher(None, a, b).ratio()
                variants.append((c, v, r, " / ".join(ce[(c, v)]["lines"]),
                                 translit(" / ".join(dev[v]))))

        tri = [v for v in range(1, n + 1) if ce[(c, v)]["metre"] == "tristubh"]
        manifest.append({"file": fname, "title": title, "part": 1, "of": 1,
                         "chapter": True, "verses": n,
                         "speakers": [[v, SPEAKERS[ce[(c, v)]["speaker"]]] for v in range(1, n + 1)
                                      if ce[(c, v)]["speaker"]],
                         "long_metre": tri})
        tot_sa += sa_words
        tot_be += be_words
        report.append(f"{fname} {title:52s} verses {n:3d}  sa {sa_words:4d}  "
                      f"besant {be_words:5d}  ratio {be_words / sa_words:.2f}  tristubh {len(tri)}")

    (BOOK / "reference" / "010_telang.txt").write_text(
        "Chapter 11 -- Telang's 1898 prose (Sacred Books of the East 8), OCR, crib only.\n"
        "No verse numbers; footnotes and page heads removed by prep.py. Names are\n"
        "OCR-mangled (Arguna = Arjuna, Pazdu = Pandu, Ganardana = Janardana): take\n"
        "every name from running_notes.txt, never from here. Use it for 11.15-49,\n"
        "where Besant's crib is her own blank verse.\n\n" + telang_11())
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")

    lines = ["Critical edition (chapters/) against the vulgate Besant prints (Devanagari,",
             "transliterated by prep.py). Spelling, sandhi spacing, hyphens and nasal",
             "spelling are normalised away first, so what is listed is a difference of",
             "READING or a transliteration artefact. Sorted by verse; ratio = similarity.",
             "THE TRANSLATION FOLLOWS THE CRITICAL EDITION. Where Besant's English",
             "follows the other reading, the crib is wrong for this source.", ""]
    for c, v, r, a, b in variants:
        lines += [f"{c}.{v}  ratio {r:.3f}", f"   CE:      {a}", f"   vulgate: {b}", ""]
    (BOOK / "variants.txt").write_text("\n".join(lines))

    print("\n".join(report))
    print(f"TOTAL verses {sum(COUNTS)}  sanskrit words {tot_sa}  besant words {tot_be}  "
          f"ratio {tot_be / tot_sa:.2f}")
    print(f"metre: {sum(len(m['long_metre']) for m in manifest)} tristubh verses")
    print(f"variants (CE != vulgate after normalising): {len(variants)}; "
          f"below 0.95: {sum(1 for x in variants if x[2] < 0.95)}")


if __name__ == "__main__":
    sys.exit(main())
