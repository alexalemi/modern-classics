"""Build herodotus/chapters/ and manifest.json from the Standard Ebooks text.

    bash herodotus/fetch.sh        # once, from herodotus/
    python3 herodotus/prep.py

Source: Standard Ebooks, Herodotus, The Histories, tr. G. C. Macaulay (1890),
_src/se/book-N.xhtml (see fetch.sh for the pinned commit). SE rather than the
old herodotus.txt because that file kept Macaulay's note-reference numbers
in the prose with no way to tell them mechanically from text: "to the end
that 1 neither", "twelve myriads 13701 of the Egyptians" (note 137, first
reuse). SE marks them as <a epub:type="noteref"> and they drop exactly.

What prep does:
  - drops every noteref and Macaulay's 1,454 endnotes (textual criticism and
    Greek readings: the translator's apparatus, not the author's book) and
    his preface; the editor's introduction replaces both;
  - starts a new paragraph at EVERY section number and writes it as Macaulay
    printed it, "43. Then when the army ...", so each section is findable in
    the source and (by the agent rules) in the translation; check.py counts
    them;
  - sets the verse oracles (SE z3998:verse blockquotes) as tab-indented lines,
    the house convention for verse (quixote/, nights/);
  - drops SE's <hr/> breaks (an SE addition; neither witness has them);
  - normalises SE typography: word joiners, hair spaces, no-break spaces;
  - cuts the nine Books into whole chapters at the section starts in CUTS
    below, chosen at narrative joints, ~4-7k words each, so every file is
    "part 1 of 1" and no file opens mid-story or mid-sentence.

Book I opens with the unnumbered proem ("This is the Showing forth ..."),
which lands at the head of file 001.

VII.35 (Xerxes has the Hellespont whipped) carries no section number in
either witness: Macaulay printed it run on into VII.34. Its text is present,
inside VII.34. check.py knows this one exception.
"""

import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src" / "se"

BOOKS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
MUSES = ["Clio", "Euterpe", "Thalia", "Melpomene", "Terpsichore", "Erato",
         "Polymnia", "Urania", "Calliope"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]

# (book, first section, chapter title). A file runs from its first section
# to the section before the next entry's. Chapter numbers run 1..51 through
# the whole book (assemble.py anchors a chapter as ch-N, so restarting the
# count per Book would make nine anchors called ch-1).
CUTS = [
    (1, 1, "The First Wrongs, Gyges and Candaules, Arion, and Solon's Visit to Croesus"),
    (1, 34, "The Son of Croesus, the Testing of the Oracles, and Athens under Pisistratus"),
    (1, 65, "Sparta, the War of Croesus with Cyrus, and the Fall of Sardis"),
    (1, 86, "Croesus on the Pyre, the Customs of Lydia, and the Rise of the Medes"),
    (1, 107, "The Birth of Cyrus and the Fall of Astyages"),
    (1, 131, "The Customs of the Persians, the Greeks of Asia, and the Revolt of Pactyes"),
    (1, 162, "Harpagus Conquers Ionia, and Cyrus Takes Babylon"),
    (1, 193, "The Land and Customs of Babylon, and the Death of Cyrus"),
    (2, 1, "The Oldest People, and the Land and River of Egypt"),
    (2, 35, "The Upside-Down Customs of Egypt, and Its Gods"),
    (2, 65, "Sacred Animals, Embalming, and Life along the Nile"),
    (2, 99, "The First Kings of Egypt, Helen in Egypt, and the Thief of Rhampsinitus"),
    (2, 124, "The Pyramid Builders, the Priests' Reckoning of Time, and the Twelve Kings"),
    (2, 148, "The Labyrinth, and the Reigns from Psammetichus to Amasis"),
    (3, 1, "Cambyses Conquers Egypt, and the March against the Ethiopians"),
    (3, 26, "The Madness of Cambyses, the Ring of Polycrates, and the Son of Periander"),
    (3, 54, "The Siege of Samos, the False Smerdis, and the Plot of the Seven"),
    (3, 80, "The Debate on Government, Darius Becomes King, and the Riches of India and Arabia"),
    (3, 114, "The Edges of the World, the Death of Polycrates, and Democedes the Physician"),
    (3, 139, "The Cloak of Syloson, and Zopyrus Takes Babylon"),
    (4, 1, "The Origins of the Scythians, and the Peoples of the Far North"),
    (4, 37, "The Shape of the World, the Rivers of Scythia, and the Customs of the Scythians"),
    (4, 76, "Anacharsis and Scyles, Darius Marches on Scythia, and the Amazons"),
    (4, 118, "The War in the Empty Land, the Scythian Riddle, and the Bridge on the Danube"),
    (4, 145, "Thera, Cyrene, and the Kings of the House of Battus"),
    (4, 168, "The Peoples of Libya, and the Vengeance of Pheretime"),
    (5, 1, "Thrace, the Persian Envoys in Macedonia, and Histiaeus Called to Susa"),
    (5, 28, "The Ionian Revolt Begins, and Aristagoras at Sparta"),
    (5, 55, "Athens Frees Itself: the End of the Tyrants and the Reforms of Cleisthenes"),
    (5, 82, "The Old Feud with Aegina, and Socles on the Tyrants of Corinth"),
    (5, 97, "Athens Joins the Revolt, the Burning of Sardis, and the Death of Aristagoras"),
    (6, 1, "The Battle of Lade, the Fall of Miletus, and the End of Histiaeus"),
    (6, 43, "Mardonius in Thrace, Earth and Water, and Cleomenes against Demaratus"),
    (6, 73, "The Death of Cleomenes, the Story of Glaucus, and the War with Aegina"),
    (6, 94, "Eretria, and the Battle of Marathon"),
    (6, 121, "The Alcmaeonids, the Wooing of Agariste, and the Fall of Miltiades"),
    (7, 1, "Xerxes Decides on War, and the Dream"),
    (7, 20, "The Canal at Athos, Pythius the Lydian, and the Bridges on the Hellespont"),
    (7, 57, "The Great Review at Doriscus, and Xerxes Questions Demaratus"),
    (7, 105, "The March through Thrace and Macedonia, and the Heralds Sent to Greece"),
    (7, 138, "Athens and the Wooden Wall, and the Greeks Appeal to Argos and to Gelon"),
    (7, 163, "Corcyra, Crete and Thessaly, the Storm off Sepias, and the Fleets at Artemisium"),
    (7, 201, "Thermopylae"),
    (8, 1, "The Sea Fights off Artemisium, and the Attack on Delphi"),
    (8, 40, "Athens Abandoned, the Acropolis Taken, and the Council at Salamis"),
    (8, 83, "The Battle of Salamis, and Xerxes Turns for Home"),
    (8, 113, "The Retreat of the King, and Alexander of Macedon at Athens"),
    (9, 1, "Mardonius Takes Athens Again, and the Armies Gather at Plataea"),
    (9, 33, "The Seers, the Waiting Game, and the Night Retreat at Plataea"),
    (9, 58, "The Battle of Plataea and Its Aftermath"),
    (9, 90, "The Battle of Mycale, the Wife of Masistes, and the Fall of Sestos"),
]

