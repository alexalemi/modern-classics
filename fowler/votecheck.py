"""The second reading for the Fowler proofs: readings where two OCRs of
OTHER copies agree against the edition, filtered to what is worth a look.

    python3 fowler/prep.py && python3 scan_diff.py fowler ID1 --vote ID2 > vote.txt
    python3 fowler/votecheck.py vote.txt

Both Archive.org scans of the 1926 printing went through the same OCR
engine, so they share its misreadings ("latier", "wncorrectable") and the
vote alone leaves a thousand hits. What is kept:
  INSERT   the print has real words the edition lacks (a dropped word:
           "means love", "a challenge, an invitation", pp. 13-14)
  TYPO     the edition has a non-word where the print has a word
           ("ancurism" for aneurism)
  VARIANT  both sides are words, and different
The rest -- the print's side a non-word, or the edition's extra words
where the OCR dropped a small-caps reference -- is the OCR's own noise.
Each kept line is for READING against the page image, never applying.
"""
import re
import sys
from pathlib import Path

DICTS = ("/usr/share/dict/british-english", "/usr/share/dict/american-english")
D = set(w.strip().lower() for f in DICTS if Path(f).exists() for w in open(f))
D |= {"oed", "vb", "adj", "adv", "pl", "n", "cf", "sc", "viz", "esp"}


def real(ws):
    return bool(ws) and all(w in D for w in ws)


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import prep  # noqa: E402


def words(s):
    return re.findall(r"[a-z]+", prep.plain(s).lower())


def page_heads():
    """[(page words as one string, running-head words)] -- a page's heads
    are its first and last headwords, and the article running on from the
    page before."""
    pages = []
    last = []
    for d, n in prep.leaf_order():
        text = (HERE / d / f"{n:03d}.txt").read_text()
        hw = [words(m.group(1)) for m in re.finditer(r"(?m)^(?:\+ )?\*\*(?!\d)(.+?)\*\*", text)]
        heads = set(last)
        for h in hw[:1] + hw[-1:]:
            heads |= set(h)
        if hw:
            last = hw[-1]
        pages.append((" ".join(words(text)), heads | {"see"}))
    return pages


PAGES = page_heads()


def running_head(pr, ctx):
    before = " ".join(ctx.split(" _ ")[0].split()[-3:])
    # the head stands between one page's last words and the next page's
    # first: take both pages' heads
    for i, (text, heads) in enumerate(PAGES):
        if before and before in text:
            nxt = PAGES[i + 1][1] if i + 1 < len(PAGES) else set()
            return all(w in heads | nxt for w in pr)
    return False


out = {"INSERT": [], "TYPO": [], "VARIANT": []}
for line in Path(sys.argv[1]).read_text().splitlines():
    m = re.match(r"\s+ED '([^']*)'\s+PRINT '([^']*)'\s+\[(.*)\]", line)
    if not m:
        continue
    ed, pr, ctx = m.group(1).split(), m.group(2).split(), m.group(3)
    if not ed and real(pr) and sum(len(w) for w in pr) >= 3:
        if not running_head(pr, ctx):
            out["INSERT"].append(line)
    elif ed and pr and not real(ed) and real(pr):
        # a word the edition splits at an accent or ligature is not a typo
        if "".join(ed) != "".join(pr):
            out["TYPO"].append(line)
    elif ed and pr and real(ed) and real(pr) and ed != pr:
        out["VARIANT"].append(line)
    elif len(ed) == len(pr) == 1 and len(ed[0]) >= 5 and not real(ed) \
            and sum(a != b for a, b in zip(ed[0], pr[0])) == 1 and len(ed[0]) == len(pr[0]):
        # one letter apart, neither side a dictionary word ("falconel" for
        # the printed Falconet, a proper name): read it
        out["TYPO"].append(line)
for k, v in out.items():
    print(f"== {k} ({len(v)})")
    print("\n".join(v))
