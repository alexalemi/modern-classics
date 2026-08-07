"""Per-file checks for Euclid and His Modern Rivals that verify.py cannot do.

    python3 euclid-rivals/check.py [NNN ...]

verify.py covers the whole project: word ratio, figure parity, must_contain,
part markers. Three things matter here that it has no way to know about.

1. THE SPEAKER SEQUENCE. This is a play, and the dangerous defect in a
   translated play is a speech given to the wrong character -- it reads
   perfectly and argues the opposite of what Carroll wrote. The source's
   tags are now trustworthy (speakers.py resolves all of them and raises
   rather than guess), so the modern file's sequence of tags must match the
   source's EXACTLY, name for name and in order. This caught nothing in the
   end but only because it was run: it is the one check that would catch
   the failure that matters most.

   It also fixes a convention. An aside is written "Minos. (thoughtfully)
   Well, ..." -- tag, period, then the parenthetical -- and NOT the modern
   playscript form "Minos (thoughtfully)." Carroll's own form keeps the
   check mechanical, and there are forty-odd of them still to come.

2. NUMERIC TOKENS. fleming/'s lesson: a lost measurement passes the word
   ratio, the marker parity and must_contain alike. Noisy on an OCR source
   (Roman numerals scan as digits), so it reports rather than fails -- but
   it is what found the dropped "(see pp. 222, 241)" citation in file 001.

3. HEADINGS THAT ARE NOT HEADINGS. assemble.is_subheading() rejects any
   line ending in ".;:,--", so "§ 5. Playfair's Axiom." renders as a
   paragraph shouted in capitals while "§ 5. Playfair's Axiom" renders as
   an <h4>. This is ball/'s trap and fourteen headings walked into it here.
"""

import collections
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import assemble                                            # noqa: E402

BOOK = Path(__file__).parent
TAG = re.compile(r"^(Minos|Euclid|Niemand|Nostradamus|Rhadamanthus)\.", re.M)
MARKER = re.compile(r"\[(?:Figure|Table) ([^\]:]+)")
MIN_RATIO, MAX_RATIO = 0.85, 1.3


def body(path, header_lines=0):
    text = path.read_text()
    if header_lines:
        text = "\n".join(text.split("\n")[header_lines:])
    return text


def words(text):
    return len(MARKER.sub("", text).split())


def numerals(text):
    return collections.Counter(re.findall(r"\d+", MARKER.sub("", text)))


def check(num):
    src = body(BOOK / "chapters" / f"{num}.txt")
    mod = body(BOOK / "modern_chapters" / f"{num}.txt", header_lines=2)
    bad = []

    sw, mw = words(src), words(mod)
    ratio = mw / sw if sw else 0
    if not MIN_RATIO <= ratio <= MAX_RATIO:
        bad.append(f"ratio {ratio:.2f} outside {MIN_RATIO}-{MAX_RATIO}")

    if MARKER.findall(src) != MARKER.findall(mod):
        bad.append(f"markers {MARKER.findall(src)} != {MARKER.findall(mod)}")

    s_tags, m_tags = TAG.findall(src), TAG.findall(mod)
    if s_tags != m_tags:
        ops = [o for o in difflib.SequenceMatcher(None, s_tags, m_tags)
               .get_opcodes() if o[0] != "equal"]
        bad.append(f"speaker sequence differs ({len(s_tags)} vs "
                   f"{len(m_tags)}): {ops[:3]}")

    for line in mod.split("\n"):
        s = line.strip()
        if (s.startswith(("§", "Table ")) and not assemble.is_subheading(s)):
            bad.append(f"heading will render as a paragraph: {s!r}")

    lost = sorted((numerals(src) - numerals(mod)).elements())
    note = f"  numerals only in source: {lost}" if lost else ""
    print(f"{num}: {sw:5} -> {mw:5}  ratio {ratio:.2f}  "
          f"{len(m_tags):3} speeches  {'OK' if not bad else 'FAIL'}")
    for b in bad:
        print(f"    !! {b}")
    if note:
        print(note)
    return not bad


def main():
    todo = sys.argv[1:] or sorted(
        p.stem for p in (BOOK / "modern_chapters").glob("*.txt"))
    ok = all([check(n) for n in todo])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
