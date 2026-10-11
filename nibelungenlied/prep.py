"""Prepare nibelungenlied/ from the sources in _src/ (run from anywhere).

    python3 nibelungenlied/prep.py

SOURCE (the text we translate): Karl Bartsch's edition of the B version,
"Der Nibelunge Nôt" (Leipzig: Brockhaus, 1870-80), in the raw form of the
Oxford Text Archive's text 0202, as published by Bibliotheca Augustana
(Ulrich Harsch): _src/augustana/nib_n_NN.html, one page per Aventiure.
2,379 strophes in 39 Aventiuren, Bartsch's numbering, continuous.
Strophes or lines the OTA typing lacked were supplied by Harsch IN ITALICS
(strophes 1, 3, 18, 389, 523, 524). They are Bartsch's text and are kept;
prep asserts which. Strophe 1, "Uns ist in alten maeren", is not in
manuscript B at all: Bartsch (and every reading edition) prints it from
A/C, and it is the poem's most famous strophe.

SECOND WITNESS (never translated): Hermann Reichert's diplomatic
transcription of manuscript B (St. Gallen, Cod. Sang. 857), same site,
_src/augustana/nib_b_NN.html. Used only to repair the three strophes the
OTA text prints with a missing line (LINE_FIXES), each asserted to fire.

CRIB (sense only): Daniel B. Shumway's literal prose translation of
Bartsch's B text (Houghton Mifflin, 1909), Gutenberg #1151, cut per
Adventure into reference/NNN.txt with his note markers and endnotes
removed. Shumway has no strophe numbers, so alignment is per Aventiure.

Also measured (not used as cribs, see text_analysis 1): Armour's 1897
prose (#3636), Needler's 1904 verse (#7321), Horton's 1898 verse (#59831),
Lettsom's 1850 verse (#38468), and Simrock's New High German verse
(#14915 -- NOT Middle High German, whatever the ROADMAP says; it follows
the C version, "daz ist der Nibelunge liet").

Writes: chapters/NNN.txt (000-038), reference/NNN.txt, manifest.json.
"""
import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).resolve().parent
SRC = BOOK / "_src"
AUG = SRC / "augustana"

N_AVENTIUREN = 39
N_STROPHES = 2379      # Bartsch's B numbering, the standard count
# First strophe of each Aventiure in Bartsch's numbering. RECORDED FROM THE
# FIRST PARSE (2026-10-10), so it is NOT a second witness: it only guards
# against a re-download that changes the pages. The independent witnesses
# are in check.py: Reichert's diplomatic B, divided into the same 39
# Aventiuren by a different editor (the opening words of each Aventiure
# must agree), Shumway's and Armour's 39 Adventures, and Bartsch's
# published total of 2,379 strophes.
FIRST = [1, 20, 44, 139, 265, 325, 389, 482, 529, 579,
         690, 724, 778, 814, 877, 916, 1002, 1073, 1101, 1143,
         1290, 1336, 1387, 1422, 1506, 1586, 1650, 1718, 1758, 1818,
         1849, 1921, 1951, 2009, 2028, 2081, 2135, 2235, 2324]

# Strophes the OTA text prints with three lines. Each repair is taken from
# the second witness (Reichert's B) and confirmed against Shumway and
# Simrock; prep asserts that each strophe is short before the fix and that
# the fix is applied exactly once.
# The lines are in the witness's own spelling (diplomatic, so "cer" and
# "uil uerre"); the OTA text itself switches to u-spellings in late
# Aventiuren (2288 line 3 is "uil hohe uliegen"), so no normalising.
LINE_FIXES = {
    # B prints this line as the last of its 521 (= Bartsch 523); Bartsch
    # gives 523 the C reading and moves B's line here. Shumway: "They
    # dressed their journey; one saw them riding forth upon the sand."
    # Simrock 541: "Sie schickten sich zur Reise: man sah sie reiten nach
    # dem Strand."
    524: (3, "si rihten sich cer verte   man sach si riten vf den sant"),
    # B 1552, line 2.
    1555: (1, "den er dannen horte   do er des niht evant"),
    # B 2285, line 2.
    2288: (1, "si slugen daz di ringe   uil uerre dræten dan"),
}

