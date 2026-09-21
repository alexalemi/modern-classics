"""A second reading of the proof leaves that shares no code with prep.py's
stream builder (the epictetus rule): every word of the kept leaves, counted,
against every word of chapters/. The first run of it found 11,966 words of
notes continued from the page before, silently dropped. Exits nonzero."""
import collections
import glob
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import mathml  # noqa: E402

DROP = {230, 231, 452, 453}
# words the edition adds, each accounted for
ADDED = collections.Counter("note on the brackets chapter part one two three appendix section "
                            "all passages and notes in are due to the translator and the author is in no way "
                            "responsible for their contents".split())


def words(t):
    t = mathml.MATH.sub(" ", t)
    t = re.sub(r"\{@[^|]*\|([^}]*)\}", r"\1", t)
    t = re.sub(r"\{¶[^}]*\}", " ", t)
    t = re.sub(r"\[Figure [^\]]*\]", " ", t)
    t = re.sub(r"⟦g:\d+⟧", " ", t)
    t = t.replace("sh*oe*", "shoe")
    return collections.Counter(w.lower() for w in re.findall(r"[A-Za-zÀ-ÿͰ-Ͽἀ-ῼ]+", t))


src = collections.Counter()
for p in sorted(glob.glob(str(HERE / "proof/*.txt"))):
    if int(Path(p).stem) in DROP:
        continue
    t = Path(p).read_text().split("\n", 2)[2]
    # a word broken at a line end is one word (only inside one paragraph:
    # never across into a note or the next paragraph)
    t = re.sub(r"-\n(?=[a-z])", "", t)
    t = re.sub(r"^Footnote[:+] ?", "", t, flags=re.M)
    t = re.sub(r"^\+ ", "", t, flags=re.M)
    src += words(t)
out = collections.Counter()
for p in sorted(glob.glob(str(HERE / "chapters/*.txt"))):
    lines = Path(p).read_text().split("\n")[1:]          # the heading is the manifest's
    out += words(re.sub(r"^Footnote: ", "", "\n".join(lines), flags=re.M))
import json
for e in json.loads((HERE / "manifest.json").read_text()):
    out += words(e["title"] + " " + e.get("part_before", ""))
lost, gained = src - out, out - src - ADDED
print(f"proof {sum(src.values()):,} words, chapters {sum(out.values()):,}")
# A word broken across two leaves ("some-" | "+ thing") is two fragments
# here and one word in the edition: explain each gained word by two lost
# halves, and consume them. Whatever is left over is a real difference.
for w, k in sorted(gained.items()):
    for _ in range(k):
        for i in range(1, len(w)):
            a, b = w[:i], w[i:]
            if lost[a] > 0 and lost[b] > 0 and (a != b or lost[a] > 1):
                lost[a] -= 1; lost[b] -= 1; gained[w] -= 1
                break
lost, gained = +lost, +gained
# the Part numerals, which the dividers spell out ("Part One")
lost -= collections.Counter({"i": 1, "ii": 1, "iii": 1})
print("lost:", lost.most_common(20))
print("gained:", gained.most_common(20))
sys.exit(1 if lost or gained else 0)
