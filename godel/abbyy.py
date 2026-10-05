"""Read the 1958 scan's ABBYY layout (_src/gdelsproof00nage_abbyy.gz) into
leaves of paragraphs, keeping what the plain OCR text throws away:

  * each paragraph's first-line indent (a leaf that opens unindented is
    continuing the last leaf's paragraph), alignment, type size, position;
  * italics as *...*, superscripts as ^{...} (Gödel numbers are powers:
    2^{6} x 3^{8});
  * the words ABBYY itself marked suspicious, as the list to read on the
    page image -- with one witness, a misread that is still a word is
    otherwise invisible.

    python3 godel/abbyy.py LEAF [LEAF ...]     # dump paragraphs
"""
import gzip
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_src/gdelsproof00nage_abbyy.gz"


def _tag(e):
    return e.tag.split("}")[-1]


def merge_marks(text):
    for a, b in (("⟨i⟩", "⟨/i⟩"), ("⟨s⟩", "⟨/s⟩")):
        text = re.sub(re.escape(b) + r"(\s*|­)" + re.escape(a), r"\1", text)
    text = re.sub(r"⟨i⟩([^A-Za-z⟨]*)⟨/i⟩", r"\1", text)
    text = text.replace("⟨i⟩", "*").replace("⟨/i⟩", "*")
    text = text.replace("⟨s⟩", "^{").replace("⟨/s⟩", "}")
    return text


def pages():
    """Yield (leaf, [para]); para = dict(text, indent, align, size, t, b,
    suspects=[words], pw, ph)."""
    with gzip.open(SRC) as f:
        leaf = -1
        for ev, el in ET.iterparse(f, events=("end",)):
            if _tag(el) != "page":
                continue
            leaf += 1
            pw, ph = int(el.get("width")), int(el.get("height"))
            paras = []
            for block in el.iter():
                if _tag(block) != "block" or block.get("blockType") != "Text":
                    continue
                for par in block.iter():
                    if _tag(par) != "par":
                        continue
                    lines, t, b, size, sus = [], None, None, [], []
                    for line in par:
                        if _tag(line) != "line":
                            continue
                        t = int(line.get("t")) if t is None else t
                        b = int(line.get("b"))
                        s = ""
                        word, bad = "", False
                        for fm in line:
                            if _tag(fm) != "formatting":
                                continue
                            txt = ""
                            for c in fm:
                                ch = c.text or ""
                                txt += ch
                                if ch.isspace() or not ch:
                                    if bad and word:
                                        sus.append(word)
                                    word, bad = "", False
                                else:
                                    word += ch
                                    bad = bad or c.get("suspicious") == "true"
                            size.append(float(fm.get("fs", "0").rstrip(".") or 0))
                            for flag, op, cl in (("italic", "⟨i⟩", "⟨/i⟩"), ("superscript", "⟨s⟩", "⟨/s⟩")):
                                if fm.get(flag) == "true" and txt.strip():
                                    lead = txt[: len(txt) - len(txt.lstrip())]
                                    trail = txt[len(txt.rstrip()):]
                                    txt = f"{lead}{op}{txt.strip()}{cl}{trail}"
                            s += txt
                        if bad and word:
                            sus.append(word)
                        lines.append(s.strip())
                    if not lines:
                        continue
                    text = ""
                    for s in lines:
                        if re.search(r"[A-Za-z]-(⟨/[is]⟩)*$", text):
                            text = re.sub(r"-((⟨/[is]⟩)*)$", "­\\1", text) + s
                        elif text.endswith("—") or s.startswith("—"):
                            text += s
                        else:
                            text = (text + " " + s).strip()
                    paras.append({"text": re.sub(r"[ \t]+", " ", merge_marks(text)),
                                  "lines": [merge_marks(l) for l in lines],
                                  "indent": int(par.get("startIndent", "0")),
                                  "left": int(par.get("leftIndent", "0")),
                                  "align": par.get("align", ""), "t": t, "b": b,
                                  "size": max(size) if size else 0, "suspects": sus,
                                  "pw": pw, "ph": ph})
            yield leaf, paras
            el.clear()


if __name__ == "__main__":
    want = {int(a) for a in sys.argv[1:]}
    for leaf, ps in pages():
        if leaf in want:
            print(f"=== leaf {leaf}")
            for p in ps:
                print(f"[ind={p['indent']} left={p['left']} {p['align']} t={p['t']} fs={p['size']}] {p['text'][:150]}")
        if want and leaf > max(want):
            break
