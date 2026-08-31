"""Screen a candidate against the shelf: archaism, calque, sentence length.

The 2026-08-17 screening pass that produced ROADMAP.md's table was run
ad hoc and its code was never committed, so this rebuilds the probe --
which means THE CALQUE LIST HERE IS A RECONSTRUCTION and its numbers are
only comparable to the table if it reproduces the table. `--calibrate`
measures the books whose scores the roadmap records, from their own
`chapters/` directories rather than from the network, and prints the
recorded value beside the measured one. Read that before trusting a new
row: a screening number that cannot be reproduced is the same defect as
a check that cannot fire.

    python3 screen.py --calibrate
    python3 screen.py 14484 8688 8689       # gutenberg ids
    python3 screen.py --local sophocles     # a prepared book dir

Scores are per 1,000 words over the MIDDLE 60% of the text, which skips
Gutenberg boilerplate, title pages, translators' introductions and
indexes without having to recognise any of them.
"""
import pathlib
import re
import statistics
import sys
import urllib.request

UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
START = re.compile(r"\*\*\* ?START OF TH[EI]S? PROJECT GUTENBERG[^\n]*\n")
END = re.compile(r"\*\*\* ?END OF TH[EI]S? PROJECT GUTENBERG")

# archaism you can feel -- verbatim from tacitus_check.py, the one piece
# of the original pass that survived in the repo
ARCH = re.compile(r"\b(thou|thee|thy|thine|hast|hath|doth|dost|unto|ere|"
                  r"shalt|wert|whilst|amongst|betwixt|nay|methinks)\b", re.I)

# Latinate abstraction: the suffixes that mark a noun as a thing you
# cannot point at. Deliberately suffix-based rather than a word list,
# because the class is open and a list would silently miss its own tail.
CALQ = re.compile(r"\b\w{4,}(?:tion|sion|ity|ties|ance|ence|ment|ism|"
                  r"itude|ousness|ency|ancy)\b", re.I)

# the roadmap's own recorded scores, to check the reconstruction against
RECORDED = {
    "origin-of-species": ("Darwin", 0.1, 34.8, None, 41),
    "hume": ("Hume, Enquiry", 0.47, 49.1, None, None),
    "leviathan": ("Hobbes", 5.0, 26.5, None, None),
    "epictetus": ("Epictetus (Long)", 1.5, 14.5, None, None),
    "progress-and-poverty": ("Henry George", 0.2, 39.8, None, 37),
    "bunyan": ("Bunyan", 15.4, None, 19.0, 16),
    "grimm": ("Grimm (Hunt)", 13.9, None, None, None),
    "nights": ("Burton Nights", 27.3, None, 53.0, 61),
    "meditations": ("Marcus Aurelius", 34.7, None, None, None),
}


def fetch(n):
    for u in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt",
              f"https://www.gutenberg.org/files/{n}/{n}-0.txt"):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=90
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


def verse_share(raw):
    """Share of non-blank lines that are set as verse.

    The drama-specific axis, and the one the 2026-08-17 pass had no
    reason to measure. A line is verse-shaped if it is short and opens
    on a capital -- which is what a Victorian translator's blank verse
    looks like and what running prose does not. It says whether the
    boethius question ("is the metre the author's or the translator's?")
    even arises for this text.
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        return 0.0
    v = sum(1 for l in lines
            if len(l) < 60 and l[:1].isupper() and not l.endswith(":")
            and len(l.split()) > 2)
    return 100.0 * v / len(lines)


def measure(raw):
    sample = middle(strip(raw))
    words = sample.split()
    sents = [s for s in re.split(r"(?<=[.!?])\s+", sample) if s.strip()]
    lens = [len(s.split()) for s in sents] or [0]
    return {
        "words": len(words),
        "arch": 1000 * len(ARCH.findall(sample)) / max(1, len(words)),
        "calq": 1000 * len(CALQ.findall(sample)) / max(1, len(words)),
        "sent": statistics.mean(lens),
        "over35": 100 * sum(1 for n in lens if n > 35) / len(lens),
        "verse": verse_share(strip(raw)),
    }


def local(book):
    d = pathlib.Path(book) / "chapters"
    if not d.is_dir():
        return None
    return "\n\n".join(f.read_text(errors="replace")
                       for f in sorted(d.glob("*.txt")))


HEAD = (f"{'source':>22}  {'sample':>8}  {'arch':>5}  {'calq':>5}  "
        f"{'sent':>5}  {'>35%':>5}  {'vers%':>5}  label")


def row(label, m, note=""):
    print(f"{label:>22}  {m['words']:>8,}  {m['arch']:>5.2f}  "
          f"{m['calq']:>5.1f}  {m['sent']:>5.1f}  {m['over35']:>5.0f}  "
          f"{m['verse']:>5.0f}  {note}")


def main(argv):
    if "--calibrate" in argv:
        print("CALIBRATION -- measured here vs recorded in ROADMAP.md\n")
        print(HEAD)
        for book, (name, a, c, s, o) in RECORDED.items():
            raw = local(book)
            if raw is None:
                print(f"{book:>22}  (no chapters/)")
                continue
            m = measure(raw)
            want = []
            if a is not None:
                want.append(f"arch {a}")
            if c is not None:
                want.append(f"calq {c}")
            if s is not None:
                want.append(f"sent {s}")
            if o is not None:
                want.append(f">35 {o}%")
            row(book, m, f"{name} -- recorded: {', '.join(want)}")
        return
    ids = [a for a in argv[1:] if a.isdigit()]
    books = [a for a in argv[1:] if not a.isdigit() and not a.startswith("-")]
    print(HEAD)
    for b in books:
        raw = local(b)
        if raw:
            row(b, measure(raw), "(local)")
    for n in ids:
        raw = fetch(n)
        if raw is None:
            print(f"{n:>22}  FETCH FAILED")
            continue
        t = re.search(r"(?:eBook|EBook) of (.{0,70})", raw)
        row(n, measure(raw), (t.group(1).strip() if t else "?")[:52])


if __name__ == "__main__":
    main(sys.argv)