# English headings, one per Aventiure, from the poem's own rubrics
# (nib_n_00.html, quoted as mhg_title in the manifest). "How ..." is the
# rubric's own form and reads as modern English; kept.
TITLES = [
    "The Nibelungs",
    "Siegfried, and How He Was Raised",
    "How Siegfried Came to Worms",
    "How Siegfried Fought the Saxons",
    "How Siegfried First Saw Kriemhild",
    "How Gunther Sailed to Isenland for Brunhild",
    "How Gunther Won Brunhild",
    "How Siegfried Went to Fetch His Nibelung Warriors",
    "How Siegfried Was Sent to Worms with the News",
    "How Gunther Married Brunhild at Worms",
    "How Siegfried Took His Wife Home",
    "How Gunther Invited Siegfried to a Festival",
    "How Kriemhild and Her Husband Rode to the Festival",
    "How the Queens Quarreled",
    "How Siegfried Was Betrayed",
    "How Siegfried Was Murdered",
    "How Kriemhild Mourned Her Husband, and How He Was Buried",
    "How Kriemhild Stayed Behind and Siegmund Rode Home",
    "How the Nibelung Treasure Was Brought to Worms",
    "How King Etzel Sent to Worms for Kriemhild",
    "How Kriemhild Left Worms for the Land of the Huns",
    "How Kriemhild and Etzel Were Married in Vienna",
    "How Kriemhild Planned to Avenge Her Wrongs",
    "How the Envoys Came to the Rhine",
    "How the Lords All Rode to the Huns",
    "How They Fought Else and Gelfrat",
    "How Rüdiger Welcomed the Kings to His House",
    "How the Nibelungs Came to Etzel's Castle",
    "How Hagen and Volker Sat Before Kriemhild's Hall",
    "How the Kings Went to Bed, and What Happened in the Night",
    "How the Lords Went to Church",
    "How Blödel Was Killed",
    "How the Burgundians Fought the Huns",
    "How They Threw the Dead from the Hall",
    "How Iring Fought Hagen",
    "How the Queen Had the Hall Set on Fire",
    "How Rüdiger Was Killed",
    "How All of Lord Dietrich's Warriors Were Killed",
    "How Lord Dietrich Overcame Gunther and Hagen",
]
PARTS = {0: "Part One: Siegfried", 19: "Part Two: Kriemhild's Revenge"}

# Strophes printed in italics on the Augustana page (supplied by Harsch
# where the OTA text lacked them). Asserted, so a re-download that changes
# the markup is noticed.
ITALIC = {1, 3, 18, 389, 523, 524}


def clean(fragment):
    s = fragment.replace('<span class="f_canus">|</span>', "\x00")
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    s = " ".join(s.split())
    s = re.sub(r"\s*\x00\s*", "   ", s)      # caesura: three spaces
    return s.strip()


def parse_aventiure(i):
    t = (AUG / f"nib_n_{i:02d}.html").read_text(encoding="utf-8")
    rows = re.findall(r"<h6>(\d+)</h6></td><td[^>]*>(.*?)</td>", t, re.S)
    out = []
    for n, body in rows:
        lines = [clean(x) for x in re.findall(r"<h3[^>]*>(.*?)</h3>", body, re.S)]
        out.append((int(n), lines, "<i>" in body))
    return out


def mhg_titles():
    t = (AUG / "nib_n_00.html").read_text(encoding="utf-8")
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    found = re.findall(r"^\s*(\d+)\s*Aventivre\s+(.*?)\s*$", t, re.M)
    assert [int(n) for n, _ in found] == list(range(1, 40)), found
    return [s for _, s in found]


