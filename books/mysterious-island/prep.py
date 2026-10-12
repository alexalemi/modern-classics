"""Build chapters/ + manifest.json for Verne's L'Île mystérieuse.

SOURCES (all under _src/):
  wikisource/P-CC.html  French Wikisource, the Hetzel 1875 in-octavo,
                        proofread against the scan ("Textes validés").
                        THE BODY TEXT COMES FROM HERE. fetch_wikisource.py.
  pg14287-fr.txt        Project Gutenberg #14287, the French. Second
                        witness only: check.py compares it word for word.
  pg8993-white.txt      Gutenberg #8993, the Stephen W. White translation
                        (Philadelphia Evening Telegraph, 1876): ~17%
                        abridged but keeps Nemo's history. SENSE CRIB ONLY,
                        sliced per chapter into reference/NNN.txt.
  pg1268-kingston.txt   Gutenberg #1268, the Kingston 1875 translation.
                        NOT a crib: it renames the cast and censors Nemo.

WHY WIKISOURCE AND NOT GUTENBERG FOR THE BODY. Measured, not assumed
(check.py prints the comparison): the two French bodies agree word for
word apart from three things, and all three go Wikisource's way.
  1. Gutenberg has NO chapter summaries. Hetzel printed one under every
     chapter number ("L'ouragan de 1865. — Cris dans les airs. — ...");
     they are Verne's text and White translates every one.
  2. Gutenberg has NONE of Verne's 25 footnotes, among them the two
     "Avis de l'Éditeur" notes in II.17 and III.16 that tie this book to
     Captain Grant's Children and to Twenty Thousand Leagues.
  3. Gutenberg moves the I.1/I.2 boundary: its chapter I stops at "le
     ballon ne pouvait plus se soutenir" and gives the landing to
     chapter II, whose summary ("Un épisode de la guerre de Sécession")
     is all flashback. Hetzel's chapter I summary ends "Une côte à
     l'horizon. — Le dénouement du drame", so the landing is chapter I.

STRUCTURE. Three Parts (22 + 20 + 20 = 62 chapters), chapter numbers
restarting in each Part, as in Hetzel. One file per chapter: the
longest chapter (III.18) is ~4,700 French words, inside one agent's
output, so nothing is split (the splitter's rule is ~7k; the 20k-leagues
prep split at 4,200 and would have split only III.18 -- not worth a seam).

EACH SOURCE FILE: the summary paragraph first (an --original build takes
its heading from the manifest and opens on the summary, as assemble.py
expects), then the body, then Verne's footnotes as "[n] text" lines after
a "NOTES" line, with "[n]" markers left at the reference points in the
body (the journey-center-earth convention). Illustration captions (Férat's
engravings, "Le ballon retombait ... (Page 12.)") are dropped: they are
the illustrator's, not Verne's, and this edition has no plates. The
"FIN DE LA ... PARTIE" lines are dropped (the manifest carries the
dividers). Verne's elision rows (". . . . .") are kept as their own
paragraphs; tables (the proportion in I.14, the chest inventory in II.2)
are kept one row per line.

The ENGLISH headings and part dividers are decided here and locked in
the manifest (TITLES below); translation agents are told the exact string.
"""

import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
SRC = BOOK / "_src"
COUNTS = {1: 22, 2: 20, 3: 20}
PART_BEFORE = {
    1: "Part One: Shipwrecked in the Air",
    2: "Part Two: The Marooned Man",
    3: "Part Three: The Secret of the Island",
}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI",
         "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
         "XXI", "XXII"]

