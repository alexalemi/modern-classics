"""Per-book checks for five-rings/ -- the dogen pattern.

    python3 books/five-rings/check.py

verify.py's ratio is INERT here, honestly so: chapters/ holds each scroll
as one unbroken line of Japanese (see prep.py), so it counts one "word"
per file and prints "ratio not checked" rather than a false number. The
real guards against silent summarising are these:

  RATIO     source CJK characters (kana + kanji) against English words.
            Measured on the finished files, 0.73-0.77 for the four long
            scrolls and 0.87 for the one-page Void; between Hōjōki's 0.62
            (kana-heavy wakan prose) and Dōgen's 1.40 (kanbun), as
            expected for plain kanji-kana prose. Band pinned
            from the measurement (the purgatorio rule), not predicted.
  ARTICLES  every article head in the source (【一...】) has a subheading
            in the translation: the count of source heads equals the
            count of subheadings, file by file. A dropped article is the
            missing-section defect no self-comparing check sees; the
            heads were counted against the page images (the OCR dropped
            one, 多敵の位, and fused six more -- see prep.py HEAD_FIX).
  COLOPHON  every scroll ends on its transmission line.
  CJK       no untranslated Japanese left in the English.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import assemble                                        # noqa: E402

MIN_RATIO, MAX_RATIO = 0.65, 0.95
CJK = re.compile(r"[㐀-鿿぀-ヿ]")
# Subheadings that are not article heads: the preface and the label 地の卷
# that the 1909 print sets between the preface and the Earth scroll.
NON_ARTICLE = {"000.txt": {"Preface", "Earth"}}


def main():
    fails = []
    man = json.load(open(os.path.join(HERE, "manifest.json")))
    for e in man:
        fn = e["file"]
        src = open(os.path.join(HERE, "chapters", fn)).read()
        mod = open(os.path.join(HERE, "modern_chapters", fn)).read()
        chars = len(CJK.findall(src))
        words = len(mod.split())
        r = words / chars
        heads = len(re.findall(r"【一", src))
        paras = [p.strip() for p in mod.split("\n\n")][1:]   # skip the heading
        subs = [p for p in paras if assemble.is_subheading(p)
                and p not in NON_ARTICLE.get(fn, set())]
        print(f"{fn} {e['title']:18} {chars:5} chars {words:5} words "
              f"ratio {r:.2f}  articles {heads}/{len(subs)}")
        if not MIN_RATIO <= r <= MAX_RATIO:
            fails.append(f"RATIO {fn} {r:.2f}")
        if heads != len(subs):
            fails.append(f"ARTICLES {fn}: source {heads}, translation {len(subs)}")
        if "Shinmen Musashi." not in mod.strip().split("\n\n")[-1]:
            fails.append(f"COLOPHON {fn}")
        if CJK.search(mod):
            fails.append(f"CJK {fn}: {CJK.findall(mod)[:5]}")
    for f in fails:
        print("FAIL", f)
    print("all checks passed" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
