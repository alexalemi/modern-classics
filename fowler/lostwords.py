"""Lost-word check for the Fowler proofs: for every leaf, the dictionary
words in the OCR draft that appear nowhere in the proof, nor on the
neighbouring leaves.

    python3 fowler/lostwords.py

Diacritics, stress marks and hyphens are ignored, so a respelled or
re-hyphenated word does not count as lost, and a word that is only a
fragment of a longer proof word is dropped. What survives is mostly OCR
junk that happened to be a real word (show-through on the Google scan,
misread respellings), but it caught 'brightsome', deleted by an agent as
noise after the OCR moved it to the foot of the column (563), and
'forbears' for *forebears* (043). It cannot see a word that also occurs
elsewhere on the page: the Google word-diff in prep covers that.
"""
import re
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DICTS = ("/usr/share/dict/british-english", "/usr/share/dict/american-english")
D = set(w.strip().lower() for f in DICTS if Path(f).exists() for w in open(f))


def words(t, dehyphen=False):
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"['ʹ′‘’]", "", t)
    t = re.sub(r"-\n", "", t)
    t = re.sub(r"[*^+]", "", t)
    if dehyphen:
        t = t.replace("-", "")
    return Counter(w.lower() for w in re.findall(r"[A-Za-z]{4,}", t))


def read(d, n):
    p = HERE / d / f"{n:03d}.txt"
    return words(p.read_text()) if p.exists() else Counter()


for pre, pro in (("preproof", "proof"), ("preproof_kv", "proof_kv")):
    for p in sorted((HERE / pro).glob("*.txt")):
        q = HERE / pre / p.name
        if not q.exists():
            continue
        n = int(p.stem)
        a, b = words(q.read_text()), words(p.read_text())
        bh = words(p.read_text(), True)
        near = read(pro, n - 1) + read(pro, n + 1)
        lost = [w for w in (a - b) if w in D and b[w] == 0 and w not in bh and w not in near]
        lost = [w for w in lost if not any(w in k and w != k for k in bh)]
        if len(lost) >= 2:
            print(p.relative_to(HERE), " ".join(sorted(lost))[:160])