# Locked English chapter titles, one per chapter, drawn from Verne's own
# summary for that chapter (its most telling item, in plain English).
# Numbers restart per Part, as in the French; assemble.unique_ids keeps
# the three "ch-1" anchors distinct.
TITLES = {
    1: [
        "The Hurricane of 1865",
        "An Episode of the Civil War",
        "The One Who Is Missing",
        "The Chimneys",
        "A Single Match",
        "The Castaways' Inventory",
        "Nab Has Not Come Back",
        "Is Cyrus Smith Alive?",
        "Cyrus Is Here",
        "The Engineer's Invention",
        "Lincoln Island",
        "Setting the Watches",
        "What They Found on Top",
        "Measuring the Granite Wall",
        "Iron and Steel",
        "A Fight Under the Water",
        "The New Waterfall",
        "Through the Granite",
        "Granite House",
        "The Rainy Season",
        "A Few Degrees Below Zero",
        "The Mysterious Well",
    ],
    2: [
        "The Lead Pellet",
        "The Chest on the Beach",
        "The Fever Trees",
        "A Forest for a Coastline",
        "Wreckage in the Air",
        "A New Servant",
        "A Bridge over the Mercy",
        "Guncotton",
        "The Hydraulic Elevator",
        "A Whale in Sight",
        "The Fuel of the Future",
        "An Unexpected Document",
        "Tabor Island",
        "A Fire Lit in Time",
        "A Few Tears",
        "Twelve Years on the Islet",
        "Abandoned on Tabor Island",
        "The Electric Telegraph",
        "Memories of Home",
        "Shark Gulf",
    ],
    3: [
        "Ruin or Rescue?",
        "Six Against Fifty",
        "The Fog Lifts",
        "Salvage",
        "Pencroff's Grand Theories",
        "Why the Wire Went Dead",
        "A Sure and Faithful Messenger",
        "The Convicts Near the Corral",
        "No News of Nab",
        "A Deadly Fever",
        "An Inexplicable Mystery",
        "A Lighted Window",
        "Ayrton's Story",
        "Three Years Have Passed",
        "The Volcano Wakes",
        "Captain Nemo",
        "The Last Hours of Captain Nemo",
        "The Dakkar Crypt",
        "Fire Against Water",
        "A Rock in the Pacific",
    ],
}

# ---------------------------------------------------------------- Wikisource

def ws_chapter(p, c):
    """Return (summary, paragraphs, notes) for Part p, Chapter c."""
    t = (SRC / "wikisource" / f"{p}-{c:02d}.html").read_text(encoding="utf-8")
    # footnotes
    notes = []
    for m in re.finditer(r'<li id="cite&#95;note-(\d+)">(.*?)</li>', t, re.S):
        txt = re.sub(r'<span class="mw-cite-backlink">.*?</span>', "",
                      m.group(2), flags=re.S)
        notes.append((int(m.group(1)), clean(txt)))
    # body: from the chapter heading to the reference list
    i = t.index("<h3")
    j = t.find('<ol class="references"')
    t = t[i:j if j > 0 else len(t)]
    t = re.sub(r"<h3.*?</h3>", "", t, flags=re.S)
    m = re.search(r'<div class="alineanegatif"[^>]*>(.*?)</div>', t, re.S)
    summary = clean(m.group(1))
    t = t[:m.start()] + t[m.end():]
    # illustrations and their captions
    t = re.sub(r'<div style="break-inside:avoid;.*?</div>', "", t, flags=re.S)
    t = re.sub(r'<span style="break-inside:avoid; float.*?'
               r'</span></span></span>', "", t, flags=re.S)
    t = re.sub(r'<div style="text-align:center;clear:both;font-size:80%;">'
               r'.*?</div>', "", t, flags=re.S)
    t = re.sub(r"<figure.*?</figure>", "", t, flags=re.S)
    t = re.sub(r'<span><span class="pagenum.*?</span></span>', "", t,
               flags=re.S)
    t = re.sub(r'<sup id="cite&#95;ref-(\d+)"[^>]*>.*?</sup>', r"[\1]", t,
               flags=re.S)
    # table rows and cells: one row per line
    t = re.sub(r"</td>", " ", t)
    t = re.sub(r"</tr>", "<br />", t)
    # line breaks inside a block survive as newlines; blocks as paragraphs
    t = re.sub(r"<br ?/?>", "\x01", t)
    t = re.sub(r"</p>|</div>|<p\b[^>]*>|<div\b[^>]*>|<table\b[^>]*>|"
               r"</table>|<hr[^>]*>", "\x02", t)
    paras = []
    for block in t.split("\x02"):
        lines = [clean(x) for x in block.split("\x01")]
        lines = [x for x in lines if x]
        if not lines:
            continue
        txt = "\n".join(lines)
        if re.fullmatch(r"(?i)fin de la .* partie\.?", txt.replace("\n", " ")):
            continue
        if re.fullmatch(r"(?i)(première|deuxième|troisième) partie\n.*", txt):
            continue                                   # stray part title
        paras.append(txt)
    return summary, paras, notes


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = re.sub(r"[ \t\r\n]+", " ", s)
    s = re.sub(r" ([,.])", r"\1", s)      # "&#32;" artefacts before stops
    return s.strip()


