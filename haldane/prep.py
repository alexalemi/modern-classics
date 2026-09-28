"""Haldane, "On Being the Right Size" -> chapters/ and modern_chapters/ 000.txt.

    python3 haldane/prep.py

RESTORED EDITION. The text is the one printed in Possible Worlds and Other
Essays (Chatto & Windus, 1927), pp. 18-26, from the OCR layer of the scan at
jbshaldane.org (source/possible-worlds-1927.pdf -> source/pw.txt). The
version most often reproduced online (source/marxists.txt, cabinet.txt)
is a DIFFERENT text in places: "provided that the ground is fairly soft. A
rat is killed, a man is broken" where 1927 prints "A rat would probably be
killed, though it can fall safely from the eleventh story of a building; a
man is killed" (checked on the page image, p. 19). We follow the print.

The web text supplies only the paragraph breaks (pdftotext loses the
indents); every word is the print's, with the OCR errors below corrected
by eye against the page images.
"""

import re
from pathlib import Path

HERE = Path(__file__).parent
L = (HERE / "source/pw.txt").read_text().split("\n")
start = next(i for i, l in enumerate(L) if "most obvious differences" in l)
end = next(i for i, l in enumerate(L) if "jumping a hedge" in l)
lines = [l for l in L[start:end + 1]
         if not re.match(r"^\s*(ON BEING THE RIGHT SIZE|POSSIBLE WORLDS|\d{1,3})\s*$", l)]
text = " ".join(l.strip() for l in lines if l.strip())
text = re.sub("\u00ad\\s*", "", text)          # line-end (soft) hyphens
text = re.sub(r"\s+", " ", text)

FIXES = [
    ("H E most obvious", "The most obvious"),
    ("hippo potamus", "hippopotamus"), ("mine sh aft", "mine shaft"),
    ("took a step ib this", "took a step this"),
    (" pre sented", " presented"), ("it carr fall", "it can fall"),
    ("ceiling vdth", "ceiling with"), ("It- oan go", "It can go"),
    ("elegant arid fantastic", "elegant and fantastic"),
    ("in creased", "increased"), ("mole cules", "molecules"),
    ("conse quence", "consequence"), ("our selves", "ourselves"),
    ("considera tions", "considerations"), ("propor tion", "proportion"),
    ("citizen to c listen", "citizen to listen"),
    ("took a step. IB This", "took a step. This"), ("it carr* fall", "it can fall"),
    ("elegant arid \\ fantastic", "elegant and fantastic"),
    ("citizen to C listen", "citizen to listen"),
    ("oxygenabsorbing", "oxygen-absorbing"),   # a real hyphen at a line end
]
for a, b in FIXES:
    # most of the split words are already joined by the hyphen rule above
    if a in text:
        text = text.replace(a, b)

text = re.sub(r"\s+([;:?!])", r"\1", text)   # the print's spaced punctuation

# paragraph breaks from the web transcription: each paragraph's opening words
web = (HERE / "source/marxists.txt").read_text().split("\n\n")
paras, pos = [], 0
for w in web[1:]:
    key = " ".join(w.split()[:4])
    i = text.find(key, pos)
    if i < 0:
        key = " ".join(w.split()[:2])
        i = text.find(key, pos)
    assert i > pos, key
    paras.append(text[pos:i].strip())
    pos = i
paras.append(text[pos:].strip())

out = "On Being the Right Size\n\n" + "\n\n".join(paras) + "\n"
for d in ("chapters", "modern_chapters"):
    (HERE / d).mkdir(exist_ok=True)
    (HERE / d / "000.txt").write_text(out)
print(len(paras), "paragraphs,", len(out.split()), "words")
