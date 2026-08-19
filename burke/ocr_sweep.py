"""Sweep the source for the scan's characteristic corruptions.

Gutenberg #15679 is a scan, and its errors are the ones a scan makes:
rn/m, ro/o, F/P, h/b, e/o, and a word split across a space. THE DANGEROUS
ONES ARE REAL ENGLISH WORDS IN THE WRONG PLACE -- "toll" for "tell",
"wore" for "were", "mate" for "make", "whoso" for "whose". Those read
past the eye at speed, survive every mechanical check in this toolchain
(the ratio does not move, must_contain does not move, the numeral diff
does not move), and are only caught by reading for sense.

So this is a REPORTER, not a fixer, and it is deliberately noisy: it
flags real words that are usually right ("ban", "bis") so that a human
decides each one. Run it before translating a file, not after. Every
finding it produced is resolved in running_notes.txt -- including the
two it raised that turned out to be CORRECT, which are the reason the
noisy patterns stay in.
"""
import collections
import pathlib
import re
import sys

SUSPECTS = {
    r"\bHo\b": "He",
    r"\bPro[mn]\b": "From",
    r"\btho\b|\btbe\b|\bthc\b": "the",
    r"\bwore\b": "were",
    r"\bwhoso\b": "whose",
    r"\btoll\b": "tell",
    r"\bmate\b": "make",
    r"\breligions\b": "religious",
    r"\bUs ten\b": "listen",
    r"\bcontrast\b": "contract",
    r"\barid\b|\bnnd\b": "and",
    r"\bnre\b": "are",
    r"\bhavo\b": "have",
    r"\bthom\b": "them",
    r"\bwitb\b": "with",
    r"\bbis\b": "his (or correct Latin 'bis', twice)",
    r"\bban\b": "ban (usually correct: the ecclesiastical ban)",
    # Added after file 017, where all three of these got past the sweep
    # above. The F/P pattern was anchored on the one word it had already
    # met ("Prom"), which is exactly the trap this script is meant to
    # avoid; it now matches the letter swap wherever it lands.
    r"\bPrance\b": "France (P for F)",
    r"\bifs\b": "its",
    r"\bmust he\b|\bcan he\b|\bto he\b": "be (h for b)",
    r"\b(the|of|and|to|a|is|in) \1\b": "doubled word",
}


def main(book="burke"):
    hits = collections.defaultdict(list)
    for f in sorted(pathlib.Path(book, "chapters").glob("*.txt")):
        text = f.read_text()
        for pat, fix in SUSPECTS.items():
            for m in re.finditer(pat, text):
                a, b = max(0, m.start() - 50), m.end() + 50
                hits[f.name].append((m.group(0), fix,
                                     text[a:b].replace("\n", " ")))
    for name in sorted(hits):
        for tok, fix, ctx in hits[name]:
            print(f"{name}  {tok!r} -> {fix}")
            print(f"      ...{ctx}...")
    print(f"{sum(len(v) for v in hits.values())} candidate(s) "
          f"in {len(hits)} file(s) -- ALL need a human; none are auto-fixed")


if __name__ == "__main__":
    main(*sys.argv[1:])