# ---------------------------------------------------------------- White crib

WHITE_HEAD = re.compile(r"^CHAPTER [IVXLC]+\.?[ \t]*$", re.M)


def white_chapters():
    """White numbers his chapters 1-62 straight through the three Parts;
    returns the 62 chapter texts (summary line + reflowed body)."""
    t = (SRC / "pg8993-white.txt").read_text(encoding="utf-8")
    t = t.replace("\r\n", "\n")
    t = t[:t.index("*** END OF")]
    t = t[:t.index("\nGLOSSARY.\n")]          # White's own appendix
    t = t[t.index("\nPART I\n"):]
    heads = list(WHITE_HEAD.finditer(t))
    assert len(heads) == 62, len(heads)
    out = []
    for k, m in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(t)
        body = t[m.end():end]
        body = re.sub(r"\n(PART I+|SHIPWRECKED IN THE AIR|THE ABANDONED|"
                      r"THE SECRET OF THE ISLAND)\n", "\n", body)
        paras = [" ".join(x.split()) for x in re.split(r"\n\s*\n", body)]
        out.append("\n\n".join(x for x in paras if x) + "\n")
    return out


# ---------------------------------------------------------------- main

def main():
    out = BOOK / "chapters"
    out.mkdir(exist_ok=True)
    ref = BOOK / "reference"
    ref.mkdir(exist_ok=True)
    white = white_chapters()
    manifest, fileno = [], 0
    for p, n in COUNTS.items():
        assert len(TITLES[p]) == n, (p, len(TITLES[p]), n)
        for c in range(1, n + 1):
            summary, paras, notes = ws_chapter(p, c)
            body = "\n\n".join(paras)
            text = summary + "\n\n" + body + "\n"
            refs = re.findall(r"\[(\d+)\]", body)
            assert sorted(map(int, refs)) == [k for k, _ in notes], \
                (p, c, refs, notes)
            if notes:
                text += "\nNOTES\n\n" + "\n\n".join(
                    f"[{k}] {v}" for k, v in notes) + "\n"
            fn = f"{fileno:03d}.txt"
            (out / fn).write_text(text, encoding="utf-8")
            (ref / fn).write_text(
                "STEPHEN W. WHITE (1876) -- SENSE CRIB ONLY. Abridged (~17% "
                "cut) and dated; translate the FRENCH in chapters/" + fn +
                ", never this.\n\n" + white[fileno], encoding="utf-8")
            entry = {
                "file": fn,
                "title": f"Chapter {c}: {TITLES[p][c - 1]}",
                "part": 1, "of": 1,
                "book": p, "chapter": f"{p}-{c}",
                "roman": ROMAN[c - 1],
                "summary_fr": summary,
                "notes": len(notes),
                "words": len(text.split()),
            }
            if c == 1:
                entry["part_before"] = PART_BEFORE[p]
            manifest.append(entry)
            fileno += 1
    # key order: the fields assemble.py reads first
    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    tot = sum(m["words"] for m in manifest)
    print(f"-> {fileno} files, {tot} French words, "
          f"{sum(m['notes'] for m in manifest)} footnotes")


if __name__ == "__main__":
    main()