def shumway():
    t = (SRC / "pg1151.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    t = t[t.index("THE NIBELUNGENLIED (1)"):t.index("*** END OF THE PROJECT")]
    parts = re.split(r"\n(ADVENTURE [IVXL]+\b[^\n]*)\n", t)[1:]
    heads, bodies = parts[0::2], parts[1::2]
    assert len(heads) == N_AVENTIUREN, len(heads)
    out = []
    for h, b in zip(heads, bodies):
        b = re.split(r"\n\s*ENDNOTES:", b)[0]
        b = re.sub(r" ?\(\d+\)", "", b)                 # note markers
        paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", b) if p.strip()]
        h = re.sub(r" ?\(\d+\)", "", h).strip()
        out.append((h, paras))
    return out


def armour_counts():
    t = (SRC / "pg3636.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    t = t[t.index("\nFirst Adventure\n", t.index("Book II") + 10):]
    t = t[:t.index("*** END OF THE PROJECT")]
    parts = re.split(r"\n[A-Z][a-z]+(?:-[A-Z][a-z]+)? Adventure\n", "\n" + t)[1:]
    assert len(parts) == N_AVENTIUREN, len(parts)
    return [len(p.split()) for p in parts]


def main():
    titles = mhg_titles()
    crib = shumway()
    armour = armour_counts()
    (BOOK / "chapters").mkdir(exist_ok=True)
    (BOOK / "reference").mkdir(exist_ok=True)
    manifest, seen, fixed, italic, nocaes = [], [], set(), set(), []
    for i in range(1, N_AVENTIUREN + 1):
        rows = parse_aventiure(i)
        nums = [n for n, _, _ in rows]
        assert nums[0] == FIRST[i - 1], (i, nums[0], FIRST[i - 1])
        assert nums == list(range(nums[0], nums[0] + len(nums))), i
        blocks = []
        for n, lines, ital in rows:
            if ital:
                italic.add(n)
            if n in LINE_FIXES:
                pos, line = LINE_FIXES[n]
                assert len(lines) == 3, (n, lines)
                lines.insert(pos, line)
                fixed.add(n)
            assert len(lines) == 4, (n, lines)
            assert all(lines), (n, lines)
            nocaes.extend(n for l in lines if "   " not in l)
            blocks.append(f"[{n}]\n" + "\n".join("\t" + l for l in lines))
        seen.extend(nums)
        f = f"{i - 1:03d}.txt"
        title = f"Chapter {i}: {TITLES[i - 1]}"
        (BOOK / "chapters" / f).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        h, paras = crib[i - 1]
        (BOOK / "reference" / f).write_text(
            f"{title} -- Shumway's prose (1909), \"{h}\", CRIB FOR SENSE ONLY\n\n"
            + "\n\n".join(paras) + "\n", encoding="utf-8")
        mhg_words = sum(len(l.split()) for _, ls, _ in rows for l in ls)
        crib_words = sum(len(p.split()) for p in paras)
        e = {"file": f, "title": title, "part": 1, "of": 1, "chapter": True}
        if (i - 1) in PARTS:
            e["part_before"] = PARTS[i - 1]
        e.update({
            "aventiure": i,
            "mhg_title": titles[i - 1],
            "strophes": [nums[0], nums[-1]],
            "n_strophes": len(nums),
            "mhg_words": mhg_words,
            "shumway_words": crib_words,
            "armour_words": armour[i - 1],
        })
        manifest.append(e)
    assert seen == list(range(1, N_STROPHES + 1)), "strophe sequence broken"
    assert fixed == set(LINE_FIXES), fixed
    assert italic == ITALIC, sorted(italic)
    (BOOK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("lines with no caesura (OTA typing; harmless):", sorted(set(nocaes)))
    tm = sum(e["mhg_words"] for e in manifest)
    ts = sum(e["shumway_words"] for e in manifest)
    ta = sum(e["armour_words"] for e in manifest)
    print(f"{len(manifest)} files, {len(seen)} strophes; MHG {tm} words, "
          f"Shumway {ts} ({ts / tm:.2f}), Armour {ta} ({ta / tm:.2f})")
    for e in manifest:
        print(f"  {e['file']} {e['n_strophes']:4d} str  mhg {e['mhg_words']:5d}  "
              f"shum {e['shumway_words']:5d} ({e['shumway_words'] / e['mhg_words']:.2f})  "
              f"armour {e['armour_words'] / e['mhg_words']:.2f}  {e['title']}")


if __name__ == "__main__":
    main()
