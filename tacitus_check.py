"""Which Tacitus text do the numbers in the screening table describe?

The re-measurement returned a row labelled "Tacitus Annals
(Church/Brodribb)" whose four scores are identical to the Histories row
already in ROADMAP.md. Two different texts do not agree to three
significant figures on four independent measures, so either the same
file was measured twice or it is an extraordinary coincidence.

The decisive quantities are the ones that do not depend on the word
lists this session does not have: the size of the middle-60% sample,
the mean sentence length, and the share of sentences over 35 words.
The table says 67,195 words, sent 22.5, 15% over 35.
"""
import re
import statistics
import sys
import urllib.request

UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
IDS = [int(a) for a in sys.argv[1:]] or [7959, 16927]

START = re.compile(r"\*\*\* ?START OF TH[EI]S? PROJECT GUTENBERG[^\n]*\n")
END = re.compile(r"\*\*\* ?END OF TH[EI]S? PROJECT GUTENBERG")
# the documented archaism probe: "thou/hast/doth/unto/ere"
ARCH = re.compile(r"\b(thou|thee|thy|thine|hast|hath|doth|dost|unto|ere|"
                  r"shalt|wert|whilst|amongst|betwixt|nay|methinks)\b", re.I)


def fetch(n):
    for u in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt",
              f"https://www.gutenberg.org/files/{n}/{n}-0.txt"):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=60
            ).read().decode("utf-8", "replace")
        except Exception:
            pass
    return None


def strip(t):
    m = START.search(t)
    if m:
        t = t[m.end():]
    m = END.search(t)
    if m:
        t = t[:m.start()]
    return t


def middle(t, frac=0.6):
    w = t.split()
    lo = int(len(w) * (1 - frac) / 2)
    return " ".join(w[lo:lo + int(len(w) * frac)])


def measure(sample):
    words = sample.split()
    sents = [s for s in re.split(r"(?<=[.!?])\s+", sample) if s.strip()]
    lens = [len(s.split()) for s in sents]
    return {
        "words": len(words),
        "arch": 1000 * len(ARCH.findall(sample)) / max(1, len(words)),
        "sent": statistics.mean(lens) if lens else 0,
        "over35": 100 * sum(1 for n in lens if n > 35) / max(1, len(lens)),
    }


print(f"{'id':>6}  {'sample':>8}  {'arch':>5}  {'sent':>5}  {'>35%':>5}  title")
for n in IDS:
    raw = fetch(n)
    if raw is None:
        print(f"{n:>6}  FETCH FAILED")
        continue
    title = re.search(r"eBook of (.{0,70})", raw)
    m = measure(middle(strip(raw)))
    print(f"{n:>6}  {m['words']:>8,}  {m['arch']:>5.2f}  {m['sent']:>5.1f}  "
          f"{m['over35']:>5.0f}  {title.group(1).strip() if title else '?'}")

print("\nthe table's row: 67,195 words, arch 0.16, sent 22.5, 15% over 35")
