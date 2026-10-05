"""Per-page check for the page readers: proof/{book}-{NN}.txt against the
OCR draft of the same page.

    python3 carson/pagecheck.py BOOK NN

Lists (1) words of the draft missing from the proof -- a dropped line, a
skipped caption -- and (2) words of the proof absent from the draft --
the reader's typo, or a draft misreading rightly fixed. Short or very
common words are ignored on both sides; the IMAGE decides every item.
"""
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent


def words(s):
    s = re.sub(r"\[PLATE[^|\]]*\|[^|\]]*\|", " ", s)          # plate boxes, keep captions
    s = re.sub(r"-\s*\n\s*", "", s)
    return [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']{4,}", s)]


def main(book, nn):
    nn = f"{int(nn):02d}"
    proof = (HERE / f"proof/{book}-{nn}.txt").read_text()
    draft = (HERE / f"_src/draft/{book}-{nn}.txt").read_text()
    pw, dw = collections.Counter(words(proof)), collections.Counter(words(draft))
    missing = sorted(w for w in dw if dw[w] > pw.get(w, 0))
    extra = sorted(w for w in pw if pw[w] > dw.get(w, 0))
    print(f"{book} {nn}: {sum(pw.values())} proof words, {sum(dw.values())} draft words")
    print("  IN DRAFT, NOT IN PROOF:", " ".join(missing) or "-")
    print("  IN PROOF, NOT IN DRAFT:", " ".join(extra) or "-")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