NOTEREF = re.compile(r'<a [^>]*epub:type="noteref"[^>]*>.*?</a>', re.S)
BLOCK = re.compile(r'<blockquote[^>]*>.*?</blockquote>|<p[ >].*?</p>|<hr/>', re.S)
SECTION = re.compile(r'<span id="chapter-(\d)-(\d+)">\s*\d+\.\s*</span>')
MARK = "\x00"


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("⁠", "").replace(" ", " ").replace(" ", " ")
    return " ".join(s.split())


def parse_book(b):
    """[(section or None, paragraph)] in reading order for Book b. A
    paragraph's section is the one it opens, None for a continuation."""
    t = (SRC / f"book-{b}.xhtml").read_text()
    body = NOTEREF.sub("", t[t.index("</hgroup>"):])
    out = []
    for m in BLOCK.finditer(body):
        block = m.group(0)
        if block == "<hr/>":
            continue
        if block.startswith("<blockquote"):
            lines = [clean(x) for x in re.findall(r"<span(?: class=\"i\d\")?>(.*?)</span>", block, re.S)]
            if not lines:
                raise SystemExit(f"Book {b}: verse block with no lines")
            out.append((None, "\n".join("\t" + x for x in lines)))
            continue
        marked = SECTION.sub(lambda s: f"{MARK}{s.group(1)}:{s.group(2)}{MARK}", block)
        pieces = marked.split(MARK)
        lead = clean(pieces[0])
        if lead:
            out.append((None, lead))
        for i in range(1, len(pieces), 2):
            bk, n = map(int, pieces[i].split(":"))
            if bk != b:
                raise SystemExit(f"Book {b}: section id for Book {bk}")
            out.append((n, f"{n}. {clean(pieces[i + 1])}"))
    return out


def main():
    chapters = BOOK / "chapters"
    chapters.mkdir(exist_ok=True)
    for old in chapters.glob("*.txt"):
        old.unlink()
    manifest = []
    num = 0
    for b in range(1, 10):
        paras = parse_book(b)
        starts = [s for (bk, s, _) in CUTS if bk == b]
        titles = [t for (bk, _, t) in CUTS if bk == b]
        index = {n: i for i, (n, _) in enumerate(paras) if n is not None}
        for k, first in enumerate(starts):
            lo = 0 if k == 0 else index[first]
            hi = index[starts[k + 1]] if k + 1 < len(starts) else len(paras)
            if k == 0 and first != 1:
                raise SystemExit(f"Book {b}: first cut must be section 1")
            body = [p for _, p in paras[lo:hi]]
            secs = [n for n, _ in paras[lo:hi] if n is not None]
            num += 1
            name = f"{num:03d}.txt"
            text = "\n\n".join(body) + "\n"
            (chapters / name).write_text(text)
            entry = {
                "file": name,
                "title": f"Chapter {num}: {titles[k]}",
                "part": 1,
                "of": 1,
                "words": len(text.split()),
                "book": b,
                "sections": f"{ROMAN[b - 1]}.{secs[0]}–{secs[-1]}",
            }
            if k == 0:
                entry["part_before"] = f"Book {BOOKS[b - 1]}: {MUSES[b - 1]}"
            manifest.append(entry)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    w = [m["words"] for m in manifest]
    print(f"{len(manifest)} files, {sum(w)} words, min {min(w)}, "
          f"median {sorted(w)[len(w) // 2]}, max {max(w)}")


if __name__ == "__main__":
    main()
